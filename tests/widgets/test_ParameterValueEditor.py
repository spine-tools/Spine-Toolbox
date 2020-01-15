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
Unit tests for the ParameterValueEditor widget.

:authors: A. Soininen (VTT)
:date:   3.7.2019
"""

import unittest
import dateutil.parser
import numpy as np
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtWidgets import QApplication
from spinedb_api import (
    DateTime,
    Duration,
    duration_to_relativedelta,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    to_database,
)
from spinetoolbox.widgets.parameter_value_editor import ParameterValueEditor


class _MockParentModel(QAbstractTableModel):
    """A mock model for testing purposes."""

    def __init__(self):
        super().__init__()
        self._table = [[None, None], [None, None]]

    def rowCount(self, parent=QModelIndex()):
        return 2

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        return self._table[index.column()][index.row()]

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        self._table[index.column()][index.row()] = value
        return True


class TestParameterValueEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def _check_parent_model_updated_when_closed(self, value):
        model = _MockParentModel()
        model_index = model.index(1, 1)
        model.setData(model_index, to_database(value))
        editor = ParameterValueEditor(model_index)
        # Reset model data to check that the value is written back from the editor
        model.setData(model_index, None)
        editor.accept()
        editor.deleteLater()
        self.assertEqual(model.data(model_index), to_database(value))

    def test_editor_sets_plain_value_in_parent_model(self):
        self._check_parent_model_updated_when_closed(23.0)

    def test_editor_sets_datetime_in_parent_model(self):
        time_stamp = DateTime(dateutil.parser.parse('2019-07-03T12:00'))
        self._check_parent_model_updated_when_closed(time_stamp)

    def test_editor_sets_duration_in_parent_model(self):
        duration = Duration(duration_to_relativedelta('3 months'))
        self._check_parent_model_updated_when_closed(duration)

    def test_editor_sets_time_pattern_in_parent_model(self):
        indexes = ["1-3m", "4-12m"]
        values = np.array([23.0, 5.0])
        pattern = TimePattern(indexes, values)
        self._check_parent_model_updated_when_closed(pattern)

    def test_editor_sets_fixed_resolution_time_series_in_parent_model(self):
        start = dateutil.parser.parse("2019-07-03T12:22")
        resolution = [duration_to_relativedelta("4 years")]
        values = np.array([23.0, 5.0])
        time_series = TimeSeriesFixedResolution(start, resolution, values, False, True)
        self._check_parent_model_updated_when_closed(time_series)

    def test_editor_sets_variable_resolution_time_series_in_parent_model(self):
        indexes = np.array([np.datetime64("2019-07-03T12:22:00"), np.datetime64("2019-07-03T12:23:00")])
        values = np.array([23.0, 5.0])
        time_series = TimeSeriesVariableResolution(indexes, values, True, False)
        self._check_parent_model_updated_when_closed(time_series)


if __name__ == '__main__':
    unittest.main()
