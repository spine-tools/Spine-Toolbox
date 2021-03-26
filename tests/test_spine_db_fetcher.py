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
from spinetoolbox.spine_db_fetcher import SpineDBFetcher
from spinetoolbox.spine_db_manager import SpineDBManager


class TestSpineDBFetcher(unittest.TestCase):
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
        self._fetcher = self._db_mngr.get_fetcher()
        self._fetcher_semaphore = Semaphore()
        self._import_semaphore = Semaphore()
        self._commit_semaphore = Semaphore()
        self._fetcher.finished.connect(self._fetcher_semaphore.let_continue)
        self._db_mngr.data_imported.connect(self._import_semaphore.let_continue)
        self._db_mngr.session_committed.connect(self._commit_semaphore.let_continue)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()
        self._fetcher_semaphore.deleteLater()
        self._import_semaphore.deleteLater()
        self._commit_semaphore.deleteLater()
        QApplication.processEvents()

    def test_fetch_empty_database(self):
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self.assertTrue(self._listener.silenced)
        self._listener.receive_alternatives_added.assert_called_once_with(
            {self._db_map: [{"id": 1, "name": "Base", "description": "Base alternative", "commit_id": 1}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "alternative", 1),
            {'commit_id': 1, 'description': 'Base alternative', 'id': 1, 'name': 'Base'},
        )
        self._listener.receive_scenarios_added.assert_not_called()
        self._listener.receive_scenario_alternatives_added.assert_not_called()
        self._listener.receive_object_classes_added.assert_not_called()
        self._listener.receive_objects_added.assert_not_called()
        self._listener.receive_relationship_classes_added.assert_not_called()
        self._listener.receive_relationships_added.assert_not_called()
        self._listener.receive_entity_groups_added.assert_not_called()
        self._listener.receive_parameter_definitions_added.assert_not_called()
        self._listener.receive_parameter_definition_tags_added.assert_not_called()
        self._listener.receive_parameter_values_added.assert_not_called()
        self._listener.receive_parameter_value_lists_added.assert_not_called()
        self._listener.receive_parameter_tags_added.assert_not_called()
        self._listener.receive_features_added.assert_not_called()
        self._listener.receive_tools_added.assert_not_called()
        self._listener.receive_tool_features_added.assert_not_called()
        self._listener.receive_tool_feature_methods_added.assert_not_called()

    def _import_data(self, **data):
        self._db_mngr.import_data({self._db_map: data})
        while not self._import_semaphore.can_continue:
            QApplication.processEvents()
        self._db_mngr._get_commit_msg = lambda *args, **kwargs: "Add test data."
        self._db_mngr.commit_session(self._db_map)
        while not self._commit_semaphore.can_continue:
            QApplication.processEvents()

    def test_fetch_alternatives(self):
        self._import_data(alternatives=("alt",))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_alternatives_added.assert_called_once_with(
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
        self._import_data(scenarios=("scenario",))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_scenarios_added.assert_called_once_with(
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
        self._import_data(alternatives=("alt",), scenarios=("scenario",), scenario_alternatives=(("scenario", "alt"),))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "scenario_alternative", 1),
            {'alternative_id': 2, 'commit_id': 2, 'id': 1, 'rank': 1, 'scenario_id': 1},
        )

    def test_fetch_object_classes(self):
        self._import_data(object_classes=("oc",))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_object_classes_added.assert_called_once_with(
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
        self._import_data(object_classes=("oc",), objects=(("oc", "obj"),))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_objects_added.assert_called_once_with(
            {self._db_map: [{'id': 1, 'class_id': 1, 'class_name': 'oc', 'name': 'obj', 'description': None}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "object", 1),
            {'class_id': 1, 'class_name': 'oc', 'description': None, 'id': 1, 'name': 'obj'},
        )

    def test_fetch_relationship_classes(self):
        self._import_data(object_classes=("oc",), relationship_classes=(("rc", ("oc",)),))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_relationship_classes_added.assert_called_once_with(
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
        self._import_data(
            object_classes=("oc",),
            objects=(("oc", "obj"),),
            relationship_classes=(("rc", ("oc",)),),
            relationships=(("rc", ("obj",)),),
        )
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_relationships_added.assert_called_once_with(
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
        self._import_data(
            object_classes=("oc",), objects=(("oc", "obj"), ("oc", "group")), object_groups=(("oc", "group", "obj"),)
        )
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_entity_groups_added.assert_called_once_with(
            {
                self._db_map: [
                    {
                        'id': 1,
                        'class_id': 1,
                        'group_id': 2,
                        'member_id': 1,
                        'class_name': 'oc',
                        'group_name': 'group',
                        'member_name': 'obj',
                    }
                ]
            }
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "entity_group", 1),
            {
                'id': 1,
                'class_id': 1,
                'group_id': 2,
                'member_id': 1,
                'class_name': 'oc',
                'group_name': 'group',
                'member_name': 'obj',
            },
        )

    def test_fetch_parameter_definitions(self):
        self._import_data(object_classes=("oc",), object_parameters=(("oc", "param"),))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_parameter_definitions_added.assert_called_once_with(
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
        self._import_data(
            object_classes=("oc",),
            objects=(("oc", "obj"),),
            object_parameters=(("oc", "param"),),
            object_parameter_values=(("oc", "obj", "param", 2.3),),
        )
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_parameter_values_added.assert_called_once_with(
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
        self._import_data(parameter_value_lists=(("value_list", (2.3,)),))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_parameter_value_lists_added.assert_called_once_with(
            {self._db_map: [{'id': 1, 'name': 'value_list', 'value_index_list': '0', 'value_list': '[2.3]'}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "parameter_value_list", 1),
            {'id': 1, 'name': 'value_list', 'value_index_list': '0', 'value_list': '[2.3]'},
        )

    def test_fetch_features(self):
        self._import_data(
            object_classes=("oc",),
            parameter_value_lists=(("value_list", (2.3,)),),
            object_parameters=(("oc", "param", 2.3, "value_list"),),
            features=(("oc", "param"),),
        )
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_features_added.assert_called_once_with(
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
        self._import_data(tools=("tool",))
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_tools_added.assert_called_once_with(
            {self._db_map: [{'id': 1, 'name': 'tool', 'description': None, 'commit_id': 2}]}
        )
        self.assertEqual(
            self._db_mngr.get_item(self._db_map, "tool", 1),
            {'commit_id': 2, 'description': None, 'id': 1, 'name': 'tool'},
        )

    def test_fetch_tool_features(self):
        self._import_data(
            object_classes=("oc",),
            parameter_value_lists=(("value_list", (2.3,)),),
            object_parameters=(("oc", "param", 2.3, "value_list"),),
            features=(("oc", "param"),),
            tools=("tool",),
            tool_features=(("tool", "oc", "param"),),
        )
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_tool_features_added.assert_called_once_with(
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
        self._import_data(
            object_classes=("oc",),
            parameter_value_lists=(("value_list", "m"),),
            object_parameters=(("oc", "param", "m", "value_list"),),
            features=(("oc", "param"),),
            tools=("tool",),
            tool_features=(("tool", "oc", "param"),),
            tool_feature_methods=(("tool", "oc", "param", "m"),),
        )
        self._fetcher.fetch(self._listener, [self._db_map])
        while not self._fetcher_semaphore.can_continue:
            QApplication.processEvents()
        self._listener.receive_tool_feature_methods_added.assert_called_once_with(
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
        self.can_continue = False

    @Slot()
    def let_continue(self):
        self.can_continue = True


if __name__ == "__main__":
    unittest.main()
