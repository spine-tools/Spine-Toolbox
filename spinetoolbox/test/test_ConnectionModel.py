######################################################################################################################
# Copyright (C) 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the ConnectionModel class.

:author: A. Soininen (VTT)
:date:   16.5.2019
"""

import unittest
from PySide2.QtCore import QModelIndex, Qt
from models import ConnectionModel


class TestConnectionModel(unittest.TestCase):

    def test_flags(self):
        model = ConnectionModel()
        flags = model.flags(QModelIndex)
        self.assertEqual(flags, Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def test_rowCount(self):
        model = ConnectionModel()
        self.assertEqual(model.rowCount(), 0)
        model.insertRows(0, 1)
        self.assertEqual(model.rowCount(), 1)

    def test_columnCount(self):
        model = ConnectionModel()
        self.assertEqual(model.columnCount(), 0)
        model.insertRows(0, 1)  # Adds also a single column
        self.assertEqual(model.columnCount(), 1)

    def test_headerData(self):
        for orientation in [Qt.Horizontal, Qt.Vertical]:
            model = ConnectionModel()
            self.assertIsNone(model.headerData(0, orientation))
            model.append_item('item', 0)
            self.assertEqual(model.headerData(0, orientation), 'item')

    def test_setHeaderData(self):
        for orientation in [Qt.Horizontal, Qt.Vertical]:
            model = ConnectionModel()
            self.assertFalse(model.setHeaderData(0, orientation, 'data'))
            model.append_item('item1', 0)
            model.append_item('item2', 0)
            self.assertTrue(model.setHeaderData(0, orientation, 'data1'))
            self.assertEqual(model.headerData(0, orientation), 'data1')
            self.assertEqual(model.headerData(1, orientation), 'item1')
            self.assertTrue(model.setHeaderData(1, orientation, 'data2'))
            self.assertEqual(model.headerData(0, orientation), 'data1')
            self.assertEqual(model.headerData(1, orientation), 'data2')

    def test_data(self):
        model = ConnectionModel()
        self.assertIsNone(model.data(QModelIndex(), Qt.DisplayRole))
        model.insertRows(0, 1)
        model.append_item('item', 0)
        model.setHeaderData(0, Qt.Horizontal, 'Horizontal header')
        model.setHeaderData(0, Qt.Vertical, 'Vertical header')
        index = model.index(0, 0)
        model.setData(index, 'data')
        data = model.data(index, Qt.DisplayRole)
        self.assertEqual(data, "True")
        data = model.data(index, Qt.ToolTipRole)
        self.assertEqual(data, "Vertical header (Feedback)")
        data = model.data(index, Qt.UserRole)
        self.assertEqual(data, 'data')

    def test_setData(self):
        model = ConnectionModel()
        model.insertRows(0, 1)
        model.append_item('item', 0)
        model.setHeaderData(0, Qt.Horizontal, 'Horizontal header')
        model.setHeaderData(0, Qt.Vertical, 'Vertical header')
        self.assertFalse(model.setData(QModelIndex(), 'bogusData'))
        index = model.index(0, 0)
        self.assertTrue(model.setData(index, 'data'))
        self.assertEqual(model.data(index, Qt.UserRole), 'data')

    def test_insertRows(self):
        model = ConnectionModel()
        self.assertFalse(model.insertRows(-1, 1))
        self.assertFalse(model.insertRows(1, 1))
        self.assertFalse(model.insertRows(0, 2))
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(model.rowCount(), 1)
        index = model.index(0, 0)
        model.setData(index, 'a')
        self.assertTrue(model.insertRows(0, 1))
        index = model.index(1, 0)
        self.assertEqual(model.data(index, Qt.UserRole), 'a')
        index = model.index(0, 0)
        model.setData(index, 'b')
        self.assertTrue(model.insertRows(1, 1))
        self.assertTrue(model.rowCount(), 3)
        self.assertEqual(model.data(index, Qt.UserRole), 'b')
        index = model.index(2, 0)
        self.assertEqual(model.data(index, Qt.UserRole), 'a')

    def test_insertColumns(self):
        model = ConnectionModel()
        self.assertFalse(model.insertColumns(-1, 1))
        self.assertFalse(model.insertColumns(1, 1))
        self.assertFalse(model.insertColumns(0, 2))
        model.insertRows(0, 1)  # This should give the first column
        self.assertEqual(model.columnCount(), 1)
        index = model.index(0, 0)
        model.setData(index, 'a')
        self.assertTrue(model.insertColumns(0, 1))
        model.setData(index, 'b')
        index = model.index(0, 1)
        self.assertEqual(model.data(index, Qt.UserRole), 'a')
        self.assertTrue(model.insertColumns(1, 1))
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(model.data(index, Qt.UserRole), 'b')
        index = model.index(0, 2)
        self.assertEqual(model.data(index, Qt.UserRole), 'a')

    def test_removeRows(self):
        model = ConnectionModel()
        model.insertRows(0, 1)
        model.insertRows(0, 1)
        model.insertRows(0, 1)
        self.assertEqual(model.rowCount(), 3)
        self.assertFalse(model.removeRows(-1, 1))
        self.assertFalse(model.removeRows(3, 1))
        self.assertFalse(model.removeRows(0, 2))
        index = model.index(0, 0)
        model.setData(index, 'a')
        index = model.index(1, 0)
        model.setData(index, 'b')
        index = model.index(2, 0)
        model.setData(index, 'c')
        self.assertTrue(model.removeRows(1, 1))
        self.assertEqual(model.rowCount(), 2)
        index = model.index(0, 0)
        self.assertEqual(model.data(index, Qt.UserRole), 'a')
        index = model.index(1, 0)
        self.assertEqual(model.data(index, Qt.UserRole), 'c')
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 1)
        index = model.index(0, 0)
        self.assertEqual(model.data(index, Qt.UserRole), 'c')
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 0)

    def test_removeColumns(self):
        model = ConnectionModel()
        model.insertRows(0, 1)  # Inserts the first column
        model.insertColumns(0, 1)
        model.insertColumns(0, 1)
        self.assertEqual(model.columnCount(), 3)
        self.assertFalse(model.removeColumns(-1, 1))
        self.assertFalse(model.removeColumns(3, 1))
        self.assertFalse(model.removeColumns(0, 2))
        index = model.index(0, 0)
        model.setData(index, 'a')
        index = model.index(0, 1)
        model.setData(index, 'b')
        index = model.index(0, 2)
        model.setData(index, 'c')
        self.assertTrue(model.removeColumns(1, 1))
        self.assertEqual(model.columnCount(), 2)
        index = model.index(0, 0)
        self.assertEqual(model.data(index, Qt.UserRole), 'a')
        index = model.index(0, 1)
        self.assertEqual(model.data(index, Qt.UserRole), 'c')
        self.assertTrue(model.removeColumns(0, 1))
        self.assertEqual(model.columnCount(), 1)
        index = model.index(0, 0)
        self.assertEqual(model.data(index, Qt.UserRole), 'c')
        self.assertTrue(model.removeColumns(0, 1))
        self.assertEqual(model.columnCount(), 0)
        self.assertEqual(model.rowCount(), 0)

    def test_append_item(self):
        model = ConnectionModel()
        self.assertFalse(model.append_item('a', -1))
        self.assertFalse(model.append_item('a', 1))
        self.assertEqual(model.rowCount(), 0)
        self.assertEqual(model.columnCount(), 0)
        self.assertIsNone(model.headerData(0, Qt.Horizontal))
        self.assertTrue(model.append_item('a', 0))
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 1)
        self.assertEqual(model.headerData(0, Qt.Horizontal), 'a')
        self.assertTrue(model.append_item('b', 1))
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 2)
        self.assertEqual(model.headerData(0, Qt.Horizontal), 'a')
        self.assertEqual(model.headerData(1, Qt.Horizontal), 'b')
        self.assertTrue(model.append_item('c', 1))
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 3)
        self.assertEqual(model.headerData(0, Qt.Horizontal), 'a')
        self.assertEqual(model.headerData(1, Qt.Horizontal), 'c')
        self.assertEqual(model.headerData(2, Qt.Horizontal), 'b')

    def test_remove_item(self):
        model = ConnectionModel()
        self.assertFalse(model.remove_item('a'))
        model.append_item('a', 0)
        model.append_item('b', 1)
        model.append_item('c', 2)
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 3)
        self.assertTrue(model.remove_item('b'))
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 2)
        self.assertEqual(model.headerData(0, Qt.Vertical), 'a')
        self.assertEqual(model.headerData(1, Qt.Vertical), 'c')
        self.assertTrue(model.remove_item('a'))
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 1)
        self.assertEqual(model.headerData(0, Qt.Vertical), 'c')
        self.assertTrue(model.remove_item('c'))
        self.assertEqual(model.rowCount(), 0)
        self.assertEqual(model.columnCount(), 0)

    def test_output_items(self):
        model = ConnectionModel()
        model.append_item('a', 0)
        model.append_item('b', 0)
        index = model.index(1, 0)
        model.setData(index, True)
        index = model.index(0, 1)
        model.setData(index, False)
        self.assertEqual(model.output_items('a'), ['b'])
        self.assertEqual(model.output_items('b'), [])

    def test_input_items(self):
        model = ConnectionModel()
        model.append_item('a', 0)
        model.append_item('b', 0)
        index = model.index(1, 0)
        model.setData(index, True)
        index = model.index(0, 1)
        model.setData(index, False)
        self.assertEqual(model.input_items('a'), [])
        self.assertEqual(model.input_items('b'), ['a'])


if __name__ == '__main__':
    unittest.main()
