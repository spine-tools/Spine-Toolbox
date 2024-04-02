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

"""Unit tests for DB editor's custom ``QTableView`` classes."""
import itertools
import os
import unittest
from tempfile import TemporaryDirectory
from unittest import mock
from PySide6.QtCore import QItemSelectionModel, QModelIndex
from PySide6.QtWidgets import QApplication, QMessageBox
from spinedb_api import Array, DatabaseMapping, import_functions, to_database
from tests.mock_helpers import fetch_model
from tests.spine_db_editor.helpers import TestBase
from tests.spine_db_editor.widgets.helpers import (
    add_entity,
    add_zero_dimension_entity_class,
    EditorDelegateMocking,
)


class TestParameterDefinitionTableView(TestBase):
    def test_plotting(self):
        self.assert_success(self._db_map.add_entity_class_item(name="Object"))
        value, value_type = to_database(Array([2.3, 23.0]))
        self.assert_success(
            self._db_map.add_parameter_definition_item(
                name="q", entity_class_name="Object", default_value=value, default_type=value_type
            )
        )
        table_view = self._db_editor.ui.tableView_parameter_definition
        model = table_view.model()
        fetch_model(model)
        index = model.index(0, 3)
        plot_widget = table_view._plot_selection([index])
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestParameterDefinitionTableView_db | Object | q")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "i")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "q")
            legend = plot_widget.canvas.legend_axes.get_legend()
            self.assertIsNone(legend)
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), [0, 1])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [2.3, 23.0])
        finally:
            plot_widget.deleteLater()


class TestParameterValueTableView(TestBase):
    def test_paste_empty_string_to_entity_byname_column(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        byname_column = model.header.index("entity_byname")
        table_view.selectionModel().setCurrentIndex(
            model.index(0, byname_column), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        mock_clipboard = mock.MagicMock()
        mock_clipboard.text.return_value = "''"
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            clipboard.return_value = mock_clipboard
            self.assertTrue(table_view.paste())
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 6)
        expected = [
            [None, "", None, None, None, "TestParameterValueTableView_db"],
        ]
        for row in range(model.rowCount()):
            for column in range(model.columnCount()):
                with self.subTest(row=row, column=column):
                    self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_remove_last_empty_row(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        index = model.index(0, 0)
        selection_model = table_view.selectionModel()
        selection_model.select(index, QItemSelectionModel.ClearAndSelect)
        table_view.remove_selected()
        self.assertFalse(selection_model.hasSelection())
        self.assertEqual(model.rowCount(), 1)

    def test_remove_rows_from_empty_model(self):
        tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(tree_view, "an_object_class")
        add_entity(tree_view, "an_object")
        table_view = self._db_editor.ui.tableView_parameter_value
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
        self.assertEqual(model.index(0, 5).data(), self.db_codename)
        self.assertEqual(model.index(1, 0).data(), None)
        self.assertEqual(model.index(1, 1).data(), None)
        self.assertEqual(model.index(1, 2).data(), None)
        self.assertEqual(model.index(1, 3).data(), None)
        self.assertEqual(model.index(1, 4).data(), None)
        self.assertEqual(model.index(1, 5).data(), self.db_codename)
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
        tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(tree_view, "an_object_class")
        add_entity(tree_view, "object_1")
        add_entity(tree_view, "object_2")
        definition_table_view = self._db_editor.ui.tableView_parameter_definition
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 0), "an_object_class")
        delegate_mock.reset()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 1), "a_parameter")
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        _set_row_data(table_view, model, 0, ["an_object_class", "object_1", "a_parameter", "Base"], delegate_mock)
        delegate_mock.reset()
        delegate_mock.write_to_index(table_view, model.index(0, 4), "value_1")
        _set_row_data(table_view, model, 1, ["an_object_class", "object_2", "a_parameter", "Base"], delegate_mock)
        delegate_mock.reset()
        delegate_mock.write_to_index(table_view, model.index(1, 4), "value_2")
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 6)
        expected = [
            ["an_object_class", "object_1", "a_parameter", "Base", "value_1", self.db_codename],
            ["an_object_class", "object_2", "a_parameter", "Base", "value_2", self.db_codename],
            [None, None, None, None, None, self.db_codename],
        ]
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])
        selection_model = table_view.selectionModel()
        selection_model.select(model.index(0, 0), QItemSelectionModel.ClearAndSelect)
        table_view.remove_selected()
        self.assertFalse(model.canFetchMore(QModelIndex()))
        expected = [
            ["an_object_class", "object_2", "a_parameter", "Base", "value_2", self.db_codename],
            [None, None, None, None, None, self.db_codename],
        ]
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_receiving_uncommitted_but_existing_value_does_not_create_duplicate_entry(self):
        tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(tree_view, "an_object_class")
        add_entity(tree_view, "an_object")
        definition_table_view = self._db_editor.ui.tableView_parameter_definition
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 0), "an_object_class")
        delegate_mock.reset()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 1), "a_parameter")
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        _set_row_data(table_view, model, 0, ["an_object_class", "an_object", "a_parameter", "Base"], delegate_mock)
        delegate_mock.reset()
        delegate_mock.write_to_index(table_view, model.index(0, 4), "value_1")
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        expected = [
            ["an_object_class", "an_object", "a_parameter", "Base", "value_1", self.db_codename],
            [None, None, None, None, None, self.db_codename],
        ]
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    @mock.patch("spinetoolbox.spine_db_worker._CHUNK_SIZE", new=1)
    def test_incremental_fetching_groups_values_by_entity_class(self):
        tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(tree_view, "object_1_class")
        add_entity(tree_view, "an_object_1")
        add_entity(tree_view, "another_object_1")
        add_zero_dimension_entity_class(tree_view, "object_2_class")
        add_entity(tree_view, "an_object_2", entity_class_index=1)
        definition_table_view = self._db_editor.ui.tableView_parameter_definition
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        _set_row_data(definition_table_view, definition_model, 0, ["object_1_class", "parameter_1"], delegate_mock)
        _set_row_data(definition_table_view, definition_model, 1, ["object_2_class", "parameter_2"], delegate_mock)
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        _set_row_data(
            table_view, model, 0, ["object_1_class", "an_object_1", "parameter_1", "Base", "a_value"], delegate_mock
        )
        _set_row_data(
            table_view, model, 1, ["object_2_class", "an_object_2", "parameter_2", "Base", "b_value"], delegate_mock
        )
        _set_row_data(
            table_view,
            model,
            2,
            ["object_1_class", "another_object_1", "parameter_1", "Base", "c_value"],
            delegate_mock,
        )
        self.assertEqual(model.rowCount(), 4)
        self.assertEqual(model.columnCount(), 6)
        expected = [
            ["object_1_class", "an_object_1", "parameter_1", "Base", "a_value", self.db_codename],
            ["object_2_class", "an_object_2", "parameter_2", "Base", "b_value", self.db_codename],
            ["object_1_class", "another_object_1", "parameter_1", "Base", "c_value", self.db_codename],
            [None, None, None, None, None, self.db_codename],
        ]
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])
        self._commit_changes_to_database("Add test data.")
        self._db_editor.refresh_session()
        while model.rowCount() != 4:
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        expected = [
            ["object_1_class", "an_object_1", "parameter_1", "Base", "a_value", self.db_codename],
            ["object_1_class", "another_object_1", "parameter_1", "Base", "c_value", self.db_codename],
            ["object_2_class", "an_object_2", "parameter_2", "Base", "b_value", self.db_codename],
            [None, None, None, None, None, self.db_codename],
        ]
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_plotting(self):
        self.assert_success(self._db_map.add_entity_class_item(name="Object"))
        self.assert_success(self._db_map.add_parameter_definition_item(name="q", entity_class_name="Object"))
        self.assert_success(self._db_map.add_entity_item(name="baffling sphere", entity_class_name="Object"))
        value, value_type = to_database(Array([2.3, 23.0]))
        self.assert_success(
            self._db_map.add_parameter_value_item(
                entity_class_name="Object",
                entity_byname=("baffling sphere",),
                parameter_definition_name="q",
                alternative_name="Base",
                value=value,
                type=value_type,
            )
        )
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        fetch_model(model)
        index = model.index(0, 4)
        plot_widget = table_view._plot_selection([index])
        try:
            self.assertEqual(
                plot_widget.canvas.axes.get_title(),
                "TestParameterValueTableView_db | Object | baffling sphere | q | Base",
            )
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "i")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "q")
            legend = plot_widget.canvas.legend_axes.get_legend()
            self.assertIsNone(legend)
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), [0, 1])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [2.3, 23.0])
        finally:
            plot_widget.deleteLater()


class TestParameterValueTableWithExistingData(TestBase):
    _CHUNK_SIZE = 100  # This has to be large enough, so the chunk won't 'fit' into the table view.

    @mock.patch("spinetoolbox.spine_db_worker._CHUNK_SIZE", new=_CHUNK_SIZE)
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        db_map = DatabaseMapping(url, create=True)
        import_functions.import_object_classes(db_map, ("object_class",))
        self._n_objects = 12
        object_data = (("object_class", f"object_{n}") for n in range(self._n_objects))
        import_functions.import_objects(db_map, object_data)
        self._n_parameters = 12
        parameter_definition_data = (("object_class", f"parameter_{n}") for n in range(self._n_parameters))
        import_functions.import_object_parameters(db_map, parameter_definition_data)
        parameter_value_data = (
            ("object_class", f"object_{object_n}", f"parameter_{parameter_n}", "a_value")
            for object_n, parameter_n in itertools.product(range(self._n_objects), range(self._n_parameters))
        )
        import_functions.import_object_parameter_values(db_map, parameter_value_data)
        db_map.commit_session("Add test data.")
        db_map.close()
        self._common_setup(url, create=False)
        model = self._db_editor.ui.tableView_parameter_value.model()
        while model.rowCount() != self._CHUNK_SIZE + 1:
            # Wait for fetching to finish.
            QApplication.processEvents()

    def tearDown(self):
        self._common_tear_down()
        self._temp_dir.cleanup()

    def test_purging_value_data_removes_all_rows(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE + 1)
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        self.assertEqual(model.rowCount(), 1)

    def test_purging_value_data_leaves_empty_rows_intact(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE + 1)
        delegate_mock = EditorDelegateMocking()
        _set_row_data(
            table_view, model, model.rowCount() - 1, ["object_class", "object_1", "parameter_1", "Base"], delegate_mock
        )
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        self.assertEqual(model.rowCount(), 2)
        expected = [
            ["object_class", "object_1", "parameter_1", "Base", None, self.db_codename],
            [None, None, None, None, None, self.db_codename],
        ]
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_removing_fetched_rows_allows_still_fetching_more(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE + 1)
        n_values = self._n_parameters * self._n_objects
        self._db_mngr.remove_items({self._db_map: {"parameter_value": set(range(1, n_values, 2))}})
        self.assertEqual(model.rowCount(), (self._CHUNK_SIZE) / 2 + 1)

    def test_undoing_purge(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE + 1)
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        self.assertEqual(model.rowCount(), 1)
        self._db_editor.undo_action.trigger()
        while model.rowCount() != self._n_objects * self._n_parameters + 1:
            # Fetch the entire model, because we want to validate all the data.
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        expected = sorted(
            [
                ["object_class", f"object_{object_n}", f"parameter_{parameter_n}", "Base", "a_value", self.db_codename]
                for object_n, parameter_n in itertools.product(range(self._n_objects), range(self._n_parameters))
            ],
            key=lambda x: (x[1], x[2]),
        )
        expected.append([None, None, None, None, None, self.db_codename])
        self.assertEqual(model.rowCount(), self._n_objects * self._n_parameters + 1)
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_rolling_back_purge(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE + 1)
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        self.assertEqual(model.rowCount(), 1)
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox") as roll_back_dialog:
            roll_back_dialog.StandardButton.Ok = QMessageBox.StandardButton.Ok
            instance = roll_back_dialog.return_value
            instance.exec.return_value = QMessageBox.StandardButton.Ok
            self._db_editor.ui.actionRollback.trigger()
            self._db_editor.rollback_session()
        while model.rowCount() != self._n_objects * self._n_parameters + 1:
            # Fetch the entire model, because we want to validate all the data.
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        expected = sorted(
            [
                ["object_class", f"object_{object_n}", f"parameter_{parameter_n}", "Base", "a_value", self.db_codename]
                for object_n, parameter_n in itertools.product(range(self._n_objects), range(self._n_parameters))
            ],
            key=lambda x: (x[1], x[2]),
        )
        QApplication.processEvents()
        expected.append([None, None, None, None, None, self.db_codename])
        self.assertEqual(model.rowCount(), self._n_objects * self._n_parameters + 1)
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])


class TestEntityAlternativeTableView(TestBase):
    def test_pasting_gibberish_to_the_active_column_converts_to_false(self):
        self._db_map.add_entity_class_item(name="Object")
        self._db_map.add_entity_item(entity_class_name="Object", name="spoon")
        table_view = self._db_editor.ui.tableView_entity_alternative
        model = table_view.model()
        table_view.selectionModel().setCurrentIndex(model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        mock_clipboard = mock.MagicMock()
        mock_clipboard.text.return_value = "Object\tspoon\tBase\tGIBBERISH"
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            clipboard.return_value = mock_clipboard
            self.assertTrue(table_view.paste())
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 5)
        expected = [
            ["Object", "spoon", "Base", False, "TestEntityAlternativeTableView_db"],
            [None, None, None, None, "TestEntityAlternativeTableView_db"],
        ]
        for row in range(model.rowCount()):
            for column in range(model.columnCount()):
                with self.subTest(row=row, column=column):
                    self.assertEqual(model.index(row, column).data(), expected[row][column])


def _set_row_data(view, model, row, data, delegate_mock):
    for column, cell_data in enumerate(data):
        delegate_mock.reset()
        delegate_mock.write_to_index(view, model.index(row, column), cell_data)


if __name__ == "__main__":
    unittest.main()
