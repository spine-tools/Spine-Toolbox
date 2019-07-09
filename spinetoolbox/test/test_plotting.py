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
from PySide2.QtWidgets import QApplication
from plotting import plot_pivot_column, plot_pivot_selection
from tabularview_models import PivotTableModel


class TestPlotting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._model = PivotTableModel()
        data = [
            ['1', 'int_col', '-3'],
            ['2', 'int_col', '-1'],
            ['3', 'int_col', '2'],
            ['1', 'float_col', '1.1'],
            ['2', 'float_col', '1.2'],
            ['3', 'float_col', '1.3'],
            [
                '1',
                'time_series_col',
                '{"type": "time_series", "data": {"2019-07-10T13:00": 2.3, "2019-07-10T13:20": 5.0}}',
            ],
            [
                '2',
                'time_series_col',
                '{"type": "time_series", "index": {"start": "2019-07-10T13:00", "resolution": "20 minutes"}, "data": [3.3, 4.0]}',
            ],
            [
                '3',
                'time_series_col',
                '{"type": "time_series", "data": {"2019-07-10T13:00": 4.3, "2019-07-10T13:20": 3.0}}',
            ],
        ]
        index_names = ['rows', 'col_types']
        index_real_names = ['real_id', 'real_col_types']
        index_types = [str, str]
        self._model.set_data(data, index_names, index_types, index_real_names=index_real_names)
        self._model.set_pivot(['rows'], ['col_types'], [], ())

    def test_plot_pivot_column_float_type(self):
        plot_widget = plot_pivot_column(self._model, 1)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [1.1, 1.2, 1.3]))

    def test_plot_pivot_column_int_type(self):
        plot_widget = plot_pivot_column(self._model, 2)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [-3.0, -1.0, 2.0]))

    def test_plot_pivot_column_time_series_type(self):
        plot_widget = plot_pivot_column(self._model, 3)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [2.3, 5.0]))
        self.assertTrue(all(lines[1].get_ydata(orig=True) == [3.3, 4.0]))
        self.assertTrue(all(lines[2].get_ydata(orig=True) == [4.3, 3.0]))

    def test_plot_pivot_selection(self):
        selected_indexes = list()
        for row in range(2, 5):
            for column in range(1, 3):
                selected_indexes.append(self._model.index(row, column))
        plot_widget = plot_pivot_selection(self._model, selected_indexes)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [1.1, 1.2, 1.3]))
        self.assertTrue(all(lines[1].get_ydata(orig=True) == [-3.0, -1.0, 2.0]))

    def test_plot_pivot_column_with_y_column(self):
        self._model.set_plot_y_column(1, True)
        plot_widget = plot_pivot_column(self._model, 2)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(all(lines[0].get_xdata(orig=True) == [1.1, 1.2, 1.3]))
        self.assertTrue(all(lines[0].get_ydata(orig=True) == [-3.0, -1.0, 2.0]))


if __name__ == '__main__':
    unittest.main()
