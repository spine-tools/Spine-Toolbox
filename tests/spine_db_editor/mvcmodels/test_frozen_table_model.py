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

from unittest.mock import MagicMock
from PySide6.QtCore import QModelIndex, Qt
import pytest
from spinetoolbox.spine_db_editor.mvcmodels.frozen_table_model import FrozenTableModel
from tests.mock_helpers import assert_table_model_data_pytest, model_data_to_table


@pytest.fixture()
def model(db_mngr, parent_object):
    yield FrozenTableModel(db_mngr, parent_object)


class TestFrozenTableModel:
    def test_initial_dimensions_are_zero(self, model):
        assert model.rowCount() == 0
        assert model.columnCount() == 0

    def test_set_headers_empty_model(self, model):
        model.set_headers(["header 1", "header 2"])
        assert model.rowCount() == 1
        assert model.columnCount() == 2
        assert model.headers == ["header 1", "header 2"]
        assert model.index(0, 0).data() == "header 1"
        assert model.index(0, 1).data() == "header 2"

    def test_set_headers_renames_existing_ones(self, model):
        model.set_headers(["header 1", "header 2"])
        model.set_headers(["new header", "even newer"])
        assert model.rowCount() == 1
        assert model.columnCount() == 2
        assert model.index(0, 0).data() == "new header"
        assert model.index(0, 1).data() == "even newer"

    def test_clear_model(self, model):
        model.set_headers(["header 1", "header 2"])
        model.clear_model()
        assert model.rowCount() == 0
        assert model.columnCount() == 0

    def test_add_values(self, model, db_map, db_name):
        model.set_headers(["alternative", "database"])
        alternative_id = db_map.alternative(name="Base")["id"]
        model.add_values({((db_map, alternative_id), db_map)})
        assert model.rowCount() == 2
        assert model.columnCount() == 2
        assert model.index(0, 0).data() == "alternative"
        assert model.index(0, 1).data() == "database"
        assert model.index(1, 0).data() == "Base"
        assert model.index(1, 1).data() == db_name

    def test_add_values_rejects_none_values(self, model, db_map):
        model.set_headers(["alternative"])
        model.add_values({((db_map, None),)})
        expected = [["alternative"]]
        assert_table_model_data_pytest(model, expected)

    def test_remove_values_before_selected_row(self, model, db_mngr, db_map):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        alternatives = db_map.get_items("alternative")
        ids = {item["id"] for item in alternatives}
        model.set_headers(["alternative", "database"])
        values = {((db_map, id_), db_map) for id_ in ids}
        model.add_values(values)
        assert model.rowCount() == 3
        model.set_selected(2)
        frozen_value = model.get_frozen_value()
        frozen_alternative_id = frozen_value[0][1]
        id_to_remove = next(iter(ids - {frozen_alternative_id}))
        model.remove_values({((db_map, id_to_remove), db_map)})
        assert model.rowCount() == 2
        assert model.get_frozen_value() == ((db_map, frozen_alternative_id), db_map)

    def test_remove_selected_row_when_selected_row_gets_updated_during_removal(self, model, db_mngr, db_map):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        alternatives = db_map.get_items("alternative")
        ids = {item["id"] for item in alternatives}
        model.set_headers(["alternative", "database"])
        values = {((db_map, id_), db_map) for id_ in ids}
        model.add_values(values)
        assert model.rowCount() == 3
        model.set_selected(2)
        # Simulate tabular_view_mixin and frozen table view here.
        row_removal_handler = MagicMock()
        row_removal_handler.side_effect = lambda *args: model.set_selected(1)
        model.rowsAboutToBeRemoved.connect(row_removal_handler)
        frozen_value = model.get_frozen_value()
        id_to_remove = frozen_value[0][1]
        model.remove_values({((db_map, id_to_remove), db_map)})
        row_removal_handler.assert_called_once()
        assert model.rowCount() == 2
        base_alternative_id = db_map.get_alternative_item(name="Base")["id"]
        assert model.get_frozen_value() == ((db_map, base_alternative_id), db_map)

    def test_remove_values_after_selected_row(self, model, db_mngr, db_map):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        alternatives = db_map.get_items("alternative")
        ids = {item["id"] for item in alternatives}
        model.set_headers(["alternative", "database"])
        values = {((db_map, id_), db_map) for id_ in ids}
        model.add_values(values)
        assert model.rowCount() == 3
        model.set_selected(1)
        frozen_value = model.get_frozen_value()
        frozen_alternative_id = frozen_value[0][1]
        id_to_remove = next(iter(ids - {frozen_alternative_id}))
        model.remove_values({((db_map, id_to_remove), db_map)})
        assert model.rowCount() == 2
        assert model.get_frozen_value() == ((db_map, frozen_alternative_id), db_map)

    def test_get_frozen_value(self, model, db_map):
        model.set_headers(["alternative", "database"])
        model.add_values({((db_map, 1), db_map)})
        model.set_selected(1)
        assert model.get_frozen_value() == ((db_map, 1), db_map)

    def test_insert_column_data_to_empty_model(self, model, db_map):
        alternative_id = db_map.alternative(name="Base")["id"]
        model.insert_column_data("alternative", {(db_map, alternative_id)}, 0)
        assert model.columnCount() == 1
        assert model.rowCount() == 2
        assert model.index(0, 0).data() == "alternative"
        assert model.index(1, 0).data() == "Base"

    def test_insert_column_data_to_header_only_model(self, model, db_map):
        model.set_headers(["index 1", "index 2"])
        assert model.columnCount() == 2
        assert model.rowCount() == 1
        model.insert_column_data("alternative", {(db_map, 1)}, 1)
        assert model.columnCount() == 3
        assert model.rowCount() == 1
        assert model.index(0, 0).data() == "index 1"
        assert model.index(0, 1).data() == "alternative"
        assert model.index(0, 2).data() == "index 2"

    def test_insert_column_data_extends_existing_data_in_model(self, model, db_mngr, db_map, db_name):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        model.insert_column_data("database", {db_map}, 0)
        assert model.columnCount() == 1
        assert model.rowCount() == 2
        alternatives = db_map.get_items("alternative")
        ids = {item["id"] for item in alternatives}
        model.insert_column_data("alternative", {(db_map, id_) for id_ in ids}, 1)
        assert model.columnCount() == 2
        assert model.rowCount() == 3
        assert model.headers == ["database", "alternative"]
        expected = [["database", "alternative"], [db_name, "Base"], [db_name, "alternative_1"]]
        assert_table_model_data_pytest(model, expected)

    def test_insert_column_data_extends_inserted_data(self, model, db_mngr, db_map, db_name):
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        alternatives = db_map.get_items("alternative")
        ids = {item["id"] for item in alternatives}
        model.insert_column_data("alternative", {(db_map, id_) for id_ in ids}, 0)
        assert model.columnCount() == 1
        assert model.rowCount() == 3
        model.insert_column_data("database", {db_map}, 0)
        assert model.columnCount() == 2
        assert model.rowCount() == 3
        assert model.headers == ["database", "alternative"]
        expected = [["database", "alternative"], [db_name, "Base"], [db_name, "alternative_1"]]
        assert_table_model_data_pytest(model, expected)

    def test_remove_last_column_clears_model(self, model, db_map):
        model.insert_column_data("database", {db_map}, 0)
        assert model.columnCount() == 1
        assert model.rowCount() == 2
        model.remove_column(0)
        assert model.columnCount() == 0
        assert model.rowCount() == 0

    def test_remove_column_shortens_existing_data(self, model, db_mngr, db_map, db_name):
        model.insert_column_data("database", {db_map}, 0)
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        alternatives = db_map.get_items("alternative")
        ids = {item["id"] for item in alternatives}
        model.insert_column_data("alternative", {(db_map, id_) for id_ in ids}, 0)
        assert model.columnCount() == 2
        assert model.rowCount() == 3
        model.remove_column(0)
        assert model.columnCount() == 1
        assert model.rowCount() == 2
        assert model.headers == ["database"]
        assert model.index(1, 0).data() == db_name

    def test_move_columns(self, model, db_mngr, db_map, db_name):
        model.insert_column_data("database", {db_map}, 0)
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        alternatives = db_map.get_items("alternative")
        ids = {item["id"] for item in alternatives}
        model.insert_column_data("alternative", {(db_map, id_) for id_ in ids}, 1)
        assert model.headers == ["database", "alternative"]
        assert model.columnCount() == 2
        assert model.rowCount() == 3
        assert model.moveColumns(QModelIndex(), 1, 1, QModelIndex(), 0)
        assert model.columnCount() == 2
        assert model.rowCount() == 3
        assert model.headers == ["alternative", "database"]
        expected = [["alternative", "database"], ["Base", db_name], ["alternative_1", db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_table_stays_sorted(self, model, db_mngr, db_map, db_name):
        model.insert_column_data("database", {db_map}, 0)
        db_mngr.add_items("alternative", {db_map: [{"name": "alternative_1"}]})
        db_mngr.add_items("entity_class", {db_map: [{"name": "Gadget"}]})
        db_mngr.add_items(
            "entity",
            {
                db_map: [
                    {"entity_class_name": "Gadget", "name": "fork"},
                    {"entity_class_name": "Gadget", "name": "spoon"},
                ]
            },
        )
        alternatives = db_map.get_items("alternative")
        ids = {item["id"] for item in alternatives}
        model.insert_column_data("alternative", {(db_map, id_) for id_ in ids}, 0)
        objects = db_map.get_items("entity")
        ids = {item["id"] for item in objects}
        model.insert_column_data("Gadget", {(db_map, id_) for id_ in ids}, 0)
        assert model.headers == ["Gadget", "alternative", "database"]
        assert model.columnCount() == 3
        assert model.rowCount() == 5
        assert model.index(0, 0).data() == "Gadget"
        assert model.index(0, 1).data() == "alternative"
        assert model.index(0, 2).data() == "database"
        assert model.index(1, 0).data() == "fork"
        assert model.index(1, 1).data() == "Base"
        assert model.index(1, 2).data() == db_name
        assert model.index(2, 0).data() == "fork"
        assert model.index(2, 1).data() == "alternative_1"
        assert model.index(2, 2).data() == db_name
        assert model.index(3, 0).data() == "spoon"
        assert model.index(3, 1).data() == "Base"
        assert model.index(3, 2).data() == db_name
        assert model.index(4, 0).data() == "spoon"
        assert model.index(4, 1).data() == "alternative_1"
        assert model.index(4, 2).data() == db_name

    def test_tooltips_work_when_no_data_is_available(self, model, db_mngr, db_map, db_name):
        model.insert_column_data("database", {db_map}, 0)
        alternative_id = db_map.alternative(name="Base")["id"]
        db_mngr.remove_items({db_map: {"alternative": [alternative_id]}})
        model.insert_column_data("alternative", {(db_map, None)}, 1)
        assert model.headers == ["database", "alternative"]
        model_data = model_data_to_table(model)
        expected = [["database", "alternative"], [db_name, None]]
        assert model_data == expected
        tool_tip_data = model_data_to_table(model, QModelIndex(), Qt.ItemDataRole.ToolTipRole)
        expected = [["database", "alternative"], [f"<qt>{db_name}</qt>", None]]
        assert tool_tip_data == expected
