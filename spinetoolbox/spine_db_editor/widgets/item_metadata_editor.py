######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains machinery to deal with item metadata editor.

:author: A. Soininen (VTT)
:date:   25.3.2022
"""
from PySide2.QtCore import Slot

from ..mvcmodels.entity_tree_item import ObjectItem, MemberObjectItem, RelationshipItem
from ..mvcmodels.item_metadata_table_model import ItemMetadataTableModel


class ItemMetadataEditor:
    def __init__(self, item_metadata_table_view, db_mngr):
        """
        Args:
            item_metadata_table_view (ItemMetadataTableView): editor's view
            db_mngr (SpineDBManager): database manager
        """
        self._item_metadata_table_view = item_metadata_table_view
        self._item_metadata_table_model = ItemMetadataTableModel(db_mngr, self._item_metadata_table_view)
        self._item_metadata_table_view.setModel(self._item_metadata_table_model)

    def connect_signals(self, ui):
        ui.treeView_object.selectionModel().currentChanged.connect(self._reload_entity_metadata)
        ui.treeView_relationship.selectionModel().currentChanged.connect(self._reload_entity_metadata)

    @Slot(dict)
    def _reload_entity_metadata(self, current_index, previous_index):
        item = current_index.model().item_from_index(current_index)
        if not isinstance(item, (ObjectItem, RelationshipItem, MemberObjectItem)):
            return
        self._item_metadata_table_model.set_entity_ids(item.db_map_ids)
