######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the models in ``custom_qwidgets`` module.

:author: A. Soininen (VTT)
:date:   4.2.2021
"""

import unittest
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.custom_qwidgets import DataToValueFilterWidget


class TestDataToValueFilterWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._widget = DataToValueFilterWidget(None, str)
        self._widget.set_filter_list(["ei", "bii", "cii"])

    def tearDown(self):
        self._widget.close()
        self._widget.deleteLater()

    def test_set_filter_list(self):
        self.assertFalse(self._widget.has_filter())
        model = self._widget._ui_list.model()
        data = [model.index(row, 0).data() for row in range(model.rowCount())]
        self.assertEqual(data, ["(Select all)", "(Empty)", "ei", "bii", "cii"])
        checked = [model.index(row, 0).data(Qt.CheckStateRole) for row in range(model.rowCount())]
        self.assertEqual(checked, 5 * [Qt.Checked])
        self.assertEqual(self._widget._filter_state, ["ei", "bii", "cii"])
        self.assertIsNone(self._widget._filter_empty_state)

    def test_click_Empty_item(self):
        model = self._widget._ui_list.model()
        self._widget._ui_list.clicked.emit(model.index(1, 0))
        model = self._widget._ui_list.model()
        checked = [model.index(row, 0).data(Qt.CheckStateRole) for row in range(model.rowCount())]
        self.assertEqual(checked, [Qt.Unchecked, Qt.Unchecked, Qt.Checked, Qt.Checked, Qt.Checked])
        self.assertTrue(self._widget.has_filter())

    def test_click_item(self):
        model = self._widget._ui_list.model()
        self._widget._ui_list.clicked.emit(model.index(2, 0))
        model = self._widget._ui_list.model()
        checked = [model.index(row, 0).data(Qt.CheckStateRole) for row in range(model.rowCount())]
        self.assertEqual(checked, [Qt.Unchecked, Qt.Checked, Qt.Unchecked, Qt.Checked, Qt.Checked])
        self.assertTrue(self._widget.has_filter())

    def test_click_Select_All_item(self):
        model = self._widget._ui_list.model()
        self._widget._ui_list.clicked.emit(model.index(0, 0))
        model = self._widget._ui_list.model()
        checked = [model.index(row, 0).data(Qt.CheckStateRole) for row in range(model.rowCount())]
        self.assertEqual(checked, 5 * [Qt.Unchecked])
        self.assertTrue(self._widget.has_filter())

    def test_save_state(self):
        model = self._widget._ui_list.model()
        self._widget._ui_list.clicked.emit(model.index(2, 0))
        self._widget.save_state()
        self.assertEqual(self._widget._filter_state, {"bii", "cii"})
        self.assertTrue(self._widget._filter_empty_state)


if __name__ == "__main__":
    unittest.main()
