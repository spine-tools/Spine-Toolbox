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

"""A tree model for parameter_value lists."""
from PySide6.QtCore import Qt, QModelIndex
from .tree_model_base import TreeModelBase
from .parameter_value_list_item import DBItem


class ParameterValueListModel(TreeModelBase):
    """A model to display parameter_value_list data in a tree view."""

    def _make_db_item(self, db_map):
        return DBItem(self, db_map)

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1."""
        return 1

    def index_name(self, index):
        return self.data(index.parent(), role=Qt.ItemDataRole.DisplayRole)

    def get_set_data_delayed(self, index):
        """Returns a function that ParameterValueEditor can call to set data for the given index at any later time,
        even if the model changes.

        Args:
            index (QModelIndex)

        Returns:
            Callable
        """
        item = self.item_from_index(index)
        return lambda value, item=item: item.set_data(0, value)
