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

"""Contains machinery to deal with item metadata editor."""
from PySide6.QtCore import Slot, QModelIndex
from ..mvcmodels.entity_tree_item import EntityItem
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
        self._item_metadata_table_model = ItemMetadataTableModel(db_mngr, db_editor.db_maps, db_editor)
        self._item_metadata_table_view.set_models(self._item_metadata_table_model, metadata_editor.metadata_model())
        self._item_metadata_table_view.setModel(self._item_metadata_table_model)
        self._item_metadata_table_view.connect_spine_db_editor(db_editor)

    def connect_signals(self, ui):
        """Connects user interface signals.

        Args:
            ui (Ui_MainWindow): DB editor's user interface
        """
        ui.treeView_entity.selectionModel().currentChanged.connect(self._reload_entity_metadata)
        ui.tableView_parameter_value.selectionModel().currentChanged.connect(self._reload_value_metadata)

    def init_models(self, db_maps):
        """Initializes editor's models.

        Args:
            db_maps (Iterable of DiffDatabaseMapping): database mappings
        """
        self._item_metadata_table_model.set_db_maps(db_maps)

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
        if not isinstance(item, EntityItem):
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
