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
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import (
    AddEntitiesDialog,
    AddEntityClassesDialog,
    ManageElementsDialog,
)
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.spine_db_manager import SpineDBManager
from tests.mock_helpers import TestCaseWithQApplication, mock_clipboard_patch
from tests.spine_db_editor.helpers import TestBase


class TestAddItemsDialog(TestCaseWithQApplication):
    def setUp(self):
        """Overridden method. Runs before each test. Makes instance of SpineDBEditor class."""
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = SpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._temp_dir = TemporaryDirectory()
            url = "sqlite:///" + self._temp_dir.name + "/db.sqlite"
            self._db_map = self._db_mngr.get_db_map(url, logger, create=True)
            self._db_mngr.name_registry.register(url, "mock_db")
            self._db_editor = SpineDBEditor(self._db_mngr, {url: "mock_db"})

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        with (
            mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"),
            mock.patch("spinetoolbox.spine_db_manager.QMessageBox"),
        ):
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
        with self._db_map:
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
        self.assertTrue(index.data())
        dialog.table_view.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        self._paste_to_table_view("false", dialog)
        self.assertFalse(model.index(0, active_by_default_column).data())
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

    def test_composite_name_functionality(self):
        """Test that the entity class name column fills automatically and correctly for ND entity classes."""
        dialog = AddEntityClassesDialog(
            self._db_editor, self._db_editor.entity_tree_model.root_item, self._db_mngr, self._db_map
        )
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        dialog._handle_spin_box_value_changed(1)
        dialog._handle_spin_box_value_changed(2)
        self.assertEqual(
            header,
            [
                "dimension name (1)",
                "dimension name (2)",
                "entity class name",
                "description",
                "display icon",
                "active by default",
                "databases",
            ],
        )
        indexes = [
            model.index(0, header.index(field))
            for field in ("dimension name (1)", "dimension name (2)", "entity class name", "databases")
        ]
        values = ["Start", None, None, "mock_db"]
        model.batch_set_data(indexes, values)
        expected = ["Start", None, "Start__", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        value = "class_name"
        model.setData(indexes[2], value)
        expected = ["Start", None, "class_name", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        value = "End"
        model.setData(indexes[1], value)
        expected = ["Start", "End", "class_name", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        values = [None, None]
        model.batch_set_data(indexes[1:3], values)
        expected = ["Start", None, "Start__", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        dialog._handle_spin_box_value_changed(1)
        indexes = [
            model.index(0, header.index(field)) for field in ("dimension name (1)", "entity class name", "databases")
        ]
        value = "one"
        model.setData(indexes[1], value)
        expected = ["Start", "one", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        value = ["not valid"]
        model.batch_set_data([model.index(-1, -1)], value)
        expected = ["Start", "one", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        value = []
        model.batch_set_data(indexes[1], value)
        expected = ["Start", "one", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        value = ""
        model.setData(indexes[1], value)
        expected = ["Start", "Start__", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)

    def test_add_entities_dialog_autofill(self):
        """Test that the autofill also works for the add entities dialog."""
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "first_class"}, {"name": "second_class"}]})
        self._db_mngr.add_items(
            "entity_class",
            {self._db_map: [{"name": "entity_class", "dimension_name_list": ["first_class", "second_class"]}]},
        )
        self._db_mngr.add_items(
            "entity",
            {
                self._db_map: [
                    {"entity_class_name": "first_class", "name": "entity_1"},
                    {"entity_class_name": "second_class", "name": "entity_2"},
                ]
            },
        )
        for item in self._db_editor.entity_tree_model.visit_all():
            while item.can_fetch_more():
                item.fetch_more()
                qApp.processEvents()  # pylint: disable=undefined-variable
        entity_classes = self._db_editor.entity_tree_model.root_item.children
        dialog = AddEntitiesDialog(self._db_editor, entity_classes[2], self._db_mngr, self._db_map)
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(
            header,
            ("first_class", "second_class", "entity name", "alternative", "entity group", "databases"),
        )
        indexes = [model.index(0, header.index(field)) for field in ("first_class", "second_class", "entity name")]
        values = ["entity_1"]
        model.batch_set_data([indexes[0]], values)
        expected = ["entity_1", None, "entity_1__", "", None, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        value = "entity_name"
        model.setData(indexes[2], value)
        expected = ["entity_1", None, "entity_name", "", None, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        value = "End"
        model.setData(indexes[1], value)
        expected = ["entity_1", "End", "entity_name", "", None, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)
        values = [None, None]
        model.batch_set_data(indexes[1:3], values)
        expected = ["entity_1", None, "entity_1__", "", None, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        self.assertEqual(expected, result)

    def _paste_to_table_view(self, text, dialog):
        with mock_clipboard_patch(text, "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertTrue(dialog.table_view.paste())

    def _commit_changes_to_database(self, commit_message):
        with mock.patch.object(self._db_editor, "_get_commit_msg") as commit_msg:
            commit_msg.return_value = commit_message
            self._db_editor.ui.actionCommit.trigger()


class TestManageElementsDialog(TestBase):
    def test_add_relationship_among_existing_ones(self):
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "Object_1"}, {"name": "Object_2"}]})
        self._db_mngr.add_items(
            "entity",
            {
                self._db_map: [
                    {"entity_class_name": "Object_1", "name": "object_11"},
                    {"entity_class_name": "Object_1", "name": "object_12"},
                    {"entity_class_name": "Object_2", "name": "object_21"},
                ]
            },
        )
        self._db_mngr.add_items(
            "entity_class", {self._db_map: [{"name": "rc", "dimension_name_list": ["Object_1", "Object_2"]}]}
        )
        self._db_mngr.add_items(
            "entity",
            {self._db_map: [{"name": "r", "entity_class_name": "rc", "element_name_list": ["object_11", "object_21"]}]},
        )
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
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "Object_1"}, {"name": "Object_2"}]})
        self._db_mngr.add_items(
            "entity",
            {
                self._db_map: [
                    {"entity_class_name": "Object_1", "name": "object_11"},
                    {"entity_class_name": "Object_1", "name": "object_12"},
                    {"entity_class_name": "Object_2", "name": "object_21"},
                ]
            },
        )
        self._db_mngr.add_items(
            "entity_class", {self._db_map: [{"name": "rc", "dimension_name_list": ["Object_1", "Object_2"]}]}
        )
        self._db_mngr.add_items(
            "entity",
            {
                self._db_map: [
                    {"name": "r11", "entity_class_name": "rc", "element_name_list": ["object_11", "object_21"]},
                    {"name": "r21", "entity_class_name": "rc", "element_name_list": ["object_12", "object_21"]},
                ]
            },
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
        relationships = [x.resolve() for x in self._db_map.get_items("entity") if x["element_id_list"]]
        self.assertEqual(
            relationships,
            [
                {
                    "class_id": None,
                    "description": None,
                    "id": None,
                    "name": "r21",
                    "element_id_list": (None, None),
                    "lat": None,
                    "lon": None,
                    "alt": None,
                    "shape_name": None,
                    "shape_blob": None,
                }
            ],
        )


class TestAddEntitiesDialog(TestBase):
    def test_default_alternative_skips_add_alternatives_row(self):
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "Object_1", "active_by_default": False}]})
        alternative_model = self._db_editor.ui.alternative_tree_view.model()
        alternative_tree_root = alternative_model.index(0, 0)
        add_alternative_index = alternative_model.index(1, 0, alternative_tree_root)
        self.assertEqual(add_alternative_index.data(), "Type new alternative name here...")
        alternative_selection_model = self._db_editor.ui.alternative_tree_view.selectionModel()
        alternative_selection_model.setCurrentIndex(
            add_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        root_index = self._db_editor.entity_tree_model.index(0, 0)
        class_index = self._db_editor.entity_tree_model.index(0, 0, root_index)
        self.assertEqual(class_index.data(), "Object_1")
        class_item = self._db_editor.entity_tree_model.item_from_index(class_index)
        dialog = AddEntitiesDialog(self._db_editor, class_item, self._db_mngr, self._db_map)
        model = dialog.model
        model.fetchMore(QModelIndex())
        self.assertEqual(model.columnCount(), 4)
        self.assertEqual(model.headerData(0), "entity name")
        self.assertEqual(model.headerData(1), "alternative")
        self.assertEqual(model.headerData(2), "entity group")
        self.assertEqual(model.headerData(3), "databases")
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(), None)
        self.assertEqual(model.index(0, 1).data(), "Base")
        self.assertEqual(model.index(0, 2).data(), None)
        self.assertEqual(model.index(0, 3).data(), self.db_codename)

    def test_default_alternative_is_empty_if_class_is_active_by_default(self):
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "Object_1"}]})
        alternative_model = self._db_editor.ui.alternative_tree_view.model()
        alternative_tree_root = alternative_model.index(0, 0)
        add_alternative_index = alternative_model.index(1, 0, alternative_tree_root)
        self.assertEqual(add_alternative_index.data(), "Type new alternative name here...")
        alternative_selection_model = self._db_editor.ui.alternative_tree_view.selectionModel()
        alternative_selection_model.setCurrentIndex(
            add_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        root_index = self._db_editor.entity_tree_model.index(0, 0)
        class_index = self._db_editor.entity_tree_model.index(0, 0, root_index)
        self.assertEqual(class_index.data(), "Object_1")
        class_item = self._db_editor.entity_tree_model.item_from_index(class_index)
        dialog = AddEntitiesDialog(self._db_editor, class_item, self._db_mngr, self._db_map)
        model = dialog.model
        model.fetchMore(QModelIndex())
        self.assertEqual(model.columnCount(), 4)
        self.assertEqual(model.headerData(0), "entity name")
        self.assertEqual(model.headerData(1), "alternative")
        self.assertEqual(model.headerData(2), "entity group")
        self.assertEqual(model.headerData(3), "databases")
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(), None)
        self.assertEqual(model.index(0, 1).data(), "")
        self.assertEqual(model.index(0, 2).data(), None)
        self.assertEqual(model.index(0, 3).data(), self.db_codename)


if __name__ == "__main__":
    unittest.main()
