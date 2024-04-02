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

"""Unit tests for MapModel class."""
import unittest
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QColor
from spinedb_api import Array, DateTime, Duration, Map, ParameterValueFormatError
from spinetoolbox.mvcmodels.map_model import MapModel, empty


class TestMapModel(unittest.TestCase):
    def setUp(self):
        self._parent = QObject()

    def tearDown(self):
        self._parent.deleteLater()

    def test_append_column(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        model.append_column()
        self.assertEqual(model.columnCount(), 5)
        expected_table = [
            ["A", "-1.1", "", "", ""],
            ["B", "a", "1.1", "", ""],
            ["B", "b", "2.2", "", ""],
            ["", "", "", "", ""],
        ]
        for y, row in enumerate(expected_table):
            for x, expected in enumerate(row):
                index = model.index(y, x)
                self.assertEqual(index.data(), expected)

    def test_columnCount(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.columnCount(), 3)

    def test_columnCount_nested_maps(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.columnCount(), 4)

    def test_columnCount_empty_map(self):
        map_value = Map([], [], index_type=int)
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.columnCount(), 3)

    def test_convert_leaf_maps(self):
        nested_map = Map([DateTime("2020-07-03 12:00:00"), DateTime("2020-07-03 12:00:00")], [22.2, 23.3])
        map_ = Map([1.0], [nested_map])
        model = MapModel(map_, self._parent)
        model.convert_leaf_maps()
        self.assertEqual(model.columnCount(), 3)
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.index(0, 0).data(), str(1.0))
        self.assertEqual(model.index(0, 1).data(), "Time series")
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 0).data(), "")
        self.assertEqual(model.index(1, 1).data(), "")
        self.assertEqual(model.index(1, 2).data(), "")

    def test_data_DisplayRole(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.index(0, 0).data(), "a")
        self.assertEqual(model.index(1, 0).data(), "b")
        self.assertEqual(model.index(2, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), str(1.1))
        self.assertEqual(model.index(1, 1).data(), str(2.2))
        self.assertEqual(model.index(2, 1).data(), "")
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 2).data(), "")
        self.assertEqual(model.index(2, 2).data(), "")

    def test_data_EditRole(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.index(0, 0).data(Qt.ItemDataRole.EditRole), "a")
        self.assertEqual(model.index(1, 0).data(Qt.ItemDataRole.EditRole), "b")
        self.assertEqual(model.index(0, 1).data(Qt.ItemDataRole.EditRole), 1.1)
        self.assertEqual(model.index(1, 1).data(Qt.ItemDataRole.EditRole), 2.2)

    def test_data_BackgroundRole(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        expected = QColor(245, 245, 245)
        self.assertEqual(model.index(0, 0).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(1, 0).data(Qt.ItemDataRole.BackgroundRole), expected)
        self.assertEqual(model.index(0, 1).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(1, 1).data(Qt.ItemDataRole.BackgroundRole), expected)
        self.assertEqual(model.index(0, 2).data(Qt.ItemDataRole.BackgroundRole), expected)
        self.assertEqual(model.index(1, 2).data(Qt.ItemDataRole.BackgroundRole), expected)

    def test_data_FontRole(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.index(0, 0).data(Qt.ItemDataRole.FontRole), None)
        self.assertEqual(model.index(1, 0).data(Qt.ItemDataRole.FontRole), None)
        self.assertTrue(model.index(0, 1).data(Qt.ItemDataRole.FontRole).bold())
        self.assertEqual(model.index(1, 1).data(Qt.ItemDataRole.FontRole), None)
        self.assertEqual(model.index(0, 2).data(Qt.ItemDataRole.FontRole), None)
        self.assertEqual(model.index(1, 2).data(Qt.ItemDataRole.FontRole), None)

    def test_data_nested_maps_DisplayRole(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.index(0, 0).data(), "A")
        self.assertEqual(model.index(1, 0).data(), "B")
        self.assertEqual(model.index(2, 0).data(), "B")
        self.assertEqual(model.index(3, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), str(-1.1))
        self.assertEqual(model.index(1, 1).data(), "a")
        self.assertEqual(model.index(2, 1).data(), "b")
        self.assertEqual(model.index(3, 1).data(), "")
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 2).data(), str(1.1))
        self.assertEqual(model.index(2, 2).data(), str(2.2))
        self.assertEqual(model.index(3, 2).data(), "")
        self.assertEqual(model.index(0, 3).data(), "")
        self.assertEqual(model.index(1, 3).data(), "")
        self.assertEqual(model.index(2, 3).data(), "")
        self.assertEqual(model.index(3, 3).data(), "")

    def test_data_nested_maps_EditRole(self):
        nested_map = Map(["a", "b"], [None, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.index(0, 0).data(Qt.ItemDataRole.EditRole), "A")
        self.assertEqual(model.index(1, 0).data(Qt.ItemDataRole.EditRole), "B")
        self.assertEqual(model.index(2, 0).data(Qt.ItemDataRole.EditRole), "B")
        self.assertEqual(model.index(0, 1).data(Qt.ItemDataRole.EditRole), -1.1)
        self.assertEqual(model.index(1, 1).data(Qt.ItemDataRole.EditRole), "a")
        self.assertEqual(model.index(2, 1).data(Qt.ItemDataRole.EditRole), "b")
        self.assertEqual(model.index(0, 2).data(Qt.ItemDataRole.EditRole), "")
        self.assertEqual(model.index(1, 2).data(Qt.ItemDataRole.EditRole), None)
        self.assertEqual(model.index(2, 2).data(Qt.ItemDataRole.EditRole), 2.2)

    def test_data_nested_maps_FontRole(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.index(0, 0).data(Qt.ItemDataRole.FontRole), None)
        self.assertEqual(model.index(1, 0).data(Qt.ItemDataRole.FontRole), None)
        self.assertEqual(model.index(2, 0).data(Qt.ItemDataRole.FontRole), None)
        self.assertTrue(model.index(0, 1).data(Qt.ItemDataRole.FontRole).bold())
        self.assertEqual(model.index(1, 1).data(Qt.ItemDataRole.FontRole), None)
        self.assertEqual(model.index(2, 1).data(Qt.ItemDataRole.FontRole), None)
        self.assertEqual(model.index(0, 2).data(Qt.ItemDataRole.FontRole), None)
        self.assertTrue(model.index(1, 2).data(Qt.ItemDataRole.FontRole).bold())
        self.assertTrue(model.index(2, 2).data(Qt.ItemDataRole.FontRole).bold())

    def test_data_nested_maps_BackgroundRole(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.index(0, 0).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(1, 0).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(2, 0).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(3, 0).data(Qt.ItemDataRole.BackgroundRole), QColor(245, 245, 245))
        self.assertEqual(model.index(0, 1).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(1, 1).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(2, 1).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(3, 1).data(Qt.ItemDataRole.BackgroundRole), QColor(245, 245, 245))
        self.assertEqual(model.index(0, 2).data(Qt.ItemDataRole.BackgroundRole), QColor(255, 240, 240))
        self.assertEqual(model.index(1, 2).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(2, 2).data(Qt.ItemDataRole.BackgroundRole), None)
        self.assertEqual(model.index(3, 2).data(Qt.ItemDataRole.BackgroundRole), QColor(245, 245, 245))
        self.assertEqual(model.index(0, 3).data(Qt.ItemDataRole.BackgroundRole), QColor(245, 245, 245))
        self.assertEqual(model.index(1, 3).data(Qt.ItemDataRole.BackgroundRole), QColor(245, 245, 245))
        self.assertEqual(model.index(2, 3).data(Qt.ItemDataRole.BackgroundRole), QColor(245, 245, 245))
        self.assertEqual(model.index(3, 3).data(Qt.ItemDataRole.BackgroundRole), QColor(245, 245, 245))

    def test_data_DisplayRole_repeated_indexes_do_not_show(self):
        leaf_map = Map(["a", "b"], [1.1, 2.2])
        nested_map = Map(["A"], [leaf_map])
        root_map = Map(["root"], [nested_map])
        model = MapModel(root_map, self._parent)
        expected_data = [["root", "A", "a", str(1.1)], ["root", "A", "b", str(2.2)]]
        for row in range(2):
            for column in range(4):
                index = model.index(row, column)
                self.assertEqual(index.data(), expected_data[row][column])

    def test_flags(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        index = model.index(0, 0)
        self.assertEqual(model.flags(index), Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

    def test_headerData(self):
        nested_map = Map(["a", "b"], [1.1, 2.2], index_name="nested index")
        map_value = Map(["A"], [nested_map], index_name="main index")
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), "main index")
        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "nested index")
        self.assertEqual(model.headerData(2, Qt.Orientation.Horizontal), "Value")
        self.assertEqual(model.headerData(0, Qt.Orientation.Vertical), 1)

    def test_setHeaderData(self):
        nested_map = Map(["a", "b"], [1.1, 2.2], index_name="nested index")
        map_value = Map(["A"], [nested_map], index_name="main index")
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), "main index")
        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "nested index")
        self.assertTrue(model.setHeaderData(0, Qt.Orientation.Horizontal, "new main"))
        self.assertTrue(model.setHeaderData(1, Qt.Orientation.Horizontal, "new nested"))
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), "new main")
        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "new nested")

    def test_insertRows_to_empty_model(self):
        map_value = Map([], [], str)
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.rowCount(), 1)
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.index(0, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), "")
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 0).data(), "")
        self.assertEqual(model.index(1, 1).data(), "")
        self.assertEqual(model.index(1, 2).data(), "")

    def test_insertRows_to_beginning(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        self.assertTrue(model.insertRows(0, 1))
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.index(0, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), "")
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 0).data(), "a")
        self.assertEqual(model.index(1, 1).data(), str(1.1))
        self.assertEqual(model.index(1, 2).data(), "")
        self.assertEqual(model.index(2, 0).data(), "")
        self.assertEqual(model.index(2, 1).data(), "")
        self.assertEqual(model.index(2, 2).data(), "")

    def test_insertRows_to_end(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.index(0, 0).data(), "a")
        self.assertEqual(model.index(0, 1).data(), str(1.1))
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 0).data(), "a")
        self.assertEqual(model.index(1, 1).data(), str(1.1))
        self.assertEqual(model.index(1, 2).data(), "")

    def test_insertRows_to_middle_of_nested_map(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A"], [nested_map])
        model = MapModel(map_value, self._parent)
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(model.rowCount(), 4)
        expected_table = [
            ["A", "a", str(1.1), ""],
            ["A", "a", str(1.1), ""],
            ["A", "b", str(2.2), ""],
            ["", "", "", ""],
        ]
        for y, row in enumerate(expected_table):
            for x, expected in enumerate(row):
                self.assertEqual(model.index(y, x).data(), expected)

    def test_rowCount(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.rowCount(), 3)

    def test_rowCount_nested_maps(self):
        nested_map = Map(["a", "b"], [1.1, 2.2])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.rowCount(), 4)

    def test_row_count_empty_map(self):
        map_value = Map([], [], index_type=str)
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.rowCount(), 1)

    def test_removeRows_single_row(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 3)
        self.assertEqual(model.index(0, 0).data(), "")

    def test_removeRows_first_row(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value, self._parent)
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.index(0, 0).data(), "b")
        self.assertEqual(model.index(0, 1).data(), str(2.2))
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 0).data(), "")
        self.assertEqual(model.index(1, 1).data(), "")
        self.assertEqual(model.index(1, 2).data(), "")

    def test_removeRows_last_row(self):
        map_value = Map(["a", "b"], [1.1, 2.2])
        model = MapModel(map_value, self._parent)
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.index(0, 0).data(), "b")
        self.assertEqual(model.index(0, 1).data(), str(2.2))
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 0).data(), "")
        self.assertEqual(model.index(1, 1).data(), "")
        self.assertEqual(model.index(1, 2).data(), "")

    def test_removeRows_middle_row_in_nested_map(self):
        nested_map = Map(["a", "b", "c"], [1.1, 2.2, 3.3])
        map_value = Map(["A"], [nested_map])
        model = MapModel(map_value, self._parent)
        self.assertTrue(model.removeRows(1, 1))
        self.assertEqual(model.rowCount(), 3)
        expected_table = [["A", "a", str(1.1), ""], ["A", "c", str(3.3), ""], ["", "", "", ""]]
        for y, row in enumerate(expected_table):
            for x, expected in enumerate(row):
                self.assertEqual(model.index(y, x).data(), expected)

    def test_setData(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        self.assertTrue(model.setData(model.index(0, 0), Duration("1 month")))
        self.assertEqual(model.index(0, 0).data(), "1M")

    def test_setData_expands_empty_table(self):
        model = MapModel(Map([], [], Duration), self._parent)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 3)
        self.assertEqual(model.index(0, 0).data(), "")
        self.assertTrue(model.setData(model.index(0, 0), Duration("1 month")))
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 3)
        self.assertEqual(model.index(0, 0).data(), "1M")
        self.assertEqual(model.index(0, 1).data(), "")
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 0).data(), "")
        self.assertEqual(model.index(1, 1).data(), "")
        self.assertEqual(model.index(1, 2).data(), "")

    def test_setData_expands_rows(self):
        model = MapModel(Map([Duration("1 month")], [1.1]), self._parent)
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 3)
        self.assertTrue(model.setData(model.index(1, 1), 2.2))
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 3)
        self.assertEqual(model.index(0, 0).data(), "1M")
        self.assertEqual(model.index(0, 1).data(), str(1.1))
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(1, 0).data(), "1M")
        self.assertEqual(model.index(1, 1).data(), str(2.2))
        self.assertEqual(model.index(1, 2).data(), "")
        self.assertEqual(model.index(2, 0).data(), "")
        self.assertEqual(model.index(2, 1).data(), "")
        self.assertEqual(model.index(2, 2).data(), "")

    def test_setData_does_not_expand_rows_if_value_is_empty(self):
        model = MapModel(Map([Duration("1 month")], [1.1]), self._parent)
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 3)
        self.assertFalse(model.setData(model.index(1, 0), ""))

    def test_setData_does_not_expand_columns_if_value_is_empty(self):
        model = MapModel(Map([Duration("1 month")], [1.1]), self._parent)
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 3)
        self.assertFalse(model.setData(model.index(0, 2), ""))

    def test_setData_does_not_clear_value_if_it_is_zero(self):
        model = MapModel(Map([], [], str), self._parent)
        model.setData(model.index(0, 0), "idx")
        model.setData(model.index(0, 1), 0.0)
        self.assertEqual(model.rowCount(), 1 + 1)
        self.assertEqual(model.columnCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "idx")
        self.assertEqual(model.index(0, 1).data(), str(0.0))

    def test_init_converts_numpy_strings_to_real_strings(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        model.setData(model.index(1, 0), "b", Qt.ItemDataRole.EditRole)
        model.setData(model.index(1, 1), 2.2, Qt.ItemDataRole.EditRole)
        value = model.value()
        self.assertEqual(value, Map(["a", "b"], [1.1, 2.2]))

    def test_reset_converts_numpy_strings_to_real_strings(self):
        model = MapModel(Map([], [], str), self._parent)
        map_value = Map(["a"], [1.1])
        model.reset(map_value)
        model.setData(model.index(1, 0), "b", Qt.ItemDataRole.EditRole)
        model.setData(model.index(1, 1), 2.2, Qt.ItemDataRole.EditRole)
        value = model.value()
        self.assertEqual(value, Map(["a", "b"], [1.1, 2.2]))

    def test_trim_columns(self):
        map_value = Map(["a"], [1.1])
        model = MapModel(map_value, self._parent)
        model.append_column()
        model.trim_columns()
        self.assertEqual(model.columnCount(), 3)

    def test_value(self):
        map_value = Map(["a", "b"], [1.1, 2.2], index_name="idx")
        model = MapModel(map_value, self._parent)
        value_from_model = model.value()
        self.assertEqual(value_from_model.indexes, ["a", "b"])
        self.assertEqual(value_from_model.values, [1.1, 2.2])
        self.assertEqual(value_from_model.index_name, "idx")

    def test_value_nested_maps(self):
        nested_map = Map(["a", "b"], [1.1, 2.2], index_name="nested idx")
        map_value = Map(["A", "B"], [-1.1, nested_map], index_name="idx")
        model = MapModel(map_value, self._parent)
        value_from_model = model.value()
        self.assertEqual(value_from_model.indexes, ["A", "B"])
        self.assertEqual(value_from_model.index_name, "idx")
        self.assertEqual(value_from_model.values[0], -1.1)
        self.assertEqual(value_from_model.values[1].indexes, ["a", "b"])
        self.assertEqual(value_from_model.values[1].index_name, "nested idx")
        self.assertEqual(value_from_model.values[1].values, [1.1, 2.2])

    def test_value_single_row_nested_map(self):
        nested_map = Map(["a"], [1.1])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        value_from_model = model.value()
        self.assertEqual(value_from_model.indexes, ["A", "B"])
        self.assertEqual(value_from_model.values[0], -1.1)
        self.assertEqual(value_from_model.values[1].indexes, ["a"])
        self.assertEqual(value_from_model.values[1].values, [1.1])

    def test_value_interleaved_rows(self):
        model = MapModel(Map(["a"], [0.0]), self._parent)
        model.insertRows(1, 2)
        self.assertEqual(model.rowCount(), 4)
        model.append_column()
        self.assertEqual(model.columnCount(), 4)
        model.setData(model.index(0, 0), "key1")
        model.setData(model.index(0, 1), "a")
        model.setData(model.index(0, 2), -2.0)
        model.setData(model.index(1, 0), "key2")
        model.setData(model.index(1, 1), 23.0)
        model.setData(model.index(2, 0), "key1")
        model.setData(model.index(2, 1), "b")
        model.setData(model.index(2, 2), -3.0)
        map_ = model.value()
        self.assertEqual(map_.indexes, ["key1", "key2"])
        self.assertIsInstance(map_.values[0], Map)
        self.assertEqual(map_.values[0].indexes, ["a", "b"])
        self.assertEqual(map_.values[0].values, [-2.0, -3.0])
        self.assertEqual(map_.values[1], 23.0)

    def test_value_interleaved_rows_nested_maps_with_same_indexes(self):
        model = MapModel(Map(["a"], [0.0]), self._parent)
        model.insertRows(1, 3)
        self.assertEqual(model.rowCount(), 5)
        model.append_column()
        self.assertEqual(model.columnCount(), 4)
        model.setData(model.index(0, 0), "key1")
        model.setData(model.index(0, 1), "kkey1")
        model.setData(model.index(0, 2), "value11")
        model.setData(model.index(1, 0), "key2")
        model.setData(model.index(1, 1), "kkey1")
        model.setData(model.index(1, 2), "value21")
        model.setData(model.index(2, 0), "key1")
        model.setData(model.index(2, 1), "kkey2")
        model.setData(model.index(2, 2), "value12")
        model.setData(model.index(3, 0), "key2")
        model.setData(model.index(3, 1), "kkey2")
        model.setData(model.index(3, 2), "value22")
        map_ = model.value()
        self.assertEqual(map_.indexes, ["key1", "key2"])
        self.assertIsInstance(map_.values[0], Map)
        self.assertEqual(map_.values[0].indexes, ["kkey1", "kkey2"])
        self.assertEqual(map_.values[0].values, ["value11", "value12"])
        self.assertIsInstance(map_.values[1], Map)
        self.assertEqual(map_.values[1].indexes, ["kkey1", "kkey2"])
        self.assertEqual(map_.values[1].values, ["value21", "value22"])

    def test_null_value(self):
        model = MapModel(Map(["a"], [None]), self._parent)
        self.assertEqual(model.index(0, 0).data(), "a")
        self.assertEqual(model.index(0, 1).data(), "None")

    def test_value_map_missing_index_raises(self):
        root = Map([None], [1.1])
        model = MapModel(root, self._parent)
        with self.assertRaises(ParameterValueFormatError):
            model.value()

    def test_value_nested_map_missing_index_raises(self):
        nested_map = Map([None], [1.1])
        map_value = Map(["A", "B"], [-1.1, nested_map])
        model = MapModel(map_value, self._parent)
        with self.assertRaises(ParameterValueFormatError):
            model.value()

    def test_different_index_types_in_column_raises(self):
        map_value = Map([99.0, 101.0], [-1.1, -2.2])
        model = MapModel(map_value, self._parent)
        model.setData(model.index(1, 0), "a")
        with self.assertRaises(ParameterValueFormatError):
            model.value()

    def test_value_shortening_rows(self):
        original = Map(["a", "b", "c"], [0.0, Map(["bb"], [Map(["bbb"], [Array([-1.0])])]), Array([-2.0])])
        model = MapModel(original, self._parent)
        map_ = model.value()
        self.assertEqual(map_, original)

    def test_insertColumns_to_empty_map(self):
        map_value = Map([], [], index_type=str)
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 3)
        self.assertTrue(model.insertColumns(0, 1))
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 4)
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), "x")
        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "x")
        self.assertEqual(model.headerData(2, Qt.Orientation.Horizontal), "Value")
        self.assertEqual(model.headerData(3, Qt.Orientation.Horizontal), None)
        self.assertEqual(model.index(0, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), "")
        self.assertEqual(model.index(0, 2).data(), "")
        self.assertEqual(model.index(0, 3).data(), "")

    def test_insertColumns_to_map(self):
        map_value = Map(["A"], [1.0], index_name="Panda")
        model = MapModel(map_value, self._parent)
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 3)
        self.assertTrue(model.insertColumns(0, 1))
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 4)
        self.assertEqual(model.headerData(0, Qt.Orientation.Horizontal), "x")
        self.assertEqual(model.headerData(1, Qt.Orientation.Horizontal), "Panda")
        self.assertEqual(model.headerData(2, Qt.Orientation.Horizontal), "Value")
        self.assertEqual(model.headerData(3, Qt.Orientation.Horizontal), None)
        self.assertEqual(model.index(0, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), "A")
        self.assertEqual(model.index(0, 2).data(), str(1.0))
        self.assertEqual(model.index(0, 3).data(), "")
        self.assertEqual(model.index(1, 0).data(), "")
        self.assertEqual(model.index(1, 1).data(), "")
        self.assertEqual(model.index(1, 2).data(), "")
        self.assertEqual(model.index(1, 3).data(), "")


if __name__ == "__main__":
    unittest.main()
