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

"""Unit tests for the ``plot_widget`` module."""
import unittest
from itertools import product
from unittest import mock
from matplotlib.gridspec import GridSpec
from PySide6.QtWidgets import QApplication
from spinedb_api.parameter_value import TimeSeriesFixedResolution
from spinetoolbox.plotting import plot_data, TreeNode, turn_node_to_xy_data, convert_indexed_value_to_tree
from spinetoolbox.widgets.plot_canvas import LegendPosition
from spinetoolbox.widgets.plot_widget import PlotWidget, _PlotDataWidget


class TestPlotWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._plot_widget = PlotWidget()

    def tearDown(self):
        self._plot_widget.deleteLater()

    def test_plot_data_widget_shows_datetimes_as_strings(self):
        # Warning: running this unit test alone might end up in an endless loop
        # probably due to Spine DB server failing to exit cleanly.
        time_series = TimeSeriesFixedResolution("2022-11-08T16:00", "3h", [1.1, 2.2], False, False)
        value_node = convert_indexed_value_to_tree(time_series)
        root_node = TreeNode("root index")
        root_node.content["first"] = value_node
        data_list = list(turn_node_to_xy_data(root_node, None))
        plot_data(data_list, self._plot_widget)
        with mock.patch.object(_PlotDataWidget, "show") as show_method:
            self._plot_widget.show_plot_data()
            show_method.assert_called_once()
        data_widget = None
        for widget in self._plot_widget.children():
            if isinstance(widget, _PlotDataWidget):
                data_widget = widget
                break
        if data_widget is None:
            self.fail("missing plot data widget")
        model = data_widget._model
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 2)
        expected = [["indexes", "first"], ["2022-11-08T16:00:00", "1.1"], ["2022-11-08T19:00:00", "2.2"]]
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_legend_axes_placement_bottom(self):
        plot_widget = PlotWidget(legend_axes_position=LegendPosition.BOTTOM)
        self.assertEqual(
            repr(plot_widget.canvas.legend_axes.get_gridspec()), repr(GridSpec(2, 1, height_ratios=[1, 0]))
        )

    def test_legend_axes_placement_right(self):
        plot_widget = PlotWidget(legend_axes_position=LegendPosition.RIGHT)
        self.assertEqual(repr(plot_widget.canvas.legend_axes.get_gridspec()), repr(GridSpec(1, 2, width_ratios=[1, 0])))


if __name__ == "__main__":
    unittest.main()
