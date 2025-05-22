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

"""Unit tests for the ``single_parameter_model`` module."""
import unittest
from unittest.mock import MagicMock
from spinedb_api import to_database
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
)
from spinetoolbox.spine_db_editor.mvcmodels.single_models import (
    SingleParameterDefinitionModel,
    SingleParameterValueModel,
)
from tests.mock_helpers import TestCaseWithQApplication, MockSpineDBManager, fetch_model, q_object

ENTITY_PARAMETER_VALUE_HEADER = [
    "entity_class_name",
    "entity_byname",
    "parameter_name",
    "alternative_name",
    "value",
    "database",
]


class ExampleSingleParameterDefinitionModel(SingleParameterDefinitionModel):
    def __init__(self, db_mngr, db_map, entity_class_id, committed):
        super().__init__(CompoundParameterDefinitionModel(None, db_mngr), db_map, entity_class_id, committed)


class ExampleSingleParameterValueModel(SingleParameterValueModel):
    def __init__(self, db_mngr, db_map, entity_class_id, committed):
        super().__init__(CompoundParameterValueModel(None, db_mngr), db_map, entity_class_id, committed)


class TestEmptySingleParameterDefinitionModel(TestCaseWithQApplication):
    HEADER = [
        "entity_class_name",
        "parameter_name",
        "valid types",
        "list_value_name",
        "default_value",
        "description",
        "database",
    ]

    def test_rowCount_is_zero(self):
        with q_object(ExampleSingleParameterDefinitionModel(None, None, 1, False)) as model:
            self.assertEqual(model.rowCount(), 0)

    def test_columnCount_is_header_length(self):
        with q_object(ExampleSingleParameterDefinitionModel(None, None, 1, False)) as model:
            self.assertEqual(model.columnCount(), len(self.HEADER))


class TestSingleObjectParameterValueModel(TestCaseWithQApplication):
    OBJECT_PARAMETER_VALUE_HEADER = [
        "entity_class_name",
        "object_name",
        "parameter_name",
        "alternative_name",
        "value",
        "database",
    ]

    def setUp(self):
        self._db_mngr = MockSpineDBManager(None, None)
        self._logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite:///", self._logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.db_url, "Test database")

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()
        self._db_mngr.deleteLater()

    def test_data_db_map_role(self):
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "my_class"}]})
        entity_class = self._db_map.get_entity_class_item(name="my_class")
        self._db_mngr.add_items(
            "parameter_definition", {self._db_map: [{"entity_class_id": entity_class["id"], "name": "my_parameter"}]}
        )
        definition = self._db_map.get_parameter_definition_item(entity_class_id=entity_class["id"], name="my_parameter")
        self._db_mngr.add_items("entity", {self._db_map: [{"class_id": entity_class["id"], "name": "my_object"}]})
        entity = self._db_map.get_entity_item(class_id=entity_class["id"], name="my_object")
        alternative = self._db_map.get_alternative_item(name="Base")
        value, type_ = to_database(2.3)
        self._db_mngr.add_items(
            "parameter_value",
            {
                self._db_map: [
                    {
                        "entity_class_id": entity_class["id"],
                        "entity_id": entity["id"],
                        "parameter_definition_id": definition["id"],
                        "value": value,
                        "type": type_,
                        "alternative_id": alternative["id"],
                    }
                ]
            },
        )
        parameter_value = self._db_map.get_parameter_value_item(
            entity_class_id=entity_class["id"],
            entity_id=entity["id"],
            parameter_definition_id=definition["id"],
            alternative_id=alternative["id"],
        )
        with q_object(
            ExampleSingleParameterValueModel(self._db_mngr, self._db_map, parameter_value["id"], True)
        ) as model:
            fetch_model(model)
            model.add_rows([parameter_value["id"]])
            self.assertEqual(model.index(0, 0).data(DB_MAP_ROLE), self._db_map)


if __name__ == "__main__":
    unittest.main()
