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
from unittest import mock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
import pytest
from spinetoolbox.spine_db_editor.mvcmodels.metadata_table_model import MetadataTableModel
from spinetoolbox.spine_db_editor.mvcmodels.metadata_table_model_base import Column
from tests.mock_helpers import assert_table_model_data_pytest, fetch_model


@pytest.fixture()
def model(db_map, db_mngr, parent_object):
    model = MetadataTableModel(db_mngr, [db_map], parent_object)
    fetch_model(model)
    return model


class TestMetadataTableModel:
    def test_empty_model(self, model, db_map, db_name):
        assert model.rowCount() == 1
        assert model.columnCount() == 3
        assert model.headerData(Column.NAME, Qt.Orientation.Horizontal) == "name"
        assert model.headerData(Column.VALUE, Qt.Orientation.Horizontal) == "value"
        assert model.headerData(Column.DB_MAP, Qt.Orientation.Horizontal) == "database"
        self._assert_empty_last_row(model, db_name)

    def test_add_metadata_from_database_to_empty_model(self, model, db_map, db_name, db_mngr):
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        db_mngr.add_items("metadata", db_map_data)
        expected = [["author", "Anonymous", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_updating_metadata_in_database_updates_existing_row(self, model, db_map, db_name, db_mngr):
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous"}]}
        db_mngr.add_items("metadata", db_map_data)
        index = model.index(0, Column.VALUE)
        assert model.setData(index, "Prof. T. Est")
        expected = [["author", "Prof. T. Est", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_remove_metadata_removes_the_row(self, model, db_map, db_name, db_mngr):
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        db_map_typed_ids = {db_map: {"metadata": {1}}}
        db_mngr.add_items("metadata", db_map_data)
        assert model.rowCount() == 2
        db_mngr.remove_items(db_map_typed_ids)
        assert model.rowCount() == 1
        self._assert_empty_last_row(model, db_name)

    def test_filling_last_row_adds_data_to_database_and_empties_last_row(self, model, db_map, db_name):
        index = model.index(0, Column.NAME)
        model.setData(index, "author")
        index = model.index(0, Column.VALUE)
        assert model.setData(index, "Anonymous")
        assert model.rowCount() == 2
        self._assert_empty_last_row(model, db_name)

    def test_adding_data_to_another_database(self, model, db_map, db_name, db_mngr, tmp_path):
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        db_mngr.add_items("metadata", db_map_data)
        logger = mock.MagicMock()
        database_path = Path(tmp_path, "db.sqlite")
        url = "sqlite:///" + str(database_path)
        try:
            db_map_2 = db_mngr.get_db_map(url, logger, create=True)
            db_mngr.name_registry.register(url, "2nd database")
            model.set_db_maps([db_map, db_map_2])
            fetch_model(model)
            index = model.index(1, Column.DB_MAP)
            assert model.setData(index, "2nd database")
            index = model.index(1, Column.NAME)
            assert model.setData(index, "title")
            index = model.index(1, Column.VALUE)
            assert model.setData(index, "My precious.")
            while model.rowCount() != 3:
                QApplication.processEvents()
        finally:
            db_mngr.close_session(url)
        expected = [
            ["author", "Anonymous", db_name],
            ["title", "My precious.", "2nd database"],
            ["", "", "2nd database"],
        ]
        assert_table_model_data_pytest(model, expected)

    def test_add_and_update_via_adding_entity_metadata(self, model, db_map, db_name, db_mngr):
        db_map_data = {db_map: [{"name": "object class", "id": 1}]}
        db_mngr.add_items("entity_class", db_map_data)
        db_map_data = {db_map: [{"class_id": 1, "name": "object"}]}
        db_mngr.add_items("entity", db_map_data)
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous"}]}
        db_mngr.add_items("metadata", db_map_data)
        expected = [["author", "Anonymous", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(model, expected)
        db_map_data = {
            db_map: [
                {"entity_name": "object", "metadata_name": "author", "metadata_value": "Anonymous"},
                {"entity_name": "object", "metadata_name": "source", "metadata_value": "The Internet"},
            ]
        }
        db_mngr.add_ext_item_metadata("entity_metadata", db_map_data)
        expected = [["author", "Anonymous", db_name], ["source", "The Internet", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_insert_rows_to_empty_model(self, model, db_map, db_name):
        model.insertRows(0, 1)
        expected = [
            ["", "", db_name],
            ["", "", db_name],
        ]
        assert_table_model_data_pytest(model, expected)

    def test_insert_rows_to_beginning_and_middle_and_end(self, model, db_map, db_name, db_mngr):
        db_mngr.add_items(
            "metadata",
            {
                db_map: [
                    {"name": "name_1", "value": "value_1", "id": 1},
                    {"name": "name_2", "value": "value_2", "id": 2},
                ]
            },
        )
        model.insertRows(0, 1)
        model.insertRows(2, 1)
        model.insertRows(4, 1)
        expected_rows = [
            ["", "", db_name],
            ["name_1", "value_1", db_name],
            ["", "", db_name],
            ["name_2", "value_2", db_name],
            ["", "", db_name],
            ["", "", db_name],
        ]
        assert_table_model_data_pytest(model, expected_rows)

    def test_insert_rows_after_adder_row_extends_normal_rows_instead(self, model, db_map, db_name, db_mngr):
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        db_mngr.add_items("metadata", db_map_data)
        assert model.rowCount() == 2
        model.insertRows(2, 1)
        assert model.rowCount() == 3
        expected = [["author", "Anonymous", db_name], ["", "", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_remove_rows_not_yet_in_database(self, model, db_map, db_name):
        model.insertRows(0, 1)
        assert model.rowCount() == 2
        assert model.removeRows(0, 1)
        assert model.rowCount() == 1
        self._assert_empty_last_row(model, db_name)

    def test_remove_rows_also_from_database(self, model, db_map, db_name, db_mngr):
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        db_mngr.add_items("metadata", db_map_data)
        assert model.removeRows(0, 1)
        assert model.rowCount() == 1
        self._assert_empty_last_row(model, db_name)

    def test_add_metadata_using_batch_set_data(self, model, db_map, db_name):
        assert model.insertRows(0, 2)
        assert model.rowCount() == 3
        indexes = [model.index(row, column) for row, column in itertools.product(range(2), range(2))]
        data = ["title", "My precious.", "source", "The Internet"]
        model.batch_set_data(indexes, data)
        expected_rows = [["title", "My precious.", db_name], ["source", "The Internet", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(model, expected_rows)

    def test_update_metadata_using_batch_set_data(self, model, db_map, db_name, db_mngr):
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous", "id": 1}]}
        db_mngr.add_items("metadata", db_map_data)
        indexes = [model.index(0, Column.NAME), model.index(0, Column.VALUE)]
        data = ["title", "My precious."]
        model.batch_set_data(indexes, data)
        expected = [["title", "My precious.", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_batch_set_incomplete_data(self, model, db_map, db_name):
        assert model.insertRows(0, 2)
        assert model.rowCount(), 3
        indexes = [model.index(0, 1), model.index(1, 1)]
        data = ["Anonymous", "The Internet"]
        model.batch_set_data(indexes, data)
        expected_rows = [["", "Anonymous", db_name], ["", "The Internet", db_name], ["", "", db_name]]
        assert_table_model_data_pytest(model, expected_rows)

    def test_roll_back(self, model, db_map, db_name, db_mngr):
        db_map_data = {db_map: [{"name": "author", "value": "Anonymous"}]}
        db_mngr.add_items("metadata", db_map_data)
        db_mngr.commit_session("Add test data.", db_map)
        index = model.index(1, Column.NAME)
        assert model.setData(index, "title")
        index = model.index(1, Column.VALUE)
        assert model.setData(index, "My precious.")
        expected = [
            ["author", "Anonymous", db_name],
            ["title", "My precious.", db_name],
            ["", "", db_name],
        ]
        assert_table_model_data_pytest(model, expected)
        db_mngr.rollback_session(db_map)
        db_mngr.add_items("metadata", db_map_data)
        expected = [
            ["author", "Anonymous", db_name],
            ["", "", db_name],
        ]
        assert_table_model_data_pytest(model, expected)

    @staticmethod
    def _assert_empty_last_row(model, db_name):
        row = model.rowCount() - 1
        assert model.index(row, Column.NAME).data() == ""
        assert model.index(row, Column.VALUE).data() == ""
        assert model.index(row, Column.DB_MAP).data() == db_name
