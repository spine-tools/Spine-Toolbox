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
Export item's settings window for .gdx export.

:author: A. Soininen (VTT)
:date:   9.9.2019
"""

from copy import deepcopy
import enum
from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QDialogButtonBox, QMessageBox, QWidget
import spinetoolbox.spine_io.exporters.gdx as gdx
from ..list_utils import move_list_elements, move_selected_elements_by
from ..settings_state import SettingsState
from .parameter_index_settings_window import ParameterIndexSettingsWindow
from .parameter_merging_settings_window import ParameterMergingSettingsWindow


class State(enum.Enum):
    """Gdx Export Settings window state"""

    OK = enum.auto()
    """Settings are ok."""
    BAD_INDEXING = enum.auto()
    """Not all indexed parameters are set up correctly."""


class GdxExportSettings(QWidget):
    """A setting window for exporting .gdx files."""

    reset_requested = Signal(str)
    """Emitted when Reset Defaults button has been clicked."""
    settings_accepted = Signal(str)
    """Emitted when the OK button has been clicked."""
    settings_rejected = Signal(str)
    """Emitted when the Cancel button has been clicked."""

    def __init__(
        self,
        settings,
        indexing_settings,
        new_indexing_domains,
        merging_settings,
        new_merging_domains,
        database_path,
        parent,
    ):
        """
        Args:
            settings (Settings): export settings
            indexing_settings (dict): indexing domain information for indexed parameter values
            new_indexing_domains (list): list of additional domains needed for indexed parameter
            merging_settings (dict): parameter merging settings
            new_merging_domains (list): list of additional domains needed for parameter merging
            database_path (str): database URL
            parent (QWidget): a parent widget
        """
        from ..ui.gdx_export_settings import Ui_Form

        super().__init__(parent=parent, f=Qt.Window)
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.setWindowTitle("Gdx Export settings    -- {} --".format(database_path))
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._database_path = database_path
        self._ui.button_box.accepted.connect(self._accept)
        self._ui.button_box.rejected.connect(self._reject)
        self._ui.button_box.clicked.connect(self._reset_settings)
        self._ui.button_box.button(QDialogButtonBox.RestoreDefaults).setToolTip(
            "Reset all settings\nby reloading the database."
        )
        self._ui.set_move_up_button.clicked.connect(self._move_sets_up)
        self._ui.set_move_down_button.clicked.connect(self._move_sets_down)
        self._populate_global_parameters_combo_box(settings)
        self._ui.global_parameters_combo_box.currentIndexChanged[str].connect(self._update_global_parameters_domain)
        self._ui.record_sort_alphabetic.clicked.connect(self._sort_records_alphabetically)
        self._ui.record_move_up_button.clicked.connect(self._move_records_up)
        self._ui.record_move_down_button.clicked.connect(self._move_records_down)
        self._settings = settings
        set_list_model = GAMSSetListModel(settings)
        self._ui.set_list_view.setModel(set_list_model)
        record_list_model = GAMSRecordListModel()
        self._ui.record_list_view.setModel(record_list_model)
        self._ui.set_list_view.selectionModel().selectionChanged.connect(self._populate_set_contents)
        self._ui.open_indexed_parameter_settings_button.clicked.connect(self._show_indexed_parameter_settings)
        self._ui.open_parameter_merging_settings_button.clicked.connect(self._show_parameter_merging_settings)
        self._indexing_settings = indexing_settings
        self._new_domains_for_indexing = new_indexing_domains
        self._indexed_parameter_settings_window = None
        self._merging_settings = merging_settings
        self._new_domains_for_merging = new_merging_domains
        self._parameter_merging_settings_window = None
        self._state = State.OK
        self._check_state()

    @property
    def settings(self):
        """the settings object"""
        return self._settings

    @property
    def indexing_settings(self):
        """indexing settings dict"""
        return self._indexing_settings

    @property
    def indexing_domains(self):
        """list of additional domains needed for indexing"""
        return self._new_domains_for_indexing

    @property
    def merging_settings(self):
        """dictionary of merging settings"""
        return self._merging_settings

    @property
    def merging_domains(self):
        """list of additional domains needed for parameter merging"""
        return self._new_domains_for_merging

    def reset_settings(self, settings, indexing_settings, new_indexing_domains, merging_settings, new_merging_domains):
        """Resets all settings."""
        if self._indexed_parameter_settings_window is not None:
            self._indexed_parameter_settings_window.close()
            self._indexed_parameter_settings_window = None
        if self._parameter_merging_settings_window is not None:
            self._parameter_merging_settings_window.close()
            self._parameter_merging_settings_window = None
        self._ui.global_parameters_combo_box.clear()
        self._populate_global_parameters_combo_box(settings)
        self._settings = settings
        self._ui.set_list_view.setModel(GAMSSetListModel(settings))
        self._ui.set_list_view.selectionModel().selectionChanged.connect(self._populate_set_contents)
        self._ui.record_list_view.setModel(GAMSRecordListModel())
        self._indexing_settings = indexing_settings
        self._new_domains_for_indexing = new_indexing_domains
        self._merging_settings = merging_settings
        self._new_domains_for_merging = new_merging_domains
        self._check_state()

    def _check_state(self):
        """Checks if there are parameters in need for indexing."""
        for setting in self.indexing_settings.values():
            if setting.indexing_domain is None:
                self._ui.indexing_status_label.setText(
                    "<span style='color:#ff3333;white-space: pre-wrap;'>Not all parameters correctly indexed.</span>"
                )
                self._state = State.BAD_INDEXING
                break

    def _populate_global_parameters_combo_box(self, settings):
        """(Re)populates the global parameters combo box."""
        self._ui.global_parameters_combo_box.addItem("Nothing selected")
        for domain_name in sorted(settings.sorted_domain_names):
            self._ui.global_parameters_combo_box.addItem(domain_name)
        if settings.global_parameters_domain_name:
            self._ui.global_parameters_combo_box.setCurrentText(settings.global_parameters_domain_name)

    def _update_new_domains_list(self, domains, old_list):
        """Merges entries from new and old domain lists."""
        model = self._ui.set_list_view.model()
        for old_domain in old_list:
            domain_found = False
            for new_domain in domains:
                if old_domain.name == new_domain.name:
                    model.update_domain(new_domain)
                    domain_found = True
                    break
            if not domain_found:
                model.drop_domain(old_domain)
        for new_domain in domains:
            domain_found = False
            for old_domain in old_list:
                if new_domain.name == old_domain.name:
                    domain_found = True
                    break
            if not domain_found:
                model.add_domain(new_domain)
        old_list[:] = list(domains)

    @Slot("QVariant")
    def handle_settings_state_changed(self, state):
        enabled = state != SettingsState.FETCHING
        self._ui.set_group_box.setEnabled(enabled)
        self._ui.contents_group_box.setEnabled(enabled)
        self._ui.misc_control_holder.setEnabled(enabled)
        self._ui.button_box.button(QDialogButtonBox.Ok).setEnabled(enabled)
        self._ui.button_box.button(QDialogButtonBox.RestoreDefaults).setEnabled(enabled)

    @Slot()
    def _accept(self):
        """Emits the settings_accepted signal."""
        if self._state != State.OK:
            QMessageBox.warning(
                self,
                "Bad Parameter Indexing",
                "Parameter indexing not set up correctly. Click 'Indexed parameters...' to open the settings window.",
            )
            return
        self.settings_accepted.emit(self._database_path)
        self.hide()

    @Slot(bool)
    def _move_sets_up(self, checked=False):
        """Moves selected domains and sets up one position."""
        move_selected_elements_by(self._ui.set_list_view, -1)

    @Slot(bool)
    def _move_sets_down(self, checked=False):
        """Moves selected domains and sets down one position."""
        move_selected_elements_by(self._ui.set_list_view, 1)

    @Slot(bool)
    def _move_records_up(self, checked=False):
        """Moves selected records up and position."""
        move_selected_elements_by(self._ui.record_list_view, -1)

    @Slot(bool)
    def _move_records_down(self, checked=False):
        """Moves selected records down on position."""
        move_selected_elements_by(self._ui.record_list_view, 1)

    @Slot()
    def _reject(self):
        """Hides the window."""
        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)
        self.settings_rejected.emit(self._database_path)

    @Slot("QAbstractButton")
    def _reset_settings(self, button):
        """Requests for fresh settings to be read from the database."""
        if self._ui.button_box.standardButton(button) != QDialogButtonBox.RestoreDefaults:
            return
        self.reset_requested.emit(self._database_path)

    @Slot(str)
    def _update_global_parameters_domain(self, text):
        """Updates the global parameters domain name."""
        if text == "Nothing selected":
            index = self._ui.set_list_view.model().index_for_domain(self._settings.global_parameters_domain_name)
            self._settings.global_parameters_domain_name = ""
        else:
            self._settings.global_parameters_domain_name = text
            index = self._ui.set_list_view.model().index_for_domain(text)
        if index.isValid():
            index.model().dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.ToolTipRole])

    @Slot("QItemSelection", "QItemSelection")
    def _populate_set_contents(self, selected, _):
        """Populates the record list by the selected domain's or set's records."""
        selected_indexes = selected.indexes()
        if not selected_indexes:
            return
        set_model = self._ui.set_list_view.model()
        selected_set_name = set_model.data(selected_indexes[0])
        record_keys = self._settings.sorted_record_key_lists(selected_set_name)
        record_model = self._ui.record_list_view.model()
        record_model.reset(record_keys, selected_set_name)

    @Slot(bool)
    def _sort_records_alphabetically(self, _):
        """Sorts the lists of set records alphabetically."""
        model = self._ui.record_list_view.model()
        model.sort_alphabetically()

    @Slot(bool)
    def _show_indexed_parameter_settings(self, _):
        """Shows the indexed parameter settings window."""
        if self._indexed_parameter_settings_window is None:
            available_domains = dict()
            for domain_name, metadata in zip(self._settings.sorted_domain_names, self._settings.domain_metadatas):
                if metadata.is_exportable():
                    record_keys = self._settings.sorted_record_key_lists(domain_name)
                    keys = [key_list[0] for key_list in record_keys]
                    if not metadata.is_additional:
                        available_domains[domain_name] = keys
            new_domains = dict()
            for domain in self._new_domains_for_indexing:
                new_domains[domain.name] = [record.keys[0] for record in domain.records]
            indexing_settings = deepcopy(self._indexing_settings)
            self._indexed_parameter_settings_window = ParameterIndexSettingsWindow(
                indexing_settings, available_domains, new_domains, self._database_path, self
            )
            self._indexed_parameter_settings_window.settings_approved.connect(self._approve_parameter_indexing_settings)
            self._indexed_parameter_settings_window.settings_rejected.connect(
                self._dispose_parameter_indexing_settings_window
            )
            self._ui.record_list_view.model().domain_records_reordered.connect(
                self._indexed_parameter_settings_window.reorder_indexes
            )
        self._indexed_parameter_settings_window.show()

    @Slot(bool)
    def _show_parameter_merging_settings(self, _):
        """Shows the parameter merging settings window."""
        if self._parameter_merging_settings_window is None:
            self._parameter_merging_settings_window = ParameterMergingSettingsWindow(
                self._merging_settings, self._database_path, self
            )
            self._parameter_merging_settings_window.settings_approved.connect(self._parameter_merging_approved)
            self._parameter_merging_settings_window.settings_rejected.connect(self._dispose_parameter_merging_window)
        self._parameter_merging_settings_window.show()

    @Slot()
    def _approve_parameter_indexing_settings(self):
        """Gathers settings from the indexed parameters settings window."""
        self._indexing_settings = self._indexed_parameter_settings_window.indexing_settings
        new_domains = self._indexed_parameter_settings_window.new_domains
        self._update_new_domains_list(new_domains, self._new_domains_for_indexing)
        self._state = State.OK
        self._ui.indexing_status_label.setText("")

    @Slot()
    def _parameter_merging_approved(self):
        """Collects merging settings from the parameter merging window."""
        self._merging_settings = self._parameter_merging_settings_window.merging_settings
        new_domains = list(map(gdx.merging_domain, self._merging_settings.values()))
        self._update_new_domains_list(new_domains, self._new_domains_for_merging)

    @Slot()
    def _dispose_parameter_indexing_settings_window(self):
        """Removes references to the indexed parameter settings window."""
        self._indexed_parameter_settings_window = None

    @Slot()
    def _dispose_parameter_merging_window(self):
        """Removes references to the parameter merging settings window."""
        self._parameter_merging_settings_window = None


class GAMSSetListModel(QAbstractListModel):
    """
    A model to configure the domain and set name lists in gdx export settings.

    This model combines the domain and set name lists into a single list.
    The two 'parts' are differentiated by different background colors.
    Items from each part cannot be mixed with the other.
    Both the ordering of the items within each list as well as their exportability flags are handled here.
    """

    def __init__(self, settings):
        """
        Args:
            settings (spine_io.exporters.gdx.Settings): settings whose domain and set name lists should be modelled
        """
        super().__init__()
        self._settings = settings

    def add_domain(self, domain):
        """Adds a new domain."""
        if self._settings.add_or_replace_domain(domain, gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True)):
            first = len(self._settings.sorted_domain_names)
            last = first
            self.beginInsertRows(QModelIndex(), first, last)
            self.endInsertRows()

    def drop_domain(self, domain):
        """Removes a domain."""
        index = self._settings.domain_index(domain)
        self.beginRemoveRows(QModelIndex(), index, index)
        self._settings.del_domain_at(index)
        self.endRemoveRows()

    def update_domain(self, domain):
        """Updates an existing domain."""
        index = self._settings.domain_index(domain)
        self._settings.update_domain(domain)
        cell = self.index(index, 0)
        self.dataChanged.emit(cell, cell, [Qt.DisplayRole])

    def data(self, index, role=Qt.DisplayRole):
        """
        Returns the value for given role at given index.

        Qt.DisplayRole returns the name of the domain or set
        while Qt.CheckStateRole returns whether the exportable flag has been set or not.
        Qt.BackgroundRole gives the item's background depending whether it is a domain or a set.

        Args:
            index (QModelIndex): an index to the model
            role (int): the query's role

        Returns:
            the requested value or `None`
        """
        if not index.isValid() or index.column() != 0 or index.row() >= self.rowCount():
            return None
        row = index.row()
        domain_count = len(self._settings.sorted_domain_names)
        if role == Qt.DisplayRole:
            if row < domain_count:
                return self._settings.sorted_domain_names[row]
            return self._settings.sorted_set_names[row - domain_count]
        if role == Qt.BackgroundRole:
            if row < domain_count:
                return QColor(Qt.lightGray)
            return None
        if role == Qt.CheckStateRole:
            if row < domain_count:
                checked = self._settings.domain_metadatas[row].is_exportable()
            else:
                checked = self._settings.set_metadatas[row - domain_count].is_exportable()
            return Qt.Checked if checked else Qt.Unchecked
        if role == Qt.ToolTipRole:
            if row < domain_count:
                exportable = self._settings.domain_metadatas[row].exportable
            else:
                exportable = self._settings.set_metadatas[row - domain_count].exportable
            if exportable == gdx.ExportFlag.FORCED_NON_EXPORTABLE:
                return "Domain is the global parameter domain\n and cannot be exported as is."
            if exportable == gdx.ExportFlag.FORCED_EXPORTABLE:
                return "Domain is used for parameter indexing\n and must be exported."
        return None

    def flags(self, index):
        """Returns an item's flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns an empty string for horizontal header and row number for vertical header."""
        if orientation == Qt.Horizontal:
            return ""
        return section + 1

    def index_for_domain(self, domain_name):
        """Returns the model index for a domain."""
        for i, name in enumerate(self._settings.sorted_domain_names):
            if name == domain_name:
                return self.index(i, 0)
        return QModelIndex()

    def is_domain(self, index):
        """Returns True if index points to a domain name, otherwise returns False."""
        if not index.isValid():
            return False
        return index.row() < len(self._settings.sorted_domain_names)

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        """
        Moves the domain and set names around.

        The names cannot be mixed between domains and sets.

        Args:
            sourceParent (QModelIndex): parent from which the rows are moved
            sourceRow (int): index of the first row to be moved
            count (int): number of rows to move
            destinationParent (QModelIndex): parent to which the rows are moved
            destinationChild (int): index where to insert the moved rows

        Returns:
            True if the operation was successful, False otherwise
        """
        row_count = self.rowCount()
        if destinationChild < 0 or destinationChild >= row_count:
            return False
        last_source_row = sourceRow + count - 1
        domain_count = len(self._settings.sorted_domain_names)
        # Cannot move domains to ordinary sets and vice versa.
        if sourceRow < domain_count <= last_source_row:
            return False
        if sourceRow < domain_count <= destinationChild:
            return False
        if destinationChild < domain_count <= sourceRow:
            return False
        row_after = destinationChild if sourceRow > destinationChild else destinationChild + 1
        self.beginMoveRows(sourceParent, sourceRow, last_source_row, destinationParent, row_after)
        if sourceRow < domain_count:
            names = self._settings.sorted_domain_names
            metadatas = self._settings.domain_metadatas
        else:
            names = self._settings.sorted_set_names
            metadatas = self._settings.set_metadatas
            sourceRow -= domain_count
            last_source_row -= domain_count
            destinationChild -= domain_count
        names[:] = move_list_elements(names, sourceRow, last_source_row, destinationChild)
        metadatas[:] = move_list_elements(metadatas, sourceRow, last_source_row, destinationChild)
        self.endMoveRows()
        return True

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows."""
        return len(self._settings.sorted_domain_names) + len(self._settings.sorted_set_names)

    def setData(self, index, value, role=Qt.EditRole):
        """Sets the exportable flag status for given row."""
        if not index.isValid() or role != Qt.CheckStateRole:
            return False
        row = index.row()
        domain_count = len(self._settings.sorted_domain_names)
        if row < domain_count:
            if self._settings.domain_metadatas[row].is_forced():
                return False
            exportable = gdx.ExportFlag.EXPORTABLE if value == Qt.Checked else gdx.ExportFlag.NON_EXPORTABLE
            self._settings.domain_metadatas[row].exportable = exportable
        else:
            if self._settings.set_metadatas[row - domain_count].is_forced():
                return False
            exportable = gdx.ExportFlag.EXPORTABLE if value == Qt.Checked else gdx.ExportFlag.NON_EXPORTABLE
            self._settings.set_metadatas[row - domain_count].exportable = exportable
        self.dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.ToolTipRole])
        return True


class GAMSRecordListModel(QAbstractListModel):
    """A model to manage record ordering within domains and sets."""

    domain_records_reordered = Signal(str, int, int, int)

    def __init__(self):
        super().__init__()
        self._records = list()
        self._set_name = ""

    def data(self, index, role=Qt.DisplayRole):
        """With `role == Qt.DisplayRole` returns the record's keys as comma separated string."""
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            keys = self._records[index.row()]
            return ", ".join(keys)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns row and column header data."""
        if orientation == Qt.Horizontal:
            return ''
        return section + 1

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        """
        Moves the records around.

        Args:
            sourceParent (QModelIndex): parent from which the rows are moved
            sourceRow (int): index of the first row to be moved
            count (int): number of rows to move
            destinationParent (QModelIndex): parent to which the rows are moved
            destinationChild (int): index where to insert the moved rows

        Returns:
            True if the operation was successful, False otherwise
        """
        row_count = self.rowCount()
        if destinationChild < 0 or destinationChild >= row_count:
            return False
        last_source_row = sourceRow + count - 1
        row_after = destinationChild if sourceRow > destinationChild else destinationChild + 1
        self.beginMoveRows(sourceParent, sourceRow, last_source_row, destinationParent, row_after)
        self._records[:] = move_list_elements(self._records, sourceRow, last_source_row, destinationChild)
        self.endMoveRows()
        if len(self._records[0]) == 1:
            self.domain_records_reordered.emit(self._set_name, sourceRow, last_source_row, destinationChild)
        return True

    def reset(self, records, set_name):
        """Resets the model's record data."""
        self._set_name = set_name
        self.beginResetModel()
        self._records = records
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Return the number of records in the model."""
        return len(self._records)

    def sort_alphabetically(self):
        self._records = sorted(self._records)
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._records) - 1, 0)
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])
