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

"""Unit tests for the plotting module."""
import unittest
from contextlib import contextmanager
from unittest.mock import patch
import numpy
from PySide6.QtCore import QModelIndex, QItemSelectionModel, QObject
from PySide6.QtWidgets import QApplication
from matplotlib.gridspec import GridSpec
from spinedb_api import (
    DateTime,
    Map,
    TimeSeriesVariableResolution,
    to_database,
    TimeSeriesFixedResolution,
    TimePattern,
    Array,
)
from spinetoolbox.plotting import (
    plot_parameter_table_selection,
    PlottingError,
    convert_indexed_value_to_tree,
    TreeNode,
    turn_node_to_xy_data,
    XYData,
    reduce_indexes,
    combine_data_with_same_indexes,
    plot_data,
    raise_if_incompatible_x,
    plot_pivot_table_selection,
    LEGEND_PLACEMENT_THRESHOLD,
    add_row_to_exception,
    IndexName,
)
from tests.spine_db_editor.helpers import TestBase


class TestPlotPivotTableSelection(TestBase):
    def _add_object_parameter_values(self, values):
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "class", "id": 1}]})
        self._db_mngr.add_parameter_definitions(
            {self._db_map: [{"entity_class_id": 1, "name": name, "id": i + 1} for i, name in enumerate(values)]}
        )
        object_count = max(len(x) for x in values.values())
        self._db_mngr.add_entities(
            {self._db_map: [{"class_id": 1, "name": f"o{i + 1}", "id": i + 1} for i in range(object_count)]}
        )
        db_values = {
            name: [(value, type_) for value, type_ in map(to_database, value_list)]
            for name, value_list in values.items()
        }
        value_items = [
            {
                "entity_class_id": 1,
                "entity_id": (i + 1),
                "parameter_definition_id": param_i + 1,
                "alternative_id": 1,
                "type": type_,
                "value": db_value,
            }
            for param_i, values_and_types in enumerate(db_values.values())
            for i, (db_value, type_) in enumerate(values_and_types)
        ]
        self._db_mngr.add_parameter_values({self._db_map: value_items})

    def _select_object_class_in_tree_view(self):
        object_tree_model = self._db_editor.ui.treeView_entity.model()
        root_index = object_tree_model.index(0, 0)
        if object_tree_model.canFetchMore(root_index):
            object_tree_model.fetchMore(root_index)
        self.assertEqual(object_tree_model.rowCount(root_index), 1)
        class_index = object_tree_model.index(0, 0, root_index)
        refreshing_models = [self._db_editor.parameter_value_model, self._db_editor.parameter_definition_model]
        with multi_signal_waiter([model.refreshed for model in refreshing_models]) as at_filter_refresh:
            self._db_editor.ui.treeView_entity.selectionModel().setCurrentIndex(
                class_index, QItemSelectionModel.ClearAndSelect
            )
            at_filter_refresh.wait()

    def _fill_pivot(self, values):
        self._add_object_parameter_values(values)
        self.assertEqual(self._db_editor.current_input_type, self._db_editor._PARAMETER_VALUE)
        self._select_object_class_in_tree_view()
        with patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as mock_is_visible:
            mock_is_visible.return_value = True
            self._db_editor.do_reload_pivot_table()
        if self._db_editor.pivot_table_model.canFetchMore(QModelIndex()):
            self._db_editor.pivot_table_model.fetchMore(QModelIndex())
        model = self._db_editor.pivot_table_proxy
        object_count = max(len(x) for x in values.values())
        while model.rowCount() != 2 + object_count + 1:
            QApplication.processEvents()

    @staticmethod
    def _select_column(column, model):
        first_data_row = model.sourceModel().headerRowCount()
        data_rows_end = model.sourceModel().rowCount()
        return [model.index(row, column) for row in range(first_data_row, data_rows_end)]

    def test_floats(self):
        self._fill_pivot({"floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        selection = self._select_column(1, model)
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | floats")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "alternative_name")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "floats")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["o1", "o2", "o3"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1])
            self.assertEqual(list(lines[1].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [1.2])
            self.assertEqual(list(lines[2].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [1.3])
        finally:
            plot_widget.deleteLater()

    def test_ints(self):
        self._fill_pivot({"ints": [-3, -1, 2]})
        model = self._db_editor.pivot_table_proxy
        selection = self._select_column(1, model)
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | ints")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "alternative_name")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "ints")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["o1", "o2", "o3"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0])
            self.assertEqual(list(lines[1].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [-1.0])
            self.assertEqual(list(lines[2].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [2.0])
        finally:
            plot_widget.deleteLater()

    def test_time_series(self):
        ts1 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [2.3, 5.0], False, False)
        ts2 = TimeSeriesFixedResolution("2019-07-10T13:00", "20m", [3.3, 4.0], False, False)
        ts3 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [4.3, 3.0], False, False)
        self._fill_pivot({"series": [ts1, ts2, ts3]})
        model = self._db_editor.pivot_table_proxy
        selection = self._select_column(1, model)
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | series | Base")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "t")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "series")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["o1", "o2", "o3"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(
                list(lines[0].get_xdata(orig=True)),
                [numpy.datetime64("2019-07-10T13:00:00"), numpy.datetime64("2019-07-10T13:20:00")],
            )
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [2.3, 5.0])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [3.3, 4.0])
            self.assertEqual(
                list(lines[1].get_xdata(orig=True)),
                [numpy.datetime64("2019-07-10T13:00:00"), numpy.datetime64("2019-07-10T13:20:00")],
            )
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [4.3, 3.0])
            self.assertEqual(
                list(lines[2].get_xdata(orig=True)),
                [numpy.datetime64("2019-07-10T13:00:00"), numpy.datetime64("2019-07-10T13:20:00")],
            )
        finally:
            plot_widget.deleteLater()

    def test_row_filtering(self):
        self._fill_pivot({"floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        id1 = self._db_map.get_entity_item(id=1)["id"]
        id3 = self._db_map.get_entity_item(id=3)["id"]
        model.set_filter("class", {(self._db_map, id1), (self._db_map, id3)})
        selection = self._select_column(1, model)
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | floats")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "alternative_name")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "floats")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["o1", "o3"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1])
            self.assertEqual(list(lines[1].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [1.3])
        finally:
            plot_widget.deleteLater()

    def test_column_filtering(self):
        self._fill_pivot({"floats": [1.1, 1.2, 1.3], "ints": [-3, -1, 2]})
        model = self._db_editor.pivot_table_proxy
        p_id = self._db_map.get_parameter_definition_item(id=2)["id"]
        model.set_filter("parameter", {(self._db_map, p_id)})
        selection = self._select_column(1, model)
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | ints")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "alternative_name")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "ints")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["o1", "o2", "o3"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0])
            self.assertEqual(list(lines[1].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [-1.0])
            self.assertEqual(list(lines[2].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [2.0])
        finally:
            plot_widget.deleteLater()

    def test_multiple_columns_selected_plots_on_two_y_axes(self):
        self._fill_pivot({"ints": [-3, -1, 2], "floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        selected_indexes = [model.index(row, column) for column in range(1, 3) for row in range(2, 5)]
        plot_widget = plot_pivot_table_selection(model, selected_indexes)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "alternative_name")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "floats")
            self.assertTrue(plot_widget.canvas.has_twinned_axes())
            twinned = plot_widget.canvas.twinned_axes()
            self.assertEqual(len(twinned), 1)
            self.assertEqual(twinned[0].get_ylabel(), "ints")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(
                legend_texts, ["floats | o1", "floats | o2", "floats | o3", "ints | o1", "ints | o2", "ints | o3"]
            )
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 3)
            for i in range(3):
                self.assertEqual(list(lines[0].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [1.2])
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [1.3])
            lines = twinned[0].get_lines()
            self.assertEqual(len(lines), 3)
            for i in range(3):
                self.assertEqual(list(lines[0].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [-1.0])
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [2.0])
        finally:
            plot_widget.deleteLater()

    def test_x_column(self):
        self._fill_pivot({"a-ints": [-3, -1, 2], "b-floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        model.sourceModel().set_plot_x_column(2, True)
        selection = self._select_column(1, model)
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | a-ints | Base")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "b-floats")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "a-ints")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["o1", "o2", "o3"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), [1.1])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0])
            self.assertEqual(list(lines[1].get_xdata(orig=True)), [1.2])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [-1.0])
            self.assertEqual(list(lines[2].get_xdata(orig=True)), [1.3])
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [2.0])
        finally:
            plot_widget.deleteLater()

    def test_hidden_x_column_should_disable_it(self):
        self._fill_pivot({"a-ints": [-3, -1, 2], "b-floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        model.sourceModel().set_plot_x_column(2, True)
        p_id = self._db_map.get_parameter_definition_item(id=1)["id"]
        model.set_filter("parameter", {(self._db_map, p_id)})
        selection = self._select_column(1, model)
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | a-ints")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "alternative_name")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "a-ints")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["o1", "o2", "o3"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0])
            self.assertEqual(list(lines[1].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [-1.0])
            self.assertEqual(list(lines[2].get_xdata(orig=True)), ["Base"])
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [2.0])
        finally:
            plot_widget.deleteLater()

    def test_add_to_existing_plot(self):
        ts1 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [2.3, 5.0], False, False)
        ts2 = TimeSeriesFixedResolution("2019-07-10T13:00", "20m", [3.3, 4.0], False, False)
        self._fill_pivot({"series": [ts1, ts2]})
        model = self._db_editor.pivot_table_proxy
        first_data_row = model.sourceModel().headerRowCount()
        selection = [model.index(first_data_row, 1)]
        plot_widget = plot_pivot_table_selection(model, selection)
        selection = [model.index(first_data_row + 1, 1)]
        plot_pivot_table_selection(model, selection, plot_widget)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | series | Base")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "t")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "series")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["o1", "o2"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(
                list(lines[0].get_xdata(orig=True)),
                [numpy.datetime64("2019-07-10T13:00:00"), numpy.datetime64("2019-07-10T13:20:00")],
            )
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [2.3, 5.0])
            self.assertEqual(
                list(lines[1].get_xdata(orig=True)),
                [numpy.datetime64("2019-07-10T13:00:00"), numpy.datetime64("2019-07-10T13:20:00")],
            )
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [3.3, 4.0])
        finally:
            plot_widget.deleteLater()

    def test_incompatible_data_types_on_existing_plot_raises(self):
        ts1 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [2.3, 5.0], False, False)
        self._fill_pivot({"series": [ts1], "floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        first_data_row = model.sourceModel().headerRowCount()
        selection = [model.index(first_data_row, 1)]
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            with self.assertRaises(PlottingError):
                selection = self._select_column(2, model)
                plot_pivot_table_selection(model, selection, plot_widget)
        finally:
            plot_widget.deleteLater()

    def test_simple_map(self):
        """Test that a selection containing a single plain number gets plotted."""
        self._fill_pivot({"maps": [Map(["a", "b"], [-1.1, -2.2])]})
        model = self._db_editor.pivot_table_proxy
        selection = [model.index(2, 1)]
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | maps | o1 | Base")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "x")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "maps")
            self.assertIsNone(plot_widget.canvas.legend_axes.get_legend())
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(list(lines[0].get_xdata(orig=True)), ["a", "b"])
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [-1.1, -2.2])
        finally:
            plot_widget.deleteLater()

    def test_nested_map(self):
        """Test that a selection containing a single plain number gets plotted."""
        self._fill_pivot(
            {
                "maps": [
                    Map(
                        ["a", "b"],
                        [
                            Map([DateTime("2020-11-13T11:00"), DateTime("2020-11-13T12:00")], [-1.1, -2.2]),
                            Map([DateTime("2020-11-13T11:00"), DateTime("2020-11-13T12:00")], [-3.3, -4.4]),
                        ],
                    )
                ]
            }
        )
        model = self._db_editor.pivot_table_proxy
        selection = [model.index(2, 1)]
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | maps | o1 | Base")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "x")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "maps")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(legend_texts, ["a", "b"])
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(
                list(lines[0].get_xdata(orig=True)),
                [numpy.datetime64("2020-11-13T11:00:00"), numpy.datetime64("2020-11-13T12:00:00")],
            )
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [-1.1, -2.2])
            self.assertEqual(
                list(lines[1].get_xdata(orig=True)),
                [numpy.datetime64("2020-11-13T11:00:00"), numpy.datetime64("2020-11-13T12:00:00")],
            )
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [-3.3, -4.4])
        finally:
            plot_widget.deleteLater()

    def test_nested_map_containing_time_series(self):
        """Test that a selection containing a single plain number gets plotted."""
        self._fill_pivot(
            {
                "maps": [
                    Map(
                        ["a", "b"],
                        [
                            Map(
                                [DateTime("2020-11-13T11:00"), DateTime("2020-11-13T12:00")],
                                [
                                    TimeSeriesVariableResolution(
                                        ["2020-11-13T11:00", "2020-11-13T12:00"], [-1.1, -2.2], False, False
                                    ),
                                    TimeSeriesVariableResolution(
                                        ["2020-11-13T12:00", "2020-11-13T13:00"], [-3.3, -4.4], False, False
                                    ),
                                ],
                            ),
                            Map(
                                [DateTime("2020-11-13T11:00"), DateTime("2020-11-13T12:00")],
                                [
                                    TimeSeriesVariableResolution(
                                        ["2020-11-13T11:00", "2020-11-13T12:00"], [-5.5, -6.6], False, False
                                    ),
                                    TimeSeriesVariableResolution(
                                        ["2020-11-13T12:00", "2020-11-13T13:00"], [-7.7, -8.8], False, False
                                    ),
                                ],
                            ),
                        ],
                    )
                ]
            }
        )
        model = self._db_editor.pivot_table_proxy
        selection = [model.index(2, 1)]
        plot_widget = plot_pivot_table_selection(model, selection)
        try:
            self.assertEqual(plot_widget.canvas.axes.get_title(), "TestPlotPivotTableSelection_db | maps | o1 | Base")
            self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "t")
            self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "maps")
            legend = plot_widget.canvas.legend_axes.get_legend()
            legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
            self.assertEqual(
                legend_texts,
                [
                    "a | 2020-11-13T11:00:00",
                    "a | 2020-11-13T12:00:00",
                    "b | 2020-11-13T11:00:00",
                    "b | 2020-11-13T12:00:00",
                ],
            )
            lines = plot_widget.canvas.axes.get_lines()
            self.assertEqual(len(lines), 4)
            self.assertEqual(
                list(lines[0].get_xdata(orig=True)),
                [numpy.datetime64("2020-11-13T11:00:00"), numpy.datetime64("2020-11-13T12:00:00")],
            )
            self.assertEqual(list(lines[0].get_ydata(orig=True)), [-1.1, -2.2])
            self.assertEqual(
                list(lines[1].get_xdata(orig=True)),
                [numpy.datetime64("2020-11-13T12:00:00"), numpy.datetime64("2020-11-13T13:00:00")],
            )
            self.assertEqual(list(lines[1].get_ydata(orig=True)), [-3.3, -4.4])
            self.assertEqual(
                list(lines[2].get_xdata(orig=True)),
                [numpy.datetime64("2020-11-13T11:00:00"), numpy.datetime64("2020-11-13T12:00:00")],
            )
            self.assertEqual(list(lines[2].get_ydata(orig=True)), [-5.5, -6.6])
            self.assertEqual(
                list(lines[3].get_xdata(orig=True)),
                [numpy.datetime64("2020-11-13T12:00:00"), numpy.datetime64("2020-11-13T13:00:00")],
            )
            self.assertEqual(list(lines[3].get_ydata(orig=True)), [-7.7, -8.8])
        finally:
            plot_widget.deleteLater()


class TestConvertIndexedValueToTree(unittest.TestCase):
    def test_time_pattern(self):
        pattern = TimePattern(["D1-3", "D4-7"], [1.1, 2.2], index_name="weekdays")
        node = convert_indexed_value_to_tree(pattern)
        self.assertEqual(node.label, "weekdays")
        self.assertEqual(node.content, {"D1-3": 1.1, "D4-7": 2.2})

    def test_time_series_fixed_resolution(self):
        time_series = TimeSeriesFixedResolution(
            "2022-09-26T09:00", "3h", [1.1, 2.2], False, False, index_name="my_index"
        )
        node = convert_indexed_value_to_tree(time_series)
        self.assertEqual(node.label, "my_index")
        self.assertEqual(
            node.content, {numpy.datetime64("2022-09-26T09:00:00"): 1.1, numpy.datetime64("2022-09-26T12:00:00"): 2.2}
        )

    def test_time_series_variable_resolution(self):
        time_series = TimeSeriesVariableResolution(
            ["2022-09-26T09:00", "2022-09-26T12:00"], [1.1, 2.2], False, False, index_name="my_index"
        )
        node = convert_indexed_value_to_tree(time_series)
        self.assertEqual(node.label, "my_index")
        self.assertEqual(
            node.content, {numpy.datetime64("2022-09-26T09:00:00"): 1.1, numpy.datetime64("2022-09-26T12:00:00"): 2.2}
        )

    def test_array(self):
        array = Array([1.1, 2.2], index_name="my_zero_based_index")
        node = convert_indexed_value_to_tree(array)
        self.assertEqual(node.label, "my_zero_based_index")
        self.assertEqual(node.content, {0: 1.1, 1: 2.2})

    def test_map_1d(self):
        map_value = Map(["a", "b"], [1.1, 2.2], index_name="root_index")
        node = convert_indexed_value_to_tree(map_value)
        self.assertEqual(node.label, "root_index")
        self.assertEqual(node.content, {"a": 1.1, "b": 2.2})

    def test_map_2d(self):
        map1 = Map([1, 2], [1.1, 2.2], index_name="map1_index")
        map2 = Map([3, 4], [3.3, 4.4], index_name="map2_index")
        map_value = Map(["a", "b"], [map1, map2], index_name="root_index")
        node = convert_indexed_value_to_tree(map_value)
        self.assertEqual(node.label, "root_index")
        expected_map1_tree = TreeNode("map1_index")
        expected_map1_tree.content = {1: 1.1, 2: 2.2}
        expected_map2_tree = TreeNode("map2_index")
        expected_map2_tree.content = {3: 3.3, 4: 4.4}
        self.assertEqual(node.content, {"a": expected_map1_tree, "b": expected_map2_tree})

    def test_map_mixed_dimensions(self):
        map1 = Map([1, 2], [1.1, 2.2], index_name="map1_index")
        map_value = Map(["a", "b"], [map1, 3.3], index_name="root_index")
        node = convert_indexed_value_to_tree(map_value)
        self.assertEqual(node.label, "root_index")
        expected_map1_tree = TreeNode("map1_index")
        expected_map1_tree.content = {1: 1.1, 2: 2.2}
        self.assertEqual(node.content, {"a": expected_map1_tree, "b": 3.3})


class TestTurnNodesToXYData(unittest.TestCase):
    def test_shallow_tree(self):
        node = TreeNode("my_index")
        node.content = {1: 1.1, 2: 2.2}
        xy_data = list(turn_node_to_xy_data(node, None))
        expected = [XYData([1, 2], [1.1, 2.2], IndexName("my_index", 0), "", [], [])]
        self.assertEqual(xy_data, expected)

    def test_one_index_deep_tree(self):
        node1 = TreeNode("index_1")
        node1.content = {1: 1.1, 2: 2.2}
        node2 = TreeNode("index_2")
        node2.content = {3: 3.3, 4: 4.4}
        root = TreeNode("root_index")
        root.content = {"a": node1, "b": node2}
        xy_data = list(turn_node_to_xy_data(root, None))
        expected = [
            XYData([1, 2], [1.1, 2.2], IndexName("index_1", 1), "", ["a"], [IndexName("root_index", 0)]),
            XYData([3, 4], [3.3, 4.4], IndexName("index_2", 1), "", ["b"], [IndexName("root_index", 0)]),
        ]
        self.assertEqual(xy_data, expected)

    def test_variable_depth_tree(self):
        node1 = TreeNode("index_1")
        node1.content = {1: 1.1, 2: 2.2}
        root = TreeNode("root_index")
        root.content = {"a": node1, 3: 3.3, 4: 4.4}
        xy_data = list(turn_node_to_xy_data(root, None))
        expected = [
            XYData([1, 2], [1.1, 2.2], IndexName("index_1", 1), "", ["a"], [IndexName("root_index", 0)]),
            XYData([3, 4], [3.3, 4.4], IndexName("root_index", 0), "", [], []),
        ]
        self.assertEqual(xy_data, expected)

    def test_take_index_as_y_label(self):
        node1 = TreeNode("index_1")
        node1.content = {1: 1.1, 2: 2.2}
        node2 = TreeNode("index_2")
        node2.content = {3: 3.3, 4: 4.4}
        node3 = TreeNode("index_3")
        node3.content = {5: 5.5, 6: 6.6}
        label_node1 = TreeNode("Y label 1")
        label_node1.content = {"to the top": node1, "upwards": node2}
        label_node2 = TreeNode("Y label 2")
        label_node2.content = {"ascent": node3}
        root = TreeNode("root_index")
        root.content = {"a": label_node1, "b": label_node2}
        xy_data = list(turn_node_to_xy_data(root, 1))
        expected = [
            XYData(
                [1, 2],
                [1.1, 2.2],
                IndexName("index_1", 2),
                "to the top",
                ["a", "to the top"],
                [IndexName("root_index", 0), IndexName("Y label 1", 1)],
            ),
            XYData(
                [3, 4],
                [3.3, 4.4],
                IndexName("index_2", 2),
                "upwards",
                ["a", "upwards"],
                [IndexName("root_index", 0), IndexName("Y label 1", 1)],
            ),
            XYData(
                [5, 6],
                [5.5, 6.6],
                IndexName("index_3", 2),
                "ascent",
                ["b", "ascent"],
                [IndexName("root_index", 0), IndexName("Y label 2", 1)],
            ),
        ]
        self.assertEqual(xy_data, expected)


class TestReduceIndexes(unittest.TestCase):
    def test_single_shallow_xy_data(self):
        data = [XYData([1, 2], [1.1, 2.2], IndexName("my_index", 0), "", [], [])]
        reduced_data, common_indexes = reduce_indexes(data)
        expected = [XYData([1, 2], [1.1, 2.2], IndexName("my_index", 0), "", [], [])]
        self.assertEqual(reduced_data, expected)
        self.assertEqual(common_indexes, [])

    def test_all_indexes_shared(self):
        data = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index_1", 1), "", ["my_index"], [IndexName("index name", 0)]),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index_2", 1), "", ["my_index"], [IndexName("index name", 0)]),
        ]
        reduced_data, common_indexes = reduce_indexes(data)
        expected = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index_1", 1), "", [], []),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index_2", 1), "", [], []),
        ]
        self.assertEqual(reduced_data, expected)
        self.assertEqual(common_indexes, ["my_index"])

    def test_uneven_depth(self):
        data = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index_1", 1), "", ["shared_1"], [IndexName("shared index", 0)]),
            XYData(
                [3, 4],
                [3.3, 4.4],
                IndexName("x_index_2", 2),
                "",
                ["shared_1", "extra"],
                [IndexName("shared index", 0), IndexName("goes deeper", 1)],
            ),
        ]
        reduced_data, common_indexes = reduce_indexes(data)
        expected = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index_1", 1), "", [], []),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index_2", 2), "", ["extra"], [IndexName("goes deeper", 1)]),
        ]
        self.assertEqual(reduced_data, expected)
        self.assertEqual(common_indexes, ["shared_1"])

    def test_first_index_not_shared(self):
        data = [
            XYData(
                [1, 2],
                [1.1, 2.2],
                IndexName("x_index_1", 2),
                "",
                ["different_1", "shared"],
                [IndexName("my_index_1", 0), IndexName("shared index", 1)],
            ),
            XYData(
                [3, 4],
                [3.3, 4.4],
                IndexName("x_index_2", 2),
                "",
                ["different_2", "shared"],
                [IndexName("my_index_2", 0), IndexName("shared index", 1)],
            ),
        ]
        reduced_data, common_indexes = reduce_indexes(data)
        expected = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index_1", 2), "", ["different_1"], [IndexName("my_index_1", 0)]),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index_2", 2), "", ["different_2"], [IndexName("my_index_2", 0)]),
        ]
        self.assertEqual(reduced_data, expected)
        self.assertEqual(common_indexes, ["shared"])


class TestCombineDataWithSameIndexes(unittest.TestCase):
    def test_not_combined_due_to_different_x_labels(self):
        data = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index_1", 0), "", [], []),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index_2", 0), "", [], []),
        ]
        combined = combine_data_with_same_indexes(data)
        expected = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index_1", 0), "", [], []),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index_2", 0), "", [], []),
        ]
        self.assertEqual(combined, expected)

    def test_not_combined_due_to_different_indexes(self):
        data = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index", 1), "", ["index_1"], [IndexName("index name", 0)]),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index", 1), "", ["index_2"], [IndexName("index name", 0)]),
        ]
        combined = combine_data_with_same_indexes(data)
        expected = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index", 1), "", ["index_1"], [IndexName("index name", 0)]),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index", 1), "", ["index_2"], [IndexName("index name", 0)]),
        ]
        self.assertEqual(combined, expected)

    def test_same_x_axes_combined(self):
        data = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index", 0), "", [], []),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index", 0), "", [], []),
        ]
        combined = combine_data_with_same_indexes(data)
        expected = [XYData([1, 2, 3, 4], [1.1, 2.2, 3.3, 4.4], IndexName("x_index", 0), "", [], [])]
        self.assertEqual(combined, expected)

    def test_all_same_indexes_combined(self):
        data = [
            XYData([1, 2], [1.1, 2.2], IndexName("x_index", 1), "", ["index_1"], [IndexName("index name", 0)]),
            XYData([3, 4], [3.3, 4.4], IndexName("x_index", 1), "", ["index_1"], [IndexName("index name", 0)]),
        ]
        combined = combine_data_with_same_indexes(data)
        expected = [
            XYData(
                [1, 2, 3, 4],
                [1.1, 2.2, 3.3, 4.4],
                IndexName("x_index", 1),
                "",
                ["index_1"],
                [IndexName("index name", 0)],
            )
        ]
        self.assertEqual(combined, expected)


class TestPlotData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_nothing_to_plot(self):
        plot_widget = plot_data([])
        self.assertEqual(len(plot_widget.canvas.axes.lines), 0)

    def test_single_plot(self):
        data = [XYData([-11, -22], [1.1, 2.2], IndexName("x_index", 1), "y", ["index_1"], [IndexName("index name", 0)])]
        plot_widget = plot_data(data)
        lines = plot_widget.canvas.axes.lines
        self.assertEqual(plot_widget.canvas.axes.get_title(), "index_1")
        self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "x_index", 1)
        self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "y")
        self.assertIsNone(plot_widget.canvas.legend_axes.get_legend())
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_xdata(orig=True)), [-11, -22])
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1, 2.2])

    def test_two_plots_with_shared_and_individual_indexes(self):
        data = [XYData([-11, -22], [1.1, 2.2], IndexName("x_index", 1), "y", ["index_1"], [IndexName("index name", 0)])]
        plot_widget = plot_data(data)
        lines = plot_widget.canvas.axes.lines
        self.assertEqual(plot_widget.canvas.axes.get_title(), "index_1")
        self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "x_index")
        self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "y")
        self.assertIsNone(plot_widget.canvas.legend_axes.get_legend())
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_xdata(orig=True)), [-11, -22])
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1, 2.2])

    def test_two_time_series_plots(self):
        data = [
            XYData(
                [numpy.datetime64("2022-11-18T16:00:00"), numpy.datetime64("2022-11-18T17:00:00")],
                [1.1, 2.2],
                IndexName("time", 1),
                "y",
                ["index_1"],
                [IndexName("index name", 0)],
            ),
            XYData(
                [numpy.datetime64("2022-11-18T16:00:00"), numpy.datetime64("2022-11-18T17:00:00")],
                [3.3, 4.4],
                IndexName("time", 1),
                "y",
                ["index_2"],
                [IndexName("index name", 0)],
            ),
        ]
        plot_widget = plot_data(data)
        self.assertFalse(plot_widget.canvas.has_twinned_axes())
        self.assertEqual(plot_widget.canvas.axes.get_title(), "")
        self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "time")
        self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "y")
        legend = plot_widget.canvas.legend_axes.get_legend()
        legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
        self.assertEqual(legend_texts, ["index_1", "index_2"])
        lines = plot_widget.canvas.axes.lines
        self.assertEqual(len(lines), 2)
        expected_x = [numpy.datetime64("2022-11-18T16:00:00"), numpy.datetime64("2022-11-18T17:00:00")]
        self.assertEqual(list(lines[0].get_xdata(orig=True)), expected_x)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1, 2.2])
        self.assertEqual(list(lines[1].get_xdata(orig=True)), expected_x)
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [3.3, 4.4])

    def test_we_find_unsqueezed_index_no_matter_what(self):
        data = [
            XYData(
                x=["t1", "t2"],
                y=[13.0, 7.0],
                x_label=IndexName("x", 1),
                y_label="y",
                data_index=["A1"],
                index_names=[IndexName("idx", 0)],
            ),
            XYData(
                x=["B1", "B2"], y=[-13.0, -7.0], x_label=IndexName("x", 1), y_label="y", data_index=[], index_names=[]
            ),
        ]
        plot_widget = plot_data(data)
        self.assertEqual(plot_widget.canvas.axes.get_title(), "")
        self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "x")
        self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "y")
        legend = plot_widget.canvas.legend_axes.get_legend()
        legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
        self.assertEqual(legend_texts, ["<root> | A1", "<root>"])
        lines = plot_widget.canvas.axes.lines
        self.assertEqual(len(lines), 2)
        self.assertEqual(list(lines[0].get_xdata(orig=True)), ["t1", "t2"])
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [13.0, 7.0])
        self.assertEqual(list(lines[1].get_xdata(orig=True)), ["B1", "B2"])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [-13.0, -7.0])

    def test_y_axis_is_not_labeled_when_more_than_two_labels_are_possible(self):
        data = [
            XYData(
                x=["t1", "t2"],
                y=[1.1, 2.2],
                x_label=IndexName("x", 1),
                y_label="y",
                data_index=["A1"],
                index_names=[IndexName("idx", 0)],
            ),
            XYData(
                x=["t1", "t2"],
                y=[3.3, 4.4],
                x_label=IndexName("x", 1),
                y_label="z",
                data_index=["B1", "b1"],
                index_names=[IndexName("jdx", 0), IndexName("kdx", 1)],
            ),
            XYData(x=["t1", "t2"], y=[5.5, 6.6], x_label=IndexName("x", 0), y_label="a", data_index=[], index_names=[]),
        ]
        plot_widget = plot_data(data)
        self.assertFalse(plot_widget.canvas.has_twinned_axes())
        self.assertEqual(plot_widget.canvas.axes.get_title(), "")
        self.assertEqual(plot_widget.canvas.axes.get_xlabel(), "x")
        self.assertEqual(plot_widget.canvas.axes.get_ylabel(), "")
        legend = plot_widget.canvas.legend_axes.get_legend()
        legend_texts = [text_patch.get_text() for text_patch in legend.get_texts()]
        self.assertEqual(legend_texts, ["<root> | A1", "<root> | B1 | b1", "<root>"])
        lines = plot_widget.canvas.axes.lines
        self.assertEqual(len(lines), 3)
        self.assertEqual(list(lines[0].get_xdata(orig=True)), ["t1", "t2"])
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1, 2.2])
        self.assertEqual(list(lines[1].get_xdata(orig=True)), ["t1", "t2"])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [3.3, 4.4])
        self.assertEqual(list(lines[2].get_xdata(orig=True)), ["t1", "t2"])
        self.assertEqual(list(lines[2].get_ydata(orig=True)), [5.5, 6.6])

    def test_legend_placement_below_threshold(self):
        data = [
            XYData(x=["x"], y=[1.0], x_label=IndexName("x", 0), y_label="", data_index=[], index_names=[])
            for _ in range(LEGEND_PLACEMENT_THRESHOLD - 1)
        ]
        plot_widget = plot_data(data)
        self.assertEqual(
            repr(plot_widget.canvas.legend_axes.get_gridspec()), repr(GridSpec(2, 1, height_ratios=[1, 0]))
        )

    def test_legend_placement_above_threshold(self):
        data = [
            XYData(x=["x"], y=[1.0], x_label=IndexName("x", 0), y_label="", data_index=[], index_names=[])
            for _ in range(LEGEND_PLACEMENT_THRESHOLD)
        ]
        plot_widget = plot_data(data)
        self.assertEqual(repr(plot_widget.canvas.legend_axes.get_gridspec()), repr(GridSpec(1, 2, width_ratios=[1, 0])))


class TestRaiseIfIncompatibleX(unittest.TestCase):
    def test_data_with_numeric_and_string_x_data_raises(self):
        data_list = [
            XYData(
                x=[1.0, 2.0, 3.0],
                y=[5.0, 2.0, -1.0],
                x_label=IndexName("x", 0),
                y_label="",
                data_index=["1d_map"],
                index_names=[IndexName("parameter_name", 0)],
            ),
            XYData(
                x=["t1", "t2"],
                y=[13.0, 7.0],
                x_label=IndexName("x", 2),
                y_label="",
                data_index=["uneven_map", "A1"],
                index_names=[IndexName("parameter_name", 0), IndexName("x", 1)],
            ),
        ]
        self.assertRaises(PlottingError, raise_if_incompatible_x, data_list)


class TestAddRowToException(unittest.TestCase):
    def test_exception_message_formatted_correctly(self):
        row = 23

        def display_row(r):
            self.assertEqual(r, row)
            return 99

        with self.assertRaises(PlottingError) as context_manager:
            with add_row_to_exception(row, display_row):
                raise PlottingError("detailed error message")
        self.assertEqual(str(context_manager.exception), "Failed to plot row 99: detailed error message")


class MultiSignalWaiter(QObject):
    """A 'traffic light' that allows waiting for a set number of signals to be emitted in another thread."""

    def __init__(self, count):
        super().__init__()
        self._expected = count
        self._trigger_count = 0
        self.args = ()

    def trigger(self, *args):
        """Signal receiving slot."""
        self._trigger_count += 1
        self.args = args

    def wait(self):
        """Wait for signal to be received."""
        while self._trigger_count < self._expected:
            QApplication.processEvents()


@contextmanager
def multi_signal_waiter(signals):
    waiter = MultiSignalWaiter(len(signals))
    for signal in signals:
        signal.connect(waiter.trigger)
    try:
        yield waiter
    finally:
        for signal in signals:
            signal.disconnect(waiter.trigger)
        waiter.deleteLater()


if __name__ == "__main__":
    unittest.main()
