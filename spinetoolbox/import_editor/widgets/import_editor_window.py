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
Contains ImportPreviewWindow class.

:authors: P. Savolainen (VTT), A. Soininen (VTT), P. Vennström (VTT)
:date:    10.6.2019
"""

import os
import json
import fnmatch
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtGui import QGuiApplication, QKeySequence
from PySide2.QtWidgets import (
    QMainWindow,
    QErrorMessage,
    QFileDialog,
    QDialogButtonBox,
    QDockWidget,
    QUndoStack,
    QDialogButtonBox,
    QDialog,
    QVBoxLayout,
    QListWidget,
    QFileDialog,
)
from spinetoolbox.helpers import get_open_file_name_in_last_dir, ensure_window_is_on_screen
from spinetoolbox.config import APPLICATION_PATH
from spine_engine.spine_io.importers.csv_reader import CSVConnector
from spine_engine.spine_io.importers.excel_reader import ExcelConnector
from spine_engine.spine_io.importers.gdx_connector import GdxConnector
from spine_engine.spine_io.importers.json_reader import JSONConnector
from spine_engine.spine_io.importers.datapackage_reader import DataPackageConnector
from spine_engine.spine_io.gdx_utils import find_gams_directory
from ..connection_manager import ConnectionManager
from ..commands import RestoreMappingsFromDict
from .import_editor import ImportEditor
from .import_mapping_options import ImportMappingOptions
from .import_mappings import ImportMappings
from .importer_specification_toolbar import ImporterSpecificationToolbar


_CONNECTOR_NAME_TO_CLASS = {
    "CSVConnector": CSVConnector,
    "ExcelConnector": ExcelConnector,
    "GdxConnector": GdxConnector,
    "JSONConnector": JSONConnector,
    "DataPackageConnector": DataPackageConnector,
}


class ImportEditorWindow(QMainWindow):
    """A QMainWindow to let users define Mappings for an Importer item."""

    connection_failed = Signal(str)
    specification_updated = Signal(dict)

    def __init__(self, toolbox, specification, filepath=None):
        """
        Args:
            toolbox (QMainWindow): ToolboxUI class
            specification (ImporterSpecification)
            filepath (str, optional): Importee path
        """
        from ..ui.import_editor_window import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        super().__init__(parent=toolbox, flags=Qt.Window)
        self._toolbox = toolbox
        self._specification = specification
        self._app_settings = self._toolbox.qsettings()
        self._connection_manager = None
        self._memoized_connectors = {}
        self._editor = None
        self._undo_stack = QUndoStack()
        self._ui_error = QErrorMessage(self)
        self._ui_error.setWindowTitle("Error")
        self._ui_error.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        self._insert_undo_redo_actions()
        self._import_mappings = ImportMappings(self._ui, self._undo_stack)
        self._import_mapping_options = ImportMappingOptions(self._ui, self._undo_stack)
        self._import_mappings.mapping_selection_changed.connect(
            self._import_mapping_options.set_mapping_specification_model
        )
        self._import_mapping_options.about_to_undo.connect(self._import_mappings.focus_on_changing_specification)
        self._size = None
        self.takeCentralWidget()
        self._spec_toolbar = ImporterSpecificationToolbar(self)
        self.addToolBar(Qt.TopToolBarArea, self._spec_toolbar)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Import Editor")
        self.settings_group = "mappingPreviewWindow"
        self.apply_classic_ui_style()
        self.restore_ui()
        self._button_box = QDialogButtonBox(self)
        self._button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self._ui.statusbar.addPermanentWidget(self._button_box)
        self._ui.statusbar.layout().setContentsMargins(6, 6, 6, 6)
        self._button_box.button(QDialogButtonBox.Ok).clicked.connect(self.save_and_close)
        self._button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self._ui.export_mappings_action.triggered.connect(self.export_mapping_to_file)
        self._ui.import_mappings_action.triggered.connect(self.import_mapping_from_file)
        self._ui.close_action.triggered.connect(self.close)
        self.connection_failed.connect(self.show_error)
        self.specification_updated.connect(self._add_or_update_specification)
        self._ui.actionLoad_file.triggered.connect(self._show_open_file_dialog)
        self._ui.actionSwitch_connector.triggered.connect(self._switch_connector)
        if filepath:
            self.start_ui(filepath)

    @Slot(bool)
    def _show_open_file_dialog(self, _=False):
        filter_ = ";;".join([conn.FILE_EXTENSIONS for conn in _CONNECTOR_NAME_TO_CLASS.values()])
        key = f"selectInputDataFileFor{self._specification.name if self._specification else None}"
        filepath, _ = get_open_file_name_in_last_dir(
            self._toolbox.qsettings(),
            key,
            self,
            "Select an input data file to define the specification",
            APPLICATION_PATH,
            filter_=filter_,
        )
        if not filepath:
            return
        if self._connection_manager:
            self._connection_manager.close_connection()
        self.start_ui(filepath)

    @Slot(bool)
    def _switch_connector(self, _=False):
        filepath = self._connection_manager.source
        if self._specification:
            self._specification.mapping.pop("source_type", None)
        self._memoized_connectors.pop(filepath, None)
        self.start_ui(filepath)

    def _get_connector_from_mapping(self, filepath):
        if not self._specification:
            return None
        mapping = self._specification.mapping
        source_type = mapping.get("source_type")
        if source_type is None:
            return None
        connector = _CONNECTOR_NAME_TO_CLASS[source_type]
        file_extensions = connector.FILE_EXTENSIONS.split(";;")
        if not any(fnmatch.fnmatch(filepath, ext) for ext in file_extensions):
            return None
        return connector

    def start_ui(self, filepath):
        """
        Args:
            filepath (str): Importee path
        """
        connector = self._get_connector_from_mapping(filepath)
        if connector is None:
            # Ask user
            connector = self._get_connector(filepath)
            if not connector:
                if not self.isVisible():
                    self.close()
                return
        self._ui.actionSwitch_connector.setEnabled(True)
        connector_settings = {"gams_directory": _gams_system_directory(self._toolbox)}
        self._connection_manager = ConnectionManager(connector, connector_settings)
        self._connection_manager.source = filepath
        mapping = self._specification.mapping if self._specification else {}
        self._editor = ImportEditor(self._ui, self._ui_error, self._undo_stack, self._connection_manager, mapping)
        self._connection_manager.connection_failed.connect(self.connection_failed.emit)
        self._connection_manager.error.connect(self.show_error)
        self._ui.source_data_table.set_undo_stack(self._undo_stack, self._editor.select_table)
        self._import_mappings.mapping_selection_changed.connect(self._editor.set_model)
        self._import_mappings.mapping_selection_changed.connect(self._editor.set_mapping)
        self._import_mappings.mapping_data_changed.connect(self._editor.set_mapping)
        self._import_mappings.about_to_undo.connect(self._editor.select_table)
        self._editor.source_table_selected.connect(self._import_mappings.set_mappings_model)
        self._editor.source_table_selected.connect(self._ui.source_data_table.horizontalHeader().set_source_table)
        self._editor.source_table_selected.connect(self._ui.source_data_table.verticalHeader().set_source_table)
        self._editor.preview_data_updated.connect(self._import_mapping_options.set_num_available_columns)
        self._connection_manager.connection_ready.connect(self._handle_connection_ready)
        self._connection_manager.init_connection()

    @Slot(bool)
    def _handle_connection_ready(self):
        self._ui.export_mappings_action.setEnabled(True)
        self._ui.import_mappings_action.setEnabled(True)
        self._ui.actionLoad_file.setText("Switch file...")

    def _get_connector(self, filepath):
        """Shows a QDialog to select a connector for the given source file.

        Args:
            filepath (str): Path of the file acting as an importee

        Returns:
            Asynchronous data reader class for the given importee
        """
        if filepath in self._memoized_connectors:
            return self._memoized_connectors[filepath]
        connector_list = list(_CONNECTOR_NAME_TO_CLASS.values())
        connector_names = [c.DISPLAY_NAME for c in connector_list]
        dialog = QDialog(self)
        dialog.setLayout(QVBoxLayout())
        connector_list_wg = QListWidget()
        connector_list_wg.addItems(connector_names)
        # Set current item in `connector_list_wg` based on file extension
        row = None
        for k, conn in enumerate(connector_list):
            file_extensions = conn.FILE_EXTENSIONS.split(";;")
            if any(fnmatch.fnmatch(filepath, ext) for ext in file_extensions):
                row = k
        if row is not None:
            connector_list_wg.setCurrentRow(row)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(dialog.accept)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(dialog.reject)
        connector_list_wg.doubleClicked.connect(dialog.accept)
        dialog.layout().addWidget(connector_list_wg)
        dialog.layout().addWidget(button_box)
        _dirname, filename = os.path.split(filepath)
        dialog.setWindowTitle("Select connector for '{}'".format(filename))
        answer = dialog.exec_()
        if not answer:
            return None
        row = connector_list_wg.currentIndex().row()
        connector = self._memoized_connectors[filepath] = connector_list[row]
        return connector

    @Slot(dict)
    def _add_or_update_specification(self, definition):
        new_specification = self._toolbox.load_specification(definition)
        if new_specification is None:
            # Happens when toolbox doesn't find the spec factory (should never happen)
            return
        if self._specification is not None and new_specification.is_equivalent(self._specification):
            # Nothing changed
            return
        if self._specification is None or new_specification.name != self._specification.name:
            # The user is creating a new spec, either from scratch or by changing the name of an existing one
            self._toolbox.add_specification(new_specification)
        else:
            # The user is modifying an existing spec, while conserving the name
            new_specification.definition_file_path = self._specification.definition_file_path
            self._toolbox.update_specification(new_specification)

    def _insert_undo_redo_actions(self):
        undo_action = self._undo_stack.createUndoAction(self)
        redo_action = self._undo_stack.createRedoAction(self)
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action.setShortcuts(QKeySequence.Redo)
        actions = self._ui.edit_menu.actions()
        before = actions[0] if actions else None
        self._ui.edit_menu.insertAction(before, undo_action)
        self._ui.edit_menu.insertAction(before, redo_action)

    @Slot(str)
    def show_error(self, message):
        self._ui_error.showMessage(message)

    def restore_dock_widgets(self):
        """Docks all floating and or hidden QDockWidgets back to the window."""
        for dock in self.findChildren(QDockWidget):
            dock.setVisible(True)
            dock.setFloating(False)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def begin_style_change(self):
        """Begins a style change operation."""
        self._size = self.size()
        self.restore_dock_widgets()

    def end_style_change(self):
        """Ends a style change operation."""
        qApp.processEvents()  # pylint: disable=undefined-variable
        self.resize(self._size)

    def apply_classic_ui_style(self):
        """Applies the classic UI style."""
        self.begin_style_change()
        docks = (self._ui.dockWidget_sources, self._ui.dockWidget_mappings)
        self.splitDockWidget(*docks, Qt.Horizontal)
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.9 * width, 0.1 * width], Qt.Horizontal)
        docks = (self._ui.dockWidget_sources, self._ui.dockWidget_source_data)
        self.splitDockWidget(*docks, Qt.Vertical)
        height = sum(d.size().height() for d in docks)
        self.resizeDocks(docks, [0.1 * height, 0.9 * height], Qt.Vertical)
        self.splitDockWidget(self._ui.dockWidget_sources, self._ui.dockWidget_source_options, Qt.Horizontal)
        self.splitDockWidget(self._ui.dockWidget_mappings, self._ui.dockWidget_mapping_options, Qt.Vertical)
        self.splitDockWidget(self._ui.dockWidget_mapping_options, self._ui.dockWidget_mapping_spec, Qt.Vertical)
        docks = (self._ui.dockWidget_mapping_options, self._ui.dockWidget_mapping_spec)
        height = sum(d.size().height() for d in docks)
        self.resizeDocks(docks, [0.1 * height, 0.9 * height], Qt.Vertical)
        self.end_style_change()

    def import_mapping_from_file(self):
        """Imports mapping spec from a user selected .json file to the preview window."""
        start_dir = self._toolbox.project().project_dir
        # noinspection PyCallByClass
        filename = QFileDialog.getOpenFileName(
            self, "Import mapping specification", start_dir, "Mapping options (*.json)"
        )
        if not filename[0]:
            return
        with open(filename[0]) as file_p:
            try:
                settings = json.load(file_p)
            except json.JSONDecodeError:
                self._ui.statusbar.showMessage(f"Could not open {filename[0]}", 10000)
                return
        expected_options = ("table_mappings", "table_types", "table_row_types", "table_options", "selected_tables")
        if not isinstance(settings, dict) or not any(key in expected_options for key in settings.keys()):
            self._ui.statusbar.showMessage(f"{filename[0]} does not contain mapping options", 10000)
        self._undo_stack.push(RestoreMappingsFromDict(self._editor, settings))
        self._ui.statusbar.showMessage(f"Mapping loaded from {filename[0]}", 10000)

    def export_mapping_to_file(self):
        """Exports all mapping specs in current preview window to .json file."""
        start_dir = self._toolbox.project().project_dir
        # noinspection PyCallByClass
        filename = QFileDialog.getSaveFileName(
            self, "Export mapping spec to a file", start_dir, "Mapping options (*.json)"
        )
        if not filename[0]:
            return
        with open(filename[0], 'w') as file_p:
            settings = self._editor.get_settings_dict()
            json.dump(settings, file_p)
        self._ui.statusbar.showMessage(f"Mapping saved to: {filename[0]}", 10000)

    def save_and_close(self):
        """Save spec and close window."""
        name = self._spec_toolbar.name()
        if not name:
            self.show_error("Please enter a name for the specification.")
        mapping = self._editor.get_settings_dict() if self._editor else {}
        description = self._spec_toolbar.description()
        definition = {"name": name, "mapping": mapping, "description": description, "item_type": "Importer"}
        self.specification_updated.emit(definition)
        self.close()

    def restore_ui(self):
        """Restore UI state from previous session."""
        app_settings = self._app_settings
        app_settings.beginGroup(self.settings_group)
        window_size = app_settings.value("windowSize")
        window_pos = app_settings.value("windowPosition")
        window_state = app_settings.value("windowState")
        window_maximized = app_settings.value("windowMaximized", defaultValue='false')
        n_screens = app_settings.value("n_screens", defaultValue=1)
        app_settings.endGroup()
        original_size = self.size()
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)
        ensure_window_is_on_screen(self, original_size)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)

    def closeEvent(self, event=None):
        """Handles close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if self._editor:
            self._editor.close_connection()
        app_settings = self._app_settings
        app_settings.beginGroup(self.settings_group)
        app_settings.setValue("windowSize", self.size())
        app_settings.setValue("windowPosition", self.pos())
        app_settings.setValue("windowState", self.saveState(version=1))
        app_settings.setValue("windowMaximized", self.windowState() == Qt.WindowMaximized)
        app_settings.setValue("n_screens", len(QGuiApplication.screens()))
        app_settings.endGroup()
        if event:
            event.accept()


def _gams_system_directory(toolbox):
    """Returns GAMS system path from Toolbox settings or None if GAMS default is to be used."""
    path = toolbox.qsettings().value("appSettings/gamsPath", defaultValue=None)
    if not path:
        path = find_gams_directory()
    if path is not None and os.path.isfile(path):
        path = os.path.dirname(path)
    return path
