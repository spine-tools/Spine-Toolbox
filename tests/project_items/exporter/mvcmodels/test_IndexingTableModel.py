######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Tests for :class:`IndexingTableModel`.

:author: A. Soininen (VTT)
:date:   1.9.2020
"""

import unittest
from PySide2.QtCore import QModelIndex, Qt
from PySide2.QtWidgets import QApplication
from spinedb_api.parameter_value import TimePattern
import spinetoolbox.spine_io.exporters.gdx as gdx
from spinetoolbox.project_items.exporter.mvcmodels.indexing_table_model import IndexingTableModel


class TestIndexingTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        time_series1 = TimePattern(["s1", "s2"], [-1.1, -2.2])
        time_series2 = TimePattern(["t1", "t2"], [1.1, 2.2])
        parameter = gdx.Parameter(["domain1", "domain2"], [("A1", "B1"), ("A2", "B2")], [time_series1, time_series2])
        self._model = IndexingTableModel(parameter)

    def testIndexingTableModel_construction(self):
        self.assertEqual(self._model.get_picking(), gdx.FixedPicking([]))
        self.assertEqual(self._model.columnCount(), 3)
        self.assertEqual(self._model.rowCount(), 0)
        self.assertEqual(self._model.headerData(1, Qt.Horizontal), "A1, B1")
        self.assertEqual(self._model.headerData(2, Qt.Horizontal), "A2, B2")

    def test_set_records(self):
        self._model.set_records(gdx.LiteralRecords([("i1",), ("i2",)]))
        self._model.fetchMore(QModelIndex())
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.get_picking(), gdx.FixedPicking([True, True]))
        self.assertEqual(self._model.index(0, 0).data(), "i1")
        self.assertEqual(self._model.index(1, 0).data(), "i2")
        self.assertEqual(self._model.index(0, 1).data(), "-1.1")
        self.assertEqual(self._model.index(1, 1).data(), "-2.2")
        self.assertEqual(self._model.index(0, 2).data(), "1.1")
        self.assertEqual(self._model.index(1, 2).data(), "2.2")

    def test_set_selection(self):
        self._model.set_records(gdx.LiteralRecords([("i1",), ("i2",), ("i3",)]))
        self._model.set_picking(gdx.FixedPicking([True, False, True]))
        self._model.fetchMore(QModelIndex())
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.index(0, 0).data(), "i1")
        self.assertEqual(self._model.index(1, 0).data(), "i2")
        self.assertEqual(self._model.index(2, 0).data(), "i3")
        self.assertEqual(self._model.index(0, 1).data(), "-1.1")
        self.assertEqual(self._model.index(1, 1).data(), None)
        self.assertEqual(self._model.index(2, 1).data(), "-2.2")
        self.assertEqual(self._model.index(0, 2).data(), "1.1")
        self.assertEqual(self._model.index(1, 2).data(), None)
        self.assertEqual(self._model.index(2, 2).data(), "2.2")
        self.assertEqual(self._model.mapped_values_balance(), 0)
        self.assertEqual(self._model.get_picking(), gdx.FixedPicking([True, False, True]))


if __name__ == '__main__':
    unittest.main()
