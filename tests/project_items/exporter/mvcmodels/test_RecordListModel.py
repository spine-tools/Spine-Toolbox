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
Unit tests for :class:`RecordListModel`.

:authors: A. Soininen (VTT)
:date:   26.9.2019
"""
import unittest
from PySide2.QtCore import QModelIndex, Qt
from spinetoolbox.spine_io.exporters import gdx
from spinetoolbox.project_items.exporter.mvcmodels.record_list_model import RecordListModel


class TestRecordListModel(unittest.TestCase):
    """Unit tests for the RecordListModel class used by the Gdx Export Settings Window."""

    def test_data(self):
        model = RecordListModel()
        model.reset(gdx.LiteralRecords([("key1", "key2")]), "set")
        index = model.index(0, 0)
        self.assertEqual(index.data(), "key1, key2")

    def test_headerData(self):
        model = RecordListModel()
        self.assertEqual(model.headerData(0, Qt.Horizontal), "")
        self.assertEqual(model.headerData(0, Qt.Vertical), 1)

    def test_moveRows_down(self):
        model = RecordListModel()
        model.reset(gdx.LiteralRecords([("key1",), ("key2",), ("key3",)]), "set")
        no_parent = QModelIndex()
        self.assertTrue(model.moveRows(no_parent, 0, 1, no_parent, 1))
        self.assertEqual(model.index(0, 0).data(), "key2")
        self.assertEqual(model.index(1, 0).data(), "key1")
        self.assertEqual(model.index(2, 0).data(), "key3")
        self.assertTrue(model.moveRows(no_parent, 1, 1, no_parent, 2))
        self.assertEqual(model.index(0, 0).data(), "key2")
        self.assertEqual(model.index(1, 0).data(), "key3")
        self.assertEqual(model.index(2, 0).data(), "key1")
        self.assertFalse(model.moveRows(no_parent, 2, 1, no_parent, 3))

    def test_moveRows_up(self):
        model = RecordListModel()
        model.reset(gdx.LiteralRecords([("key1",), ("key2",), ("key3",)]), "set")
        no_parent = QModelIndex()
        self.assertTrue(model.moveRows(no_parent, 2, 1, no_parent, 1))
        self.assertEqual(model.index(0, 0).data(), "key1")
        self.assertEqual(model.index(1, 0).data(), "key3")
        self.assertEqual(model.index(2, 0).data(), "key2")
        self.assertTrue(model.moveRows(no_parent, 1, 1, no_parent, 0))
        self.assertEqual(model.index(0, 0).data(), "key3")
        self.assertEqual(model.index(1, 0).data(), "key1")
        self.assertEqual(model.index(2, 0).data(), "key2")
        self.assertFalse(model.moveRows(no_parent, 0, 1, no_parent, -1))

    def test_reset(self):
        model = RecordListModel()
        self.assertEqual(model.rowCount(), 0)
        model.reset(gdx.LiteralRecords([("key1", "key2")]), "set")
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(), "key1, key2")

    def test_rowCount(self):
        model = RecordListModel()
        self.assertEqual(model.rowCount(), 0)
        model.reset(gdx.LiteralRecords([("key1",)]), "set")
        self.assertEqual(model.rowCount(), 1)


if __name__ == "__main__":
    unittest.main()
