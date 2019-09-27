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
from project_items.gdx_export.widgets.gdx_export_settings import GAMSRecordListModel, GAMSSetListModel
from spine_io.exporters.gdx import Settings

class TestGAMSSetListModel(unittest.TestCase):
    """Unit tests for the GAMSSetListModel class used by the Gdx Export Settings Window."""

    def test_data_DisplayRole(self):
        settings = Settings(['a'], ['b'], {})
        model = GAMSSetListModel(settings)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "a")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "b")

    def test_data_BackgroundRole(self):
        settings = Settings(['a'], ['b'], {})
        model = GAMSSetListModel(settings)
        index = model.index(0, 0)
        self.assertEqual(index.data(Qt.BackgroundRole), QColor(Qt.lightGray))
        index = model.index(1, 0)
        self.assertEqual(index.data(Qt.BackgroundRole), None)

    def test_data_CheckStateRole(self):
        settings = Settings(['a'], ['b'], {}, [False], [False])
        model = GAMSSetListModel(settings)
        index = model.index(0, 0)
        self.assertEqual(index.data(Qt.CheckStateRole), Qt.Unchecked)
        index = model.index(1, 0)
        self.assertEqual(index.data(Qt.CheckStateRole), Qt.Unchecked)

    def test_flags(self):
        settings = Settings(['a'], ['b'], {})
        model = GAMSSetListModel(settings)
        flags = model.flags(model.index(0, 0))
        self.assertEqual(flags, Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)

    def test_headerData(self):
        settings = Settings([], [], {})
        model = GAMSSetListModel(settings)
        self.assertEqual(model.headerData(0, Qt.Horizontal), "")

    def test_is_domain(self):
        settings = Settings(['a'], ['b'], {})
        model = GAMSSetListModel(settings)
        self.assertTrue(model.is_domain(model.index(0, 0)))
        self.assertFalse(model.is_domain(model.index(1, 0)))

    def test_moveRows_move_domain_row_down(self):
        settings = Settings(['a', 'b', 'c'], [], {}, [True, False, False])
        model = GAMSSetListModel(settings)
        self.assertTrue(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))
        self.assertEqual(settings.sorted_domain_names, ['b', 'a', 'c'])
        self.assertEqual(settings.domain_exportable_flags, [False, True, False])
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 2))
        self.assertEqual(settings.sorted_domain_names, ['b', 'c', 'a'])
        self.assertEqual(settings.domain_exportable_flags, [False, False, True])
        self.assertFalse(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 3))

    def test_moveRows_move_domain_row_up(self):
        settings = Settings(['a', 'b', 'c'], [], {}, [False, False, True])
        model = GAMSSetListModel(settings)
        self.assertTrue(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 1))
        self.assertEqual(settings.sorted_domain_names, ['a', 'c', 'b'])
        self.assertEqual(settings.domain_exportable_flags, [False, True, False])
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))
        self.assertEqual(settings.sorted_domain_names, ['c', 'a', 'b'])
        self.assertEqual(settings.domain_exportable_flags, [True, False, False])
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), -1))

    def test_moveRows_domain_cannot_cross_to_sets(self):
        settings = Settings(['a'], ['b'], {})
        model = GAMSSetListModel(settings)
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))

    def test_moveRows_move_set_row_down(self):
        settings = Settings([], ['a', 'b', 'c'], {}, [], [True, False, False])
        model = GAMSSetListModel(settings)
        self.assertTrue(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))
        self.assertEqual(settings.sorted_set_names, ['b', 'a', 'c'])
        self.assertEqual(settings.set_exportable_flags, [False, True, False])
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 2))
        self.assertEqual(settings.sorted_set_names, ['b', 'c', 'a'])
        self.assertEqual(settings.set_exportable_flags, [False, False, True])
        self.assertFalse(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 3))

    def test_moveRows_move_set_row_up(self):
        settings = Settings([], ['a', 'b', 'c'], {}, [], [False, False, True])
        model = GAMSSetListModel(settings)
        self.assertTrue(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 1))
        self.assertEqual(settings.sorted_set_names, ['a', 'c', 'b'])
        self.assertEqual(settings.set_exportable_flags, [False, True, False])
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))
        self.assertEqual(settings.sorted_set_names, ['c', 'a', 'b'])
        self.assertEqual(settings.set_exportable_flags, [True, False, False])
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), -1))

    def test_moveRows_set_cannot_cross_to_domains(self):
        settings = Settings(['a'], ['b'], {})
        model = GAMSSetListModel(settings)
        self.assertFalse(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))

    def test_rowCount(self):
        settings = Settings(['a'], ['b'], {})
        model = GAMSSetListModel(settings)
        self.assertEqual(model.rowCount(), 2)

    def test_setData_CheckStateRole(self):
        settings = Settings(['a'], ['b'], {})
        model = GAMSSetListModel(settings)
        index = model.index(0, 0)
        model.setData(index, Qt.Unchecked, Qt.CheckStateRole)
        self.assertEqual(settings.domain_exportable_flags[0], False)
        index = model.index(1, 0)
        model.setData(index, Qt.Unchecked, Qt.CheckStateRole)
        self.assertEqual(settings.set_exportable_flags[0], False)



if __name__ == '__main__':
    unittest.main()
