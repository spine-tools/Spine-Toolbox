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
A model for indexed parameter values, used by the parameter value editors.

:authors: A. Soininen (VTT)
:date:   18.6.2019
"""

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt


class IndexedValueTableModel(QAbstractTableModel):
    def __init__(self, value, index_header, value_header):
        """A base class for time pattern and time series models.

        Args:
            value (TimePattern, TimeSeriesFixedStep, TimeSeriesVariableStep): a parameter value
            index_header (str): a header for the index column
            value_header (str): a header for the value column
        """
        super().__init__(parent=None)
        self._value = value
        self._index_header = index_header
        self._value_header = value_header

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns which is two."""
        return 2

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data at index for given role."""
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        if index.column() == 0:
            return str(self._value.indexes[index.row()])
        return float(self._value.values[index.row()])

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Returns a header."""
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section + 1
        return self._index_header if section == 0 else self._value_header

    def reset(self, value):
        """Resets the model."""
        self.beginResetModel()
        self._value = value
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows."""
        return len(self._value)

    @property
    def value(self):
        """Returns the parameter value associated with the model."""
        return self._value
