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
Unit tests for the spine_db_manager module.

:author: A. Soininen (VTT)
:date:   12.7.2019
"""

import unittest
from unittest.mock import Mock
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinedb_api import (
    to_database,
    DateTime,
    Duration,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
)
from spinetoolbox.spine_db_manager import SpineDBManager


class TestParameterValueFormatting(unittest.TestCase):
    """Tests for parameter value formatting in SpineDBManager."""

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self.db_mngr = SpineDBManager(None, None)
        self.db_mngr.get_item = Mock()

    def get_value(self, role):
        mock_db_map = Mock()
        id_ = 0
        return self.db_mngr.get_value(mock_db_map, "parameter value", id_, "value", role)

    def test_plain_number_in_display_role(self):
        value = 2.3
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, 2.3)

    def test_plain_number_in_edit_role(self):
        value = 2.3
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, "2.3")

    def test_plain_number_in_tool_tip_role(self):
        value = 2.3
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        self.assertIsNone(self.get_value(Qt.ToolTipRole))

    def test_date_time_in_display_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "2019-07-12 16:00:00")

    def test_date_time_in_edit_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, to_database(value))

    def test_date_time_in_tool_tip_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        self.assertIsNone(self.get_value(Qt.ToolTipRole))

    def test_duration_in_display_role(self):
        value = Duration("3Y")
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "3Y")

    def test_variable_duration_in_display_role(self):
        value = Duration(["2Y", "3Y"])
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "2Y, 3Y")

    def test_duration_in_edit_role(self):
        value = Duration("2M")
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, to_database(value))

    def test_duration_in_tool_tip_role(self):
        value = Duration("13D")
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        self.assertIsNone(self.get_value(Qt.ToolTipRole))

    def test_time_pattern_in_display_role(self):
        value = TimePattern(["1-12m"], [5.0])
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "Time pattern")

    def test_time_pattern_in_edit_role(self):
        value = TimePattern(["1-12m"], [5.0])
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, to_database(value))

    def test_time_pattern_in_tool_tip_role(self):
        value = TimePattern(["1-12m"], [5.0])
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        self.assertIsNone(self.get_value(Qt.ToolTipRole))

    def test_time_series_in_display_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "Time series")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "Time series")

    def test_time_series_in_edit_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, to_database(value))
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, to_database(value))

    def test_time_series_in_tool_tip_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", ["7 hours", "12 hours"], [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.ToolTipRole)
        self.assertEqual(formatted, "Start: 2019-07-12 08:00:00, resolution: [7h, 12h], length: 3")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.return_value = {"value": to_database(value)}
        formatted = self.get_value(Qt.ToolTipRole)
        self.assertEqual(formatted, "Start: 2019-07-12T08:00:00, resolution: variable, length: 2")

    def test_broken_value_in_display_role(self):
        value = "dubbidubbidu"
        self.db_mngr.get_item.return_value = {"value": value}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "Error")

    def test_broken_value_in_edit_role(self):
        value = "diibadaaba"
        self.db_mngr.get_item.return_value = {"value": value}
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, "diibadaaba")

    def test_broken_value_in_tool_tip_role(self):
        value = "diibadaaba"
        self.db_mngr.get_item.return_value = {"value": value}
        formatted = self.get_value(Qt.ToolTipRole)
        self.assertEqual(formatted, 'Could not decode the value')


if __name__ == '__main__':
    unittest.main()
