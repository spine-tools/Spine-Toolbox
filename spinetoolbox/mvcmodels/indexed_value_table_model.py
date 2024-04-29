######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""A model for indexed parameter values, used by the parameter_value editors."""
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

EXPANSE_COLOR = QColor(245, 245, 245)


class IndexedValueTableModel(QAbstractTableModel):
    """A base class for time pattern and time series models."""

    def __init__(self, value, parent):
        """
        Args:
            value (IndexedValue): a parameter_value
            parent (QObject): parent object
        """
        super().__init__(parent)
        self._value = value

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns which is two."""
        return 2

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Returns the data at index for given role."""
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            row = index.row()
            if row == len(self._value):
                return None
            if index.column() == 0:
                return str(self._value.indexes[index.row()])
            value = self._value.values[index.row()]
            return str(value) if role == Qt.ItemDataRole.DisplayRole else value
        if role == Qt.ItemDataRole.BackgroundRole:
            if index.row() == len(self._value):
                return EXPANSE_COLOR
            return None
        return None

    def headerData(self, section, orientation=Qt.Orientation.Horizontal, role=Qt.ItemDataRole.DisplayRole):
        """Returns a header."""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Vertical:
            return section + 1
        return (self._value.index_name, "Value")[section]

    def is_expanse_row(self, row):
        """
        Returns True if row is the expanse row.

        Args:
            row (int): a row

        Returns:
            bool: True if row is the expanse row, False otherwise
        """
        return row == len(self._value)

    def reset(self, value):
        """Resets the model."""
        self.beginResetModel()
        self._value = value
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows."""
        return len(self._value) + 1

    def setHeaderData(self, section, orientation, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or section != 0 or orientation != Qt.Orientation.Horizontal or not value:
            return False
        self._value.index_name = value
        self.headerDataChanged.emit(orientation, section, section)
        return True

    @property
    def value(self):
        """Returns the parameter_value associated with the model."""
        return self._value
