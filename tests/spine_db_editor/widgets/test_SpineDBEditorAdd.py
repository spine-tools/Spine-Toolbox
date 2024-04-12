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

"""Unit tests for adding database items in Database editor."""
from unittest import mock
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from spinetoolbox.spine_db_editor.mvcmodels.single_models import SingleParameterDefinitionModel
from .spine_db_editor_test_base import DBEditorTestBase


class TestSpineDBEditorAdd(DBEditorTestBase):
    def test_add_entity_classes_to_object_tree_model(self):
        """Test that object classes are added to the object tree model."""
        root_item = self.spine_db_editor.entity_tree_model.root_item
        self.put_mock_object_classes_in_db_mngr()
        self.fetch_object_tree_model()
        dog_item = next(x for x in root_item.children if x.display_data == "dog")
        fish_item = next(x for x in root_item.children if x.display_data == "fish")
        self.assertEqual(fish_item.item_type, "entity_class")
        self.assertEqual(fish_item.display_data, "fish")
        self.assertEqual(dog_item.item_type, "entity_class")
        self.assertEqual(dog_item.display_data, "dog")
        self.assertEqual(root_item.child_count(), 2)

    def test_add_entities_to_object_tree_model(self):
        """Test that objects are added to the object tree model."""
        self.spine_db_editor.init_models()
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.fetch_object_tree_model()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        dog_item = next(x for x in root_item.children if x.display_data == "dog")
        fish_item = next(x for x in root_item.children if x.display_data == "fish")
        nemo_item = fish_item.child(0)
        pluto_item, scooby_item = dog_item.children
        self.assertEqual(nemo_item.item_type, "entity")
        self.assertEqual(nemo_item.display_data, "nemo")
        self.assertEqual(fish_item.child_count(), 1)
        self.assertEqual(pluto_item.item_type, "entity")
        self.assertEqual(pluto_item.display_data, "pluto")
        self.assertEqual(scooby_item.item_type, "entity")
        self.assertEqual(scooby_item.display_data, "scooby")
        self.assertEqual(dog_item.child_count(), 2)

    def test_add_relationship_classes_to_object_tree_model(self):
        """Test that entity classes are added to the object tree model."""
        self.spine_db_editor.init_models()
        self.fetch_object_tree_model()
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        dog_fish_item = next(x for x in root_item.children if x.display_data == "dog__fish")
        fish_dog_item = next(x for x in root_item.children if x.display_data == "fish__dog")
        self.assertEqual(root_item.child_count(), 4)
        self.assertEqual(dog_fish_item.item_type, "entity_class")
        self.assertEqual(dog_fish_item.display_data, "dog__fish")
        self.assertEqual(fish_dog_item.item_type, "entity_class")
        self.assertEqual(fish_dog_item.display_data, "fish__dog")

    def test_add_relationships_to_object_tree_model(self):
        """Test that relationships are added to the object tree model."""
        self.spine_db_editor.init_models()
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        self.put_mock_relationships_in_db_mngr()
        self.fetch_object_tree_model()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        dog_item = next(x for x in root_item.children if x.display_data == "dog")
        fish_item = next(x for x in root_item.children if x.display_data == "fish")
        nemo_item = fish_item.child(0)
        pluto_item, scooby_item = dog_item.children
        pluto_nemo_item1 = pluto_item.child(0)
        pluto_nemo_item2 = nemo_item.child(0)
        nemo_pluto_item1 = pluto_item.child(1)
        nemo_pluto_item2 = nemo_item.child(1)
        nemo_scooby_item1 = scooby_item.child(0)
        nemo_scooby_item2 = nemo_item.child(2)
        self.assertEqual(nemo_item.child_count(), 3)
        self.assertEqual(pluto_item.child_count(), 2)
        self.assertEqual(scooby_item.child_count(), 1)
        self.assertEqual(pluto_nemo_item1.item_type, "entity")
        self.assertTrue("dog__fish" in pluto_nemo_item1.display_id and "nemo" in pluto_nemo_item1.display_data)
        self.assertEqual(pluto_nemo_item2.item_type, "entity")
        self.assertTrue("dog__fish" in pluto_nemo_item2.display_id and "pluto" in pluto_nemo_item2.display_data)
        self.assertEqual(nemo_pluto_item1.item_type, "entity")
        self.assertTrue("fish__dog" in nemo_pluto_item1.display_id and "nemo" in nemo_pluto_item1.display_data)
        self.assertEqual(nemo_pluto_item2.item_type, "entity")
        self.assertTrue("fish__dog" in nemo_pluto_item2.display_id and "pluto" in nemo_pluto_item2.display_data)
        self.assertEqual(nemo_scooby_item1.item_type, "entity")
        self.assertTrue("fish__dog" in nemo_scooby_item1.display_id and "nemo" in nemo_scooby_item1.display_data)
        self.assertEqual(nemo_scooby_item2.item_type, "entity")
        self.assertTrue("fish__dog" in nemo_scooby_item2.display_id and "scooby" in nemo_scooby_item2.display_data)

    def test_add_object_parameter_definitions_to_model(self):
        """Test that object parameter definitions are added to the model."""
        model = self.spine_db_editor.parameter_definition_model
        if model.canFetchMore(None):
            model.fetchMore(None)
        self.put_mock_object_classes_in_db_mngr()
        with mock.patch.object(SingleParameterDefinitionModel, "__lt__") as lt_mocked:
            lt_mocked.return_value = False
            self.put_mock_object_parameter_definitions_in_db_mngr()
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (model.index(row, h("entity_class_name")).data(), model.index(row, h("parameter_name")).data())
            )
        self.assertTrue(("fish", "water") in parameters)
        self.assertTrue(("dog", "breed") in parameters)

    def test_add_relationship_parameter_definitions_to_model(self):
        """Test that entity parameter definitions are added to the model."""
        model = self.spine_db_editor.parameter_definition_model
        if model.canFetchMore(None):
            model.fetchMore(None)
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        with mock.patch.object(SingleParameterDefinitionModel, "__lt__") as lt_mocked:
            lt_mocked.return_value = False
            self.put_mock_relationship_parameter_definitions_in_db_mngr()
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (model.index(row, h("entity_class_name")).data(), model.index(row, h("parameter_name")).data())
            )
        self.assertTrue(("fish__dog", "relative_speed") in parameters)
        self.assertTrue(("dog__fish", "combined_mojo") in parameters)

    def test_add_object_parameter_values_to_model(self):
        """Test that object parameter values are added to the model."""
        model = self.spine_db_editor.parameter_value_model
        if model.canFetchMore(None):
            model.fetchMore(None)
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_object_parameter_definitions_in_db_mngr()
        with mock.patch.object(SingleParameterDefinitionModel, "__lt__") as lt_mocked:
            lt_mocked.return_value = False
            self.put_mock_object_parameter_values_in_db_mngr()
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (
                    model.index(row, h("entity_byname")).data(),
                    model.index(row, h("parameter_name")).data(),
                    model.index(row, h("value")).data(),
                )
            )
        self.assertTrue(("nemo", "water", "salt") in parameters)
        self.assertTrue(("pluto", "breed", "bloodhound") in parameters)
        self.assertTrue(("scooby", "breed", "great dane") in parameters)

    def test_add_relationship_parameter_values_to_model(self):
        """Test that object parameter values are added to the model."""
        model = self.spine_db_editor.parameter_value_model
        if model.canFetchMore(None):
            model.fetchMore(None)
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        self.put_mock_relationships_in_db_mngr()
        self.put_mock_object_parameter_definitions_in_db_mngr()
        self.put_mock_relationship_parameter_definitions_in_db_mngr()
        with mock.patch.object(SingleParameterDefinitionModel, "__lt__") as lt_mocked:
            lt_mocked.return_value = False
            self.put_mock_relationship_parameter_values_in_db_mngr()
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (
                    tuple((model.index(row, h("entity_byname")).data() or "").split(DB_ITEM_SEPARATOR)),
                    model.index(row, h("parameter_name")).data(),
                    model.index(row, h("value")).data(),
                )
            )
        self.assertTrue((("nemo", "pluto"), "relative_speed", "-1.0") in parameters)
        self.assertTrue((("nemo", "scooby"), "relative_speed", "5.0") in parameters)
        self.assertTrue((("pluto", "nemo"), "combined_mojo", "100.0") in parameters)
