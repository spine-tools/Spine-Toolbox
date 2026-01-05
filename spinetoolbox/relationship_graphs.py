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
from __future__ import annotations
import networkx as nx
from PySide6.QtCore import QObject, Slot
from spinedb_api import DatabaseMapping
from spinedb_api.helpers import ItemType
from spinedb_api.temp_id import TempId
from .fetch_parent import DBMapMixedItems


class GraphBase(QObject):
    def __init__(self, parent: QObject | None):
        super().__init__(parent)
        self._graphs: dict[DatabaseMapping, nx.DiGraph] = {}

    def is_any_id_reachable(self, db_map: DatabaseMapping, source_id: TempId, target_ids: set[TempId]) -> bool:
        if db_map not in self._graphs:
            self._graphs[db_map] = self._build_graph(db_map)
        graph = self._graphs[db_map]
        relationship_ids = list(graph.predecessors(source_id))
        while relationship_ids:
            relationship_id = relationship_ids.pop(-1)
            if relationship_id in target_ids:
                return True
            relationship_ids += graph.predecessors(relationship_id)
        return False

    @staticmethod
    def _build_graph(db_map: DatabaseMapping) -> nx.DiGraph:
        raise NotImplementedError()

    @Slot(object)
    def invalidate_caches(self, db_map: DatabaseMapping) -> None:
        if db_map in self._graphs:
            del self._graphs[db_map]

    @Slot(str, object)
    def maybe_invalidate_caches_after_data_changed(self, item_type: ItemType, db_map_data: DBMapMixedItems) -> None:
        if item_type != "entity_class" and item_type != "superclass_subclass":
            return
        for db_map in db_map_data:
            if db_map in self._graphs:
                del self._graphs[db_map]

    @Slot(str, object)
    def maybe_invalidate_caches_after_fetch(self, item_type: ItemType, db_map: DatabaseMapping) -> None:
        if (item_type != "entity_class" and item_type != "superclass_subclass") or db_map not in self._graphs:
            return
        del self._graphs[db_map]


class RelationshipClassGraph(GraphBase):
    @staticmethod
    def _build_graph(db_map: DatabaseMapping) -> nx.DiGraph:
        graph = _build_graph(db_map, "entity_class", "dimension_id_list")
        for superclass_subclass in db_map.mapped_table("superclass_subclass").values():
            if not superclass_subclass.is_valid():
                continue
            graph.add_edge(superclass_subclass["subclass_id"], superclass_subclass["superclass_id"])
        return graph


class RelationshipGraph(GraphBase):
    @staticmethod
    def _build_graph(db_map: DatabaseMapping) -> nx.DiGraph:
        return _build_graph(db_map, "entity", "element_id_list")


def _build_graph(db_map: DatabaseMapping, item_type: ItemType, id_list_name: str) -> nx.DiGraph:
    graph = nx.DiGraph()
    for item in db_map.mapped_table(item_type).values():
        if not item.is_valid():
            continue
        item_id = item["id"]
        if not graph.has_node(item_id):
            graph.add_node(item_id)
        for dimension_id in item[id_list_name]:
            if not graph.has_node(dimension_id):
                graph.add_node(dimension_id)
            graph.add_edge(dimension_id, item_id)
    return graph
