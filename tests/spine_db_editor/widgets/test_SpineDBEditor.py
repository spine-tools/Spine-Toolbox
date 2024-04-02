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
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QModelIndex, QItemSelectionModel
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from .spine_db_editor_test_base import DBEditorTestBase
from tests.mock_helpers import TestSpineDBManager


class TestSpineDBEditor(DBEditorTestBase):
    def test_set_object_parameter_definition_defaults(self):
        """Test that defaults are set in object parameter_definition models according the object tree selection."""
        self.spine_db_editor.init_models()
        self.put_mock_object_classes_in_db_mngr()
        self.fetch_object_tree_model()
        # Select fish item in object tree
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = root_item.child(1)
        fish_index = self.spine_db_editor.entity_tree_model.index_from_item(fish_item)
        self.spine_db_editor.ui.treeView_entity.setCurrentIndex(fish_index)
        self.spine_db_editor.ui.treeView_entity.selectionModel().select(fish_index, QItemSelectionModel.Select)
        # Check default in object parameter_definition
        model = self.spine_db_editor.parameter_definition_model
        model.empty_model.fetchMore(QModelIndex())
        h = model.header.index
        row_data = []
        for row in range(model.rowCount()):
            row_data.append(tuple(model.index(row, h(field)).data() for field in ("entity_class_name", "database")))
        self.assertIn(("fish", "database"), row_data)


class TestClosingDBEditors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._editors = []
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = TestSpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="database", create=True)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        for editor in self._editors:
            editor.deleteLater()

    def _make_db_editor(self):
        editor = SpineDBEditor(self._db_mngr, {"sqlite://": "database"})
        self._editors.append(editor)
        return editor

    def test_first_editor_to_close_does_not_ask_for_confirmation_on_dirty_database(self):
        editor_1 = self._make_db_editor()
        editor_2 = self._make_db_editor()
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "my_object_class"}]})
        self.assertTrue(self._db_mngr.dirty(self._db_map))
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor._prompt_to_commit_changes"
        ) as commit_changes:
            commit_changes.return_value = QMessageBox.StandardButton.Discard
            editor_1.close()
            commit_changes.assert_not_called()
            editor_2.close()
            commit_changes.assert_called_once()

    def test_editor_asks_for_confirmation_even_when_non_editor_listeners_are_connected(self):
        editor = self._make_db_editor()
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "my_object_class"}]})
        self.assertTrue(self._db_mngr.dirty(self._db_map))
        non_editor_listener = object()
        self._db_mngr.register_listener(non_editor_listener, self._db_map)
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor._prompt_to_commit_changes"
        ) as commit_changes:
            commit_changes.return_value = QMessageBox.StandardButton.Discard
            editor.close()
            commit_changes.assert_called_once()


if __name__ == "__main__":
    unittest.main()
