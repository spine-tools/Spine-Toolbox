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
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication
from spinedb_api import (
    import_object_classes,
    import_object_parameters,
    import_objects,
    import_relationship_classes,
    import_relationship_parameters,
    import_relationships,
)
from spinetoolbox.spine_db_editor.mvcmodels.empty_models import EmptyParameterValueModel, EmptyParameterDefinitionModel
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundParameterValueModel,
    CompoundParameterDefinitionModel,
)
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from spinedb_api.parameter_value import join_value_and_type
from tests.mock_helpers import TestSpineDBManager, fetch_model


class TestEmptyParameterDefinitionModel(EmptyParameterDefinitionModel):
    def __init__(self, db_mngr):
        super().__init__(CompoundParameterDefinitionModel(None, db_mngr))


class TestEmptyParameterValueModel(EmptyParameterValueModel):
    def __init__(self, db_mngr):
        super().__init__(CompoundParameterValueModel(None, db_mngr))


def _empty_indexes(model):
    return [model.index(0, model.header.index(field)) for field in model.header]


class TestEmptyParameterModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Overridden method. Runs before each test."""
        app_settings = mock.MagicMock()
        logger = mock.MagicMock()
        self._db_mngr = TestSpineDBManager(app_settings, None)
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="mock_db", create=True)
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
        self.assertTrue(
            model.batch_set_data(
                _empty_indexes(model),
                ["dog", "pluto", "breed", "Base", join_value_and_type(b'"bloodhound"', None), "mock_db"],
            )
        )
        values = self._db_mngr.get_items(self._db_map, "parameter_value")
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["entity_class_name"], "dog")
        self.assertEqual(values[0]["entity_name"], "pluto")
        self.assertEqual(values[0]["parameter_name"], "breed")
        self.assertEqual(values[0]["value"], b'"bloodhound"')

    def test_do_not_add_invalid_object_parameter_values(self):
        """Test that object parameter values aren't added to the db if data is incomplete."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["fish", "nemo", "water", "Base", "salty", "mock_db"])
        )
        values = [x for x in self._db_mngr.get_items(self._db_map, "parameter_value") if not x["dimension_id_list"]]
        self.assertEqual(values, [])

    def test_infer_class_from_object_and_parameter(self):
        """Test that object classes are inferred from the object and parameter if possible."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        indexes = _empty_indexes(model)
        self.assertTrue(
            model.batch_set_data(
                indexes, ["cat", "pluto", "breed", "Base", join_value_and_type(b'"bloodhound"', None), "mock_db"]
            )
        )
        self.assertEqual(indexes[0].data(), "dog")
        values = [x for x in self._db_mngr.get_items(self._db_map, "parameter_value") if not x["dimension_id_list"]]
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["entity_class_name"], "dog")
        self.assertEqual(values[0]["entity_name"], "pluto")
        self.assertEqual(values[0]["parameter_name"], "breed")
        self.assertEqual(values[0]["value"], b'"bloodhound"')

    def test_add_relationship_parameter_values_to_db(self):
        """Test that relationship parameter values are added to the db when editing the table."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(
                _empty_indexes(model),
                [
                    "dog__fish",
                    DB_ITEM_SEPARATOR.join(["pluto", "nemo"]),
                    "relative_speed",
                    "Base",
                    join_value_and_type(b"-1", None),
                    "mock_db",
                ],
            )
        )
        values = [x for x in self._db_mngr.get_items(self._db_map, "parameter_value") if x["dimension_id_list"]]
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["entity_class_name"], "dog__fish")
        self.assertEqual(values[0]["element_name_list"], ("pluto", "nemo"))
        self.assertEqual(values[0]["parameter_name"], "relative_speed")
        self.assertEqual(values[0]["value"], b"-1")

    def test_do_not_add_invalid_relationship_parameter_values(self):
        """Test that relationship parameter values aren't added to the db if data is incomplete."""
        model = TestEmptyParameterValueModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["dog__fish", "pluto,nemo", "combined_mojo", 100, "mock_db"])
        )
        values = [x for x in self._db_mngr.get_items(self._db_map, "parameter_value") if x["dimension_id_list"]]
        self.assertEqual(values, [])

    def test_add_object_parameter_definitions_to_db(self):
        """Test that object parameter definitions are added to the db when editing the table."""
        model = TestEmptyParameterDefinitionModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(model.batch_set_data(_empty_indexes(model), ["dog", "color", None, None, None, "mock_db"]))
        definitions = [
            x for x in self._db_mngr.get_items(self._db_map, "parameter_definition") if not x["dimension_id_list"]
        ]
        self.assertEqual(len(definitions), 2)
        names = {d["name"] for d in definitions}
        self.assertEqual(names, {"breed", "color"})

    def test_do_not_add_invalid_object_parameter_definitions(self):
        """Test that object parameter definitions aren't added to the db if data is incomplete."""
        model = TestEmptyParameterDefinitionModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(model.batch_set_data(_empty_indexes(model), ["cat", "color", None, None, None, "mock_db"]))
        definitions = [
            x for x in self._db_mngr.get_items(self._db_map, "parameter_definition") if not x["dimension_id_list"]
        ]
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["name"], "breed")

    def test_add_relationship_parameter_definitions_to_db(self):
        """Test that relationship parameter definitions are added to the db when editing the table."""
        model = TestEmptyParameterDefinitionModel(self._db_mngr)
        fetch_model(model)
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["dog__fish", "combined_mojo", None, None, None, "mock_db"])
        )
        definitions = [
            x for x in self._db_mngr.get_items(self._db_map, "parameter_definition") if x["dimension_id_list"]
        ]
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
        definitions = [
            x for x in self._db_mngr.get_items(self._db_map, "parameter_definition") if x["dimension_id_list"]
        ]
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["name"], "relative_speed")
