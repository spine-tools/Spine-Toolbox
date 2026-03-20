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
import math
from typing import ClassVar
import networkx as nx
from PySide6.QtCore import Slot
from spinedb_api import DatabaseMapping
from spinedb_api.helpers import ItemType
from spinedb_api.temp_id import TempId
from .fetch_parent import DBMapMixedItems


class GraphBase:
    INVALIDATING_ITEM_TYPES: ClassVar[set[str]] = NotImplemented

    def __init__(self):
        self._graphs: dict[DatabaseMapping, nx.DiGraph] = {}

    @Slot(object)
    def invalidate_caches(self, db_map: DatabaseMapping) -> None:
        if db_map in self._graphs:
            del self._graphs[db_map]

    @Slot(str, object)
    def maybe_invalidate_caches_after_data_changed(self, item_type: ItemType, db_map_data: DBMapMixedItems) -> None:
        if item_type not in self.INVALIDATING_ITEM_TYPES:
            return
        for db_map in db_map_data:
            if db_map in self._graphs:
                del self._graphs[db_map]

    @Slot(str, object)
    def maybe_invalidate_caches_after_fetch(self, item_type: ItemType, db_map: DatabaseMapping) -> None:
        if (item_type not in self.INVALIDATING_ITEM_TYPES) or db_map not in self._graphs:
            return
        del self._graphs[db_map]


class SuperclassGraphBase(GraphBase):
    INVALIDATING_ITEM_TYPES: ClassVar[set[str]] = {"entity_class", "superclass_subclass"}

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


class RelationshipClassGraph(SuperclassGraphBase):
    @staticmethod
    def _build_graph(db_map: DatabaseMapping) -> nx.DiGraph:
        graph = _build_graph(db_map, "entity_class", "dimension_id_list")
        for superclass_subclass in db_map.mapped_table("superclass_subclass").values():
            if not superclass_subclass.is_valid():
                continue
            graph.add_edge(superclass_subclass["subclass_id"], superclass_subclass["superclass_id"])
        return graph


class RelationshipGraph(SuperclassGraphBase):
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


class EntityScenarioActivityGraph(GraphBase):
    INVALIDATING_ITEM_TYPES: ClassVar[set[str]] = {"scenario_alternative", "entity_alternative"}

    def is_entity_active(self, db_map: DatabaseMapping, entity_id: TempId, scenario_id: TempId) -> bool | None:
        if db_map not in self._graphs:
            self._graphs[db_map] = self._build_graph(db_map)
        graph = self._graphs[db_map]
        if scenario_id not in graph:
            return None
        activity = None
        max_rank = -math.inf
        for alternative_id in graph.successors(scenario_id):
            if not (alternative_id, entity_id) in graph.edges:
                continue
            rank = graph.edges[scenario_id, alternative_id]["rank"]
            if rank < max_rank:
                continue
            activity = graph.edges[alternative_id, entity_id]["active"]
            max_rank = rank
        if activity is None:
            class_table = db_map.mapped_table("entity_class")
            entity_table = db_map.mapped_table("entity")
            entity = entity_table[entity_id]
            for element_id in entity["element_id_list"]:
                element_activity = self.is_entity_active(db_map, element_id, scenario_id)
                if element_activity is False:
                    return False
                elif element_activity is None:
                    entity_class = class_table[entity_table[element_id]["class_id"]]
                    if not entity_class["active_by_default"]:
                        return False
        return activity

    @staticmethod
    def _build_graph(db_map: DatabaseMapping) -> nx.DiGraph:
        graph = nx.DiGraph()
        db_map.fetch_all("scenario_alternative")
        for scenario_alternative in db_map.mapped_table("scenario_alternative").values():
            if not scenario_alternative.is_valid():
                continue
            scenario_id = scenario_alternative["scenario_id"]
            graph.add_node(scenario_id)
            alternative_id = scenario_alternative["alternative_id"]
            graph.add_node(alternative_id)
            graph.add_edge(scenario_id, alternative_id, rank=scenario_alternative["rank"])
        for entity_alternative in db_map.mapped_table("entity_alternative").values():
            if not entity_alternative.is_valid():
                continue
            alternative_id = entity_alternative["alternative_id"]
            if alternative_id in graph:
                entity_id = entity_alternative["entity_id"]
                graph.add_node(entity_id)
                graph.add_edge(alternative_id, entity_id, active=entity_alternative["active"])
        return graph
