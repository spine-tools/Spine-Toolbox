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

import pickle
from PySide6.QtCore import QByteArray, QMimeData, Qt
from PySide6.QtWidgets import QApplication
import pytest
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.mvcmodels import mime_types
from spinetoolbox.spine_db_editor.mvcmodels.scenario_model import ScenarioModel
from tests.mock_helpers import model_data_to_dict


def _fetch_recursively(model):
    for item in model.visit_all():
        while item.can_fetch_more():
            item.fetch_more()
            QApplication.processEvents()


@pytest.fixture()
def model(db_map, db_editor, db_mngr):
    model = ScenarioModel(db_editor, db_mngr, db_map)
    model.build_tree()
    return model


class TestScenarioModel:
    def test_initial_state(self, model, db_name):
        data = model_data_to_dict(model)
        expected = [[{db_name: [["Type new scenario name here...", ""]]}, None]]
        assert data == expected

    def test_add_scenario(self, model, db_map, db_name, db_mngr):
        _fetch_recursively(model)
        db_mngr.add_items("scenario", {db_map: [{"name": "scenario_1", "description": "Just a test."}]})
        data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
                        [{"scenario_1": [["Type scenario alternative name here...", ""]]}, "Just a test."],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        assert data == expected

    def test_update_scenario(self, model, db_map, db_name, db_mngr):
        _fetch_recursively(model)
        db_mngr.add_items("scenario", {db_map: [{"name": "scenario_1", "description": "Just a test."}]})
        scenario_id = db_map.scenario(name="scenario_1")["id"]
        db_mngr.update_items(
            "scenario",
            {db_map: [{"name": "scenario_2.0", "description": "More than just a test.", "id": scenario_id}]},
        )
        data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
                        [{"scenario_2.0": [["Type scenario alternative name here...", ""]]}, "More than just a test."],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        assert data == expected

    def test_remove_scenario(self, model, db_map, db_name, db_mngr):
        _fetch_recursively(model)
        db_mngr.add_items("scenario", {db_map: [{"name": "scenario_1", "description": "Just a test."}]})
        scenario_id = db_map.scenario(name="scenario_1")["id"]
        db_mngr.remove_items({db_map: {"scenario": {scenario_id}}})
        data = model_data_to_dict(model)
        expected = [[{db_name: [["Type new scenario name here...", ""]]}, None]]
        assert data == expected

    def test_mimeData(self, model, db_map, db_name, db_mngr):
        _fetch_recursively(model)
        root_index = model.index(0, 0)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        assert scenario_index.data() == "my_scenario"
        add_alternative_index = model.index(0, 0, scenario_index)
        assert add_alternative_index.data() == "Type scenario alternative name here..."
        with signal_waiter(db_mngr.items_added, timeout=5.0) as waiter:
            assert model.setData(add_alternative_index, 1, Qt.ItemDataRole.EditRole)
            waiter.wait()
        _fetch_recursively(model)
        assert model.rowCount(scenario_index) == 2
        alternative_index = model.index(0, 0, scenario_index)
        assert alternative_index.data() == "Base"
        description_index = model.index(0, 1, scenario_index)
        mime_data = model.mimeData([alternative_index, description_index])
        assert mime_data.hasText()
        assert mime_data.text() == "Base\tBase alternative\r\n"
        assert mime_data.hasFormat(mime_types.ALTERNATIVE_DATA)
        data = pickle.loads(mime_data.data(mime_types.ALTERNATIVE_DATA).data())
        id_ = db_map.get_alternative_item(id=1)["id"]
        assert data == {db_mngr.db_map_key(db_map): [id_]}

    def test_canDropMimeData_returns_true_when_dropping_alternative_to_empty_scenario(
        self, model, db_map, db_name, db_mngr
    ):
        _fetch_recursively(model)
        root_index = model.index(0, 0)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        assert scenario_index.data() == "my_scenario"
        mime_data = QMimeData()
        data = {db_mngr.db_map_key(db_map): ["Base"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        assert model.canDropMimeData(mime_data, Qt.DropAction.CopyAction, -1, -1, scenario_index)

    def test_dropMimeData_adds_alternative_to_model(self, model, db_map, db_name, db_mngr):
        _fetch_recursively(model)
        root_index = model.index(0, 0)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        assert scenario_index.data() == "my_scenario"
        mime_data = QMimeData()
        data = {db_mngr.db_map_key(db_map): ["Base"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        assert model.dropMimeData(mime_data, Qt.DropAction.CopyAction, -1, -1, scenario_index)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
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
        assert model_data == expected

    def test_dropMimeData_reorders_alternatives(self, model, db_map, db_name, db_mngr):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        _fetch_recursively(model)
        root_index = model.index(0, 0)
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        assert scenario_index.data() == "my_scenario"
        mime_data = QMimeData()
        data = {db_mngr.db_map_key(db_map): ["Base"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        assert model.dropMimeData(mime_data, Qt.DropAction.CopyAction, -1, -1, scenario_index)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
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
        assert model_data == expected
        mime_data = QMimeData()
        data = {db_mngr.db_map_key(db_map): ["alternative_1"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        assert model.dropMimeData(mime_data, Qt.DropAction.CopyAction, 0, 0, scenario_index)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
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
        assert model_data == expected
        mime_data = model.mimeData([model.index(1, 0, scenario_index)])
        assert model.dropMimeData(mime_data, Qt.DropAction.CopyAction, 0, 0, scenario_index)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
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
        assert model_data == expected

    def test_paste_alternative_mime_data(self, model, db_map, db_name, db_mngr):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        _fetch_recursively(model)
        root_index = model.index(0, 0)
        assert root_index.data() == db_name
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        assert scenario_index.data() == "my_scenario"
        mime_data = QMimeData()
        data = {db_mngr.db_map_key(db_map): ["alternative_1"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        scenario_item = model.item_from_index(scenario_index)
        model.paste_alternative_mime_data(mime_data, -1, scenario_item)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
                        [{"my_scenario": [["alternative_1", ""], ["Type scenario alternative name here...", ""]]}, ""],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ]
        ]
        assert model_data == expected

    def test_paste_alternative_mime_data_ranks_alternatives(self, model, db_map, db_name, db_mngr):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        _fetch_recursively(model)
        root_index = model.index(0, 0)
        assert root_index.data() == db_name
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        assert scenario_index.data() == "my_scenario"
        mime_data = QMimeData()
        data = {db_mngr.db_map_key(db_map): ["Base"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        scenario_item = model.item_from_index(scenario_index)
        model.paste_alternative_mime_data(mime_data, -1, scenario_item)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
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
        assert model_data == expected
        data = {db_mngr.db_map_key(db_map): ["alternative_1"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        scenario_item = model.item_from_index(scenario_index)
        model.paste_alternative_mime_data(mime_data, 0, scenario_item)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
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
        assert model_data == expected

    def test_duplicate_scenario(self, model, db_map, db_name, db_mngr, db_editor):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        db_mngr.add_items("scenario", {db_map: [{"name": "my_scenario", "description": "My test scenario"}]})
        scenario_id = db_map.scenario(name="my_scenario")["id"]
        base_alternative_id = db_map.alternative(name="Base")["id"]
        alternative_1_id = db_map.alternative(name="alternative_1")["id"]
        db_mngr.set_scenario_alternatives(
            {db_map: [{"id": scenario_id, "alternative_id_list": [alternative_1_id, base_alternative_id]}]}
        )
        model = ScenarioModel(db_editor, db_mngr, db_map)
        model.build_tree()
        _fetch_recursively(model)
        root_index = model.index(0, 0)
        scenario_index = model.index(0, 0, root_index)
        scenario_item = model.item_from_index(scenario_index)
        model.duplicate_scenario(scenario_item)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    db_name: [
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
        assert model_data == expected

    def test_paste_alternative_mime_data_doesnt_paste_across_databases(self, db_map_generator, db_mngr, db_editor):
        db_map1 = db_map_generator()
        db_map2 = db_map_generator()
        db_mngr.add_items("alternative", {db_map1: [{"name": "alternative_1"}]})
        model = ScenarioModel(db_editor, db_mngr, db_map1, db_map2)
        model.build_tree()
        _fetch_recursively(model)
        root_index = model.index(1, 0)
        assert root_index.data() == "TestScenarioModel_db_2"
        edit_index = model.index(0, 0, root_index)
        model.setData(edit_index, "my_scenario", Qt.ItemDataRole.EditRole)
        scenario_index = model.index(0, 0, root_index)
        assert scenario_index.data() == "my_scenario"
        mime_data = QMimeData()
        data = {db_mngr.db_map_key(db_map1): ["alternative_1"]}
        mime_data.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(data)))
        scenario_item = model.item_from_index(scenario_index)
        model.paste_alternative_mime_data(mime_data, -1, scenario_item)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [{"TestScenarioModel_db_1": [["Type new scenario name here...", ""]]}, None],
            [
                {
                    "TestScenarioModel_db_2": [
                        [{"my_scenario": [["Type scenario alternative name here...", ""]]}, ""],
                        ["Type new scenario name here...", ""],
                    ]
                },
                None,
            ],
        ]
        assert model_data == expected

    def test_paste_scenario_mime_data(self, db_map_generator, db_mngr, db_editor):
        db_map1 = db_map_generator()
        db_map2 = db_map_generator()
        db_mngr.add_items("scenario", {db_map1: [{"name": "my_scenario"}]})
        db_mngr.add_items("alternative", {db_map1: [{"name": "alternative_1"}]})
        scenario_id = db_map1.scenario(name="my_scenario")["id"]
        db_mngr.set_scenario_alternatives(
            {db_map1: [{"id": scenario_id, "alternative_name_list": ["alternative_1", "Base"]}]}
        )
        model = ScenarioModel(db_editor, db_mngr, db_map1, db_map2)
        model.build_tree()
        _fetch_recursively(model)
        mime_data = QMimeData()
        data = {db_mngr.db_map_key(db_map1): ["my_scenario"]}
        mime_data.setData(mime_types.SCENARIO_DATA, QByteArray(pickle.dumps(data)))
        root_index = model.index(1, 0)
        assert root_index.data() == "TestScenarioModel_db_2"
        db_item = model.item_from_index(root_index)
        model.paste_scenario_mime_data(mime_data, db_item)
        _fetch_recursively(model)
        model_data = model_data_to_dict(model)
        expected = [
            [
                {
                    "TestScenarioModel_db_1": [
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
                    "TestScenarioModel_db_2": [
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
        assert model_data == expected
