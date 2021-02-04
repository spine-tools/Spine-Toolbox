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
Unit tests for ``spine_db_fetcher`` module.

:authors: A. Soininen (VTT)
:date:    4.2.2021
"""
import unittest
from unittest.mock import MagicMock
from PySide2.QtCore import QObject, Slot
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication
from spinedb_api import (
    import_alternatives,
    import_features,
    import_object_classes,
    import_objects,
    import_object_parameter_values,
    import_object_parameters,
    import_parameter_value_lists,
    import_relationship_classes,
    import_relationships,
    import_scenario_alternatives,
    import_scenarios,
    import_tool_feature_methods,
    import_tool_features,
    import_tools,
)
from spinedb_api.import_functions import import_object_groups
from spinetoolbox.spine_db_fetcher import SpineDBFetcher
from spinetoolbox.spine_db_manager import SpineDBManager


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        self._logger = MagicMock()  # Collects error messages therefore handy for debugging.
        self._db_mngr = SpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", self._logger, codename="test_db", create=True)
        self._listener = MagicMock()
        self._fetcher = SpineDBFetcher(self._db_mngr, self._listener)
        self._semaphore = Semaphore()
        self._fetcher.finished.connect(self._semaphore.let_continue)

    def tearDown(self):
        self._fetcher.clean_up()
        self.assertFalse(self._listener.silenced)
        self._db_mngr.close_all_sessions()
        self._semaphore.deleteLater()

    def test_fetch_empty_database(self):
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self.assertTrue(self._listener.silenced)
        self._listener.receive_alternatives_fetched.assert_called_once_with(
            {self._db_map: [{"id": 1, "name": "Base", "description": "Base alternative", "commit_id": 1}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "alternative", 1),
            {'commit_id': 1, 'description': 'Base alternative', 'id': 1, 'name': 'Base'},
        )
        self._listener.receive_scenarios_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_scenario_alternatives_fetched.assert_not_called()
        self._listener.receive_object_classes_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_objects_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_relationship_classes_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_relationships_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_entity_groups_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_parameter_definitions_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_parameter_definition_tags_fetched.assert_not_called()
        self._listener.receive_parameter_values_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_parameter_value_lists_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_parameter_tags_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_features_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_tools_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_tool_features_fetched.assert_called_once_with({self._db_map: []})
        self._listener.receive_tool_feature_methods_fetched.assert_called_once_with({self._db_map: []})

    def test_fetch_alternatives(self):
        import_alternatives(self._db_map, ("alt",))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_alternatives_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {'id': 1, 'name': 'Base', 'description': 'Base alternative', 'commit_id': 1},
                    {'id': 2, 'name': 'alt', 'description': None, 'commit_id': 2},
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "alternative", 2),
            {'commit_id': 2, 'description': None, 'id': 2, 'name': 'alt'},
        )

    def test_fetch_scenarios(self):
        import_scenarios(self._db_map, ("scenario",))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_scenarios_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 1,
                        'name': 'scenario',
                        'description': None,
                        'active': False,
                        'alternative_id_list': None,
                        'alternative_name_list': None,
                    }
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "scenario", 1),
            {
                'active': False,
                'alternative_id_list': None,
                'alternative_name_list': None,
                'description': None,
                'id': 1,
                'name': 'scenario',
            },
        )

    def test_fetch_scenario_alternatives(self):
        import_alternatives(self._db_map, ("alt",))
        import_scenarios(self._db_map, ("scenario",))
        import_scenario_alternatives(self._db_map, (("scenario", "alt"),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "scenario_alternative", 1),
            {'alternative_id': 2, 'commit_id': 2, 'id': 1, 'rank': 1, 'scenario_id': 1},
        )

    def test_fetch_object_classes(self):
        import_object_classes(self._db_map, ("oc",))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_object_classes_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 1,
                        'name': 'oc',
                        'description': None,
                        'display_order': 99,
                        'display_icon': None,
                        'hidden': 0,
                        'commit_id': 2,
                    }
                ]
            }
        )
        self.assertIsInstance(self._db_mngr.entity_class_icon(self._db_map, "object_class", 1), QIcon)
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "object_class", 1),
            {
                'commit_id': 2,
                'description': None,
                'display_icon': None,
                'display_order': 99,
                'hidden': 0,
                'id': 1,
                'name': 'oc',
            },
        )

    def test_fetch_objects(self):
        import_object_classes(self._db_map, ("oc",))
        import_objects(self._db_map, (("oc", "obj"),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_objects_fetched.assert_called_once_with(
            {self._db_map: [{'id': 1, 'class_id': 1, 'class_name': 'oc', 'name': 'obj', 'description': None}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "object", 1),
            {'class_id': 1, 'class_name': 'oc', 'description': None, 'id': 1, 'name': 'obj'},
        )

    def test_fetch_relationship_classes(self):
        import_object_classes(self._db_map, ("oc",))
        import_relationship_classes(self._db_map, (("rc", ("oc",)),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_relationship_classes_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 2,
                        'name': 'rc',
                        'description': None,
                        'object_class_id_list': '1',
                        'object_class_name_list': 'oc',
                    }
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "relationship_class", 2),
            {'description': None, 'id': 2, 'name': 'rc', 'object_class_id_list': '1', 'object_class_name_list': 'oc'},
        )

    def test_fetch_relationships(self):
        import_object_classes(self._db_map, ("oc",))
        import_objects(self._db_map, (("oc", "obj"),))
        import_relationship_classes(self._db_map, (("rc", ("oc",)),))
        import_relationships(self._db_map, (("rc", ("obj",)),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_relationships_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 2,
                        'name': 'rc_obj',
                        'class_id': 2,
                        'class_name': 'rc',
                        'object_id_list': '1',
                        'object_name_list': 'obj',
                        'object_class_id_list': '1',
                        'object_class_name_list': 'oc',
                    }
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "relationship", 2),
            {
                'class_id': 2,
                'class_name': 'rc',
                'id': 2,
                'name': 'rc_obj',
                'object_class_id_list': '1',
                'object_class_name_list': 'oc',
                'object_id_list': '1',
                'object_name_list': 'obj',
            },
        )

    def test_fetch_object_groups(self):
        import_object_classes(self._db_map, ("oc",))
        import_objects(self._db_map, (("oc", "obj"), ("oc", "group")))
        import_object_groups(self._db_map, (("oc", "group", "obj"),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_entity_groups_fetched.assert_called_once_with(
            {self._db_map: [{'id': 1, 'entity_id': 2, 'entity_class_id': 1, 'member_id': 1}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "entity_group", 1),
            {'entity_class_id': 1, 'entity_id': 2, 'id': 1, 'member_id': 1},
        )

    def test_fetch_parameter_definitions(self):
        import_object_classes(self._db_map, ("oc",))
        import_object_parameters(self._db_map, (("oc", "param"),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_parameter_definitions_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 1,
                        'entity_class_id': 1,
                        'object_class_id': 1,
                        'object_class_name': 'oc',
                        'parameter_name': 'param',
                        'value_list_id': None,
                        'value_list_name': None,
                        'parameter_tag_id_list': None,
                        'parameter_tag_list': None,
                        'default_value': None,
                        'description': None,
                    }
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "parameter_definition", 1),
            {
                'default_value': None,
                'description': None,
                'entity_class_id': 1,
                'id': 1,
                'object_class_id': 1,
                'object_class_name': 'oc',
                'parameter_name': 'param',
                'parameter_tag_id_list': None,
                'parameter_tag_list': None,
                'value_list_id': None,
                'value_list_name': None,
            },
        )

    def test_fetch_parameter_values(self):
        import_object_classes(self._db_map, ("oc",))
        import_objects(self._db_map, (("oc", "obj"),))
        import_object_parameters(self._db_map, (("oc", "param"),))
        import_object_parameter_values(self._db_map, (("oc", "obj", "param", 2.3),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_parameter_values_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 1,
                        'entity_class_id': 1,
                        'object_class_id': 1,
                        'object_class_name': 'oc',
                        'entity_id': 1,
                        'object_id': 1,
                        'object_name': 'obj',
                        'parameter_id': 1,
                        'parameter_name': 'param',
                        'alternative_id': 1,
                        'alternative_name': 'Base',
                        'value': '2.3',
                    }
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "parameter_value", 1),
            {
                'alternative_id': 1,
                'alternative_name': 'Base',
                'entity_class_id': 1,
                'entity_id': 1,
                'id': 1,
                'object_class_id': 1,
                'object_class_name': 'oc',
                'object_id': 1,
                'object_name': 'obj',
                'parameter_id': 1,
                'parameter_name': 'param',
                'value': '2.3',
            },
        )

    def test_fetch_parameter_value_lists(self):
        import_parameter_value_lists(self._db_map, (("value_list", (2.3,)),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_parameter_value_lists_fetched.assert_called_once_with(
            {self._db_map: [{'id': 1, 'name': 'value_list', 'value_index_list': '0', 'value_list': '[2.3]'}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "parameter_value_list", 1),
            {'id': 1, 'name': 'value_list', 'value_index_list': '0', 'value_list': '[2.3]'},
        )

    def test_fetch_features(self):
        import_object_classes(self._db_map, ("oc",))
        import_parameter_value_lists(self._db_map, (("value_list", (2.3,)),))
        import_object_parameters(self._db_map, (("oc", "param", 2.3, "value_list"),))
        import_features(self._db_map, (("oc", "param"),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_features_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 1,
                        'entity_class_id': 1,
                        'entity_class_name': 'oc',
                        'parameter_definition_id': 1,
                        'parameter_definition_name': 'param',
                        'parameter_value_list_id': 1,
                        'parameter_value_list_name': 'value_list',
                        'description': None,
                    }
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "feature", 1),
            {
                'description': None,
                'entity_class_id': 1,
                'entity_class_name': 'oc',
                'id': 1,
                'parameter_definition_id': 1,
                'parameter_definition_name': 'param',
                'parameter_value_list_id': 1,
                'parameter_value_list_name': 'value_list',
            },
        )

    def test_fetch_tools(self):
        import_tools(self._db_map, ("tool",))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_tools_fetched.assert_called_once_with(
            {self._db_map: [{'id': 1, 'name': 'tool', 'description': None, 'commit_id': 2}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "tool", 1),
            {'commit_id': 2, 'description': None, 'id': 1, 'name': 'tool'},
        )

    def test_fetch_tool_features(self):
        import_object_classes(self._db_map, ("oc",))
        import_parameter_value_lists(self._db_map, (("value_list", (2.3,)),))
        import_object_parameters(self._db_map, (("oc", "param", 2.3, "value_list"),))
        import_features(self._db_map, (("oc", "param"),))
        import_tools(self._db_map, ("tool",))
        import_tool_features(self._db_map, (("tool", "oc", "param"),))
        self._db_map.commit_session("Add test data.")
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_tool_features_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 1,
                        'tool_id': 1,
                        'feature_id': 1,
                        'parameter_value_list_id': 1,
                        'required': False,
                        'commit_id': 2,
                    }
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "tool_feature", 1),
            {'commit_id': 2, 'feature_id': 1, 'id': 1, 'parameter_value_list_id': 1, 'required': False, 'tool_id': 1},
        )

    def test_fetch_tool_feature_methods(self):
        import_object_classes(self._db_map, ("oc",))
        import_parameter_value_lists(self._db_map, (("value_list", "m"),))
        import_object_parameters(self._db_map, (("oc", "param", "m", "value_list"),))
        import_features(self._db_map, (("oc", "param"),))
        import_tools(self._db_map, ("tool",))
        import_tool_features(self._db_map, (("tool", "oc", "param"),))
        import_tool_feature_methods(self._db_map, (("tool", "oc", "param", "m"),))
        self._db_map.commit_session("Add test data.")
        value_lists = self._db_map.query(self._db_map.wide_parameter_value_list_sq).all()
        self._fetcher.fetch([self._db_map])
        while not self._semaphore.fetcher_finished:
            QApplication.processEvents()
        self._listener.receive_tool_feature_methods_fetched.assert_called_once_with(
            {
                self._db_map: [
                    {'id': 1, 'tool_feature_id': 1, 'parameter_value_list_id': 1, 'method_index': 0, 'commit_id': 2}
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "tool_feature_method", 1),
            {'commit_id': 2, 'id': 1, 'method_index': 0, 'parameter_value_list_id': 1, 'tool_feature_id': 1},
        )


class Semaphore(QObject):
    def __init__(self):
        super().__init__()
        self.fetcher_finished = False

    @Slot()
    def let_continue(self):
        self.fetcher_finished = True


if __name__ == "__main__":
    unittest.main()
