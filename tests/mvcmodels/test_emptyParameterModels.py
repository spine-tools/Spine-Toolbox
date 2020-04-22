######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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
from spinetoolbox.mvcmodels.empty_parameter_models import (
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
        self.mock_db_mngr = mock.MagicMock()
        self.mock_db_map = mock.Mock()
        self.mock_db_map.codename = "mock_db"
        self.mock_db_mngr.db_maps = [self.mock_db_map]

        def _get_item(db_map, item_type, id_):
            # print(db_map, item_type, id_)
            return {
                (self.mock_db_map, "object class", 1): {"id": 1, "name": "dog"},
                (self.mock_db_map, "object class", 2): {"id": 2, "name": "fish"},
            }.get((db_map, item_type, id_), {})

        def _get_items_by_field(db_map, item_type, field, value):
            return {
                (self.mock_db_map, "object", "name", "pluto"): [{"id": 1, "class_id": 1, "name": "pluto"}],
                (self.mock_db_map, "object", "name", "nemo"): [{"id": 2, "class_id": 2, "name": "nemo"}],
                (self.mock_db_map, "relationship", "object_name_list", "pluto,nemo"): [
                    {"id": 3, "class_id": 3, "object_id_list": "1,2"}
                ],
                (self.mock_db_map, "object class", "name", "dog"): [{"id": 1, "name": "dog"}],
                (self.mock_db_map, "object class", "name", "fish"): [{"id": 2, "name": "fish"}],
                (self.mock_db_map, "relationship class", "name", "dog__fish"): [
                    {"id": 3, "name": "dog__fish", "object_class_id_list": "1,2"}
                ],
                (self.mock_db_map, "parameter definition", "parameter_name", "breed"): [
                    {"id": 1, "object_class_id": 1, "parameter_name": "breed"}
                ],
                (self.mock_db_map, "parameter definition", "parameter_name", "relative_speed"): [
                    {"id": 2, "relationship_class_id": 3, "parameter_name": "relative_speed"}
                ],
            }.get((db_map, item_type, field, value), [])

        self.mock_db_mngr.get_items_by_field.side_effect = _get_items_by_field
        self.mock_db_mngr.get_item_by_field.side_effect = lambda *args: next(iter(_get_items_by_field(*args)), {})
        self.mock_db_mngr.get_item.side_effect = _get_item

    def test_add_object_parameter_values_to_db(self):
        """Test that object parameter values are added to the db when editing the table."""
        header = ["object_class_name", "object_name", "parameter_name", "value", "database"]
        model = EmptyObjectParameterValueModel(None, header, self.mock_db_mngr)
        model.fetchMore()

        def _add_parameter_values(db_map_data):
            items = db_map_data[self.mock_db_map]
            item = items[0]
            self.assertEqual(len(items), 1)
            self.assertEqual(item["object_class_id"], 1)
            self.assertEqual(item["object_id"], 1)
            self.assertEqual(item["parameter_definition_id"], 1)
            self.assertEqual(item["value"], '"bloodhound"')

        self.mock_db_mngr.add_parameter_values.side_effect = _add_parameter_values
        model.batch_set_data(_empty_indexes(model), ["dog", "pluto", "breed", "bloodhound", "mock_db"])
        self.mock_db_mngr.add_parameter_values.assert_called_once()

    def test_do_not_add_invalid_object_parameter_values(self):
        """Test that object parameter values aren't added to the db if data is incomplete."""
        header = ["object_class_name", "object_name", "parameter_name", "value", "database"]
        model = EmptyObjectParameterValueModel(None, header, self.mock_db_mngr)
        model.fetchMore()
        model.batch_set_data(_empty_indexes(model), ["fish", "nemo", "water", "salty", "mock_db"])
        self.mock_db_mngr.add_parameter_values.assert_not_called()

    def test_infer_class_from_object_and_parameter(self):
        """Test that object classes are inferred from the object and parameter if possible."""
        header = ["object_class_name", "object_name", "parameter_name", "value", "database"]
        model = EmptyObjectParameterValueModel(None, header, self.mock_db_mngr)
        model.fetchMore()
        indexes = _empty_indexes(model)
        model.batch_set_data(indexes, ["cat", "pluto", "breed", "bloodhound", "mock_db"])
        self.assertEqual(indexes[0].data(), "dog")
        self.mock_db_mngr.add_parameter_values.assert_called_once()

    def test_add_relationship_parameter_values_to_db(self):
        """Test that relationship parameter values are added to the db when editing the table."""
        header = ["relationship_class_name", "object_name_list", "parameter_name", "value", "database"]
        model = EmptyRelationshipParameterValueModel(None, header, self.mock_db_mngr)
        model.fetchMore()

        def _add_parameter_values(db_map_data):
            items = db_map_data[self.mock_db_map]
            item = items[0]
            self.assertEqual(len(items), 1)
            self.assertEqual(item["relationship_class_id"], 3)
            self.assertEqual(item["relationship_id"], 3)
            self.assertEqual(item["parameter_definition_id"], 2)
            self.assertEqual(item["value"], '-1')

        self.mock_db_mngr.add_parameter_values.side_effect = _add_parameter_values
        model.batch_set_data(_empty_indexes(model), ["dog__fish", "pluto,nemo", "relative_speed", -1, "mock_db"])
        self.assertEqual(self.mock_db_mngr.add_parameter_values.call_count, 2)

    def test_do_not_add_invalid_relationship_parameter_values(self):
        """Test that relationship parameter values aren't added to the db if data is incomplete."""
        header = ["relationship_class_name", "object_name_list", "parameter_name", "value", "database"]
        model = EmptyRelationshipParameterValueModel(None, header, self.mock_db_mngr)
        model.fetchMore()
        model.batch_set_data(_empty_indexes(model), ["dog__fish", "pluto,nemo", "combined_mojo", 100, "mock_db"])
        self.mock_db_mngr.add_parameter_values.assert_not_called()

    def test_add_object_parameter_definitions_to_db(self):
        """Test that object parameter definitions are added to the db when editing the table."""
        header = ["object_class_name", "parameter_name", "value_list_name", "parameter_tag_list", "database"]
        model = EmptyObjectParameterDefinitionModel(None, header, self.mock_db_mngr)
        model.fetchMore()

        def _add_parameter_definitions(db_map_data):
            items = db_map_data[self.mock_db_map]
            item = items[0]
            self.assertEqual(len(items), 1)
            self.assertEqual(item["object_class_id"], 1)
            self.assertEqual(item["name"], "color")

        self.mock_db_mngr.add_parameter_definitions.side_effect = _add_parameter_definitions
        model.batch_set_data(_empty_indexes(model), ["dog", "color", None, None, "mock_db"])
        self.mock_db_mngr.add_parameter_definitions.assert_called_once()

    def test_do_not_add_invalid_object_parameter_definitions(self):
        """Test that object parameter definitions aren't added to the db if data is incomplete."""
        header = ["object_class_name", "parameter_name", "value_list_name", "parameter_tag_list", "database"]
        model = EmptyObjectParameterDefinitionModel(None, header, self.mock_db_mngr)
        model.fetchMore()
        model.batch_set_data(_empty_indexes(model), ["cat", "color", None, None, "mock_db"])
        self.mock_db_mngr.add_parameter_values.assert_not_called()

    def test_add_relationship_parameter_definitions_to_db(self):
        """Test that relationship parameter definitions are added to the db when editing the table."""
        header = ["relationship_class_name", "parameter_name", "value_list_name", "parameter_tag_list", "database"]
        model = EmptyRelationshipParameterDefinitionModel(None, header, self.mock_db_mngr)
        model.fetchMore()

        def _add_parameter_definitions(db_map_data):
            items = db_map_data[self.mock_db_map]
            item = items[0]
            self.assertEqual(len(items), 1)
            self.assertEqual(item["relationship_class_id"], 3)
            self.assertEqual(item["name"], "combined_mojo")

        self.mock_db_mngr.add_parameter_definitions.side_effect = _add_parameter_definitions
        model.batch_set_data(_empty_indexes(model), ["dog__fish", "combined_mojo", None, None, "mock_db"])
        self.mock_db_mngr.add_parameter_definitions.assert_called_once()

    def test_do_not_add_invalid_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions aren't added to the db if data is incomplete."""
        header = ["relationship_class_name", "parameter_name", "value_list_name", "parameter_tag_list", "database"]
        model = EmptyRelationshipParameterDefinitionModel(None, header, self.mock_db_mngr)
        model.fetchMore()
        model.batch_set_data(_empty_indexes(model), ["fish__dog", "each_others_opinion", None, None, "mock_db"])
        self.mock_db_mngr.add_parameter_values.assert_not_called()
