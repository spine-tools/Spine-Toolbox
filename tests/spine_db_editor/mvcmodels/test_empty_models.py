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
import unittest
from unittest import mock
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QApplication
from spinedb_api import to_database
from spinetoolbox.mvcmodels.minimal_table_model import MinimalTableModel
from spinetoolbox.spine_db_editor.mvcmodels.empty_models import (
    DelayedDataSetter,
    EmptyModelBase,
    EmptyParameterDefinitionModel,
    EmptyParameterValueModel,
)
from tests.mock_helpers import (
    MockSpineDBManager,
    TestCaseWithQApplication,
    assert_table_model_data,
    fetch_model,
    q_object,
)


class TestEmptyModelBase(TestCaseWithQApplication):
    def setUp(self):
        """Overridden method. Runs before each test."""
        app_settings = mock.MagicMock()
        logger = mock.MagicMock()
        self._db_mngr = MockSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, "mock_db")
        self._undo_stack = QUndoStack()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()
        self._db_mngr.deleteLater()
        self._undo_stack.deleteLater()

    def test_undo_change_in_single_cell(self):
        model = EmptyModelBase(["entity_class_name", "header 2", "database"], self._db_mngr, parent=self._db_mngr)
        model.set_undo_stack(self._undo_stack)
        fetch_model(model)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 3)
        self.assertTrue(model.batch_set_data([model.index(0, 0)], ["X"]))
        expected = [["X", None, None], [None, None, None]]
        assert_table_model_data(model, expected, self)
        self.assertTrue(self._undo_stack.canUndo())
        self._undo_stack.undo()
        expected = [[None, None, None]]
        assert_table_model_data(model, expected, self)

    def test_undo_handles_entity_class_name_candidates(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Widget")
        model = EmptyModelBase(
            ["entity_class_name", "name", "description", "database"], self._db_mngr, parent=self._db_mngr
        )
        model.item_type = "entity"
        model.set_undo_stack(self._undo_stack)
        fetch_model(model)
        model.set_default_row(database="mock_db")
        model.set_rows_to_default(model.rowCount() - 1)
        self.assertEqual(model.columnCount(), 4)
        self.assertEqual(model.rowCount(), 1)
        with (
            mock.patch.object(model, "_convert_to_db") as convert_to_db,
            mock.patch.object(model, "_entity_class_name_candidates") as entity_class_name_candidates,
            mock.patch.object(model, "_check_item") as check_item,
        ):
            convert_to_db.side_effect = lambda item: item
            entity_class_name_candidates.return_value = ["Widget"]
            check_item.side_effect = lambda item: "entity_class_name" in item and "name" in item
            self.assertTrue(model.batch_set_data([model.index(0, 1)], ["gadget"]))
            expected = [["Widget", "gadget", None, "mock_db"], [None, None, None, "mock_db"]]
            assert_table_model_data(model, expected, self)
            self.assertTrue(self._undo_stack.canUndo())
            self._undo_stack.undo()
            expected = [[None, None, None, "mock_db"]]
            assert_table_model_data(model, expected, self)

    def test_remove_multiple_rows(self):
        model = EmptyModelBase(
            ["entity_class_name", "header 1", "header 2", "database"], self._db_mngr, parent=self._db_mngr
        )
        model.set_undo_stack(self._undo_stack)
        fetch_model(model)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 4)
        model.insertRow(0)
        model.insertRow(0)
        expected = [[None, None, None, None], [None, None, None, None], [None, None, None, None]]
        assert_table_model_data(model, expected, self)
        model.remove_rows([0, 1])
        expected = [[None, None, None, None]]
        assert_table_model_data(model, expected, self)

    def test_undo_remove_rows(self):
        model = EmptyModelBase(
            ["entity_class_name", "header 1", "header 2", "database"], self._db_mngr, parent=self._db_mngr
        )
        model.set_undo_stack(self._undo_stack)
        fetch_model(model)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 4)
        model.insertRow(0)
        self.assertTrue(model.batch_set_data([model.index(0, 1)], ["X"]))
        expected = [[None, "X", None, None], [None, None, None, None]]
        assert_table_model_data(model, expected, self)
        model.removeRows(0, 1)
        expected = [[None, None, None, None]]
        assert_table_model_data(model, expected, self)
        self.assertTrue(self._undo_stack.canUndo())
        self._undo_stack.undo()
        expected = [[None, "X", None, None], [None, None, None, None]]
        assert_table_model_data(model, expected, self)

    def test_undo_command_removed_when_row_goes_to_database(self):
        self._db_map.add_entity_class(name="Widget")
        model = EmptyModelBase(
            ["entity_class_name", "name", "description", "database"], self._db_mngr, parent=self._db_mngr
        )
        model.item_type = "entity"
        model.set_undo_stack(self._undo_stack)
        model._fetch_parent.fetch_item_type = model.item_type
        model.reset_db_maps([self._db_map])
        fetch_model(model)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 4)
        with (
            mock.patch.object(model, "_convert_to_db") as convert_to_db,
            mock.patch.object(model, "_entity_class_name_candidates") as entity_class_name_candidates,
            mock.patch.object(model, "_check_item") as check_item,
            mock.patch.object(model, "_make_unique_id") as make_unique_id,
        ):
            convert_to_db.side_effect = lambda item: item
            entity_class_name_candidates.return_value = ["Widget"]
            check_item.side_effect = lambda item: "entity_class_name" in item and "name" in item
            make_unique_id.side_effect = lambda item: (item["entity_class_name"], item["name"])
            self.assertTrue(
                model.batch_set_data(
                    [model.index(0, 0), model.index(0, 1), model.index(0, 2), model.index(0, 3)],
                    ["Widget", "gadget", "A new friend for other widgets.", "mock_db"],
                )
            )
            while model.rowCount() != 1:
                QApplication.processEvents()
        new_entity = self._db_map.entity(entity_class_name="Widget", name="gadget")
        self.assertEqual(new_entity["description"], "A new friend for other widgets.")
        expected = [[None, None, None, None]]
        assert_table_model_data(model, expected, self)
        self.assertFalse(self._undo_stack.canUndo())
        self.assertFalse(self._undo_stack.canRedo())

    def test_undo_multiple_row_insertions(self):
        self._db_map.add_entity_class(name="Widget")
        model = EmptyModelBase(
            ["entity_class_name", "name", "description", "database"], self._db_mngr, parent=self._db_mngr
        )
        model.item_type = "entity"
        model.set_undo_stack(self._undo_stack)
        model._fetch_parent.fetch_item_type = model.item_type
        model.reset_db_maps([self._db_map])
        fetch_model(model)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 4)
        model.insertRows(model.rowCount(), 1)
        self.assertEqual(model.rowCount(), 2)
        model.insertRows(model.rowCount(), 1)
        self.assertEqual(model.rowCount(), 3)
        self._undo_stack.undo()
        self.assertEqual(model.rowCount(), 2)
        self._undo_stack.undo()
        self.assertEqual(model.rowCount(), 1)
        expected = [[None, None, None, None]]
        assert_table_model_data(model, expected, self)

    def test_batch_setting_same_values_is_considered_a_no_operation(self):
        self._db_map.add_entity_class(name="Widget")
        model = EmptyModelBase(
            ["entity_class_name", "name", "description", "database"], self._db_mngr, parent=self._db_mngr
        )
        model.item_type = "entity"
        model.set_undo_stack(self._undo_stack)
        model._fetch_parent.fetch_item_type = model.item_type
        model.set_default_row(database="mock_db")
        model.reset_db_maps([self._db_map])
        fetch_model(model)
        with (
            mock.patch.object(model, "_convert_to_db") as convert_to_db,
            mock.patch.object(model, "_entity_class_name_candidates") as entity_class_name_candidates,
            mock.patch.object(model, "_check_item") as check_item,
            mock.patch.object(model, "_make_unique_id") as make_unique_id,
        ):
            convert_to_db.side_effect = lambda item: item
            entity_class_name_candidates.return_value = ["Widget"]
            check_item.side_effect = lambda item: "entity_class_name" in item and "name" in item
            make_unique_id.side_effect = lambda item: (item["entity_class_name"], item["name"])
            self.assertTrue(model.batch_set_data([model.index(0, 1)], ["gadget"]))
        self.assertEqual(self._undo_stack.count(), 1)
        expected = [["Widget", "gadget", None, "mock_db"], [None, None, None, "mock_db"]]
        assert_table_model_data(model, expected, self)
        with (
            mock.patch.object(model, "_convert_to_db") as convert_to_db,
            mock.patch.object(model, "_entity_class_name_candidates") as entity_class_name_candidates,
            mock.patch.object(model, "_check_item") as check_item,
            mock.patch.object(model, "_make_unique_id") as make_unique_id,
        ):
            convert_to_db.side_effect = lambda item: item
            entity_class_name_candidates.return_value = ["Widget"]
            check_item.side_effect = lambda item: "entity_class_name" in item and "name" in item
            make_unique_id.side_effect = lambda item: (item["entity_class_name"], item["name"])
            self.assertFalse(model.batch_set_data([model.index(0, 1)], ["gadget"]))
        self.assertEqual(self._undo_stack.count(), 1)

    def test_batch_setting_complete_rows_results_in_single_empty_row(self):
        self._db_map.add_entity_class(name="Widget")
        model = EmptyModelBase(
            ["entity_class_name", "name", "description", "database"], self._db_mngr, parent=self._db_mngr
        )
        model.item_type = "entity"
        model.set_undo_stack(self._undo_stack)
        model._fetch_parent.fetch_item_type = model.item_type
        model.set_default_row(database="mock_db")
        model.reset_db_maps([self._db_map])
        fetch_model(model)
        with (
            mock.patch.object(model, "_convert_to_db") as convert_to_db,
            mock.patch.object(model, "_entity_class_name_candidates") as entity_class_name_candidates,
            mock.patch.object(model, "_check_item") as check_item,
            mock.patch.object(model, "_make_unique_id") as make_unique_id,
        ):
            convert_to_db.side_effect = lambda item: item
            entity_class_name_candidates.return_value = ["Widget"]
            check_item.side_effect = lambda item: "entity_class_name" in item and "name" in item
            make_unique_id.side_effect = lambda item: (item["entity_class_name"], item["name"])
            self.assertTrue(model.insertRows(1, 1))
            self.assertTrue(
                model.batch_set_data(
                    [
                        model.index(0, 0),
                        model.index(0, 1),
                        model.index(0, 2),
                        model.index(1, 0),
                        model.index(1, 1),
                        model.index(1, 2),
                    ],
                    ["Widget", "gadget1", "First widget.", "Widget", "gadget2", "Second widget."],
                )
            )
            while model.rowCount() != 1:
                QApplication.processEvents()
        self.assertEqual(self._undo_stack.count(), 0)
        expected = [[None, None, None, "mock_db"]]
        assert_table_model_data(model, expected, self)


class TestDelayedDataSetter:
    def test_sets_data_for_model(self, application):
        with q_object(MinimalTableModel(header=["col 1"])) as model:
            model.insertRows(0, 1, QModelIndex())
            index = model.index(0, 0)
            data_setter = DelayedDataSetter(model, index)
            value_and_type = to_database(2.3)
            data_setter(value_and_type)
            assert model.index(0, 0).data() == 2.3

    def test_moves_set_row_if_previous_row_is_removed(self, application):
        with q_object(MinimalTableModel(header=["col 1"])) as model:
            model.insertRows(0, 2)
            index = model.index(1, 0)
            data_setter = DelayedDataSetter(model, index)
            model.removeRows(0, 1)
            value_and_type = to_database(2.3)
            data_setter(value_and_type)
            assert model.index(0, 0).data() == 2.3

    def test_gets_invalidated_when_row_is_removed(self, application):
        with q_object(MinimalTableModel(header=["col 1"])) as model:
            model.insertRows(0, 2)
            index = model.index(1, 0)
            data_setter = DelayedDataSetter(model, index)
            model.removeRows(1, 1)
            value_and_type = to_database(2.3)
            data_setter(value_and_type)
            assert model.index(0, 0).data() is None

    def test_removing_succeeding_row_has_no_effect(self, application):
        with q_object(MinimalTableModel(header=["col 1"])) as model:
            model.insertRows(0, 2)
            index = model.index(0, 0)
            data_setter = DelayedDataSetter(model, index)
            model.removeRows(1, 1)
            value_and_type = to_database(2.3)
            data_setter(value_and_type)
            assert model.index(0, 0).data() == 2.3

    def test_resetting_model_invalidates_setter(self):
        with q_object(MinimalTableModel(header=["col 1"])) as model:
            model.insertRows(0, 2)
            index = model.index(1, 0)
            data_setter = DelayedDataSetter(model, index)
            model.clear()
            value_and_type = to_database(2.3)
            data_setter(value_and_type)
            assert model.rowCount() == 0


class TestEmptyParameterDefinitionModel:
    def test_value_index_name_when_row_is_empty(self, db_mngr):
        with q_object(EmptyParameterDefinitionModel(db_mngr, parent=None)) as model:
            model.append_empty_row()
            index = model.index(0, model.columnCount() - 2)
            assert model.index_name(index) == "<database> - <entity_class_name> - <parameter_name>"

    def test_value_index_name_when_row_has_data(self, db_mngr):
        with q_object(EmptyParameterDefinitionModel(db_mngr, parent=None)) as model:
            undo_stack = QUndoStack(model)
            model.set_undo_stack(undo_stack)
            model.append_empty_row()
            indexes = [model.index(0, 0), model.index(0, 1), model.index(0, 6)]
            data = ["my class", "my parameter", "my database"]
            model.batch_set_data(indexes, data)
            index = model.index(0, model.columnCount() - 2)
            assert model.index_name(index) == "my database - my class - my parameter"


class TestEmptyParameterValueModel:
    def test_value_index_name_when_row_is_empty(self, db_mngr):
        with q_object(EmptyParameterValueModel(db_mngr, parent=None)) as model:
            model.append_empty_row()
            index = model.index(0, model.columnCount() - 2)
            assert (
                model.index_name(index)
                == "<database> - <entity_class_name> - <entity_byname> - <parameter_name> - <alternative_name>"
            )

    def test_value_index_name_when_row_has_data(self, db_mngr):
        with q_object(EmptyParameterValueModel(db_mngr, parent=None)) as model:
            undo_stack = QUndoStack(model)
            model.set_undo_stack(undo_stack)
            model.append_empty_row()
            indexes = [model.index(0, 0), model.index(0, 1), model.index(0, 2), model.index(0, 3), model.index(0, 5)]
            data = ["my class", "my entity", "my parameter", "my alternative", "my database"]
            model.batch_set_data(indexes, data)
            index = model.index(0, model.columnCount() - 2)
            assert model.index_name(index) == "my database - my class - my entity - my parameter - my alternative"


if __name__ == "__main__":
    unittest.main()
