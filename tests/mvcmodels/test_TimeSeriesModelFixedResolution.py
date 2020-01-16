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
Unit tests for the TimeSeriesModelFixedResolution class.

:authors: A. Soininen (VTT)
:date:   5.7.2019
"""

import unittest
import dateutil.parser
from dateutil.relativedelta import relativedelta
import numpy as np
import numpy.testing
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinedb_api import TimeSeriesFixedResolution
from spinetoolbox.mvcmodels.time_series_model_fixed_resolution import TimeSeriesModelFixedResolution


class TestTimeSeriesModelFixedStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_data(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        )
        for role in [Qt.DisplayRole, Qt.EditRole]:
            model_index = model.index(0, 0)
            self.assertEqual(model.data(model_index, role), "2019-07-05T12:00:00")
            model_index = model.index(0, 1)
            self.assertEqual(model.data(model_index, role), -5.0)

    def test_flags(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        )
        model_index = model.index(0, 0)
        self.assertEqual(model.flags(model_index), Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        model_index = model.index(0, 1)
        self.assertEqual(model.flags(model_index), Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

    def test_indexes(self):  # pylint: disable=no-self-use
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        )
        numpy.testing.assert_equal(
            model.indexes, numpy.array(["2019-07-05T12:00", "2019-07-05T14:00"], dtype='datetime64')
        )

    def test_insertRows_at_the_beginning(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        )
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(
            model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [0.0, -5.0, 7.0], True, False)
        )
        np.testing.assert_equal(
            model.indexes, np.array(["2019-07-05T12:00", "2019-07-05T14:00", "2019-07-05T16:00"], dtype="datetime64")
        )

    def test_insertRows_single_row_in_the_middle(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        )
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(
            model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 0.0, 7.0], True, False)
        )
        np.testing.assert_equal(
            model.indexes, np.array(["2019-07-05T12:00", "2019-07-05T14:00", "2019-07-05T16:00"], dtype="datetime64")
        )

    def test_insertRows_multiple_rows_in_the_middle(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        )
        self.assertTrue(model.insertRows(1, 3))
        self.assertEqual(
            model.value,
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 0.0, 0.0, 0.0, 7.0], True, False),
        )
        np.testing.assert_equal(
            model.indexes,
            np.array(
                ["2019-07-05T12:00", "2019-07-05T14:00", "2019-07-05T16:00", "2019-07-05T18:00", "2019-07-05T20:00"],
                dtype="datetime64",
            ),
        )

    def test_insertRows_in_the_end(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        )
        self.assertTrue(model.insertRows(2, 1))
        self.assertEqual(
            model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0, 0.0], True, False)
        )
        np.testing.assert_equal(
            model.indexes, np.array(["2019-07-05T12:00", "2019-07-05T14:00", "2019-07-05T16:00"], dtype="datetime64")
        )

    def test_removeRows_from_the_beginning(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False)
        )
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(
            model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        )
        np.testing.assert_equal(model.indexes, np.array(["2019-07-05T12:00", "2019-07-05T14:00"], dtype="datetime64"))

    def test_removeRows_from_the_middle(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False)
        )
        self.assertTrue(model.removeRows(1, 1))
        self.assertEqual(model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, 7.0], True, False))
        np.testing.assert_equal(model.indexes, np.array(["2019-07-05T12:00", "2019-07-05T14:00"], dtype="datetime64"))

    def test_removeRows_from_the_end(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False)
        )
        self.assertTrue(model.removeRows(2, 1))
        self.assertEqual(
            model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False)
        )
        np.testing.assert_equal(model.indexes, np.array(["2019-07-05T12:00", "2019-07-05T14:00"], dtype="datetime64"))

    def test_cannot_remove_all_rows(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False)
        )
        self.assertTrue(model.removeRows(0, 3))
        self.assertEqual(model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3], True, False))
        np.testing.assert_equal(model.indexes, np.array(["2019-07-05T12:00"], dtype="datetime64"))

    def test_removing_last_row_fails(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3], True, False)
        )
        self.assertFalse(model.removeRows(0, 1))

    def test_reset_updates_indexes(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False)
        )
        model.reset(TimeSeriesFixedResolution("1991-01-01T13:30", "3 months", [7.0, -4.0], False, True))
        self.assertEqual(
            model.value, TimeSeriesFixedResolution("1991-01-01T13:30", "3 months", [7.0, -4.0], False, True)
        )
        numpy.testing.assert_equal(
            model.indexes, np.array(["1991-01-01T13:30", "1991-04-01T13:30"], dtype="datetime64")
        )

    def test_setData(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False)
        )
        model_index = model.index(0, 1)
        model.setData(model_index, -4.0)
        self.assertEqual(
            model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-4.0, -5.0], True, False)
        )

    def test_set_resolution_updates_indexes(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False)
        )
        model.set_resolution([relativedelta(minutes=4)])
        self.assertEqual(
            model.value, TimeSeriesFixedResolution("2019-07-05T12:00", "4 minutes", [2.3, -5.0], True, False)
        )
        np.testing.assert_equal(model.indexes, np.array(["2019-07-05T12:00", "2019-07-05T12:04"], dtype="datetime64"))

    def test_set_start_updates_indexes(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False)
        )
        model.set_start(dateutil.parser.parse("1975-07-07T06:33"))
        self.assertEqual(model.value, TimeSeriesFixedResolution("1975-07-07T06:33", "2h", [2.3, -5.0], True, False))
        np.testing.assert_equal(model.indexes, np.array(["1975-07-07T06:33", "1975-07-07T08:33"], dtype="datetime64"))

    def test_batch_set_data(self):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False)
        )
        indexes = [model.index(0, 0), model.index(1, 1), model.index(2, 1)]
        values = ["1999-01-01T12:00", 55.5, -55.5]
        model.batch_set_data(indexes, values)
        expected = TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, 55.5, -55.5], True, False)
        self.assertEqual(model.value, expected)


if __name__ == '__main__':
    unittest.main()
