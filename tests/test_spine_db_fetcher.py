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
Unit tests for ``spine_db_fetcher`` module.
"""
import unittest
from unittest.mock import MagicMock
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from spinetoolbox.fetch_parent import ItemTypeFetchParent
from spinedb_api import DatabaseMapping
from spinedb_api.temp_id import TempId
from spinedb_api.import_functions import import_data
from tests.mock_helpers import TestSpineDBManager


class TestItemTypeFetchParent(ItemTypeFetchParent):
    def __init__(self, item_type):
        super().__init__(item_type)
        self.handle_items_added = MagicMock()


class TestSpineDBFetcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        self._logger = MagicMock()  # Collects error messages therefore handy for debugging.
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", self._logger, codename="db_fetcher_test_db", create=True)
        self._temp_id_reset = False

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()

    def test_fetch_empty_database(self):
        for item_type in DatabaseMapping.item_types():
            fetcher = TestItemTypeFetchParent(item_type)
            if self._db_mngr.can_fetch_more(self._db_map, fetcher):
                self._db_mngr.fetch_more(self._db_map, fetcher)
                qApp.processEvents()
            if item_type in ("alternative", "commit"):
                fetcher.handle_items_added.assert_called_once()
            else:
                fetcher.handle_items_added.assert_not_called()
            fetcher.set_obsolete(True)

    def _import_data(self, **data):
        if self._temp_id_reset:
            raise RuntimeError("_import_data can be called only once per test since it resets TempId counters")
        self._temp_id_reset = True
        TempId._next_id = {}
        import_data(self._db_map, **data)
        self._db_map.commit_session("ddd")

    def test_fetch_alternatives(self):
        self._import_data(alternatives=("alt",))
        fetcher = TestItemTypeFetchParent("alternative")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call(
            {self._db_map: [{'id': 1, 'name': 'Base', 'description': 'Base alternative', 'commit_id': 1}]}
        )
        fetcher.handle_items_added.assert_any_call(
            {self._db_map: [{'id': 2, 'name': 'alt', 'description': None, 'commit_id': 2}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "alternative", 2),
            {'commit_id': 2, 'description': None, 'id': 2, 'name': 'alt'},
        )
        fetcher.set_obsolete(True)

    def test_fetch_scenarios(self):
        self._import_data(scenarios=("scenario",))
        item = {'id': 1, 'name': 'scenario', 'description': None, 'active': False, 'commit_id': 2}
        fetcher = TestItemTypeFetchParent("scenario")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "scenario", 1), item)
        fetcher.set_obsolete(True)

    def test_fetch_scenario_alternatives(self):
        self._import_data(alternatives=("alt",), scenarios=("scenario",), scenario_alternatives=(("scenario", "alt"),))
        item = {'id': 1, 'scenario_id': 1, 'alternative_id': 2, 'rank': 1, 'commit_id': 2}
        for item_type in ("scenario", "alternative"):
            dep_fetcher = TestItemTypeFetchParent(item_type)
            self._db_mngr.fetch_more(self._db_map, dep_fetcher)
            dep_fetcher.set_obsolete(True)
        fetcher = TestItemTypeFetchParent("scenario_alternative")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "scenario_alternative", 1), item)
        fetcher.set_obsolete(True)

    def test_fetch_object_classes(self):
        self._import_data(entity_classes=(("oc",),))
        item = {
            'id': 1,
            'name': 'oc',
            'description': None,
            'display_order': 99,
            'display_icon': None,
            'hidden': 0,
            'dimension_id_list': (),
        }
        fetcher = TestItemTypeFetchParent("entity_class")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertIsInstance(self._db_mngr.entity_class_icon(self._db_map, 1), QIcon)
        self.assertEqual(self._db_mngr.get_item(self._db_map, "entity_class", 1), item)
        fetcher.set_obsolete(True)

    def test_fetch_objects(self):
        self._import_data(entity_classes=(("oc",),), entities=(("oc", "obj"),))
        item = {
            'id': 1,
            'class_id': 1,
            'name': 'obj',
            'element_id_list': (),
            'description': None,
            'commit_id': 2,
        }
        self._db_mngr.fetch_more(self._db_map, TestItemTypeFetchParent("entity_class"))
        for item_type in ("entity",):
            dep_fetcher = TestItemTypeFetchParent(item_type)
            self._db_mngr.fetch_more(self._db_map, dep_fetcher)
            dep_fetcher.set_obsolete(True)
        fetcher = TestItemTypeFetchParent("entity")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "entity", 1), item)
        fetcher.set_obsolete(True)

    def test_fetch_relationship_classes(self):
        self._import_data(object_classes=("oc",), relationship_classes=(("rc", ("oc",)),))
        item = {
            'id': 2,
            'name': 'rc',
            'description': None,
            'display_order': 99,
            'display_icon': None,
            'hidden': 0,
            'dimension_id_list': (1,),
        }
        for item_type in ("entity_class",):
            dep_fetcher = TestItemTypeFetchParent(item_type)
            self._db_mngr.fetch_more(self._db_map, dep_fetcher)
            dep_fetcher.set_obsolete(True)
        fetcher = TestItemTypeFetchParent("entity_class")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "entity_class", 2), item)
        fetcher.set_obsolete(True)

    def test_fetch_relationships(self):
        self._import_data(entity_classes=(("oc",), ("rc", ("oc",))), entities=(("oc", "obj"), ("rc", None, ("obj",))))
        item = {
            'id': -2,
            'name': 'obj',
            'class_id': -2,
            'element_id_list': (-1,),
            'description': None,
            'commit_id': 2,
        }
        for item_type in ("entity_class", "entity"):
            dep_fetcher = TestItemTypeFetchParent(item_type)
            self._db_mngr.fetch_more(self._db_map, dep_fetcher)
            dep_fetcher.set_obsolete(True)
        fetcher = TestItemTypeFetchParent("entity")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "entity", 2), item)
        fetcher.set_obsolete(True)

    def test_fetch_object_groups(self):
        self._import_data(
            object_classes=("oc",), objects=(("oc", "obj"), ("oc", "group")), object_groups=(("oc", "group", "obj"),)
        )
        item = {'id': 1, 'entity_class_id': 1, 'entity_id': 2, 'member_id': 1, 'commit_id': 2}
        fetcher = TestItemTypeFetchParent("entity_group")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "entity_group", 1), item)
        fetcher.set_obsolete(True)

    def test_fetch_parameter_definitions(self):
        self._import_data(object_classes=("oc",), object_parameters=(("oc", "param"),))
        item = {
            'id': -1,
            'entity_class_id': -1,
            'name': 'param',
            'parameter_value_list_id': None,
            'default_value': None,
            'default_type': None,
            'description': None,
            'commit_id': 2,
            "list_value_id": None,
        }
        for item_type in ("entity_class",):
            dep_fetcher = TestItemTypeFetchParent(item_type)
            self._db_mngr.fetch_more(self._db_map, dep_fetcher)
            dep_fetcher.set_obsolete(True)
        fetcher = TestItemTypeFetchParent("parameter_definition")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_called_once_with({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "parameter_definition", 1), item)
        fetcher.set_obsolete(True)

    def test_fetch_parameter_values(self):
        self._import_data(
            object_classes=("oc",),
            objects=(("oc", "obj"),),
            object_parameters=(("oc", "param"),),
            object_parameter_values=(("oc", "obj", "param", 2.3),),
        )
        item = {
            'id': -1,
            'entity_class_id': -1,
            'entity_id': -1,
            'parameter_definition_id': -1,
            'alternative_id': 1,
            'value': b'2.3',
            'type': None,
            'commit_id': 2,
            "list_value_id": None,
        }
        for item_type in ("entity_class", "entity", "parameter_definition", "alternative"):
            dep_fetcher = TestItemTypeFetchParent(item_type)
            self._db_mngr.fetch_more(self._db_map, dep_fetcher)
            dep_fetcher.set_obsolete(True)
        fetcher = TestItemTypeFetchParent("parameter_value")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_called_once_with({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "parameter_value", 1), item)
        fetcher.set_obsolete(True)

    def test_fetch_parameter_value_lists(self):
        self._import_data(parameter_value_lists=(("value_list", (2.3,)),))
        item = {'id': 1, 'name': 'value_list', 'commit_id': 2}
        fetcher = TestItemTypeFetchParent("parameter_value_list")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "parameter_value_list", 1), item)
        item = {'id': 1, 'parameter_value_list_id': 1, 'index': 0, 'value': b'[2.3]', 'type': None, 'commit_id': 2}
        fetcher = TestItemTypeFetchParent("list_value")
        if self._db_mngr.can_fetch_more(self._db_map, fetcher):
            self._db_mngr.fetch_more(self._db_map, fetcher)
        fetcher.handle_items_added.assert_any_call({self._db_map: [item]})
        self.assertEqual(self._db_mngr.get_item(self._db_map, "list_value", 1), item)
        fetcher.set_obsolete(True)


if __name__ == "__main__":
    unittest.main()
