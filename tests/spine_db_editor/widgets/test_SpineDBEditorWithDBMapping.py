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

"""Unit tests for SpineDBEditor classes."""
import os.path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
import logging
import sys
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import TestSpineDBManager


class TestSpineDBEditorWithDBMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def setUp(self):
        """Overridden method. Runs before each test. Makes instances of SpineDBEditor classes."""
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test.sqlite")
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwards: 0
            self.db_mngr = TestSpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self.db_map = self.db_mngr.get_db_map(url, logger, codename="db", create=True)
            self.spine_db_editor = SpineDBEditor(self.db_mngr, {url: "db"})
            self.spine_db_editor.pivot_table_model = mock.MagicMock()

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ) as mock_save_w_s, mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self.spine_db_editor.close()
            mock_save_w_s.assert_called_once()
        QApplication.removePostedEvents(None)  # Clean up unfinished fetcher signals
        self.db_mngr.close_all_sessions()
        self.db_mngr.clean_up()
        self.db_mngr = None  # Ensure the database file is closed to allow the temporary directory to be removed.
        self.spine_db_editor.deleteLater()
        self.spine_db_editor = None
        self._temp_dir.cleanup()

    def fetch_object_tree_model(self):
        for item in self.spine_db_editor.entity_tree_model.visit_all():
            if item.can_fetch_more():
                item.fetch_more()

    def test_duplicate_object_in_object_tree_model(self):
        data = {
            "entity_classes": [("fish",), ("dog",), ("fish__dog", ("fish", "dog"))],
            "entities": [("fish", "nemo"), ("dog", "pluto"), ("fish__dog", ("nemo", "pluto"))],
            "parameter_definitions": [("fish", "color")],
            "parameter_values": [("fish", "nemo", "color", "orange")],
        }
        self.db_mngr.import_data({self.db_map: data})
        self.fetch_object_tree_model()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = next(iter(item for item in root_item.children if item.display_data == "fish"))
        nemo_item = fish_item.child(0)
        with mock.patch.object(self.db_mngr, "error_msg") as error_msg_signal:
            self.spine_db_editor.duplicate_entity(nemo_item)
            error_msg_signal.emit.assert_not_called()
        self.assertEqual(fish_item.row_count(), 2)
        nemo_dupe = fish_item.child(1)
        self.assertEqual(nemo_dupe.display_data, "nemo (1)")
        fish_dog_item = next(iter(item for item in root_item.children if item.display_data == "fish__dog"))
        fish_dog_item.fetch_more()
        self.assertEqual(fish_dog_item.row_count(), 2)
        nemo_pluto_dupe = fish_dog_item.child(1)
        self.assertEqual(nemo_pluto_dupe.display_data, "nemo (1) ǀ pluto")
        root_index = self.spine_db_editor.entity_tree_model.index_from_item(root_item)
        self.spine_db_editor.ui.treeView_entity.selectionModel().setCurrentIndex(
            root_index, QItemSelectionModel.SelectionFlags.ClearAndSelect
        )
        while self.spine_db_editor.parameter_value_model.rowCount() != 3:
            QApplication.processEvents()
        expected = [
            ["fish", "nemo", "color", "Base", "orange", "db"],
            ["fish", "nemo (1)", "color", "Base", "orange", "db"],
            [None, None, None, None, None, "db"],
        ]
        for row in range(3):
            for column in range(self.spine_db_editor.parameter_value_model.columnCount()):
                with self.subTest(row=row, column=column):
                    self.assertEqual(
                        self.spine_db_editor.parameter_value_model.index(row, column).data(), expected[row][column]
                    )


if __name__ == "__main__":
    unittest.main()
