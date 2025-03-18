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

"""Unit tests for the EmptyParameterModel subclasses."""
from unittest import mock
from spinedb_api import (
    import_object_classes,
    import_object_parameters,
    import_objects,
    import_relationship_classes,
    import_relationship_parameters,
    import_relationships,
)
from spinedb_api.parameter_value import join_value_and_type, to_database
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
)
from spinetoolbox.spine_db_editor.mvcmodels.empty_models import EmptyParameterDefinitionModel, EmptyParameterValueModel
from tests.mock_helpers import TestCaseWithQApplication, TestSpineDBManager, fetch_model


class TestEmptyParameterDefinitionModel(EmptyParameterDefinitionModel):
    def __init__(self, db_mngr):
        super().__init__(CompoundParameterDefinitionModel(None, db_mngr))


class TestEmptyParameterValueModel(EmptyParameterValueModel):
    def __init__(self, db_mngr):
        super().__init__(CompoundParameterValueModel(None, db_mngr))


def _empty_indexes(model):
    return [model.index(0, model.header.index(field)) for field in model.header]


class TestEmptyParameterModel(TestCaseWithQApplication):
    def setUp(self):
        """Overridden method. Runs before each test."""
        app_settings = mock.MagicMock()
        logger = mock.MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, "mock_db")
        import_object_classes(self._db_map, ("dog", "fish"))
        import_object_parameters(self._db_map, (("dog", "breed"),))
        import_objects(self._db_map, (("dog", "pluto"), ("fish", "nemo")))
        import_relationship_classes(self._db_map, (("dog__fish", ("dog", "fish")),))
        import_relationship_parameters(self._db_map, (("dog__fish", "relative_speed"),))
        import_relationships(self._db_map, (("dog__fish", ("pluto", "nemo")),))
        self._db_map.commit_session("Add test data")
        self._db_map.fetch_all()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()

    def test_add_object_parameter_values_to_db(self):
        """Test that object parameter values are added to the db when editing the table."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        value, value_type = to_database("bloodhound")
        self.assertTrue(
            model.batch_set_data(
                _empty_indexes(model),
                ["dog", "pluto", "breed", "Base", join_value_and_type(value, value_type), "mock_db"],
            )
        )
        values = self._db_map.get_items("parameter_value")
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["entity_class_name"], "dog")
        self.assertEqual(values[0]["entity_name"], "pluto")
        self.assertEqual(values[0]["parameter_name"], "breed")
        self.assertEqual(values[0]["value"], value)

    def test_do_not_add_invalid_object_parameter_values(self):
        """Test that object parameter values aren't added to the db if data is incomplete."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["fish", "nemo", "water", "Base", "salty", "mock_db"])
        )
        values = [x for x in self._db_map.get_items("parameter_value") if not x["dimension_id_list"]]
        self.assertEqual(values, [])

    def test_infer_class_from_object_and_parameter(self):
        """Test that object classes are inferred from the object and parameter if possible."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        indexes = _empty_indexes(model)
        value, value_type = to_database("bloodhound")
        self.assertTrue(
            model.batch_set_data(
                indexes, ["cat", "pluto", "breed", "Base", join_value_and_type(value, value_type), "mock_db"]
            )
        )
        self.assertEqual(indexes[0].data(), "dog")
        values = [x for x in self._db_map.get_items("parameter_value") if not x["dimension_id_list"]]
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["entity_class_name"], "dog")
        self.assertEqual(values[0]["entity_name"], "pluto")
        self.assertEqual(values[0]["parameter_name"], "breed")
        self.assertEqual(values[0]["value"], value)

    def test_add_relationship_parameter_values_to_db(self):
        """Test that relationship parameter values are added to the db when editing the table."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        value, value_type = to_database(-1)
        self.assertTrue(
            model.batch_set_data(
                _empty_indexes(model),
                [
                    "dog__fish",
                    DB_ITEM_SEPARATOR.join(["pluto", "nemo"]),
                    "relative_speed",
                    "Base",
                    join_value_and_type(value, value_type),
                    "mock_db",
                ],
            )
        )
        values = [x for x in self._db_map.get_items("parameter_value") if x["dimension_id_list"]]
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["entity_class_name"], "dog__fish")
        self.assertEqual(values[0]["element_name_list"], ("pluto", "nemo"))
        self.assertEqual(values[0]["parameter_name"], "relative_speed")
        self.assertEqual(values[0]["value"], value)

    def test_do_not_add_invalid_relationship_parameter_values(self):
        """Test that relationship parameter values aren't added to the db if data is incomplete."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["dog__fish", "pluto,nemo", "combined_mojo", 100, "mock_db"])
        )
        values = [x for x in self._db_map.get_items("parameter_value") if x["dimension_id_list"]]
        self.assertEqual(values, [])

    def test_add_object_parameter_definitions_to_db(self):
        """Test that object parameter definitions are added to the db when editing the table."""
        model = TestEmptyParameterDefinitionModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(model.batch_set_data(_empty_indexes(model), ["dog", "color", (), None, None, None, "mock_db"]))
        definitions = [x for x in self._db_map.get_items("parameter_definition") if not x["dimension_id_list"]]
        self.assertEqual(len(definitions), 2)
        names = {d["name"] for d in definitions}
        self.assertEqual(names, {"breed", "color"})

    def test_add_parameter_definitions_with_types_to_db(self):
        """Test that object parameter definitions are added to the db when editing the table."""
        model = TestEmptyParameterDefinitionModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(
                _empty_indexes(model), ["dog", "color", ("string", "array"), None, None, None, "mock_db"]
            )
        )
        definitions = [x for x in self._db_map.get_items("parameter_definition") if not x["dimension_id_list"]]
        self.assertEqual(len(definitions), 2)
        type_lists = {d["parameter_type_list"] for d in definitions}
        self.assertEqual(type_lists, {(), ("array", "string")})

    def test_do_not_add_invalid_object_parameter_definitions(self):
        """Test that object parameter definitions aren't added to the db if data is incomplete."""
        model = TestEmptyParameterDefinitionModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(model.batch_set_data(_empty_indexes(model), ["cat", "color", None, None, None, "mock_db"]))
        definitions = [x for x in self._db_map.get_items("parameter_definition") if not x["dimension_id_list"]]
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["name"], "breed")

    def test_add_relationship_parameter_definitions_to_db(self):
        """Test that relationship parameter definitions are added to the db when editing the table."""
        model = TestEmptyParameterDefinitionModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["dog__fish", "combined_mojo", (), None, None, None, "mock_db"])
        )
        definitions = [x for x in self._db_map.get_items("parameter_definition") if x["dimension_id_list"]]
        self.assertEqual(len(definitions), 2)
        names = {d["name"] for d in definitions}
        self.assertEqual(names, {"relative_speed", "combined_mojo"})

    def test_do_not_add_invalid_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions aren't added to the db if data is incomplete."""
        model = TestEmptyParameterDefinitionModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(
                _empty_indexes(model), ["fish__dog", "each_others_opinion", None, None, None, "mock_db"]
            )
        )
        definitions = [x for x in self._db_map.get_items("parameter_definition") if x["dimension_id_list"]]
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["name"], "relative_speed")

    def test_add_entity_parameter_values_adds_entity(self):
        """Test that adding parameter a value for a nonexistent entity creates the entity."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        value, value_type = to_database("dog-human")
        with mock.patch("spinetoolbox.spine_db_editor.mvcmodels.empty_models.AddedEntitiesPopup") as add_entities_popup:
            show_method = mock.MagicMock()
            add_entities_popup.return_value = show_method
            self.assertTrue(
                model.batch_set_data(
                    _empty_indexes(model),
                    ["dog", "plato", "breed", "Base", join_value_and_type(value, value_type), "mock_db"],
                )
            )
            show_method.show.assert_called_once()
        parameter_values = self._db_map.get_items("parameter_value")
        entities = self._db_map.get_items("entity")
        self.assertEqual(len(parameter_values), 1)
        self.assertEqual(parameter_values[0]["entity_class_name"], "dog")
        self.assertEqual(parameter_values[0]["entity_name"], "plato")
        self.assertEqual(parameter_values[0]["parameter_name"], "breed")
        self.assertEqual(parameter_values[0]["value"], value)
        self.assertEqual(len(entities), 4)
        self.assertEqual(entities[0]["name"], "pluto")
        self.assertEqual(entities[1]["name"], "nemo")
        self.assertEqual(entities[2]["name"], "pluto__nemo")
        self.assertEqual(entities[3]["name"], "plato")

    def test_clean_to_be_added_entities(self):
        """Tests that the model is not too keen on making entities on the fly."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        self.assertFalse(model._db_map_entities_to_add)
        mock_entities = [mock.MagicMock() for _ in range(9)]
        ent1, ent2, ent3, ent4, ent5, ent6, ent7, ent8, ent9 = mock_entities
        model._db_map_entities_to_add = {
            "db1": {ent1, ent2, ent3},
            "db2": {ent4, ent5, ent6},
            "db3": {ent7, ent8, ent9},
        }
        new_entities = {
            "db1": {ent1, ent2, ent3},
            "db2": {ent4, ent5, ent7},
        }
        model._clean_to_be_added_entities(new_entities)
        expected = {
            "db1": [ent1, ent2, ent3],
            "db2": [ent4, ent5],
        }
        self.assertEqual(expected.keys(), model._db_map_entities_to_add.keys())
        self.assertEqual(set(expected["db1"]), set(model._db_map_entities_to_add["db1"]))
        self.assertEqual(set(expected["db2"]), set(model._db_map_entities_to_add["db2"]))
