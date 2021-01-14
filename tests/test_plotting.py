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
from unittest.mock import Mock, MagicMock, PropertyMock, patch
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtWidgets import QApplication, QAction
from spinedb_api import DateTime, from_database, Map, TimeSeries, TimeSeriesVariableResolution, to_database
from spinetoolbox.mvcmodels.shared import PARSED_ROLE
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
from spinetoolbox.spine_db_editor.mvcmodels.pivot_table_models import ParameterValuePivotTableModel

db = Mock()


def _make_pivot_proxy_model():
    """Returns a prefilled PivotTableModel."""
    db_mngr = MagicMock()
    db_mngr.get_value.side_effect = lambda db_map, item_type, id_, role: from_database(id_)
    mock_db_map = MagicMock()
    mock_db_map.codename = "codename"
    db_mngr.undo_action.__getitem__.side_effect = lambda key: QAction()
    db_mngr.redo_action.__getitem__.side_effect = lambda key: QAction()
    with patch.object(SpineDBEditor, "restore_ui"), patch.object(SpineDBEditor, "show"):
        spine_db_editor = SpineDBEditor(db_mngr, mock_db_map)
    spine_db_editor.create_header_widget = lambda *args, **kwargs: None
    simple_map = Map(["a", "b"], [-1.1, -2.2])
    nested_map = Map(
        ["a", "b"],
        [
            Map([DateTime("2020-11-13T11:00"), DateTime("2020-11-13T12:00")], [-1.1, -2.2]),
            Map([DateTime("2020-11-13T11:00"), DateTime("2020-11-13T12:00")], [-3.3, -4.4]),
        ],
    )
    nested_map_with_time_series = Map(
        ["a", "b"],
        [
            Map(
                [DateTime("2020-11-13T11:00"), DateTime("2020-11-13T12:00")],
                [
                    TimeSeriesVariableResolution(["2020-11-13T11:00", "2020-11-13T12:00"], [-1.1, -2.2], False, False),
                    TimeSeriesVariableResolution(["2020-11-13T12:00", "2020-11-13T13:00"], [-3.3, -4.4], False, False),
                ],
            ),
            Map(
                [DateTime("2020-11-13T11:00"), DateTime("2020-11-13T12:00")],
                [
                    TimeSeriesVariableResolution(["2020-11-13T11:00", "2020-11-13T12:00"], [-5.5, -6.6], False, False),
                    TimeSeriesVariableResolution(["2020-11-13T12:00", "2020-11-13T13:00"], [-7.7, -8.8], False, False),
                ],
            ),
        ],
    )
    data = {
        ('1', 'int_col', 'base_alternative'): '-3',
        ('2', 'int_col', 'base_alternative'): '-1',
        ('3', 'int_col', 'base_alternative'): '2',
        ('1', 'float_col', 'base_alternative'): '1.1',
        ('2', 'float_col', 'base_alternative'): '1.2',
        ('3', 'float_col', 'base_alternative'): '1.3',
        (
            '1',
            'time_series_col',
            'base_alternative',
        ): '{"type": "time_series", "data": {"2019-07-10T13:00": 2.3, "2019-07-10T13:20": 5.0}}',
        (
            '2',
            'time_series_col',
            'base_alternative',
        ): '{"type": "time_series", "index": {"start": "2019-07-10T13:00", "resolution": "20 minutes"}, "data": [3.3, 4.0]}',
        (
            '3',
            'time_series_col',
            'base_alternative',
        ): '{"type": "time_series", "data": {"2019-07-10T13:00": 4.3, "2019-07-10T13:20": 3.0}}',
        ("1", "map_col", "base_alternative"): to_database(simple_map),
        ("2", "map_col", "base_alternative"): to_database(nested_map),
        ("3", "map_col", "base_alternative"): to_database(nested_map_with_time_series),
    }
    data = {tuple((db, k) for k in key) + (db,): (db, value) for key, value in data.items()}
    spine_db_editor.load_parameter_value_data = lambda: data
    spine_db_editor.pivot_table_model = model = ParameterValuePivotTableModel(spine_db_editor)
    with patch.object(
        SpineDBEditor, "current_object_class_ids", new_callable=PropertyMock
    ) as mock_current_object_class_ids:
        mock_current_object_class_ids.return_value = {"object": {db: 1}}
        model.call_reset_model(pivot=(['object'], ['parameter', 'alternative'], ['database'], (db,)))
    model.start_fetching()
    spine_db_editor.pivot_table_model = model
    spine_db_editor.pivot_table_proxy.setSourceModel(model)
    return spine_db_editor.pivot_table_proxy


class _MockParameterModel(QAbstractTableModel):
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
        if role != PARSED_ROLE:
            return None
        return from_database(self._table[index.row()][index.column()])

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        return "value"

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        self._table[index.row()][index.column()] = value
        return True

    def index_name(self, index):  # pylint: disable=no-self-use
        return "entity - parameter"


class TestPlotting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_plot_pivot_column_float_type(self):
        model = _make_pivot_proxy_model()
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 2, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1, 1.2, 1.3])

    def test_plot_pivot_column_int_type(self):
        model = _make_pivot_proxy_model()
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])

    def test_plot_pivot_column_time_series_type(self):
        model = _make_pivot_proxy_model()
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 3, support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [2.3, 5.0])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [3.3, 4.0])
        self.assertEqual(list(lines[2].get_ydata(orig=True)), [4.3, 3.0])

    def test_plot_pivot_column_with_row_filtering(self):
        model = _make_pivot_proxy_model()
        model.set_filter("object", {(db, "1"), (db, "3")})
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 2, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [1.1, 1.3])

    def test_plot_pivot_column_with_column_filtering(self):
        model = _make_pivot_proxy_model()
        model.set_filter("parameter", {(db, "int_col")})
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])

    def test_plot_pivot_selection(self):
        model = _make_pivot_proxy_model()
        selected_indexes = list()
        for row in range(3, 6):
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
        model = _make_pivot_proxy_model()
        model.sourceModel().set_plot_x_column(2, True)
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_xdata(orig=True)), [1.1, 1.2, 1.3])
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])

    def test_plot_pivot_column_when_x_column_hidden(self):
        model = _make_pivot_proxy_model()
        model.sourceModel().set_plot_x_column(1, True)
        model.set_filter("parameter", {(db, "int_col")})
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 1, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_xdata(orig=True)), [1.0, 2.0, 3.0])
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-3.0, -1.0, 2.0])

    def test_plot_pivot_column_on_existing_plot(self):
        model = _make_pivot_proxy_model()
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 3, support)
        plot_pivot_column(model, 3, support, plot_widget)
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
        model = _make_pivot_proxy_model()
        support = PivotTablePlottingHints()
        plot_widget = plot_pivot_column(model, 3, support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        with self.assertRaises(PlottingError):
            plot_pivot_column(model, 2, support, plot_widget)

    def test_plot_tree_view_selection_of_floats(self):
        model = _MockParameterModel()
        selected_indexes = list()
        selected_indexes.append(model.index(0, 1))
        selected_indexes.append(model.index(1, 1))
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        self.assertEqual(plot_widget.plot_type, float)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-2.3, -0.5])

    def test_plot_tree_view_selection_of_time_series(self):
        model = _MockParameterModel()
        selected_indexes = list()
        selected_indexes.append(model.index(2, 1))
        selected_indexes.append(model.index(3, 1))
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [0.5, 2.3])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [-5.0, -3.3])

    def test_plot_tree_view_selection_into_existing_plot(self):
        model = _MockParameterModel()
        selected_indexes = [model.index(2, 1)]
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        selected_indexes = [model.index(3, 1)]
        plot_selection(model, selected_indexes, support, plot_widget)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [0.5, 2.3])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [-5.0, -3.3])

    def test_plot_tree_view_selection_raises_with_mixed_data(self):
        model = _MockParameterModel()
        selected_indexes = list()
        selected_indexes.append(model.index(1, 1))
        selected_indexes.append(model.index(2, 1))
        support = ParameterTablePlottingHints()
        with self.assertRaises(PlottingError):
            plot_selection(model, selected_indexes, support)

    def test_plot_tree_view_selection_into_existing_plot_with_mixed_data_raises(self):
        model = _MockParameterModel()
        selected_indexes = [model.index(2, 1)]
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        selected_indexes = [model.index(0, 1), model.index(1, 1)]
        with self.assertRaises(PlottingError):
            plot_selection(model, selected_indexes, support, plot_widget)

    def test_plot_single_plain_number(self):
        """Test that a selection containing a single plain number gets plotted."""
        model = _MockParameterModel()
        selected_indexes = list()
        selected_indexes.append(model.index(0, 1))
        support = ParameterTablePlottingHints()
        plot_widget = plot_selection(model, selected_indexes, support)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-2.3])

    def test_plot_simple_map(self):
        """Test that a selection containing a single plain number gets plotted."""
        model = _make_pivot_proxy_model()
        support = PivotTablePlottingHints()
        plot_widget = plot_selection(model, [model.index(3, 4)], support)
        self.assertEqual(plot_widget.plot_type, Map)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-1.1, -2.2])

    def test_plot_nested_map(self):
        """Test that a selection containing a single plain number gets plotted."""
        model = _make_pivot_proxy_model()
        support = PivotTablePlottingHints()
        plot_widget = plot_selection(model, [model.index(4, 4)], support)
        self.assertEqual(plot_widget.plot_type, TimeSeries)
        lines = plot_widget.canvas.axes.get_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(list(lines[0].get_ydata(orig=True)), [-1.1, -2.2])
        self.assertEqual(list(lines[1].get_ydata(orig=True)), [-3.3, -4.4])

    def test_plot_nested_map_containing_time_series(self):
        """Test that a selection containing a single plain number gets plotted."""
        model = _make_pivot_proxy_model()
        support = PivotTablePlottingHints()
        plot_widget = plot_selection(model, [model.index(5, 4)], support)
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


if __name__ == '__main__':
    unittest.main()
