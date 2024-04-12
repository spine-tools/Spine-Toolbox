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

"""Unit tests for the metadata table model."""
import itertools
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.mvcmodels.metadata_table_model_base import Column
from spinetoolbox.spine_db_editor.mvcmodels.metadata_table_model import MetadataTableModel
from tests.mock_helpers import TestSpineDBManager, fetch_model


class TestMetadataTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        mock_settings = mock.Mock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = TestSpineDBManager(mock_settings, None)
        logger = mock.MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="database", create=True)
        QApplication.processEvents()
        self._model = MetadataTableModel(self._db_mngr, [self._db_map], None)
        fetch_model(self._model)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._model.deleteLater()

    def test_empty_model(self):
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(self._model.columnCount(), 3)
        self.assertEqual(self._model.headerData(Column.NAME, Qt.Orientation.Horizontal), "name")
        self.assertEqual(self._model.headerData(Column.VALUE, Qt.Orientation.Horizontal), "value")
        self.assertEqual(self._model.headerData(Column.DB_MAP, Qt.Orientation.Horizontal), "database")
        self._assert_empty_last_row()

    def test_add_metadata_from_database_to_empty_model(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        self._db_mngr.add_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Anonymous")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_updating_metadata_in_database_updates_existing_row(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous"}]}
        self._db_mngr.add_metadata(db_map_data)
        index = self._model.index(0, Column.VALUE)
        self.assertTrue(self._model.setData(index, "Prof. T. Est"))
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Prof. T. Est")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_remove_metadata_removes_the_row(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        db_map_typed_ids = {self._db_map: {"metadata": {1}}}
        self._db_mngr.add_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 2)
        self._db_mngr.remove_items(db_map_typed_ids)
        self.assertEqual(self._model.rowCount(), 1)
        self._assert_empty_last_row()

    def test_filling_last_row_adds_data_to_database_and_empties_last_row(self):
        index = self._model.index(0, Column.NAME)
        self._model.setData(index, "author")
        index = self._model.index(0, Column.VALUE)
        self.assertTrue(self._model.setData(index, "Anonymous"))
        self.assertEqual(self._model.rowCount(), 2)
        self._assert_empty_last_row()

    def test_adding_data_to_another_database(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        self._db_mngr.add_metadata(db_map_data)
        logger = mock.MagicMock()
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir, "db.sqlite")
            url = "sqlite:///" + str(database_path)
            try:
                db_map_2 = self._db_mngr.get_db_map(url, logger, codename="2nd database", create=True)
                self._model.set_db_maps([self._db_map, db_map_2])
                fetch_model(self._model)
                index = self._model.index(1, Column.DB_MAP)
                self.assertTrue(self._model.setData(index, "2nd database"))
                index = self._model.index(1, Column.NAME)
                self.assertTrue(self._model.setData(index, "title"))
                index = self._model.index(1, Column.VALUE)
                self.assertTrue(self._model.setData(index, "My precious."))
            finally:
                self._db_mngr.close_session(url)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.index(1, Column.NAME).data(), "title")
        self.assertEqual(self._model.index(1, Column.VALUE).data(), "My precious.")
        self.assertEqual(self._model.index(1, Column.DB_MAP).data(), "2nd database")
        row = self._model.rowCount() - 1
        self.assertEqual(self._model.index(row, Column.NAME).data(), "")
        self.assertEqual(self._model.index(row, Column.VALUE).data(), "")
        self.assertEqual(self._model.index(row, Column.DB_MAP).data(), "2nd database")

    def test_add_and_update_via_adding_entity_metadata(self):
        db_map_data = {self._db_map: [{"name": "object class", "id": 1}]}
        self._db_mngr.add_entity_classes(db_map_data)
        db_map_data = {self._db_map: [{"class_id": 1, "name": "object"}]}
        self._db_mngr.add_entities(db_map_data)
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous"}]}
        self._db_mngr.add_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Anonymous")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()
        db_map_data = {
            self._db_map: [
                {"entity_name": "object", "metadata_name": "author", "metadata_value": "Anonymous"},
                {"entity_name": "object", "metadata_name": "source", "metadata_value": "The Internet"},
            ]
        }
        self._db_mngr.add_ext_entity_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Anonymous")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self.assertEqual(self._model.index(1, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(1, Column.VALUE).data(), "The Internet")
        self.assertEqual(self._model.index(1, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_insert_rows_to_empty_model(self):
        self._model.insertRows(0, 1)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_insert_rows_to_beginning_and_middle_and_end(self):
        self._db_mngr.add_metadata(
            {
                self._db_map: [
                    {"name": "name_1", "value": "value_1", "id": 1},
                    {"name": "name_2", "value": "value_2", "id": 2},
                ]
            }
        )
        self._model.insertRows(0, 1)
        self._model.insertRows(2, 1)
        self._model.insertRows(4, 1)
        self.assertEqual(self._model.rowCount(), 6)
        expected_rows = [
            ["", "", "database"],
            ["name_1", "value_1", "database"],
            ["", "", "database"],
            ["name_2", "value_2", "database"],
            ["", "", "database"],
        ]
        for row, expected in enumerate(expected_rows):
            self.assertEqual(self._model.index(row, Column.NAME).data(), expected[Column.NAME])
            self.assertEqual(self._model.index(row, Column.VALUE).data(), expected[Column.VALUE])
            self.assertEqual(self._model.index(row, Column.DB_MAP).data(), expected[Column.DB_MAP])
        self._assert_empty_last_row()

    def test_insert_rows_after_adder_row_extends_normal_rows_instead(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        self._db_mngr.add_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 2)
        self._model.insertRows(2, 1)
        self.assertEqual(self._model.rowCount(), 3)
        expected = [["author", "Anonymous", "database"], ["", "", "database"]]
        for row, column in itertools.product(range(2), range(self._model.columnCount())):
            self.assertEqual(self._model.index(row, column).data(), expected[row][column])
        self._assert_empty_last_row()

    def test_remove_rows_not_yet_in_database(self):
        self._model.insertRows(0, 1)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertTrue(self._model.removeRows(0, 1))
        self.assertEqual(self._model.rowCount(), 1)
        self._assert_empty_last_row()

    def test_remove_rows_also_from_database(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        self._db_mngr.add_metadata(db_map_data)
        self.assertTrue(self._model.removeRows(0, 1))
        self.assertEqual(self._model.rowCount(), 1)
        self._assert_empty_last_row()

    def test_add_metadata_using_batch_set_data(self):
        self.assertTrue(self._model.insertRows(0, 2))
        self.assertEqual(self._model.rowCount(), 3)
        indexes = [self._model.index(row, column) for row, column in itertools.product(range(2), range(2))]
        data = ["title", "My precious.", "source", "The Internet"]
        self._model.batch_set_data(indexes, data)
        expected_rows = [["title", "My precious.", "database"], ["source", "The Internet", "database"]]
        for row, expected in enumerate(expected_rows):
            self.assertEqual(self._model.index(row, Column.NAME).data(), expected[Column.NAME])
            self.assertEqual(self._model.index(row, Column.VALUE).data(), expected[Column.VALUE])
            self.assertEqual(self._model.index(row, Column.DB_MAP).data(), expected[Column.DB_MAP])
        self._assert_empty_last_row()

    def test_update_metadata_using_batch_set_data(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        self._db_mngr.add_metadata(db_map_data)
        indexes = [self._model.index(0, Column.NAME), self._model.index(0, Column.VALUE)]
        data = ["title", "My precious."]
        self._model.batch_set_data(indexes, data)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "title")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "My precious.")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_batch_set_incomplete_data(self):
        self.assertTrue(self._model.insertRows(0, 2))
        self.assertEqual(self._model.rowCount(), 3)
        indexes = [self._model.index(0, 1), self._model.index(1, 1)]
        data = ["Anonymous", "The Internet"]
        self._model.batch_set_data(indexes, data)
        expected_rows = [["", "Anonymous", "database"], ["", "The Internet", "database"]]
        for row, expected in enumerate(expected_rows):
            self.assertEqual(self._model.index(row, Column.NAME).data(), expected[Column.NAME])
            self.assertEqual(self._model.index(row, Column.VALUE).data(), expected[Column.VALUE])
            self.assertEqual(self._model.index(row, Column.DB_MAP).data(), expected[Column.DB_MAP])
        self._assert_empty_last_row()

    def test_roll_back(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous"}]}
        self._db_mngr.add_metadata(db_map_data)
        self._db_mngr.commit_session("Add test data.", self._db_map)
        index = self._model.index(1, Column.NAME)
        self.assertTrue(self._model.setData(index, "title"))
        index = self._model.index(1, Column.VALUE)
        self.assertTrue(self._model.setData(index, "My precious."))
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Anonymous")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self.assertEqual(self._model.index(1, Column.NAME).data(), "title")
        self.assertEqual(self._model.index(1, Column.VALUE).data(), "My precious.")
        self.assertEqual(self._model.index(1, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()
        self._db_mngr.rollback_session(self._db_map)
        self._db_mngr.add_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Anonymous")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def _assert_empty_last_row(self):
        row = self._model.rowCount() - 1
        self.assertEqual(self._model.index(row, Column.NAME).data(), "")
        self.assertEqual(self._model.index(row, Column.VALUE).data(), "")
        self.assertEqual(self._model.index(row, Column.DB_MAP).data(), "database")


if __name__ == "__main__":
    unittest.main()
