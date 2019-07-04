######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the IndexedValueTableModel class.

:authors: A. Soininen (VTT)
:date:   2.7.2019
"""

import unittest
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from indexed_value_table_model import IndexedValueTableModel


class TestIndexedValueTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._indexes = ['a', 'b', 'c']
        self._values = [7, 5, 3]
        self._model = IndexedValueTableModel(self._indexes, self._values, str, int)

    def test_column_count_is_2(self):
        self.assertEqual(self._model.columnCount(), 2)

    def test_data(self):
        model_index = self._model.index(0, 0)
        self.assertEqual(self._model.data(model_index), 'a')
        model_index = self._model.index(2, 0)
        self.assertEqual(self._model.data(model_index), 'c')
        model_index = self._model.index(0, 1)
        self.assertEqual(self._model.data(model_index), 7)
        model_index = self._model.index(2, 1)
        self.assertEqual(self._model.data(model_index), 3)

    def test_flags(self):
        for row in range(3):
            model_index = self._model.index(row, 0)
            self.assertEqual(self._model.flags(model_index), Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            model_index = self._model.index(row, 1)
            self.assertEqual(self._model.flags(model_index), Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

    def test_flags_with_fixed_indexes(self):
        self._model.set_fixed_indexes(True)
        for row in range(3):
            model_index = self._model.index(row, 0)
            self.assertEqual(self._model.flags(model_index), Qt.ItemIsSelectable)
            model_index = self._model.index(row, 1)
            self.assertEqual(self._model.flags(model_index), Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

    def test_horizontal_header_data(self):
        self._model.set_index_header('A')
        self._model.set_value_header('B')
        self.assertEqual(self._model.headerData(0), 'A')
        self.assertEqual(self._model.headerData(1), 'B')

    def test_vertical_header_data_is_row_number(self):
        for row in range(3):
            self.assertEqual(self._model.headerData(row, orientation=Qt.Vertical), row + 1)

    def test_reset(self):
        new_indexes = ['d']
        new_values = [1]
        self._model.reset(new_indexes, new_values)
        self.assertEqual(self._model.rowCount(), 1)
        model_index = self._model.index(0, 0)
        self.assertEqual(self._model.data(model_index), new_indexes[0])
        model_index = self._model.index(0, 1)
        self.assertEqual(self._model.data(model_index), 1)

    def test_row_count(self):
        self.assertEqual(self._model.rowCount(), 3)

    def test_setData_converters(self):
        model_index = self._model.index(0, 0)
        self.assertTrue(self._model.setData(model_index, 13))
        self.assertEqual(self._model.data(model_index), '13')
        model_index = self._model.index(0, 1)
        self.assertTrue(self._model.setData(model_index, '23'))
        self.assertEqual(self._model.data(model_index), 23)
        self.assertFalse(self._model.setData(model_index, 'I am not a number'))

    def test_indexes(self):
        self.assertEqual(self._model.indexes, ['a', 'b', 'c'])
        self.assertEqual(self._model.values, [7, 5, 3])


if __name__ == '__main__':
    unittest.main()
