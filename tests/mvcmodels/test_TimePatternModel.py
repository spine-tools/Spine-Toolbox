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

"""Unit tests for the TimePatternModel class."""
import unittest
import numpy as np
import numpy.testing
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from spinedb_api import TimePattern
from spinetoolbox.mvcmodels.time_pattern_model import TimePatternModel


class TestTimePatternModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_flags(self):
        model = TimePatternModel(TimePattern(["", ""], [0.0, 0.0]), None)
        for row in range(len(model.value)):
            for column in range(2):
                model_index = model.index(row, column)
                self.assertEqual(model.flags(model_index), Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
        model.deleteLater()

    def test_insert_rows_in_the_beginning(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6"], [-5.0, 7.0]), None)
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(len(model.value), 3)
        self.assertEqual(model.value.indexes, ["", "M7-12", "M1-6"])
        numpy.testing.assert_equal(model.value.values, np.array([0.0, -5.0, 7.0]))
        model.deleteLater()

    def test_insert_single_row_in_the_middle(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6"], [-5.0, 7.0]), None)
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(len(model.value), 3)
        self.assertEqual(model.value.indexes, ["M7-12", "", "M1-6"])
        numpy.testing.assert_equal(model.value.values, np.array([-5.0, 0.0, 7.0]))
        model.deleteLater()

    def test_insert_multiple_rows_in_the_middle(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6"], [-5.0, 7.0]), None)
        self.assertTrue(model.insertRows(1, 3))
        self.assertEqual(len(model.value), 5)
        self.assertEqual(model.value.indexes, ["M7-12", "", "", "", "M1-6"])
        numpy.testing.assert_equal(model.value.values, np.array([-5.0, 0.0, 0.0, 0.0, 7.0]))
        model.deleteLater()

    def test_insert_rows_in_the_end(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6"], [-5.0, 7.0]), None)
        self.assertTrue(model.insertRows(2, 1))
        self.assertEqual(len(model.value), 3)
        self.assertEqual(model.value.indexes, ["M7-12", "M1-6", ""])
        numpy.testing.assert_equal(model.value.values, np.array([-5.0, 7.0, 0.0]))
        model.deleteLater()

    def test_remove_rows_from_the_beginning(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6"], [-5.0, 7.0]), None)
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(len(model.value), 1)
        self.assertEqual(model.value.indexes, ["M1-6"])
        numpy.testing.assert_equal(model.value.values, np.array([7.0]))
        model.deleteLater()

    def test_remove_rows_from_the_middle(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6", "M4-9"], [-5.0, 3.0, 7.0]), None)
        self.assertTrue(model.removeRows(1, 1))
        self.assertEqual(len(model.value), 2)
        self.assertEqual(model.value.indexes, ["M7-12", "M4-9"])
        numpy.testing.assert_equal(model.value.values, np.array([-5.0, 7.0]))
        model.deleteLater()

    def test_remove_rows_from_the_end(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6"], [-5.0, 7.0]), None)
        self.assertTrue(model.removeRows(1, 1))
        self.assertEqual(len(model.value), 1)
        self.assertEqual(model.value.indexes, ["M7-12"])
        numpy.testing.assert_equal(model.value.values, [-5.0])
        model.deleteLater()

    def test_cannot_remove_all_rows(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6"], [-5.0, 7.0]), None)
        self.assertTrue(model.removeRows(0, 2))
        self.assertEqual(len(model.value), 1)
        self.assertEqual(model.value.indexes, ["M7-12"])
        numpy.testing.assert_equal(model.value.values, [-5.0])
        model.deleteLater()

    def test_removing_last_row_fails(self):
        model = TimePatternModel(TimePattern(["M7-12"], [-5.0]), None)
        self.assertFalse(model.removeRows(0, 1))
        model.deleteLater()

    def test_setData(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6"], [-5.0, 7.0]), None)
        model_index = model.index(1, 1)
        model.setData(model_index, 2.3)
        self.assertEqual(model.value.indexes, ["M7-12", "M1-6"])
        numpy.testing.assert_equal(model.value.values, [-5.0, 2.3])
        model.deleteLater()

    def test_batch_set_data(self):
        model = TimePatternModel(TimePattern(["M7-12", "M1-6", "M4-9"], [-5.0, 3.0, 7.0]), None)
        indexes = [model.index(0, 0), model.index(1, 1), model.index(2, 1)]
        values = ["D1-7", 55.5, -55.5]
        model.batch_set_data(indexes, values)
        expected = TimePattern(["D1-7", "M1-6", "M4-9"], [-5.0, 55.5, -55.5])
        self.assertEqual(model.value, expected)
        model.deleteLater()


if __name__ == "__main__":
    unittest.main()
