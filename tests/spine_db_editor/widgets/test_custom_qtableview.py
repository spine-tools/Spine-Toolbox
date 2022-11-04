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

"""Unit tests for DB editor's custom ``QTableView`` classes."""
import unittest
from unittest import mock
from PySide2.QtCore import QItemSelectionModel, QModelIndex
from PySide2.QtWidgets import QApplication

from spinetoolbox.helpers import signal_waiter, ItemTypeFetchParent
from tests.spine_db_editor.widgets.helpers import add_object, add_object_class, TestBase, EditorDelegateMocking


class TestParameterTableView(TestBase):
    def setUp(self):
        self._common_setup("sqlite://", create=True)

    def tearDown(self):
        self._common_tear_down()

    def test_remove_last_empty_row(self):
        table_view = self._db_editor.ui.tableView_object_parameter_value
        model = table_view.model()
        index = model.index(0, 0)
        selection_model = table_view.selectionModel()
        selection_model.select(index, QItemSelectionModel.ClearAndSelect)
        table_view.remove_selected()
        self.assertFalse(selection_model.hasSelection())
        self.assertEqual(model.rowCount(), 1)

    def test_remove_rows_from_empty_model(self):
        tree_view = self._db_editor.ui.treeView_object
        add_object_class(tree_view, "an_object_class")
        add_object(tree_view, "an_object")
        table_view = self._db_editor.ui.tableView_object_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        index = model.index(0, 0)
        delegate_mock = EditorDelegateMocking()
        delegate_mock.write_to_index(table_view, index, "an_object_class")
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        self.assertEqual(model.index(0, 0).data(), "an_object_class")
        self.assertEqual(model.index(0, 1).data(), None)
        self.assertEqual(model.index(0, 2).data(), None)
        self.assertEqual(model.index(0, 3).data(), None)
        self.assertEqual(model.index(0, 4).data(), None)
        self.assertEqual(model.index(0, 5).data(), "database")
        self.assertEqual(model.index(1, 0).data(), None)
        self.assertEqual(model.index(1, 1).data(), None)
        self.assertEqual(model.index(1, 2).data(), None)
        self.assertEqual(model.index(1, 3).data(), None)
        self.assertEqual(model.index(1, 4).data(), None)
        self.assertEqual(model.index(1, 5).data(), "database")
        selection_model = table_view.selectionModel()
        selection_model.select(index, QItemSelectionModel.ClearAndSelect)
        table_view.remove_selected()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(), None)
        self.assertEqual(model.index(0, 1).data(), None)
        self.assertEqual(model.index(0, 2).data(), None)
        self.assertEqual(model.index(0, 3).data(), None)
        self.assertEqual(model.index(0, 4).data(), None)
        self.assertFalse(selection_model.hasSelection())

    def test_removing_row_does_not_allow_fetching_more_data(self):
        tree_view = self._db_editor.ui.treeView_object
        add_object_class(tree_view, "an_object_class")
        add_object(tree_view, "object_1")
        add_object(tree_view, "object_2")
        definition_table_view = self._db_editor.ui.tableView_object_parameter_definition
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 0), "an_object_class")
        delegate_mock.reset()
        with signal_waiter(self._db_mngr.parameter_definitions_added) as waiter:
            delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 1), "a_parameter")
            waiter.wait()
        table_view = self._db_editor.ui.tableView_object_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        _set_row_data(table_view, model, 0, ["an_object_class", "object_1", "a_parameter", "Base"], delegate_mock)
        delegate_mock.reset()
        with signal_waiter(self._db_mngr.parameter_values_added) as waiter:
            delegate_mock.write_to_index(table_view, model.index(0, 4), "value_1")
            waiter.wait()
        _set_row_data(table_view, model, 1, ["an_object_class", "object_2", "a_parameter", "Base"], delegate_mock)
        delegate_mock.reset()
        with signal_waiter(self._db_mngr.parameter_values_added) as waiter:
            delegate_mock.write_to_index(table_view, model.index(1, 4), "value_2")
            waiter.wait()
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 6)
        expected = [
            ["an_object_class", "object_1", "Base", "value_1", "database"],
            ["an_object_class", "object_2", "Base", "value_2", "database"],
            [None, None, None, None, None, "database"],
        ]
        for row, column in zip(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])
        selection_model = table_view.selectionModel()
        selection_model.select(model.index(0, 0), QItemSelectionModel.ClearAndSelect)
        with signal_waiter(self._db_mngr.parameter_values_removed) as waiter:
            table_view.remove_selected()
            waiter.wait()
        self.assertFalse(model.canFetchMore(QModelIndex()))
        expected = [
            ["an_object_class", "object_2", "Base", "value_2", "database"],
            [None, None, None, None, None, "database"],
        ]
        for row, column in zip(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_receiving_uncommitted_but_existing_value_does_not_create_duplicate_entry(self):
        tree_view = self._db_editor.ui.treeView_object
        add_object_class(tree_view, "an_object_class")
        add_object(tree_view, "an_object")
        definition_table_view = self._db_editor.ui.tableView_object_parameter_definition
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 0), "an_object_class")
        delegate_mock.reset()
        with signal_waiter(self._db_mngr.parameter_definitions_added) as waiter:
            delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 1), "a_parameter")
            waiter.wait()
        table_view = self._db_editor.ui.tableView_object_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        _set_row_data(table_view, model, 0, ["an_object_class", "an_object", "a_parameter", "Base"], delegate_mock)
        delegate_mock.reset()
        with signal_waiter(self._db_mngr.parameter_values_added) as waiter:
            delegate_mock.write_to_index(table_view, model.index(0, 4), "value_1")
            waiter.wait()
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        expected = [
            ["an_object_class", "an_object", "Base", "value_1", "database"],
            [None, None, None, None, None, "database"],
        ]
        for row, column in zip(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])
        fetch_parent = ItemTypeFetchParent("parameter_value")
        with signal_waiter(self._db_mngr.parameter_values_added) as waiter:
            while self._db_mngr.can_fetch_more(self._db_map, fetch_parent):
                self._db_mngr.fetch_more(self._db_map, fetch_parent)
                QApplication.processEvents()
            waiter.wait()
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        for row, column in zip(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    @mock.patch("spinetoolbox.spine_db_worker._CHUNK_SIZE", new=1)
    def test_incremental_fetching_groups_values_by_entity_class(self):
        tree_view = self._db_editor.ui.treeView_object
        add_object_class(tree_view, "object_1_class")
        add_object(tree_view, "an_object_1")
        add_object(tree_view, "another_object_1")
        add_object_class(tree_view, "object_2_class")
        add_object(tree_view, "an_object_2", object_class_index=1)
        definition_table_view = self._db_editor.ui.tableView_object_parameter_definition
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        _set_row_data(definition_table_view, definition_model, 0, ["object_1_class", "parameter_1"], delegate_mock)
        with signal_waiter(self._db_mngr.parameter_definitions_added) as waiter:
            _set_row_data(definition_table_view, definition_model, 1, ["object_2_class", "parameter_2"], delegate_mock)
            waiter.wait()
        table_view = self._db_editor.ui.tableView_object_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        _set_row_data(
            table_view, model, 0, ["object_1_class", "an_object_1", "parameter_1", "Base", "a_value"], delegate_mock
        )
        _set_row_data(
            table_view, model, 1, ["object_2_class", "an_object_2", "parameter_2", "Base", "b_value"], delegate_mock
        )
        with signal_waiter(self._db_mngr.parameter_values_added) as waiter:
            _set_row_data(
                table_view,
                model,
                2,
                ["object_1_class", "another_object_1", "parameter_1", "Base", "c_value"],
                delegate_mock,
            )
            waiter.wait()
        self.assertEqual(model.rowCount(), 4)
        self.assertEqual(model.columnCount(), 6)
        expected = [
            ["object_1_class", "an_object_1", "parameter_1", "Base", "a_value", "database"],
            ["object_2_class", "an_object_2", "parameter_2", "Base", "b_value", "database"],
            ["object_1_class", "another_object_1", "parameter_1", "Base", "c_value", "database"],
            [None, None, None, None, None, "database"],
        ]
        for row, column in zip(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])
        self._commit_changes_to_database("Add test data.")
        with signal_waiter(self._db_mngr.session_refreshed) as waiter:
            self._db_editor.refresh_session()
            waiter.wait()
        while model.rowCount() != 4:
            QApplication.processEvents()
        expected = [
            ["object_1_class", "an_object_1", "parameter_1", "Base", "a_value", "database"],
            ["object_1_class", "another_object_1", "parameter_1", "Base", "c_value", "database"],
            ["object_2_class", "an_object_2", "parameter_2", "Base", "b_value", "database"],
            [None, None, None, None, None, "database"],
        ]
        for row, column in zip(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])


def _set_row_data(view, model, row, data, delegate_mock):
    for column, cell_data in enumerate(data):
        delegate_mock.reset()
        delegate_mock.write_to_index(view, model.index(row, column), cell_data)


if __name__ == '__main__':
    unittest.main()
