######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for SpineDBEditor classes.

:author: M. Marin (KTH)
:date:   6.12.2018
"""

import unittest
from unittest import mock
from pathlib import Path
import tempfile
import logging
import sys
from PySide2.QtWidgets import QApplication
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.spine_db_manager import SpineDBManager
from spinedb_api import create_new_spine_database, import_data


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
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def setUp(self):
        """Overridden method. Runs before each test. Makes instances of SpineDBEditor classes."""
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwards: 0
            self.db_mngr = SpineDBManager(mock_settings, None, None)
            # TODO: Use a temp file?
            url = "sqlite:///test.sqlite"
            create_new_spine_database(url)
            self.db_mngr.fetch_db_maps_for_listener = lambda *args: None
            self.db_mngr.show_spine_db_editor({url: "db"}, None)
            self.spine_db_editor = next(iter(self.db_mngr.db_editors))
            self.db_map = self.spine_db_editor.first_db_map
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
        self.spine_db_editor.deleteLater()
        self.spine_db_editor = None

    def fetch_object_tree_model(self):
        for item in self.spine_db_editor.object_tree_model.visit_all():
            if item.can_fetch_more():
                item.fetch_more()

    def test_duplicate_object_in_object_tree_model(self):
        data = dict()
        data["object_classes"] = ["fish", "dog"]
        data["relationship_classes"] = [("fish__dog", ("fish", "dog"))]
        data["objects"] = [("fish", "nemo"), ("dog", "pluto")]
        data["relationships"] = [("fish__dog", ("nemo", "pluto"))]
        data["object_parameters"] = [("fish", "color")]
        data["object_parameter_values"] = [("fish", "nemo", "color", "orange")]
        self.db_mngr.import_data({self.db_map: data})
        self.fetch_object_tree_model()
        root_item = self.spine_db_editor.object_tree_model.root_item
        fish_item = next(iter(item for item in root_item.children if item.display_data == "fish"))
        nemo_item = fish_item.child(0)
        with mock.patch("spinetoolbox.spine_db_editor.widgets.tree_view_mixin.QInputDialog") as mock_input_dialog:
            mock_input_dialog.getText.side_effect = lambda *args, **kwargs: ("nemo_copy", True)
            self.spine_db_editor.duplicate_object(nemo_item.index())
        nemo_dupe = fish_item.child(1)
        self.assertEqual(nemo_dupe.display_data, "nemo_copy")


if __name__ == '__main__':
    unittest.main()
