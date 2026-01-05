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
import networkx as nx
import pytest
from spinedb_api import DatabaseMapping
from spinetoolbox.relationship_graphs import RelationshipClassGraph, RelationshipGraph


class TestRelationshipClassGraph:
    def test_is_any_id_reachable_with_empty_target_ids(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            entity_class = db_map.add_entity_class(name="A")
        assert not graph.is_any_id_reachable(db_map, entity_class["id"], set())

    def test_is_any_id_reachable_in_both_directions(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            a_ = db_map.add_entity_class(dimension_name_list=["A"])
            a__ = db_map.add_entity_class(dimension_name_list=["A__"])
        assert graph.is_any_id_reachable(db_map, a_["id"], {a["id"]})
        assert graph.is_any_id_reachable(db_map, a__["id"], {a_["id"]})
        assert graph.is_any_id_reachable(db_map, a__["id"], {a["id"]})
        assert not graph.is_any_id_reachable(db_map, a["id"], {a_["id"]})
        assert not graph.is_any_id_reachable(db_map, a["id"], {a__["id"]})
        assert not graph.is_any_id_reachable(db_map, a_["id"], {a__["id"]})

    def test_is_any_id_reachable_from_unrelated_class(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            db_map.add_entity_class(name="B")
            b_ = db_map.add_entity_class(dimension_name_list=["B"])
        assert not graph.is_any_id_reachable(db_map, a["id"], {b_["id"]})

    def test_removed_class_is_ignored(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            a_ = db_map.add_entity_class(dimension_name_list=["A"])
            a_.remove()
        assert not graph.is_any_id_reachable(db_map, a["id"], {a_["id"]})

    def test_superclass_subclasses_are_taken_into_account(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            b = db_map.add_entity_class(name="B")
            db_map.add_entity_class(name="Any")
            db_map.add_superclass_subclass(superclass_name="Any", subclass_name="A")
            db_map.add_superclass_subclass(superclass_name="Any", subclass_name="B")
            any_any = db_map.add_entity_class(dimension_name_list=["Any", "Any"])
        assert graph.is_any_id_reachable(db_map, any_any["id"], {a["id"]})
        assert graph.is_any_id_reachable(db_map, any_any["id"], {b["id"]})

    def test_removed_superclass_subclasses_are_ignored(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            b = db_map.add_entity_class(name="B")
            db_map.add_entity_class(name="Any")
            db_map.add_superclass_subclass(superclass_name="Any", subclass_name="A")
            super_sub = db_map.add_superclass_subclass(superclass_name="Any", subclass_name="B")
            super_sub.remove()
            any_any = db_map.add_entity_class(dimension_name_list=["Any", "Any"])
        assert graph.is_any_id_reachable(db_map, any_any["id"], {a["id"]})
        assert not graph.is_any_id_reachable(db_map, any_any["id"], {b["id"]})

    def test_invalidate_caches(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            db_map.add_entity_class(name="B")
            a_b = db_map.add_entity_class(dimension_name_list=["A", "B"])
        assert graph.is_any_id_reachable(db_map, a_b["id"], {a["id"]})
        b_a = db_map.add_entity_class(dimension_name_list=["B", "A"])
        other_db_map = DatabaseMapping("sqlite:///", create=True)
        graph.invalidate_caches(other_db_map)
        with pytest.raises(nx.exception.NetworkXError):
            graph.is_any_id_reachable(db_map, b_a["id"], {a["id"]})
        graph.invalidate_caches(db_map)
        assert graph.is_any_id_reachable(db_map, b_a["id"], {a["id"]})

    def test_maybe_invalidate_caches_after_data_changed(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            db_map.add_entity_class(name="B")
            a_b = db_map.add_entity_class(dimension_name_list=["A", "B"])
        assert graph.is_any_id_reachable(db_map, a_b["id"], {a["id"]})
        b_a = db_map.add_entity_class(dimension_name_list=["B", "A"])
        graph.maybe_invalidate_caches_after_data_changed("alternative", {db_map: [db_map.alternative(name="Base")]})
        with pytest.raises(nx.exception.NetworkXError):
            graph.is_any_id_reachable(db_map, b_a["id"], {a["id"]})
        other_db_map = DatabaseMapping("sqlite:///", create=True)
        graph.maybe_invalidate_caches_after_data_changed("entity_class", {other_db_map: []})
        with pytest.raises(nx.exception.NetworkXError):
            graph.is_any_id_reachable(db_map, b_a["id"], {a["id"]})
        graph.maybe_invalidate_caches_after_data_changed("entity_class", {db_map: [b_a]})
        assert graph.is_any_id_reachable(db_map, b_a["id"], {a["id"]})

    def test_maybe_invalidate_caches_after_data_changed_superclass_subclass(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            db_map.add_entity_class(name="Any")
            super_sub = db_map.add_superclass_subclass(superclass_name="Any", subclass_name="A")
            any_any = db_map.add_entity_class(dimension_name_list=["Any", "Any"])
        assert graph.is_any_id_reachable(db_map, any_any["id"], {a["id"]})
        super_sub.remove()
        graph.maybe_invalidate_caches_after_data_changed("superclass_subclass", {db_map: [super_sub]})
        assert not graph.is_any_id_reachable(db_map, any_any["id"], {a["id"]})

    def test_maybe_invalidate_caches_after_fetch(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            db_map.add_entity_class(name="B")
            a_b = db_map.add_entity_class(dimension_name_list=["A", "B"])
        assert graph.is_any_id_reachable(db_map, a_b["id"], {a["id"]})
        b_a = db_map.add_entity_class(dimension_name_list=["B", "A"])
        graph.maybe_invalidate_caches_after_fetch("alternative", db_map)
        with pytest.raises(nx.exception.NetworkXError):
            graph.is_any_id_reachable(db_map, b_a["id"], {a["id"]})
        other_db_map = DatabaseMapping("sqlite:///", create=True)
        graph.maybe_invalidate_caches_after_fetch("entity_class", other_db_map)
        with pytest.raises(nx.exception.NetworkXError):
            graph.is_any_id_reachable(db_map, b_a["id"], {a["id"]})
        graph.maybe_invalidate_caches_after_fetch("entity_class", db_map)
        assert graph.is_any_id_reachable(db_map, b_a["id"], {a["id"]})

    def test_maybe_invalidate_caches_after_fetch_superclass_subclass(self, db_map, parent_object):
        graph = RelationshipClassGraph(parent_object)
        with db_map:
            a = db_map.add_entity_class(name="A")
            db_map.add_entity_class(name="Any")
            super_sub = db_map.add_superclass_subclass(superclass_name="Any", subclass_name="A")
            any_any = db_map.add_entity_class(dimension_name_list=["Any", "Any"])
        assert graph.is_any_id_reachable(db_map, any_any["id"], {a["id"]})
        super_sub.remove()
        graph.maybe_invalidate_caches_after_fetch("superclass_subclass", db_map)
        assert not graph.is_any_id_reachable(db_map, any_any["id"], {a["id"]})


class TestRelationshipGraph:
    def test_is_any_element_in_both_directions_with_superclass(self, db_map, parent_object):
        graph = RelationshipGraph(parent_object)
        with db_map:
            db_map.add_entity_class(name="A")
            db_map.add_entity_class(dimension_name_list=["A"])
            db_map.add_entity_class(name="Element")
            db_map.add_superclass_subclass(superclass_name="Element", subclass_name="A__")
            db_map.add_entity_class(dimension_name_list=["Element"])
            item_a = db_map.add_entity(entity_class_name="A", name="a")
            item_a_ = db_map.add_entity(entity_class_name="A__", entity_byname=("a",))
            relationship_item = db_map.add_entity(entity_class_name="Element__", entity_byname=("a",))
        assert graph.is_any_id_reachable(db_map, item_a_["id"], {item_a["id"]})
        assert graph.is_any_id_reachable(db_map, relationship_item["id"], {item_a["id"]})
        assert graph.is_any_id_reachable(db_map, relationship_item["id"], {item_a_["id"]})
        assert not graph.is_any_id_reachable(db_map, item_a["id"], {item_a_["id"]})
        assert not graph.is_any_id_reachable(db_map, item_a["id"], {relationship_item["id"]})
        assert not graph.is_any_id_reachable(db_map, item_a_["id"], {relationship_item["id"]})
