######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""

import sys
import itertools
from time import monotonic
from PySide6.QtCore import Slot, QTimer, QThreadPool
from PySide6.QtWidgets import QHBoxLayout
from spinedb_api import from_database
from ...widgets.custom_qgraphicsscene import CustomGraphicsScene
from ...helpers import get_save_file_name_in_last_dir
from ...fetch_parent import FlexibleFetchParent
from ..graphics_items import (
    EntityItem,
    ObjectItem,
    RelationshipItem,
    ArcItem,
    CrossHairsItem,
    CrossHairsRelationshipItem,
    CrossHairsArcItem,
)
from .graph_layout_generator import GraphLayoutGeneratorRunnable, ProgressBarWidget
from .add_items_dialogs import AddObjectsDialog, AddReadyRelationshipsDialog


class GraphViewMixin:
    """Provides the graph view for the DS form."""

    VERTEX_EXTENT = 64
    _ARC_WIDTH = 0.15 * VERTEX_EXTENT
    _ARC_LENGTH_HINT = 1.0 * VERTEX_EXTENT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui.graphicsView.connect_spine_db_editor(self)
        self._progress_bar_widget = ProgressBarWidget()
        self._progress_bar_widget.hide()
        self._progress_bar_widget.stop_button.clicked.connect(self._stop_extending_graph)
        layout = QHBoxLayout(self.ui.graphicsView)
        layout.addWidget(self._progress_bar_widget)
        self._persistent = False
        self._owes_graph = False
        self.scene = CustomGraphicsScene(self)
        self.ui.graphicsView.setScene(self.scene)
        self.object_items = list()
        self.relationship_items = list()
        self.arc_items = list()
        self.selected_tree_inds = {}
        self.db_map_object_id_sets = list()
        self.db_map_relationship_id_sets = list()
        self.src_inds = list()
        self.dst_inds = list()
        self._adding_relationships = False
        self._pos_for_added_objects = None
        self.added_db_map_relationship_ids = set()
        self._thread_pool = QThreadPool()
        self.layout_gens = dict()
        self._layout_gen_id = None
        self._extend_graph_timer = QTimer(self)
        self._extend_graph_timer.setSingleShot(True)
        self._extend_graph_timer.setInterval(100)
        self._extend_graph_timer.timeout.connect(self.build_graph)
        self._extending_graph = False
        self._object_fetch_parent = None
        self._relationship_fetch_parent = None

    def _renew_fetch_parents(self):
        if self._object_fetch_parent is not None:
            self._object_fetch_parent.set_obsolete(True)
        if self._relationship_fetch_parent is not None:
            self._relationship_fetch_parent.set_obsolete(True)
        self._object_fetch_parent = FlexibleFetchParent(
            "object",
            handle_items_added=self._handle_objects_added,
            handle_items_removed=self._handle_objects_removed,
            handle_items_updated=self._handle_objects_updated,
            accepts_item=self._accepts_object_item,
            owner=self,
        )
        self._relationship_fetch_parent = FlexibleFetchParent(
            "relationship",
            handle_items_added=self._handle_relationships_added,
            handle_items_removed=self._handle_relationships_removed,
            handle_items_updated=self._handle_relationships_updated,
            accepts_item=self._accepts_relationship_item,
            owner=self,
        )

    @Slot(bool)
    def _stop_extending_graph(self, _=False):
        self._extending_graph = False

    def init_models(self):
        self.scene.clear()
        super().init_models()

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.ui.treeView_object.object_selection_changed.connect(self._handle_tree_selection_changed)
        self.ui.treeView_relationship.relationship_selection_changed.connect(self._handle_tree_selection_changed)
        self.ui.dockWidget_entity_graph.visibilityChanged.connect(self._handle_entity_graph_visibility_changed)
        self.scene.selectionChanged.connect(self.ui.graphicsView.handle_scene_selection_changed)
        self.db_mngr.items_added.connect(self._refresh_icons)
        self.db_mngr.items_updated.connect(self._refresh_icons)

    def _refresh_icons(self, item_type, db_map_data):
        """Runs when entity classes are added or updated in the db. Refreshes icons of entities in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        if item_type not in ("object_class", "relationship_class"):
            return
        updated_ids = {(db_map, x["id"]) for db_map, items in db_map_data.items() for x in items}
        for item in self.ui.graphicsView.items():
            if isinstance(item, EntityItem) and (item.first_db_map, item.entity_class_id) in updated_ids:
                item.refresh_icon()

    def _accepts_object_item(self, item, db_map):
        return True

    def _accepts_relationship_item(self, item, db_map):
        return True

    def _handle_objects_added(self, db_map_data):
        """Runs when objects are added to the db.
        Adds the new objects to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        new_db_map_id_sets = self.add_db_map_ids_to_items(db_map_data, ObjectItem)
        if not new_db_map_id_sets:
            return
        if self._pos_for_added_objects is not None:
            spread = self.VERTEX_EXTENT * self.ui.graphicsView.zoom_factor
            gen = GraphLayoutGeneratorRunnable(None, len(new_db_map_id_sets), spread=spread)
            gen.run()
            x = self._pos_for_added_objects.x()
            y = self._pos_for_added_objects.y()
            for dx, dy, db_map_ids in zip(gen.x, gen.y, new_db_map_id_sets):
                object_item = ObjectItem(self, x + dx, y + dy, self.VERTEX_EXTENT, tuple(db_map_ids))
                self.scene.addItem(object_item)
                object_item.apply_zoom(self.ui.graphicsView.zoom_factor)
            self._pos_for_added_objects = None
        elif self._extending_graph:
            self._extend_graph_timer.start()

    def _handle_relationships_added(self, db_map_data):
        """Runs when relationships are added to the db.
        Adds the new relationships to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        new_db_map_id_sets = self.add_db_map_ids_to_items(db_map_data, RelationshipItem)
        if not new_db_map_id_sets:
            return
        if self._adding_relationships:
            for db_map_ids in new_db_map_id_sets:
                self.added_db_map_relationship_ids.update(db_map_ids)
            self.build_graph(persistent=True)
            self._end_add_relationships()
        elif self._extending_graph:
            self._extend_graph_timer.start()

    def _handle_objects_updated(self, db_map_data):
        """Runs when objects are updated in the db. Refreshes names of objects in graph.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        for item in self.ui.graphicsView.items():
            if isinstance(item, ObjectItem) and not item.update_name():
                self.build_graph(persistent=True)
                break

    def _handle_objects_removed(self, db_map_data):
        """Runs when objects are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        self.hide_removed_entities(db_map_data, ObjectItem)

    def _handle_relationships_updated(self, db_map_data):
        """Runs when relationships are updated in the db.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        updated_ids = {(db_map, x["id"]) for db_map, rels in db_map_data.items() for x in rels}
        for item in self.ui.graphicsView.items():
            if isinstance(item, RelationshipItem) and set(item.db_map_ids).intersection(updated_ids):
                self.build_graph(persistent=True)
                break

    def _handle_relationships_removed(self, db_map_data):
        """Runs when relationships are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        self.hide_removed_entities(db_map_data, RelationshipItem)

    def add_db_map_ids_to_items(self, db_map_data, type_):
        """Goes through items of given type and adds the corresponding db_map ids.
        This could mean either restoring removed (db_map, id) tuples previously removed,
        or adding new (db_map, id) tuples.

        Args:
            db_map_data (dict(DiffDatabaseMapping, list)): List of added items keyed by db_map

        Returns:
            list: tuples (db_map, id) that didn't match any item in the view.
        """
        get_key = {ObjectItem: self._get_object_key, RelationshipItem: self._get_relationship_key}[type_]
        added_db_map_ids_by_key = {}
        for db_map, entities in db_map_data.items():
            for entity in entities:
                db_map_id = (db_map, entity["id"])
                key = get_key(db_map_id)
                added_db_map_ids_by_key.setdefault(key, set()).add(db_map_id)
        restored_items = set()
        for item in self.ui.graphicsView.items():
            if not isinstance(item, type_):
                continue
            for db_map_id in item.original_db_map_ids:
                try:
                    key = get_key(db_map_id)
                except KeyError:
                    continue
                db_map_ids = added_db_map_ids_by_key.pop(key, None)
                if db_map_ids:
                    item.add_db_map_ids(db_map_ids)
                    restored_items.add(item)
        for item in restored_items:
            self.ui.graphicsView.removed_items.discard(item)
            item.setVisible(True)
        return list(added_db_map_ids_by_key.values())

    def hide_removed_entities(self, db_map_data, type_):
        """Hides removed entities while saving them into a set.
        This allows entities to be restored in case the user undoes the operation."""
        removed_db_map_ids = {(db_map, x["id"]) for db_map, items in db_map_data.items() for x in items}
        self.added_db_map_relationship_ids -= removed_db_map_ids
        removed_items = set()
        for item in self.ui.graphicsView.items():
            if not isinstance(item, type_):
                continue
            item.remove_db_map_ids(removed_db_map_ids)
            if not item.db_map_ids:
                removed_items.add(item)
        if not removed_items:
            return
        self.ui.graphicsView.removed_items |= removed_items
        scene = self.scene
        self.scene = None
        for item in removed_items:
            item.setVisible(False)
        self.scene = scene

    @Slot(bool)
    def _handle_entity_graph_visibility_changed(self, visible):
        if not visible:
            self._stop_layout_generators()
            return
        if self._owes_graph:
            QTimer.singleShot(100, self.build_graph)

    @Slot(dict)
    def _handle_tree_selection_changed(self, selected):
        """Stores the given selection of entity tree indexes and builds graph."""
        self._renew_fetch_parents()
        self.selected_tree_inds = selected
        self.added_db_map_relationship_ids.clear()
        self._extending_graph = True
        self.build_graph()

    @Slot(bool)
    def rebuild_graph(self, _checked=False):
        self.db_map_object_id_sets.clear()
        self.db_map_relationship_id_sets.clear()
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
        if not self._update_graph_data():
            return
        self._owes_graph = False
        self.ui.graphicsView.clear_cross_hairs_items()  # Needed
        self._persistent = persistent
        self._stop_layout_generators()
        self._layout_gen_id = monotonic()
        self.layout_gens[self._layout_gen_id] = layout_gen = self._make_layout_generator()
        self._progress_bar_widget.set_layout_generator(layout_gen)
        self._progress_bar_widget.show()
        layout_gen.layout_available.connect(self._complete_graph)
        layout_gen.finished.connect(lambda id_: self.layout_gens.pop(id_, None))  # Lambda to avoid issues in Python 3.7
        self._thread_pool.start(layout_gen)

    def _stop_layout_generators(self):
        for layout_gen in self.layout_gens.values():
            layout_gen.stop()

    def _complete_graph(self, layout_gen_id, x, y):
        """
        Args:
            layout_gen_id (object)
            x (list): Horizontal coordinates
            y (list): Vertical coordinates
        """
        # Ignore layouts from obsolete generators
        if layout_gen_id != self._layout_gen_id:
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
        for fetch_parent in (self._object_fetch_parent, self._relationship_fetch_parent):
            for db_map in self.db_maps:
                if self.db_mngr.can_fetch_more(db_map, fetch_parent):
                    self.db_mngr.fetch_more(db_map, fetch_parent)
        if "root" in self.selected_tree_inds:
            return (
                set((db_map, x["id"]) for db_map in self.db_maps for x in self.db_mngr.get_items(db_map, "object")),
                set(),
            )
        selected_object_ids = set()
        selected_relationship_ids = set()
        for index in self.selected_tree_inds.get("object", {}):
            item = index.model().item_from_index(index)
            selected_object_ids |= set(item.db_map_ids.items())
        for index in self.selected_tree_inds.get("relationship", {}):
            item = index.model().item_from_index(index)
            selected_relationship_ids |= set(item.db_map_ids.items())
        for index in self.selected_tree_inds.get("object_class", {}):
            item = index.model().item_from_index(index)
            selected_object_ids |= set(
                (db_map, x["id"])
                for db_map, id_ in item.db_map_ids.items()
                for x in self.db_mngr.get_items(db_map, "object")
                if x["class_id"] == id_
            )
        for index in self.selected_tree_inds.get("relationship_class", {}):
            item = index.model().item_from_index(index)
            selected_relationship_ids |= set(
                (db_map, x["id"])
                for db_map, id_ in item.db_map_ids.items()
                for x in self.db_mngr.get_items(db_map, "relationship")
                if x["class_id"] == id_
            )
        return selected_object_ids, selected_relationship_ids

    def _get_db_map_relationships_for_graph(self, db_map_object_ids, db_map_relationship_ids):
        cond = any if self.ui.graphicsView.auto_expand_objects else all
        return [
            (db_map, x)
            for db_map in self.db_maps
            for x in self.db_mngr.get_items(db_map, "relationship", only_visible=False)
            if cond(((db_map, id_) in db_map_object_ids for id_ in x["object_id_list"]))
        ] + [(db_map, self.db_mngr.get_item(db_map, "relationship", id_)) for db_map, id_ in db_map_relationship_ids]

    def _update_graph_data(self):
        """Updates data for graph according to selection in trees."""
        db_map_object_ids, db_map_relationship_ids = self._get_selected_entity_ids()
        db_map_relationship_ids.update(self.added_db_map_relationship_ids)
        pruned_db_map_entity_ids = {
            id_ for ids in self.ui.graphicsView.pruned_db_map_entity_ids.values() for id_ in ids
        }
        db_map_object_ids -= pruned_db_map_entity_ids
        db_map_relationship_ids -= pruned_db_map_entity_ids
        db_map_relationships = self._get_db_map_relationships_for_graph(db_map_object_ids, db_map_relationship_ids)
        db_map_object_id_lists = dict()
        max_rel_dim = (
            self.ui.graphicsView.max_relationship_dimension
            if not self.ui.graphicsView.disable_max_relationship_dimension
            else sys.maxsize
        )
        for db_map, relationship in db_map_relationships:
            if (db_map, relationship["id"]) in pruned_db_map_entity_ids:
                continue
            db_map_object_id_list = [
                (db_map, id_) for id_ in relationship["object_id_list"] if (db_map, id_) not in pruned_db_map_entity_ids
            ]
            if len(db_map_object_id_list) < 2 or len(db_map_object_id_list) > max_rel_dim:
                continue
            db_map_object_ids.update(db_map_object_id_list)
            db_map_object_id_lists[db_map, relationship["id"]] = db_map_object_id_list
        db_map_object_ids_by_key = {}
        db_map_relationship_ids_by_key = {}
        for db_map_object_id in db_map_object_ids:
            key = self._get_object_key(db_map_object_id)
            db_map_object_ids_by_key.setdefault(key, set()).add(db_map_object_id)
        for db_map_relationship_id in db_map_object_id_lists:
            key = self._get_relationship_key(db_map_relationship_id)
            db_map_relationship_ids_by_key.setdefault(key, set()).add(db_map_relationship_id)

        new_db_map_object_id_sets = list(db_map_object_ids_by_key.values())
        new_db_map_relationship_id_sets = list(db_map_relationship_ids_by_key.values())
        if (
            new_db_map_object_id_sets == self.db_map_object_id_sets
            and new_db_map_relationship_id_sets == self.db_map_relationship_id_sets
        ):
            return False
        self.db_map_object_id_sets = new_db_map_object_id_sets
        self.db_map_relationship_id_sets = new_db_map_relationship_id_sets
        self._update_src_dst_inds(db_map_object_id_lists)
        return True

    def _get_object_key(self, db_map_object_id):
        db_map, object_id = db_map_object_id
        object_ = self.db_mngr.get_item(db_map, "object", object_id)
        key = (object_["class_name"], object_["name"])
        if not self.ui.graphicsView.merge_dbs:
            key += (db_map.codename,)
        return key

    def _get_relationship_key(self, db_map_relationship_id):
        db_map, relationship_id = db_map_relationship_id
        relationship = self.db_mngr.get_item(db_map, "relationship", relationship_id)
        key = (relationship["class_name"], relationship["object_class_name_list"], relationship["object_name_list"])
        if not self.ui.graphicsView.merge_dbs:
            key += (db_map.codename,)
        return key

    def _update_src_dst_inds(self, db_map_object_id_lists):
        self.src_inds = list()
        self.dst_inds = list()
        obj_ind_lookup = {
            db_map_obj_id: k
            for k, db_map_obj_ids in enumerate(self.db_map_object_id_sets)
            for db_map_obj_id in db_map_obj_ids
        }
        rel_ind_lookup = {
            db_map_rel_id: len(self.db_map_object_id_sets) + k
            for k, db_map_rel_ids in enumerate(self.db_map_relationship_id_sets)
            for db_map_rel_id in db_map_rel_ids
        }
        edges = dict()
        for db_map_rel_id, db_map_object_id_list in db_map_object_id_lists.items():
            object_inds = [obj_ind_lookup[db_map_obj_id] for db_map_obj_id in db_map_object_id_list]
            relationship_ind = rel_ind_lookup[db_map_rel_id]
            for object_ind in object_inds:
                edges[relationship_ind, object_ind] = None
        for src, dst in edges:  # pylint: disable=dict-iter-missing-items
            self.src_inds.append(src)
            self.dst_inds.append(dst)

    def _get_parameter_positions(self, parameter_name):
        if not parameter_name:
            yield from []
        for db_map in self.db_maps:
            for p in self.db_mngr.get_items_by_field(
                db_map, "parameter_value", "parameter_name", parameter_name, only_visible=False
            ):
                pos = from_database(p["value"], p["type"])
                if isinstance(pos, float):
                    yield (db_map, p["entity_id"]), pos

    def _make_layout_generator(self):
        """Returns a layout generator for the current graph.

        Returns:
            GraphLayoutGeneratorRunnable
        """
        fixed_positions = {}
        if self._persistent:
            for item in self.ui.graphicsView.items():
                if isinstance(item, EntityItem):
                    fixed_positions[item.first_db_map, item.first_id] = {"x": item.pos().x(), "y": item.pos().y()}
        param_pos_x = dict(self._get_parameter_positions(self.ui.graphicsView.pos_x_parameter))
        param_pos_y = dict(self._get_parameter_positions(self.ui.graphicsView.pos_y_parameter))
        for db_map_entity_id in param_pos_x.keys() & param_pos_y.keys():
            fixed_positions[db_map_entity_id] = {"x": param_pos_x[db_map_entity_id], "y": param_pos_y[db_map_entity_id]}
        db_map_entity_ids = self.db_map_object_id_sets + self.db_map_relationship_id_sets
        heavy_positions = {
            ind: fixed_positions[db_map_entity_id]
            for ind, db_map_entity_ids in enumerate(db_map_entity_ids)
            for db_map_entity_id in db_map_entity_ids
            if db_map_entity_id in fixed_positions
        }
        return GraphLayoutGeneratorRunnable(
            self._layout_gen_id,
            len(db_map_entity_ids),
            self.src_inds,
            self.dst_inds,
            self._ARC_LENGTH_HINT,
            heavy_positions=heavy_positions,
        )

    def _make_new_items(self, x, y):
        """Returns new items for the graph.

        Args:
            x (list)
            y (list)
        """
        self.object_items = [
            ObjectItem(self, x[i], y[i], self.VERTEX_EXTENT, tuple(db_map_object_ids))
            for i, db_map_object_ids in enumerate(self.db_map_object_id_sets)
        ]
        offset = len(self.object_items)
        self.relationship_items = [
            RelationshipItem(
                self, x[offset + i], y[offset + i], 0.5 * self.VERTEX_EXTENT, tuple(db_map_relationship_id)
            )
            for i, db_map_relationship_id in enumerate(self.db_map_relationship_id_sets)
        ]
        self.arc_items = [
            ArcItem(self.relationship_items[rel_ind - offset], self.object_items[obj_ind], self._ARC_WIDTH)
            for rel_ind, obj_ind in zip(self.src_inds, self.dst_inds)
        ]
        return any(self.object_items)

    def _add_new_items(self):
        for item in self.object_items + self.relationship_items + self.arc_items:
            self.scene.addItem(item)

    def start_relationship(self, db_map, relationship_class, obj_item):
        """Starts a relationship from the given object item.

        Args:
            db_map (DiffDatabaseMapping)
            relationship_class (dict)
            obj_item (..graphics_items.ObjectItem)
        """
        object_class_ids_to_go = relationship_class["object_class_id_list"].copy()
        object_class_ids_to_go.remove(obj_item.entity_class_id(db_map))
        relationship_class["object_class_ids_to_go"] = object_class_ids_to_go
        relationship_class["db_map"] = db_map
        db_map_ids = ((db_map, None),)
        ch_item = CrossHairsItem(
            self, obj_item.pos().x(), obj_item.pos().y(), 0.8 * self.VERTEX_EXTENT, db_map_ids=db_map_ids
        )
        ch_rel_item = CrossHairsRelationshipItem(
            self, obj_item.pos().x(), obj_item.pos().y(), 0.5 * self.VERTEX_EXTENT, db_map_ids=db_map_ids
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
        db_map = relationship_class["db_map"]
        relationships = set()
        object_class_id_list = relationship_class["object_class_id_list"]
        for item_permutation in itertools.permutations(object_items):
            if [item.entity_class_id(db_map) for item in item_permutation] == object_class_id_list:
                relationship = tuple(item.entity_name for item in item_permutation)
                relationships.add(relationship)
        dialog = AddReadyRelationshipsDialog(self, relationship_class, list(relationships), self.db_mngr, db_map)
        dialog.accepted.connect(self._begin_add_relationships)
        dialog.show()

    def _begin_add_relationships(self):
        self._adding_relationships = True

    def _end_add_relationships(self):
        self._adding_relationships = False

    def add_objects_at_position(self, pos):
        self._pos_for_added_objects = pos
        parent_item = self.object_tree_model.root_item
        dialog = AddObjectsDialog(self, parent_item, self.db_mngr, *self.db_maps)
        dialog.show()

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
        if self.scene is not None:
            self.scene.deleteLater()
        self.scene = None
