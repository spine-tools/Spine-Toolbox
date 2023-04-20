######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""Contains unit tests for the ``frozen_table_model`` module."""
import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import QModelIndex, QObject
from PySide6.QtWidgets import QApplication

from spinetoolbox.spine_db_editor.mvcmodels.frozen_table_model import FrozenTableModel
from tests.mock_helpers import TestSpineDBManager


class TestFrozenTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="test_db", create=True)
        self._parent = QObject()
        self._model = FrozenTableModel(self._db_mngr, self._parent)

    def tearDown(self):
        self._parent.deleteLater()
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def test_initial_dimensions_are_zero(self):
        self.assertEqual(self._model.rowCount(), 0)
        self.assertEqual(self._model.columnCount(), 0)

    def test_set_headers_empty_model(self):
        self._model.set_headers(["header 1", "header 2"])
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.index(0, 0).data(), "header 1")
        self.assertEqual(self._model.index(0, 1).data(), "header 2")

    def test_set_headers_renames_existing_ones(self):
        self._model.set_headers(["header 1", "header 2"])
        self._model.set_headers(["new header", "even newer"])
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.index(0, 0).data(), "new header")
        self.assertEqual(self._model.index(0, 1).data(), "even newer")

    def test_clear_model(self):
        self._model.set_headers(["header 1", "header 2"])
        self._model.clear_model()
        self.assertEqual(self._model.rowCount(), 0)
        self.assertEqual(self._model.columnCount(), 0)

    def test_add_values(self):
        self._model.set_headers(["alternative", "database"])
        self._model.add_values({((self._db_map, 1), self._db_map)})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.index(0, 0).data(), "alternative")
        self.assertEqual(self._model.index(0, 1).data(), "database")
        self.assertEqual(self._model.index(1, 0).data(), "Base")
        self.assertEqual(self._model.index(1, 1).data(), "test_db")

    def test_remove_values_before_selected_row(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.set_headers(["alternative", "database"])
        values = {((self._db_map, id_), self._db_map) for id_ in ids}
        self._model.add_values(values)
        self.assertEqual(self._model.rowCount(), 3)
        self._model.set_selected(2)
        frozen_value = self._model.get_frozen_value()
        frozen_alternative_id = frozen_value[0][1]
        id_to_remove = next(iter(ids - {frozen_alternative_id}))
        self._model.remove_values({((self._db_map, id_to_remove), self._db_map)})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.get_frozen_value(), ((self._db_map, frozen_alternative_id), self._db_map))

    def test_remove_values_after_selected_row(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.set_headers(["alternative", "database"])
        values = {((self._db_map, id_), self._db_map) for id_ in ids}
        self._model.add_values(values)
        self.assertEqual(self._model.rowCount(), 3)
        self._model.set_selected(1)
        frozen_value = self._model.get_frozen_value()
        frozen_alternative_id = frozen_value[0][1]
        id_to_remove = next(iter(ids - {frozen_alternative_id}))
        self._model.remove_values({((self._db_map, id_to_remove), self._db_map)})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.get_frozen_value(), ((self._db_map, frozen_alternative_id), self._db_map))

    def test_get_frozen_value(self):
        self._model.set_headers(["alternative", "database"])
        self._model.add_values({((self._db_map, 1), self._db_map)})
        self._model.set_selected(1)
        self.assertEqual(self._model.get_frozen_value(), ((self._db_map, 1), self._db_map))

    def test_insert_column_data_to_empty_model(self):
        self._model.insert_column_data("alternative", {(self._db_map, 1)}, 0)
        self.assertEqual(self._model.columnCount(), 1)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, 0).data(), "alternative")
        self.assertEqual(self._model.index(1, 0).data(), "Base")

    def test_insert_column_data_to_header_only_model(self):
        self._model.set_headers(["index 1", "index 2"])
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.rowCount(), 1)
        self._model.insert_column_data("alternative", {(self._db_map, 1)}, 1)
        self.assertEqual(self._model.columnCount(), 3)
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(self._model.index(0, 0).data(), "index 1")
        self.assertEqual(self._model.index(0, 1).data(), "alternative")
        self.assertEqual(self._model.index(0, 2).data(), "index 2")

    def test_insert_column_data_extends_existing_data_in_model(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        self._model.insert_column_data("database", {self._db_map}, 0)
        self.assertEqual(self._model.columnCount(), 1)
        self.assertEqual(self._model.rowCount(), 2)
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.insert_column_data("alternative", {(self._db_map, id_) for id_ in ids}, 1)
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.headers, ["database", "alternative"])
        names = {item["id"]: item["name"] for item in alternatives}
        expected = {("test_db", names[id_]) for id_ in ids}
        table = set()
        for row in range(2):
            row_data = []
            for column in range(self._model.columnCount()):
                row_data.append(self._model.index(row + 1, column).data())
            table.add(tuple(row_data))
        self.assertEqual(table, expected)

    def test_insert_column_data_extends_inserted_data(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.insert_column_data("alternative", {(self._db_map, id_) for id_ in ids}, 0)
        self.assertEqual(self._model.columnCount(), 1)
        self.assertEqual(self._model.rowCount(), 3)
        self._model.insert_column_data("database", {self._db_map}, 0)
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.headers, ["database", "alternative"])
        names = {item["id"]: item["name"] for item in alternatives}
        expected = {("test_db", names[id_]) for id_ in ids}
        table = set()
        for row in range(2):
            row_data = []
            for column in range(self._model.columnCount()):
                row_data.append(self._model.index(row + 1, column).data())
            table.add(tuple(row_data))
        self.assertEqual(table, expected)

    def test_remove_last_column_clears_model(self):
        self._model.insert_column_data("database", {self._db_map}, 0)
        self.assertEqual(self._model.columnCount(), 1)
        self.assertEqual(self._model.rowCount(), 2)
        self._model.remove_column(0)
        self.assertEqual(self._model.columnCount(), 0)
        self.assertEqual(self._model.rowCount(), 0)

    def test_remove_column_shortens_existing_data(self):
        self._model.insert_column_data("database", {self._db_map}, 0)
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.insert_column_data("alternative", {(self._db_map, id_) for id_ in ids}, 0)
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.rowCount(), 3)
        self._model.remove_column(0)
        self.assertEqual(self._model.columnCount(), 1)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.headers, ["database"])
        self.assertEqual(self._model.index(1, 0).data(), "test_db")

    def test_move_columns(self):
        self._model.insert_column_data("database", {self._db_map}, 0)
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.insert_column_data("alternative", {(self._db_map, id_) for id_ in ids}, 1)
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertTrue(self._model.moveColumns(QModelIndex(), 1, 1, QModelIndex(), 0))


if __name__ == '__main__':
    unittest.main()
