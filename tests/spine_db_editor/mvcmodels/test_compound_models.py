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

"""Unit tests for the models in ``compound_models`` module."""
import unittest
from spinedb_api import Array, to_database
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
)
from tests.mock_helpers import fetch_model
from ..helpers import TestBase


class TestCompoundParameterDefinitionModel(TestBase):
    def test_horizontal_header(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "entity_class_name",
            "parameter_name",
            "value_list_name",
            "default_value",
            "description",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter_definition(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"name": "p", "entity_class_id": 1, "id": 1}]})
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["oc", "p", None, "None", None, self.db_codename]
        self.assertEqual(row, expected)

    def test_data_for_single_parameter_definition_in_multidimensional_entity_class(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "rc", "dimension_id_list": [1], "id": 2}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"name": "p", "entity_class_id": 2, "id": 1}]})
        self._db_map.fetch_all()
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["rc", "p", None, "None", None, self.db_codename]
        self.assertEqual(row, expected)

    def test_model_updates_when_entity_class_is_removed(self):
        self._db_map.add_entity_class_item(name="oc1")
        self._db_map.add_parameter_definition_item(entity_class_name="oc1", name="x")
        entity_class_2 = self.assert_success(self._db_map.add_entity_class_item(name="oc2"))
        self._db_map.add_parameter_definition_item(entity_class_name="oc2", name="x")
        self._db_map.add_entity_class_item(name="rc", dimension_name_list=("oc1", "oc2"))
        self._db_map.add_parameter_definition_item(entity_class_name="rc", name="x")
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        model.set_filter_class_ids({self._db_map: {entity_class_2["id"]}})
        self.assertEqual(model.rowCount(), 4)
        self._db_mngr.remove_items({self._db_map: {"entity_class": [entity_class_2["id"]]}})
        self.assertEqual(model.rowCount(), 1)

    def test_index_name_returns_sane_label(self):
        self.assert_success(self._db_map.add_entity_class_item(name="Object"))
        value, value_type = to_database(Array([2.3]))
        self.assert_success(
            self._db_map.add_parameter_definition_item(
                name="x", entity_class_name="Object", default_value=value, default_type=value_type
            )
        )
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        index = model.index(0, 3)
        self.assertEqual(model.index_name(index), "TestCompoundParameterDefinitionModel_db - x - Object")


class TestCompoundParameterValueModel(TestBase):
    def test_horizontal_header(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "entity_class_name",
            "entity_byname",
            "parameter_name",
            "alternative_name",
            "value",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"name": "p", "entity_class_id": 1, "id": 1}]})
        self._db_mngr.add_entities({self._db_map: [{"name": "o", "class_id": 1, "id": 1}]})
        value, value_type = to_database(23.0)
        self._db_mngr.add_parameter_values(
            {
                self._db_map: [
                    {
                        "parameter_definition_id": 1,
                        "value": value,
                        "type": value_type,
                        "entity_id": 1,
                        "entity_class_id": 1,
                        "alternative_id": 1,
                        "id": 1,
                    }
                ]
            }
        )
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["oc", "o", "p", "Base", "23.0", self.db_codename]
        self.assertEqual(row, expected)

    def test_data_for_single_parameter_in_multidimensional_entity(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_entities({self._db_map: [{"name": "o", "class_id": 1, "id": 1}]})
        self._db_mngr.add_entity_classes({self._db_map: [{"name": "rc", "dimension_id_list": [1], "id": 2}]})
        self._db_mngr.add_parameter_definitions({self._db_map: [{"name": "p", "entity_class_id": 2, "id": 1}]})
        self._db_mngr.add_entities({self._db_map: [{"name": "r", "class_id": 2, "element_id_list": [1], "id": 2}]})
        value, value_type = to_database(23.0)
        self._db_mngr.add_parameter_values(
            {
                self._db_map: [
                    {
                        "parameter_definition_id": 1,
                        "value": value,
                        "type": value_type,
                        "entity_id": 2,
                        "entity_class_id": 2,
                        "alternative_id": 1,
                        "id": 1,
                    }
                ]
            }
        )
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["rc", "o", "p", "Base", "23.0", self.db_codename]
        self.assertEqual(row, expected)

    def test_index_name_returns_sane_label(self):
        self.assert_success(self._db_map.add_entity_class_item(name="Object"))
        self.assert_success(self._db_map.add_parameter_definition_item(name="x", entity_class_name="Object"))
        self.assert_success(self._db_map.add_entity_item(name="mysterious cube", entity_class_name="Object"))
        value, value_type = to_database(Array([2.3]))
        self.assert_success(
            self._db_map.add_parameter_value_item(
                entity_class_name="Object",
                entity_byname=("mysterious cube",),
                parameter_definition_name="x",
                alternative_name="Base",
                value=value,
                type=value_type,
            )
        )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        index = model.index(0, 3)
        self.assertEqual(model.index_name(index), "TestCompoundParameterValueModel_db - x - Base - mysterious cube")


if __name__ == "__main__":
    unittest.main()
