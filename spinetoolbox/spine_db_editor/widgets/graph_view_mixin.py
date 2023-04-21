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
from ..graphics_items import EntityItem, ArcItem, CrossHairsItem, CrossHairsEntityItem, CrossHairsArcItem
from .graph_layout_generator import GraphLayoutGeneratorRunnable, ProgressBarWidget
from .add_items_dialogs import AddEntitiesDialog, AddReadyEntitiesDialog


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
        self.entity_items = []
        self.arc_items = []
        self.selected_tree_inds = {}
        self.db_map_entity_id_sets = []
        self.entity_inds = []
        self.element_inds = []
        self._connecting_entities = False
        self._pos_for_added_entities = None
        self.added_db_map_entity_ids = set()
        self._thread_pool = QThreadPool()
        self.layout_gens = {}
        self._layout_gen_id = None
        self._extend_graph_timer = QTimer(self)
        self._extend_graph_timer.setSingleShot(True)
        self._extend_graph_timer.setInterval(100)
        self._extend_graph_timer.timeout.connect(self.build_graph)
        self._extending_graph = False
        self._entity_fetch_parent = None

    def _renew_fetch_parents(self):
        if self._entity_fetch_parent is not None:
            self._entity_fetch_parent.set_obsolete(True)
        self._entity_fetch_parent = FlexibleFetchParent(
            "entity",
            handle_items_added=self._graph_handle_entities_added,
            handle_items_removed=self._graph_handle_entities_removed,
            handle_items_updated=self._graph_handle_entities_updated,
            owner=self,
        )
        for db_map in self.db_maps:
            if self.db_mngr.can_fetch_more(db_map, self._entity_fetch_parent):
                self.db_mngr.fetch_more(db_map, self._entity_fetch_parent)

    @Slot(bool)
    def _stop_extending_graph(self, _=False):
        self._extending_graph = False

    def init_models(self):
        self.scene.clear()
        super().init_models()

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
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

    def _graph_handle_entities_added(self, db_map_data):
        """Runs when entities are added to the db.
        Adds the new entities to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        new_db_map_id_sets = self.add_db_map_ids_to_items(db_map_data)
        if not new_db_map_id_sets:
            return
        if self._pos_for_added_entities is not None:
            spread = self.VERTEX_EXTENT * self.ui.graphicsView.zoom_factor
            gen = GraphLayoutGeneratorRunnable(None, len(new_db_map_id_sets), spread=spread)
            gen.run()
            x = self._pos_for_added_entities.x()
            y = self._pos_for_added_entities.y()
            for dx, dy, db_map_ids in zip(gen.x, gen.y, new_db_map_id_sets):
                entity_item = EntityItem(self, x + dx, y + dy, self.VERTEX_EXTENT, tuple(db_map_ids))
                self.scene.addItem(entity_item)
                entity_item.apply_zoom(self.ui.graphicsView.zoom_factor)
            self._pos_for_added_entities = None
        elif self._connecting_entities:
            for db_map_ids in new_db_map_id_sets:
                self.added_db_map_entity_ids.update(db_map_ids)
            self.build_graph(persistent=True)
            self._end_connect_entities()
        elif self._extending_graph:
            self._extend_graph_timer.start()

    def _graph_handle_entities_removed(self, db_map_data):
        """Runs when entities are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        self.hide_removed_entities(db_map_data)

    def _graph_handle_entities_updated(self, db_map_data):
        """Runs when entities are updated in the db.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        updated_ids = {(db_map, x["id"]) for db_map, ents in db_map_data.items() for x in ents}
        for item in self.ui.graphicsView.items():
            if isinstance(item, EntityItem) and set(item.db_map_ids).intersection(updated_ids):
                if not item.update_name():
                    self.build_graph(persistent=True)
                    break

    def add_db_map_ids_to_items(self, db_map_data):
        """Goes through entity items and adds the corresponding db_map ids.
        This could mean either restoring removed (db_map, id) tuples previously removed,
        or adding new (db_map, id) tuples.

        Args:
            db_map_data (dict(DiffDatabaseMapping, list)): List of added items keyed by db_map

        Returns:
            list: tuples (db_map, id) that didn't match any item in the view.
        """
        # FIXME: It looks like undoing twice and then redoing once restores all the items.
        # It should only restores the items corresponding to one redo operation at a time
        added_db_map_ids_by_key = {}
        for db_map, entities in db_map_data.items():
            for entity in entities:
                db_map_id = (db_map, entity["id"])
                key = self._get_entity_key(db_map_id)
                added_db_map_ids_by_key.setdefault(key, set()).add(db_map_id)
        restored_items = set()
        for item in self.ui.graphicsView.items():
            if not isinstance(item, EntityItem):
                continue
            for db_map_id in item.original_db_map_ids:
                try:
                    key = self._get_entity_key(db_map_id)
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

    def hide_removed_entities(self, db_map_data):
        """Hides removed entities while saving them into a set.
        This allows entities to be restored in case the user undoes the operation."""
        removed_db_map_ids = {(db_map, x["id"]) for db_map, items in db_map_data.items() for x in items}
        self.added_db_map_entity_ids -= removed_db_map_ids
        removed_items = set()
        for item in self.ui.graphicsView.items():
            if not isinstance(item, EntityItem):
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
    def _handle_entity_tree_selection_changed(self, selected):
        """Stores the given selection of entity tree indexes and builds graph."""
        super()._handle_entity_tree_selection_changed(selected)
        self._renew_fetch_parents()
        self.selected_tree_inds = selected
        self.added_db_map_entity_ids.clear()
        self._extending_graph = True
        self.build_graph()

    @Slot(bool)
    def rebuild_graph(self, _checked=False):
        self.db_map_entity_id_sets.clear()
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

    def _get_selected_db_map_entity_ids(self):
        """Returns a set of ids corresponding to selected entities in the trees.

        Returns:
            set: selected object ids
            set: selected relationship ids
        """
        if "root" in self.selected_tree_inds:
            return set((db_map, x["id"]) for db_map in self.db_maps for x in self.db_mngr.get_items(db_map, "entity"))
        db_map_entity_ids = set()
        for index in self.selected_tree_inds.get("entity", {}):
            item = index.model().item_from_index(index)
            db_map_entity_ids |= set(item.db_map_ids.items())
        for index in self.selected_tree_inds.get("entity_class", {}):
            item = index.model().item_from_index(index)
            db_map_entity_ids |= set(
                (db_map, x["id"])
                for db_map, id_ in item.db_map_ids.items()
                for x in self.db_mngr.get_items(db_map, "entity")
                if x["class_id"] == id_
            )
        return db_map_entity_ids

    def _get_db_map_entities_for_graph(self, db_map_entity_ids):
        cond = any if self.ui.graphicsView.auto_expand_entities else all
        return [
            (db_map, x)
            for db_map in self.db_maps
            for x in self.db_mngr.get_items(db_map, "entity", only_visible=False)
            if cond(((db_map, id_) in db_map_entity_ids for id_ in x["element_id_list"]))
        ] + [
            (db_map, self.db_mngr.get_item(db_map, "entity", id_, only_visible=False))
            for db_map, id_ in db_map_entity_ids
        ]

    def _update_graph_data(self):
        """Updates data for graph according to selection in trees."""
        pruned_db_map_entity_ids = {
            id_ for ids in self.ui.graphicsView.pruned_db_map_entity_ids.values() for id_ in ids
        }
        db_map_entity_ids = self._get_selected_db_map_entity_ids()
        db_map_entity_ids |= self.added_db_map_entity_ids
        db_map_entity_ids -= pruned_db_map_entity_ids
        db_map_entities = self._get_db_map_entities_for_graph(db_map_entity_ids)
        max_ent_dim = (
            self.ui.graphicsView.max_entity_dimension
            if not self.ui.graphicsView.disable_max_relationship_dimension
            else sys.maxsize
        )
        db_map_element_id_lists = {}
        for db_map, entity in db_map_entities:
            if (db_map, entity["id"]) in pruned_db_map_entity_ids:
                continue
            db_map_element_id_list = [
                (db_map, id_) for id_ in entity["element_id_list"] if (db_map, id_) not in pruned_db_map_entity_ids
            ]
            el_count = len(db_map_element_id_list)
            if el_count != 0 and (el_count < 2 or el_count > max_ent_dim):
                continue
            db_map_entity_ids.add((db_map, entity["id"]))
            db_map_entity_ids.update(db_map_element_id_list)
            db_map_element_id_lists[db_map, entity["id"]] = db_map_element_id_list
        db_map_entity_ids_by_key = {}
        for db_map_entity_id in db_map_entity_ids:
            key = self._get_entity_key(db_map_entity_id)
            db_map_entity_ids_by_key.setdefault(key, set()).add(db_map_entity_id)
        new_db_map_entity_id_sets = list(db_map_entity_ids_by_key.values())
        if new_db_map_entity_id_sets == self.db_map_entity_id_sets:
            return False
        self.db_map_entity_id_sets = new_db_map_entity_id_sets
        self._update_entity_element_inds(db_map_element_id_lists)
        return True

    def _get_entity_key(self, db_map_entity_id):
        db_map, entity_id = db_map_entity_id
        entity = self.db_mngr.get_item(db_map, "entity", entity_id)
        key = (entity["class_name"], entity["dimension_name_list"], entity["byname"])
        if not self.ui.graphicsView.merge_dbs:
            key += (db_map.codename,)
        return key

    def _update_entity_element_inds(self, db_map_element_id_lists):
        self.entity_inds = []
        self.element_inds = []
        ent_ind_lookup = {
            db_map_ent_id: k
            for k, db_map_ent_ids in enumerate(self.db_map_entity_id_sets)
            for db_map_ent_id in db_map_ent_ids
        }
        edges = {}
        for db_map_entity_id, db_map_element_id_list in db_map_element_id_lists.items():
            el_inds = [ent_ind_lookup[db_map_el_id] for db_map_el_id in db_map_element_id_list]
            ent_ind = ent_ind_lookup[db_map_entity_id]
            for el_ind in el_inds:
                edges[ent_ind, el_ind] = None
        for ent_ind, el_ind in edges:  # pylint: disable=dict-iter-missing-items
            self.entity_inds.append(ent_ind)
            self.element_inds.append(el_ind)

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
        heavy_positions = {
            ind: fixed_positions[db_map_entity_id]
            for ind, db_map_entity_ids in enumerate(self.db_map_entity_id_sets)
            for db_map_entity_id in db_map_entity_ids
            if db_map_entity_id in fixed_positions
        }
        return GraphLayoutGeneratorRunnable(
            self._layout_gen_id,
            len(self.db_map_entity_id_sets),
            self.entity_inds,
            self.element_inds,
            self._ARC_LENGTH_HINT,
            heavy_positions=heavy_positions,
        )

    def _make_new_items(self, x, y):
        """Returns new items for the graph.

        Args:
            x (list)
            y (list)
        """
        self.entity_items = [
            EntityItem(self, x[i], y[i], self.VERTEX_EXTENT, tuple(db_map_entity_ids))
            for i, db_map_entity_ids in enumerate(self.db_map_entity_id_sets)
        ]
        self.arc_items = [
            ArcItem(self.entity_items[ent_id], self.entity_items[el_ind], self._ARC_WIDTH)
            for ent_id, el_ind in zip(self.entity_inds, self.element_inds)
        ]
        return any(self.entity_items)

    def _add_new_items(self):
        for item in self.entity_items + self.arc_items:
            self.scene.addItem(item)

    def start_connecting_entities(self, db_map, entity_class, ent_item):
        """Starts connecting entites with the given entity item.

        Args:
            db_map (DiffDatabaseMapping)
            entity_class (dict)
            ent_item (..graphics_items.EntityItem)
        """
        dimension_ids_to_go = entity_class["dimension_id_list"].copy()
        dimension_ids_to_go.remove(ent_item.entity_class_id(db_map))
        entity_class["dimension_ids_to_go"] = dimension_ids_to_go
        entity_class["db_map"] = db_map
        db_map_ids = ((db_map, None),)
        ch_item = CrossHairsItem(
            self, ent_item.pos().x(), ent_item.pos().y(), 0.8 * self.VERTEX_EXTENT, db_map_ids=db_map_ids
        )
        ch_ent_item = CrossHairsEntityItem(
            self, ent_item.pos().x(), ent_item.pos().y(), 0.5 * self.VERTEX_EXTENT, db_map_ids=db_map_ids
        )
        ch_arc_item1 = CrossHairsArcItem(ch_ent_item, ent_item, self._ARC_WIDTH)
        ch_arc_item2 = CrossHairsArcItem(ch_ent_item, ch_item, self._ARC_WIDTH)
        ch_ent_item.refresh_icon()
        self.ui.graphicsView.set_cross_hairs_items(entity_class, [ch_item, ch_ent_item, ch_arc_item1, ch_arc_item2])

    def finalize_connecting_entities(self, entity_class, *entity_items):
        """Tries to add multi dimensional entity with the given entity items as elements.

        Args:
            entity_class (dict)
            entity_items (..graphics_items.EntityItem)
        """
        db_map = entity_class["db_map"]
        entities = set()
        dimension_id_list = entity_class["dimension_id_list"]
        for item_permutation in itertools.permutations(entity_items):
            if [item.entity_class_id(db_map) for item in item_permutation] == dimension_id_list:
                entity = tuple(item.entity_name for item in item_permutation)
                entities.add(entity)
        dialog = AddReadyEntitiesDialog(self, entity_class, list(entities), self.db_mngr, db_map)
        dialog.accepted.connect(self._begin_connect_entities)
        dialog.show()

    def _begin_connect_entities(self):
        self._connecting_entities = True

    def _end_connect_entities(self):
        self._connecting_entities = False

    def add_entities_at_position(self, pos):
        self._pos_for_added_entities = pos
        parent_item = self.entity_tree_model.root_item
        dialog = AddEntitiesDialog(self, parent_item, self.db_mngr, *self.db_maps)
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
