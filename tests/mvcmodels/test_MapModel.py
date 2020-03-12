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
Unit tests for MapModel class.

:authors: A. Soininen (VTT)
:date:    11.2.2020
"""

import unittest
from PySide2.QtCore import Qt
from spinedb_api import Map, ParameterValueFormatError
from spinetoolbox.mvcmodels.map_model import MapModel


class TestMapModel(unittest.TestCase):
    def test_append_column(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value)
        model.append_column()
        self.assertEqual(model.columnCount(), 4)
        expected_table = [["A", -1.1, None, None], ["B", "a", 1.1, None], [None, "b", 2.2, None]]
        for row in range(3):
            for column in range(4):
                index = model.index(row, column)
                self.assertEqual(index.data(), expected_table[row][column])

    def test_columnCount(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value)
        self.assertEqual(model.columnCount(), 2)

    def test_columnCount_nested_maps(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value)
        self.assertEqual(model.columnCount(), 3)

    def test_data_DisplayRole(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "a")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "b")
        index = model.index(0, 1)
        self.assertEqual(index.data(), 1.1)
        index = model.index(1, 1)
        self.assertEqual(index.data(), 2.2)

    def test_data_EditRole(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value)
        index = model.index(0, 0)
        self.assertEqual(index.data(Qt.EditRole), '"a"')
        index = model.index(1, 0)
        self.assertEqual(index.data(Qt.EditRole), '"b"')
        index = model.index(0, 1)
        self.assertEqual(index.data(Qt.EditRole), "1.1")
        index = model.index(1, 1)
        self.assertEqual(index.data(Qt.EditRole), "2.2")

    def test_data_nested_maps_DisplayRole(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "A")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "B")
        index = model.index(2, 0)
        self.assertEqual(index.data(), None)
        index = model.index(0, 1)
        self.assertEqual(index.data(), -1.1)
        index = model.index(1, 1)
        self.assertEqual(index.data(), "a")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "b")
        index = model.index(0, 2)
        self.assertEqual(index.data(), None)
        index = model.index(1, 2)
        self.assertEqual(index.data(), 1.1)
        index = model.index(2, 2)
        self.assertEqual(index.data(), 2.2)

    def test_data_nested_maps_EditRole(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value)
        index = model.index(0, 0)
        self.assertEqual(index.data(Qt.EditRole), '"A"')
        index = model.index(1, 0)
        self.assertEqual(index.data(Qt.EditRole), '"B"')
        index = model.index(2, 0)
        self.assertEqual(index.data(Qt.EditRole), '"B"')
        index = model.index(0, 1)
        self.assertEqual(index.data(Qt.EditRole), "-1.1")
        index = model.index(1, 1)
        self.assertEqual(index.data(Qt.EditRole), '"a"')
        index = model.index(2, 1)
        self.assertEqual(index.data(Qt.EditRole), '"b"')
        index = model.index(0, 2)
        self.assertEqual(index.data(Qt.EditRole), '""')
        index = model.index(1, 2)
        self.assertEqual(index.data(Qt.EditRole), "1.1")
        index = model.index(2, 2)
        self.assertEqual(index.data(Qt.EditRole), "2.2")

    def test_data_DisplayRole_repeated_indexes_do_not_show(self):
        leaf_map = Map(["a", "b"], [1.1, 2.2])
        nested_map = Map(["A"], [leaf_map])
        root_map = Map(["root"], [nested_map])
        model = MapModel(root_map)
        expected_data = [["root", "A", "a", 1.1], [None, None, "b", 2.2]]
        for row in range(2):
            for column in range(4):
                index = model.index(row, column)
                self.assertEqual(index.data(), expected_data[row][column])

    def test_flags(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value)
        index = model.index(0, 0)
        self.assertEqual(model.flags(index), Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

    def test_headerData(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A"], [nested_map])
        model = MapModel(map_value)
        self.assertEqual(model.headerData(0, Qt.Horizontal), "Index")
        self.assertEqual(model.headerData(1, Qt.Horizontal), "Index or value")
        self.assertEqual(model.headerData(2, Qt.Horizontal), "Value")
        self.assertEqual(model.headerData(0, Qt.Vertical), 1)

    def test_insertRows_to_empty_model(self):
        map_value = Map([], [], str)
        model = MapModel(map_value)
        self.assertEqual(model.rowCount(), 0)
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(model.rowCount(), 1)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "key")
        index = model.index(0, 1)
        self.assertEqual(index.data(), 0.0)

    def test_insertRows_to_beginning(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value)
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(model.rowCount(), 2)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "key")
        index = model.index(0, 1)
        self.assertEqual(index.data(), 0.0)
        index = model.index(1, 0)
        self.assertEqual(index.data(), "a")
        index = model.index(1, 1)
        self.assertEqual(index.data(), 1.1)

    def test_insertRows_to_end(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value)
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(model.rowCount(), 2)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "a")
        index = model.index(0, 1)
        self.assertEqual(index.data(), 1.1)
        index = model.index(1, 0)
        self.assertEqual(index.data(), "key")
        index = model.index(1, 1)
        self.assertEqual(index.data(), 0.0)

    def test_insertRows_to_middle_of_nested_map(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A"], [nested_map])
        model = MapModel(map_value)
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(model.rowCount(), 3)
        expected_table = [["A", "a", 1.1], [None, "key", 0.0], [None, "b", 2.2]]
        for row in range(3):
            for column in range(3):
                index = model.index(row, column)
                self.assertEqual(index.data(), expected_table[row][column])

    def test_rowCount(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value)
        self.assertEqual(model.rowCount(), 2)

    def test_rowCount_nested_maps(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value)
        self.assertEqual(model.rowCount(), 3)

    def test_removeRows_single_row(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value)
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 0)

    def test_removeRows_first_row(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value)
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 1)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "b")
        index = model.index(0, 1)
        self.assertEqual(index.data(), 2.2)

    def test_removeRows_last_row(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value)
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 1)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "b")
        index = model.index(0, 1)
        self.assertEqual(index.data(), 2.2)

    def test_removeRows_middle_row_in_nested_map(self):
        nested_map = Map(["a", "b", "c"], [1.1, 2.2, 3.3])
        map_value = Map(["A"], [nested_map])
        model = MapModel(map_value)
        self.assertTrue(model.removeRows(1, 1))
        self.assertEqual(model.rowCount(), 2)
        expected_table = [["A", "a", 1.1], [None, "c", 3.3]]
        for row in range(2):
            for column in range(3):
                index = model.index(row, column)
                self.assertEqual(index.data(), expected_table[row][column])

    def test_setData(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value)
        index = model.index(0, 0)
        model.setData(index, '{"type":"duration", "data":"1 month"}')
        index = model.index(0, 0)
        self.assertEqual(index.data(), "1M")

    def test_trim_columns(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value)
        model.append_column()
        model.trim_columns()
        self.assertEqual(model.columnCount(), 2)

    def test_value(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value)
        value_from_model = model.value()
        self.assertEqual(value_from_model.indexes, ["a", "b"])
        self.assertEqual(value_from_model.values, [1.1, 2.2])

    def test_value_nested_maps(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value)
        value_from_model = model.value()
        self.assertEqual(value_from_model.indexes, ["A", "B"])
        self.assertEqual(value_from_model.values[0], -1.1)
        self.assertEqual(value_from_model.values[1].indexes, ["a", "b"])
        self.assertEqual(value_from_model.values[1].values, [1.1, 2.2])

    def test_value_single_row_nested_map(self):
        nested_map = Map(["a"], [1.1])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value)
        value_from_model = model.value()
        self.assertEqual(value_from_model.indexes, ["A", "B"])
        self.assertEqual(value_from_model.values[0], -1.1)
        self.assertEqual(value_from_model.values[1].indexes, ["a"])
        self.assertEqual(value_from_model.values[1].values, [1.1])

    def test_value_map_missing_index_raises(self):
        root = Map([None], [1.1])
        model = MapModel(root)
        with self.assertRaises(ParameterValueFormatError):
            model.value()

    def test_value_nested_map_missing_index_raises(self):
        nested_map = Map([None], [1.1])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value)
        with self.assertRaises(ParameterValueFormatError):
            model.value()


if __name__ == '__main__':
    unittest.main()
