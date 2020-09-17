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
Contains :class:`DomainNameListModel`

:author: A. Soininen (VTT)
:date:   17.9.2020
"""
from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt


class DomainNameListModel(QAbstractListModel):
    """
    Model for domains_list_view.

    Stores EntityClassInfo objects displaying the entity name in domains_list_view.
    """

    def __init__(self, entity_classes):
        """
        Args:
            entity_classes (list): a list of EntityClassObjects
        """
        super().__init__()
        self._entity_classes = entity_classes

    def data(self, index, role=Qt.DisplayRole):
        """Returns model's data for given index."""
        if role != Qt.DisplayRole or not index.isValid():
            return None
        return self._entity_classes[index.row()].name

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns None."""
        return None

    def index_for(self, set_name):
        """Returns the QModelIndex for given set name."""
        try:
            row = [entity_class.name for entity_class in self._entity_classes].index(set_name)
        except ValueError:
            return QModelIndex()
        else:
            return self.index(row, 0)

    def item_at(self, row):
        """Returns the EntityClassInfo object at given row."""
        return self._entity_classes[row]

    def rowCount(self, parent=QModelIndex()):
        """Returns the size of the model."""
        return len(self._entity_classes)
