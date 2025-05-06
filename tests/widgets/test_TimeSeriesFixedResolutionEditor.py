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

"""Unit tests for the TimeSeriesFixedResolutionEditor widget."""
import unittest
from PySide6.QtWidgets import QWidget
from spinedb_api import TimeSeriesFixedResolution
from spinetoolbox.widgets.time_series_fixed_resolution_editor import TimeSeriesFixedResolutionEditor
from tests.mock_helpers import TestCaseWithQApplication, q_object


class TestTimeSeriesFixedResolutionEditor(TestCaseWithQApplication):
    def test_initial_value(self):
        with q_object(QWidget()) as parent:
            editor = TimeSeriesFixedResolutionEditor(parent)
            value = editor.value()
            self.assertEqual(value, TimeSeriesFixedResolution("2000-01-01T00:00", "1 hour", [0.0, 0.0], False, False))

    def test_value_access(self):
        with q_object(QWidget()) as parent:
            editor = TimeSeriesFixedResolutionEditor(parent)
            editor.set_value(TimeSeriesFixedResolution("1996-04-06T16:06", "3 days", [4.0, 3.5, 3.0], True, True))
            self.assertEqual(
                editor.value(), TimeSeriesFixedResolution("1996-04-06T16:06", "3 days", [4.0, 3.5, 3.0], True, True)
            )


if __name__ == "__main__":
    unittest.main()
