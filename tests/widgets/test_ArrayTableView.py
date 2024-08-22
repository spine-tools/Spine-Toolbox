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

"""Unit tests for ArrayTableView class."""
import csv
from io import StringIO
import locale
import unittest
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QApplication
from spinedb_api import Array
from spinetoolbox.mvcmodels.array_model import ArrayModel
from spinetoolbox.widgets.custom_qtableview import ArrayTableView, system_lc_numeric
from tests.mock_helpers import TestCaseWithQApplication, mock_clipboard_patch


class TestArrayTableView(TestCaseWithQApplication):
    def setUp(self):
        self._table_view = ArrayTableView()
        self._model = ArrayModel(self._table_view)
        self._table_view.setModel(self._model)

    def tearDown(self):
        self._table_view.deleteLater()

    def test_copy_without_selection_returns_false(self):
        self.assertFalse(self._table_view.copy())

    def test_copy_single_non_numeric_cell(self):
        self._model.reset(Array(["a"]))
        index = self._model.index(0, 1)
        self._table_view.selectionModel().select(index, QItemSelectionModel.Select)
        self.assertTrue(self._table_view.copy())
        clip = StringIO(QApplication.clipboard().text())
        array = list(csv.reader(clip))
        self.assertEqual(array, [["a"]])

    def test_copy_single_numeric_cell(self):
        self._model.reset(Array([5.5]))
        index = self._model.index(0, 1)
        self._table_view.selectionModel().select(index, QItemSelectionModel.Select)
        self.assertTrue(self._table_view.copy())
        clip = StringIO(QApplication.clipboard().text())
        array = list(csv.reader(clip, delimiter="\t"))
        with system_lc_numeric():
            self.assertEqual(array, [[locale.str(5.5)]])

    def test_copy_does_not_copy_expansion_row(self):
        self._model.reset(Array([5.5]))
        for column in range(self._model.columnCount()):
            for row in range(self._model.rowCount()):
                self._table_view.selectionModel().select(self._model.index(row, column), QItemSelectionModel.Select)
        self.assertTrue(self._table_view.copy())
        clip = StringIO(QApplication.clipboard().text())
        array = list(csv.reader(clip, delimiter="\t"))
        with system_lc_numeric():
            self.assertEqual(array, [["0", locale.str(5.5)]])

    def test_paste_non_numeric_to_empty_table(self):
        self._model.set_array_type(str)
        index = self._model.index(0, 0)
        self._table_view.selectionModel().select(index, QItemSelectionModel.Select)
        data = self._write_clipboard([["a"]])
        with mock_clipboard_patch(data, "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertTrue(self._table_view.paste())
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.array(), Array(["a"]))

    def test_paste_numeric_to_empty_table(self):
        index = self._model.index(0, 0)
        self._table_view.selectionModel().select(index, QItemSelectionModel.Select)
        data = self._write_clipboard([[2.3]])
        with mock_clipboard_patch(data, "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertTrue(self._table_view.paste())
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.array(), Array([2.3]))

    def test_paste_multiple_rows_to_single_row_selection(self):
        self._model.reset(Array([5.5]))
        index = self._model.index(0, 0)
        self._table_view.selectionModel().select(index, QItemSelectionModel.Select)
        data = self._write_clipboard([[2.3], [-2.3]])
        with mock_clipboard_patch(data, "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertTrue(self._table_view.paste())
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.array(), Array([2.3, -2.3]))

    def test_paste_only_what_fits_selection(self):
        self._model.reset(Array([5.5, -5.5]))
        for row in (0, 1):
            self._table_view.selectionModel().select(self._model.index(row, 0), QItemSelectionModel.Select)
        data = self._write_clipboard([[2.3], [-2.3], [23.0]])
        with mock_clipboard_patch(data, "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertTrue(self._table_view.paste())
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.array(), Array([2.3, -2.3]))

    def test_pasting_incompatible_data_type_does_not_expand_model(self):
        self._model.reset(Array([5.5]))
        for row in (0, 1):
            self._table_view.selectionModel().select(self._model.index(row, 0), QItemSelectionModel.Select)
        data = self._write_clipboard([["Ilmarinen"], ["Väinämöinen"], ["Joukahainen"]])
        with mock_clipboard_patch(data, "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertFalse(self._table_view.paste())
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.array(), Array([5.5]))

    def test_pasting_incompatible_data_type_in_the_middle_expands_model_properly(self):
        self._model.reset(Array([5.5]))
        self._table_view.selectionModel().select(self._model.index(0, 0), QItemSelectionModel.Select)
        data = self._write_clipboard([[-2.3], ["Väinämöinen"], [-23.0]])
        with mock_clipboard_patch(data, "spinetoolbox.widgets.custom_qtableview.QApplication.clipboard"):
            self.assertTrue(self._table_view.paste())
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.array(), Array([-2.3, -23.0]))

    @staticmethod
    def _write_clipboard(data):
        with StringIO() as out_string:
            writer = csv.writer(out_string)
            writer.writerows(data)
            return out_string.getvalue()


if __name__ == "__main__":
    unittest.main()
