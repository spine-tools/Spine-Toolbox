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

"""Unit tests for the ``single_models`` module."""
import pytest
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE, HAS_METADATA_ROLE
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundEntityModel,
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
)
from spinetoolbox.spine_db_editor.mvcmodels.single_models import (
    SingleEntityModel,
    SingleParameterDefinitionModel,
    SingleParameterValueModel,
)
from spinetoolbox.spine_db_editor.mvcmodels.utils import (
    ENTITY_FIELD_MAP,
    PARAMETER_DEFINITION_FIELD_MAP,
    PARAMETER_VALUE_FIELD_MAP,
)

ENTITY_PARAMETER_VALUE_HEADER = [
    "entity_class_name",
    "entity_byname",
    "parameter_name",
    "alternative_name",
    "value",
    "database",
]


@pytest.fixture
def compound_parameter_definition_model(parent_object, db_mngr):
    model = CompoundParameterDefinitionModel(parent_object, db_mngr)
    yield model
    model.tear_down()


@pytest.fixture
def gadget(db_map):
    with db_map:
        return db_map.add_entity_class(name="Gadget")


@pytest.fixture
def single_parameter_definition_model(compound_parameter_definition_model, db_map, gadget):
    compound_parameter_definition_model.reset_db_maps([db_map])
    return SingleParameterDefinitionModel(compound_parameter_definition_model, db_map, gadget["id"], False)


class TestSingleParameterDefinitionModel:
    def test_column_count_is_header_length(self, single_parameter_definition_model, db_map):
        assert single_parameter_definition_model.columnCount() == len(PARAMETER_DEFINITION_FIELD_MAP)


@pytest.fixture
def compound_parameter_value_model(parent_object, db_mngr):
    model = CompoundParameterValueModel(parent_object, db_mngr)
    yield model
    model.tear_down()


@pytest.fixture
def single_parameter_value_model(compound_parameter_value_model, db_map, gadget):
    compound_parameter_value_model.reset_db_maps([db_map])
    return SingleParameterValueModel(compound_parameter_value_model, db_map, gadget["id"], False)


class TestSingleParameterValueModel:
    def test_column_count(self, single_parameter_value_model):
        assert single_parameter_value_model.columnCount() == len(PARAMETER_VALUE_FIELD_MAP)

    def test_data_db_map_role(self, single_parameter_value_model, db_map, gadget):
        with db_map:
            my_parameter = db_map.add_parameter_definition(entity_class_id=gadget["id"], name="my_parameter")
            my_object = db_map.add_entity(class_id=gadget["id"], name="my_object")
            parameter_value = db_map.add_parameter_value(
                entity_class_id=gadget["id"],
                entity_id=my_object["id"],
                parameter_definition_id=my_parameter["id"],
                alternative_name="Base",
                parsed_value=2.3,
            )
        model = single_parameter_value_model
        model.add_rows([parameter_value["id"]]),
        for column in range(model.columnCount()):
            assert model.index(0, column).data(DB_MAP_ROLE) is db_map

    def test_data_has_metadata_role(self, single_parameter_value_model, db_map, gadget):
        with db_map:
            my_parameter = db_map.add_parameter_definition(entity_class_id=gadget["id"], name="my_parameter")
            mobile = db_map.add_entity(class_id=gadget["id"], name="mobile")
            tablet = db_map.add_entity(class_id=gadget["id"], name="tablet")
            mobile_value = db_map.add_parameter_value(
                entity_class_id=gadget["id"],
                entity_id=mobile["id"],
                parameter_definition_id=my_parameter["id"],
                alternative_name="Base",
                parsed_value=2.3,
            )
            tablet_value = db_map.add_parameter_value(
                entity_class_id=gadget["id"],
                entity_id=tablet["id"],
                parameter_definition_id=my_parameter["id"],
                alternative_name="Base",
                parsed_value=2.3,
            )
            manufacturer_data = db_map.add_metadata(name="manufacturer", value="Bonk works")
            db_map.add_parameter_value_metadata(
                parameter_value_id=mobile_value["id"], metadata_id=manufacturer_data["id"]
            )
        model = single_parameter_value_model
        model.add_rows([item["id"] for item in [mobile_value, tablet_value]])
        for column in range(model.columnCount()):
            assert model.index(0, column).data(HAS_METADATA_ROLE)
            assert not model.index(1, column).data(HAS_METADATA_ROLE)


@pytest.fixture
def compound_entity_model(parent_object, db_mngr):
    model = CompoundEntityModel(parent_object, db_mngr)
    yield model
    model.tear_down()


@pytest.fixture
def single_entity_model(compound_entity_model, db_map, gadget):
    compound_entity_model.reset_db_maps([db_map])
    return SingleEntityModel(compound_entity_model, db_map, gadget["id"], False)


class TestSingleEntityModel:
    def test_column_count(self, single_entity_model):
        assert single_entity_model.columnCount() == len(ENTITY_FIELD_MAP)

    def test_data_has_metadata_role(self, single_entity_model, db_map, gadget):
        with db_map:
            mobile = db_map.add_entity(class_id=gadget["id"], name="mobile")
            tablet = db_map.add_entity(class_id=gadget["id"], name="tablet")
            manufacturer_data = db_map.add_metadata(name="manufacturer", value="Bonk works")
            db_map.add_entity_metadata(entity_id=mobile["id"], metadata_id=manufacturer_data["id"])
        model = single_entity_model
        model.add_rows([mobile["id"], tablet["id"]])
        for column in range(model.columnCount()):
            assert model.index(0, column).data(HAS_METADATA_ROLE)
            assert not model.index(1, column).data(HAS_METADATA_ROLE)
