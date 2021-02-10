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
Unit tests for the EmptyParameterModel subclasses.

:author: M. Marin (KTH)
:date:   10.5.2019
"""
import unittest
from unittest import mock
from PySide2.QtWidgets import QApplication
from spinedb_api import (
    import_object_classes,
    import_object_parameters,
    import_objects,
    import_relationship_classes,
    import_relationship_parameters,
    import_relationships,
)
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.mvcmodels.empty_parameter_models import (
    EmptyObjectParameterValueModel,
    EmptyRelationshipParameterValueModel,
    EmptyObjectParameterDefinitionModel,
    EmptyRelationshipParameterDefinitionModel,
)


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
        with mock.patch(
            "spinetoolbox.spine_db_manager.SpineDBManager.thread", new_callable=mock.PropertyMock
        ) as mock_thread:
            mock_thread.return_value = QApplication.instance().thread()
            self._db_mngr = SpineDBManager(app_settings, None)
            fetcher = self._db_mngr.get_fetcher(mock.MagicMock())
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename="mock_db", create=True)
        import_object_classes(self._db_map, ("dog", "fish"))
        import_object_parameters(self._db_map, (("dog", "breed"),))
        import_objects(self._db_map, (("dog", "pluto"), ("fish", "nemo")))
        import_relationship_classes(self._db_map, (("dog__fish", ("dog", "fish")),))
        import_relationship_parameters(self._db_map, (("dog__fish", "relative_speed"),))
        import_relationships(self._db_map, (("dog_fish", ("pluto", "nemo")),))
        self._db_map.commit_session("Add test data")
        fetcher.fetch([self._db_map])
        self.object_table_header = [
            "object_class_name",
            "object_name",
            "parameter_name",
            "alternative_id",
            "value",
            "database",
        ]
        self.relationship_table_header = [
            "relationship_class_name",
            "object_name_list",
            "parameter_name",
            "alternative_id",
            "value",
            "database",
        ]

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.deleteLater()

    def test_add_object_parameter_values_to_db(self):
        """Test that object parameter values are added to the db when editing the table."""
        header = self.object_table_header
        model = EmptyObjectParameterValueModel(None, header, self._db_mngr)
        model.fetchMore()
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["dog", "pluto", "breed", 1, "bloodhound", "mock_db"])
        )
        values = next(self._db_mngr.get_object_parameter_values(self._db_map), [])
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["object_class_name"], "dog")
        self.assertEqual(values[0]["object_name"], "pluto")
        self.assertEqual(values[0]["parameter_name"], "breed")
        self.assertEqual(values[0]["value"], "bloodhound")

    def test_do_not_add_invalid_object_parameter_values(self):
        """Test that object parameter values aren't added to the db if data is incomplete."""
        header = self.object_table_header
        model = EmptyObjectParameterValueModel(None, header, self._db_mngr)
        model.fetchMore()
        self.assertTrue(model.batch_set_data(_empty_indexes(model), ["fish", "nemo", "water", "salty", "mock_db"]))
        values = next(self._db_mngr.get_object_parameter_values(self._db_map), [])
        self.assertEqual(values, [])

    def test_infer_class_from_object_and_parameter(self):
        """Test that object classes are inferred from the object and parameter if possible."""
        header = self.object_table_header
        model = EmptyObjectParameterValueModel(None, header, self._db_mngr)
        model.fetchMore()
        indexes = _empty_indexes(model)
        self.assertTrue(model.batch_set_data(indexes, ["cat", "pluto", "breed", 1, "bloodhound", "mock_db"]))
        self.assertEqual(indexes[0].data(), "dog")
        values = next(self._db_mngr.get_object_parameter_values(self._db_map), [])
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["object_class_name"], "dog")
        self.assertEqual(values[0]["object_name"], "pluto")
        self.assertEqual(values[0]["parameter_name"], "breed")
        self.assertEqual(values[0]["value"], "bloodhound")

    def test_add_relationship_parameter_values_to_db(self):
        """Test that relationship parameter values are added to the db when editing the table."""
        header = self.relationship_table_header
        model = EmptyRelationshipParameterValueModel(None, header, self._db_mngr)
        model.fetchMore()
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["dog__fish", "pluto,nemo", "relative_speed", 1, -1, "mock_db"])
        )
        values = next(self._db_mngr.get_relationship_parameter_values(self._db_map), [])
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["relationship_class_name"], "dog__fish")
        self.assertEqual(values[0]["object_name_list"], "pluto,nemo")
        self.assertEqual(values[0]["parameter_name"], "relative_speed")
        self.assertEqual(values[0]["value"], "-1")

    def test_do_not_add_invalid_relationship_parameter_values(self):
        """Test that relationship parameter values aren't added to the db if data is incomplete."""
        header = self.relationship_table_header
        model = EmptyRelationshipParameterValueModel(None, header, self._db_mngr)
        model.fetchMore()
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["dog__fish", "pluto,nemo", "combined_mojo", 100, "mock_db"])
        )
        values = next(self._db_mngr.get_relationship_parameter_values(self._db_map), [])
        self.assertEqual(values, [])

    def test_add_object_parameter_definitions_to_db(self):
        """Test that object parameter definitions are added to the db when editing the table."""
        header = ["object_class_name", "parameter_name", "value_list_name", "parameter_tag_list", "database"]
        model = EmptyObjectParameterDefinitionModel(None, header, self._db_mngr)
        model.fetchMore()
        self.assertTrue(model.batch_set_data(_empty_indexes(model), ["dog", "color", None, None, "mock_db"]))
        definitions = next(self._db_mngr.get_object_parameter_definitions(self._db_map), [])
        self.assertEqual(len(definitions), 2)
        names = {d["parameter_name"] for d in definitions}
        self.assertEqual(names, {"breed", "color"})

    def test_do_not_add_invalid_object_parameter_definitions(self):
        """Test that object parameter definitions aren't added to the db if data is incomplete."""
        header = self.object_table_header
        model = EmptyObjectParameterDefinitionModel(None, header, self._db_mngr)
        model.fetchMore()
        self.assertTrue(model.batch_set_data(_empty_indexes(model), ["cat", "color", None, None, "mock_db"]))
        definitions = next(self._db_mngr.get_object_parameter_definitions(self._db_map), [])
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["parameter_name"], "breed")

    def test_add_relationship_parameter_definitions_to_db(self):
        """Test that relationship parameter definitions are added to the db when editing the table."""
        header = ["relationship_class_name", "parameter_name", "value_list_name", "parameter_tag_list", "database"]
        model = EmptyRelationshipParameterDefinitionModel(None, header, self._db_mngr)
        model.fetchMore()
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["dog__fish", "combined_mojo", None, None, "mock_db"])
        )
        definitions = next(self._db_mngr.get_relationship_parameter_definitions(self._db_map), [])
        self.assertEqual(len(definitions), 2)
        names = {d["parameter_name"] for d in definitions}
        self.assertEqual(names, {"relative_speed", "combined_mojo"})

    def test_do_not_add_invalid_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions aren't added to the db if data is incomplete."""
        header = self.relationship_table_header
        model = EmptyRelationshipParameterDefinitionModel(None, header, self._db_mngr)
        model.fetchMore()
        self.assertTrue(
            model.batch_set_data(_empty_indexes(model), ["fish__dog", "each_others_opinion", None, None, "mock_db"])
        )
        definitions = next(self._db_mngr.get_relationship_parameter_definitions(self._db_map), [])
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["parameter_name"], "relative_speed")
