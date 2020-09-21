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
Contains :class:`ParameterNameListModel`

:author: A. Soininen (VTT)
:date:   17.9.2020
"""
from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt


class ParameterNameListModel(QAbstractListModel):
    """Model for parameter_name_list_view."""

    def __init__(self, names):
        """
        Args:
            names (list): list of parameter names to show in the view
        """
        super().__init__()
        self._names = names
        self._selected = len(names) * [True]

    def data(self, index, role=Qt.DisplayRole):
        """Returns the model's data."""
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self._names[index.row()]
        if role == Qt.CheckStateRole:
            return Qt.Checked if self._selected[index.row()] else Qt.Unchecked
        return None

    def flags(self, index):
        """Returns flags for given index."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns None."""
        return None

    def reset(self, names):
        """Resets the model's contents when a new index is selected in domains_list_view."""
        self.beginResetModel()
        self._names = names
        self._selected = len(names) * [True]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of parameter names."""
        return len(self._names)

    def select(self, names):
        """Selects parameters for inclusion in the merged parameter."""
        for i, existing_name in enumerate(self._names):
            self._selected[i] = existing_name in names

    def selected(self):
        """Returns a list of the selected parameters."""
        return [name for name, select in zip(self._names, self._selected) if select]

    def setData(self, index, value, role=Qt.EditRole):
        """Selects or deselects the parameter at given index for inclusion in the merged parameter."""
        if role != Qt.CheckStateRole or not index.isValid():
            return False
        self._selected[index.row()] = value == Qt.Checked
        return True
