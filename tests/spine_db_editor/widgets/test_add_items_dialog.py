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
Unit tests for ``add_items_dialog`` module.
"""

import unittest
from unittest import mock
from tempfile import TemporaryDirectory
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex
from PySide6.QtWidgets import QApplication
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import AddObjectClassesDialog, ManageRelationshipsDialog
from tests.spine_db_editor.widgets.helpers import TestBase


class TestAddItemsDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Overridden method. Runs before each test. Makes instance of SpineDBEditor class."""
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = SpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._temp_dir = TemporaryDirectory()
            url = "sqlite:///" + self._temp_dir.name + "/db.sqlite"
            self._db_map = self._db_mngr.get_db_map(url, logger, codename="mock_db", create=True)
            self._db_editor = SpineDBEditor(self._db_mngr, {url: "mock_db"})

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._db_editor = None
        self._temp_dir.cleanup()

    def test_add_object_classes(self):
        """Test object classes are added through the manager when accepting the dialog."""
        dialog = AddObjectClassesDialog(self._db_editor, self._db_mngr, self._db_map)
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(header, ['object_class name', 'description', 'display icon', 'databases'])
        indexes = [model.index(0, header.index(field)) for field in ('object_class name', 'databases')]
        values = ['fish', 'mock_db']
        model.batch_set_data(indexes, values)
        dialog.accept()
        self._commit_changes_to_database("Add object class.")
        data = self._db_mngr.query(self._db_map, "object_class_sq")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].name, "fish")

    def test_do_not_add_object_classes_with_invalid_db(self):
        """Test object classes aren't added when the database is not correct."""
        dialog = AddObjectClassesDialog(self._db_editor, self._db_mngr, self._db_map)
        self._db_editor.msg_error = mock.NonCallableMagicMock()
        self._db_editor.msg_error.attach_mock(mock.MagicMock(), "emit")
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(header, ['object_class name', 'description', 'display icon', 'databases'])
        indexes = [model.index(0, header.index(field)) for field in ('object_class name', 'databases')]
        values = ['fish', 'gibberish']
        model.batch_set_data(indexes, values)
        dialog.accept()
        self._db_editor.msg_error.emit.assert_called_with("Invalid database 'gibberish' at row 1")

    def _commit_changes_to_database(self, commit_message):
        with mock.patch.object(self._db_editor, "_get_commit_msg") as commit_msg:
            commit_msg.return_value = commit_message
            with signal_waiter(self._db_mngr.session_committed) as waiter:
                self._db_editor.ui.actionCommit.trigger()
                waiter.wait()


class TestManageRelationshipsDialog(TestBase):
    def setUp(self):
        self._common_setup("sqlite://", create=True)

    def tearDown(self):
        self._common_tear_down()

    def test_add_relationship_among_existing_ones(self):
        self._db_mngr.add_object_classes({self._db_map: [{"name": "Object_1", "id": 1}, {"name": "Object_2", "id": 2}]})
        self._db_mngr.add_objects(
            {
                self._db_map: [
                    {"class_id": 1, "name": "object_11"},
                    {"class_id": 1, "name": "object_12"},
                    {"class_id": 2, "name": "object_21"},
                ]
            }
        )
        self._db_mngr.add_relationship_classes(
            {self._db_map: [{"name": "rc", "id": 3, "object_class_id_list": [1, 2]}]}
        )
        self._db_mngr.add_relationships({self._db_map: [{"name": "r", "class_id": 3, "object_id_list": [1, 3]}]})
        root_index = self._db_editor.relationship_tree_model.index(0, 0)
        class_index = self._db_editor.relationship_tree_model.index(0, 0, root_index)
        self.assertEqual(class_index.data(), "rc")
        relationship_item = self._db_editor.relationship_tree_model.item_from_index(class_index)
        dialog = ManageRelationshipsDialog(self._db_editor, relationship_item, self._db_mngr, self._db_map)
        self.assertEqual(dialog.existing_items_model.rowCount(), 1)
        self.assertEqual(dialog.existing_items_model.columnCount(), 2)
        self.assertEqual(dialog.existing_items_model.index(0, 0).data(), "object_11")
        self.assertEqual(dialog.existing_items_model.index(0, 1).data(), "object_21")
        self.assertEqual(dialog.new_items_model.rowCount(), 0)
        for tree_widget in dialog.splitter_widgets():
            tree_widget.selectAll()
        dialog.add_relationships()
        self.assertEqual(dialog.new_items_model.rowCount(), 1)
        self.assertEqual(dialog.new_items_model.columnCount(), 2)
        self.assertEqual(dialog.new_items_model.index(0, 0).data(), "object_12")
        self.assertEqual(dialog.new_items_model.index(0, 1).data(), "object_21")

    def test_accept_relationship_removal(self):
        self._db_mngr.add_object_classes({self._db_map: [{"name": "Object_1", "id": 1}, {"name": "Object_2", "id": 2}]})
        self._db_mngr.add_objects(
            {
                self._db_map: [
                    {"class_id": 1, "name": "object_11"},
                    {"class_id": 1, "name": "object_12"},
                    {"class_id": 2, "name": "object_21"},
                ]
            }
        )
        self._db_mngr.add_relationship_classes(
            {self._db_map: [{"name": "rc", "id": 3, "object_class_id_list": [1, 2]}]}
        )
        self._db_mngr.add_relationships(
            {
                self._db_map: [
                    {"name": "r11", "class_id": 3, "object_id_list": [1, 3]},
                    {"name": "r21", "class_id": 3, "object_id_list": [2, 3]},
                ]
            }
        )
        root_index = self._db_editor.relationship_tree_model.index(0, 0)
        class_index = self._db_editor.relationship_tree_model.index(0, 0, root_index)
        self.assertEqual(class_index.data(), "rc")
        relationship_item = self._db_editor.relationship_tree_model.item_from_index(class_index)
        dialog = ManageRelationshipsDialog(self._db_editor, relationship_item, self._db_mngr, self._db_map)
        self.assertEqual(dialog.existing_items_model.rowCount(), 2)
        self.assertEqual(dialog.existing_items_model.columnCount(), 2)
        self.assertEqual(dialog.existing_items_model.index(0, 0).data(), "object_11")
        self.assertEqual(dialog.existing_items_model.index(0, 1).data(), "object_21")
        self.assertEqual(dialog.existing_items_model.index(1, 0).data(), "object_12")
        self.assertEqual(dialog.existing_items_model.index(1, 1).data(), "object_21")
        self.assertEqual(dialog.table_view.model().rowCount(), 2)
        self.assertEqual(dialog.table_view.model().columnCount(), 2)
        top_left = dialog.table_view.model().index(0, 0)
        bottom_right = dialog.table_view.model().index(0, 1)
        self.assertEqual(top_left.data(), "object_11")
        self.assertEqual(bottom_right.data(), "object_21")
        dialog.table_view.selectionModel().select(
            QItemSelection(top_left, bottom_right), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        dialog.remove_selected_rows()
        self.assertEqual(dialog.existing_items_model.rowCount(), 1)
        dialog.accept()
        relationships = self._db_mngr.get_items(self._db_map, "relationship")
        self.assertEqual(
            relationships,
            [
                {
                    'class_id': 3,
                    'commit_id': 2,
                    'id': 5,
                    'name': 'r21',
                    'object_class_id_list': (1, 2),
                    'object_id_list': (2, 3),
                }
            ],
        )


if __name__ == '__main__':
    unittest.main()
