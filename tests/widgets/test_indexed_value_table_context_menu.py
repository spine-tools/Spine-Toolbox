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
Unit tests for the indexed_value_table_context_menu module.

:author: A. Soininen (VTT)
:date:   5.7.2019
"""

import unittest
from spinetoolbox.widgets.indexed_value_table_context_menu import _remove_rows


class _MockModel:
    def __init__(self):
        self.row = list()
        self.count = list()

    def removeRows(self, row, count):
        self.row.append(row)
        self.count.append(count)


class TestIndexedValueTableContextMenu(unittest.TestCase):
    def test_remove_rows_first_row(self):
        model = _MockModel()
        selected_rows = [0]
        _remove_rows(selected_rows, model)
        self.assertEqual(len(model.row), 1)
        self.assertEqual(model.row[0], 0)
        self.assertEqual(len(model.count), 1)
        self.assertEqual(model.count[0], 1)

    def test_remove_rows_single_row(self):
        model = _MockModel()
        selected_rows = [23]
        _remove_rows(selected_rows, model)
        self.assertEqual(len(model.row), 1)
        self.assertEqual(model.row[0], 23)
        self.assertEqual(len(model.count), 1)
        self.assertEqual(model.count[0], 1)

    def test_remove_rows_single_block(self):
        model = _MockModel()
        selected_rows = [3, 4, 5]
        _remove_rows(selected_rows, model)
        self.assertEqual(len(model.row), 1)
        self.assertEqual(model.row[0], 3)
        self.assertEqual(len(model.count), 1)
        self.assertEqual(model.count[0], 3)

    def test_remove_rows_multiple_blocks(self):
        model = _MockModel()
        selected_rows = [3, 4, 5, 7]
        _remove_rows(selected_rows, model)
        self.assertEqual(len(model.row), 2)
        self.assertEqual(model.row[0], 7)
        self.assertEqual(model.row[1], 3)
        self.assertEqual(len(model.count), 2)
        self.assertEqual(model.count[0], 1)
        self.assertEqual(model.count[1], 3)

    def test_remove_rows_scattered(self):
        model = _MockModel()
        selected_rows = [3, 5, 6, 8, 10]
        _remove_rows(selected_rows, model)
        self.assertEqual(len(model.row), 4)
        self.assertEqual(model.row[0], 10)
        self.assertEqual(model.row[1], 8)
        self.assertEqual(model.row[2], 5)
        self.assertEqual(model.row[3], 3)
        self.assertEqual(len(model.count), 4)
        self.assertEqual(model.count[0], 1)
        self.assertEqual(model.count[1], 1)
        self.assertEqual(model.count[2], 2)
        self.assertEqual(model.count[3], 1)


if __name__ == '__main__':
    unittest.main()
