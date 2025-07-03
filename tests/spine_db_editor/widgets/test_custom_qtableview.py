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
import csv
import io
import itertools
import os
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, Qt
from PySide6.QtWidgets import QApplication, QMessageBox
from spinedb_api import Array, DatabaseMapping, import_functions
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from tests.mock_helpers import (
    assert_table_model_data,
    assert_table_model_data_pytest,
    fetch_model,
    mock_clipboard_patch,
)
from tests.spine_db_editor.helpers import TestBase
from tests.spine_db_editor.widgets.helpers import EditorDelegateMocking, add_entity, add_zero_dimension_entity_class


class TestParameterDefinitionTableView(TestBase):
    def test_plotting(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="q", entity_class_name="Object", parsed_value=Array([2.3, 23.0]))
        table_view = self._db_editor.ui.tableView_parameter_definition
        model = table_view.model()
        fetch_model(model)
        index = model.index(0, 4)
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

    def test_set_db_column_visible(self):
        table_view = self._db_editor.ui.tableView_parameter_definition
        self.assertTrue(table_view.isColumnHidden(table_view._EXPECTED_COLUMN_COUNT - 1))
        self._db_editor.ui.tableView_parameter_definition.set_db_column_visibility(True)
        self.assertFalse(table_view.isColumnHidden(table_view._EXPECTED_COLUMN_COUNT - 1))

    def test_copy_empty_valid_values_column(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        table_view = self._db_editor.ui.tableView_parameter_definition
        model = table_view.model()
        fetch_model(model)
        valid_types_column = model.header.index("valid types")
        table_view.selectionModel().setCurrentIndex(
            model.index(0, valid_types_column), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        self.assertTrue(table_view.currentIndex().isValid())
        with mock_clipboard_patch("", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            self.assertTrue(table_view.copy())
            out_stream = io.StringIO()
            writer = csv.writer(out_stream, delimiter="\t", quotechar="'")
            writer.writerow([None])
            clipboard.setText.assert_called_once_with(out_stream.getvalue())

    def test_copy_valid_values_column(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X", parameter_type_list=("str", "bool"))
        table_view = self._db_editor.ui.tableView_parameter_definition
        model = table_view.model()
        fetch_model(model)
        valid_types_column = model.header.index("valid types")
        table_view.selectionModel().setCurrentIndex(
            model.index(0, valid_types_column), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        self.assertTrue(table_view.currentIndex().isValid())
        with mock_clipboard_patch("", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            self.assertTrue(table_view.copy())
            out_stream = io.StringIO()
            writer = csv.writer(out_stream, delimiter="\t", quotechar="'")
            writer.writerow(["bool" + DB_ITEM_SEPARATOR + "str"])
            clipboard.setText.assert_called_once_with(out_stream.getvalue())

    def test_paste_db_separator_data_to_valid_type_column(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X", parameter_type_list=("str", "bool"))
        table_view = self._db_editor.ui.tableView_parameter_definition
        model = table_view.model()
        fetch_model(model)
        valid_types_column = model.header.index("valid types")
        table_view.selectionModel().setCurrentIndex(
            model.index(0, valid_types_column), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        self.assertTrue(table_view.currentIndex().isValid())
        out_stream = io.StringIO()
        writer = csv.writer(out_stream, delimiter="\t", quotechar="'")
        writer.writerow(["str" + DB_ITEM_SEPARATOR + "bool"])
        with mock_clipboard_patch(
            out_stream.getvalue(), "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"
        ):
            self.assertTrue(table_view.paste())
        expected = [
            ["Object", "X", "bool" + DB_ITEM_SEPARATOR + "str", None, "None", None, self.db_codename],
        ]
        assert_table_model_data(model, expected, self)


class TestParameterValueTableView(TestBase):
    def test_paste_empty_string_to_entity_byname_column(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_entity(entity_class_name="Object", name="my_object")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("my_object",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        fetch_model(model)
        byname_column = model.header.index("entity_byname")
        table_view.selectionModel().setCurrentIndex(
            model.index(0, byname_column), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        self.assertTrue(table_view.currentIndex().isValid())
        with mock_clipboard_patch("''", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertTrue(table_view.paste())
        expected = {
            Qt.ItemDataRole.DisplayRole: [
                ["Object", "my_object", "X", "Base", "2.3", self.db_codename],
            ],
            Qt.ItemDataRole.ToolTipRole: [
                ["Object", "my_object", "X", "<qt>Base alternative</qt>", None, self.db_codename],
            ],
            Qt.ItemDataRole.EditRole: [
                ["Object", ("my_object",), "X", "Base", "2.3", self.db_codename],
            ],
        }
        for role, expected_for_role in expected.items():
            assert_table_model_data(model, expected_for_role, self, role)

    def test_removing_row_removes_data_from_database(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="y")
        self._db_map.add_entity(entity_class_name="Object", name="pencil")
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("pencil",),
            parameter_definition_name="y",
            alternative_name="Base",
            parsed_value=2.3,
        )
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        model.fetchMore(QModelIndex())
        while model.rowCount() != 1:
            QApplication.processEvents()
        expected = [
            ["Object", "pencil", "y", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        selection_model = table_view.selectionModel()
        selection_model.select(model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        table_view.remove_selected()
        while model.rowCount() != 0:
            QApplication.processEvents()
        self.assertEqual(self._db_map.find_parameter_values(), [])

    def test_removing_row_does_not_allow_fetching_more_data(self):
        tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(tree_view, "an_object_class")
        add_entity(tree_view, "object_1")
        add_entity(tree_view, "object_2")
        definition_table_view = self._db_editor.ui.empty_parameter_definition_table_view
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 0), "an_object_class")
        delegate_mock.reset()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 1), "a_parameter")
        empty_table_view = self._db_editor.ui.empty_parameter_value_table_view
        empty_model = empty_table_view.model()
        self.assertEqual(empty_model.rowCount(), 1)
        _set_row_data(
            empty_table_view, empty_model, 0, ["an_object_class", ("object_1",), "a_parameter", "Base"], delegate_mock
        )
        delegate_mock.reset()
        delegate_mock.write_to_index(empty_table_view, empty_model.index(0, 4), "value_1")
        _set_row_data(
            empty_table_view, empty_model, 1, ["an_object_class", ("object_2",), "a_parameter", "Base"], delegate_mock
        )
        delegate_mock.reset()
        delegate_mock.write_to_index(empty_table_view, empty_model.index(1, 4), "value_2")
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        expected = [
            ["an_object_class", "object_1", "a_parameter", "Base", "value_1", self.db_codename],
            ["an_object_class", "object_2", "a_parameter", "Base", "value_2", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        selection_model = table_view.selectionModel()
        selection_model.select(model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        table_view.remove_selected()
        self.assertFalse(model.canFetchMore(QModelIndex()))
        expected = [
            ["an_object_class", "object_2", "a_parameter", "Base", "value_2", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)

    def test_receiving_uncommitted_but_existing_value_does_not_create_duplicate_entry(self):
        tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(tree_view, "an_object_class")
        add_entity(tree_view, "an_object")
        definition_table_view = self._db_editor.ui.empty_parameter_definition_table_view
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 0), "an_object_class")
        delegate_mock.reset()
        delegate_mock.write_to_index(definition_table_view, definition_model.index(0, 1), "a_parameter")
        empty_table_view = self._db_editor.ui.empty_parameter_value_table_view
        empty_model = empty_table_view.model()
        self.assertEqual(empty_model.rowCount(), 1)
        _set_row_data(
            empty_table_view, empty_model, 0, ["an_object_class", ("an_object",), "a_parameter", "Base"], delegate_mock
        )
        delegate_mock.reset()
        delegate_mock.write_to_index(empty_table_view, empty_model.index(0, 4), "value_1")
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        expected = [
            ["an_object_class", "an_object", "a_parameter", "Base", "value_1", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)

    @mock.patch("spinetoolbox.spine_db_worker._CHUNK_SIZE", new=1)
    def test_incremental_fetching_groups_values_by_entity_class(self):
        tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(tree_view, "object_1_class")
        add_entity(tree_view, "an_object_1")
        add_entity(tree_view, "another_object_1")
        add_zero_dimension_entity_class(tree_view, "object_2_class")
        add_entity(tree_view, "an_object_2", entity_class_index=1)
        definition_table_view = self._db_editor.ui.empty_parameter_definition_table_view
        definition_model = definition_table_view.model()
        delegate_mock = EditorDelegateMocking()
        _set_row_data(definition_table_view, definition_model, 0, ["object_1_class", "parameter_1"], delegate_mock)
        _set_row_data(definition_table_view, definition_model, 1, ["object_2_class", "parameter_2"], delegate_mock)
        empty_table_view = self._db_editor.ui.empty_parameter_value_table_view
        empty_model = empty_table_view.model()
        self.assertEqual(empty_model.rowCount(), 1)
        _set_row_data(
            empty_table_view,
            empty_model,
            0,
            ["object_1_class", ("an_object_1",), "parameter_1", "Base", "a_value"],
            delegate_mock,
        )
        _set_row_data(
            empty_table_view,
            empty_model,
            1,
            ["object_2_class", ("an_object_2",), "parameter_2", "Base", "b_value"],
            delegate_mock,
        )
        _set_row_data(
            empty_table_view,
            empty_model,
            2,
            ["object_1_class", ("another_object_1",), "parameter_1", "Base", "c_value"],
            delegate_mock,
        )
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        expected = [
            ["object_1_class", "an_object_1", "parameter_1", "Base", "a_value", self.db_codename],
            ["object_2_class", "an_object_2", "parameter_2", "Base", "b_value", self.db_codename],
            ["object_1_class", "another_object_1", "parameter_1", "Base", "c_value", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])
        self._commit_changes_to_database("Add test data.")
        self._db_editor.refresh_session()
        while model.rowCount() != 3:
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        expected = [
            ["object_1_class", "an_object_1", "parameter_1", "Base", "a_value", self.db_codename],
            ["object_2_class", "an_object_2", "parameter_2", "Base", "b_value", self.db_codename],
            ["object_1_class", "another_object_1", "parameter_1", "Base", "c_value", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_plotting(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="q", entity_class_name="Object")
        self._db_map.add_entity(name="baffling sphere", entity_class_name="Object")
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("baffling sphere",),
            parameter_definition_name="q",
            alternative_name="Base",
            parsed_value=Array([2.3, 23.0]),
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

    def test_set_db_column_visible(self):
        table_view = self._db_editor.ui.tableView_parameter_definition
        self.assertTrue(table_view.isColumnHidden(table_view._EXPECTED_COLUMN_COUNT - 1))
        self._db_editor.ui.tableView_parameter_definition.set_db_column_visibility(True)
        self.assertFalse(table_view.isColumnHidden(table_view._EXPECTED_COLUMN_COUNT - 1))


class TestParameterValueTableWithExistingData(TestBase):
    _CHUNK_SIZE = 100  # This has to be large enough, so the chunk won't 'fit' into the table view.

    @mock.patch("spinetoolbox.spine_db_worker._CHUNK_SIZE", new=_CHUNK_SIZE)
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        with DatabaseMapping(url, create=True) as db_map:
            # 1-D entity class
            self._n_entities = 12
            self._n_parameters = 12
            import_functions.import_entity_classes(db_map, (("object_class",),))
            object_data = [("object_class", f"object_{n}") for n in range(self._n_entities)]
            import_functions.import_entities(db_map, object_data)
            parameter_definition_data = (("object_class", f"parameter_{n}") for n in range(self._n_parameters))
            import_functions.import_object_parameters(db_map, parameter_definition_data)
            parameter_value_data = (
                ("object_class", f"object_{object_n}", f"parameter_{parameter_n}", "a_value")
                for object_n, parameter_n in itertools.product(range(self._n_entities), range(self._n_parameters))
            )
            import_functions.import_object_parameter_values(db_map, parameter_value_data)
            # 2-D entity class
            self._n_ND_entities = 2
            self._n_ND_parameters = 2
            import_functions.import_entity_classes(
                db_map,
                (
                    (
                        "multi_d_class",
                        (
                            "object_class",
                            "object_class",
                        ),
                    ),
                ),
            )
            nd_entity_names = [
                (f"object_{i}", f"object_{j}") for i, j in itertools.permutations(range(self._n_ND_entities), 2)
            ]
            object_data = [("multi_d_class", byname) for byname in nd_entity_names]
            import_functions.import_entities(db_map, object_data)
            parameter_definition_data = (("multi_d_class", f"parameter_{n}") for n in range(self._n_ND_parameters))
            import_functions.import_object_parameters(db_map, parameter_definition_data)
            parameter_value_data = [
                (
                    "multi_d_class",
                    byname,
                    f"parameter_{parameter_n}",
                    "a_value",
                )
                for byname, parameter_n in itertools.product(nd_entity_names, range(self._n_ND_parameters))
            ]
            import_functions.import_parameter_values(db_map, parameter_value_data)
            db_map.commit_session("Add test data.")
        self._common_setup(url, create=False)
        model = self._db_editor.ui.tableView_parameter_value.model()
        while model.rowCount() != self._CHUNK_SIZE:
            # Wait for fetching to finish.
            QApplication.processEvents()

    def tearDown(self):
        self._common_tear_down()
        self._temp_dir.cleanup()

    def _whole_model_rowcount(self):
        return self._n_entities * self._n_parameters + self._n_ND_entities * self._n_ND_parameters

    def test_purging_value_data_removes_all_rows(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE)
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        self.assertEqual(model.rowCount(), 0)

    def test_purging_value_data_clears_table(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE)
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        self.assertEqual(model.rowCount(), 0)

    def test_remove_fetched_rows(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE)
        ids = [model.item_at_row(row) for row in range(0, model.rowCount() - 1, 2)]
        self._db_mngr.remove_items({self._db_map: {"parameter_value": set(ids)}})
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE // 2)

    def test_undoing_purge(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE)
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        self.assertEqual(model.rowCount(), 0)
        self._db_mngr.undo_stack[self._db_map].undo()
        while model.rowCount() != self._whole_model_rowcount():
            # Fetch the entire model, because we want to validate all the data.
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        expected = [
            ["object_class", f"object_{object_n}", f"parameter_{parameter_n}", "Base", "a_value", self.db_codename]
            for object_n, parameter_n in itertools.product(range(self._n_entities), range(self._n_parameters))
        ]
        nd_entity_names = [f"object_{i} ǀ object_{j}" for i, j in itertools.permutations(range(self._n_ND_entities), 2)]
        expected.extend(
            [
                ["multi_d_class", entity_name, f"parameter_{parameter_n}", "Base", "a_value", self.db_codename]
                for entity_name, parameter_n in itertools.product(nd_entity_names, range(self._n_ND_parameters))
            ]
        )
        self.assertEqual(model.rowCount(), self._whole_model_rowcount())
        assert_table_model_data(model, expected, self)

    def test_rolling_back_purge(self):
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE)
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        self.assertEqual(model.rowCount(), 0)
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox") as roll_back_dialog:
            roll_back_dialog.StandardButton.Ok = QMessageBox.StandardButton.Ok
            instance = roll_back_dialog.return_value
            instance.exec.return_value = QMessageBox.StandardButton.Ok
            self._db_editor.ui.actionRollback.trigger()
            self._db_editor.rollback_session()
        while model.rowCount() != self._whole_model_rowcount():
            # Fetch the entire model, because we want to validate all the data.
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        expected = [
            ["object_class", f"object_{object_n}", f"parameter_{parameter_n}", "Base", "a_value", self.db_codename]
            for object_n, parameter_n in itertools.product(range(self._n_entities), range(self._n_parameters))
        ]
        nd_entity_names = [f"object_{i} ǀ object_{j}" for i, j in itertools.permutations(range(self._n_ND_entities), 2)]
        expected.extend(
            [
                ["multi_d_class", entity_name, f"parameter_{parameter_n}", "Base", "a_value", self.db_codename]
                for entity_name, parameter_n in itertools.product(nd_entity_names, range(self._n_ND_parameters))
            ]
        )
        QApplication.processEvents()
        self.assertEqual(model.rowCount(), self._whole_model_rowcount())
        assert_table_model_data(model, expected, self)

    def test_sorting(self):
        """Test that the parameter value table sorts in an expected order."""
        url = "sqlite:///" + os.path.join(self._temp_dir.name, "test_database.sqlite")
        with DatabaseMapping(url) as db_map:
            parameter_definition_data = (
                ("object_class", "0parameter_"),
                ("object_class", "1parameter_"),
            )
            import_functions.import_object_parameters(db_map, parameter_definition_data)
            parameter_value_data = (
                ("object_class", "object_0", "0parameter_", "a_value"),
                ("object_class", "object_0", "1parameter_", "a_value"),
                ("object_class", "object_1", "0parameter_", "a_value"),
                ("object_class", "object_1", "1parameter_", "a_value"),
            )
            import_functions.import_object_parameter_values(db_map, parameter_value_data)
            db_map.commit_session("Add test data.")
        table_view = self._db_editor.ui.tableView_parameter_value
        model = table_view.model()
        self.assertEqual(model.rowCount(), self._CHUNK_SIZE)
        while model.rowCount() != self._whole_model_rowcount() + 4:
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        expected = []
        for object_n in range(self._n_entities):
            for parameter_n in range(self._n_parameters):
                expected.append(
                    [
                        "object_class",
                        f"object_{object_n}",
                        f"parameter_{parameter_n}",
                        "Base",
                        "a_value",
                        self.db_codename,
                    ]
                )
            if object_n < 2:
                expected.extend(
                    [
                        ["object_class", f"object_{object_n}", "0parameter_", "Base", "a_value", self.db_codename],
                        ["object_class", f"object_{object_n}", "1parameter_", "Base", "a_value", self.db_codename],
                    ]
                )
        nd_entity_names = [f"object_{i} ǀ object_{j}" for i, j in itertools.permutations(range(self._n_ND_entities), 2)]
        expected.extend(
            [
                ["multi_d_class", entity_name, f"parameter_{parameter_n}", "Base", "a_value", self.db_codename]
                for entity_name, parameter_n in itertools.product(nd_entity_names, range(self._n_ND_parameters))
            ]
        )
        self.assertEqual(model.rowCount(), self._whole_model_rowcount() + 4)
        assert_table_model_data(model, expected, self)


class TestEntityAlternativeTableView(TestBase):
    def test_pasting_gibberish_to_the_active_column_converts_to_false(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_entity(entity_class_name="Object", name="spoon")
        self._db_map.add_entity_alternative(
            entity_class_name="Object", entity_byname=("spoon",), alternative_name="Base", active=True
        )
        table_view = self._db_editor.ui.tableView_entity_alternative
        model = table_view.model()
        fetch_model(model)
        table_view.selectionModel().setCurrentIndex(model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with mock_clipboard_patch(
            "Object\tspoon\tBase\tGIBBERISH", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"
        ):
            self.assertTrue(table_view.paste())
        expected = [
            ["Object", "spoon", "Base", False, "TestEntityAlternativeTableView_db"],
        ]
        assert_table_model_data(model, expected, self)

    def test_pasting_sane_date_to_the_active_column_converts_to_boolean_correctly(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_entity(entity_class_name="Object", name="spoon")
        self._db_map.add_entity_alternative(
            entity_class_name="Object", entity_byname=("spoon",), alternative_name="Base", active=False
        )
        table_view = self._db_editor.ui.tableView_entity_alternative
        model = table_view.model()
        fetch_model(model)
        table_view.selectionModel().setCurrentIndex(model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with mock_clipboard_patch(
            "Object\tspoon\tBase\tyes", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"
        ):
            self.assertTrue(table_view.paste())
        expected = [
            ["Object", "spoon", "Base", True, "TestEntityAlternativeTableView_db"],
        ]
        assert_table_model_data(model, expected, self)

    def test_set_db_column_visible(self):
        table_view = self._db_editor.ui.tableView_parameter_definition
        self.assertTrue(table_view.isColumnHidden(table_view._EXPECTED_COLUMN_COUNT - 1))
        self._db_editor.ui.tableView_parameter_definition.set_db_column_visibility(True)
        self.assertFalse(table_view.isColumnHidden(table_view._EXPECTED_COLUMN_COUNT - 1))


class TestEmptyParameterDefinitionTableView:
    def test_paste_parameter_types(self, db_editor):
        table_view = db_editor.ui.empty_parameter_definition_table_view
        model = table_view.model()
        type_column = model.header.index("valid types")
        index = model.index(0, type_column)
        table_view.setCurrentIndex(index)
        with mock_clipboard_patch("bool", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            assert table_view.paste()
        expected = [
            [None, None, "bool", None, None, None, "TestEmptyParameterDefinitionTableView_db"],
            [None, None, None, None, None, None, "TestEmptyParameterDefinitionTableView_db"],
        ]
        assert_table_model_data_pytest(model, expected)


class TestEmptyParameterValueTableView(TestBase):
    def test_remove_last_empty_row(self):
        table_view = self._db_editor.ui.empty_parameter_value_table_view
        model = table_view.model()
        index = model.index(0, 0)
        selection_model = table_view.selectionModel()
        selection_model.select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        table_view.remove_selected()
        self.assertFalse(selection_model.hasSelection())
        self.assertEqual(model.rowCount(), 1)

    def test_remove_rows_from_empty_model(self):
        tree_view = self._db_editor.ui.treeView_entity
        add_zero_dimension_entity_class(tree_view, "an_object_class")
        add_entity(tree_view, "an_object")
        table_view = self._db_editor.ui.empty_parameter_value_table_view
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
        selection_model.select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        table_view.remove_selected()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(), None)
        self.assertEqual(model.index(0, 1).data(), None)
        self.assertEqual(model.index(0, 2).data(), None)
        self.assertEqual(model.index(0, 3).data(), None)
        self.assertEqual(model.index(0, 4).data(), None)
        self.assertFalse(selection_model.hasSelection())

    def test_paste_empty_string_to_entity_byname_column(self):
        table_view = self._db_editor.ui.empty_parameter_value_table_view
        model = table_view.model()
        byname_column = model.header.index("entity_byname")
        table_view.selectionModel().setCurrentIndex(
            model.index(0, byname_column), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        with mock_clipboard_patch("''", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertTrue(table_view.paste())
        expected = {
            Qt.ItemDataRole.DisplayRole: [
                [None, None, None, None, None, self.db_codename],
            ],
            Qt.ItemDataRole.ToolTipRole: [
                [None, None, None, None, None, None],
            ],
            Qt.ItemDataRole.EditRole: [
                [None, (), None, None, None, self.db_codename],
            ],
        }
        for role, expected_for_role in expected.items():
            assert_table_model_data(model, expected_for_role, self, role)

    def test_purging_value_data_leaves_empty_rows_intact(self):
        self._db_map.add_entity_class(name="object_class")
        self._db_map.add_entity(entity_class_name="object_class", name="object_1")
        self._db_map.add_parameter_definition(entity_class_name="object_class", name="parameter_1")
        table_view = self._db_editor.ui.empty_parameter_value_table_view
        model = table_view.model()
        self.assertEqual(model.rowCount(), 1)
        delegate_mock = EditorDelegateMocking()
        _set_row_data(
            table_view,
            model,
            model.rowCount() - 1,
            ["object_class", ("object_1",), "parameter_1", "Base"],
            delegate_mock,
        )
        self._db_mngr.purge_items({self._db_map: ["parameter_value"]})
        expected = {
            Qt.ItemDataRole.DisplayRole: [
                ["object_class", "object_1", "parameter_1", "Base", None, self.db_codename],
                [None, None, None, None, None, self.db_codename],
            ],
            Qt.ItemDataRole.ToolTipRole: [
                [None, None, None, None, None, None],
                [None, None, None, None, None, None],
            ],
            Qt.ItemDataRole.EditRole: [
                ["object_class", ("object_1",), "parameter_1", "Base", None, self.db_codename],
                [None, None, None, None, None, self.db_codename],
            ],
        }
        for role, expected_for_role in expected.items():
            assert_table_model_data(model, expected_for_role, self, role)


class TestEmptyEntityAlternativeTableView(TestBase):
    def test_pasting_gibberish_to_the_active_column_converts_to_false(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_entity(entity_class_name="Object", name="spoon")
        empty_table_view = self._db_editor.ui.empty_entity_alternative_table_view
        empty_model = empty_table_view.model()
        empty_table_view.selectionModel().setCurrentIndex(
            empty_model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        with mock_clipboard_patch(
            "Object\tspoon\tBase\tGIBBERISH", "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"
        ):
            self.assertTrue(empty_table_view.paste())
        expected = {
            Qt.ItemDataRole.DisplayRole: [
                [None, None, None, None, self.db_codename],
            ],
            Qt.ItemDataRole.ToolTipRole: [
                [None, None, None, None, None],
            ],
            Qt.ItemDataRole.EditRole: [
                [None, None, None, None, self.db_codename],
            ],
        }
        while empty_model.rowCount() != len(expected[Qt.ItemDataRole.DisplayRole]):
            QApplication.processEvents()
        for role, expected_for_role in expected.items():
            assert_table_model_data(empty_model, expected_for_role, self, role)
        table_view = self._db_editor.ui.tableView_entity_alternative
        model = table_view.model()
        expected = {
            Qt.ItemDataRole.DisplayRole: [
                ["Object", "spoon", "Base", False, self.db_codename],
            ],
            Qt.ItemDataRole.ToolTipRole: [
                ["Object", "spoon", "<qt>Base alternative</qt>", False, self.db_codename],
            ],
            Qt.ItemDataRole.EditRole: [
                ["Object", ("spoon",), "Base", False, self.db_codename],
            ],
        }
        for role, expected_for_role in expected.items():
            assert_table_model_data(model, expected_for_role, self, role)


class TestMetadataTableView(TestBase):
    def test_copy_name_and_value_from_single_row(self):
        self._db_map.add_metadata(name="Title", value="Catalogue of things")
        metadata_table_view = self._db_editor.ui.metadata_table_view
        metadata_model = metadata_table_view.model()
        fetch_model(metadata_model)
        expected = [
            ["Title", "Catalogue of things", self.db_codename],
            ["", "", self.db_codename],
        ]
        assert_table_model_data(metadata_model, expected, self)
        selection_model = metadata_table_view.selectionModel()
        selection_model.select(metadata_model.index(0, 0), QItemSelectionModel.SelectionFlag.Select)
        selection_model.select(metadata_model.index(0, 1), QItemSelectionModel.SelectionFlag.Select)
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as get_clipboard:
            clipboard = mock.MagicMock()
            get_clipboard.return_value = clipboard
            self.assertTrue(metadata_table_view.copy())
            clipboard.setText.assert_called_once_with("Title\tCatalogue of things\r\n")

    def test_copy_name_and_value_to_single_row(self):
        metadata_table_view = self._db_editor.ui.metadata_table_view
        metadata_model = metadata_table_view.model()
        fetch_model(metadata_model)
        self.assertEqual(metadata_model.rowCount(), 1)
        metadata_table_view.setCurrentIndex(metadata_model.index(0, 0))
        selection_model = metadata_table_view.selectionModel()
        selection_model.select(metadata_model.index(0, 0), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with mock_clipboard_patch(
            "Title\tA catalogue of things that should be",
            "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard",
        ):
            self.assertTrue(metadata_table_view.paste())
        expected = [
            ["Title", "A catalogue of things that should be", self.db_codename],
            ["", "", self.db_codename],
        ]
        assert_table_model_data(metadata_model, expected, self)


def _set_row_data(view, model, row, data, delegate_mock):
    for column, cell_data in enumerate(data):
        delegate_mock.reset()
        delegate_mock.write_to_index(view, model.index(row, column), cell_data)


class TestPivotTableView(TestBase):
    def test_copy_element_data(self):
        self._db_map.add_entity_class(name="A")
        self._db_map.add_entity(entity_class_name="A", name="a1")
        self._db_map.add_entity(entity_class_name="A", name="a2")
        self._db_map.add_entity_class(name="B")
        self._db_map.add_entity(entity_class_name="B", name="b1")
        self._db_map.add_entity(entity_class_name="B", name="b2")
        self._db_map.add_entity_class(dimension_name_list=("B", "A"))
        self._db_editor.current_input_type = self._db_editor._ELEMENT
        entity_tree_view = self._db_editor.ui.treeView_entity
        entity_tree_model = entity_tree_view.model()
        entity_tree_root_index = entity_tree_model.index(0, 0)
        while entity_tree_model.rowCount(entity_tree_root_index) != 3:
            entity_tree_model.fetchMore(entity_tree_root_index)
            QApplication.processEvents()
        relationship_index = entity_tree_model.index(2, 0, entity_tree_root_index)
        self.assertEqual(relationship_index.data(), "B__A")
        with mock.patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as is_pivot_visible:
            is_pivot_visible.return_value = True
            entity_tree_view.setCurrentIndex(relationship_index)
        fetch_model(self._db_editor.pivot_table_model)
        pivot_table_view = self._db_editor.ui.pivot_table
        pivot_model = pivot_table_view.model()
        expected = [
            ["B", "A", None],
            ["b1", "a1", False],
            ["b1", "a2", False],
            ["b2", "a1", False],
            ["b2", "a2", False],
            [None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)
        selection = QItemSelection(
            pivot_model.index(0, 0), pivot_model.index(pivot_model.rowCount() - 1, pivot_model.columnCount() - 1)
        )
        pivot_table_view.selectionModel().select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as get_clipboard:
            clipboard = mock.MagicMock()
            get_clipboard.return_value = clipboard
            self.assertTrue(pivot_table_view.copy())
            expected = [
                ["B", "A", ""],
                ["b1", "a1", "false"],
                ["b1", "a2", "false"],
                ["b2", "a1", "false"],
                ["b2", "a2", "false"],
                ["", "", ""],
            ]
            str_out = io.StringIO()
            writer = csv.writer(str_out, delimiter="\t")
            writer.writerows(expected)
            clipboard.setText.assert_called_once_with(str_out.getvalue())

    def test_create_relationship_by_pasting(self):
        self._db_map.add_entity_class(name="A")
        self._db_map.add_entity(entity_class_name="A", name="a1")
        self._db_map.add_entity(entity_class_name="A", name="a2")
        self._db_map.add_entity_class(name="B")
        self._db_map.add_entity(entity_class_name="B", name="b1")
        self._db_map.add_entity(entity_class_name="B", name="b2")
        self._db_map.add_entity_class(dimension_name_list=("B", "A"))
        self._db_editor.current_input_type = self._db_editor._ELEMENT
        entity_tree_view = self._db_editor.ui.treeView_entity
        entity_tree_model = entity_tree_view.model()
        entity_tree_root_index = entity_tree_model.index(0, 0)
        while entity_tree_model.rowCount(entity_tree_root_index) != 3:
            entity_tree_model.fetchMore(entity_tree_root_index)
            QApplication.processEvents()
        relationship_index = entity_tree_model.index(2, 0, entity_tree_root_index)
        self.assertEqual(relationship_index.data(), "B__A")
        with mock.patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as is_pivot_visible:
            is_pivot_visible.return_value = True
            entity_tree_view.setCurrentIndex(relationship_index)
        fetch_model(self._db_editor.pivot_table_model)
        pivot_table_view = self._db_editor.ui.pivot_table
        pivot_model = pivot_table_view.model()
        expected = [
            ["B", "A", None],
            ["b1", "a1", False],
            ["b1", "a2", False],
            ["b2", "a1", False],
            ["b2", "a2", False],
            [None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)
        pivot_table_view.setCurrentIndex(pivot_model.index(3, 2))
        with mock_clipboard_patch(
            "yes",
            "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard",
        ):
            self.assertTrue(pivot_table_view.paste())
        expected = [
            ["B", "A", None],
            ["b1", "a1", False],
            ["b1", "a2", False],
            ["b2", "a1", True],
            ["b2", "a2", False],
            [None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)

    def test_destroy_relationship_by_pasting(self):
        self._db_map.add_entity_class(name="A")
        self._db_map.add_entity(entity_class_name="A", name="a1")
        self._db_map.add_entity(entity_class_name="A", name="a2")
        self._db_map.add_entity_class(name="B")
        self._db_map.add_entity(entity_class_name="B", name="b1")
        self._db_map.add_entity(entity_class_name="B", name="b2")
        self._db_map.add_entity_class(dimension_name_list=("B", "A"))
        self._db_map.add_entity(entity_class_name="B__A", entity_byname=("b2", "a1"))
        self._db_editor.current_input_type = self._db_editor._ELEMENT
        entity_tree_view = self._db_editor.ui.treeView_entity
        entity_tree_model = entity_tree_view.model()
        entity_tree_root_index = entity_tree_model.index(0, 0)
        while entity_tree_model.rowCount(entity_tree_root_index) != 3:
            entity_tree_model.fetchMore(entity_tree_root_index)
            QApplication.processEvents()
        relationship_index = entity_tree_model.index(2, 0, entity_tree_root_index)
        self.assertEqual(relationship_index.data(), "B__A")
        with mock.patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as is_pivot_visible:
            is_pivot_visible.return_value = True
            entity_tree_view.setCurrentIndex(relationship_index)
        fetch_model(self._db_editor.pivot_table_model)
        pivot_table_view = self._db_editor.ui.pivot_table
        pivot_model = pivot_table_view.model()
        expected = [
            ["B", "A", None],
            ["b1", "a1", False],
            ["b1", "a2", False],
            ["b2", "a1", True],
            ["b2", "a2", False],
            [None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)
        pivot_table_view.setCurrentIndex(pivot_model.index(3, 2))
        with mock_clipboard_patch(
            "no",
            "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard",
        ):
            self.assertTrue(pivot_table_view.paste())
        expected = [
            ["B", "A", None],
            ["b1", "a1", False],
            ["b1", "a2", False],
            ["b2", "a1", False],
            ["b2", "a2", False],
            [None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)

    def test_create_entities_by_pasting(self):
        self._db_map.add_entity_class(name="A")
        self._db_map.add_entity(entity_class_name="A", name="a1")
        self._db_map.add_entity_class(name="B")
        self._db_map.add_entity(entity_class_name="B", name="b1")
        self._db_map.add_entity_class(dimension_name_list=("B", "A"))
        self._db_editor.current_input_type = self._db_editor._ELEMENT
        entity_tree_view = self._db_editor.ui.treeView_entity
        entity_tree_model = entity_tree_view.model()
        entity_tree_root_index = entity_tree_model.index(0, 0)
        while entity_tree_model.rowCount(entity_tree_root_index) != 3:
            entity_tree_model.fetchMore(entity_tree_root_index)
            QApplication.processEvents()
        relationship_index = entity_tree_model.index(2, 0, entity_tree_root_index)
        self.assertEqual(relationship_index.data(), "B__A")
        with mock.patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as is_pivot_visible:
            is_pivot_visible.return_value = True
            entity_tree_view.setCurrentIndex(relationship_index)
        fetch_model(self._db_editor.pivot_table_model)
        pivot_table_view = self._db_editor.ui.pivot_table
        pivot_model = pivot_table_view.model()
        expected = [
            ["B", "A", None],
            ["b1", "a1", False],
            [None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)
        selection = QItemSelection(pivot_model.index(2, 0), pivot_model.index(2, 2))
        pivot_table_view.selectionModel().select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with mock_clipboard_patch(
            "b2\ta2\t\r\n",
            "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard",
        ):
            self.assertTrue(pivot_table_view.paste())
        expected = [
            ["B", "A", None],
            ["b1", "a1", False],
            ["b1", "a2", False],
            ["b2", "a1", False],
            ["b2", "a2", False],
            [None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)

    def test_copy_scenario_data(self):
        self._db_map.add_scenario(name="Scen1")
        self._db_map.add_alternatives([{"name": "alt1"}, {"name": "alt2"}, {"name": "alt3"}, {"name": "alt4"}])
        self._db_map.add_scenario_alternative(scenario_name="Scen1", alternative_name="alt3", rank=1)
        self._db_map.add_scenario_alternative(scenario_name="Scen1", alternative_name="alt1", rank=2)
        self._db_editor.current_input_type = self._db_editor._SCENARIO_ALTERNATIVE
        with mock.patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as is_pivot_visible:
            is_pivot_visible.return_value = True
            self._db_editor.do_reload_pivot_table()
        fetch_model(self._db_editor.pivot_table_model)
        pivot_table_view = self._db_editor.ui.pivot_table
        pivot_model = pivot_table_view.model()
        expected = [
            ["alternative", "Base", "alt1", "alt2", "alt3", "alt4", None],
            ["scenario", None, None, None, None, None, None],
            ["Scen1", False, 2, False, 1, False, None],
            [None, None, None, None, None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)
        selection_model = pivot_table_view.selectionModel()
        selection = QItemSelection(pivot_model.index(2, 1), pivot_model.index(2, 5))
        selection_model.select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as get_clipboard:
            clipboard = mock.MagicMock()
            get_clipboard.return_value = clipboard
            self.assertTrue(pivot_table_view.copy())
            clipboard.setText.assert_called_once_with("false\t2\tfalse\t1\tfalse\r\n")

    def test_paste_new_scenario_alternative_data(self):
        self._db_map.add_scenario(name="Scen1")
        self._db_map.add_alternatives([{"name": "alt1"}, {"name": "alt2"}, {"name": "alt3"}, {"name": "alt4"}])
        self._db_editor.current_input_type = self._db_editor._SCENARIO_ALTERNATIVE
        with mock.patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as is_pivot_visible:
            is_pivot_visible.return_value = True
            self._db_editor.do_reload_pivot_table()
        fetch_model(self._db_editor.pivot_table_model)
        pivot_table_view = self._db_editor.ui.pivot_table
        pivot_model = pivot_table_view.model()
        expected = [
            ["alternative", "Base", "alt1", "alt2", "alt3", "alt4", None],
            ["scenario", None, None, None, None, None, None],
            ["Scen1", False, False, False, False, False, None],
            [None, None, None, None, None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)
        pivot_table_view.setCurrentIndex(pivot_model.index(2, 1))
        with mock_clipboard_patch(
            "false\t2\tfalse\t1",
            "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard",
        ):
            self.assertTrue(pivot_table_view.paste())
        expected = [
            ["alternative", "Base", "alt1", "alt2", "alt3", "alt4", None],
            ["scenario", None, None, None, None, None, None],
            ["Scen1", False, 2, False, 1, False, None],
            [None, None, None, None, None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)

    def test_remove_alternative_from_scenario_by_pasting(self):
        self._db_map.add_scenario(name="Scen1")
        self._db_map.add_alternatives([{"name": "alt1"}, {"name": "alt2"}, {"name": "alt3"}, {"name": "alt4"}])
        self._db_map.add_scenario_alternative(scenario_name="Scen1", alternative_name="alt3", rank=1)
        self._db_map.add_scenario_alternative(scenario_name="Scen1", alternative_name="alt2", rank=2)
        self._db_editor.current_input_type = self._db_editor._SCENARIO_ALTERNATIVE
        with mock.patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as is_pivot_visible:
            is_pivot_visible.return_value = True
            self._db_editor.do_reload_pivot_table()
        fetch_model(self._db_editor.pivot_table_model)
        pivot_table_view = self._db_editor.ui.pivot_table
        pivot_model = pivot_table_view.model()
        expected = [
            ["alternative", "Base", "alt1", "alt2", "alt3", "alt4", None],
            ["scenario", None, None, None, None, None, None],
            ["Scen1", False, False, 2, 1, False, None],
            [None, None, None, None, None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)
        pivot_table_view.setCurrentIndex(pivot_model.index(2, 4))
        with mock_clipboard_patch(
            "false",
            "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard",
        ):
            self.assertTrue(pivot_table_view.paste())
        expected = [
            ["alternative", "Base", "alt1", "alt2", "alt3", "alt4", None],
            ["scenario", None, None, None, None, None, None],
            ["Scen1", False, False, 1, False, False, None],
            [None, None, None, None, None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)

    def test_modify_scenario_alternatives_by_pasting(self):
        self._db_map.add_scenario(name="Scen1")
        self._db_map.add_alternatives([{"name": "alt1"}, {"name": "alt2"}, {"name": "alt3"}, {"name": "alt4"}])
        self._db_map.add_scenario_alternative(scenario_name="Scen1", alternative_name="alt3", rank=1)
        self._db_map.add_scenario_alternative(scenario_name="Scen1", alternative_name="alt2", rank=2)
        self._db_editor.current_input_type = self._db_editor._SCENARIO_ALTERNATIVE
        with mock.patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as is_pivot_visible:
            is_pivot_visible.return_value = True
            self._db_editor.do_reload_pivot_table()
        fetch_model(self._db_editor.pivot_table_model)
        pivot_table_view = self._db_editor.ui.pivot_table
        pivot_model = pivot_table_view.model()
        expected = [
            ["alternative", "Base", "alt1", "alt2", "alt3", "alt4", None],
            ["scenario", None, None, None, None, None, None],
            ["Scen1", False, False, 2, 1, False, None],
            [None, None, None, None, None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)
        pivot_table_view.setCurrentIndex(pivot_model.index(2, 1))
        with mock_clipboard_patch(
            "false\tfalse\t1\t2\tFalse",
            "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard",
        ):
            self.assertTrue(pivot_table_view.paste())
        expected = [
            ["alternative", "Base", "alt1", "alt2", "alt3", "alt4", None],
            ["scenario", None, None, None, None, None, None],
            ["Scen1", False, False, 1, 2, False, None],
            [None, None, None, None, None, None, None],
        ]
        assert_table_model_data(pivot_model, expected, self)


if __name__ == "__main__":
    unittest.main()
