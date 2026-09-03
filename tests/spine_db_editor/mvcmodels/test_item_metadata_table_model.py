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

"""Unit tests for the item metadata table model."""

from PySide6.QtCore import Qt
import pytest
from spinedb_api import (
    import_metadata,
    import_object_classes,
    import_object_metadata,
    import_object_parameter_value_metadata,
    import_object_parameter_values,
    import_object_parameters,
    import_objects,
    import_relationship_classes,
    import_relationship_metadata,
    import_relationship_parameter_value_metadata,
    import_relationship_parameter_values,
    import_relationship_parameters,
    import_relationships,
)
from spinetoolbox.spine_db_editor.mvcmodels.item_metadata_table_model import ItemMetadataTableModel
from spinetoolbox.spine_db_editor.mvcmodels.metadata_table_model_base import Column
from tests.mock_helpers import fetch_model


@pytest.fixture
def db_map(db_map):
    with db_map:
        import_object_classes(db_map, ("my_class",))
        import_objects(db_map, (("my_class", "my_object"),))
        import_object_parameters(db_map, (("my_class", "object_parameter"),))
        import_object_parameter_values(db_map, (("my_class", "my_object", "object_parameter", 2.3),))
        import_relationship_classes(db_map, (("entity_class", ("my_class",)),))
        import_relationships(db_map, (("entity_class", ("my_object",)),))
        import_relationship_parameters(db_map, (("entity_class", "relationship_parameter"),))
        import_relationship_parameter_values(db_map, (("entity_class", ("my_object",), "relationship_parameter", 5.0),))
        import_metadata(db_map, [("source", "Fountain of objects")])
        import_object_metadata(db_map, (("my_class", "my_object", "source", "Fountain of objects"),))
        import_metadata(db_map, [("source", "Fountain of relationships")])
        import_relationship_metadata(db_map, (("entity_class", ("my_object",), "source", "Fountain of relationships"),))
        import_metadata(db_map, [("source", "Fountain of object values")])
        import_object_parameter_value_metadata(
            db_map, (("my_class", "my_object", "object_parameter", "source", "Fountain of object values"),)
        )
        import_metadata(db_map, [("source", "Fountain of relationship values")])
        import_relationship_parameter_value_metadata(
            db_map,
            (
                (
                    "entity_class",
                    ("my_object",),
                    "relationship_parameter",
                    "source",
                    "Fountain of relationship values",
                ),
            ),
        )
        db_map.commit_session("Add test data.")
    return db_map


@pytest.fixture()
def model(db_map, db_mngr, parent_object):
    model = ItemMetadataTableModel(db_mngr, [db_map], parent_object)
    fetch_model(model)
    return model


class TestItemMetadataTableModelWithExistingData:
    def test_model_is_initially_empty(self, model, db_map, db_name):
        assert model.rowCount() == 1
        assert model.columnCount() == 3
        assert model.headerData(Column.NAME, Qt.Orientation.Horizontal) == "name"
        assert model.headerData(Column.VALUE, Qt.Orientation.Horizontal) == "value"
        assert model.headerData(Column.DB_MAP, Qt.Orientation.Horizontal) == "database"
        self._assert_empty_last_row(model, db_name)

    def test_get_metadata_for_object(self, model, db_map, db_name):
        model.set_entity_ids({db_map: db_map.get_entity_item(id=1)["id"]})
        assert model.rowCount(), 2
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Fountain of objects"
        assert model.index(0, Column.DB_MAP).data() == db_name
        self._assert_empty_last_row(model, db_name)

    def test_get_metadata_for_relationship(self, model, db_map, db_name):
        model.set_entity_ids({db_map: db_map.get_entity_item(id=2)["id"]})
        assert model.rowCount() == 2
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Fountain of relationships"
        assert model.index(0, Column.DB_MAP).data() == db_name
        self._assert_empty_last_row(model, db_name)

    def test_get_metadata_for_object_parameter_value(self, model, db_map, db_name):
        model.set_parameter_value_ids({db_map: db_map.get_parameter_value_item(id=1)["id"]})
        assert model.rowCount() == 2
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Fountain of object values"
        assert model.index(0, Column.DB_MAP).data() == db_name
        self._assert_empty_last_row(model, db_name)

    def test_get_metadata_for_relationship_parameter_value(self, model, db_map, db_name):
        model.set_parameter_value_ids({db_map: db_map.get_parameter_value_item(id=2)["id"]})
        assert model.rowCount() == 2
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Fountain of relationship values"
        assert model.index(0, Column.DB_MAP).data() == db_name
        self._assert_empty_last_row(model, db_name)

    @staticmethod
    def _assert_empty_last_row(model, db_name):
        row = model.rowCount() - 1
        assert model.index(row, Column.NAME).data() == ""
        assert model.index(row, Column.VALUE).data() == ""
        assert model.index(row, Column.DB_MAP).data() == db_name

    def test_roll_back_after_item_metadata_update(self, model, db_map, db_name, db_mngr):
        model.set_entity_ids({db_map: db_map.get_entity_item(id=1)["id"]})
        index = model.index(0, Column.VALUE)
        assert model.setData(index, "Magician's hat")
        assert model.rowCount() == 2
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Magician's hat"
        self._assert_empty_last_row(model, db_name)
        db_mngr.rollback_session(db_map)
        assert model.rowCount() == 2
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Fountain of objects"
        self._assert_empty_last_row(model, db_name)

    def test_update_relationship_parameter_value_metadata(self, model, db_map, db_name):
        model.set_parameter_value_ids({db_map: db_map.get_parameter_value_item(id=2)["id"]})
        index = model.index(0, Column.VALUE)
        assert model.setData(index, "Magician's hat")
        assert model.rowCount() == 2
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Magician's hat"
        self._assert_empty_last_row(model, db_name)

    def test_update_relationship_metadata(self, model, db_map, db_name):
        model.set_entity_ids({db_map: db_map.get_entity_item(id=2)["id"]})
        index = model.index(0, Column.VALUE)
        assert model.setData(index, "Magician's hat")
        assert model.rowCount() == 2
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Magician's hat"
        self._assert_empty_last_row(model, db_name)

    def test_add_relationship_parameter_value_metadata(self, model, db_map, db_name, db_mngr):
        model.set_parameter_value_ids({db_map: db_map.get_parameter_value_item(id=2)["id"]})
        index = model.index(1, Column.NAME)
        assert model.setData(index, "author")
        index = model.index(1, Column.VALUE)
        assert model.setData(index, "Anonymous")
        db_map_item_metadata = {
            db_map: [
                {"metadata_name": "author", "metadata_value": "Anonymous", "parameter_value_id": 2, "commit_id": None}
            ]
        }
        db_mngr.add_items("parameter_value_metadata", db_map_item_metadata)
        assert model.rowCount() == 3
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Fountain of relationship values"
        assert model.index(1, Column.NAME).data() == "author"
        assert model.index(1, Column.VALUE).data() == "Anonymous"
        self._assert_empty_last_row(model, db_name)

    def test_add_relationship_metadata(self, model, db_map, db_name, db_mngr):
        model.set_entity_ids({db_map: db_map.get_entity_item(id=2)["id"]})
        index = model.index(1, Column.NAME)
        assert model.setData(index, "author")
        index = model.index(1, Column.VALUE)
        assert model.setData(index, "Anonymous")
        db_map_item_metadata = {
            db_map: [
                {
                    "metadata_name": "author",
                    "metadata_value": "Anonymous",
                    "entity_id": 2,
                    "commit_id": None,
                }
            ]
        }
        db_mngr.add_items("entity_metadata", db_map_item_metadata)
        assert model.rowCount() == 3
        assert model.index(0, Column.NAME).data() == "source"
        assert model.index(0, Column.VALUE).data() == "Fountain of relationships"
        assert model.index(1, Column.NAME).data() == "author"
        assert model.index(1, Column.VALUE).data() == "Anonymous"
        self._assert_empty_last_row(model, db_name)

    def test_remove_object_metadata_row(self, model, db_map):
        model.set_entity_ids({db_map: db_map.get_entity_item(id=1)["id"]})
        model.removeRows(0, 1)
        assert model.rowCount() == 1

    def test_remove_object_parameter_value_metadata_row(self, model, db_map):
        model.set_parameter_value_ids({db_map: db_map.get_parameter_value_item(id=1)["id"]})
        model.removeRows(0, 1)
        assert model.rowCount() == 1
