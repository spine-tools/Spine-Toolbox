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
Unit tests for the TreeViewFormAddMixin class.

:author: M. Marin (KTH)
:date:   6.12.2018
"""
from PySide2.QtCore import Qt


class TestTreeViewFormAddMixin:
    def test_add_object_classes_to_object_tree_model(self):
        """Test that object classes are added to the object tree model.
        """
        root_item = self.tree_view_form.object_tree_model.root_item
        root_item.fetch_more()
        object_classes = [self.fish_class, self.dog_class]
        self.db_mngr.object_classes_added.emit({self.mock_db_map: object_classes})
        fish_item, dog_item = root_item.children
        self.assertEqual(fish_item.item_type, "object class")
        self.assertEqual(fish_item.display_name, "fish")
        self.assertEqual(dog_item.item_type, "object class")
        self.assertEqual(dog_item.display_name, "dog")
        self.assertEqual(root_item.child_count(), 2)

    def test_add_objects_to_object_tree_model(self):
        """Test that objects are added to the object tree model."""
        self.put_mock_object_classes_in_db_mngr()
        self.tree_view_form.init_models()
        for item in self.tree_view_form.object_tree_model.visit_all():
            item.fetch_more()
        objects = [self.nemo_object, self.pluto_object, self.scooby_object]
        self.db_mngr.objects_added.emit({self.mock_db_map: objects})
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item, dog_item = root_item.children
        nemo_item = fish_item.child(0)
        pluto_item, scooby_item = dog_item.children
        self.assertEqual(nemo_item.item_type, "object")
        self.assertEqual(nemo_item.display_name, "nemo")
        self.assertEqual(fish_item.child_count(), 1)
        self.assertEqual(pluto_item.item_type, "object")
        self.assertEqual(pluto_item.display_name, "pluto")
        self.assertEqual(scooby_item.item_type, "object")
        self.assertEqual(scooby_item.display_name, "scooby")
        self.assertEqual(dog_item.child_count(), 2)

    def test_add_relationship_classes_to_object_tree_model(self):
        """Test that relationship classes are added to the object tree model."""
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.tree_view_form.init_models()
        for item in self.tree_view_form.object_tree_model.visit_all():
            item.fetch_more()
        relationship_classes = [self.fish_dog_class, self.dog_fish_class]
        self.db_mngr.relationship_classes_added.emit({self.mock_db_map: relationship_classes})
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item, dog_item = root_item.children
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_fish_dog_item = pluto_item.child(0)
        self.assertEqual(nemo_dog_fish_item.item_type, "relationship class")
        self.assertEqual(nemo_dog_fish_item.display_name, "dog__fish")
        self.assertEqual(nemo_item.child_count(), 2)
        self.assertEqual(pluto_fish_dog_item.item_type, "relationship class")
        self.assertEqual(pluto_fish_dog_item.display_name, "fish__dog")
        self.assertEqual(pluto_item.child_count(), 2)

    def test_add_relationships_to_object_tree_model(self):
        """Test that relationships are added to the object tree model."""
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        self.tree_view_form.init_models()
        for item in self.tree_view_form.object_tree_model.visit_all():
            item.fetch_more()
        relationships = [self.pluto_nemo_rel, self.nemo_pluto_rel, self.nemo_scooby_rel]
        self.db_mngr.relationships_added.emit({self.mock_db_map: relationships})
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item, dog_item = root_item.children
        nemo_item = fish_item.child(0)
        pluto_item, scooby_item = dog_item.children
        nemo_fish_dog_item, nemo_dog_fish_item = nemo_item.children
        pluto_fish_dog_item, pluto_dog_fish_item = pluto_item.children
        scooby_fish_dog_item, scooby_dog_fish_item = scooby_item.children
        pluto_nemo_item1 = pluto_dog_fish_item.child(0)
        pluto_nemo_item2 = nemo_dog_fish_item.child(0)
        nemo_pluto_item1 = pluto_fish_dog_item.child(0)
        nemo_pluto_item2 = nemo_fish_dog_item.child(0)
        nemo_scooby_item1 = scooby_fish_dog_item.child(0)
        nemo_scooby_item2 = nemo_fish_dog_item.child(1)
        self.assertEqual(nemo_dog_fish_item.child_count(), 1)
        self.assertEqual(nemo_fish_dog_item.child_count(), 2)
        self.assertEqual(pluto_dog_fish_item.child_count(), 1)
        self.assertEqual(pluto_fish_dog_item.child_count(), 1)
        self.assertEqual(scooby_dog_fish_item.child_count(), 0)
        self.assertEqual(scooby_fish_dog_item.child_count(), 1)
        self.assertEqual(pluto_nemo_item1.item_type, "relationship")
        self.assertEqual(pluto_nemo_item1.display_name, 'nemo')
        self.assertEqual(pluto_nemo_item2.item_type, "relationship")
        self.assertEqual(pluto_nemo_item2.display_name, 'pluto')
        self.assertEqual(nemo_pluto_item1.item_type, "relationship")
        self.assertEqual(nemo_pluto_item1.display_name, 'nemo')
        self.assertEqual(nemo_pluto_item2.item_type, "relationship")
        self.assertEqual(nemo_pluto_item2.display_name, 'pluto')
        self.assertEqual(nemo_scooby_item1.item_type, "relationship")
        self.assertEqual(nemo_scooby_item1.display_name, 'nemo')
        self.assertEqual(nemo_scooby_item2.item_type, "relationship")
        self.assertEqual(nemo_scooby_item2.display_name, 'scooby')

    def test_add_object_parameter_definitions_to_model(self):
        """Test that object parameter definitions are added to the model."""
        self.put_mock_object_parameter_definitions_in_db_mngr()
        self.db_mngr.parameter_definitions_added.emit({self.mock_db_map: [self.water_parameter, self.breed_parameter]})
        model = self.tree_view_form.object_parameter_definition_model
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (model.index(row, h("object_class_name")).data(), model.index(row, h("parameter_name")).data())
            )
        self.assertTrue(("fish", "water") in parameters)
        self.assertTrue(("dog", "breed") in parameters)

    def test_add_relationship_parameter_definitions_to_model(self):
        """Test that relationship parameter definitions are added to the model."""
        self.put_mock_relationship_parameter_definitions_in_db_mngr()
        self.db_mngr.parameter_definitions_added.emit(
            {self.mock_db_map: [self.relative_speed_parameter, self.combined_mojo_parameter]}
        )
        model = self.tree_view_form.relationship_parameter_definition_model
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (model.index(row, h("relationship_class_name")).data(), model.index(row, h("parameter_name")).data())
            )
        self.assertTrue(("fish__dog", "relative_speed") in parameters)
        self.assertTrue(("dog__fish", "combined_mojo") in parameters)

    def test_add_object_parameter_values_to_model(self):
        """Test that object parameter values are added to the model."""
        self.put_mock_object_parameter_values_in_db_mngr()
        self.db_mngr.parameter_values_added.emit(
            {self.mock_db_map: [self.nemo_water, self.pluto_breed, self.scooby_breed]}
        )
        model = self.tree_view_form.object_parameter_value_model
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (
                    model.index(row, h("object_name")).data(),
                    model.index(row, h("parameter_name")).data(),
                    model.index(row, h("value")).data(),
                )
            )
        self.assertTrue(("nemo", "water", "salt") in parameters)
        self.assertTrue(("pluto", "breed", "bloodhound") in parameters)
        self.assertTrue(("scooby", "breed", "great dane") in parameters)

    def test_add_relationship_parameter_values_to_model(self):
        """Test that object parameter values are added to the model."""
        self.put_mock_relationship_parameter_values_in_db_mngr()
        self.db_mngr.parameter_values_added.emit(
            {
                self.mock_db_map: [
                    self.nemo_pluto_relative_speed,
                    self.nemo_scooby_relative_speed,
                    self.pluto_nemo_combined_mojo,
                ]
            }
        )
        model = self.tree_view_form.relationship_parameter_value_model
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (
                    model.index(row, h("object_name_list")).data(Qt.EditRole),
                    model.index(row, h("parameter_name")).data(),
                    model.index(row, h("value")).data(),
                )
            )
        self.assertTrue(("nemo,pluto", "relative_speed", -1) in parameters)
        self.assertTrue(("nemo,scooby", "relative_speed", 5) in parameters)
        self.assertTrue(("pluto,nemo", "combined_mojo", 100) in parameters)
