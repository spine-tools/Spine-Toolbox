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

"""Unit tests for ``scenario_model`` module."""
from pathlib import Path
import pickle
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QMimeData, Qt, QByteArray
from PySide6.QtWidgets import QApplication
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.mvcmodels.scenario_model import ScenarioModel
from spinetoolbox.spine_db_editor.mvcmodels import mime_types
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import model_data_to_dict, TestSpineDBManager


class _TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    @staticmethod
    def _fetch_recursively(model):
        for item in model.visit_all():
            while item.can_fetch_more():
                item.fetch_more()
                qApp.processEvents()


class TestScenarioModel(_TestBase):
    db_codename = "scenario_model_test_db"

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename=self.db_codename, create=True)
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": self.db_codename})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()

    def test_initial_state(self):
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        data = model_data_to_dict(model)
        expected = [[{self.db_codename: [["Type new scenario name here...", ""]]}, None]]
        self.assertEqual(data, expected)

    def test_add_scenario(self):
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        self._db_mngr.add_scenarios({self._db_map: [{"name": "scenario_1", "description": "Just a test."}]})
        data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [{"scenario_1": [["Type scenario alternative name here...", ""]]}, "Just a test."],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)

    def test_update_scenario(self):
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        self._db_mngr.add_scenarios({self._db_map: [{"name": "scenario_1", "description": "Just a test.", "id": 1}]})
        self._db_mngr.update_scenarios(
            {self._db_map: [{"name": "scenario_2.0", "description": "More than just a test.", "id": 1}]}
        )
        data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [{"scenario_2.0": [["Type scenario alternative name here...", ""]]}, "More than just a test."],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)

    def test_remove_scenario(self):
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        self._db_mngr.add_scenarios({self._db_map: [{"name": "scenario_1", "description": "Just a test.", "id": 1}]})
        self._db_mngr.remove_items({self._db_map: {"scenario": {1}}})
        data = model_data_to_dict(model)
        expected = [[{self.db_codename: [["Type new scenario name here...", ""]]}, None]]
        self.assertEqual(data, expected)

    def test_mimeData(self):
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        root_index = model.index(0, 0)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        self.assertEqual(scenario_index.data(), "my_scenario")
        add_alternative_index = model.index(0, 0, scenario_index)
        self.assertEqual(add_alternative_index.data(), "Type scenario alternative name here...")
        with signal_waiter(self._db_mngr.items_added, timeout=5.0) as waiter:
            self.assertTrue(model.setData(add_alternative_index, 1, Qt.ItemDataRole.EditRole))
            waiter.wait()
        self._fetch_recursively(model)
        self.assertEqual(model.rowCount(scenario_index), 2)
        alternative_index = model.index(0, 0, scenario_index)
        self.assertEqual(alternative_index.data(), "Base")
        description_index = model.index(0, 1, scenario_index)
        mime_data = model.mimeData([alternative_index, description_index])
        self.assertTrue(mime_data.hasText())
        self.assertEqual(mime_data.text(), "Base\tBase alternative\r\n")
        self.assertTrue(mime_data.hasFormat(mime_types.ALTERNATIVE_DATA))
        data = pickle.loads(mime_data.data(mime_types.ALTERNATIVE_DATA).data())
        id_ = self._db_map.get_alternative_item(id=1)["id"]
        self.assertEqual(data, {self._db_mngr.db_map_key(self._db_map): [id_]})

    def test_canDropMimeData_returns_true_when_dropping_alternative_to_empty_scenario(self):
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        root_index = model.index(0, 0)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        self.assertEqual(scenario_index.data(), "my_scenario")
        mime_data = QMimeData()
        data = {self._db_mngr.db_map_key(self._db_map): ["Base"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        self.assertTrue(model.canDropMimeData(mime_data, Qt.DropAction.CopyAction, -1, -1, scenario_index))

    def test_dropMimeData_adds_alternative_to_model(self):
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        root_index = model.index(0, 0)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        self.assertEqual(scenario_index.data(), "my_scenario")
        mime_data = QMimeData()
        data = {self._db_mngr.db_map_key(self._db_map): ["Base"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        self.assertTrue(model.dropMimeData(mime_data, Qt.DropAction.CopyAction, -1, -1, scenario_index))
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [
                            {
                                "my_scenario": [
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(model_data, expected)

    def test_dropMimeData_reorders_alternatives(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        root_index = model.index(0, 0)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        self.assertEqual(scenario_index.data(), "my_scenario")
        mime_data = QMimeData()
        data = {self._db_mngr.db_map_key(self._db_map): ["Base"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        self.assertTrue(model.dropMimeData(mime_data, Qt.DropAction.CopyAction, -1, -1, scenario_index))
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [
                            {
                                "my_scenario": [
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(model_data, expected)
        mime_data = QMimeData()
        data = {self._db_mngr.db_map_key(self._db_map): ["alternative_1"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        self.assertTrue(model.dropMimeData(mime_data, Qt.DropAction.CopyAction, 0, 0, scenario_index))
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [
                            {
                                "my_scenario": [
                                    ["alternative_1", ""],
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(model_data, expected)
        mime_data = model.mimeData([model.index(1, 0, scenario_index)])
        self.assertTrue(model.dropMimeData(mime_data, Qt.DropAction.CopyAction, 0, 0, scenario_index))
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [
                            {
                                "my_scenario": [
                                    ["Base", "Base alternative"],
                                    ["alternative_1", ""],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(model_data, expected)

    def test_paste_alternative_mime_data(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        root_index = model.index(0, 0)
        self.assertEqual(root_index.data(), self.db_codename)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        self.assertEqual(scenario_index.data(), "my_scenario")
        mime_data = QMimeData()
        data = {self._db_mngr.db_map_key(self._db_map): ["alternative_1"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        scenario_item = model.item_from_index(scenario_index)
        model.paste_alternative_mime_data(mime_data, -1, scenario_item)
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [{"my_scenario": [["alternative_1", ""], ["Type scenario alternative name here...", ""]]}, ""],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(model_data, expected)

    def test_paste_alternative_mime_data_ranks_alternatives(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        root_index = model.index(0, 0)
        self.assertEqual(root_index.data(), self.db_codename)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        self.assertEqual(scenario_index.data(), "my_scenario")
        mime_data = QMimeData()
        data = {self._db_mngr.db_map_key(self._db_map): ["Base"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        scenario_item = model.item_from_index(scenario_index)
        model.paste_alternative_mime_data(mime_data, -1, scenario_item)
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [
                            {
                                "my_scenario": [
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(model_data, expected)
        data = {self._db_mngr.db_map_key(self._db_map): ["alternative_1"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        scenario_item = model.item_from_index(scenario_index)
        model.paste_alternative_mime_data(mime_data, 0, scenario_item)
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [
                            {
                                "my_scenario": [
                                    ["alternative_1", ""],
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(model_data, expected)

    def test_duplicate_scenario(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1", "id": 2}]})
        self._db_mngr.add_scenarios(
            {self._db_map: [{"name": "my_scenario", "description": "My test scenario", "id": 1}]}
        )
        self._db_mngr.set_scenario_alternatives({self._db_map: [{"id": 1, "alternative_id_list": [2, 1]}]})
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        self._fetch_recursively(model)
        root_index = model.index(0, 0)
        scenario_index = model.index(0, 0, root_index)
        scenario_item = model.item_from_index(scenario_index)
        model.duplicate_scenario(scenario_item)
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        [
                            {
                                "my_scenario": [
                                    ["alternative_1", ""],
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "My test scenario",
                        ],
                        [
                            {
                                "my_scenario (1)": [
                                    ["alternative_1", ""],
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "My test scenario",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(model_data, expected)


class TestScenarioModelWithTwoDatabases(_TestBase):
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map1 = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db_1", create=True)
        url2 = "sqlite:///" + str(Path(self._temp_dir.name, "db_2.sqlite"))
        self._db_map2 = self._db_mngr.get_db_map(url2, logger, codename="test_db_2", create=True)
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": "test_db_1", url2: "test_db_2"})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map1.closed and self._db_map2.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._temp_dir.cleanup()

    def test_paste_alternative_mime_data_doesnt_paste_across_databases(self):
        self._db_mngr.add_alternatives({self._db_map1: [{"name": "alternative_1"}]})
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map1, self._db_map2)
        model.build_tree()
        self._fetch_recursively(model)
        root_index = model.index(1, 0)
        self.assertEqual(root_index.data(), "test_db_2")
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        self.assertEqual(scenario_index.data(), "my_scenario")
        mime_data = QMimeData()
        data = {self._db_mngr.db_map_key(self._db_map1): ["alternative_1"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        scenario_item = model.item_from_index(scenario_index)
        model.paste_alternative_mime_data(mime_data, -1, scenario_item)
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [{"test_db_1": [["Type new scenario name here...", ""]]}, None],
            [
                {
                    "test_db_2": [
                        [{"my_scenario": [["Type scenario alternative name here...", ""]]}, ""],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ],
        ]
        self.assertEqual(model_data, expected)

    def test_paste_scenario_mime_data(self):
        self._db_mngr.add_scenarios({self._db_map1: [{"name": "my_scenario"}]})
        self._db_mngr.add_alternatives({self._db_map1: [{"name": "alternative_1"}]})
        scenario_id = self._db_map1.get_scenario_item(name="my_scenario")["id"]
        self._db_mngr.set_scenario_alternatives(
            {self._db_map1: [{"id": scenario_id, "alternative_name_list": ["alternative_1", "Base"]}]}
        )
        model = ScenarioModel(self._db_editor, self._db_mngr, self._db_map1, self._db_map2)
        model.build_tree()
        self._fetch_recursively(model)
        mime_data = QMimeData()
        data = {self._db_mngr.db_map_key(self._db_map1): ["my_scenario"]}
        mime_data.setData(mime_types.SCENARIO_DATA, QByteArray(pickle.dumps(data)))
        root_index = model.index(1, 0)
        self.assertEqual(root_index.data(), "test_db_2")
        db_item = model.item_from_index(root_index)
        model.paste_scenario_mime_data(mime_data, db_item)
        self._fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    "test_db_1": [
                        [
                            {
                                "my_scenario": [
                                    ["alternative_1", ""],
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ],
            [
                {
                    "test_db_2": [
                        [
                            {
                                "my_scenario": [
                                    ["alternative_1", ""],
                                    ["Base", "Base alternative"],
                                    ["Type scenario alternative name here...", ""],
                                ]
                            },
                            "",
                        ],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ],
        ]
        self.assertEqual(model_data, expected)


if __name__ == "__main__":
    unittest.main()
