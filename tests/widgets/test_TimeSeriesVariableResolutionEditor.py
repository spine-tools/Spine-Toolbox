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

"""Unit tests for the TimeSeriesVariableResolutionEditor widget."""
import unittest
from PySide6.QtWidgets import QApplication
from spinedb_api import TimeSeriesVariableResolution
from spinetoolbox.widgets.time_series_variable_resolution_editor import TimeSeriesVariableResolutionEditor


class TestTimeSeriesVariableResolutionEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_initial_value(self):
        editor = TimeSeriesVariableResolutionEditor()
        value = editor.value()
        self.assertEqual(
            value, TimeSeriesVariableResolution(["2000-01-01T00:00", "2000-01-01T01:00"], [0.0, 0.0], False, False)
        )

    def test_value_access(self):
        editor = TimeSeriesVariableResolutionEditor()
        editor.set_value(
            TimeSeriesVariableResolution(
                ["1996-04-06T16:06", "1996-04-07T16:06", "1996-04-08T16:06"], [4.0, 3.5, 3.0], True, True
            )
        )
        self.assertEqual(
            editor.value(),
            TimeSeriesVariableResolution(
                ["1996-04-06T16:06", "1996-04-07T16:06", "1996-04-08T16:06"], [4.0, 3.5, 3.0], True, True
            ),
        )


if __name__ == "__main__":
    unittest.main()
