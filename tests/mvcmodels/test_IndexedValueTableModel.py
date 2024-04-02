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

"""Unit tests for the IndexedValueTableModel class."""
import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from spinetoolbox.mvcmodels.indexed_value_table_model import IndexedValueTableModel


class MockValue:
    def __init__(self, indexes, values):
        self.indexes = indexes
        self.values = values
        self.index_name = "idx"

    def __eq__(self, other):
        if not isinstance(other, MockValue):
            return False
        return (self.indexes == other.indexes).all() and (self.values == other.values).all()

    def __len__(self):
        return len(self.indexes)


class TestIndexedValueTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._value = MockValue(["a", "b", "c"], [7, 5, 3])
        self._model = IndexedValueTableModel(self._value, None)

    def test_column_count_is_2(self):
        self.assertEqual(self._model.columnCount(), 2)

    def test_data(self):
        model_index = self._model.index(0, 0)
        self.assertEqual(self._model.data(model_index), "a")
        model_index = self._model.index(2, 0)
        self.assertEqual(self._model.data(model_index), "c")
        model_index = self._model.index(0, 1)
        self.assertEqual(self._model.data(model_index), "7")
        model_index = self._model.index(2, 1)
        self.assertEqual(self._model.data(model_index), "3")

    def test_horizontal_header_data(self):
        self.assertEqual(self._model.headerData(0), "idx")
        self.assertEqual(self._model.headerData(1), "Value")

    def test_set_horizontal_header_data(self):
        self._model.setHeaderData(0, Qt.Orientation.Horizontal, "new idx")
        self.assertEqual(self._model.headerData(0), "new idx")

    def test_vertical_header_data_is_row_number(self):
        for row in range(3):
            self.assertEqual(self._model.headerData(row, orientation=Qt.Orientation.Vertical), row + 1)

    def test_reset(self):
        new_value = MockValue(["d"], [1])
        self._model.reset(new_value)
        self.assertEqual(self._model.rowCount(), 2)
        model_index = self._model.index(0, 0)
        self.assertEqual(self._model.data(model_index), "d")
        model_index = self._model.index(0, 1)
        self.assertEqual(self._model.data(model_index), "1")

    def test_row_count(self):
        self.assertEqual(self._model.rowCount(), 4)


if __name__ == "__main__":
    unittest.main()
