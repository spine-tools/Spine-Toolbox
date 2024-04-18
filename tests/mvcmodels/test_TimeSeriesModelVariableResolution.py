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

"""Unit tests for the TimeSeriesModelVariableResolution class."""
import unittest
import numpy
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QApplication
from spinedb_api import TimeSeriesVariableResolution
from spinetoolbox.mvcmodels.time_series_model_variable_resolution import TimeSeriesModelVariableResolution


class TestTimeSeriesModelFixedStep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._parent = QObject()

    def tearDown(self):
        self._parent.deleteLater()

    def test_data(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-21T08:15"], [-5.0, 7.0], True, False),
            self._parent,
        )
        for role in [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]:
            model_index = model.index(0, 0)
            self.assertEqual(model.data(model_index, role), "2019-07-05T12:00:00")
            model_index = model.index(0, 1)
            expected = str(-5.0) if role == Qt.ItemDataRole.DisplayRole else -5.0
            self.assertEqual(model.data(model_index, role), expected)

    def test_flags(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-21T08:15"], [-5.0, 7.0], True, False),
            self._parent,
        )
        for row in range(2):
            for column in range(2):
                model_index = model.index(row, column)
                self.assertEqual(model.flags(model_index), Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

    def test_insertRows_at_the_beginning(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-21T12:00"], [-5.0, 7.0], True, False),
            self._parent,
        )
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(
                ["2019-06-19T12:00", "2019-07-05T12:00", "2019-07-21T12:00"], [0.0, -5.0, 7.0], True, False
            ),
        )

    def test_insertRows_at_the_beginning_with_only_one_value(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00"], [-5.0], True, False), self._parent
        )
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(["2019-07-05T11:00", "2019-07-05T12:00"], [0.0, -5.0], True, False),
        )

    def test_insertRows_single_row_in_the_middle(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-21T12:00"], [-5.0, 7.0], True, False),
            self._parent,
        )
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(
                ["2019-07-05T12:00", "2019-07-13T12:00", "2019-07-21T12:00"], [-5.0, 0.0, 7.0], True, False
            ),
        )

    def test_insertRows_multiple_rows_in_the_middle(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-21T12:00"], [-5.0, 7.0], True, False),
            self._parent,
        )
        self.assertTrue(model.insertRows(1, 3))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(
                ["2019-07-05T12:00", "2019-07-09T12:00", "2019-07-13T12:00", "2019-07-17T12:00", "2019-07-21T12:00"],
                [-5.0, 0.0, 0.0, 0.0, 7.0],
                True,
                False,
            ),
        )

    def test_insertRows_in_the_end(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-21T12:00"], [-5.0, 7.0], True, False),
            self._parent,
        )
        self.assertTrue(model.insertRows(2, 1))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(
                ["2019-07-05T12:00", "2019-07-21T12:00", "2019-08-06T12:00"], [-5.0, 7.0, 0.0], True, False
            ),
        )

    def test_insertRows_in_the_end_with_only_one_value(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00"], [-5.0], True, False), self._parent
        )
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-05T13:00"], [-5.0, 0.0], True, False),
        )

    def test_removeRows_from_the_beginning(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(
                ["2019-07-05T12:00", "2019-07-21T08:15", "2019-07-23T09:10"], [2.3, -5.0, 7.0], True, False
            ),
            self._parent,
        )
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(["2019-07-21T08:15", "2019-07-23T09:10"], [-5.0, 7.0], True, False),
        )

    def test_removeRows_from_the_middle(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(
                ["2019-07-05T12:00", "2019-07-21T08:15", "2019-07-23T09:10"], [2.3, -5.0, 7.0], True, False
            ),
            self._parent,
        )
        self.assertTrue(model.removeRows(1, 1))
        self.assertEqual(
            model.value, TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-23T09:10"], [2.3, 7.0], True, False)
        )

    def test_removeRows_from_the_end(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(
                ["2019-07-05T12:00", "2019-07-21T08:15", "2019-07-23T09:10"], [2.3, -5.0, 7.0], True, False
            ),
            self._parent,
        )
        self.assertTrue(model.removeRows(2, 1))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-21T08:15"], [2.3, -5.0], True, False),
        )

    def test_cannot_remove_all_rows(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(
                ["2019-07-05T12:00", "2019-07-21T08:15", "2019-07-23T09:10"], [2.3, -5.0, 7.0], True, False
            ),
            self._parent,
        )
        self.assertTrue(model.removeRows(0, 3))
        self.assertEqual(model.value, TimeSeriesVariableResolution(["2019-07-05T12:00"], [2.3], True, False))

    def test_removing_last_row_fails(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00"], [2.3], True, False), self._parent
        )
        self.assertFalse(model.removeRows(0, 1))

    def test_reset_updates_indexes(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["2019-07-05T12:00", "2019-07-21T08:15"], [2.3, -5.0], True, False),
            self._parent,
        )
        model.reset(TimeSeriesVariableResolution(["1991-01-01T13:30", "1992-01-01T13:30"], [7.0, -4.0], False, True))
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(["1991-01-01T13:30", "1992-01-01T13:30"], [7.0, -4.0], False, True),
        )

    def test_setData(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["1991-01-01T13:30", "1992-01-01T13:30"], [2.3, -5.0], True, False),
            self._parent,
        )
        model_index = model.index(0, 1)
        model.setData(model_index, -4.0)
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(["1991-01-01T13:30", "1992-01-01T13:30"], [-4.0, -5.0], True, False),
        )

    def test_setData_sets_value_to_nan_if_conversion_to_float_fails(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["1991-01-01T13:30", "1992-01-01T13:30"], [2.3, -5.0], True, False),
            self._parent,
        )
        model_index = model.index(0, 1)
        model.setData(model_index, "1,1")
        self.assertEqual(
            model.value,
            TimeSeriesVariableResolution(["1991-01-01T13:30", "1992-01-01T13:30"], [numpy.nan, -5.0], True, False),
        )

    def test_setData_sets_timestamp_to_nan_if_conversion_to_datetime_fails(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(["1991-01-01T13:30", "1992-01-01T13:30"], [2.3, -5.0], True, False),
            self._parent,
        )
        model_index = model.index(0, 0)
        model.setData(model_index, "what happened to Tuesday")
        expected = TimeSeriesVariableResolution([numpy.datetime64(), "1992-01-01T13:30"], [2.3, -5.0], True, False)
        self.assertEqual([str(x) for x in model.value.indexes], [str(x) for x in expected.indexes])
        self.assertTrue(numpy.array_equal(model.value.values, expected.values))
        self.assertEqual(model.value.ignore_year, expected.ignore_year)
        self.assertEqual(model.value.repeat, expected.repeat)
        self.assertEqual(model.value.index_name, expected.index_name)

    def test_batch_set_data(self):
        model = TimeSeriesModelVariableResolution(
            TimeSeriesVariableResolution(
                ["2019-07-05T12:00", "2019-07-21T08:15", "2019-07-23T09:10"], [2.3, -5.0, 7.0], True, False
            ),
            self._parent,
        )
        indexes = [model.index(0, 0), model.index(1, 1), model.index(2, 1)]
        values = ["2018-07-05T12:00", 55.5, -55.5]
        model.batch_set_data(indexes, values)
        expected = TimeSeriesVariableResolution(
            ["2018-07-05T12:00", "2019-07-21T08:15", "2019-07-23T09:10"], [2.3, 55.5, -55.5], True, False
        )
        self.assertEqual(model.value, expected)


if __name__ == "__main__":
    unittest.main()
