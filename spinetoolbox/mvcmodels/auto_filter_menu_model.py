######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

from PySide2.QtCore import Qt, Signal, Slot, QStringListModel, QSortFilterProxyModel, QModelIndex


class AutoFilterMenuItem:
    """An item for the auto filter menu."""

    def __init__(self, checked, value, in_classes=()):
        """Init class."""
        self.checked = checked
        self.value = value
        self.in_classes = in_classes


class AutoFilterMenuItemModel(QStringListModel):
    """A source model for the auto filter menu widget."""

    def __init__(self, parent=None, fetch_step=32):
        """Init class."""
        super().__init__(parent)
        self._data = []
        self._unfetched = []
        self._fetch_step = fetch_step

    def canFetchMore(self, parent=QModelIndex()):
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
        return self.createIndex(row, column, self._data[row])

    def data(self, index, role=Qt.DisplayRole):
        item = index.internalPointer()
        if role == Qt.CheckStateRole:
            return item.checked
        if role == Qt.DisplayRole:
            return item.value
        return super().data(index, role)

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

    checked_state_changed = Signal("int", name="checked_state_changed")

    def __init__(self, parent=None, fetch_step=32):
        """Init class."""
        super().__init__(parent)
        self._item = AutoFilterMenuItem(Qt.Checked, "(Select All)")
        self._data = [self._item]

    @Slot("int", name="set_checked_state")
    def set_checked_state(self, state):
        self._item.checked = state
        ind = self.index(0, 0)
        self.dataChanged.emit(ind, ind, [Qt.CheckStateRole])

    def toggle_checked_state(self, index):
        """Toggle checked state of given index."""
        if self._item.checked in (Qt.Unchecked, Qt.PartiallyChecked):
            self._item.checked = Qt.Checked
        else:
            self._item.checked = Qt.Unchecked
        self.checked_state_changed.emit(self._item.checked)
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])


class AutoFilterMenuItemProxyModel(QSortFilterProxyModel):
    """A source model for the auto filter menu widget."""

    all_checked_state_changed = Signal("int", name="all_checked_state_changed")

    def __init__(self, parent=None, fetch_step=32):
        """Init class."""
        super().__init__(parent)
        self._checked_count = 0
        source = AutoFilterMenuItemModel(parent)
        self.setSourceModel(source)

    def filterAcceptsRow(self, source_row, source_parent):
        if not super().filterAcceptsRow(source_row, source_parent):
            return False
        item = self.sourceModel()._data[source_row]
        if item.checked == Qt.Checked:
            self._checked_count += 1
        return True

    def setFilterRegExp(self, regexp):
        self._checked_count = 0
        super().setFilterRegExp(regexp)

    @Slot("int", name="set_all_items_checked_state")
    def set_all_items_checked_state(self, state):
        """"""
        for row in range(self.rowCount()):
            item = self.mapToSource(self.index(row, 0)).internalPointer()
            item.checked = state
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, 0), [Qt.CheckStateRole])
        self._checked_count = self.rowCount()

    def toggle_checked_state(self, index):
        """Toggle checked state of given index."""
        item = self.mapToSource(index).internalPointer()
        if item.checked in (Qt.Unchecked, Qt.PartiallyChecked):
            item.checked = Qt.Checked
            self._checked_count += 1
        else:
            item.checked = Qt.Unchecked
            self._checked_count -= 1
        if self._checked_count == 0:
            all_checked = Qt.Unchecked
        elif self._checked_count == self.rowCount():
            all_checked = Qt.Checked
        else:
            all_checked = Qt.PartiallyChecked
        self.all_checked_state_changed.emit(all_checked)
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])

    def reset_model(self, data=None):
        """Calls the source method."""
        self.sourceModel().reset_model(data)

    def get_auto_filter(self):
        """Returns autofilter.
        """
        d = dict()
        for row in range(self.rowCount()):
            item = self.mapToSource(self.index(row, 0)).internalPointer()
            if not item.checked:
                for class_id in item.in_classes:
                    d.setdefault(class_id, set()).add(item.value)
        return d
