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
Contains the GraphViewMixin class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""
import itertools
from PySide2.QtCore import Slot, QTimer
from PySide2.QtWidgets import QHBoxLayout
from spinedb_api import from_database
from ...widgets.custom_qgraphicsscene import CustomGraphicsScene
from ...helpers import get_save_file_name_in_last_dir
from ..graphics_items import (
    EntityItem,
    ObjectItem,
    RelationshipItem,
    ArcItem,
    CrossHairsItem,
    CrossHairsRelationshipItem,
    CrossHairsArcItem,
)
from .graph_layout_generator import GraphLayoutGenerator
from .add_items_dialogs import AddReadyRelationshipsDialog


class GraphViewMixin:
    """Provides the graph view for the DS form."""

    VERTEX_EXTENT = 64
    _ARC_WIDTH = 0.15 * VERTEX_EXTENT
    _ARC_LENGTH_HINT = 1.5 * VERTEX_EXTENT
    _MAX_CONCURRENT_BUILDS = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        QHBoxLayout(self.ui.graphicsView)
        self._persistent = False
        self._owes_graph = False
        self.scene = None
        self.object_items = list()
        self.relationship_items = list()
        self.arc_items = list()
        self.selected_tree_inds = {}
        self.object_ids = list()
        self.relationship_ids = list()
        self.src_inds = list()
        self.dst_inds = list()
        self._relationships_being_added = False
        self.added_relationship_ids = set()
        self.layout_gens = list()
        self.ui.graphicsView.connect_spine_db_editor(self)

    def init_models(self):
        super().init_models()
        self.scene = CustomGraphicsScene(self)
        self.ui.graphicsView.setScene(self.scene)

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.ui.treeView_object.tree_selection_changed.connect(self.rebuild_graph)
        self.ui.treeView_relationship.tree_selection_changed.connect(self.rebuild_graph)
        self.ui.dockWidget_entity_graph.visibilityChanged.connect(self._handle_entity_graph_visibility_changed)

    def receive_objects_added(self, db_map_data):
        """Runs when objects are added to the db.
        Adds the new objects to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_added(db_map_data)
        added_ids = {(db_map, x["id"]) for db_map, objects in db_map_data.items() for x in objects}
        self.restore_removed_entities(added_ids)

    def receive_relationships_added(self, db_map_data):
        """Runs when relationships are added to the db.
        Adds the new relationships to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_relationships_added(db_map_data)
        added_ids = {(db_map, x["id"]) for db_map, relationships in db_map_data.items() for x in relationships}
        restored_ids = self.restore_removed_entities(added_ids)
        added_ids -= restored_ids
        if added_ids and self._relationships_being_added:
            self.added_relationship_ids.update(added_ids)
            self.build_graph(persistent=True)
            self._end_add_relationships()

    def receive_object_classes_updated(self, db_map_data):
        super().receive_object_classes_updated(db_map_data)
        self.refresh_icons(db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        super().receive_relationship_classes_updated(db_map_data)
        self.refresh_icons(db_map_data)

    def receive_objects_updated(self, db_map_data):
        """Runs when objects are updated in the db. Refreshes names of objects in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_updated(db_map_data)
        updated_ids = {(db_map, x["id"]): x["name"] for db_map, objects in db_map_data.items() for x in objects}
        for item in self.ui.graphicsView.items():
            if isinstance(item, ObjectItem) and item.db_map_entity_id in updated_ids:
                name = updated_ids[item.db_map_entity_id]
                item.update_name(name)

    def receive_objects_removed(self, db_map_data):
        """Runs when objects are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_objects_removed(db_map_data)
        self.hide_removed_entities(db_map_data)

    def receive_relationships_removed(self, db_map_data):
        """Runs when relationships are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        super().receive_relationships_removed(db_map_data)
        self.hide_removed_entities(db_map_data)

    def restore_removed_entities(self, added_ids):
        """Restores any entities that have been previously removed and returns their ids.
        This happens in the context of undo/redo.

        Args:
            added_ids (set(int)): Set of newly added ids.

        Returns:
            set(int)
        """
        restored_items = [item for item in self.ui.graphicsView.removed_items if item.db_map_entity_id in added_ids]
        for item in restored_items:
            self.ui.graphicsView.removed_items.remove(item)
            item.set_all_visible(True)
        return {item.db_map_entity_id for item in restored_items}

    def hide_removed_entities(self, db_map_data):
        """Hides removed entities while saving them into a list attribute.
        This allows entities to be restored in case the user undoes the operation."""
        removed_ids = {(db_map, x["id"]) for db_map, items in db_map_data.items() for x in items}
        self.added_relationship_ids -= removed_ids
        removed_items = [
            item
            for item in self.ui.graphicsView.items()
            if isinstance(item, EntityItem) and item.db_map_entity_id in removed_ids
        ]
        if not removed_items:
            return
        self.ui.graphicsView.removed_items.extend(removed_items)
        scene = self.scene
        self.scene = None
        for item in removed_items:
            item.set_all_visible(False)
        self.scene = scene

    def refresh_icons(self, db_map_data):
        """Runs when entity classes are updated in the db. Refreshes icons of entities in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        updated_ids = {(db_map, x["id"]) for db_map, items in db_map_data.items() for x in items}
        for item in self.ui.graphicsView.items():
            if isinstance(item, EntityItem) and (item.db_map, item.entity_class_id) in updated_ids:
                item.refresh_icon()

    @Slot(bool)
    def _handle_entity_graph_visibility_changed(self, visible):
        if not visible:
            self._stop_layout_generators()
            return
        if self._owes_graph:
            QTimer.singleShot(100, self.build_graph)

    @Slot(dict)
    def rebuild_graph(self, selected):
        """Stores the given selection of entity tree indexes and builds graph."""
        self.selected_tree_inds = selected
        self.added_relationship_ids.clear()
        self.build_graph()

    def build_graph(self, persistent=False):
        """Builds the graph.

        Args:
            persistent (bool, optional): If True, elements in the current graph (if any) retain their position
                in the new one.
        """
        if not self.ui.dockWidget_entity_graph.isVisible():
            self._owes_graph = True
            return
        self._owes_graph = False
        if len(self.layout_gens) > self._MAX_CONCURRENT_BUILDS:
            return
        self.ui.graphicsView.clear_cross_hairs_items()  # Needed
        self._persistent = persistent
        self._stop_layout_generators()
        self._update_graph_data()
        layout_gen = self._make_layout_generator()
        self.layout_gens.append(layout_gen)
        layout_gen.show_progress_widget(self.ui.graphicsView)
        layout_gen.finished.connect(lambda x, y, layout_gen=layout_gen: self._complete_graph(x, y, layout_gen))
        layout_gen.destroyed.connect(lambda obj=None, layout_gen=layout_gen: self.layout_gens.remove(layout_gen))
        layout_gen.start()

    def _stop_layout_generators(self):
        for layout_gen in self.layout_gens:
            if layout_gen.is_running():
                layout_gen.stop()

    def _complete_graph(self, x, y, layout_gen):
        """
        Args:
            x (list): Horizontal coordinates
            y (list): Vertical coordinates
        """
        if layout_gen != self.layout_gens[-1]:
            return
        self.ui.graphicsView.removed_items.clear()
        self.ui.graphicsView.selected_items.clear()
        self.ui.graphicsView.hidden_items.clear()
        self.ui.graphicsView.heat_map_items.clear()
        self.scene.clear()
        if self._make_new_items(x, y):
            self._add_new_items()  # pylint: disable=no-value-for-parameter
        if not self._persistent:
            self.ui.graphicsView.reset_zoom()
        else:
            self.ui.graphicsView.apply_zoom()

    def _get_selected_entity_ids(self):
        """Returns a set of ids corresponding to selected entities in the trees.

        Returns:
            set: selected object ids
            set: selected relationship ids
        """
        if "root" in self.selected_tree_inds:
            return (
                set((db_map, x["id"]) for db_map in self.db_maps for x in self.db_mngr.get_items(db_map, "object")),
                set(),
            )
        selected_object_ids = set()
        selected_relationship_ids = set()
        for index in self.selected_tree_inds.get("object", {}):
            item = index.model().item_from_index(index)
            for db_map_id in item.db_map_ids.items():
                selected_object_ids.add(db_map_id)
        for index in self.selected_tree_inds.get("relationship", {}):
            item = index.model().item_from_index(index)
            for db_map_id in item.db_map_ids.items():
                selected_relationship_ids.add(db_map_id)
        for index in self.selected_tree_inds.get("object_class", {}):
            item = index.model().item_from_index(index)
            for db_map in item.db_maps:
                object_ids = set((db_map, id_) for id_ in item._get_children_ids(db_map))
                selected_object_ids.update(object_ids)
        for index in self.selected_tree_inds.get("relationship_class", {}):
            item = index.model().item_from_index(index)
            for db_map in item.db_maps:
                relationship_ids = set((db_map, id_) for id_ in item._get_children_ids(db_map))
                selected_relationship_ids.update(relationship_ids)
        return selected_object_ids, selected_relationship_ids

    def _get_all_relationships_for_graph(self, object_ids, relationship_ids):
        cond = any if self.ui.graphicsView.auto_expand_objects else all
        return [
            (db_map, x)
            for db_map in self.db_maps
            for x in self.db_mngr.get_items(db_map, "relationship")
            if cond([(db_map, int(id_)) in object_ids for id_ in x["object_id_list"].split(",")])
        ] + [(db_map, self.db_mngr.get_item(db_map, "relationship", id_)) for db_map, id_ in relationship_ids]

    def _update_graph_data(self):
        """Updates data for graph according to selection in trees."""
        object_ids, relationship_ids = self._get_selected_entity_ids()
        relationship_ids.update(self.added_relationship_ids)
        prunned_entity_ids = {id_ for ids in self.ui.graphicsView.prunned_entity_ids.values() for id_ in ids}
        object_ids -= prunned_entity_ids
        relationship_ids -= prunned_entity_ids
        relationships = self._get_all_relationships_for_graph(object_ids, relationship_ids)
        object_id_lists = dict()
        for db_map, relationship in relationships:
            if (db_map, relationship["id"]) in prunned_entity_ids:
                continue
            object_id_list = [
                (db_map, id_)
                for id_ in (int(x) for x in relationship["object_id_list"].split(","))
                if (db_map, id_) not in prunned_entity_ids
            ]
            if len(object_id_list) < 2:
                continue
            object_ids.update(object_id_list)
            object_id_lists[db_map, relationship["id"]] = object_id_list
        self.object_ids = list(object_ids)
        self.relationship_ids = list(object_id_lists)
        self._update_src_dst_inds(object_id_lists)

    def _update_src_dst_inds(self, object_id_lists):
        self.src_inds = list()
        self.dst_inds = list()
        object_ind_lookup = {id_: k for k, id_ in enumerate(self.object_ids)}
        relationship_ind_lookup = {id_: len(self.object_ids) + k for k, id_ in enumerate(self.relationship_ids)}
        for relationship_id, object_id_list in object_id_lists.items():
            object_inds = [object_ind_lookup[object_id] for object_id in object_id_list]
            relationship_ind = relationship_ind_lookup[relationship_id]
            for object_ind in object_inds:
                self.src_inds.append(relationship_ind)
                self.dst_inds.append(object_ind)

    def _get_parameter_positions(self, parameter_name):
        if not parameter_name:
            yield from []
        for db_map in self.db_maps:
            for p in self.db_mngr.get_items_by_field(db_map, "parameter_value", "parameter_name", parameter_name):
                pos = from_database(p["value"])
                if isinstance(pos, float):
                    yield (db_map, p["entity_id"]), pos

    def _make_layout_generator(self):
        """Returns a layout generator for the current graph.

        Returns:
            GraphLayoutGenerator
        """
        fixed_positions = {}
        if self._persistent:
            for item in self.ui.graphicsView.items():
                if isinstance(item, EntityItem):
                    fixed_positions[item.db_map_entity_id] = {"x": item.pos().x(), "y": item.pos().y()}
        param_pos_x = dict(self._get_parameter_positions(self.ui.graphicsView.pos_x_parameter))
        param_pos_y = dict(self._get_parameter_positions(self.ui.graphicsView.pos_y_parameter))
        for db_map_entity_id in param_pos_x.keys() & param_pos_y.keys():
            fixed_positions[db_map_entity_id] = {"x": param_pos_x[db_map_entity_id], "y": param_pos_y[db_map_entity_id]}
        entity_ids = self.object_ids + self.relationship_ids
        heavy_positions = {ind: fixed_positions[id_] for ind, id_ in enumerate(entity_ids) if id_ in fixed_positions}
        return GraphLayoutGenerator(
            len(entity_ids), self.src_inds, self.dst_inds, self._ARC_LENGTH_HINT, heavy_positions=heavy_positions
        )

    def _make_new_items(self, x, y):
        """Returns new items for the graph.

        Args:
            x (list)
            y (list)
        """
        self.object_items = list()
        self.relationship_items = list()
        self.arc_items = list()
        for i, object_id in enumerate(self.object_ids):
            object_item = ObjectItem(self, x[i], y[i], self.VERTEX_EXTENT, object_id)
            self.object_items.append(object_item)
        offset = len(self.object_items)
        for i, relationship_id in enumerate(self.relationship_ids):
            relationship_item = RelationshipItem(
                self, x[offset + i], y[offset + i], 0.5 * self.VERTEX_EXTENT, relationship_id
            )
            self.relationship_items.append(relationship_item)
        for rel_ind, obj_ind in zip(self.src_inds, self.dst_inds):
            arc_item = ArcItem(self.relationship_items[rel_ind - offset], self.object_items[obj_ind], self._ARC_WIDTH)
            self.arc_items.append(arc_item)
        return any(self.object_items)

    def _add_new_items(self):
        for item in self.object_items + self.relationship_items + self.arc_items:
            self.scene.addItem(item)

    def start_relationship(self, relationship_class, obj_item):
        """Starts a relationship from the given object item.

        Args:
            relationship_class (dict)
            obj_item (..graphics_items.ObjectItem)
        """
        db_map = obj_item.db_map
        object_class_ids_to_go = relationship_class["object_class_id_list"].copy()
        object_class_ids_to_go.remove(obj_item.entity_class_id)
        relationship_class["object_class_ids_to_go"] = object_class_ids_to_go
        ch_item = CrossHairsItem(
            self, obj_item.pos().x(), obj_item.pos().y(), 0.8 * self.VERTEX_EXTENT, db_map_entity_id=(db_map, None)
        )
        ch_rel_item = CrossHairsRelationshipItem(
            self, obj_item.pos().x(), obj_item.pos().y(), 0.5 * self.VERTEX_EXTENT, db_map_entity_id=(db_map, None)
        )
        ch_arc_item1 = CrossHairsArcItem(ch_rel_item, obj_item, self._ARC_WIDTH)
        ch_arc_item2 = CrossHairsArcItem(ch_rel_item, ch_item, self._ARC_WIDTH)
        ch_rel_item.refresh_icon()
        self.ui.graphicsView.set_cross_hairs_items(
            relationship_class, [ch_item, ch_rel_item, ch_arc_item1, ch_arc_item2]
        )

    def finalize_relationship(self, relationship_class, *object_items):
        """Tries to add relationships between the given object items.

        Args:
            relationship_class (dict)
            object_items (..graphics_items.ObjectItem)
        """
        db_map = object_items[0].db_map
        relationships = set()
        object_class_id_list = relationship_class["object_class_id_list"]
        for item_permutation in itertools.permutations(object_items):
            if [item.entity_class_id for item in item_permutation] == object_class_id_list:
                relationship = tuple(item.entity_name for item in item_permutation)
                relationships.add(relationship)
        dialog = AddReadyRelationshipsDialog(self, relationship_class, list(relationships), self.db_mngr, db_map)
        dialog.accepted.connect(self._begin_add_relationships)
        dialog.show()

    def _begin_add_relationships(self):
        self._relationships_being_added = True

    def _end_add_relationships(self):
        self._relationships_being_added = False

    def get_pdf_file_path(self):
        self.qsettings.beginGroup(self.settings_group)
        file_path, _ = get_save_file_name_in_last_dir(
            self.qsettings, "exportGraphAsPDF", self, "Export as PDF...", self._get_base_dir(), "PDF files (*.pdf)"
        )
        self.qsettings.endGroup()
        return file_path

    def closeEvent(self, event):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event
        """
        super().closeEvent(event)
        self.scene = None
