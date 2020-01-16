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
A model for the auto filter menu widget.

:authors: M. Marin (KTH)
:date:   7.10.2019
"""

import re
from PySide2.QtCore import Qt, Signal, Slot, QStringListModel, QModelIndex


class AutoFilterMenuItem:
    """An item for the auto filter menu."""

    def __init__(self, checked, value, classes=()):
        """Init class.

        Args:
            checked (int): the checked status, checked if not filtered
            value: the value
            classes (tuple): the entity classes where the value is found
        """
        self.checked = checked
        self.value = value
        self.classes = classes

    def __repr__(self):
        return str(self.__dict__)


class AutoFilterMenuItemModel(QStringListModel):
    """Base class for filter menu widget models."""

    def __init__(self, parent=None, fetch_step=32):
        """Init class."""
        super().__init__(parent)
        self._data = []
        self._unfetched = []
        self._fetch_step = fetch_step

    def canFetchMore(self, parent=QModelIndex()):
        """Returns whether or not there're unfetched rows."""
        return bool(self._unfetched)

    def fetchMore(self, parent=QModelIndex()):
        """Fetches at most _fetch_step rows."""
        count = min(len(self._unfetched), self._fetch_step)
        fetched, self._unfetched = self._unfetched[:count], self._unfetched[count:]
        self.beginInsertRows(parent, self.rowCount(), self.rowCount() + count - 1)
        self._data += fetched
        self.endInsertRows()

    def flags(self, index):
        """Make the items non-editable."""
        return ~Qt.ItemIsEditable

    def rowCount(self, parent=QModelIndex()):
        """Returns number of rows."""
        return len(self._data)

    def index(self, row, column, parent=QModelIndex()):
        """Returns an index for this model, with the corresponding AutoFilterMenuItem in the internal pointer."""
        return self.createIndex(row, column, self._data[row])

    def data(self, index, role=Qt.DisplayRole):
        """Handle the check state role."""
        item = index.internalPointer()
        if role == Qt.CheckStateRole:
            return item.checked
        if role == Qt.DisplayRole:
            return item.value
        return super().data(index, role)

    def toggle_checked_state(self, index):
        """Toggle checked state of given index.
        Must be reimplemented in subclasses.
        """
        raise NotImplementedError()

    def reset_model(self, data=None):
        """Resets model.

        Args:
            data (list): a list of AutoFilterMenuItem
        """
        if data is None:
            data = []
        self.beginResetModel()
        self._data.clear()
        self._unfetched = data
        self.endResetModel()


class AutoFilterMenuAllItemModel(AutoFilterMenuItemModel):
    """A model for the 'All' item in the auto filter menu."""

    checked_state_changed = Signal("int", name="checked_state_changed")

    def __init__(self, parent=None, fetch_step=32):
        """Init class."""
        super().__init__(parent)
        self._item = AutoFilterMenuItem(Qt.Checked, "(Select All)")
        self._data = [self._item]

    @Slot("int", name="set_checked_state")
    def set_checked_state(self, state):
        """Sets the checked state for the item."""
        self._item.checked = state
        ind = self.index(0, 0)
        self.dataChanged.emit(ind, ind, [Qt.CheckStateRole])

    def toggle_checked_state(self, index):
        """Toggle checked state and emit checked_state_changed."""
        if self._item.checked in (Qt.Unchecked, Qt.PartiallyChecked):
            self._item.checked = Qt.Checked
        else:
            self._item.checked = Qt.Unchecked
        self.checked_state_changed.emit(self._item.checked)
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])


class AutoFilterMenuValueItemModel(AutoFilterMenuItemModel):
    """A model for the value items in the auto filter menu."""

    all_checked_state_changed = Signal("int", name="all_checked_state_changed")

    def __init__(self, parent=None, fetch_step=32):
        """Init class."""
        super().__init__(parent)
        self._checked_count = 0
        self._row_map = []
        self._filter_reg_exp = ""
        self.rowsInserted.connect(self._handle_rows_inserted)

    @Slot("QModelIndex", "int", "int", name="_handle_rows_inserted")
    def _handle_rows_inserted(self, parent, first, last):
        """Builds the row map and call the method that emits all_checked_state_changed appropriatly."""
        self.build_row_map()
        self.emit_all_checked_state_changed()

    def map_to_src(self, index):
        """Maps an index using the row map."""
        mapped_row = self._row_map[index.row()]
        return self.index(mapped_row, index.column())

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data from the mapped index, as in a filter."""
        return super().data(self.map_to_src(index), role)

    def rowCount(self, parent=QModelIndex()):
        """Returns the length of the row map."""
        return len(self._row_map)

    def filter_accepts_row(self, row):
        """Returns whether or not the row passes the filter, and update the checked count
        so we know how many items are checked for emitting all_checked_state_changed."""
        item = super().index(row, 0).internalPointer()
        if not re.search(self._filter_reg_exp, str(item.value)):
            return False
        if item.checked == Qt.Checked:
            self._checked_count += 1
        return True

    def set_filter_reg_exp(self, regexp):
        """Sets the regular expression to filter row values."""
        self._checked_count = 0
        if regexp != self._filter_reg_exp:
            self._filter_reg_exp = regexp
            self.refresh()

    def refresh(self):
        """Rebuilds the row map so as to update the filter.
        Called when the filter regular expression changes."""
        self.layoutAboutToBeChanged.emit()
        self.build_row_map()
        self.layoutChanged.emit()
        self.emit_all_checked_state_changed()

    def build_row_map(self):
        """Buils the row map while applying the filter to each row."""
        self._row_map = [row for row in range(super().rowCount()) if self.filter_accepts_row(row)]

    @Slot("int", name="set_all_items_checked_state")
    def set_all_items_checked_state(self, state):
        """Set the checked state for all items."""
        for row in range(self.rowCount()):
            item = self.index(row, 0).internalPointer()
            item.checked = state
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, 0), [Qt.CheckStateRole])
        self._checked_count = self.rowCount() if state else 0

    def toggle_checked_state(self, index):
        """Toggle checked state of given index."""
        item = self.map_to_src(index).internalPointer()
        if item.checked in (Qt.Unchecked, Qt.PartiallyChecked):
            item.checked = Qt.Checked
            self._checked_count += 1
        else:
            item.checked = Qt.Unchecked
            self._checked_count -= 1
        self.emit_all_checked_state_changed()
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])

    def emit_all_checked_state_changed(self):
        """Emits signal depending on how many items are checked."""
        if self._checked_count == 0:
            all_checked_state = Qt.Unchecked
        elif self._checked_count == self.rowCount():
            all_checked_state = Qt.Checked
        else:
            all_checked_state = Qt.PartiallyChecked
        self.all_checked_state_changed.emit(all_checked_state)

    def reset_model(self, data=None):
        """Resets model."""
        self._checked_count = 0
        self._filter_reg_exp = ""
        self._row_map.clear()
        super().reset_model(data)

    def get_auto_filter(self):
        """Returns the output of the auto filter.

        Returns:
            dict, NoneType: An empty dictionary if *all* values are accepted; None if *no* values are accepted;
                and a dictionary mapping tuples (db_map, class_id) to a set of values if *some* are accepted.
        """
        if self._checked_count == 0:
            return None
        if self._checked_count == super().rowCount():
            return {}
        d = dict()
        for row in range(self.rowCount()):
            mapped_row = self._row_map[row]
            item = self.index(mapped_row, 0).internalPointer()
            if not item.checked:
                continue
            for class_ in item.classes:
                d.setdefault(class_, set()).add(item.value)
        return d
