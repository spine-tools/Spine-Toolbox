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
Unit tests for Gdx Export settings widget and related MVC models.

:authors: A. Soininen (VTT)
:date:   26.9.2019
"""

import unittest
from PySide2.QtCore import QModelIndex, Qt
from PySide2.QtGui import QColor
from spinetoolbox.project_items.exporter.widgets.gdx_export_settings import GAMSRecordListModel, GAMSSetListModel
from spinetoolbox.spine_io.exporters.gdx import ExportFlag, SetMetadata, SetSettings


class TestGAMSSetListModel(unittest.TestCase):
    """Unit tests for the GAMSSetListModel class used by the Gdx Export Settings Window."""

    def test_data_DisplayRole(self):
        set_settings = SetSettings(['domain1'], ['set1'], {})
        domain_dependencies = {"domain1": ["set1"]}
        set_dependencies = {"set1": {"domain1": True}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_dependencies)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "domain1")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "set1")

    def test_data_BackgroundRole(self):
        set_settings = SetSettings(['domain1'], ['set1'], {})
        domain_dependencies = {"domain1": ["set1"]}
        set_export_dependencies = {"set1": {"domain1": True}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_export_dependencies)
        index = model.index(0, 0)
        self.assertEqual(index.data(Qt.BackgroundRole), QColor(Qt.lightGray))
        index = model.index(1, 0)
        self.assertEqual(index.data(Qt.BackgroundRole), None)

    def test_data_CheckStateRole(self):
        set_settings = SetSettings(
            ['domain1'],
            ['set1'],
            {},
            [SetMetadata(ExportFlag.NON_EXPORTABLE)],
            [SetMetadata(ExportFlag.NON_EXPORTABLE)],
        )
        domain_dependencies = {"domain1": ["set1"]}
        set_dependencies = {"set1": {"domain1": False}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_dependencies)
        index = model.index(0, 0)
        self.assertEqual(index.data(Qt.CheckStateRole), Qt.Unchecked)
        index = model.index(1, 0)
        self.assertEqual(index.data(Qt.CheckStateRole), Qt.Unchecked)

    def test_flags(self):
        set_settings = SetSettings(['domain1'], ['set1'], {})
        domain_dependencies = {"domain1": ["set1"]}
        set_dependencies = {"set1": {"domain1": False}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_dependencies)
        flags = model.flags(model.index(0, 0))
        self.assertEqual(flags, Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)

    def test_headerData(self):
        set_settings = SetSettings([], [], {})
        domain_dependencies = {}
        set_dependencies = {}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_dependencies)
        self.assertEqual(model.headerData(0, Qt.Horizontal), "")

    def test_is_domain(self):
        set_settings = SetSettings(['domain1'], ['set1'], {})
        domain_dependencies = {"domain1": ["set1"]}
        set_dependencies = {"set1": {"domain1": False}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_dependencies)
        self.assertTrue(model.is_domain(model.index(0, 0)))
        self.assertFalse(model.is_domain(model.index(1, 0)))

    def test_moveRows_move_domain_row_down(self):
        set_settings = SetSettings(
            ['domain1', 'domain2', 'domain3'],
            [],
            {},
            [
                SetMetadata(ExportFlag.EXPORTABLE),
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
            ],
        )
        domain_dependencies = {"domain1": [], "domain2": [], "domain3": []}
        set_dependencies = {}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_dependencies)
        self.assertTrue(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))
        self.assertEqual(set_settings.sorted_domain_names, ['domain2', 'domain1', 'domain3'])
        self.assertEqual(
            set_settings.domain_metadatas,
            [
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
            ],
        )
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 2))
        self.assertEqual(set_settings.sorted_domain_names, ['domain2', 'domain3', 'domain1'])
        self.assertEqual(
            set_settings.domain_metadatas,
            [
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
                SetMetadata(ExportFlag.EXPORTABLE),
            ],
        )
        self.assertFalse(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 3))

    def test_moveRows_move_domain_row_up(self):
        set_settings = SetSettings(
            ['domain1', 'domain2', 'domain3'],
            [],
            {},
            [
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
                SetMetadata(ExportFlag.EXPORTABLE),
            ],
        )
        domain_dependencies = {"domain1": [], "domain2": [], "domain3": []}
        set_export_dependencies = {}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_export_dependencies)
        self.assertTrue(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 1))
        self.assertEqual(set_settings.sorted_domain_names, ['domain1', 'domain3', 'domain2'])
        self.assertEqual(
            set_settings.domain_metadatas,
            [
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
            ],
        )
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))
        self.assertEqual(set_settings.sorted_domain_names, ['domain3', 'domain1', 'domain2'])
        self.assertEqual(
            set_settings.domain_metadatas,
            [
                SetMetadata(ExportFlag.EXPORTABLE),
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
            ],
        )
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), -1))

    def test_moveRows_domain_cannot_cross_to_sets(self):
        set_settings = SetSettings(['domain1'], ['domain2'], {})
        domain_dependencies = {"domain1": ["set1"]}
        set_export_dependencies = {"set1": {"domain1": True}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_export_dependencies)
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))

    def test_moveRows_move_set_row_down(self):
        set_settings = SetSettings(
            [],
            ['set1', 'set2', 'set3'],
            {},
            [],
            [
                SetMetadata(ExportFlag.EXPORTABLE),
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
            ],
        )
        domain_dependencies = {}
        set_export_dependencies = {"set1": {}, "set2": {}, "set3": {}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_export_dependencies)
        self.assertTrue(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), 1))
        self.assertEqual(set_settings.sorted_set_names, ['set2', 'set1', 'set3'])
        self.assertEqual(
            set_settings.set_metadatas,
            [
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
            ],
        )
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 2))
        self.assertEqual(set_settings.sorted_set_names, ['set2', 'set3', 'set1'])
        self.assertEqual(
            set_settings.set_metadatas,
            [
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
                SetMetadata(ExportFlag.EXPORTABLE),
            ],
        )
        self.assertFalse(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 3))

    def test_moveRows_move_set_row_up(self):
        set_settings = SetSettings(
            [],
            ['set1', 'set2', 'set3'],
            {},
            [],
            [
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
                SetMetadata(ExportFlag.EXPORTABLE),
            ],
        )
        domain_dependencies = {}
        set_export_dependencies = {"set1": {}, "set2": {}, "set3": {}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_export_dependencies)
        self.assertTrue(model.moveRows(QModelIndex(), 2, 1, QModelIndex(), 1))
        self.assertEqual(set_settings.sorted_set_names, ['set1', 'set3', 'set2'])
        self.assertEqual(
            set_settings.set_metadatas,
            [
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
            ],
        )
        self.assertTrue(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))
        self.assertEqual(set_settings.sorted_set_names, ['set3', 'set1', 'set2'])
        self.assertEqual(
            set_settings.set_metadatas,
            [
                SetMetadata(ExportFlag.EXPORTABLE),
                SetMetadata(ExportFlag.NON_EXPORTABLE),
                SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE),
            ],
        )
        self.assertFalse(model.moveRows(QModelIndex(), 0, 1, QModelIndex(), -1))

    def test_moveRows_set_cannot_cross_to_domains(self):
        set_settings = SetSettings(['domain1'], ['set1'], {})
        domain_dependencies = {"domain1": ["set1"]}
        set_export_dependencies = {"set1": {"domain1": True}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_export_dependencies)
        self.assertFalse(model.moveRows(QModelIndex(), 1, 1, QModelIndex(), 0))

    def test_rowCount(self):
        set_settings = SetSettings(['domain1'], ['set1'], {})
        domain_dependencies = {"domain1": ["set1"]}
        set_export_dependencies = {"set1": {"domain1": True}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_export_dependencies)
        self.assertEqual(model.rowCount(), 2)

    def test_setData_CheckStateRole(self):
        set_settings = SetSettings(['domain1'], ['set1'], {})
        domain_dependencies = {"domain1": ["set1"]}
        set_export_dependencies = {"set1": {"domain1": True}}
        model = GAMSSetListModel(set_settings, domain_dependencies, set_export_dependencies)
        index = model.index(0, 0)
        model.setData(index, Qt.Unchecked, Qt.CheckStateRole)
        self.assertEqual(set_settings.domain_metadatas[0], SetMetadata(ExportFlag.NON_EXPORTABLE))
        self.assertEqual(set_settings.set_metadatas[0], SetMetadata(ExportFlag.FORCED_NON_EXPORTABLE))
        model.setData(index, Qt.Checked, Qt.CheckStateRole)
        self.assertEqual(set_settings.domain_metadatas[0], SetMetadata(ExportFlag.EXPORTABLE))
        self.assertEqual(set_settings.set_metadatas[0], SetMetadata(ExportFlag.EXPORTABLE))
        index = model.index(1, 0)
        model.setData(index, Qt.Unchecked, Qt.CheckStateRole)
        self.assertEqual(set_settings.set_metadatas[0], SetMetadata(ExportFlag.NON_EXPORTABLE))


class TestGAMSRecordListModel(unittest.TestCase):
    """Unit tests for the GAMSRecordListModel class used by the Gdx Export Settings Window."""

    def test_data(self):
        model = GAMSRecordListModel()
        model.reset([("key1", "key2")], "set")
        index = model.index(0, 0)
        self.assertEqual(index.data(), "key1, key2")

    def test_headerData(self):
        model = GAMSRecordListModel()
        self.assertEqual(model.headerData(0, Qt.Horizontal), '')
        self.assertEqual(model.headerData(0, Qt.Vertical), 1)

    def test_moveRows_down(self):
        model = GAMSRecordListModel()
        model.reset([("key1",), ("key2",), ("key3",)], "set")
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
        model.reset([("key1",), ("key2",), ("key3",)], "set")
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
        model.reset([("key1", "key2")], "set")
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.index(0, 0).data(), "key1, key2")

    def test_rowCount(self):
        model = GAMSRecordListModel()
        self.assertEqual(model.rowCount(), 0)
        model.reset([["key1"]], "set")
        self.assertEqual(model.rowCount(), 1)


if __name__ == '__main__':
    unittest.main()
