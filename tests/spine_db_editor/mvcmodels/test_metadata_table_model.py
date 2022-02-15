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
Unit tests for the metadata table model.

:author: A. Soininen (VTT)
:date:   30.3.2022
"""
import itertools
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtCore import QModelIndex, Qt
from PySide2.QtWidgets import QApplication
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.mvcmodels.metadata_table_model import Column, MetadataTableModel


class TestMetadataTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        mock_settings = mock.Mock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        logger = mock.MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="database", create=True)
        QApplication.processEvents()
        self._model = MetadataTableModel(self._db_mngr, [self._db_map])
        self._model.fetchMore(QModelIndex())

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._model.deleteLater()

    def test_empty_model(self):
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(self._model.columnCount(), 3)
        self.assertEqual(self._model.headerData(Column.NAME, Qt.Horizontal), "name")
        self.assertEqual(self._model.headerData(Column.VALUE, Qt.Horizontal), "value")
        self.assertEqual(self._model.headerData(Column.DB_MAP, Qt.Horizontal), "db_map")
        self._assert_empty_last_row()

    def test_add_metadata_from_database_to_empty_model(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        self._model.add_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Anonymous")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_updating_metadata_in_database_updates_existing_row(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        change_listener = _MetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.metadata_added) as waiter:
            self._db_mngr.add_metadata(db_map_data)
            waiter.wait()
        self._model.add_metadata(change_listener.added_items)
        with signal_waiter(self._db_mngr.metadata_updated) as waiter:
            index = self._model.index(0, Column.VALUE)
            self.assertTrue(self._model.setData(index, "Prof. T. Est"))
            waiter.wait()
        self._model.update_metadata(change_listener.updated_items)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Prof. T. Est")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_remove_metadata_removes_the_row(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        self._model.add_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 2)
        self._model.remove_metadata(db_map_data)
        self.assertEqual(self._model.rowCount(), 1)
        self._assert_empty_last_row()

    def test_filling_last_row_adds_data_to_database_and_empties_last_row(self):
        index = self._model.index(0, Column.NAME)
        self._model.setData(index, "author")
        index = self._model.index(0, Column.VALUE)
        listener = _MetadataChangeListener()
        self._db_mngr.register_listener(listener, self._db_map)
        with signal_waiter(self._db_mngr.metadata_added) as waiter:
            self.assertTrue(self._model.setData(index, "Anonymous"))
            waiter.wait()
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(
            listener.added_items, {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1, "commit_id": None}]}
        )
        self._assert_empty_last_row()

    def test_adding_data_to_another_database(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        change_listener = _MetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.metadata_added) as waiter:
            self._db_mngr.add_metadata(db_map_data)
            waiter.wait()
        self._model.add_metadata(change_listener.added_items)
        logger = mock.MagicMock()
        with TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir, "db.sqlite")
            url = "sqlite:///" + str(database_path)
            try:
                db_map_2 = self._db_mngr.get_db_map(url, logger, codename="2nd database", create=True)
                self._model.set_db_maps([self._db_map, db_map_2])
                self._db_mngr.register_listener(change_listener, db_map_2)
                index = self._model.index(1, Column.DB_MAP)
                self.assertTrue(self._model.setData(index, "2nd database"))
                index = self._model.index(1, Column.NAME)
                self.assertTrue(self._model.setData(index, "title"))
                index = self._model.index(1, Column.VALUE)
                with signal_waiter(self._db_mngr.metadata_added) as waiter:
                    self.assertTrue(self._model.setData(index, "My precious."))
                    waiter.wait()
                self._model.add_metadata(change_listener.added_items)
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

    def test_insert_rows_to_empty_model(self):
        self._model.insertRows(0, 1)
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_insert_rows_to_beginning_and_middle_and_end(self):
        self._model.add_metadata(
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
        self._model.add_metadata(db_map_data)
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
        change_listener = _MetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.metadata_added) as waiter:
            self._db_mngr.add_metadata(db_map_data)
            waiter.wait()
        self._model.add_metadata(change_listener.added_items)
        with signal_waiter(self._db_mngr.metadata_removed) as waiter:
            self.assertTrue(self._model.removeRows(0, 1))
            waiter.wait()
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(
            change_listener.removed_items,
            {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1, "commit_id": None}]},
        )
        self._assert_empty_last_row()

    def test_add_metadata_using_batch_set_data(self):
        self.assertTrue(self._model.insertRows(0, 2))
        self.assertEqual(self._model.rowCount(), 3)
        indexes = [self._model.index(row, column) for row, column in itertools.product(range(2), range(2))]
        data = ["title", "My precious.", "source", "The Internet"]
        change_listener = _MetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.metadata_added) as waiter:
            self._model.batch_set_data(indexes, data)
            waiter.wait()
        self.assertEqual(
            change_listener.added_items,
            {
                self._db_map: [
                    {"name": "title", "value": "My precious.", "id": 1, "commit_id": None},
                    {"name": "source", "value": "The Internet", "id": 2, "commit_id": None},
                ]
            },
        )
        expected_rows = [["title", "My precious.", "database"], ["source", "The Internet", "database"]]
        for row, expected in enumerate(expected_rows):
            self.assertEqual(self._model.index(row, Column.NAME).data(), expected[Column.NAME])
            self.assertEqual(self._model.index(row, Column.VALUE).data(), expected[Column.VALUE])
            self.assertEqual(self._model.index(row, Column.DB_MAP).data(), expected[Column.DB_MAP])
        self._assert_empty_last_row()

    def test_update_metadata_using_batch_set_data(self):
        db_map_data = {self._db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        change_listener = _MetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.metadata_added) as waiter:
            self._db_mngr.add_metadata(db_map_data)
            waiter.wait()
        self._model.add_metadata(change_listener.added_items)
        indexes = [self._model.index(0, Column.NAME), self._model.index(0, Column.VALUE)]
        data = ["title", "My precious."]
        with signal_waiter(self._db_mngr.metadata_updated) as waiter:
            self._model.batch_set_data(indexes, data)
            waiter.wait()
        self.assertEqual(
            change_listener.updated_items,
            {self._db_map: [{"name": "title", "value": "My precious.", "id": 1, "commit_id": None}]},
        )
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

    def _assert_empty_last_row(self):
        row = self._model.rowCount() - 1
        self.assertEqual(self._model.index(row, Column.NAME).data(), "")
        self.assertEqual(self._model.index(row, Column.VALUE).data(), "")
        self.assertEqual(self._model.index(row, Column.DB_MAP).data(), "database")


class _MetadataChangeListener:
    added_items = None
    updated_items = None
    removed_items = None

    def receive_metadata_added(self, db_map_data):
        self.added_items = db_map_data

    def receive_metadata_updated(self, db_map_data):
        self.updated_items = db_map_data

    def receive_metadata_removed(self, db_map_data):
        self.removed_items = db_map_data


if __name__ == '__main__':
    unittest.main()
