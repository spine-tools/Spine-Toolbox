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

"""Unit tests for the ``utils`` module."""
import unittest
from PySide6.QtCore import QObject
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.mvcmodels.utils import two_column_as_csv


class TestTwoColumnAsCsv(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._parent = QObject()

    def tearDown(self):
        self._parent.deleteLater()

    def test_indexes_from_two_columns(self):
        model = QStandardItemModel(self._parent)
        data = [["11", "12"], ["21", "22"]]
        for y, row in enumerate(data):
            for x, cell in enumerate(row):
                item = QStandardItem(cell)
                model.setItem(y, x, item)
        indexes = []
        for y in range(model.rowCount()):
            for x in range(model.columnCount()):
                indexes.append(model.index(y, x))
        as_csv = two_column_as_csv(indexes)
        self.assertEqual(as_csv, "11\t12\r\n21\t22\r\n")

    def test_indexes_from_single_column(self):
        model = QStandardItemModel(self._parent)
        data = [["11", "12"], ["21", "22"]]
        for y, row in enumerate(data):
            for x, cell in enumerate(row):
                item = QStandardItem(cell)
                model.setItem(y, x, item)
        indexes = []
        for y in range(model.rowCount()):
            indexes.append(model.index(y, 1))
        as_csv = two_column_as_csv(indexes)
        self.assertEqual(as_csv, "12\r\n22\r\n")


if __name__ == "__main__":
    unittest.main()
