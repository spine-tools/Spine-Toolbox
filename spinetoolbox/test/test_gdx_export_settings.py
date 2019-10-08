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
Unit tests for Gdx Export settings widget and related MVC models.

:authors: A. Soininen (VTT)
:date:   26.9.2019
"""

import unittest
from PySide2.QtCore import QModelIndex, Qt
from PySide2.QtGui import QColor
from spinetoolbox.project_items.gdx_export.widgets.gdx_export_settings import GAMSRecordListModel, GAMSSetListModel
from spinetoolbox.spine_io.exporters.gdx import Settings


class TestGAMSSetListModel(unittest.TestCase):
    """Unit tests for the GAMSSetListModel class used by the Gdx Export Settings Window."""

    def test_data_DisplayRole(self):
        settings = Settings(['domain1'], ['set1'], {})
        model = GAMSSetListModel(settings)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "domain1")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "set1")

    def test_data_BackgroundRole(self):
        settings = Settings(['domain1'], ['set1'], {})
        model = GAMSSetListModel(settings)
        index = model.index(0, 0)
        self.assertEqual(index.data(Qt.BackgroundRole), QColor(Qt.lightGray))
        index = model.index(1, 0)
        self.assertEqual(index.data(Qt.BackgroundRole), None)

    def test_data_CheckStateRole(self):
        settings = Settings(['domain1'], ['set1'], {}, [False], [False])
        model = GAMSSetListModel(settings)
        index = model.index(0, 0)
        self.assertEqual(index.data(Qt.CheckStateRole), Qt.Unchecked)
        index = model.index(1, 0)
        self.assertEqual(index.data(Qt.CheckStateRole), Qt.Unchecked)

    def test_flags(self):
        settings = Settings(['domain1'], ['set1'], {})
        model = GAMSSetListModel(settings)
        flags = model.flags(model.index(0, 0))
        self.assertEqual(flags, Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)

    def test_headerData(self):
        settings = Settings([], [], {})
        model = GAMSSetListModel(settings)
        self.assertEqual(model.headerData(0, Qt.Horizontal), "")

    def test_is_domain(self):
        settings = Settings(['domain1'], ['set1'], {})
        model = GAMSSetListModel(settings)
        self.assertTrue(model.is_domain(model.index(0, 0)))
        self.assertFalse(model.is_domain(model.index(1, 0)))

    def test_moveRows_move_domain_row_down(self):
        settings = Settings(['domain1', 'domain2', 'domain3'], [], {}, [True, False, False])
        model = GAMSSetListModel(settings)
        self.assertTrue(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))
        self.assertEqual(settings.sorted_domain_names, ['domain2', 'domain1', 'domain3'])
        self.assertEqual(settings.domain_exportable_flags, [False, True, False])
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 2))
        self.assertEqual(settings.sorted_domain_names, ['domain2', 'domain3', 'domain1'])
        self.assertEqual(settings.domain_exportable_flags, [False, False, True])
        self.assertFalse(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 3))

    def test_moveRows_move_domain_row_up(self):
        settings = Settings(['domain1', 'domain2', 'domain3'], [], {}, [False, False, True])
        model = GAMSSetListModel(settings)
        self.assertTrue(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 1))
        self.assertEqual(settings.sorted_domain_names, ['domain1', 'domain3', 'domain2'])
        self.assertEqual(settings.domain_exportable_flags, [False, True, False])
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))
        self.assertEqual(settings.sorted_domain_names, ['domain3', 'domain1', 'domain2'])
        self.assertEqual(settings.domain_exportable_flags, [True, False, False])
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), -1))

    def test_moveRows_domain_cannot_cross_to_sets(self):
        settings = Settings(['domain1'], ['domain2'], {})
        model = GAMSSetListModel(settings)
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))

    def test_moveRows_move_set_row_down(self):
        settings = Settings([], ['set1', 'set2', 'set3'], {}, [], [True, False, False])
        model = GAMSSetListModel(settings)
        self.assertTrue(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))
        self.assertEqual(settings.sorted_set_names, ['set2', 'set1', 'set3'])
        self.assertEqual(settings.set_exportable_flags, [False, True, False])
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 2))
        self.assertEqual(settings.sorted_set_names, ['set2', 'set3', 'set1'])
        self.assertEqual(settings.set_exportable_flags, [False, False, True])
        self.assertFalse(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 3))

    def test_moveRows_move_set_row_up(self):
        settings = Settings([], ['set1', 'set2', 'set3'], {}, [], [False, False, True])
        model = GAMSSetListModel(settings)
        self.assertTrue(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 1))
        self.assertEqual(settings.sorted_set_names, ['set1', 'set3', 'set2'])
        self.assertEqual(settings.set_exportable_flags, [False, True, False])
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))
        self.assertEqual(settings.sorted_set_names, ['set3', 'set1', 'set2'])
        self.assertEqual(settings.set_exportable_flags, [True, False, False])
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), -1))

    def test_moveRows_set_cannot_cross_to_domains(self):
        settings = Settings(['domain1'], ['set1'], {})
        model = GAMSSetListModel(settings)
        self.assertFalse(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))

    def test_rowCount(self):
        settings = Settings(['domain1'], ['set1'], {})
        model = GAMSSetListModel(settings)
        self.assertEqual(model.rowCount(), 2)

    def test_setData_CheckStateRole(self):
        settings = Settings(['domain1'], ['set1'], {})
        model = GAMSSetListModel(settings)
        index = model.index(0, 0)
        model.setData(index, Qt.Unchecked, Qt.CheckStateRole)
        self.assertEqual(settings.domain_exportable_flags[0], False)
        index = model.index(1, 0)
        model.setData(index, Qt.Unchecked, Qt.CheckStateRole)
        self.assertEqual(settings.set_exportable_flags[0], False)


class TestGAMSRecordListModel(unittest.TestCase):
    """Unit tests for the GAMSRecordListModel class used by the Gdx Export Settings Window."""

    def test_data(self):
        model = GAMSRecordListModel()
        model.reset([['key1', 'key2']])
        index = model.index(0, 0)
        self.assertEqual(index.data(), "key1, key2")

    def test_headerData(self):
        model = GAMSRecordListModel()
        self.assertEqual(model.headerData(0, Qt.Horizontal), '')
        self.assertEqual(model.headerData(0, Qt.Vertical), 1)

    def test_moveRows_down(self):
        model = GAMSRecordListModel()
        model.reset([['key1'], ['key2'], ['key3']])
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
        model = GAMSRecordListModel()
        model.reset([['key1'], ['key2'], ['key3']])
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
        model = GAMSRecordListModel()
        self.assertEqual(model.rowCount(), 0)
        model.reset([['key1', 'key2']])
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(), "key1, key2")

    def test_rowCount(self):
        model = GAMSRecordListModel()
        self.assertEqual(model.rowCount(), 0)
        model.reset([['key1']])
        self.assertEqual(model.rowCount(), 1)


if __name__ == '__main__':
    unittest.main()
