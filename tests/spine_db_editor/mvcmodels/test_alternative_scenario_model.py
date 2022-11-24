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
Unit tests for :class:`AlternativeScenarioModel`.

:authors: A. Soininen (VTT)
:date:    21.1.2021
"""
import unittest
from unittest.mock import MagicMock, patch
from PySide2.QtCore import QModelIndex
from PySide2.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.mvcmodels.alternative_scenario_model import AlternativeScenarioModel
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from ...mock_helpers import TestSpineDBManager


class TestAlternativeScenarioModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": "test_db"})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()

    def test_initial_state(self):
        model = AlternativeScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        data = self._model_data_to_dict(model)
        expected = [
            [
                {
                    "test_db": [
                        [{"alternative": [["Type new alternative name here...", ""]]}, None],
                        [{"scenario": [["Type new scenario name here...", ""]]}, None],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)

    def test_add_alternatives(self):
        model = AlternativeScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        for item in model.visit_all():
            if item.can_fetch_more():
                item.fetch_more()
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        data = self._model_data_to_dict(model)
        expected = [
            [
                {
                    "test_db": [
                        [
                            {
                                "alternative": [
                                    ["Base", "Base alternative"],
                                    ["alternative_1", ""],
                                    ["Type new alternative name here...", ""],
                                ]
                            },
                            None,
                        ],
                        [{"scenario": [["Type new scenario name here...", ""]]}, None],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)
        index = model.index(0, 0)
        index = model.index(0, 0, index)
        index = model.index(0, 0, index)
        self.assertTrue(model.setData(index, "perse"))

    def test_add_alternatives_with_scenario_alternative(self):
        model = AlternativeScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        for item in model.visit_all():
            if item.can_fetch_more():
                item.fetch_more()
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        self._db_mngr.add_scenarios({self._db_map: [{"name": "scenario_1"}]})
        self._db_mngr.set_scenario_alternatives({self._db_map: [{"id": 1, "alternative_id_list": [2]}]})
        data = self._model_data_to_dict(model)
        expected = [
            [
                {
                    'test_db': [
                        [
                            {
                                'alternative': [
                                    ["Base", "Base alternative"],
                                    ['alternative_1', ''],
                                    ['Type new alternative name here...', ''],
                                ]
                            },
                            None,
                        ],
                        [
                            {
                                'scenario': [
                                    [
                                        {
                                            'scenario_1': [
                                                ['active: no', None],
                                                [
                                                    {
                                                        'scenario_alternative': [
                                                            ['alternative_1', ''],
                                                            ['Type scenario alternative name here...', ''],
                                                        ]
                                                    },
                                                    None,
                                                ],
                                            ]
                                        },
                                        '',
                                    ],
                                    ['Type new scenario name here...', ''],
                                ]
                            },
                            None,
                        ],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)
        index = model.index(0, 0)
        index = model.index(0, 0, index)
        index = model.index(0, 0, index)
        self.assertTrue(model.setData(index, "perse"))

    def test_update_alternatives(self):
        model = AlternativeScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        for item in model.visit_all():
            if item.can_fetch_more():
                item.fetch_more()
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        self._db_mngr.update_alternatives({self._db_map: [{"id": 2, "name": "renamed"}]})
        data = self._model_data_to_dict(model)
        expected = [
            [
                {
                    "test_db": [
                        [
                            {
                                "alternative": [
                                    ["Base", "Base alternative"],
                                    ["renamed", ""],
                                    ["Type new alternative name here...", ""],
                                ]
                            },
                            None,
                        ],
                        [{"scenario": [["Type new scenario name here...", ""]]}, None],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)

    def test_update_alternatives_with_scenario_alternatives(self):
        model = AlternativeScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        for item in model.visit_all():
            if item.can_fetch_more():
                item.fetch_more()
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        self._db_mngr.add_scenarios({self._db_map: [{"name": "scenario_1"}]})
        self._db_mngr.set_scenario_alternatives({self._db_map: [{"id": 1, "alternative_id_list": [2]}]})
        self._db_mngr.update_alternatives({self._db_map: [{"id": 2, "name": "renamed"}]})
        self._db_mngr.update_alternatives({self._db_map: [{"id": 2}]})
        self._db_mngr.update_scenarios({self._db_map: [{"id": 1, "alternative_id_list": [2]}]})
        data = self._model_data_to_dict(model)
        expected = [
            [
                {
                    'test_db': [
                        [
                            {
                                'alternative': [
                                    ["Base", "Base alternative"],
                                    ['renamed', ''],
                                    ['Type new alternative name here...', ''],
                                ]
                            },
                            None,
                        ],
                        [
                            {
                                'scenario': [
                                    [
                                        {
                                            'scenario_1': [
                                                ['active: no', None],
                                                [
                                                    {
                                                        'scenario_alternative': [
                                                            ['renamed', ''],
                                                            ['Type scenario alternative name here...', ''],
                                                        ]
                                                    },
                                                    None,
                                                ],
                                            ]
                                        },
                                        '',
                                    ],
                                    ['Type new scenario name here...', ''],
                                ]
                            },
                            None,
                        ],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)

    def test_remove_alternatives(self):
        model = AlternativeScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        for item in model.visit_all():
            if item.can_fetch_more():
                item.fetch_more()
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        self._db_mngr.remove_items({self._db_map: {"alternative": {2}}})
        data = self._model_data_to_dict(model)
        expected = [
            [
                {
                    "test_db": [
                        [
                            {"alternative": [["Base", "Base alternative"], ["Type new alternative name here...", ""]]},
                            None,
                        ],
                        [{"scenario": [["Type new scenario name here...", ""]]}, None],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)

    def _model_data_to_dict(self, model, parent=QModelIndex()):
        self.assertEqual(model.columnCount(parent), 2)
        rows = list()
        for row in range(model.rowCount(parent)):
            index = model.index(row, 0, parent)
            child_data = self._model_data_to_dict(model, index)
            data1 = {index.data(): child_data} if child_data else index.data()
            index = model.index(row, 1, parent)
            child_data = self._model_data_to_dict(model, index)
            data2 = {index.data(): child_data} if child_data else index.data()
            rows.append([data1, data2])
        return rows


if __name__ == '__main__':
    unittest.main()
