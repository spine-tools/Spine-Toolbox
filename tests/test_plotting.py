######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

:author: A. Soininen (VTT)
:date:   10.7.2019
"""

import unittest
from contextlib import contextmanager
from unittest.mock import Mock, MagicMock, patch
from PySide2.QtCore import QModelIndex, QItemSelectionModel, QObject
from PySide2.QtWidgets import QApplication, QMessageBox

from spinedb_api import DateTime, Map, TimeSeries, TimeSeriesVariableResolution, to_database, TimeSeriesFixedResolution
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.plotting import (
    add_map_plot,
    add_time_series_plot,
    plot_pivot_column,
    plot_selection,
    PlottingError,
    ParameterTablePlottingHints,
    PivotTablePlottingHints,
)
from spinetoolbox.widgets.plot_widget import PlotWidget
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor


class TestPlotting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = SpineDBManager(mock_settings, None)
            logger = MagicMock()
            self._db_map = self._db_mngr.get_db_map("sqlite:///", logger, codename="database", create=True)
            self._db_editor = SpineDBEditor(self._db_mngr, {"sqlite:///": "database"})

    def tearDown(self):
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.QMessageBox") as message_box:
            message_box.exec_.return_value = QMessageBox.Ok
            with signal_waiter(self._db_mngr.session_rolled_back) as waiter:
                self._db_editor.rollback_session()
                if message_box.exec_.call_count > 0:
                    waiter.wait()
        with patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"), patch(
            "spinetoolbox.spine_db_manager.QMessageBox"
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._db_editor = None

    def _add_object_parameter_values(self, values):
        self._db_mngr.add_object_classes({self._db_map: [{"name": "class"}]})
        self._db_mngr.add_parameter_definitions(
            {self._db_map: [{"entity_class_id": 1, "name": name} for name in values]}
        )
        object_count = max(len(x) for x in values.values())
        self._db_mngr.add_objects({self._db_map: [{"class_id": 1, "name": f"o{i + 1}"} for i in range(object_count)]})
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
        with signal_waiter(self._db_mngr.parameter_values_added) as waiter:
            self._db_mngr.add_parameter_values({self._db_map: value_items})
            waiter.wait()

    def _select_object_class_in_tree_view(self):
        object_tree_model = self._db_editor.ui.treeView_object.model()
        root_index = object_tree_model.index(0, 0)
        self.assertEqual(object_tree_model.rowCount(root_index), 1)
        class_index = object_tree_model.index(0, 0, root_index)
        refreshing_models = list(self._db_editor._parameter_models) + list(self._db_editor._parameter_value_models)
        with multi_signal_waiter([model.refreshed for model in refreshing_models]) as at_filter_refresh:
            self._db_editor.ui.treeView_object.selectionModel().setCurrentIndex(
                class_index, QItemSelectionModel.ClearAndSelect
            )
            at_filter_refresh.wait()

    def _fill_pivot(self, values):
        self._add_object_parameter_values(values)
        self.assertEqual(self._db_editor.current_input_type, self._db_editor._PARAMETER_VALUE)
        self._select_object_class_in_tree_view()
        self._db_editor.do_reload_pivot_table()
        self._db_editor.pivot_table_model.fetchMore(QModelIndex())
        model = self._db_editor.pivot_table_proxy
        object_count = max(len(x) for x in values.values())
        while model.rowCount() != 2 + object_count + 1:
            QApplication.processEvents()

    def _fill_parameter_value_table(self, values):
        self._add_object_parameter_values(values)
        self._select_object_class_in_tree_view()

    def test_plot_pivot_column_float_type(self):
        self._fill_pivot({"floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1, 1.2, 1.3])

    def test_plot_pivot_column_int_type(self):
        self._fill_pivot({"ints": [-3, -1, 2]})
        model = self._db_editor.pivot_table_proxy
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])

    def test_plot_pivot_column_time_series_type(self):
        ts1 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [2.3, 5.0], False, False)
        ts2 = TimeSeriesFixedResolution("2019-07-10T13:00", "20m", [3.3, 4.0], False, False)
        ts3 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [4.3, 3.0], False, False)
        self._fill_pivot({"series": [ts1, ts2, ts3]})
        model = self._db_editor.pivot_table_proxy
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [2.3, 5.0])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [3.3, 4.0])
        self.assertEqual(list(lines[2].get_ydata(orig=True)), [4.3, 3.0])

    def test_plot_pivot_column_with_row_filtering(self):
        self._fill_pivot({"floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        model.set_filter("class", {(self._db_map, 1), (self._db_map, 3)})
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1, 1.3])

    def test_plot_pivot_column_with_column_filtering(self):
        self._fill_pivot({"floats": [1.1, 1.2, 1.3], "ints": [-3, -1, 2]})
        model = self._db_editor.pivot_table_proxy
        model.set_filter("parameter", {(self._db_map, 2)})
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])

    def test_plot_pivot_selection(self):
        self._fill_pivot({"ints": [-3, -1, 2], "floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        selected_indexes = list()
        for row in range(2, 5):
            for column in range(1, 3):
                selected_indexes.append(model.index(row, column))
        support = PivotTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [1.1, 1.2, 1.3])

    def test_plot_pivot_column_with_x_column(self):
        self._fill_pivot({"ints": [-3, -1, 2], "floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        model.sourceModel().set_plot_x_column(2, True)
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_xdata(orig=True)), [1.1, 1.2, 1.3])
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])

    def test_plot_pivot_column_when_x_column_hidden(self):
        self._fill_pivot({"ints": [-3, -1, 2], "floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        model.sourceModel().set_plot_x_column(1, True)
        model.set_filter("parameter", {(self._db_map, 1)})
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_xdata(orig=True)), [1.0, 2.0, 3.0])
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])

    def test_plot_pivot_column_on_existing_plot(self):
        ts1 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [2.3, 5.0], False, False)
        ts2 = TimeSeriesFixedResolution("2019-07-10T13:00", "20m", [3.3, 4.0], False, False)
        ts3 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [4.3, 3.0], False, False)
        self._fill_pivot({"series": [ts1, ts2, ts3]})
        model = self._db_editor.pivot_table_proxy
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        plot_pivot_column(model, 1, support, plot_widget)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 6)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [2.3, 5.0])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [3.3, 4.0])
        self.assertEqual(list(lines[2].get_ydata(orig=True)), [4.3, 3.0])
        self.assertEqual(list(lines[3].get_ydata(orig=True)), [2.3, 5.0])
        self.assertEqual(list(lines[4].get_ydata(orig=True)), [3.3, 4.0])
        self.assertEqual(list(lines[5].get_ydata(orig=True)), [4.3, 3.0])

    def test_plot_pivot_column_incompatible_data_types_on_existing_plot_raises(self):
        ts1 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [2.3, 5.0], False, False)
        ts2 = TimeSeriesFixedResolution("2019-07-10T13:00", "20m", [3.3, 4.0], False, False)
        ts3 = TimeSeriesVariableResolution(["2019-07-10T13:00", "2019-07-10T13:20"], [4.3, 3.0], False, False)
        self._fill_pivot({"series": [ts1, ts2, ts3], "floats": [1.1, 1.2, 1.3]})
        model = self._db_editor.pivot_table_proxy
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        with self.assertRaises(PlottingError):
            plot_pivot_column(model, 2, support, plot_widget)

    def test_plot_tree_view_selection_of_floats(self):
        self._fill_parameter_value_table({"floats": [-2.3, -0.5]})
        model = self._db_editor.object_parameter_value_model
        selected_indexes = list()
        selected_indexes.append(model.index(0, 4))
        selected_indexes.append(model.index(1, 4))
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-2.3, -0.5])

    def test_plot_tree_view_selection_of_time_series(self):
        ts1 = TimeSeriesFixedResolution("2019-07-11T09:00", "3 days", [0.5, 2.3], False, False)
        ts2 = TimeSeriesVariableResolution(["2019-07-11T09:00", "2019-07-17T10:35"], [-5.0, -3.3], False, False)
        self._fill_parameter_value_table({"time_series": [ts1, ts2]})
        model = self._db_editor.object_parameter_value_model
        selected_indexes = list()
        selected_indexes.append(model.index(0, 4))
        selected_indexes.append(model.index(1, 4))
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [0.5, 2.3])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [-5.0, -3.3])

    def test_plot_tree_view_selection_into_existing_plot(self):
        ts1 = TimeSeriesFixedResolution("2019-07-11T09:00", "3 days", [0.5, 2.3], False, False)
        ts2 = TimeSeriesVariableResolution(["2019-07-11T09:00", "2019-07-17T10:35"], [-5.0, -3.3], False, False)
        self._fill_parameter_value_table({"time_series": [ts1, ts2]})
        model = self._db_editor.object_parameter_value_model
        selected_indexes = [model.index(0, 4)]
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        selected_indexes = [model.index(1, 4)]
        plot_selection(model, selected_indexes, support, plot_widget)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [0.5, 2.3])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [-5.0, -3.3])

    def test_plot_tree_view_selection_raises_with_mixed_data(self):
        ts1 = TimeSeriesFixedResolution("2019-07-11T09:00", "3 days", [0.5, 2.3], False, False)
        self._fill_parameter_value_table({"time_series": [ts1], "floats": [2.3, 5.5]})
        model = self._db_editor.object_parameter_value_model
        selected_indexes = [model.index(row, 4) for row in range(3)]
        support = ParameterTablePlottingHints()
        with self.assertRaises(PlottingError):
            plot_selection(model, selected_indexes, support)

    def test_plot_tree_view_selection_into_existing_plot_with_mixed_data_raises(self):
        ts1 = TimeSeriesFixedResolution("2019-07-11T09:00", "3 days", [0.5, 2.3], False, False)
        self._fill_parameter_value_table({"time_series": [ts1], "floats": [2.3, 5.5]})
        model = self._db_editor.object_parameter_value_model
        selected_indexes = [model.index(0, 4)]
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        selected_indexes = [model.index(1, 4), model.index(2, 4)]
        with self.assertRaises(PlottingError):
            plot_selection(model, selected_indexes, support, plot_widget)

    def test_plot_single_plain_number(self):
        """Test that a selection containing a single plain number gets plotted."""
        self._fill_parameter_value_table({"float": [5.0]})
        model = self._db_editor.object_parameter_value_model
        selected_indexes = list()
        selected_indexes.append(model.index(0, 4))
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [5.0])

    def test_plot_simple_map(self):
        """Test that a selection containing a single plain number gets plotted."""
        self._fill_pivot({"maps": [Map(["a", "b"], [-1.1, -2.2])]})
        model = self._db_editor.pivot_table_proxy
        support = PivotTablePlottingHints()
        plot_widget = plot_selection(model, [model.index(2, 1)], support)
        self.assertEqual(plot_widget.plot_type, Map)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-1.1, -2.2])

    def test_plot_nested_map(self):
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
        support = PivotTablePlottingHints()
        plot_widget = plot_selection(model, [model.index(2, 1)], support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-1.1, -2.2])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [-3.3, -4.4])

    def test_plot_nested_map_containing_time_series(self):
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
        support = PivotTablePlottingHints()
        plot_widget = plot_selection(model, [model.index(2, 1)], support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-1.1, -2.2])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [-3.3, -4.4])
        self.assertEqual(list(lines[2].get_ydata(orig=True)), [-5.5, -6.6])
        self.assertEqual(list(lines[3].get_ydata(orig=True)), [-7.7, -8.8])

    def test_add_dictionary_plot(self):
        plot_widget = PlotWidget()
        dictionary = Map(["key 1 ", "key 2"], [2.3, 5.5])
        add_map_plot(plot_widget, dictionary)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [2.3, 5.5])

    def test_add_time_series_plot(self):
        plot_widget = PlotWidget()
        time_series = TimeSeriesVariableResolution(["1917-12-06", "2017-12-06"], [0.0, 100.0], False, False)
        add_time_series_plot(plot_widget, time_series)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [0.0, 100.0])


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


if __name__ == '__main__':
    unittest.main()
