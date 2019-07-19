######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the plotting module.

:author: A. Soininen(VTT)
:date:   10.7.2019
"""

import unittest
from unittest.mock import Mock
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtWidgets import QApplication
from spinedb_api import TimeSeriesVariableResolution
from plotting import (
    add_time_series_plot,
    plot_pivot_column,
    plot_selection,
    PlottingError,
    GraphAndTreeViewPlottingSupport,
    PivotTablePlottingSupport,
)
from tabularview_models import PivotTableModel
from widgets.plot_widget import PlotWidget


def _make_pivot_model():
    """Returns a prefilled PivotTableModel."""
    model = PivotTableModel()
    data = [
        ['1', 'int_col', '-3'],
        ['2', 'int_col', '-1'],
        ['3', 'int_col', '2'],
        ['1', 'float_col', '1.1'],
        ['2', 'float_col', '1.2'],
        ['3', 'float_col', '1.3'],
        ['1', 'time_series_col', '{"type": "time_series", "data": {"2019-07-10T13:00": 2.3, "2019-07-10T13:20": 5.0}}'],
        [
            '2',
            'time_series_col',
            '{"type": "time_series", "index": {"start": "2019-07-10T13:00", "resolution": "20 minutes"}, "data": [3.3, 4.0]}',
        ],
        ['3', 'time_series_col', '{"type": "time_series", "data": {"2019-07-10T13:00": 4.3, "2019-07-10T13:20": 3.0}}'],
    ]
    index_names = ['rows', 'col_types']
    index_real_names = ['real_id', 'real_col_types']
    index_types = [str, str]
    model.set_data(data, index_names, index_types, index_real_names=index_real_names)
    model.set_pivot(['rows'], ['col_types'], [], ())
    return model


class _MockTreeGraphViewModel(QAbstractTableModel):
    """A mock model for testing purposes."""

    def __init__(self):
        super().__init__()
        self._table = [
            ["label1", "-2.3"],
            ["label2", "-0.5"],
            [
                "label3",
                '{"type": "time_series", "index": {"start": "2019-07-11T09:00", "resolution": "3 days"}, "data": [0.5, 2.3]}',
            ],
            ["label4", '{"type": "time_series", "data": [["2019-07-11T09:00", -5.0], ["2019-07-17T10:35", -3.3]]}'],
        ]

    def rowCount(self, parent=QModelIndex()):
        return 4

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        return self._table[index.row()][index.column()]

    def headerData(self, column):
        return "value"

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        self._table[index.row()][index.column()] = value
        return True


def mock_graph_tree_view_plotting_support():
    mock_table_view = Mock()
    mock_table_view.isColumnHidden.return_value = False
    return GraphAndTreeViewPlottingSupport(mock_table_view)


class TestPlotting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_plot_pivot_column_float_type(self):
        model = _make_pivot_model()
        support = PivotTablePlottingSupport()
        plot_widget = plot_pivot_column(model, 1, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [1.1, 1.2, 1.3]))

    def test_plot_pivot_column_int_type(self):
        model = _make_pivot_model()
        support = PivotTablePlottingSupport()
        plot_widget = plot_pivot_column(model, 2, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [-3.0, -1.0, 2.0]))

    def test_plot_pivot_column_time_series_type(self):
        model = _make_pivot_model()
        support = PivotTablePlottingSupport()
        plot_widget = plot_pivot_column(model, 3, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [2.3, 5.0]))
        self.assertTrue(all(lines[1].get_ydata(orig=True) == [3.3, 4.0]))
        self.assertTrue(all(lines[2].get_ydata(orig=True) == [4.3, 3.0]))

    def test_plot_pivot_selection(self):
        model = _make_pivot_model()
        selected_indexes = list()
        for row in range(2, 5):
            for column in range(1, 3):
                selected_indexes.append(model.index(row, column))
        support = PivotTablePlottingSupport()
        plot_widget = plot_selection(model, selected_indexes, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [1.1, 1.2, 1.3]))
        self.assertTrue(all(lines[1].get_ydata(orig=True) == [-3.0, -1.0, 2.0]))

    def test_plot_pivot_column_with_x_column(self):
        model = _make_pivot_model()
        model.set_plot_x_column(1, True)
        support = PivotTablePlottingSupport()
        plot_widget = plot_pivot_column(model, 2, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_xdata(orig=True) == [1.1, 1.2, 1.3]))
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [-3.0, -1.0, 2.0]))

    def test_plot_tree_view_selection_of_floats(self):
        model = _MockTreeGraphViewModel()
        selected_indexes = list()
        selected_indexes.append(model.index(0, 1))
        selected_indexes.append(model.index(1, 1))
        support = mock_graph_tree_view_plotting_support()
        plot_widget = plot_selection(model, selected_indexes, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [-2.3, -0.5]))

    def test_plot_tree_view_selection_of_time_series(self):
        model = _MockTreeGraphViewModel()
        selected_indexes = list()
        selected_indexes.append(model.index(2, 1))
        selected_indexes.append(model.index(3, 1))
        support = mock_graph_tree_view_plotting_support()
        plot_widget = plot_selection(model, selected_indexes, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [0.5, 2.3]))
        self.assertTrue(all(lines[1].get_ydata(orig=True) == [-5.0, -3.3]))

    def test_plot_tree_view_selection_raises_with_mixed_data(self):
        model = _MockTreeGraphViewModel()
        selected_indexes = list()
        selected_indexes.append(model.index(1, 1))
        selected_indexes.append(model.index(2, 1))
        support = mock_graph_tree_view_plotting_support()
        self.assertRaises(PlottingError, plot_selection, model, selected_indexes, support)

    def test_plot_single_plain_number(self):
        """Test that a selection containing a single plain number gets plotted."""
        model = _MockTreeGraphViewModel()
        selected_indexes = list()
        selected_indexes.append(model.index(0, 1))
        support = mock_graph_tree_view_plotting_support()
        plot_widget = plot_selection(model, selected_indexes, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [-2.3]))

    def test_add_time_series_plot(self):
        plot_widget = PlotWidget()
        time_series = TimeSeriesVariableResolution(["1917-12-06", "2017-12-06"], [0.0, 100.0], False, False)
        add_time_series_plot(plot_widget, time_series)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [0.0, 100.0]))


if __name__ == '__main__':
    unittest.main()
