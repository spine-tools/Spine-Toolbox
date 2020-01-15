######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for IndexedValueTableView class.

:author: A. Soininen (VTT)
:date:   8.8.2019
"""

import locale
import unittest
from PySide2.QtCore import QItemSelectionModel
from PySide2.QtWidgets import QApplication
from spinedb_api import TimeSeriesVariableResolution
from spinetoolbox.mvcmodels.time_series_model_variable_resolution import TimeSeriesModelVariableResolution
from spinetoolbox.widgets.custom_qtableview import IndexedValueTableView


class TestIndexedValueTableView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        QApplication.clipboard().clear()
        self._table_view = IndexedValueTableView(parent=None)
        series = TimeSeriesVariableResolution(
            ["2019-08-08T12:00", "2019-08-08T13:00", "2019-08-08T14:00", "2019-08-08T15:00"],
            [1.1, 2.2, 3.3, 4.4],
            False,
            False,
        )
        model = TimeSeriesModelVariableResolution(series)
        self._table_view.setModel(model)

    def test_copy(self):
        selection_model = self._table_view.selectionModel()
        model = self._table_view.model()
        selection_model.select(model.index(0, 0), QItemSelectionModel.Select)
        selection_model.select(model.index(1, 1), QItemSelectionModel.Select)
        selection_model.select(model.index(2, 0), QItemSelectionModel.Select)
        self._table_view.copy()
        copied = QApplication.clipboard().text()
        self.assertEqual(copied, "2019-08-08T12:00:00\t\r\n\t{:n}\r\n2019-08-08T14:00:00\t\r\n".format(2.2))

    def test_paste_single_value(self):
        selection_model = self._table_view.selectionModel()
        model = self._table_view.model()
        selection_model.select(model.index(0, 1), QItemSelectionModel.Select)
        copied_data = locale.str(-1.1)
        QApplication.clipboard().setText(copied_data)
        self._table_view.paste()
        series = TimeSeriesVariableResolution(
            ["2019-08-08T12:00", "2019-08-08T13:00", "2019-08-08T14:00", "2019-08-08T15:00"],
            [-1.1, 2.2, 3.3, 4.4],
            False,
            False,
        )
        self.assertEqual(model.value, series)

    def test_paste_single_index(self):
        selection_model = self._table_view.selectionModel()
        model = self._table_view.model()
        selection_model.select(model.index(0, 0), QItemSelectionModel.Select)
        copied_data = "2019-08-08T00:00"
        QApplication.clipboard().setText(copied_data)
        self._table_view.paste()
        series = TimeSeriesVariableResolution(
            ["2019-08-08T00:00", "2019-08-08T13:00", "2019-08-08T14:00", "2019-08-08T15:00"],
            [1.1, 2.2, 3.3, 4.4],
            False,
            False,
        )
        self.assertEqual(model.value, series)

    def test_pasting_multiple_columns_to_last_row_expands_model(self):
        selection_model = self._table_view.selectionModel()
        model = self._table_view.model()
        selection_model.select(model.index(3, 1), QItemSelectionModel.Select)
        copied_data = "2019-08-08T17:00\t{:n}\n2019-08-08T18:00\t{:n}".format(-4.4, -5.5)
        QApplication.clipboard().setText(copied_data)
        self._table_view.paste()
        series = TimeSeriesVariableResolution(
            ["2019-08-08T12:00", "2019-08-08T13:00", "2019-08-08T14:00", "2019-08-08T17:00", "2019-08-08T18:00"],
            [1.1, 2.2, 3.3, -4.4, -5.5],
            False,
            False,
        )
        self.assertEqual(model.value, series)

    def test_pasting_single_column_to_last_row_expands_model(self):
        selection_model = self._table_view.selectionModel()
        model = self._table_view.model()
        selection_model.select(model.index(3, 0), QItemSelectionModel.Select)
        copied_data = "2019-08-08T17:00\n2019-08-08T18:00"
        QApplication.clipboard().setText(copied_data)
        self._table_view.paste()
        series = TimeSeriesVariableResolution(
            ["2019-08-08T12:00", "2019-08-08T13:00", "2019-08-08T14:00", "2019-08-08T17:00", "2019-08-08T18:00"],
            [1.1, 2.2, 3.3, 4.4, 0.0],
            False,
            False,
        )
        self.assertEqual(model.value, series)

    def test_paste_to_multirow_selection_limits_pasted_data(self):
        selection_model = self._table_view.selectionModel()
        model = self._table_view.model()
        selection_model.select(model.index(1, 0), QItemSelectionModel.Select)
        selection_model.select(model.index(1, 1), QItemSelectionModel.Select)
        selection_model.select(model.index(2, 0), QItemSelectionModel.Select)
        selection_model.select(model.index(2, 1), QItemSelectionModel.Select)
        copied_data = "2019-08-08T12:30\t{:n}\n2019-08-08T13:30\t{:n}\n2019-08-08T14:30\t{:n}".format(-2.2, -3.3, -4.4)
        QApplication.clipboard().setText(copied_data)
        self._table_view.paste()
        series = TimeSeriesVariableResolution(
            ["2019-08-08T12:00", "2019-08-08T12:30", "2019-08-08T13:30", "2019-08-08T15:00"],
            [1.1, -2.2, -3.3, 4.4],
            False,
            False,
        )
        self.assertEqual(model.value, series)

    def test_paste_to_larger_selection_overrides_first_rows_only(self):
        selection_model = self._table_view.selectionModel()
        model = self._table_view.model()
        selection_model.select(model.index(0, 0), QItemSelectionModel.Select)
        selection_model.select(model.index(0, 1), QItemSelectionModel.Select)
        selection_model.select(model.index(1, 0), QItemSelectionModel.Select)
        selection_model.select(model.index(1, 1), QItemSelectionModel.Select)
        selection_model.select(model.index(2, 0), QItemSelectionModel.Select)
        selection_model.select(model.index(2, 1), QItemSelectionModel.Select)
        copied_data = "2019-08-08T12:30\t{:n}\n2019-08-08T13:30\t{:n}".format(-1.1, -2.2)
        QApplication.clipboard().setText(copied_data)
        self._table_view.paste()
        series = TimeSeriesVariableResolution(
            ["2019-08-08T12:30", "2019-08-08T13:30", "2019-08-08T14:00", "2019-08-08T15:00"],
            [-1.1, -2.2, 3.3, 4.4],
            False,
            False,
        )
        self.assertEqual(model.value, series)

    def test_pasted_cells_are_selected(self):
        selection_model = self._table_view.selectionModel()
        model = self._table_view.model()
        selection_model.select(model.index(0, 1), QItemSelectionModel.Select)
        copied_data = locale.str(-1.1) + '\n' + locale.str(-2.2)
        QApplication.clipboard().setText(copied_data)
        self._table_view.paste()
        selected_indexes = selection_model.selectedIndexes()
        self.assertEqual(len(selected_indexes), 2)
        self.assertTrue(model.index(0, 1) in selected_indexes)
        self.assertTrue(model.index(1, 1) in selected_indexes)


if __name__ == '__main__':
    unittest.main()
