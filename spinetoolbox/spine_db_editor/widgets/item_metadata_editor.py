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
from PySide2.QtCore import Slot, QModelIndex

from spinetoolbox.helpers import separate_metadata_and_item_metadata
from ..mvcmodels.entity_tree_item import ObjectItem, MemberObjectItem, RelationshipItem
from ..mvcmodels.item_metadata_table_model import ItemMetadataTableModel


class ItemMetadataEditor:
    """A DB editor helper class that manages entity and parameter value metadata editor."""

    def __init__(self, item_metadata_table_view, db_editor, metadata_editor, db_mngr):
        """
        Args:
            item_metadata_table_view (ItemMetadataTableView): editor's view
            db_editor (SpineDBEditor): database editor
            metadata_editor (MetadataEditor): metadata editor
            db_mngr (SpineDBManager): database manager
        """
        self._db_mngr = db_mngr
        self._metadata_editor = metadata_editor
        self._item_metadata_table_view = item_metadata_table_view
        self._item_metadata_table_model = ItemMetadataTableModel(
            db_mngr, db_editor.db_maps, self._item_metadata_table_view
        )
        self._item_metadata_table_view.set_models(self._item_metadata_table_model, metadata_editor.metadata_model())
        self._item_metadata_table_view.setModel(self._item_metadata_table_model)
        self._item_metadata_table_view.connect_spine_db_editor(db_editor)

    def connect_signals(self, ui):
        """Connects user interface signals.

        Args:
            ui (Ui_MainWindow): DB editor's user interface
        """
        ui.treeView_object.selectionModel().currentChanged.connect(self._reload_entity_metadata)
        ui.treeView_relationship.selectionModel().currentChanged.connect(self._reload_entity_metadata)
        ui.tableView_object_parameter_value.selectionModel().currentChanged.connect(self._reload_value_metadata)
        ui.tableView_relationship_parameter_value.selectionModel().currentChanged.connect(self._reload_value_metadata)

    def init_models(self, db_maps):
        """Initializes editor's models.

        Args:
            db_maps (Iterable of DiffDatabaseMapping): database mappings
        """
        self._cache_item_metadata(db_maps)
        self._item_metadata_table_model.set_db_maps(db_maps)

    def _cache_item_metadata(self, db_maps):
        """Caches item metadata into DB manager's cache.

        Args:
            db_maps (Iterable of DiffDatabaseMapping): database mappings
        """
        for db_map in db_maps:
            self._db_mngr.get_db_map_cache(db_map, {"entity_metadata", "parameter_value_metadata"})

    @Slot(QModelIndex, QModelIndex)
    def _reload_entity_metadata(self, current_index, previous_index):
        """Loads entity metadata for selected object or relationship.

        Args:
            current_index (QModelIndex): currently selected index in object/relationship tree
            previous_index (QModelIndex): unused
        """
        self._item_metadata_table_view.setEnabled(False)
        self._item_metadata_table_model.clear()
        if not current_index.isValid():
            return
        item = current_index.model().item_from_index(current_index)
        if not isinstance(item, (ObjectItem, RelationshipItem, MemberObjectItem)):
            return
        self._item_metadata_table_model.set_entity_ids(item.db_map_ids)
        self._item_metadata_table_view.setEnabled(True)

    @Slot(QModelIndex, QModelIndex)
    def _reload_value_metadata(self, current_index, previous_index):
        """Loads parameter value metadata for selected value.

        Args:
            current_index (QModelIndex): currently selected index in object/relationship parameter value table
            previous_index (QModelIndex): unused
        """
        self._item_metadata_table_view.setEnabled(False)
        self._item_metadata_table_model.clear()
        if not current_index.isValid():
            return
        db_map, id_ = current_index.model().db_map_id(current_index)
        if id_ is None:
            return
        db_map_ids = {db_map: id_}
        self._item_metadata_table_model.set_parameter_value_ids(db_map_ids)
        self._item_metadata_table_view.setEnabled(True)

    def add_item_metadata(self, db_map_data):
        """Adds new item metadata records to the model and updates metadata model if required.

        Args:
            db_map_data (dict): added records keyed by database mapping
        """
        item_metadata_db_map_data, metadata_db_map_data = separate_metadata_and_item_metadata(db_map_data)
        if metadata_db_map_data:
            self._metadata_editor.add_metadata(metadata_db_map_data)
        self._item_metadata_table_model.add_item_metadata(item_metadata_db_map_data)

    def update_item_metadata(self, db_map_data):
        """Updates item metadata.

        Args:
            db_map_data (dict): updated metadata records
        """
        item_metadata_db_map_data, metadata_db_map_data = separate_metadata_and_item_metadata(db_map_data)
        if metadata_db_map_data:
            self._metadata_editor.add_and_update_metadata(metadata_db_map_data)
        self._item_metadata_table_model.update_item_metadata(item_metadata_db_map_data)

    def remove_item_metadata(self, db_map_data):
        """Removes item metadata records from the model.

        Args:
            db_map_data (dict): added records keyed by database mapping
        """
        self._item_metadata_table_model.remove_item_metadata(db_map_data)

    def update_metadata(self, db_map_data):
        """Updates metadata.

        Args:
            db_map_data (dict): updated metadata records
        """
        self._item_metadata_table_model.update_metadata(db_map_data)

    def remove_metadata(self, db_map_data):
        """Removes entries corresponding to removed metadata from the model.

        Args:
            db_map_data (dict): removed metadata records
        """
        self._item_metadata_table_model.remove_metadata(db_map_data)

    def roll_back(self, db_maps):
        """Rolls back database changes.

        Args:
            db_maps (Iterable of DiffDatabaseMapping): rolled back databases
        """
        self._item_metadata_table_model.roll_back(db_maps)