######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
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

from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QWidget


def _move_selected_elements_by(list_view, delta):
    """
    Moves selected items in a QListView by given delta.

    Args:
        list_view (QListView): a list view
        delta (int): positive values move the items up, negative down
    """
    selection_model = list_view.selectionModel()
    selected_rows = sorted(selection_model.selectedRows())
    if not selected_rows:
        return
    first_row = selected_rows[0].row()
    contiguous_selections = [[first_row, 1]]
    current_contiguous_chunk = contiguous_selections[0]
    for row in selected_rows[1:]:
        if row == current_contiguous_chunk[0] + 1:
            current_contiguous_chunk[1] += 1
        else:
            contiguous_selections.append((row, 1))
            current_contiguous_chunk = contiguous_selections[-1]
    model = list_view.model()
    for chunk in contiguous_selections:
        model.moveRows(QModelIndex(), chunk[0], chunk[1], QModelIndex(), chunk[0] + delta)


class GdxExportSettings(QWidget):
    """
    A setting window for exporting .gdx files.

    Attributes:
        window_closing (Signal): fired when the settings window is closing
    """

    window_closing = Signal()

    def __init__(self, settings, database_path, parent):
        """
        Args:
            settings (Settings): export settings
            parent (QWidget): a parent widget
        """
        from ..ui.gdx_export_settings import Ui_Form

        # super().__init__(parent)
        super().__init__(parent=parent, f=Qt.Window)
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.setWindowTitle("Gdx Export settings    -- {} --".format(database_path))
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._ui.button_box.rejected.connect(self.close)
        self._ui.set_move_up_button.clicked.connect(self._move_sets_up)
        self._ui.set_move_down_button.clicked.connect(self._move_sets_down)
        self._ui.set_as_global_parameters_object_class_button.clicked.connect(
            self._set_selected_set_as_global_parameters_object_class
        )
        self._ui.record_move_up_button.clicked.connect(self._move_records_up)
        self._ui.record_move_down_button.clicked.connect(self._move_records_down)
        self._ui.global_parameters_object_class_line_edit.setText(settings.global_parameters_domain_name)
        self._ui.global_parameters_object_class_line_edit.textChanged.connect(
            self._update_global_parameters_object_class
        )
        self._settings = settings
        set_list_model = GAMSSetListModel(settings)
        self._ui.set_list_view.setModel(set_list_model)
        record_list_model = GAMSRecordListModel()
        self._ui.record_list_view.setModel(record_list_model)
        self._ui.set_list_view.selectionModel().selectionChanged.connect(self._populate_set_contents)
        self._ui.set_list_view.selectionModel().currentChanged.connect(self._update_as_global_button_enabled_state)

    @property
    def settings(self):
        """the settings object"""
        return self._settings

    @property
    def button_box(self):
        """window's dialog button box containing the OK and Cancel buttons"""
        return self._ui.button_box

    @Slot(bool)
    def _move_sets_up(self, checked=False):
        """Moves selected domains and sets up one position."""
        _move_selected_elements_by(self._ui.set_list_view, -1)

    @Slot(bool)
    def _move_sets_down(self, checked=False):
        """Moves selected domains and sets down one position."""
        _move_selected_elements_by(self._ui.set_list_view, 1)

    @Slot(bool)
    def _move_records_up(self, checked=False):
        """Moves selected records up and position."""
        _move_selected_elements_by(self._ui.record_list_view, -1)

    @Slot(bool)
    def _move_records_down(self, checked=False):
        """Moves selected records down on position."""
        _move_selected_elements_by(self._ui.record_list_view, 1)

    @Slot("QModelIndex", "QModelIndex")
    def _update_as_global_button_enabled_state(self, current, previous):
        """Enables or disables the *As Global* button depending if the selected element is a domain or a set."""
        model = current.model()
        is_previous_domain = model.is_domain(previous)
        is_current_domain = model.is_domain(current)
        if is_current_domain != is_previous_domain:
            self._ui.set_as_global_parameters_object_class_button.setEnabled(is_current_domain)

    @Slot(bool)
    def _set_selected_set_as_global_parameters_object_class(self, checked=False):
        """Sets the currently selected domain as the global parameters object class."""
        selection_model = self._ui.set_list_view.selectionModel()
        current_index = selection_model.currentIndex()
        model = current_index.model()
        if not current_index.isValid() or not model.is_domain(current_index):
            return
        set_name = current_index.data()
        self._ui.global_parameters_object_class_line_edit.setText(set_name)
        model.setData(current_index, Qt.Unchecked, Qt.CheckStateRole)

    @Slot(str)
    def _update_global_parameters_object_class(self, text):
        """Sets the global parameters domain name to `text` in the settings."""
        self._settings.global_parameters_domain_name = text

    @Slot("QItemSelection", "QItemSelection")
    def _populate_set_contents(self, selected, deselected):
        """Populates the record list by the selected domain's or set's records."""
        selected_indexes = selected.indexes()
        if not selected_indexes:
            return
        set_model = self._ui.set_list_view.model()
        selected_set_name = set_model.data(selected_indexes[0])
        record_keys = self._settings.sorted_record_key_lists(selected_set_name)
        record_model = self._ui.record_list_view.model()
        record_model.reset(record_keys)

    def closeEvent(self, event):
        self.window_closing.emit()
        super().closeEvent(event)


def _move_list_elements(originals, first, last, target):
    """
    Moves elements in a list.

    Args:
        originals (list): a list
        first (int): index of the first element to move
        last (int): index of the last element to move
        target (int): index where the elements `[first:last]` should be inserted

    Return:
        a new list with the elements moved
    """
    trashable = list(originals)
    elements_to_move = list(originals[first : last + 1])
    del trashable[first : last + 1]
    elements_that_come_before = trashable[:target]
    elements_that_come_after = trashable[target:]
    brave_new_list = elements_that_come_before + elements_to_move + elements_that_come_after
    return brave_new_list


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
                checked = self._settings.domain_exportable_flags[row]
            else:
                checked = self._settings.set_exportable_flags[row - domain_count]
            return Qt.Checked if checked else Qt.Unchecked
        return None

    def flags(self, index):
        """Returns an item's flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns an empty string for horizontal header and row number for vertical header."""
        if orientation == Qt.Horizontal:
            return ''
        return section + 1

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
            export_flags = self._settings.domain_exportable_flags
        else:
            names = self._settings.sorted_set_names
            export_flags = self._settings.set_exportable_flags
            sourceRow -= domain_count
            last_source_row -= domain_count
            destinationChild -= domain_count
        names[:] = _move_list_elements(names, sourceRow, last_source_row, destinationChild)
        export_flags[:] = _move_list_elements(export_flags, sourceRow, last_source_row, destinationChild)
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
            self._settings.domain_exportable_flags[row] = value != Qt.Unchecked
        else:
            self._settings.set_exportable_flags[row - domain_count] = value != Qt.Unchecked
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])
        return True


class GAMSRecordListModel(QAbstractListModel):
    """A model to manage record ordering within domains and sets."""

    def __init__(self):
        super().__init__()
        self._records = list()

    def data(self, index, role=Qt.DisplayRole):
        """With `role == Qt.DisplayRole` returns the record's keys as comma separated string."""
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            keys = self._records[index.row()]
            return ', '.join(keys)
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
        self._records[:] = _move_list_elements(self._records, sourceRow, last_source_row, destinationChild)
        self.endMoveRows()
        return True

    def reset(self, records):
        """Resets the model's record data."""
        self.beginResetModel()
        self._records = records
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Return the number of records in the model."""
        return len(self._records)
