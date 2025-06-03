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

"""Unit tests for ``spine_db_fetcher`` module."""
import unittest
from unittest.mock import MagicMock
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from spinedb_api import DatabaseMapping, to_database
from spinedb_api.import_functions import import_data
from spinetoolbox.fetch_parent import ItemTypeFetchParent
from tests.mock_helpers import TestCaseWithQApplication, MockSpineDBManager, q_object


class ExampleItemTypeFetchParent(ItemTypeFetchParent):
    def __init__(self, item_type, parent):
        super().__init__(item_type, owner=parent)
        self.handle_items_added = MagicMock()


class TestSpineDBFetcher(TestCaseWithQApplication):
    def setUp(self):
        app_settings = MagicMock()
        self._logger = MagicMock()  # Collects error messages therefore handy for debugging.
        self._db_mngr = MockSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", self._logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, "db_fetcher_test_db")

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()

    def test_fetch_empty_database(self):
        with q_object(QObject()) as parent:
            for item_type in DatabaseMapping.item_types():
                fetcher = ExampleItemTypeFetchParent(item_type, parent)
                while self._db_mngr.can_fetch_more(self._db_map, fetcher):
                    self._db_mngr.fetch_more(self._db_map, fetcher)
                    qApp.processEvents()  # pylint: disable=undefined-variable
                if item_type in ("alternative", "commit"):
                    fetcher.handle_items_added.assert_called_once()
                else:
                    fetcher.handle_items_added.assert_not_called()
                fetcher.set_obsolete(True)

    def _import_data(self, **data):
        import_data(self._db_map, **data)
        self._db_map.commit_session("ddd")

    def test_fetch_alternatives(self):
        self._import_data(alternatives=("alt",))
        with q_object(QObject()) as parent:
            fetcher = ExampleItemTypeFetchParent("alternative", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call(
                {
                    self._db_map: [
                        {
                            "id": self._db_map.get_alternative_item(id=1)["id"],
                            "name": "Base",
                            "description": "Base alternative",
                            "commit_id": 1,
                        }
                    ]
                }
            )
            fetcher.handle_items_added.assert_any_call(
                {
                    self._db_map: [
                        {
                            "id": self._db_map.get_alternative_item(id=2)["id"],
                            "name": "alt",
                            "description": None,
                            "commit_id": 2,
                        }
                    ]
                }
            )
            alternative_id = self._db_map.alternative(name="alt")["id"]
            self.assertEqual(
                self._db_mngr.get_item(self._db_map, "alternative", alternative_id),
                {
                    "commit_id": 2,
                    "description": None,
                    "id": self._db_map.get_alternative_item(id=2)["id"],
                    "name": "alt",
                },
            )
            fetcher.set_obsolete(True)

    def test_fetch_scenarios(self):
        self._import_data(scenarios=("scenario",))
        scenario_id = self._db_map.scenario(name="scenario")["id"]
        item = {
            "id": scenario_id,
            "name": "scenario",
            "description": None,
            "active": False,
            "commit_id": 2,
        }
        with q_object(QObject()) as parent:
            fetcher = ExampleItemTypeFetchParent("scenario", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "scenario", scenario_id), item)
            fetcher.set_obsolete(True)

    def test_fetch_scenario_alternatives(self):
        self._import_data(alternatives=("alt",), scenarios=("scenario",), scenario_alternatives=(("scenario", "alt"),))
        scenario_alternative_id = self._db_map.scenario_alternative(scenario_name="scenario", alternative_name="alt")[
            "id"
        ]
        item = {
            "id": scenario_alternative_id,
            "scenario_id": self._db_map.scenario(name="scenario")["id"],
            "alternative_id": self._db_map.alternative(name="alt")["id"],
            "rank": 1,
            "commit_id": 2,
        }
        with q_object(QObject()) as parent:
            for item_type in ("scenario", "alternative"):
                dep_fetcher = ExampleItemTypeFetchParent(item_type, parent)
                self._db_mngr.fetch_more(self._db_map, dep_fetcher)
                dep_fetcher.set_obsolete(True)
                dep_fetcher.deleteLater()
            fetcher = ExampleItemTypeFetchParent("scenario_alternative", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertEqual(
                self._db_mngr.get_item(self._db_map, "scenario_alternative", scenario_alternative_id), item
            )
            fetcher.set_obsolete(True)

    def test_fetch_object_classes(self):
        self._import_data(entity_classes=(("oc",),))
        entity_class_id = self._db_map.entity_class(name="oc")["id"]
        item = {
            "id": entity_class_id,
            "name": "oc",
            "description": None,
            "display_order": 99,
            "display_icon": None,
            "hidden": 0,
            "active_by_default": True,
            "dimension_id_list": (),
        }
        with q_object(QObject()) as parent:
            fetcher = ExampleItemTypeFetchParent("entity_class", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertIsInstance(self._db_mngr.entity_class_icon(self._db_map, entity_class_id), QIcon)
            self.assertEqual(self._db_mngr.get_item(self._db_map, "entity_class", entity_class_id), item)
            fetcher.set_obsolete(True)

    def test_fetch_objects(self):
        self._import_data(entity_classes=(("oc",),), entities=(("oc", "obj"),))
        entity_id = self._db_map.entity(entity_class_name="oc", name="obj")["id"]
        item = {
            "id": entity_id,
            "class_id": self._db_map.entity_class(name="oc")["id"],
            "name": "obj",
            "element_id_list": (),
            "description": None,
            "commit_id": 2,
        }
        with q_object(QObject()) as parent:
            self._db_mngr.fetch_more(self._db_map, ExampleItemTypeFetchParent("entity_class", parent))
            for item_type in ("entity",):
                dep_fetcher = ExampleItemTypeFetchParent(item_type, parent)
                self._db_mngr.fetch_more(self._db_map, dep_fetcher)
                dep_fetcher.set_obsolete(True)
            fetcher = ExampleItemTypeFetchParent("entity", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "entity", entity_id), item)
            fetcher.set_obsolete(True)

    def test_fetch_relationship_classes(self):
        self._import_data(
            entity_classes=(
                "oc",
                ("rc", ("oc",)),
            )
        )
        entity_class_id = self._db_map.get_entity_class_item(name="rc")["id"]
        item = {
            "id": entity_class_id,
            "name": "rc",
            "description": None,
            "display_order": 99,
            "display_icon": None,
            "hidden": 0,
            "active_by_default": True,
            "dimension_id_list": (self._db_map.entity_class(name="oc")["id"],),
        }
        with q_object(QObject()) as parent:
            for item_type in ("entity_class",):
                dep_fetcher = ExampleItemTypeFetchParent(item_type, parent)
                self._db_mngr.fetch_more(self._db_map, dep_fetcher)
                dep_fetcher.set_obsolete(True)
            fetcher = ExampleItemTypeFetchParent("entity_class", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "entity_class", entity_class_id), item)
            fetcher.set_obsolete(True)

    def test_fetch_relationships(self):
        self._import_data(entity_classes=(("oc",), ("rc", ("oc",))), entities=(("oc", "obj"), ("rc", ("obj",))))
        relationship_id = self._db_map.entity(entity_class_name="rc", entity_byname=("obj",))["id"]
        item = {
            "id": relationship_id,
            "name": "obj__",
            "class_id": self._db_map.entity_class(name="rc")["id"],
            "element_id_list": (self._db_map.entity(entity_class_name="oc", name="obj")["id"],),
            "description": None,
            "commit_id": 2,
        }
        with q_object(QObject()) as parent:
            for item_type in ("entity_class", "entity"):
                dep_fetcher = ExampleItemTypeFetchParent(item_type, parent)
                self._db_mngr.fetch_more(self._db_map, dep_fetcher)
                dep_fetcher.set_obsolete(True)
            fetcher = ExampleItemTypeFetchParent("entity", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "entity", relationship_id), item)
            fetcher.set_obsolete(True)

    def test_fetch_object_groups(self):
        self._import_data(
            entity_classes=("oc",), entities=(("oc", "obj"), ("oc", "group")), entity_groups=(("oc", "group", "obj"),)
        )
        group_id = self._db_map.entity_group(entity_class_name="oc", group_name="group", member_name="obj")["id"]
        item = {
            "id": group_id,
            "entity_class_id": self._db_map.entity_class(name="oc")["id"],
            "entity_id": self._db_map.entity(entity_class_name="oc", name="group")["id"],
            "member_id": self._db_map.entity(entity_class_name="oc", name="obj")["id"],
        }
        with q_object(QObject()) as parent:
            fetcher = ExampleItemTypeFetchParent("entity_group", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "entity_group", group_id), item)
            fetcher.set_obsolete(True)

    def test_fetch_parameter_definitions(self):
        self._import_data(entity_classes=("oc",), parameter_definitions=(("oc", "param"),))
        definition_id = self._db_map.parameter_definition(entity_class_name="oc", name="param")["id"]
        item = {
            "id": definition_id,
            "entity_class_id": self._db_map.entity_class(name="oc")["id"],
            "name": "param",
            "parameter_value_list_id": None,
            "default_value": None,
            "default_type": None,
            "description": None,
            "commit_id": 2,
            "list_value_id": None,
        }
        with q_object(QObject()) as parent:
            for item_type in ("entity_class",):
                dep_fetcher = ExampleItemTypeFetchParent(item_type, parent)
                self._db_mngr.fetch_more(self._db_map, dep_fetcher)
                dep_fetcher.set_obsolete(True)
            fetcher = ExampleItemTypeFetchParent("parameter_definition", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_called_once_with({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "parameter_definition", definition_id), item)
            fetcher.set_obsolete(True)

    def test_fetch_parameter_values(self):
        self._import_data(
            entity_classes=("oc",),
            entities=(("oc", "obj"),),
            parameter_definitions=(("oc", "param"),),
            parameter_values=(("oc", "obj", "param", 2.3),),
        )
        value_id = self._db_map.parameter_value(
            entity_class_name="oc", entity_byname=("obj",), parameter_definition_name="param", alternative_name="Base"
        )["id"]
        value, value_type = to_database(2.3)
        item = {
            "id": value_id,
            "entity_class_id": self._db_map.entity_class(name="oc")["id"],
            "entity_id": self._db_map.entity(entity_class_name="oc", name="obj")["id"],
            "parameter_definition_id": self._db_map.parameter_definition(entity_class_name="oc", name="param")["id"],
            "alternative_id": self._db_map.alternative(name="Base")["id"],
            "value": value,
            "type": value_type,
            "commit_id": 2,
            "list_value_id": None,
        }
        with q_object(QObject()) as parent:
            for item_type in ("entity_class", "entity", "parameter_definition", "alternative"):
                dep_fetcher = ExampleItemTypeFetchParent(item_type, parent)
                self._db_mngr.fetch_more(self._db_map, dep_fetcher)
                dep_fetcher.set_obsolete(True)
            fetcher = ExampleItemTypeFetchParent("parameter_value", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_called_once_with({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "parameter_value", value_id), item)
            fetcher.set_obsolete(True)

    def test_fetch_parameter_value_lists(self):
        self._import_data(parameter_value_lists=(("value_list", 2.3),))
        value_list_id = self._db_map.parameter_value_list(name="value_list")["id"]
        item = {"id": value_list_id, "name": "value_list", "commit_id": 2}
        with q_object(QObject()) as parent:
            fetcher = ExampleItemTypeFetchParent("parameter_value_list", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "parameter_value_list", value_list_id), item)
            list_value_id = self._db_map.list_value(parameter_value_list_name="value_list", index=0)["id"]
            value, value_type = to_database(2.3)
            item = {
                "id": list_value_id,
                "parameter_value_list_id": value_list_id,
                "index": 0,
                "value": value,
                "type": value_type,
                "commit_id": 2,
            }
            fetcher = ExampleItemTypeFetchParent("list_value", parent)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
            fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
            self.assertEqual(self._db_mngr.get_item(self._db_map, "list_value", list_value_id), item)
            fetcher.set_obsolete(True)


if __name__ == "__main__":
    unittest.main()
