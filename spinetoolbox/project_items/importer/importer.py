######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains Importer project item class.

:authors: P. Savolainen (VTT), P. Vennström (VTT), A. Soininen (VTT)
:date:   10.6.2019
"""

from collections import Counter
import os
from itertools import takewhile
from PySide2.QtCore import QAbstractListModel, QFileInfo, QModelIndex, Qt, Signal, Slot
from PySide2.QtWidgets import QFileIconProvider, QListWidget, QDialog, QVBoxLayout, QDialogButtonBox
from spine_engine import ExecutionDirection
from spinetoolbox.project_item import ProjectItem
from spinetoolbox.helpers import create_dir, serialize_path
from spinetoolbox.spine_io.gdx_utils import find_gams_directory
from spinetoolbox.spine_io.importers.csv_reader import CSVConnector
from spinetoolbox.spine_io.importers.excel_reader import ExcelConnector
from spinetoolbox.spine_io.importers.gdx_connector import GdxConnector
from spinetoolbox.spine_io.importers.json_reader import JSONConnector
from spinetoolbox.import_editor.widgets.import_editor_window import ImportEditorWindow
from .commands import ChangeItemSelectionCommand, UpdateSettingsCommand
from ..shared.commands import UpdateCancelOnErrorCommand
from .executable_item import ExecutableItem
from .item_info import ItemInfo
from .utils import deserialize_mappings

_CONNECTOR_NAME_TO_CLASS = {
    "CSVConnector": CSVConnector,
    "ExcelConnector": ExcelConnector,
    "GdxConnector": GdxConnector,
    "JSONConnector": JSONConnector,
}


class Importer(ProjectItem):
    def __init__(
        self, toolbox, project, logger, name, description, mappings, x, y, cancel_on_error=True, mapping_selection=None
    ):
        """Importer class.

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            project (SpineToolboxProject): the project this item belongs to
            logger (LoggerInterface): a logger instance
            name (str): Project item name
            description (str): Project item description
            mappings (list): List where each element contains two dicts (path dict and mapping dict)
            x (float): Initial icon scene X coordinate
            y (float): Initial icon scene Y coordinate
            cancel_on_error (bool, optional): if True, changes will be reverted on errors
            mapping_selection (list, optional): a list of booleans, one for each mapping marking the mappings
                either selected or unselected
       """
        super().__init__(name, description, x, y, project, logger)
        # Make logs subdirectory for this item
        self._toolbox = toolbox
        self.logs_dir = os.path.join(self.data_dir, "logs")
        try:
            create_dir(self.logs_dir)
        except OSError:
            self._logger.msg_error.emit(f"[OSError] Creating directory {self.logs_dir} failed. Check permissions.")
        # Variables for saving selections when item is (de)activated
        if not mappings:
            mappings = list()
        # convert table_types and table_row_types keys to int since json always has strings as keys.
        for _, mapping in mappings:
            table_types = mapping.get("table_types", {})
            mapping["table_types"] = {
                table_name: {int(col): t for col, t in col_types.items()}
                for table_name, col_types in table_types.items()
            }
            table_row_types = mapping.get("table_row_types", {})
            mapping["table_row_types"] = {
                table_name: {int(row): t for row, t in row_types.items()}
                for table_name, row_types in table_row_types.items()
            }
        # Convert serialized paths to absolute in mappings
        _fix_1d_array_to_array(mappings)
        self.settings = deserialize_mappings(mappings, self._project.project_dir)
        # self.settings is now a dictionary, where elements have the absolute path as the key and the mapping as value
        self.cancel_on_error = cancel_on_error
        self._file_model = _FileListModel()
        if mapping_selection is None:
            mapping_selection = len(self.settings) * [True]
        self._file_model.set_initial_state(self.settings.keys(), mapping_selection)
        self._file_model.selected_for_import_state_changed.connect(self._push_file_selection_change_to_undo_stack)
        # connector class
        self._preview_widget = {}  # Key is the filepath, value is the ImportEditorWindow instance

    @staticmethod
    def item_type():
        """See base class."""
        return ItemInfo.item_type()

    @staticmethod
    def item_category():
        """See base class."""
        return ItemInfo.item_category()

    def execution_item(self):
        """Creates project item's execution counterpart."""
        selected_settings = dict()
        for file_item in self._file_model.existing_files():
            label = file_item.label
            selected_settings[label] = self.settings[label] if file_item.selected_for_import else "deselected"
        python_path = self._project.settings.value("appSettings/pythonPath", defaultValue="")
        gams_path = self._project.settings.value("appSettings/gamsPath", defaultValue=None)
        executable = ExecutableItem(
            self.name, selected_settings, self.logs_dir, python_path, gams_path, self.cancel_on_error, self._logger
        )
        return executable

    @Slot()
    def executed_successfully(self, execution_direction, engine_state):
        """Notifies Toolbox for successful database import."""
        if execution_direction != ExecutionDirection.FORWARD:
            return
        successors = self._project.direct_successors(self)
        committed_db_maps = set()
        for successor in successors:
            if successor.item_type() == "Data Store":
                url = successor.sql_alchemy_url()
                database_map = self._project.db_mngr.get_db_map(url)
                if database_map is not None:
                    committed_db_maps.add(database_map)
        if committed_db_maps:
            cookie = self
            self._project.db_mngr.session_committed.emit(committed_db_maps, cookie)

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = super().make_signal_handler_dict()
        s[self._properties_ui.toolButton_open_dir.clicked] = lambda checked=False: self.open_directory()
        s[self._properties_ui.pushButton_import_editor.clicked] = self._handle_import_editor_clicked
        s[self._properties_ui.treeView_files.doubleClicked] = self._handle_files_double_clicked
        s[self._properties_ui.cancel_on_error_checkBox.stateChanged] = self._handle_cancel_on_error_changed
        return s

    @Slot(int)
    def _handle_cancel_on_error_changed(self, _state):
        cancel_on_error = self._properties_ui.cancel_on_error_checkBox.isChecked()
        if self.cancel_on_error == cancel_on_error:
            return
        self._toolbox.undo_stack.push(UpdateCancelOnErrorCommand(self, cancel_on_error))

    def set_cancel_on_error(self, cancel_on_error):
        self.cancel_on_error = cancel_on_error
        if not self._active:
            return
        check_state = Qt.Checked if self.cancel_on_error else Qt.Unchecked
        self._properties_ui.cancel_on_error_checkBox.blockSignals(True)
        self._properties_ui.cancel_on_error_checkBox.setCheckState(check_state)
        self._properties_ui.cancel_on_error_checkBox.blockSignals(False)

    def set_file_selected(self, label, selected):
        self._file_model.set_selected(label, selected)

    def restore_selections(self):
        """Restores selections into shared widgets when this project item is selected."""
        self._properties_ui.cancel_on_error_checkBox.setCheckState(Qt.Checked if self.cancel_on_error else Qt.Unchecked)
        self._properties_ui.label_name.setText(self.name)
        self._properties_ui.treeView_files.setModel(self._file_model)

    def save_selections(self):
        """Saves selections in shared widgets for this project item into instance variables."""
        self._properties_ui.treeView_files.setModel(None)

    def update_name_label(self):
        """Update Importer properties tab name label. Used only when renaming project items."""
        self._properties_ui.label_name.setText(self.name)

    @Slot(bool)
    def _handle_import_editor_clicked(self, checked=False):
        """Opens Import editor for the file selected in list view."""
        index = self._properties_ui.treeView_files.currentIndex()
        if not index.isValid():
            for row, item in enumerate(self._file_model.files):
                if item.exists():
                    index = self._file_model.index(row, 0)
                    self._properties_ui.treeView_files.setCurrentIndex(index)
                    break
        self.open_import_editor(index)

    @Slot("QModelIndex")
    def _handle_files_double_clicked(self, index):
        """Opens Import editor for the double clicked index."""
        self.open_import_editor(index)

    def open_import_editor(self, index):
        """Opens Import editor for the given index."""
        label = index.data()
        if label is None:
            self._logger.msg_error.emit("Please select a source file from the list first.")
            return
        file_item = self._file_model.find_file(label)
        file_path = file_item.path
        if not file_item.exists():
            self._logger.msg_error.emit(f"File does not exist yet.")
            self._file_model.mark_as_nonexistent(index)
            return
        if not os.path.exists(file_path):
            self._logger.msg_error.emit(f"Cannot find file '{file_path}'.")
            self._file_model.mark_as_nonexistent(index)
            return
        # Raise current form for the selected file if any
        preview_widget = self._preview_widget.get(label, None)
        if preview_widget:
            if preview_widget.windowState() & Qt.WindowMinimized:
                # Remove minimized status and restore window with the previous state (maximized/normal state)
                preview_widget.setWindowState(preview_widget.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                preview_widget.activateWindow()
            else:
                preview_widget.raise_()
            return
        # Create a new form for the selected file
        settings = self.get_settings(label)
        # Try and get connector from settings
        source_type = settings.get("source_type", None)
        if source_type is not None:
            connector = _CONNECTOR_NAME_TO_CLASS[source_type]
        else:
            # Ask user
            connector = self.get_connector(label)
            if not connector:
                # Aborted by the user
                return
        self._logger.msg.emit(f"Opening Import editor for file: {file_path}")
        connector_settings = {"gams_directory": self._gams_system_directory()}
        preview_widget = self._preview_widget[label] = ImportEditorWindow(
            self, file_path, connector, connector_settings, settings, self._toolbox
        )
        preview_widget.settings_updated.connect(lambda s, importee=label: self.save_settings(s, importee))
        preview_widget.connection_failed.connect(lambda m, importee=label: self._connection_failed(m, importee))
        preview_widget.destroyed.connect(lambda o=None, importee=label: self._preview_destroyed(importee))
        preview_widget.start_ui()

    def get_connector(self, importee):
        """Shows a QDialog to select a connector for the given source file.
        Mimics similar routine in `spine_io.widgets.import_widget.ImportDialog`

        Args:
            importee (str): Label of the file acting as an importee

        Returns:
            Asynchronous data reader class for the given importee
        """
        connector_list = [CSVConnector, ExcelConnector, GdxConnector, JSONConnector]  # add others as needed
        connector_names = [c.DISPLAY_NAME for c in connector_list]
        dialog = QDialog(self._toolbox)
        dialog.setLayout(QVBoxLayout())
        connector_list_wg = QListWidget()
        connector_list_wg.addItems(connector_names)
        # Set current item in `connector_list_wg` based on file extension
        _filename, file_extension = os.path.splitext(importee)
        file_extension = file_extension.lower()
        if file_extension.startswith(".xls"):
            row = connector_list.index(ExcelConnector)
        elif file_extension in (".csv", ".dat", ".txt"):
            row = connector_list.index(CSVConnector)
        elif file_extension == ".gdx":
            row = connector_list.index(GdxConnector)
        elif file_extension == ".json":
            row = connector_list.index(JSONConnector)
        else:
            row = None
        if row is not None:
            connector_list_wg.setCurrentRow(row)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(dialog.accept)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(dialog.reject)
        connector_list_wg.doubleClicked.connect(dialog.accept)
        dialog.layout().addWidget(connector_list_wg)
        dialog.layout().addWidget(button_box)
        _dirname, filename = os.path.split(importee)
        dialog.setWindowTitle("Select connector for '{}'".format(filename))
        answer = dialog.exec_()
        if answer:
            row = connector_list_wg.currentIndex().row()
            return connector_list[row]

    def select_connector_type(self, index):
        """Opens dialog to select connector type for the given index."""
        importee = index.data()
        connector = self.get_connector(importee)
        if not connector:
            # Aborted by the user
            return
        settings = self.get_settings(importee)
        settings["source_type"] = connector.__name__

    def _connection_failed(self, msg, importee):
        self._logger.msg_error.emit(msg)
        preview_widget = self._preview_widget.pop(importee, None)
        if preview_widget:
            preview_widget.close()

    def get_settings(self, importee):
        """Returns the mapping dictionary for the file in given path.

        Args:
            importee (str): Label of the file whose mapping is queried

        Returns:
            dict: Mapping dictionary for the requested importee or an empty dict if not found
        """
        return self.settings.get(importee, {})

    def save_settings(self, settings, importee):
        """Updates an existing mapping or adds a new mapping
         (settings) after closing the import preview window.

        Args:
            settings (dict): Updated mapping (settings) dictionary
            importee (str): Absolute path to a file, whose mapping has been updated
        """
        if self.settings.get(importee) == settings:
            return
        self._toolbox.undo_stack.push(UpdateSettingsCommand(self, settings, importee))

    def _preview_destroyed(self, importee):
        """Destroys preview widget instance for the given importee.

        Args:
            importee (str): Absolute path to a file, whose preview widget is destroyed
        """
        self._preview_widget.pop(importee, None)

    @Slot(bool, str)
    def _push_file_selection_change_to_undo_stack(self, selected, label):
        """Makes changes to file selection undoable."""
        self._toolbox.undo_stack.push(ChangeItemSelectionCommand(self, selected, label))

    def _do_handle_dag_changed(self, resources):
        """See base class."""
        self._file_model.update(resources)
        labels = self._file_model.labels()
        for settings_label in list(self.settings):
            if settings_label not in labels:
                del self.settings[settings_label]
        self._notify_if_duplicate_file_paths()
        if self._file_model.rowCount() == 0:
            self.add_notification(
                "This Importer does not have any input data. "
                "Connect Data Connections to this Importer to use their data as input."
            )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        # Serialize mappings before saving
        d["mappings"] = self.serialize_mappings(self.settings, self._project.project_dir)
        d["cancel_on_error"] = self._properties_ui.cancel_on_error_checkBox.isChecked()
        d["mapping_selection"] = [item.selected_for_import for item in self._file_model.files]
        return d

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type() == "Data Connection":
            self._logger.msg.emit(
                "Link established. You can define mappings on data from "
                f"<b>{source_item.name}</b> using item <b>{self.name}</b>."
            )
        elif source_item.item_type() == "Tool":
            self._logger.msg.emit(
                "Link established. You can define mappings on output files from "
                f"<b>{source_item.name}</b> using item <b>{self.name}</b>."
            )
        elif source_item.item_type() == "Data Store":
            self._logger.msg.emit("Link established.")
        else:
            super().notify_destination(source_item)

    @staticmethod
    def default_name_prefix():
        """see base class"""
        return "Importer"

    def tear_down(self):
        """Closes all preview widgets."""
        for widget in self._preview_widget.values():
            widget.close()

    def _notify_if_duplicate_file_paths(self):
        """Adds a notification if file_list contains duplicate entries."""
        labels = list()
        for item in self._file_model.files:
            labels.append(item.label)
        file_counter = Counter(labels)
        duplicates = list()
        for label, count in file_counter.items():
            if count > 1:
                duplicates.append(label)
        if duplicates:
            self.add_notification("Duplicate input files from upstream items:<br>{}".format("<br>".join(duplicates)))

    @staticmethod
    def upgrade_from_no_version_to_version_1(item_name, old_item_dict, old_project_dir):
        """Converts mappings to a list, where each element contains two dictionaries,
        the serialized path dictionary and the mapping dictionary for the file in that
        path."""
        new_importer = dict(old_item_dict)
        mappings = new_importer.get("mappings", {})
        list_of_mappings = list()
        paths = list(mappings.keys())
        for path in paths:
            mapping = mappings[path]
            if "source_type" in mapping and mapping["source_type"] == "CSVConnector":
                _fix_csv_connector_settings(mapping)
            new_path = serialize_path(path, old_project_dir)
            if new_path["relative"]:
                new_path["path"] = os.path.join(".spinetoolbox", "items", new_path["path"])
            list_of_mappings.append([new_path, mapping])
        new_importer["mappings"] = list_of_mappings
        return new_importer

    @staticmethod
    def serialize_mappings(mappings, project_path):
        """
        Serializes the importer's mappings.

        Returns a list where each element contains two dictionaries:
        the 'serialized' file label in a dictionary and the mapping dictionary.

        Args:
            mappings (dict): Dictionary with mapping specifications
            project_path (str): Path to project directory

        Returns:
            list: serialized file item labels and mappings
        """
        serialized_mappings = list()
        for source, mapping in mappings.items():  # mappings is a dict with absolute paths as keys and mapping as values
            serialized_mappings.append([serialize_path(source, project_path), mapping])
        return serialized_mappings

    def _gams_system_directory(self):
        """Returns GAMS system path from Toolbox settings or None if GAMS default is to be used."""
        path = self._project.settings.value("appSettings/gamsPath", defaultValue=None)
        if not path:
            path = find_gams_directory()
        if path is not None and os.path.isfile(path):
            path = os.path.dirname(path)
        return path


def _fix_1d_array_to_array(mappings):
    """
    Replaces '1d array' with 'array' for parameter type in mappings.

    With spinedb_api >= 0.3, '1d array' parameter type was replaced by 'array'.
    Other settings in a mapping are backwards compatible except the name.
    """
    for more_mappings in mappings:
        for settings in more_mappings:
            table_mappings = settings.get("table_mappings")
            if table_mappings is not None:
                for sheet_settings in table_mappings.values():
                    for setting in sheet_settings:
                        parameter_setting = setting.get("parameters")
                        if parameter_setting is not None:
                            parameter_type = parameter_setting.get("parameter_type")
                            if parameter_type == "1d array":
                                parameter_setting["parameter_type"] = "array"


def _fix_csv_connector_settings(settings):
    """CSVConnector saved the table names as the filepath, change that
    to 'csv' instead. This function will mutate the dictionary.

    Args:
        settings (dict): Mapping settings that should be updated
    """
    table_mappings = settings.get("table_mappings", {})
    k = list(table_mappings)
    if len(k) == 1 and k[0] != "csv":
        table_mappings["csv"] = table_mappings.pop(k[0])

    table_types = settings.get("table_types", {})
    k = list(table_types.keys())
    if len(k) == 1 and k[0] != "csv":
        table_types["csv"] = table_types.pop(k[0])

    table_row_types = settings.get("table_row_types", {})
    k = list(table_row_types.keys())
    if len(k) == 1 and k[0] != "csv":
        table_row_types["csv"] = table_row_types.pop(k[0])

    table_options = settings.get("table_options", {})
    k = list(table_options.keys())
    if len(k) == 1 and k[0] != "csv":
        table_options["csv"] = table_options.pop(k[0])

    selected_tables = settings.get("selected_tables", [])
    if len(selected_tables) == 1 and selected_tables[0] != "csv":
        selected_tables.pop(0)
        selected_tables.append("csv")


def _file_label(resource):
    """Picks a label for given file resource."""
    if resource.type_ == "file":
        return resource.path
    elif resource.type_ in ("transient_file", "file_pattern"):
        label = resource.metadata.get("label")
        if label is None:
            if resource.url is None:
                raise RuntimeError("ProjectItemResource is missing a url and metadata 'label'.")
            return resource.path
        return label
    raise RuntimeError(f"Unknown resource type '{resource.type_}'")


class _FileListItem:
    """
    An item for FileListModel.

    Attributes:
        label (str): a file's label; a full path for 'permanent' files or just the basename
            for 'transient' files like Tool's output.
        path (str): absolute path to file, can be an empty string if file doesn't exist yet
        selected_for_import (bool): if True, the file has been selected for importing
        provider_name (str): name of the item providing the file
        is_pattern (bool): True if the file is actually a file name pattern
    """

    def __init__(self, label, path, provider_name, is_pattern=False):
        """
        Args:
            label (str): a file's label; a full path for 'permanent' files or just the basename
                for 'transient' files like Tool's output.
            path (str): absolute path to the file, empty if not known
            provider_name (str): name of the project item providing the file
            is_pattern (bool): True if the file is actually a file name pattern
        """
        self.label = label
        self.path = path
        self.selected_for_import = True
        self.provider_name = provider_name
        self.is_pattern = is_pattern

    @classmethod
    def from_resource(cls, resource):
        """
        Constructs a _FileListItem from ProjectItemResource.

        Args:
            resource (ProjectItemResource): a resource
        Return:
            _FileListItem: an item based on given resource
        """
        is_pattern = False
        if resource.type_ == "file":
            label = resource.path
        elif resource.type_ == "transient_file":
            label = _file_label(resource)
        elif resource.type_ == "file_pattern":
            label = _file_label(resource)
            is_pattern = True
        else:
            raise RuntimeError(f"Unknown resource type '{resource.type_}'")
        return cls(label, resource.path if resource.url else "", resource.provider.name, is_pattern)

    def exists(self):
        """Returns true if the file exists."""
        return bool(self.path)

    def update(self, resource):
        """
        Updates item information.

        Args:
            resource (ProjectItem): a fresh file resource
        """
        self.path = resource.path if resource.url else ""
        self.provider_name = resource.provider.name
        self.is_pattern = resource.type_ == "file_pattern"


class _FileListModel(QAbstractListModel):
    """A model for Importer's file list widget."""

    selected_for_import_state_changed = Signal(bool, str)
    """Emitted when an item has been checked or unchecked for importing."""

    def __init__(self):
        super().__init__()
        self._files = list()

    @property
    def files(self):
        """All model's file items."""
        return self._files

    def existing_files(self):
        """Returns a list of items that exist."""
        return [item for item in self._files if item.exists()]

    def data(self, index, role=Qt.DisplayRole):
        """Returns data associated with given role at given index."""
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self._files[index.row()].label
        if role == Qt.CheckStateRole:
            return Qt.Checked if self._files[index.row()].selected_for_import else Qt.Unchecked
        if role == Qt.DecorationRole:
            path = self._files[index.row()].path
            if path:
                return QFileIconProvider().icon(QFileInfo(path))
        if role == Qt.ToolTipRole:
            item = self._files[index.row()]
            if not item.exists():
                if item.is_pattern:
                    tooltip = f"These files will be generated by {item.provider_name} upon execution."
                else:
                    tooltip = f"This file will be generated by {item.provider_name} upon execution."
            else:
                tooltip = item.path
            return tooltip
        return None

    def flags(self, index):
        """Returns item's flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        item = self._files[index.row()]
        if item.exists():
            return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemNeverHasChildren
        return Qt.ItemNeverHasChildren

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns header information."""
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        return "Source files"

    def find_file(self, label):
        """Returns a file item with given label."""
        for item in self._files:
            if item.label == label:
                return item
        raise RuntimeError(f"Could not find file with label '{label}'")

    def labels(self):
        """Returns a list of file labels."""
        return [item.label for item in self._files]

    def mark_as_nonexistent(self, index):
        """Marks item at index as not existing."""
        self._files[index.row()].path = ""
        self.dataChanged.emit(index, index, [Qt.ToolTipRole])

    def update(self, resources):
        """Updates the model according to given list of resources."""
        self.beginResetModel()
        items = {item.label: item for item in self._files}
        updated = list()
        new = list()
        for resource in resources:
            if resource.type_ not in ("file", "transient_file", "file_pattern"):
                continue
            label = _file_label(resource)
            item = items.get(label)
            if item is not None:
                item.update(resource)
                updated.append(item)
            else:
                new.append(_FileListItem.from_resource(resource))
        self._files = updated + new
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows in the file list."""
        return len(self._files)

    def set_selected(self, label, selected):
        """
        Changes the given item's selection status.

        Args:
            label (str): item's label
            selected (bool): True to select the item, False to deselect
        """
        row = len(list(takewhile(lambda item: item.label != label, self._files)))
        if row < len(self._files):
            item = self._files[row]
            item.selected_for_import = selected
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])

    def setData(self, index, value, role=Qt.EditRole):
        """Sets data in the model."""
        if role != Qt.CheckStateRole or not index.isValid():
            return False
        checked = value == Qt.Checked
        item = self._files[index.row()]
        self.selected_for_import_state_changed.emit(checked, item.label)
        return True

    def set_initial_state(self, labels, selected_list):
        """Fills model with incomplete data; needs a call to :func:`update` to make the model usable."""
        for label, selected in zip(labels, selected_list):
            self._files.append(_FileListItem(label, label, ""))
            self._files[-1].selected_for_import = selected
