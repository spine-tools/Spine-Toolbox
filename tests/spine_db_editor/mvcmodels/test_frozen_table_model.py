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

"""Contains unit tests for the ``frozen_table_model`` module."""
import unittest
from unittest.mock import MagicMock
from PySide6.QtCore import QModelIndex, QObject, Qt
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.mvcmodels.frozen_table_model import FrozenTableModel
from tests.mock_helpers import model_data_to_table, TestSpineDBManager


class TestFrozenTableModel(unittest.TestCase):
    db_codename = "frozen_table_model_test_db"

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        app_settings = MagicMock()
        logger = MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename=self.db_codename, create=True)
        self._parent = QObject()
        self._model = FrozenTableModel(self._db_mngr, self._parent)

    def tearDown(self):
        self._parent.deleteLater()
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def test_initial_dimensions_are_zero(self):
        self.assertEqual(self._model.rowCount(), 0)
        self.assertEqual(self._model.columnCount(), 0)

    def test_set_headers_empty_model(self):
        self._model.set_headers(["header 1", "header 2"])
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.headers, ["header 1", "header 2"])
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
        self.assertEqual(self._model.index(1, 1).data(), self.db_codename)

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

    def test_remove_selected_row_when_selected_row_gets_updated_during_removal(self):
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.set_headers(["alternative", "database"])
        values = {((self._db_map, id_), self._db_map) for id_ in ids}
        self._model.add_values(values)
        self.assertEqual(self._model.rowCount(), 3)
        self._model.set_selected(2)
        # Simulate tabular_view_mixin and frozen table view here.
        row_removal_handler = MagicMock()
        row_removal_handler.side_effect = lambda *args: self._model.set_selected(1)
        self._model.rowsAboutToBeRemoved.connect(row_removal_handler)
        frozen_value = self._model.get_frozen_value()
        id_to_remove = frozen_value[0][1]
        self._model.remove_values({((self._db_map, id_to_remove), self._db_map)})
        row_removal_handler.assert_called_once()
        self.assertEqual(self._model.rowCount(), 2)
        base_alternative_id = self._db_map.get_alternative_item(name="Base")["id"]
        self.assertEqual(self._model.get_frozen_value(), ((self._db_map, base_alternative_id), self._db_map))

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
        expected = [[self.db_codename, "Base"], [self.db_codename, "alternative_1"]]
        for row in range(1, self._model.rowCount()):
            for column in range(self._model.columnCount()):
                with self.subTest(f"row {row} column {column}"):
                    self.assertEqual(self._model.index(row, column).data(), expected[row - 1][column])

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
        expected = [[self.db_codename, "Base"], [self.db_codename, "alternative_1"]]
        for row in range(1, self._model.rowCount()):
            for column in range(self._model.columnCount()):
                with self.subTest(f"row {row} column {column}"):
                    self.assertEqual(self._model.index(row, column).data(), expected[row - 1][column])

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
        self.assertEqual(self._model.index(1, 0).data(), self.db_codename)

    def test_move_columns(self):
        self._model.insert_column_data("database", {self._db_map}, 0)
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.insert_column_data("alternative", {(self._db_map, id_) for id_ in ids}, 1)
        self.assertEqual(self._model.headers, ["database", "alternative"])
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertTrue(self._model.moveColumns(QModelIndex(), 1, 1, QModelIndex(), 0))
        self.assertEqual(self._model.columnCount(), 2)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.headers, ["alternative", "database"])
        expected = [["Base", self.db_codename], ["alternative_1", self.db_codename]]
        for row in range(1, self._model.rowCount()):
            for column in range(self._model.columnCount()):
                with self.subTest(f"row {row} column {column}"):
                    self.assertEqual(self._model.index(row, column).data(), expected[row - 1][column])

    def test_table_stays_sorted(self):
        self._model.insert_column_data("database", {self._db_map}, 0)
        self._db_mngr.add_alternatives({self._db_map: [{"name": "alternative_1", "id": 2}]})
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "Gadget", "id": 1}]})
        self._db_mngr.add_entities({self._db_map: [{"class_id": 1, "name": "fork"}, {"class_id": 1, "name": "spoon"}]})
        alternatives = self._db_mngr.get_items(self._db_map, "alternative")
        ids = {item["id"] for item in alternatives}
        self._model.insert_column_data("alternative", {(self._db_map, id_) for id_ in ids}, 0)
        objects = self._db_mngr.get_items(self._db_map, "entity")
        ids = {item["id"] for item in objects}
        self._model.insert_column_data("Gadget", {(self._db_map, id_) for id_ in ids}, 0)
        self.assertEqual(self._model.headers, ["Gadget", "alternative", "database"])
        self.assertEqual(self._model.columnCount(), 3)
        self.assertEqual(self._model.rowCount(), 5)
        self.assertEqual(self._model.index(0, 0).data(), "Gadget")
        self.assertEqual(self._model.index(0, 1).data(), "alternative")
        self.assertEqual(self._model.index(0, 2).data(), "database")
        self.assertEqual(self._model.index(1, 0).data(), "fork")
        self.assertEqual(self._model.index(1, 1).data(), "Base")
        self.assertEqual(self._model.index(1, 2).data(), self.db_codename)
        self.assertEqual(self._model.index(2, 0).data(), "fork")
        self.assertEqual(self._model.index(2, 1).data(), "alternative_1")
        self.assertEqual(self._model.index(2, 2).data(), self.db_codename)
        self.assertEqual(self._model.index(3, 0).data(), "spoon")
        self.assertEqual(self._model.index(3, 1).data(), "Base")
        self.assertEqual(self._model.index(3, 2).data(), self.db_codename)
        self.assertEqual(self._model.index(4, 0).data(), "spoon")
        self.assertEqual(self._model.index(4, 1).data(), "alternative_1")
        self.assertEqual(self._model.index(4, 2).data(), self.db_codename)

    def test_tooltips_work_when_no_data_is_available(self):
        self._model.insert_column_data("database", {self._db_map}, 0)
        self._db_mngr.remove_items({self._db_map: {"alternative": [1]}})
        self._model.insert_column_data("alternative", {(self._db_map, None)}, 1)
        self.assertEqual(self._model.headers, ["database", "alternative"])
        model_data = model_data_to_table(self._model)
        expected = [["database", "alternative"], [self.db_codename, None]]
        self.assertEqual(model_data, expected)
        tool_tip_data = model_data_to_table(self._model, QModelIndex(), Qt.ItemDataRole.ToolTipRole)
        expected = [["database", "alternative"], [f"<qt>{self.db_codename}</qt>", None]]
        self.assertEqual(tool_tip_data, expected)


if __name__ == "__main__":
    unittest.main()
