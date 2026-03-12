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
from unittest import mock
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex
from PySide6.QtWidgets import QApplication
import pytest
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import (
    AddEntitiesDialog,
    AddEntityClassesDialog,
    ManageElementsDialog,
)
from tests.mock_helpers import assert_table_model_data, assert_table_model_data_pytest, mock_clipboard_patch
from tests.spine_db_editor.helpers import TestBase, commit_changes_to_database


@pytest.fixture()
def add_items_dialog(db_map, db_mngr, db_editor):
    dialog = AddEntityClassesDialog(db_editor, db_editor.entity_tree_model.root_item, db_mngr, db_map)
    yield dialog


class TestAddItemsDialog:
    def test_add_entity_classes(self, add_items_dialog, db_map, db_name, db_editor):
        """Test entity classes are added through the manager when accepting the dialog."""
        model = add_items_dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        assert header == ["entity class name", "description", "display icon", "active by default", "databases"]
        indexes = [model.index(0, header.index(field)) for field in ("entity class name", "databases")]
        values = ["fish", db_name]
        model.batch_set_data(indexes, values)
        add_items_dialog.accept()
        commit_changes_to_database("Add object class.", db_editor)
        with db_map:
            data = db_map.query(db_map.object_class_sq).all()
        assert len(data) == 1
        assert data[0].name == "fish"

    def test_do_not_add_entity_classes_with_invalid_db(self, add_items_dialog, db_editor):
        """Test entity classes aren't added when the database is not correct."""
        db_editor.msg_error = mock.NonCallableMagicMock()
        db_editor.msg_error.attach_mock(mock.MagicMock(), "emit")
        model = add_items_dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        assert header == ["entity class name", "description", "display icon", "active by default", "databases"]
        indexes = [model.index(0, header.index(field)) for field in ("entity class name", "databases")]
        values = ["fish", "gibberish"]
        model.batch_set_data(indexes, values)
        add_items_dialog.accept()
        db_editor.msg_error.emit.assert_called_with("Invalid database gibberish at row 1")

    def test_pasting_data_to_active_by_default_column(self, add_items_dialog):
        model = add_items_dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        assert header == ["entity class name", "description", "display icon", "active by default", "databases"]
        active_by_default_column = header.index("active by default")
        index = model.index(0, active_by_default_column)
        assert index.data()
        add_items_dialog.table_view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        self._paste_to_table_view("false", add_items_dialog)
        assert not model.index(0, active_by_default_column).data()
        self._paste_to_table_view("GIBBERISH", add_items_dialog)
        assert not model.index(0, active_by_default_column).data()

    def test_pasting_data_to_display_icon_column(self, add_items_dialog):
        model = add_items_dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        assert header == ["entity class name", "description", "display icon", "active by default", "databases"]
        display_icon_column = header.index("display icon")
        index = model.index(0, display_icon_column)
        assert index.data() is None
        add_items_dialog.table_view.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        self._paste_to_table_view("23", add_items_dialog)
        assert model.index(0, display_icon_column).data() == 23
        self._paste_to_table_view("GIBBERISH", add_items_dialog)
        assert model.index(0, display_icon_column).data() is None

    def test_composite_name_functionality(self, add_items_dialog):
        """Test that the entity class name column fills automatically and correctly for ND entity classes."""
        model = add_items_dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        add_items_dialog._handle_spin_box_value_changed(1)
        add_items_dialog._handle_spin_box_value_changed(2)
        assert header == [
            "dimension name (1)",
            "dimension name (2)",
            "entity class name",
            "description",
            "display icon",
            "active by default",
            "databases",
        ]
        indexes = [
            model.index(0, header.index(field))
            for field in ("dimension name (1)", "dimension name (2)", "entity class name", "databases")
        ]
        values = ["Start", None, None, "mock_db"]
        model.batch_set_data(indexes, values)
        expected = ["Start", None, "Start__", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        value = "class_name"
        model.setData(indexes[2], value)
        expected = ["Start", None, "class_name", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        value = "End"
        model.setData(indexes[1], value)
        expected = ["Start", "End", "class_name", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        values = [None, None]
        model.batch_set_data(indexes[1:3], values)
        expected = ["Start", None, "Start__", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        add_items_dialog._handle_spin_box_value_changed(1)
        indexes = [
            model.index(0, header.index(field)) for field in ("dimension name (1)", "entity class name", "databases")
        ]
        value = "one"
        model.setData(indexes[1], value)
        expected = ["Start", "one", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        value = ["not valid"]
        model.batch_set_data([model.index(-1, -1)], value)
        expected = ["Start", "one", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        value = []
        model.batch_set_data(indexes[1], value)
        expected = ["Start", "one", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        value = ""
        model.setData(indexes[1], value)
        expected = ["Start", "Start__", None, None, True, "mock_db"]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result

    def _paste_to_table_view(self, text, dialog):
        with mock_clipboard_patch(text, "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            assert dialog.table_view.paste()


class TestManageElementsDialog:
    def test_add_relationship_among_existing_ones(self, db_map, db_mngr, db_editor):
        db_mngr.add_items("entity_class", {db_map: [{"name": "Object_1"}, {"name": "Object_2"}]})
        db_mngr.add_items(
            "entity",
            {
                db_map: [
                    {"entity_class_name": "Object_1", "name": "object_11"},
                    {"entity_class_name": "Object_1", "name": "object_12"},
                    {"entity_class_name": "Object_2", "name": "object_21"},
                ]
            },
        )
        db_mngr.add_items("entity_class", {db_map: [{"name": "rc", "dimension_name_list": ["Object_1", "Object_2"]}]})
        db_mngr.add_items(
            "entity",
            {db_map: [{"name": "r", "entity_class_name": "rc", "element_name_list": ["object_11", "object_21"]}]},
        )
        root_index = db_editor.entity_tree_model.index(0, 0)
        class_index = db_editor.entity_tree_model.index(2, 0, root_index)
        assert class_index.data() == "rc"
        relationship_item = db_editor.entity_tree_model.item_from_index(class_index)
        dialog = ManageElementsDialog(db_editor, relationship_item, db_mngr, db_map)
        assert dialog.existing_items_model.rowCount() == 1
        assert dialog.existing_items_model.columnCount() == 3
        assert dialog.existing_items_model.index(0, 0).data() == "object_11"
        assert dialog.existing_items_model.index(0, 1).data() == "object_21"
        assert dialog.existing_items_model.index(0, 2).data() == "r"
        assert dialog.new_items_model.rowCount() == 0
        for tree_widget in dialog.splitter_widgets():
            tree_widget.selectAll()
        dialog.add_entities()
        assert dialog.new_items_model.rowCount() == 1
        assert dialog.new_items_model.columnCount() == 3
        assert dialog.new_items_model.index(0, 0).data() == "object_12"
        assert dialog.new_items_model.index(0, 1).data() == "object_21"
        assert dialog.new_items_model.index(0, 2).data() == "object_12__object_21"

    def test_accept_relationship_removal(self, db_map, db_mngr, db_editor):
        db_mngr.add_items("entity_class", {db_map: [{"name": "Object_1"}, {"name": "Object_2"}]})
        db_mngr.add_items(
            "entity",
            {
                db_map: [
                    {"entity_class_name": "Object_1", "name": "object_11"},
                    {"entity_class_name": "Object_1", "name": "object_12"},
                    {"entity_class_name": "Object_2", "name": "object_21"},
                ]
            },
        )
        db_mngr.add_items("entity_class", {db_map: [{"name": "rc", "dimension_name_list": ["Object_1", "Object_2"]}]})
        db_mngr.add_items(
            "entity",
            {
                db_map: [
                    {"name": "r11", "entity_class_name": "rc", "element_name_list": ["object_11", "object_21"]},
                    {"name": "r21", "entity_class_name": "rc", "element_name_list": ["object_12", "object_21"]},
                ]
            },
        )
        root_index = db_editor.entity_tree_model.index(0, 0)
        class_index = db_editor.entity_tree_model.index(2, 0, root_index)
        assert class_index.data(), "rc"
        relationship_item = db_editor.entity_tree_model.item_from_index(class_index)
        dialog = ManageElementsDialog(db_editor, relationship_item, db_mngr, db_map)
        assert dialog.existing_items_model.rowCount() == 2
        assert dialog.existing_items_model.columnCount() == 3
        assert dialog.existing_items_model.index(0, 0).data() == "object_11"
        assert dialog.existing_items_model.index(0, 1).data() == "object_21"
        assert dialog.existing_items_model.index(1, 0).data() == "object_12"
        assert dialog.existing_items_model.index(1, 1).data() == "object_21"
        assert dialog.table_view.model().rowCount() == 2
        assert dialog.table_view.model().columnCount() == 3
        top_left = dialog.table_view.model().index(0, 0)
        bottom_right = dialog.table_view.model().index(0, 1)
        assert top_left.data() == "object_11"
        assert bottom_right.data() == "object_21"
        dialog.table_view.selectionModel().select(
            QItemSelection(top_left, bottom_right), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        dialog.remove_selected_rows()
        assert dialog.existing_items_model.rowCount() == 1
        dialog.accept()
        relationships = [x.resolve() for x in db_map.get_items("entity") if x["element_id_list"]]
        assert relationships == [
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
        ]


class TestAddEntitiesDialog:
    def test_default_alternative_skips_add_alternatives_row(self, db_map, db_name, db_mngr, db_editor):
        db_mngr.add_items("entity_class", {db_map: [{"name": "Object_1", "active_by_default": False}]})
        alternative_model = db_editor.ui.alternative_tree_view.model()
        alternative_tree_root = alternative_model.index(0, 0)
        add_alternative_index = alternative_model.index(1, 0, alternative_tree_root)
        assert add_alternative_index.data() == "Type new alternative name here..."
        alternative_selection_model = db_editor.ui.alternative_tree_view.selectionModel()
        alternative_selection_model.setCurrentIndex(
            add_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        root_index = db_editor.entity_tree_model.index(0, 0)
        class_index = db_editor.entity_tree_model.index(0, 0, root_index)
        assert class_index.data() == "Object_1"
        class_item = db_editor.entity_tree_model.item_from_index(class_index)
        dialog = AddEntitiesDialog(db_editor, class_item, db_mngr, db_map)
        model = dialog.model
        model.fetchMore(QModelIndex())
        assert model.columnCount() == 4
        assert model.headerData(0) == "entity name"
        assert model.headerData(1) == "alternative"
        assert model.headerData(2) == "entity group"
        assert model.headerData(3) == "databases"
        assert model.rowCount() == 1
        assert model.index(0, 0).data() is None
        assert model.index(0, 1).data() == "Base"
        assert model.index(0, 2).data() is None
        assert model.index(0, 3).data() == db_name

    def test_default_alternative_is_empty_if_class_is_active_by_default(self, db_map, db_name, db_mngr, db_editor):
        db_mngr.add_items("entity_class", {db_map: [{"name": "Object_1"}]})
        alternative_model = db_editor.ui.alternative_tree_view.model()
        alternative_tree_root = alternative_model.index(0, 0)
        add_alternative_index = alternative_model.index(1, 0, alternative_tree_root)
        assert add_alternative_index.data() == "Type new alternative name here..."
        alternative_selection_model = db_editor.ui.alternative_tree_view.selectionModel()
        alternative_selection_model.setCurrentIndex(
            add_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        root_index = db_editor.entity_tree_model.index(0, 0)
        class_index = db_editor.entity_tree_model.index(0, 0, root_index)
        assert class_index.data() == "Object_1"
        class_item = db_editor.entity_tree_model.item_from_index(class_index)
        dialog = AddEntitiesDialog(db_editor, class_item, db_mngr, db_map)
        model = dialog.model
        model.fetchMore(QModelIndex())
        assert model.columnCount(), 4
        assert model.headerData(0) == "entity name"
        assert model.headerData(1) == "alternative"
        assert model.headerData(2) == "entity group"
        assert model.headerData(3) == "databases"
        assert model.rowCount() == 1
        assert model.index(0, 0).data() is None
        assert model.index(0, 1).data() == ""
        assert model.index(0, 2).data() is None
        assert model.index(0, 3).data() == db_name

    def test_select_entity_class_with_combo_box_when_no_entity_is_selected_in_entity_tree(
        self, db_map, db_name, db_mngr, db_editor
    ):
        db_mngr.add_items("entity_class", {db_map: [{"name": "Object_1", "active_by_default": False}]})
        root_index = db_editor.entity_tree_model.index(0, 0)
        root_item = db_editor.entity_tree_model.item_from_index(root_index)
        dialog = AddEntitiesDialog(db_editor, root_item, db_mngr, db_map)
        model = dialog.model
        dialog.ent_cls_combo_box.setCurrentText("Object_1")
        model.fetchMore(QModelIndex())
        assert model.columnCount() == 4
        assert model.headerData(0) == "entity name"
        assert model.headerData(1) == "alternative"
        assert model.headerData(2) == "entity group"
        assert model.headerData(3) == "databases"
        assert model.rowCount() == 1
        assert model.index(0, 0).data() is None
        assert model.index(0, 1).data() == "Base"
        assert model.index(0, 2).data() is None
        assert model.index(0, 3).data() == db_name

    def test_get_db_map_data_when_dialog_is_empty(self, db_map, db_mngr, db_editor):
        db_mngr.add_items("entity_class", {db_map: [{"name": "Object_1", "active_by_default": False}]})
        root_index = db_editor.entity_tree_model.index(0, 0)
        root_item = db_editor.entity_tree_model.item_from_index(root_index)
        dialog = AddEntitiesDialog(db_editor, root_item, db_mngr, db_map)
        assert dialog.get_db_map_data() == {}

    def test_entity_name_is_constructed_correctly_for_relationships_of_relationships(
        self, db_map, db_name, db_mngr, db_editor
    ):
        db_mngr.add_items(
            "entity_class",
            {
                db_map: [
                    {"name": "A"},
                    {"name": "B"},
                    {"dimension_name_list": ["A", "B"]},
                    {"dimension_name_list": ["A__B", "B"]},
                ]
            },
        )
        db_mngr.add_items(
            "entity",
            {
                db_map: [
                    {"entity_class_name": "A", "name": "a"},
                    {"entity_class_name": "B", "name": "b"},
                    {"entity_class_name": "A__B", "entity_byname": ("a", "b")},
                    {"entity_class_name": "A__B__B", "entity_byname": ("a", "b", "b")},
                ]
            },
        )
        root_index = db_editor.entity_tree_model.index(0, 0)
        relationship_class_index = db_editor.entity_tree_model.index(3, 0, root_index)
        assert relationship_class_index.data() == "A__B__B"
        relationship_class_item = db_editor.entity_tree_model.item_from_index(relationship_class_index)
        dialog = AddEntitiesDialog(db_editor, relationship_class_item, db_mngr, db_map)
        model = dialog.model
        model.fetchMore(QModelIndex())
        assert model.columnCount() == 6
        assert model.headerData(0) == "A__B"
        assert model.headerData(1) == "B"
        assert model.headerData(2) == "entity name"
        assert model.headerData(3) == "alternative"
        assert model.headerData(4) == "entity group"
        assert model.headerData(5) == "databases"
        expected = [[None, None, None, "", None, db_name]]
        assert_table_model_data_pytest(model, expected)
        a_b = DB_ITEM_SEPARATOR.join(("a", "b"))
        model_index = model.index(0, 0)
        model.setData(model_index, a_b)
        expected = [[a_b, None, "a__b", "", None, db_name], [None, None, None, "", None, db_name]]
        assert_table_model_data_pytest(model, expected)
        model_index = model.index(0, 1)
        model.setData(model_index, "b")
        expected = [[a_b, "b", "a__b__b", "", None, db_name], [None, None, None, "", None, db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_entity_name_is_constructed_correctly_for_relationships_of_relationships_with_batch_set_data(
        self, db_map, db_name, db_mngr, db_editor
    ):
        db_mngr.add_items(
            "entity_class",
            {
                db_map: [
                    {"name": "A"},
                    {"name": "B"},
                    {"dimension_name_list": ["A", "B"]},
                    {"dimension_name_list": ["A__B", "B"]},
                ]
            },
        )
        db_mngr.add_items(
            "entity",
            {
                db_map: [
                    {"entity_class_name": "A", "name": "a"},
                    {"entity_class_name": "B", "name": "b"},
                    {"entity_class_name": "A__B", "entity_byname": ("a", "b")},
                    {"entity_class_name": "A__B__B", "entity_byname": ("a", "b", "b")},
                ]
            },
        )
        root_index = db_editor.entity_tree_model.index(0, 0)
        relationship_class_index = db_editor.entity_tree_model.index(3, 0, root_index)
        assert relationship_class_index.data() == "A__B__B"
        relationship_class_item = db_editor.entity_tree_model.item_from_index(relationship_class_index)
        dialog = AddEntitiesDialog(db_editor, relationship_class_item, db_mngr, db_map)
        model = dialog.model
        model.fetchMore(QModelIndex())
        assert model.columnCount() == 6
        assert model.headerData(0) == "A__B"
        assert model.headerData(1) == "B"
        assert model.headerData(2) == "entity name"
        assert model.headerData(3) == "alternative"
        assert model.headerData(4) == "entity group"
        assert model.headerData(5) == "databases"
        expected = [[None, None, None, "", None, db_name]]
        assert_table_model_data_pytest(model, expected)
        a_b = DB_ITEM_SEPARATOR.join(("a", "b"))
        model_index_1 = model.index(0, 0)
        model_index_2 = model.index(0, 1)
        model.batch_set_data([model_index_1, model_index_2], [a_b, "b"])
        expected = [[a_b, "b", "a__b__b", "", None, db_name], [None, None, None, "", None, db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_add_entities_dialog_autofill(self, db_map, db_name, db_mngr, db_editor):
        """Test that the autofill also works for the add entities dialog."""
        db_mngr.add_items("entity_class", {db_map: [{"name": "first_class"}, {"name": "second_class"}]})
        db_mngr.add_items(
            "entity_class",
            {db_map: [{"name": "entity_class", "dimension_name_list": ["first_class", "second_class"]}]},
        )
        db_mngr.add_items(
            "entity",
            {
                db_map: [
                    {"entity_class_name": "first_class", "name": "entity_1"},
                    {"entity_class_name": "second_class", "name": "entity_2"},
                ]
            },
        )
        for item in db_editor.entity_tree_model.visit_all():
            while item.can_fetch_more():
                item.fetch_more()
                QApplication.processEvents()  # pylint: disable=undefined-variable
        entity_classes = db_editor.entity_tree_model.root_item.children
        dialog = AddEntitiesDialog(db_editor, entity_classes[2], db_mngr, db_map)
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        assert header == ("first_class", "second_class", "entity name", "alternative", "entity group", "databases")
        indexes = [model.index(0, header.index(field)) for field in ("first_class", "second_class", "entity name")]
        values = ["entity_1"]
        model.batch_set_data([indexes[0]], values)
        expected = ["entity_1", None, "entity_1__", "", None, db_name]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        value = "entity_name"
        model.setData(indexes[2], value)
        expected = ["entity_1", None, "entity_name", "", None, db_name]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        value = "End"
        model.setData(indexes[1], value)
        expected = ["entity_1", "End", "entity_name", "", None, db_name]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
        values = [None, None]
        model.batch_set_data(indexes[1:3], values)
        expected = ["entity_1", None, "entity_1__", "", None, db_name]
        result = [model.index(0, column).data() for column in range(model.columnCount())]
        assert expected == result
