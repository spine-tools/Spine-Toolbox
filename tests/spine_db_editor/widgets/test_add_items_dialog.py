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

"""Unit tests for ``add_items_dialog`` module."""
import unittest
from unittest import mock
from tempfile import TemporaryDirectory
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import AddEntityClassesDialog, ManageElementsDialog
from tests.spine_db_editor.helpers import TestBase


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
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._db_editor = None
        self._temp_dir.cleanup()

    def test_add_entity_classes(self):
        """Test entity classes are added through the manager when accepting the dialog."""
        dialog = AddEntityClassesDialog(
            self._db_editor, self._db_editor.entity_tree_model.root_item, self._db_mngr, self._db_map
        )
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(header, ["entity class name", "description", "display icon", "active by default", "databases"])
        indexes = [model.index(0, header.index(field)) for field in ("entity class name", "databases")]
        values = ["fish", "mock_db"]
        model.batch_set_data(indexes, values)
        dialog.accept()
        self._commit_changes_to_database("Add object class.")
        data = self._db_map.query(self._db_map.object_class_sq).all()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].name, "fish")

    def test_do_not_add_entity_classes_with_invalid_db(self):
        """Test entity classes aren't added when the database is not correct."""
        dialog = AddEntityClassesDialog(
            self._db_editor, self._db_editor.entity_tree_model.root_item, self._db_mngr, self._db_map
        )
        self._db_editor.msg_error = mock.NonCallableMagicMock()
        self._db_editor.msg_error.attach_mock(mock.MagicMock(), "emit")
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(header, ["entity class name", "description", "display icon", "active by default", "databases"])
        indexes = [model.index(0, header.index(field)) for field in ("entity class name", "databases")]
        values = ["fish", "gibberish"]
        model.batch_set_data(indexes, values)
        dialog.accept()
        self._db_editor.msg_error.emit.assert_called_with("Invalid database gibberish at row 1")

    def test_pasting_data_to_active_by_default_column(self):
        dialog = AddEntityClassesDialog(
            self._db_editor, self._db_editor.entity_tree_model.root_item, self._db_mngr, self._db_map
        )
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(header, ["entity class name", "description", "display icon", "active by default", "databases"])
        active_by_default_column = header.index("active by default")
        index = model.index(0, active_by_default_column)
        self.assertFalse(index.data())
        dialog.table_view.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self._paste_to_table_view("true", dialog)
        self.assertTrue(model.index(0, active_by_default_column).data())
        self._paste_to_table_view("GIBBERISH", dialog)
        self.assertFalse(model.index(0, active_by_default_column).data())

    def test_pasting_data_to_display_icon_column(self):
        dialog = AddEntityClassesDialog(
            self._db_editor, self._db_editor.entity_tree_model.root_item, self._db_mngr, self._db_map
        )
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(header, ["entity class name", "description", "display icon", "active by default", "databases"])
        display_icon_column = header.index("display icon")
        index = model.index(0, display_icon_column)
        self.assertIsNone(index.data())
        dialog.table_view.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self._paste_to_table_view("23", dialog)
        self.assertEqual(model.index(0, display_icon_column).data(), 23)
        self._paste_to_table_view("GIBBERISH", dialog)
        self.assertIsNone(model.index(0, display_icon_column).data())

    @staticmethod
    def _paste_to_table_view(text, dialog):
        mock_clipboard = mock.MagicMock()
        mock_clipboard.text.return_value = text
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            clipboard.return_value = mock_clipboard
            dialog.table_view.paste()

    def _commit_changes_to_database(self, commit_message):
        with mock.patch.object(self._db_editor, "_get_commit_msg") as commit_msg:
            commit_msg.return_value = commit_message
            self._db_editor.ui.actionCommit.trigger()


class TestManageElementsDialog(TestBase):
    def test_add_relationship_among_existing_ones(self):
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "Object_1", "id": 1}, {"name": "Object_2", "id": 2}]})
        self._db_mngr.add_entities(
            {
                self._db_map: [
                    {"class_id": 1, "name": "object_11", "id": 1},
                    {"class_id": 1, "name": "object_12", "id": 2},
                    {"class_id": 2, "name": "object_21", "id": 3},
                ]
            }
        )
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "rc", "id": 3, "dimension_id_list": [1, 2]}]})
        self._db_mngr.add_entities({self._db_map: [{"name": "r", "class_id": 3, "element_id_list": [1, 3], "id": 4}]})
        root_index = self._db_editor.entity_tree_model.index(0, 0)
        class_index = self._db_editor.entity_tree_model.index(2, 0, root_index)
        self.assertEqual(class_index.data(), "rc")
        relationship_item = self._db_editor.entity_tree_model.item_from_index(class_index)
        dialog = ManageElementsDialog(self._db_editor, relationship_item, self._db_mngr, self._db_map)
        self.assertEqual(dialog.existing_items_model.rowCount(), 1)
        self.assertEqual(dialog.existing_items_model.columnCount(), 3)
        self.assertEqual(dialog.existing_items_model.index(0, 0).data(), "object_11")
        self.assertEqual(dialog.existing_items_model.index(0, 1).data(), "object_21")
        self.assertEqual(dialog.existing_items_model.index(0, 2).data(), "r")
        self.assertEqual(dialog.new_items_model.rowCount(), 0)
        for tree_widget in dialog.splitter_widgets():
            tree_widget.selectAll()
        dialog.add_entities()
        self.assertEqual(dialog.new_items_model.rowCount(), 1)
        self.assertEqual(dialog.new_items_model.columnCount(), 3)
        self.assertEqual(dialog.new_items_model.index(0, 0).data(), "object_12")
        self.assertEqual(dialog.new_items_model.index(0, 1).data(), "object_21")
        self.assertEqual(dialog.new_items_model.index(0, 2).data(), "object_12__object_21")

    def test_accept_relationship_removal(self):
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "Object_1", "id": 1}, {"name": "Object_2", "id": 2}]})
        self._db_mngr.add_entities(
            {
                self._db_map: [
                    {"class_id": 1, "name": "object_11", "id": 1},
                    {"class_id": 1, "name": "object_12", "id": 2},
                    {"class_id": 2, "name": "object_21", "id": 3},
                ]
            }
        )
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "rc", "id": 3, "dimension_id_list": [1, 2]}]})
        self._db_mngr.add_entities(
            {
                self._db_map: [
                    {"name": "r11", "class_id": 3, "element_id_list": [1, 3], "id": 4},
                    {"name": "r21", "class_id": 3, "element_id_list": [2, 3], "id": 5},
                ]
            }
        )
        root_index = self._db_editor.entity_tree_model.index(0, 0)
        class_index = self._db_editor.entity_tree_model.index(2, 0, root_index)
        self.assertEqual(class_index.data(), "rc")
        relationship_item = self._db_editor.entity_tree_model.item_from_index(class_index)
        dialog = ManageElementsDialog(self._db_editor, relationship_item, self._db_mngr, self._db_map)
        self.assertEqual(dialog.existing_items_model.rowCount(), 2)
        self.assertEqual(dialog.existing_items_model.columnCount(), 3)
        self.assertEqual(dialog.existing_items_model.index(0, 0).data(), "object_11")
        self.assertEqual(dialog.existing_items_model.index(0, 1).data(), "object_21")
        self.assertEqual(dialog.existing_items_model.index(1, 0).data(), "object_12")
        self.assertEqual(dialog.existing_items_model.index(1, 1).data(), "object_21")
        self.assertEqual(dialog.table_view.model().rowCount(), 2)
        self.assertEqual(dialog.table_view.model().columnCount(), 3)
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
        relationships = [x.resolve() for x in self._db_mngr.get_items(self._db_map, "entity") if x["element_id_list"]]
        self.assertEqual(
            relationships,
            [{"class_id": 3, "description": None, "id": 5, "name": "r21", "element_id_list": (2, 3)}],
        )


if __name__ == "__main__":
    unittest.main()
