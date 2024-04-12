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

"""Unit tests for MapTableView class."""
import csv
import locale
from io import StringIO
import unittest
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QApplication
from spinedb_api import Map
from spinetoolbox.mvcmodels.map_model import MapModel
from spinetoolbox.widgets.custom_qtableview import MapTableView, system_lc_numeric


class TestMapTableView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._original_clip = QApplication.clipboard().text()

    def tearDown(self):
        QApplication.clipboard().setText(self._original_clip)

    def test_copy_without_selection_returns_false(self):
        table_view = MapTableView()
        model = MapModel(Map([], [], float), table_view)
        table_view.setModel(model)
        self.assertFalse(table_view.copy())
        table_view.deleteLater()

    def test_copy_selection(self):
        table_view = MapTableView()
        model = MapModel(Map(["A"], [2.3]), table_view)
        table_view.setModel(model)
        for column in (0, 1):
            table_view.selectionModel().select(model.index(0, column), QItemSelectionModel.Select)
        self.assertTrue(table_view.copy())
        clip = StringIO(QApplication.clipboard().text())
        table = [row for row in csv.reader(clip, delimiter="\t")]
        with system_lc_numeric():
            self.assertEqual(table, [["A", locale.str(2.3)]])
        table_view.deleteLater()

    def test_copy_selection_does_not_copy_expanse_row_or_column(self):
        table_view = MapTableView()
        model = MapModel(Map(["A"], [2.3]), table_view)
        table_view.setModel(model)
        for column in range(model.columnCount()):
            for row in range(model.rowCount()):
                table_view.selectionModel().select(model.index(row, column), QItemSelectionModel.Select)
        self.assertTrue(table_view.copy())
        clip = StringIO(QApplication.clipboard().text())
        table = [row for row in csv.reader(clip, delimiter="\t")]
        with system_lc_numeric():
            self.assertEqual(table, [["A", locale.str(2.3)]])
        table_view.deleteLater()

    def test_paste_without_selection_returns_false(self):
        table_view = MapTableView()
        model = MapModel(Map(["A"], [2.3]), table_view)
        table_view.setModel(model)
        self.assertFalse(table_view.paste())
        table_view.deleteLater()

    def test_paste_to_empty_table(self):
        table_view = MapTableView()
        model = MapModel(Map([], [], str), table_view)
        table_view.setModel(model)
        table_view.selectionModel().select(model.index(0, 0), QItemSelectionModel.Select)
        self._write_to_clipboard([["A", 2.3]])
        self.assertTrue(table_view.paste())
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 3)
        self.assertEqual(model.value(), Map(["A"], [2.3]))
        table_view.deleteLater()

    def test_paste_to_single_cell_pastes_everything(self):
        table_view = MapTableView()
        model = MapModel(Map(["A"], [2.3]), table_view)
        table_view.setModel(model)
        table_view.selectionModel().select(model.index(0, 0), QItemSelectionModel.Select)
        self._write_to_clipboard([["V", -5.5], ["W", -6.6]])
        self.assertTrue(table_view.paste())
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 3)
        self.assertEqual(model.value(), Map(["V", "W"], [-5.5, -6.6]))
        table_view.deleteLater()

    def test_paste_large_data_to_small_selection_cuts_data(self):
        table_view = MapTableView()
        model = MapModel(Map(["A", "B", "C"], [2.3, 3.2, 4.3]), table_view)
        table_view.setModel(model)
        for row in (0, 1):
            table_view.selectionModel().select(model.index(row, 0), QItemSelectionModel.Select)
        self._write_to_clipboard([["Q", -4.4], ["V", -5.5], ["W", -6.6]])
        self.assertTrue(table_view.paste())
        self.assertEqual(model.rowCount(), 4)
        self.assertEqual(model.columnCount(), 3)
        m = model.value()
        self.assertEqual(model.value(), Map(["Q", "V", "C"], [2.3, 3.2, 4.3]))
        table_view.deleteLater()

    @staticmethod
    def _write_to_clipboard(data):
        with StringIO() as out_string:
            writer = csv.writer(out_string, delimiter="\t")
            writer.writerows(data)
            clip = out_string.getvalue()
        QApplication.clipboard().setText(clip)


if __name__ == "__main__":
    unittest.main()
