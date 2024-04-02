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

"""Unit tests for the MinimalTableModel class."""
import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from spinetoolbox.mvcmodels.minimal_table_model import MinimalTableModel


class TestMinimalTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_clear(self):
        """Test the clear() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.insertColumns(0, 1)
        model.insertRows(0, 1)
        index = model.index(0, 0)
        model.setData(index, 23)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 1)
        model.clear()
        self.assertEqual(model.rowCount(), 0)
        self.assertEqual(model.columnCount(), 0)

    def test_flags(self):
        """Test the flags() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.insertColumns(0, 1)
        model.insertRows(0, 1)
        index = model.index(0, 0)
        flags = model.flags(index)
        self.assertEqual(flags, Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def test_rowCount(self):
        """Test the rowCount() method of MinimalTableModel."""
        model = MinimalTableModel()
        self.assertEqual(model.rowCount(), 0)
        model.insertRows(0, 1)
        self.assertEqual(model.rowCount(), 1)
        model.insertRows(1, 10)
        self.assertEqual(model.rowCount(), 11)
        model.removeRows(0, 5)
        self.assertEqual(model.rowCount(), 6)

    def test_columnCount(self):
        """Test the columnCount() method of MinimalTableModel."""
        model = MinimalTableModel()
        self.assertEqual(model.columnCount(), 0)
        model.insertRows(0, 1)
        self.assertEqual(model.columnCount(), 1)
        model.insertColumns(0, 13)
        self.assertEqual(model.columnCount(), 14)
        model.removeColumns(0, 1)
        self.assertEqual(model.columnCount(), 13)

    def test_headerData(self):
        """Test the headerData() method of MinimalTableModel."""
        model = MinimalTableModel()
        labels = ["a", "b", "c"]
        model.set_horizontal_header_labels(labels)
        for index, label in enumerate(labels):
            self.assertEqual(model.headerData(index), label)
        self.assertEqual(model.headerData(5, orientation=Qt.Orientation.Vertical), 5 + 1)

    def test_set_horizontal_header_labels(self):
        """Test the set_horizontal_header_labels() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.set_horizontal_header_labels(["a", "b"])
        self.assertEqual(model.horizontal_header_labels(), ["a", "b"])

    def test_insert_horizontal_header_labels(self):
        """Test the insert_horizontal_header_labels() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.insert_horizontal_header_labels(0, ["a", "b"])
        self.assertEqual(model.horizontal_header_labels(), ["a", "b"])
        model.insert_horizontal_header_labels(0, ["c"])
        self.assertEqual(model.horizontal_header_labels(), ["c", "a", "b"])
        model.insert_horizontal_header_labels(1, ["d"])
        self.assertEqual(model.horizontal_header_labels(), ["c", "d", "a", "b"])
        model.insert_horizontal_header_labels(4, ["e"])
        self.assertEqual(model.horizontal_header_labels(), ["c", "d", "a", "b", "e"])

    def test_setHeaderData(self):
        """Test the setHeaderData() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.set_horizontal_header_labels(["a"])
        self.assertTrue(model.setHeaderData(0, Qt.Orientation.Horizontal, "b"))
        self.assertEqual(model.horizontal_header_labels(), ["b"])
        self.assertFalse(model.setHeaderData(0, Qt.Orientation.Vertical, "c"))
        self.assertFalse(model.setHeaderData(0, Qt.Orientation.Horizontal, "d", role=Qt.ItemDataRole.ToolTipRole))
        self.assertIsNone(model.headerData(0, role=Qt.ItemDataRole.ToolTipRole))

    def test_data(self):
        """Test the data() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.insertRows(0, 1)
        index = model.index(0, 0)
        model.setData(index, "a")
        self.assertTrue(model.data(index), "a")

    def test_row_data(self):
        """Test the row_data() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.insertRows(0, 1)
        n_columns = 3
        model.insertColumns(0, n_columns - 1)
        data = ["a", "b", "c"]
        for column in range(n_columns):
            index = model.index(0, column)
            model.setData(index, data[column])
        self.assertEqual(model.row_data(0), data)

    def test_setData(self):
        """Test the setData() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.insertRows(0, 1)
        index = model.index(0, 0)
        self.assertTrue(model.setData(index, "a"))
        self.assertEqual(model.data(index), "a")

    def test_batch_set_data(self):
        """Test the batch_set_data() method of MinimalTableModel."""
        model = MinimalTableModel()

        n_rows = 3
        model.insertRows(0, n_rows)
        n_columns = 3
        model.insertColumns(0, n_columns)
        background = n_rows * n_columns * ["0xdeadbeef"]
        indices = list()
        for row in range(n_rows):
            for column in range(n_columns):
                indices.append(model.index(row, column))

        def _handle_data_changed(top_left, bottom_right, roles):
            self.assertEqual(top_left, indices[0])
            self.assertEqual(bottom_right, indices[-1])
            self.assertTrue(Qt.ItemDataRole.EditRole in roles)
            self.assertTrue(Qt.ItemDataRole.DisplayRole in roles)

        model.dataChanged.connect(_handle_data_changed)
        self.assertTrue(model.batch_set_data(indices, background))
        for row in range(n_rows):
            for column in range(n_columns):
                index = model.index(row, column)
                self.assertEqual(model.data(index), "0xdeadbeef")

    def test_insertRows(self):
        """Test the insertRows() method of MinimalTableModel."""
        model = MinimalTableModel()
        self.assertEqual(model.rowCount(), 0)
        self.assertFalse(model.insertRows(1, 1))
        self.assertTrue(model.insertRows(0, 2))
        self.assertEqual(model.rowCount(), 2)

        def check_data(expecteds):
            for row, expected in enumerate(expecteds):
                index = model.index(row, 0)
                if expected is not None:
                    self.assertEqual(model.data(index), expected)
                else:
                    self.assertIsNone(model.data(index))

        index = model.index(0, 0)
        model.setData(index, "a")
        index = model.index(1, 0)
        model.setData(index, "b")
        self.assertTrue(model.insertRows(1, 1))
        self.assertEqual(model.rowCount(), 3)
        check_data(["a", None, "b"])
        index = model.index(1, 0)
        model.setData(index, "c")
        self.assertTrue(model.insertRows(3, 1))
        self.assertEqual(model.rowCount(), 4)
        check_data(["a", "c", "b", None])

    def test_insertColumns(self):
        """Test the insertColumns() method of MinimalTableModel."""
        model = MinimalTableModel()
        model.insertRows(0, 1)
        self.assertEqual(model.columnCount(), 1)
        index = model.index(0, 0)
        model.setData(index, "a")
        self.assertTrue(model.insertColumns(0, 1))
        self.assertEqual(model.columnCount(), 2)

        def check_data(expecteds):
            for column, expected in enumerate(expecteds):
                index = model.index(0, column)
                if expected is not None:
                    self.assertEqual(model.data(index), expected)
                else:
                    self.assertIsNone(model.data(index))

        check_data([None, "a"])
        index = model.index(0, 0)
        model.setData(index, "b")
        self.assertTrue(model.insertColumns(1, 1))
        self.assertEqual(model.columnCount(), 3)
        check_data(["b", None, "a"])
        index = model.index(0, 1)
        model.setData(index, "c")
        self.assertTrue(model.insertColumns(3, 1))
        self.assertEqual(model.columnCount(), 4)
        check_data(["b", "c", "a", None])

    def test_removeRows(self):
        """Test the removeRows() method of MinimalTableModel."""
        model = MinimalTableModel()
        self.assertFalse(model.removeRows(-1, 1))
        self.assertFalse(model.removeRows(0, 1))
        data = ["a", "b", "c", "d", "e"]
        model.insertRows(0, len(data))
        for row, value in enumerate(data):
            index = model.index(row, 0)
            model.setData(index, value)
        self.assertTrue(model.removeRows(1, 2))
        self.assertEqual(model.rowCount(), 3)

        def check_data(expecteds):
            for row, expected in enumerate(expecteds):
                index = model.index(row, 0)
                self.assertEqual(model.data(index), expected)

        check_data(["a", "d", "e"])
        self.assertTrue(model.removeRows(2, 1))
        self.assertEqual(model.rowCount(), 2)
        check_data(["a", "d"])
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 1)
        check_data(["d"])
        self.assertTrue(model.removeRows(0, 1))
        self.assertEqual(model.rowCount(), 0)

    def test_removeColumns(self):
        """Test the removeColumns() method of MinimalTableModel."""
        model = MinimalTableModel()
        self.assertFalse(model.removeColumns(-1, 1))
        self.assertFalse(model.removeColumns(0, 1))
        model.insertRows(0, 1)
        model.insertColumns(0, 4)
        data = ["a", "b", "c", "d", "e"]
        for column, value in enumerate(data):
            index = model.index(0, column)
            model.setData(index, value)
        self.assertTrue(model.removeColumns(4, 1))
        self.assertEqual(model.columnCount(), 4)

        def check_data(expecteds):
            for column, expected in enumerate(expecteds):
                index = model.index(0, column)
                self.assertEqual(model.data(index), expected)

        check_data(["a", "b", "c", "d"])
        self.assertTrue(model.removeColumns(0, 1))
        self.assertEqual(model.columnCount(), 3)
        check_data(["b", "c", "d"])
        self.assertTrue(model.removeColumns(1, 1))
        self.assertEqual(model.columnCount(), 2)
        check_data(["b", "d"])

    def test_reset_model(self):
        """Test the reset_model() method of MinimalTableModel."""
        model = MinimalTableModel()
        data = [["a", "b", "c"], ["d", "e", "f"]]
        model.reset_model(data)
        for row, row_data in enumerate(data):
            for column, value in enumerate(row_data):
                index = model.index(row, column)
                self.assertEqual(model.data(index), value)


if __name__ == "__main__":
    unittest.main()
