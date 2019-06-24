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
Models for time series editors.

:authors: A. Soininen (VTT)
:date:   18.6.2019
"""

from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide2.QtGui import QBrush


class TimeSeriesTableModel(QAbstractTableModel):

    set_data_failed = Signal(QModelIndex, name='set_data_failed')

    def __init__(self, stamps, values, parent=None):
        super().__init__(parent)
        self._stamps = stamps
        self._fixed_stamps = False
        self._values = values

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        if index.column() == 0:
            return str(self._stamps[index.row()])
        return float(self._values[index.row()])

    def flags(self, index):
        """Return index flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == 0 and self._fixed_stamps:
            return Qt.ItemIsSelectable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:
            return section + 1
        return "Time" if section == 0 else "Value"

    def reset(self, stamps, values):
        self.beginResetModel()
        self._stamps = stamps
        self._values = values
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._stamps)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False
        if index.column() == 0:
            try:
                self._stamps[index.row()] = value
            except ValueError:
                self.set_data_failed.emit(index)
                return False
        else:
            try:
                self._values[index.row()] = value
            except ValueError:
                self.set_data_failed.emit(index)
                return False
        self.dataChanged.emit(index, index, [Qt.EditRole])
        return True

    def set_fixed_time_stamps(self, fixed):
        self._fixed_stamps = fixed

    @property
    def stamps(self):
        return self._stamps

    @property
    def values(self):
        return self._values
