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

"""Unit tests for :class:`AlternativeModel`."""
from pathlib import Path
import pickle
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.mvcmodels import mime_types
from spinetoolbox.spine_db_editor.mvcmodels.alternative_model import AlternativeModel
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import model_data_to_dict, TestSpineDBManager


class TestAlternativeModel(unittest.TestCase):
    db_codename = "alternative_model_test_db"

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

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
        model = AlternativeModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        data = model_data_to_dict(model)
        expected = [[{self.db_codename: [["Type new alternative name here...", ""]]}, None]]
        self.assertEqual(data, expected)

    def test_add_alternatives(self):
        model = AlternativeModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        _fetch_all_recursively(model)
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        ["Base", "Base alternative"],
                        ["alternative_1", ""],
                        ["Type new alternative name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)

    def test_update_alternatives(self):
        model = AlternativeModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        _fetch_all_recursively(model)
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1", "id": 2}]})
        self._db_mngr.update_alternatives({self._db_map: [{"id": 2, "name": "renamed"}]})
        data = model_data_to_dict(model)
        expected = [
            [
                {
                    self.db_codename: [
                        ["Base", "Base alternative"],
                        ["renamed", ""],
                        ["Type new alternative name here...", ""],
                    ]
                },
                None,
            ]
        ]
        self.assertEqual(data, expected)

    def test_remove_alternatives(self):
        model = AlternativeModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        _fetch_all_recursively(model)
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1", "id": 2}]})
        self._db_mngr.remove_items({self._db_map: {"alternative": {2}}})
        data = model_data_to_dict(model)
        expected = [
            [{self.db_codename: [["Base", "Base alternative"], ["Type new alternative name here...", ""]]}, None]
        ]
        self.assertEqual(data, expected)

    def test_mimeData(self):
        model = AlternativeModel(self._db_editor, self._db_mngr, self._db_map)
        model.build_tree()
        _fetch_all_recursively(model)
        root_index = model.index(0, 0)
        alternative_index = model.index(0, 0, root_index)
        description_index = model.index(0, 1, root_index)
        mime_data = model.mimeData([alternative_index, description_index])
        self.assertTrue(mime_data.hasText())
        self.assertEqual(mime_data.text(), "Base\tBase alternative\r\n")
        self.assertTrue(mime_data.hasFormat(mime_types.ALTERNATIVE_DATA))
        alternative_data = pickle.loads(mime_data.data(mime_types.ALTERNATIVE_DATA).data())
        self.assertEqual(alternative_data, {self._db_mngr.db_map_key(self._db_map): ["Base"]})


class TestAlternativeModelWithTwoDatabases(unittest.TestCase):
    db_codename = "alternative_model_with_two_databases_test_db"

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map1 = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db_1", create=True)
        url2 = "sqlite:///" + str(Path(self._temp_dir.name, "db2.sqlite"))
        self._db_map2 = self._db_mngr.get_db_map(url2, logger, codename=self.db_codename, create=True)
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite://": "test_db_1", url2: self.db_codename})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map1.closed and not self._db_map2.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._temp_dir.cleanup()

    def test_paste_alternative_mime_data(self):
        self._db_mngr.add_alternatives(
            {self._db_map1: [{"name": "my_alternative", "description": "My test alternative"}]}
        )
        model = AlternativeModel(self._db_editor, self._db_mngr, self._db_map1, self._db_map2)
        model.build_tree()
        _fetch_all_recursively(model)
        root_index = model.index(0, 0)
        source_index = model.index(1, 0, root_index)
        self.assertEqual(source_index.data(), "my_alternative")
        mime_data = model.mimeData([source_index])
        target_index = model.index(1, 0)
        self.assertEqual(target_index.data(), self.db_codename)
        target_item = model.item_from_index(target_index)
        model.paste_alternative_mime_data(mime_data, target_item)
        _fetch_all_recursively(model)
        data = model_data_to_dict(model)
        expected = [
            [
                {
                    "test_db_1": [
                        ["Base", "Base alternative"],
                        ["my_alternative", "My test alternative"],
                        ["Type new alternative name here...", ""],
                    ]
                },
                None,
            ],
            [
                {
                    self.db_codename: [
                        ["Base", "Base alternative"],
                        ["my_alternative", "My test alternative"],
                        ["Type new alternative name here...", ""],
                    ]
                },
                None,
            ],
        ]
        self.assertEqual(data, expected)


def _fetch_all_recursively(model):
    for item in model.visit_all():
        while item.can_fetch_more():
            item.fetch_more()
            qApp.processEvents()


if __name__ == "__main__":
    unittest.main()
