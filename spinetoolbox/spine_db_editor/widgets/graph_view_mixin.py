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

"""Contains the GraphViewMixin class."""
import itertools
import json
from time import monotonic
from PySide6.QtCore import Slot, QTimer, QThreadPool
from spinedb_api import from_database
from spinedb_api.parameter_value import IndexedValue, TimeSeries
from ...widgets.custom_qgraphicsscene import CustomGraphicsScene
from ...helpers import get_save_file_name_in_last_dir, get_open_file_name_in_last_dir, busy_effect, remove_first
from ...fetch_parent import FlexibleFetchParent
from ..graphics_items import EntityItem, ArcItem, CrossHairsItem, CrossHairsEntityItem, CrossHairsArcItem
from .graph_layout_generator import GraphLayoutGenerator, GraphLayoutGeneratorRunnable
from .add_items_dialogs import AddEntitiesDialog, AddReadyEntitiesDialog


def _min_value(pv):
    if isinstance(pv, IndexedValue):
        return min(pv.values)
    return pv


def _max_value(pv):
    if isinstance(pv, IndexedValue):
        return max(pv.values)
    return pv


def _get_value(pv, index):
    if isinstance(pv, IndexedValue):
        try:
            return pv.get_nearest(index)
        except Exception:
            return None
    return pv


def _min_max(pvs):
    pvs = [pv for pv in pvs if pv is not None]
    if not pvs:
        return None, None
    return min(_min_value(pv) for pv in pvs), max(_max_value(pv) for pv in pvs)


@busy_effect
def _min_max_indexes(pvs):
    return min(pv.indexes[0] for pv in pvs), max(pv.indexes[-1] for pv in pvs)


class GraphViewMixin:
    """Provides the graph view for the DB editor."""

    NOT_SPECIFIED = object()
    _VERTEX_EXTENT = 64
    _ARC_WIDTH = 0.05 * _VERTEX_EXTENT
    _ARC_LENGTH_HINT = 1.0 * _VERTEX_EXTENT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._owes_graph = False
        self.scene = CustomGraphicsScene(self)
        self.ui.graphicsView.setScene(self.scene)
        self.ui.graphicsView.connect_spine_db_editor(self)
        self.ui.progress_bar_widget.hide()
        self.ui.time_line_widget.hide()
        self.ui.time_line_widget.index_changed.connect(self._update_time_line_index)
        self.ui.legend_widget.hide()
        self.entity_items = []
        self.arc_items = []
        self._selected_item_type_db_map_ids = {}
        self.pruned_db_map_entity_ids = {}
        self.expanded_db_map_entity_ids = set()
        self.collapsed_db_map_entity_ids = set()
        self.db_map_entity_id_sets = []
        self.entity_inds = []
        self.element_inds = []
        self._entity_offsets = {}
        self._pvs_by_pname = {}
        self._val_ranges_by_pname = {}
        self._persisted_positions = {}
        self._thread_pool = QThreadPool()
        self.layout_gens = {}
        self._layout_gen_id = None
        self._entity_fetch_parent = FlexibleFetchParent(
            "entity",
            accepts_item=self._accepts_entity_item,
            handle_items_added=self._graph_handle_entities_added,
            handle_items_removed=self._graph_handle_entities_removed,
            handle_items_updated=self._graph_handle_entities_updated,
            owner=self,
        )
        self._parameter_value_fetch_parent = FlexibleFetchParent(
            "parameter_value", handle_items_added=self._graph_handle_parameter_values_added, owner=self
        )
        self._graph_fetch_more_later()

    @Slot(int)
    def _update_time_line_index(self, index):
        for item in self.ui.graphicsView.entity_items:
            item.update_props(index)

    def _graph_fetch_more_later(self, entity=True, parameter_value=True):
        QTimer.singleShot(0, lambda: self._graph_fetch_more(entity=entity, parameter_value=parameter_value))

    def _graph_fetch_more(self, entity=True, parameter_value=True):
        parents = []
        if entity:
            parents.append(self._entity_fetch_parent)
        if parameter_value:
            parents.append(self._parameter_value_fetch_parent)
        for parent in parents:
            for db_map in self.db_maps:
                if self.db_mngr.can_fetch_more(db_map, parent):
                    self.db_mngr.fetch_more(db_map, parent)

    def _graph_fetch_more_parameter_value(self):
        QTimer.singleShot(0, lambda: self._graph_fetch_more_parents(self._parameter_value_fetch_parent))

    def _graph_fetch_more_entity(self):
        QTimer.singleShot(0, lambda: self._graph_fetch_more_parents(self._parameter_value_fetch_parent))

    def init_models(self):
        self.scene.clear()
        super().init_models()

    def connect_signals(self):
        """Connects signals."""
        super().connect_signals()
        self.ui.treeView_entity.tree_selection_changed.connect(self._handle_entity_tree_selection_changed_in_graph)
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

    def _all_pruned_db_map_entity_ids(self):
        return {db_map_id for db_map_ids in self.pruned_db_map_entity_ids.values() for db_map_id in db_map_ids}

    def _accepts_entity_item(self, item, db_map):
        if (db_map, item["id"]) in self.expanded_db_map_entity_ids:
            return True
        if (db_map, item["id"]) in self.collapsed_db_map_entity_ids:
            return False
        if (db_map, item["id"]) in self._all_pruned_db_map_entity_ids():
            return False
        if "root" in self._selected_item_type_db_map_ids:
            return True
        selected_entity_ids = self._selected_item_type_db_map_ids.get("entity", {}).get(db_map, ())
        if item["id"] in selected_entity_ids:
            return True
        selected_class_ids = self._selected_item_type_db_map_ids.get("entity_class", {}).get(db_map, ())
        if item["class_id"] in selected_class_ids:
            return True
        cond = any if self.ui.graphicsView.get_property("auto_expand_entities") else all
        if item["element_id_list"] and cond(id_ in selected_entity_ids for id_ in item["element_id_list"]):
            return True
        if item["dimension_id_list"] and cond(id_ in selected_class_ids for id_ in item["dimension_id_list"]):
            return True
        return False

    def _graph_handle_entities_added(self, db_map_data):
        """Runs when entities are added to the db.
        Adds the new entities to the graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        new_db_map_id_sets = self.add_db_map_ids_to_items(db_map_data)
        if not new_db_map_id_sets:
            self._graph_fetch_more_later(entity=True, parameter_value=False)
            return
        self._refresh_graph()

    def _graph_handle_entities_removed(self, db_map_data):
        """Runs when entities are removed from the db. Rebuilds graph if needed.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        removed_db_map_ids = {(db_map, x["id"]) for db_map, items in db_map_data.items() for x in items}
        for item in self.ui.graphicsView.entity_items:
            item.remove_db_map_ids(removed_db_map_ids)
            if not item.db_map_ids:
                item.setVisible(False)

    def _graph_handle_entities_updated(self, db_map_data):
        """Runs when entities are updated in the db.

        Args:
            db_map_data (dict): list of dictionary-items keyed by DiffDatabaseMapping instance.
        """
        updated_ids = {(db_map, x["id"]) for db_map, ents in db_map_data.items() for x in ents}
        for item in self.ui.graphicsView.items():
            if isinstance(item, EntityItem) and set(item.db_map_ids).intersection(updated_ids):
                if not item.has_unique_key():
                    self.build_graph(persistent=True)
                    break
                item.set_up()

    def _db_map_ids_by_key(self, db_map_data):
        added_db_map_ids_by_key = {}
        for db_map, entities in db_map_data.items():
            for entity in entities:
                db_map_id = (db_map, entity["id"])
                key = self.get_entity_key(db_map_id)
                added_db_map_ids_by_key.setdefault(key, set()).add(db_map_id)
        return added_db_map_ids_by_key

    def add_db_map_ids_to_items(self, db_map_data):
        """Goes through entity items and adds the corresponding db_map ids.
        This could mean either restoring removed (db_map, id) tuples previously removed,
        or adding new (db_map, id) tuples.

        Args:
            db_map_data (dict(DiffDatabaseMapping, list)): List of added items keyed by db_map

        Returns:
            list: tuples (db_map, id) that didn't match any item in the view.
        """
        added_db_map_ids_by_key = self._db_map_ids_by_key(db_map_data)
        restored_items = set()
        for item in self.ui.graphicsView.items():
            if not isinstance(item, EntityItem):
                continue
            for db_map_id in item.original_db_map_ids:
                try:
                    key = self.get_entity_key(db_map_id)
                except KeyError:
                    continue
                db_map_ids = added_db_map_ids_by_key.pop(key, None)
                if db_map_ids:
                    item.add_db_map_ids(db_map_ids)
                    restored_items.add(item)
        for item in restored_items:
            item.setVisible(True)
        return list(added_db_map_ids_by_key.values())

    def _graph_handle_parameter_values_added(self, db_map_data):
        pnames = {x["parameter_definition_name"] for db_map in self.db_maps for x in db_map_data.get(db_map, ())}
        position_pnames = {self.ui.graphicsView.pos_x_parameter, self.ui.graphicsView.pos_y_parameter}
        property_pnames = {
            self.ui.graphicsView.name_parameter,
            self.ui.graphicsView.color_parameter,
            self.ui.graphicsView.arc_width_parameter,
            self.ui.graphicsView.vertex_radius_parameter,
        }
        if pnames & position_pnames:
            self._refresh_graph()
            return
        if pnames & property_pnames:
            self.polish_items()
        self._graph_fetch_more_later(entity=False, parameter_value=True)

    def polish_items(self):
        self._update_property_pvs()
        for item in self.ui.graphicsView.entity_items:
            item.set_up()

    def _update_property_pvs(self):
        self._pvs_by_pname = {
            pname: {
                (db_map, ent_id): self._get_pv(db_map, ent_id, pname)
                for db_map_ent_ids in self.db_map_entity_id_sets
                for db_map, ent_id in db_map_ent_ids
            }
            for pname in (
                self.ui.graphicsView.color_parameter,
                self.ui.graphicsView.arc_width_parameter,
                self.ui.graphicsView.vertex_radius_parameter,
            )
            if pname
        }
        self._val_ranges_by_pname = {pname: _min_max(pvs.values()) for pname, pvs in self._pvs_by_pname.items()}
        if self._val_ranges_by_pname:
            legend = [
                (legend_type, pname, self._val_ranges_by_pname.get(pname))
                for (legend_type, pname) in (
                    ("color", self.ui.graphicsView.color_parameter),
                    ("width", self.ui.graphicsView.arc_width_parameter),
                    ("width", self.ui.graphicsView.vertex_radius_parameter),
                )
            ]
            self.ui.legend_widget.show()
            self.ui.legend_widget.set_legend(legend)
        else:
            self.ui.legend_widget.hide()
        ts_pvs = [pv for pname, pvs in self._pvs_by_pname.items() for pv in pvs.values() if isinstance(pv, TimeSeries)]
        if ts_pvs:
            min_, max_ = _min_max_indexes(ts_pvs)
            self.ui.time_line_widget.set_index_range(min_, max_)
        else:
            self.ui.time_line_widget.hide()

    @Slot(bool)
    def _handle_entity_graph_visibility_changed(self, visible):
        if not visible:
            self._stop_layout_generators()
            return
        if self._owes_graph:
            QTimer.singleShot(100, self.build_graph)

    @Slot(dict)
    def _handle_entity_tree_selection_changed_in_graph(self, selected):
        """Stores the given selection of entity tree indexes and builds graph."""
        self._update_selected_item_type_db_map_ids(selected)
        self.build_graph()

    def expand_graph(self, db_map_entity_ids):
        self.expanded_db_map_entity_ids.update(db_map_entity_ids)
        self.collapsed_db_map_entity_ids.difference_update(db_map_entity_ids)
        self.build_graph(persistent=True)

    def collapse_graph(self, db_map_entity_ids):
        self.expanded_db_map_entity_ids.difference_update(db_map_entity_ids)
        self.collapsed_db_map_entity_ids.update(db_map_entity_ids)
        self.build_graph(persistent=True)

    def prune_graph(self, key, db_map_entity_ids):
        self.pruned_db_map_entity_ids[key] = db_map_entity_ids
        self.build_graph()

    def restore_graph(self, key=None):
        if not self.pruned_db_map_entity_ids:
            return
        if key is None:
            self.pruned_db_map_entity_ids.clear()
            self.build_graph()
            return
        if self.pruned_db_map_entity_ids.pop(key, None) is not None:
            self.build_graph()

    def _get_db_map_graph_data(self):
        db_map_graph_data = {}
        for db_map in self.db_maps:
            graph_data = {
                "type": "graph_data",
                "selected_item_type_ids": {
                    item_type: list(db_map_ids.get(db_map, []))
                    for item_type, db_map_ids in self._selected_item_type_db_map_ids.items()
                },
                "pruned_entity_ids": [
                    id_
                    for db_map_ids in self.pruned_db_map_entity_ids.values()
                    for db_map_, id_ in db_map_ids
                    if db_map_ is db_map
                ],
                "expanded_entity_ids": [
                    id_
                    for db_map_ids in self.expanded_db_map_entity_ids
                    for db_map_, id_ in db_map_ids
                    if db_map_ is db_map
                ],
                "collapsed_entity_ids": [
                    id_
                    for db_map_ids in self.collapsed_db_map_entity_ids
                    for db_map_, id_ in db_map_ids
                    if db_map_ is db_map
                ],
                "pos_x_parameter": self.ui.graphicsView.pos_x_parameter,
                "pos_y_parameter": self.ui.graphicsView.pos_y_parameter,
                "name_parameter": self.ui.graphicsView.name_parameter,
                "color_parameter": self.ui.graphicsView.color_parameter,
                "arc_width_parameter": self.ui.graphicsView.arc_width_parameter,
                "vertex_radius_parameter": self.ui.graphicsView.vertex_radius_parameter,
                "bg_svg": self.ui.graphicsView.get_bg_svg(),
                "bg_rect": self.ui.graphicsView.get_bg_rect(),
                "properties": self.ui.graphicsView.get_all_properties(),
            }
            db_map_graph_data[db_map] = json.dumps(graph_data)
        return db_map_graph_data

    def save_graph_data(self, name):
        db_map_graph_data = self._get_db_map_graph_data()
        db_map_data = {db_map: [{"name": name, "value": gd}] for db_map, gd in db_map_graph_data.items()}
        self.db_mngr.add_metadata(db_map_data)
        # TODO: also add entity_metadata so it sticks

    def overwrite_graph_data(self, db_map_graph_data):
        db_map_graph_data_ = self._get_db_map_graph_data()
        db_map_data = {
            db_map: [{"id": db_map_graph_data[db_map]["id"], "value": gd}] for db_map, gd in db_map_graph_data_.items()
        }
        self.db_mngr.update_metadata(db_map_data)

    def get_db_map_graph_data_by_name(self):
        db_map_graph_data_by_name = {}
        for db_map in self.db_maps:
            for metadata_item in self.db_mngr.get_items(db_map, "metadata"):
                try:
                    graph_data = json.loads(metadata_item["value"])
                except json.decoder.JSONDecodeError:
                    continue
                if isinstance(graph_data, dict) and graph_data.get("type") == "graph_data":
                    graph_data["id"] = metadata_item["id"]
                    db_map_graph_data_by_name.setdefault(metadata_item["name"], {})[db_map] = graph_data
        return db_map_graph_data_by_name

    def load_graph_data(self, db_map_graph_data):
        if not db_map_graph_data:
            self.msg_error.emit("Invalid graph data")
        self._selected_item_type_db_map_ids = {}
        for db_map, gd in db_map_graph_data.items():
            for item_type, ids in gd["selected_item_type_ids"].items():
                self._selected_item_type_db_map_ids.setdefault(item_type, {})[db_map] = ids
        self.pruned_db_map_entity_ids = {
            "Pruned in loaded state": {
                (db_map, id_) for db_map, gd in db_map_graph_data.items() for id_ in gd["pruned_entity_ids"]
            }
        }
        self.expanded_db_map_entity_ids = {
            (db_map, id_) for db_map, gd in db_map_graph_data.items() for id_ in gd["expanded_entity_ids"]
        }
        self.collapsed_db_map_entity_ids = {
            (db_map, id_) for db_map, gd in db_map_graph_data.items() for id_ in gd["collapsed_entity_ids"]
        }
        graph_data = db_map_graph_data[self.first_db_map]
        self.ui.graphicsView.pos_x_parameter = graph_data["pos_x_parameter"]
        self.ui.graphicsView.pos_y_parameter = graph_data["pos_y_parameter"]
        self.ui.graphicsView.name_parameter = graph_data["name_parameter"]
        self.ui.graphicsView.color_parameter = graph_data["color_parameter"]
        self.ui.graphicsView.arc_width_parameter = graph_data["arc_width_parameter"]
        self.ui.graphicsView.vertex_radius_parameter = graph_data.get("vertex_radius_parameter", "")
        self.ui.graphicsView.set_bg_svg(graph_data["bg_svg"])
        self.ui.graphicsView.set_bg_rect(graph_data["bg_rect"])
        self.ui.graphicsView.set_many_properties(graph_data["properties"])
        self.build_graph()

    def remove_graph_data(self, name):
        db_map_typed_ids = {}
        for db_map in self.db_maps:
            metadata_item = next((x for x in self.db_mngr.get_items(db_map, "metadata") if x["name"] == name), None)
            if metadata_item is None:
                continue
            db_map_typed_ids[db_map] = {"metadata": {metadata_item["id"]}}
        self.db_mngr.remove_items(db_map_typed_ids)

    @Slot(bool)
    def rebuild_graph(self, _checked=False):
        self.db_map_entity_id_sets.clear()
        self.expanded_db_map_entity_ids.clear()
        self.collapsed_db_map_entity_ids.clear()
        self.build_graph()

    def build_graph(self, persistent=False):
        """Builds graph from current selection of items.

        Args:
            persistent (bool, optional): If True, elements in the current graph (if any) retain their position
                in the new one.
        """
        self._persisted_positions.clear()
        if persistent:
            for item in self.entity_items:
                x, y = self.convert_position(item.pos().x(), item.pos().y())
                self._persisted_positions[item.first_db_map, item.first_id] = {"x": x, "y": y}
        if not self.ui.dockWidget_entity_graph.isVisible():
            self._owes_graph = True
            return
        self._owes_graph = False
        self.ui.graphicsView.clear_scene()
        self._entity_fetch_parent.reset()
        self._parameter_value_fetch_parent.reset()
        self._graph_fetch_more_later()

    def _refresh_graph(self):
        self._update_graph_data()
        self.ui.graphicsView.clear_cross_hairs_items()  # Needed
        self._stop_layout_generators()
        self._layout_gen_id = monotonic()
        self.layout_gens[self._layout_gen_id] = layout_gen = self._make_layout_generator()
        self.ui.progress_bar_widget.set_layout_generator(layout_gen)
        self.ui.progress_bar_widget.show()
        layout_gen.layout_available.connect(self._complete_graph)
        layout_gen.finished.connect(lambda id_: self.layout_gens.pop(id_, None))  # Lambda to avoid issues in Python 3.7
        self._thread_pool.start(layout_gen)
        self._graph_fetch_more_later()

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
        self.ui.graphicsView.selected_items.clear()
        self.ui.graphicsView.hidden_items.clear()
        self.ui.graphicsView.clear_scene()
        if self._make_new_items(x, y):
            self._add_new_items()
        if not self._persisted_positions:
            self.ui.graphicsView.reset_zoom()
        else:
            self.ui.graphicsView.apply_zoom()

    def _update_selected_item_type_db_map_ids(self, selected_tree_inds):
        """Upsates the dict mapping item type to db_map to selected ids."""
        if "root" in selected_tree_inds:
            self._selected_item_type_db_map_ids = {"root": None}
            return
        self._selected_item_type_db_map_ids = {}
        for item_type, indexes in selected_tree_inds.items():
            for index in indexes:
                item = index.model().item_from_index(index)
                for db_map, id_ in item.db_map_ids.items():
                    self._selected_item_type_db_map_ids.setdefault(item_type, {}).setdefault(db_map, set()).add(id_)

    def _get_db_map_entities_for_graph(self):
        return [
            (db_map, x)
            for db_map in self.db_maps
            for x in self.db_mngr.get_items(db_map, "entity")
            if self._entity_fetch_parent.accepts_item(x, db_map)
        ]

    def _update_graph_data(self):
        """Updates data for graph according to selection in trees."""
        db_map_entities = self._get_db_map_entities_for_graph()
        pruned_db_map_entity_ids = self._all_pruned_db_map_entity_ids()
        max_ent_dim_count = self.ui.graphicsView.get_property("max_entity_dimension_count")
        db_map_entity_ids = set()
        db_map_element_id_lists = {}
        for db_map, entity in db_map_entities:
            if not entity["element_id_list"]:
                db_map_entity_ids.add((db_map, entity["id"]))
                continue
            db_map_element_id_list = [
                (db_map, id_) for id_ in entity["element_id_list"] if (db_map, id_) not in pruned_db_map_entity_ids
            ]
            el_count = len(db_map_element_id_list)
            if el_count != 0 and (el_count < 2 or el_count > max_ent_dim_count):
                continue
            db_map_entity_ids.add((db_map, entity["id"]))
            db_map_element_id_lists[db_map, entity["id"]] = db_map_element_id_list
        # Bind elements
        for db_map_element_id_list in db_map_element_id_lists.values():
            for db_map, entity_id in db_map_element_id_list:
                if (db_map, entity_id) not in db_map_entity_ids:
                    db_map_entity_ids.add((db_map, entity_id))
                    item = self.db_mngr.get_item(db_map, "entity", entity_id)
                    self._entity_fetch_parent.bind_item(item, db_map)
        db_map_entity_ids_by_key = {}
        for db_map_entity_id in db_map_entity_ids:
            key = self.get_entity_key(db_map_entity_id)
            db_map_entity_ids_by_key.setdefault(key, set()).add(db_map_entity_id)
        self.db_map_entity_id_sets = list(db_map_entity_ids_by_key.values())
        self._update_entity_element_inds(db_map_element_id_lists)
        self._update_property_pvs()
        self._entity_offsets = {}

    def get_entity_key(self, db_map_entity_id):
        db_map, entity_id = db_map_entity_id
        entity = self.db_mngr.get_item(db_map, "entity", entity_id)
        key = (entity["entity_class_name"], entity["dimension_name_list"], entity["entity_byname"])
        if not self.ui.graphicsView.get_property("merge_dbs"):
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

    def _get_pv(self, db_map, entity_id, pname):
        if not pname:
            return None
        entity = self.db_mngr.get_item(db_map, "entity", entity_id)
        if not entity:
            return None
        alternative = next(iter(self.db_mngr.get_items(db_map, "alternative")), None)
        if not alternative:
            return None
        pv = db_map.get_item(
            "parameter_value",
            parameter_definition_name=pname,
            entity_class_name=entity["entity_class_name"],
            entity_byname=entity["entity_byname"],
            alternative_name=alternative["name"],
        )
        if not pv:
            return None
        return from_database(pv["value"], pv["type"])

    def get_item_name(self, db_map, entity_id):
        if not self.ui.graphicsView.name_parameter:
            entity = self.db_mngr.get_item(db_map, "entity", entity_id)
            return entity["name"]
        return self._get_pv(db_map, entity_id, self.ui.graphicsView.name_parameter)

    def get_item_color(self, db_map, entity_id, time_line_index):
        return self._get_item_property(db_map, entity_id, self.ui.graphicsView.color_parameter, time_line_index)

    def get_arc_width(self, db_map, entity_id, time_line_index):
        return self._get_item_property(db_map, entity_id, self.ui.graphicsView.arc_width_parameter, time_line_index)

    def get_vertex_radius(self, db_map, entity_id, time_line_index):
        return self._get_item_property(db_map, entity_id, self.ui.graphicsView.vertex_radius_parameter, time_line_index)

    def _get_item_property(self, db_map, entity_id, pname, time_line_index):
        """Returns a tuple of (min_value, value, max_value) for given entity and property.
        Returns self.NOT_SPECIFIED if the property is not defined for the entity.
        Returns None if the property is not defined for *any* entity.

        Returns:
            tuple or None
        """
        pvs = self._pvs_by_pname.get(pname, {})
        if not pvs:
            return None
        pv = pvs.get((db_map, entity_id))
        if pv is None:
            return self.NOT_SPECIFIED
        val = _get_value(pv, time_line_index)
        if val is None:
            return self.NOT_SPECIFIED
        # NOTE: By construction, self._val_ranges_by_pname has the same keys as self._pvs_by_pname
        val_range = self._val_ranges_by_pname[pname]
        min_val, max_val = val_range
        return min_val, val, max_val

    def _get_fixed_pos(self, db_map, entity_id):
        pos_x, pos_y = [
            self._get_pv(db_map, entity_id, pname)
            for pname in (self.ui.graphicsView.pos_x_parameter, self.ui.graphicsView.pos_y_parameter)
        ]
        if isinstance(pos_x, float) and isinstance(pos_y, float):
            return {"x": pos_x, "y": pos_y}
        return self._persisted_positions.get((db_map, entity_id))

    def _make_layout_generator(self):
        """Returns a layout generator for the current graph.

        Returns:
            GraphLayoutGeneratorRunnable
        """
        heavy_positions = {
            ind: pos
            for ind, db_map_entity_ids in enumerate(self.db_map_entity_id_sets)
            for db_map_entity_id in db_map_entity_ids
            if (pos := self._get_fixed_pos(*db_map_entity_id))
        }
        spread_factor = self.ui.graphicsView.get_property("spread_factor") / 100
        build_iters = self.ui.graphicsView.get_property("build_iters")
        neg_weight_exp = self.ui.graphicsView.get_property("neg_weight_exp")
        return GraphLayoutGeneratorRunnable(
            self._layout_gen_id,
            len(self.db_map_entity_id_sets),
            self.entity_inds,
            self.element_inds,
            spread=spread_factor * self._ARC_LENGTH_HINT,
            heavy_positions=heavy_positions,
            weight_exp=-neg_weight_exp,
            max_iters=build_iters,
        )

    @staticmethod
    def convert_position(x, y):
        return (x, -y)

    def _get_entity_offset(self, db_map_entity_ids):
        db_map, entity_id = next(iter(db_map_entity_ids))
        entity = self.db_mngr.get_item(db_map, "entity", entity_id)
        element_id_list = entity.get("element_id_list")
        if not element_id_list:
            return None
        key = (db_map, tuple(sorted(element_id_list)))
        offsets = self._entity_offsets.setdefault(key, [])
        offset = _Offset(offsets)
        offsets.append(offset)
        return offset

    def _make_new_items(self, x, y):
        """Makes new items for the graph.

        Args:
            x (list)
            y (list)

        Returns:
            bool: True if graph contains any items after the operation, False otherwise
        """
        self.entity_items = [
            EntityItem(
                self,
                *self.convert_position(x[i], y[i]),
                self._VERTEX_EXTENT,
                tuple(db_map_entity_ids),
                offset=self._get_entity_offset(db_map_entity_ids),
            )
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
        remove_first(dimension_ids_to_go, ent_item.entity_class_ids(db_map))
        entity_class["dimension_ids_to_go"] = dimension_ids_to_go
        entity_class["db_map"] = db_map
        db_map_ids = ((db_map, None),)
        ch_item = CrossHairsItem(
            self, ent_item.pos().x(), ent_item.pos().y(), 0.8 * self._VERTEX_EXTENT, db_map_ids=db_map_ids
        )
        ch_ent_item = CrossHairsEntityItem(
            self, ent_item.pos().x(), ent_item.pos().y(), 0.5 * self._VERTEX_EXTENT, db_map_ids=db_map_ids
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
        for item_permutation in itertools.permutations(entity_items):
            dimension_id_lists = list(itertools.product(*[item.entity_class_ids(db_map) for item in item_permutation]))
            if tuple(entity_class["dimension_id_list"]) in dimension_id_lists:
                element_name_list = tuple(item.name for item in item_permutation)
                if not db_map.get_item(
                    "entity", entity_class_name=entity_class["name"], element_name_list=element_name_list
                ):
                    element_byname_list = tuple(item.byname for item in item_permutation)
                    entities.add(element_byname_list)
        if not entities:
            return
        dialog = AddReadyEntitiesDialog(self, entity_class, list(entities), self.db_mngr, db_map, commit_data=False)
        dialog.accepted.connect(lambda: self._do_finalize_connecting_entities(dialog, entity_items))
        dialog.show()

    def _do_finalize_connecting_entities(self, dialog, element_items):
        added_db_map_data = self._add_entities_from_dialog(dialog)
        new_db_map_id_sets = list(self._db_map_ids_by_key(added_db_map_data).values())
        for db_map_ids in new_db_map_id_sets:
            entity_item = EntityItem(
                self, 0, 0, self._VERTEX_EXTENT, tuple(db_map_ids), offset=self._get_entity_offset(db_map_ids)
            )
            self.scene.addItem(entity_item)
            entity_item.apply_zoom(self.ui.graphicsView.zoom_factor)
            for el_item in element_items:
                arc_item = ArcItem(entity_item, el_item, self._ARC_WIDTH)
                self.scene.addItem(arc_item)
                arc_item.apply_zoom(self.ui.graphicsView.zoom_factor)
        for el_item in element_items:
            for arc_item in el_item.arc_items:
                arc_item.ent_item.update_entity_pos()

    def add_entities_at_position(self, pos):
        parent_item = self.entity_tree_model.root_item
        dialog = AddEntitiesDialog(self, parent_item, self.db_mngr, *self.db_maps, commit_data=False)
        dialog.accepted.connect(lambda: self._do_add_entites_at_pos(dialog, pos.x(), pos.y()))
        dialog.show()

    def _do_add_entites_at_pos(self, dialog, x, y):
        added_db_map_data = self._add_entities_from_dialog(dialog)
        new_db_map_id_sets = list(self._db_map_ids_by_key(added_db_map_data).values())
        spread = self._VERTEX_EXTENT * self.ui.graphicsView.zoom_factor
        gen = GraphLayoutGenerator(len(new_db_map_id_sets), spread=spread)
        layout_x, layout_y = gen.compute_layout()
        for dx, dy, db_map_ids in zip(layout_x, layout_y, new_db_map_id_sets):
            entity_item = EntityItem(self, x + dx, y + dy, self._VERTEX_EXTENT, tuple(db_map_ids))
            self.scene.addItem(entity_item)
            entity_item.apply_zoom(self.ui.graphicsView.zoom_factor)

    def _add_entities_from_dialog(self, dialog):
        db_map_data = dialog.get_db_map_data()
        self._entity_fetch_parent.set_busy(True)
        self.db_mngr.add_entities(db_map_data)
        self._entity_fetch_parent.set_busy(False)
        added_db_map_data = {
            db_map: [db_map.get_item("entity", **item) for item in items] for db_map, items in db_map_data.items()
        }
        for db_map, items in added_db_map_data.items():
            for item in items:
                self._entity_fetch_parent.bind_item(item, db_map)
        return added_db_map_data

    def get_save_file_path(self, group, caption, filters):
        self.qsettings.beginGroup(self.settings_group)
        file_path, _ = get_save_file_name_in_last_dir(
            self.qsettings, group, self, caption, self._get_base_dir(), filters
        )
        self.qsettings.endGroup()
        return file_path

    def get_open_file_path(self, group, caption, filters):
        self.qsettings.beginGroup(self.settings_group)
        file_path, _ = get_open_file_name_in_last_dir(
            self.qsettings, group, self, caption, self._get_base_dir(), filters
        )
        self.qsettings.endGroup()
        return file_path

    def closeEvent(self, event):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event
        """
        super().closeEvent(event)
        if not event.isAccepted():
            return
        self.ui.treeView_entity.tree_selection_changed.disconnect(self._handle_entity_tree_selection_changed_in_graph)
        if self.scene is not None:
            self.scene.deleteLater()
        # Make sure the fetch parent isn't used to remove discarded changes after we've deleted the graph scene.
        self._entity_fetch_parent.set_obsolete(True)
        self._parameter_value_fetch_parent.set_obsolete(True)


class _Offset:
    def __init__(self, all_offsets):
        self._value = len(all_offsets)
        self._all_offsets = all_offsets

    def value(self):
        offsets = list(range(len(self._all_offsets)))  # [0, 1, 2, ...]
        center = sum(offsets) / len(offsets)
        return (self._value - center) / len(offsets)
