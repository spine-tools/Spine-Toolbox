######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for TreeViewForm and GraphViewForm classes.

:author: M. Marin (KTH)
:date:   6.12.2018
"""

import unittest
import os
import logging
import sys
from unittest import mock
from PySide2.QtWidgets import QApplication, QStyleOptionViewItem
from PySide2.QtCore import Qt, QItemSelectionModel, QItemSelection
from widgets.data_store_widgets import TreeViewForm
from collections import namedtuple
from widgets.custom_editors import CustomComboEditor, CustomLineEditor, ObjectNameListEditor


class TestTreeViewForm(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        cls.ObjectClass = namedtuple("ObjectClass", ["id", "name", "description", "display_order"])
        cls.Object = namedtuple("Object", ["id", "class_id", "name", "description"])
        cls.RelationshipClass = namedtuple(
            "RelationshipClass", ["id", "name", "object_class_id_list", "object_class_name_list"])
        cls.Relationship = namedtuple(
            "Relationship", ["id", "class_id", "name", "object_id_list", "object_name_list"])
        cls.ObjectParameter = namedtuple(
            "ObjectParameter",
            ['id', 'object_class_id', 'object_class_name', 'parameter_name'])
        cls.RelationshipParameter = namedtuple(
            "RelationshipParameter",
            ['id', 'relationship_class_id', 'relationship_class_name',
            'object_class_id_list', 'object_class_name_list', 'parameter_name'])
        cls.ObjectParameterValue = namedtuple(
            "ObjectParameterValue",
            [
                'id', 'object_class_id', 'object_class_name', 'object_id', 'object_name',
                'parameter_id', 'parameter_name', 'index', 'value'
            ])
        cls.RelationshipParameterValue = namedtuple(
            "RelationshipParameterValue",
            [
                'id', 'relationship_class_id', 'relationship_class_name',
                'object_class_id_list', 'object_class_name_list',
                'relationship_id', 'object_id_list', 'object_name_list',
                'parameter_id', 'parameter_name', 'index', 'value'
            ])

    def setUp(self):
        """Overridden method. Runs before each test. Makes instances of TreeViewForm and GraphViewForm classes.
        """
        # Set logging level to Error to silence "Logging level: All messages" print
        with mock.patch("data_store.DataStore") as mock_data_store, \
                mock.patch("spinedatabase_api.DiffDatabaseMapping") as mock_db_map:
            # logging.disable(level=logging.ERROR)  # Disable logging
            mock_db_map.object_parameter_fields.return_value = [
                'id', 'object_class_id', 'object_class_name', 'parameter_name']
            mock_db_map.relationship_parameter_fields.return_value = [
                'id', 'relationship_class_id', 'relationship_class_name',
                'object_class_id_list', 'object_class_name_list', 'parameter_name'
            ]
            mock_db_map.object_parameter_value_fields.return_value = [
                'id', 'object_class_id', 'object_class_name', 'object_id', 'object_name',
                'parameter_id', 'parameter_name', 'index', 'value'
            ]
            mock_db_map.relationship_parameter_value_fields.return_value = [
                'id', 'relationship_class_id', 'relationship_class_name',
                'object_class_id_list', 'object_class_name_list',
                'relationship_id', 'object_id_list', 'object_name_list',
                'parameter_id', 'parameter_name', 'index', 'value'
            ]
            self.tree_view_form = TreeViewForm(mock_data_store, mock_db_map, "mock_db")
            # logging.disable(level=logging.NOTSET)  # Enable logging

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.tree_view_form = None

    def test_add_object_classes(self):
        """Test that object classes are added to the object tree model in the right positions.
        """
        object_classes = [
            self.ObjectClass(1, "fish", "A fish.", 1),
            self.ObjectClass(2, "dog", "A dog.", 3),
            self.ObjectClass(3, "cat", "A cat.", 2)
        ]
        self.tree_view_form.add_object_classes(object_classes)
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_type = fish_item.data(Qt.UserRole)
        fish_name = fish_item.data(Qt.UserRole + 1)['name']
        dog_item = root_item.child(2)
        dog_type = dog_item.data(Qt.UserRole)
        dog_name = dog_item.data(Qt.UserRole + 1)['name']
        cat_item = root_item.child(1)
        cat_type = cat_item.data(Qt.UserRole)
        cat_name = cat_item.data(Qt.UserRole + 1)['name']
        self.assertEqual(fish_type, "object_class")
        self.assertEqual(fish_name, "fish")
        self.assertEqual(dog_type, "object_class")
        self.assertEqual(dog_name, "dog")
        self.assertEqual(cat_type, "object_class")
        self.assertEqual(cat_name, "cat")
        self.assertEqual(root_item.rowCount(), 3)

    def test_add_objects(self):
        """Test that objects are added to the object tree model.
        """
        fish_class, dog_class = self.add_mock_object_classes()
        self.tree_view_form.init_object_tree_model()
        objects = [
            self.Object(1, fish_class.id, "nemo", "The lost one."),
            self.Object(2, fish_class.id, "dory", "Nemo's girl."),
            self.Object(3, dog_class.id, "pluto", "Mickey's."),
            self.Object(4, dog_class.id, "scooby", "Scooby-Dooby-Doo.")
        ]
        # Fetch fish object class id before adding objects, to reach more lines of code
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        # Make object_list return something meaningful
        def side_effect(class_id):
            if class_id == fish_class.id:
                return objects[0:2]
            elif class_id == dog_class.id:
                return objects[2:4]
            else:
                return []
        self.tree_view_form.db_map.object_list.side_effect = side_effect
        # Add objects
        self.tree_view_form.add_objects(objects)
        # Check tree
        dog_item = root_item.child(1)
        nemo_item = fish_item.child(0)
        nemo_type = nemo_item.data(Qt.UserRole)
        nemo_class_id = nemo_item.data(Qt.UserRole + 1)['class_id']
        nemo_id = nemo_item.data(Qt.UserRole + 1)['id']
        nemo_name = nemo_item.data(Qt.UserRole + 1)['name']
        dory_item = fish_item.child(1)
        dory_type = dory_item.data(Qt.UserRole)
        dory_class_id = dory_item.data(Qt.UserRole + 1)['class_id']
        dory_id = dory_item.data(Qt.UserRole + 1)['id']
        dory_name = dory_item.data(Qt.UserRole + 1)['name']
        pluto_item = dog_item.child(0)
        pluto_type = pluto_item.data(Qt.UserRole)
        pluto_class_id = pluto_item.data(Qt.UserRole + 1)['class_id']
        pluto_id = pluto_item.data(Qt.UserRole + 1)['id']
        pluto_name = pluto_item.data(Qt.UserRole + 1)['name']
        scooby_item = dog_item.child(1)
        scooby_type = scooby_item.data(Qt.UserRole)
        scooby_class_id = scooby_item.data(Qt.UserRole + 1)['class_id']
        scooby_id = scooby_item.data(Qt.UserRole + 1)['id']
        scooby_name = scooby_item.data(Qt.UserRole + 1)['name']
        self.assertEqual(nemo_type, "object")
        self.assertEqual(nemo_class_id, fish_class.id)
        self.assertEqual(nemo_id, 1)
        self.assertEqual(nemo_name, "nemo")
        self.assertEqual(dory_type, "object")
        self.assertEqual(dory_class_id, fish_class.id)
        self.assertEqual(dory_id, 2)
        self.assertEqual(dory_name, "dory")
        self.assertEqual(fish_item.rowCount(), 2)
        self.assertEqual(pluto_type, "object")
        self.assertEqual(pluto_class_id, dog_class.id)
        self.assertEqual(pluto_id, 3)
        self.assertEqual(pluto_name, "pluto")
        self.assertEqual(scooby_type, "object")
        self.assertEqual(scooby_class_id, dog_class.id)
        self.assertEqual(scooby_id, 4)
        self.assertEqual(scooby_name, "scooby")
        self.assertEqual(fish_item.rowCount(), 2)

    def test_add_relationship_classes(self):
        """Test that relationship classes are added to the object tree model.
        """
        fish_class, dog_class = self.add_mock_object_classes()
        self.tree_view_form.init_object_tree_model()
        # Add nemo object before adding the relationships to test fetch more
        nemo = dict(
            class_id=fish_class.id,
            name='nemo',
            description='The lost one.'
        )
        nemo_object = self.Object(1, fish_class.id, "nemo", "The lost one.")
        # Make object_list return something meaningful
        def side_effect(class_id):
            if class_id == fish_class.id:
                return [nemo_object]
            else:
                return []
        self.tree_view_form.db_map.object_list.side_effect = side_effect
        # Add nemo object
        self.tree_view_form.add_objects([nemo_object])
        # Add dog__fish and fish__dog relationship classes
        relationship_classes = [
            self.RelationshipClass(1, "dog__fish", str(dog_class.id) + "," + str(fish_class.id), "dog,fish"),
            self.RelationshipClass(2, "fish__dog", str(fish_class.id) + "," + str(dog_class.id), "fish,dog")
        ]
        # Make wide_relationship_class_list return something meaningful
        def side_effect(object_class_id):
            if object_class_id in (fish_class.id, dog_class.id):
                return relationship_classes
            else:
                return []
        self.tree_view_form.db_map.wide_relationship_class_list.side_effect = side_effect
        self.tree_view_form.add_relationship_classes(relationship_classes)
        # Add pluto object after adding the relationships to test fetch more
        pluto_object = self.Object(2, dog_class.id, "pluto", "Mickey's.")
        # Make object_list return something meaningful
        def side_effect(class_id):
            if class_id == fish_class.id:
                return [nemo_object]
            if class_id == dog_class.id:
                return [pluto_object]
            else:
                return []
        self.tree_view_form.db_map.object_list.side_effect = side_effect
        self.tree_view_form.add_objects([pluto_object])
        # Check that nemo can't fetch more (adding the relationship class should have fetched it)
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        can_nemo_fetch_more = self.tree_view_form.object_tree_model.canFetchMore(nemo_index)
        self.assertFalse(can_nemo_fetch_more, "Nemo can fetch more.")
        # Check that pluto *can* fetch more (since it wasn't there when adding the relationship class)
        dog_item = root_item.child(1)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        can_pluto_fetch_more = self.tree_view_form.object_tree_model.canFetchMore(pluto_index)
        self.assertTrue(can_pluto_fetch_more, "Pluto can't fetch more.")
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        # Check relationship class items are good
        # The first one under nemo
        nemo_dog_fish_item = nemo_item.child(0)
        nemo_dog_fish_type = nemo_dog_fish_item.data(Qt.UserRole)
        nemo_dog_fish_name = nemo_dog_fish_item.data(Qt.UserRole + 1)['name']
        nemo_dog_fish_object_class_id_list = nemo_dog_fish_item.data(Qt.UserRole + 1)['object_class_id_list']
        nemo_dog_fish_object_class_name_list = nemo_dog_fish_item.data(Qt.UserRole + 1)['object_class_name_list']
        self.assertEqual(nemo_dog_fish_type, "relationship_class")
        self.assertEqual(nemo_dog_fish_name, "dog__fish")
        split_nemo_dog_fish_object_class_id_list = [int(x) for x in nemo_dog_fish_object_class_id_list.split(",")]
        self.assertEqual(split_nemo_dog_fish_object_class_id_list, [dog_class.id, fish_class.id])
        self.assertEqual(nemo_dog_fish_object_class_name_list, "dog,fish")
        self.assertEqual(nemo_item.rowCount(), 2)
        # The second one under pluto
        pluto_fish_dog_item = pluto_item.child(1)
        pluto_fish_dog_type = pluto_fish_dog_item.data(Qt.UserRole)
        pluto_fish_dog_name = pluto_fish_dog_item.data(Qt.UserRole + 1)['name']
        pluto_fish_dog_object_class_id_list = pluto_fish_dog_item.data(Qt.UserRole + 1)['object_class_id_list']
        pluto_fish_dog_object_class_name_list = pluto_fish_dog_item.data(Qt.UserRole + 1)['object_class_name_list']
        self.assertEqual(pluto_fish_dog_type, "relationship_class")
        self.assertEqual(pluto_fish_dog_name, "fish__dog")
        split_pluto_fish_dog_object_class_id_list = [int(x) for x in pluto_fish_dog_object_class_id_list.split(",")]
        self.assertEqual(split_pluto_fish_dog_object_class_id_list, [fish_class.id, dog_class.id])
        self.assertEqual(pluto_fish_dog_object_class_name_list, "fish,dog")
        self.assertEqual(pluto_item.rowCount(), 2)

    def test_add_relationships(self):
        """Test that relationships are added to the object tree model.
        """
        fish_class, dog_class = self.add_mock_object_classes()
        self.tree_view_form.init_object_tree_model()
        nemo_object, pluto_object, scooby_object = self.add_mock_objects(fish_class.id, dog_class.id)
        fish_dog_class, dog_fish_class = self.add_mock_relationship_classes(fish_class.id, dog_class.id)
        # Add pluto_nemo, nemo_pluto and nemo_scooby relationships
        rel1 = self.Relationship(
            1, dog_fish_class.id, "rel1", str(pluto_object.id) + "," + str(nemo_object.id), "pluto,nemo")
        rel2 = self.Relationship(
            2, fish_dog_class.id, "rel2", str(nemo_object.id) + "," + str(pluto_object.id), "nemo,pluto")
        rel3 = self.Relationship(
            3, fish_dog_class.id, "rel3", str(nemo_object.id) + "," + str(scooby_object.id), "nemo,scooby")
        # Make wide_relationship_list return something meaningful
        def side_effect(class_id, object_id):
            if class_id == dog_fish_class.id:
                if object_id in (nemo_object.id, pluto_object.id):
                    return [rel1]
                else:
                    return []
            elif class_id == fish_dog_class.id:
                if object_id == nemo_object.id:
                    return [rel2, rel3]
                elif object_id == pluto_object.id:
                    return [rel2]
                elif object_id == scooby_object.id:
                    return [rel3]
                else:
                    return []
            else:
                return []
        self.tree_view_form.db_map.wide_relationship_list.side_effect = side_effect
        self.tree_view_form.add_relationships([rel1, rel2, rel3])
        # Get items
        root_item = self.tree_view_form.object_tree_model.root_item
        # Object class items
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        # Object items
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_index)
        # Relationship class items
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_fish_dog_item = pluto_item.child(0)
        pluto_dog_fish_item = pluto_item.child(1)
        scooby_fish_dog_item = scooby_item.child(0)
        scooby_dog_fish_item = scooby_item.child(1)
        nemo_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_dog_fish_item)
        nemo_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        pluto_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_dog_fish_item)
        pluto_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_fish_dog_item)
        scooby_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_dog_fish_item)
        scooby_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_fish_dog_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(nemo_fish_dog_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_fish_dog_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_fish_dog_index)
        # Relationship items
        pluto_nemo_item1 = pluto_dog_fish_item.child(0)
        pluto_nemo_item2 = nemo_dog_fish_item.child(0)
        nemo_pluto_item1 = pluto_fish_dog_item.child(0)
        nemo_pluto_item2 = nemo_fish_dog_item.child(0)
        nemo_scooby_item1 = scooby_fish_dog_item.child(0)
        nemo_scooby_item2 = nemo_fish_dog_item.child(1)
        # Check number of items is good
        self.assertEqual(nemo_dog_fish_item.rowCount(), 1)
        self.assertEqual(nemo_fish_dog_item.rowCount(), 2)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 1)
        self.assertEqual(pluto_fish_dog_item.rowCount(), 1)
        self.assertEqual(scooby_dog_fish_item.rowCount(), 0)
        self.assertEqual(scooby_fish_dog_item.rowCount(), 1)
        # Check relationship items are good
        # pluto_nemo_item1
        pluto_nemo_item1_type = pluto_nemo_item1.data(Qt.UserRole)
        pluto_nemo_item1_name = pluto_nemo_item1.data(Qt.UserRole + 1)['name']
        pluto_nemo_item1_class_id = pluto_nemo_item1.data(Qt.UserRole + 1)['class_id']
        pluto_nemo_item1_object_id_list = pluto_nemo_item1.data(Qt.UserRole + 1)['object_id_list']
        pluto_nemo_item1_object_name_list = pluto_nemo_item1.data(Qt.UserRole + 1)['object_name_list']
        self.assertEqual(pluto_nemo_item1_type, "relationship")
        self.assertEqual(pluto_nemo_item1_name, 'rel1')
        self.assertEqual(pluto_nemo_item1_class_id, dog_fish_class.id)
        split_pluto_nemo_object_id_list = [int(x) for x in pluto_nemo_item1_object_id_list.split(",")]
        self.assertEqual(split_pluto_nemo_object_id_list, [pluto_object.id, nemo_object.id])
        self.assertEqual(pluto_nemo_item1_object_name_list, "pluto,nemo")
        # pluto_nemo_item2
        pluto_nemo_item2_type = pluto_nemo_item2.data(Qt.UserRole)
        pluto_nemo_item2_name = pluto_nemo_item2.data(Qt.UserRole + 1)['name']
        pluto_nemo_item2_class_id = pluto_nemo_item2.data(Qt.UserRole + 1)['class_id']
        pluto_nemo_item2_object_id_list = pluto_nemo_item2.data(Qt.UserRole + 1)['object_id_list']
        pluto_nemo_item2_object_name_list = pluto_nemo_item2.data(Qt.UserRole + 1)['object_name_list']
        self.assertEqual(pluto_nemo_item2_type, "relationship")
        self.assertEqual(pluto_nemo_item2_name, 'rel1')
        self.assertEqual(pluto_nemo_item2_class_id, dog_fish_class.id)
        split_pluto_nemo_object_id_list = [int(x) for x in pluto_nemo_item2_object_id_list.split(",")]
        self.assertEqual(split_pluto_nemo_object_id_list, [pluto_object.id, nemo_object.id])
        self.assertEqual(pluto_nemo_item2_object_name_list, "pluto,nemo")
        # nemo_pluto_item1
        nemo_pluto_item1_type = nemo_pluto_item1.data(Qt.UserRole)
        nemo_pluto_item1_name = nemo_pluto_item1.data(Qt.UserRole + 1)['name']
        nemo_pluto_item1_class_id = nemo_pluto_item1.data(Qt.UserRole + 1)['class_id']
        nemo_pluto_item1_object_id_list = nemo_pluto_item1.data(Qt.UserRole + 1)['object_id_list']
        nemo_pluto_item1_object_name_list = nemo_pluto_item1.data(Qt.UserRole + 1)['object_name_list']
        self.assertEqual(nemo_pluto_item1_type, "relationship")
        self.assertEqual(nemo_pluto_item1_name, 'rel2')
        self.assertEqual(nemo_pluto_item1_class_id, fish_dog_class.id)
        split_pluto_nemo_object_id_list = [int(x) for x in nemo_pluto_item1_object_id_list.split(",")]
        self.assertEqual(split_pluto_nemo_object_id_list, [nemo_object.id, pluto_object.id])
        self.assertEqual(nemo_pluto_item1_object_name_list, "nemo,pluto")
        # nemo_pluto_item2
        nemo_pluto_item2_type = nemo_pluto_item2.data(Qt.UserRole)
        nemo_pluto_item2_name = nemo_pluto_item2.data(Qt.UserRole + 1)['name']
        nemo_pluto_item2_class_id = nemo_pluto_item2.data(Qt.UserRole + 1)['class_id']
        nemo_pluto_item2_object_id_list = nemo_pluto_item2.data(Qt.UserRole + 1)['object_id_list']
        nemo_pluto_item2_object_name_list = nemo_pluto_item2.data(Qt.UserRole + 1)['object_name_list']
        self.assertEqual(nemo_pluto_item2_type, "relationship")
        self.assertEqual(nemo_pluto_item2_name, 'rel2')
        self.assertEqual(nemo_pluto_item2_class_id, fish_dog_class.id)
        split_pluto_nemo_object_id_list = [int(x) for x in nemo_pluto_item2_object_id_list.split(",")]
        self.assertEqual(split_pluto_nemo_object_id_list, [nemo_object.id, pluto_object.id])
        self.assertEqual(nemo_pluto_item2_object_name_list, "nemo,pluto")
        # nemo_scooby_item1
        nemo_scooby_item1_type = nemo_scooby_item1.data(Qt.UserRole)
        nemo_scooby_item1_name = nemo_scooby_item1.data(Qt.UserRole + 1)['name']
        nemo_scooby_item1_class_id = nemo_scooby_item1.data(Qt.UserRole + 1)['class_id']
        nemo_scooby_item1_object_id_list = nemo_scooby_item1.data(Qt.UserRole + 1)['object_id_list']
        nemo_scooby_item1_object_name_list = nemo_scooby_item1.data(Qt.UserRole + 1)['object_name_list']
        self.assertEqual(nemo_scooby_item1_type, "relationship")
        self.assertEqual(nemo_scooby_item1_name, 'rel3')
        self.assertEqual(nemo_scooby_item1_class_id, fish_dog_class.id)
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item1_object_id_list.split(",")]
        self.assertEqual(split_scooby_nemo_object_id_list, [nemo_object.id, scooby_object.id])
        self.assertEqual(nemo_scooby_item1_object_name_list, "nemo,scooby")
        # nemo_scooby_item2
        nemo_scooby_item2_type = nemo_scooby_item2.data(Qt.UserRole)
        nemo_scooby_item2_name = nemo_scooby_item2.data(Qt.UserRole + 1)['name']
        nemo_scooby_item2_class_id = nemo_scooby_item2.data(Qt.UserRole + 1)['class_id']
        nemo_scooby_item2_object_id_list = nemo_scooby_item2.data(Qt.UserRole + 1)['object_id_list']
        nemo_scooby_item2_object_name_list = nemo_scooby_item2.data(Qt.UserRole + 1)['object_name_list']
        self.assertEqual(nemo_scooby_item2_type, "relationship")
        self.assertEqual(nemo_scooby_item2_name, 'rel3')
        self.assertEqual(nemo_scooby_item2_class_id, fish_dog_class.id)
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item2_object_id_list.split(",")]
        self.assertEqual(split_scooby_nemo_object_id_list, [nemo_object.id, scooby_object.id])
        self.assertEqual(nemo_scooby_item2_object_name_list, "nemo,scooby")

    def test_add_object_parameter_definitions(self):
        """Test that object parameter definitions are added to the model.
        """
        self.tree_view_form.db_map.object_parameter_fields.return_value = [
            'id', 'object_class_id', 'object_class_name', 'parameter_name']
        self.tree_view_form.object_parameter_definition_model.reset_model()
        # Add fish and dog object classes
        fish_class, dog_class = self.add_mock_object_classes()
        # Add object parameter definition
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        # Enter object class name
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        self.assertIsNone(obj_cls_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_cls_name_index)
        view.itemDelegate().setEditorData(editor, obj_cls_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor))
        self.assertEqual(editor.count(), 2)
        self.assertEqual(editor.itemText(0), 'fish')
        self.assertEqual(editor.itemText(1), 'dog')
        editor.setCurrentIndex(1)
        view.itemDelegate().setModelData(editor, model, obj_cls_name_index)
        view.itemDelegate().destroyEditor(editor, obj_cls_name_index)
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        obj_cls_id_index = model.index(0, header_index("object_class_id"))
        self.assertEqual(obj_cls_id_index.data(), dog_class.id)
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.text(), "")
        editor.setText("breed")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'breed')

    def test_add_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions are added to the model.
        """
        self.tree_view_form.db_map.relationship_parameter_fields.return_value = [
            'id', 'relationship_class_id', 'relationship_class_name',
            'object_class_id_list', 'object_class_name_list', 'parameter_name'
        ]
        self.tree_view_form.relationship_parameter_definition_model.reset_model()
        fish_class, dog_class = self.add_mock_object_classes()
        nemo_object, pluto_object, scooby_object = self.add_mock_objects(fish_class.id, dog_class.id)
        fish_dog_class, dog_fish_class = self.add_mock_relationship_classes(fish_class.id, dog_class.id)
        # Add relationship parameter definition
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header_index = model.horizontal_header_labels().index
        # Enter relationship class name
        rel_cls_name_index = model.index(0, header_index("relationship_class_name"))
        self.assertIsNone(rel_cls_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), rel_cls_name_index)
        view.itemDelegate().setEditorData(editor, rel_cls_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor))
        self.assertEqual(editor.count(), 2)
        self.assertEqual(editor.itemText(0), 'fish__dog')
        self.assertEqual(editor.itemText(1), 'dog__fish')
        editor.setCurrentIndex(1)
        view.itemDelegate().setModelData(editor, model, rel_cls_name_index)
        view.itemDelegate().destroyEditor(editor, rel_cls_name_index)
        self.assertEqual(rel_cls_name_index.data(), 'dog__fish')
        rel_cls_id_index = model.index(0, header_index("relationship_class_id"))
        self.assertEqual(rel_cls_id_index.data(), dog_fish_class.id)
        obj_cls_name_list_index = model.index(0, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'dog,fish')
        obj_cls_id_list_index = model.index(0, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [dog_class.id, fish_class.id])
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor))
        self.assertEqual(editor.text(), "")
        editor.setText("combined_mojo")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'combined_mojo')

    def test_add_object_parameter_values(self):
        """Test that object parameter values are added to the model.
        """
        self.tree_view_form.db_map.object_parameter_value_fields.return_value = [
            'id', 'object_class_id', 'object_class_name', 'object_id', 'object_name',
            'parameter_id', 'parameter_name', 'index', 'value', 'json'
        ]
        self.tree_view_form.object_parameter_value_model.reset_model()
        fish_class, dog_class = self.add_mock_object_classes()
        nemo_object, pluto_object, scooby_object = self.add_mock_objects(fish_class.id, dog_class.id)
        water_id, breed_id = self.add_mock_object_parameter_definitions(fish_class.id, dog_class.id)
        # Add first object parameter value (for scooby), to test autofilling of object class from *object*
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
        # Enter object name
        obj_name_index = model.index(0, header_index("object_name"))
        self.assertIsNone(obj_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_index)
        view.itemDelegate().setEditorData(editor, obj_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor))
        self.assertEqual(editor.count(), 3)
        self.assertEqual(editor.itemText(0), 'nemo')
        self.assertEqual(editor.itemText(1), 'pluto')
        self.assertEqual(editor.itemText(2), 'scooby')
        editor.setCurrentIndex(2)
        view.itemDelegate().setModelData(editor, model, obj_name_index)
        view.itemDelegate().destroyEditor(editor, obj_name_index)
        self.assertEqual(obj_name_index.data(), 'scooby')
        obj_id_index = model.index(0, header_index("object_id"))
        self.assertEqual(obj_id_index.data(), scooby_object.id)
        # Check objet class
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        obj_cls_id_index = model.index(0, header_index("object_class_id"))
        self.assertEqual(obj_cls_id_index.data(), dog_class.id)
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor))
        self.assertEqual(editor.count(), 1)
        self.assertEqual(editor.itemText(0), 'breed')
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'breed')
        # Add second object parameter value (for pluto), to test autofilling of object class from *parameter*
        # Enter parameter name
        parameter_name_index = model.index(1, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor))
        self.assertEqual(editor.count(), 2)
        self.assertEqual(editor.itemText(1), 'breed')
        editor.setCurrentIndex(1)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'breed')
        # Check objet class
        obj_cls_name_index = model.index(1, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        obj_cls_id_index = model.index(1, header_index("object_class_id"))
        self.assertEqual(obj_cls_id_index.data(), dog_class.id)
        # Enter object name
        obj_name_index = model.index(1, header_index("object_name"))
        self.assertIsNone(obj_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_index)
        view.itemDelegate().setEditorData(editor, obj_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor))
        self.assertEqual(editor.count(), 2)
        self.assertEqual(editor.itemText(0), 'pluto')
        self.assertEqual(editor.itemText(1), 'scooby')
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, obj_name_index)
        view.itemDelegate().destroyEditor(editor, obj_name_index)
        self.assertEqual(obj_name_index.data(), 'pluto')
        obj_id_index = model.index(1, header_index("object_id"))
        self.assertEqual(obj_id_index.data(), pluto_object.id)

    def test_add_relationship_parameter_values(self):
        """Test that relationship parameter values are added to the model.
        """
        self.tree_view_form.db_map.relationship_parameter_value_fields.return_value = [
            'id', 'relationship_class_id', 'relationship_class_name',
            'object_class_id_list', 'object_class_name_list',
            'relationship_id', 'object_id_list', 'object_name_list',
            'parameter_id', 'parameter_name', 'index', 'value', 'json'
        ]
        self.tree_view_form.relationship_parameter_value_model.reset_model()
        fish_class, dog_class = self.add_mock_object_classes()
        nemo_object, pluto_object, scooby_object = self.add_mock_objects(fish_class.id, dog_class.id)
        fish_dog_class, dog_fish_class = self.add_mock_relationship_classes(fish_class.id, dog_class.id)
        self.add_mock_relationship_parameter_definitions(
            fish_class.id, dog_class.id, fish_dog_class.id, dog_fish_class.id)
        self.tree_view_form.init_models()
        # Fetch nemo's fish__dog
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_fish__dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_fish__dog_index)
        # Add nemo_pluto relationship
        # Don't add nemo_scooby since that one we want to be added 'on the fly'
        nemo_pluto_relationship = self.Relationship(
            1, fish_dog_class.id, "fish__dog_nemo__pluto",
            str(nemo_object.id) + "," + str(pluto_object.id), "nemo,pluto")
        def side_effect(class_id=None, object_id=None):
            if class_id == fish_dog_class.id:
                if object_id in (nemo_object.id, pluto_object.id):
                    return [nemo_pluto_relationship]
                else:
                    return []
            elif class_id is None and object_id is None:
                return [nemo_pluto_relationship]
            else:
                return []
        self.tree_view_form.db_map.wide_relationship_list.side_effect = side_effect
        # Add first relationship parameter value (for existing relationship)
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header_index = model.horizontal_header_labels().index
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor))
        self.assertEqual(editor.count(), 2)
        self.assertEqual(editor.itemText(0), 'relative_speed')
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'relative_speed')
        # Check relationship class
        rel_cls_name = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'fish__dog')
        rel_cls_id = model.index(0, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, fish_dog_class.id)
        obj_cls_name_list_index = model.index(0, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'fish,dog')
        obj_cls_id_list_index = model.index(0, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [fish_class.id, dog_class.id])
        # Enter object name list
        obj_name_list_index = model.index(0, header_index("object_name_list"))
        self.assertIsNone(obj_name_list_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_list_index)
        view.itemDelegate().setEditorData(editor, obj_name_list_index)
        self.assertTrue(isinstance(editor, ObjectNameListEditor))
        combos = editor.combos
        self.assertEqual(len(combos), 2)
        self.assertEqual(combos[0].count(), 3)
        self.assertEqual(combos[0].itemText(0), 'fish')
        self.assertEqual(combos[0].itemText(2), 'nemo')
        self.assertEqual(combos[1].count(), 4)
        self.assertEqual(combos[1].itemText(0), 'dog')
        self.assertEqual(combos[1].itemText(2), 'pluto')
        self.assertEqual(combos[1].itemText(3), 'scooby')
        combos[0].setCurrentIndex(2)
        combos[1].setCurrentIndex(2)
        view.itemDelegate().setModelData(editor, model, obj_name_list_index)
        view.itemDelegate().destroyEditor(editor, obj_name_list_index)
        # Check relationship
        relationship_id = model.index(0, header_index("relationship_id")).data()
        self.assertEqual(relationship_id, nemo_pluto_relationship.id)
        obj_id_list_index = model.index(0, header_index("object_id_list"))
        split_obj_id_list = [int(x) for x in obj_id_list_index.data().split(',')]
        self.assertEqual(split_obj_id_list, [nemo_object.id, pluto_object.id])
        # Add second relationship parameter value (relationship on the fly)
        parameter_name_index = model.index(1, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor))
        self.assertEqual(editor.count(), 2)
        self.assertEqual(editor.itemText(0), 'relative_speed')
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'relative_speed')
        # Check relationship class
        rel_cls_name = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'fish__dog')
        rel_cls_id = model.index(1, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, fish_dog_class.id)
        obj_cls_name_list_index = model.index(1, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'fish,dog')
        obj_cls_id_list_index = model.index(1, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [fish_class.id, dog_class.id])
        # Enter object name list
        obj_name_list_index = model.index(1, header_index("object_name_list"))
        self.assertIsNone(obj_name_list_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_list_index)
        view.itemDelegate().setEditorData(editor, obj_name_list_index)
        self.assertTrue(isinstance(editor, ObjectNameListEditor))
        combos = editor.combos
        self.assertEqual(len(combos), 2)
        self.assertEqual(combos[0].count(), 3)
        self.assertEqual(combos[0].itemText(0), 'fish')
        self.assertEqual(combos[0].itemText(2), 'nemo')
        self.assertEqual(combos[1].count(), 4)
        self.assertEqual(combos[1].itemText(0), 'dog')
        self.assertEqual(combos[1].itemText(2), 'pluto')
        self.assertEqual(combos[1].itemText(3), 'scooby')
        combos[0].setCurrentIndex(2)
        combos[1].setCurrentIndex(3)
        view.itemDelegate().setModelData(editor, model, obj_name_list_index)
        view.itemDelegate().destroyEditor(editor, obj_name_list_index)
        # Check relationship
        obj_id_list_index = model.index(1, header_index("object_id_list"))
        split_obj_id_list = [int(x) for x in obj_id_list_index.data().split(',')]
        self.assertEqual(split_obj_id_list, [nemo_object.id, scooby_object.id])

    @unittest.skipIf(sys.platform.startswith("win"), "QApplication.clipboard() tests do not work on Windows")
    def test_paste_add_object_parameter_definitions(self):
        """Test that data is pasted onto the view and object parameter definitions are added to the model.
        """
        fish_class, dog_class = self.add_mock_object_classes()
        self.tree_view_form.init_models()
        # Paste data
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        clipboard_text = "dog\tbreed\nfish\twater\n"
        QApplication.clipboard().setText(clipboard_text)
        obj_cls_name_index = model.index(0, header_index('object_class_name'))
        view.setCurrentIndex(obj_cls_name_index)
        view.paste()
        # Check model
        # Object class name and id
        obj_cls_name0 = model.index(0, header_index("object_class_name")).data()
        obj_cls_name1 = model.index(1, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name0, 'dog')
        self.assertEqual(obj_cls_name1, 'fish')
        obj_cls_id0 = model.index(0, header_index("object_class_id")).data()
        obj_cls_id1 = model.index(1, header_index("object_class_id")).data()
        self.assertEqual(obj_cls_id0, dog_class.id)
        self.assertEqual(obj_cls_id1, fish_class.id)
        # Parameter name
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        parameter_name1 = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, 'breed')
        self.assertEqual(parameter_name1, 'water')

    @unittest.skipIf(sys.platform.startswith("win"), "QApplication.clipboard() tests do not work on Windows")
    def test_paste_add_object_parameter_values(self):
        """Test that data is pasted onto the view and object parameter values are added to the model.
        """
        fish_class, dog_class = self.add_mock_object_classes()
        nemo_object, pluto_object, scooby_object = self.add_mock_objects(fish_class.id, dog_class.id)
        water_parameter, breed_parameter = self.add_mock_object_parameter_definitions(
            fish_class.id, dog_class.id)
        self.tree_view_form.init_models()
        # Paste data
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
        clipboard_text = "nemo\twater\t\tsalt\npluto\tbreed\t\tbloodhound\nscooby\tbreed\t\tgreat dane\n"
        QApplication.clipboard().setText(clipboard_text)
        obj_name_index = model.index(0, header_index('object_name'))
        view.setCurrentIndex(obj_name_index)
        view.paste()
        # Check model
        # Object class name and id
        obj_cls_name = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name, 'fish')
        obj_cls_id = model.index(0, header_index("object_class_id")).data()
        self.assertEqual(obj_cls_id, fish_class.id)
        obj_cls_name = model.index(1, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name, 'dog')
        obj_cls_id = model.index(1, header_index("object_class_id")).data()
        self.assertEqual(obj_cls_id, dog_class.id)
        obj_cls_name = model.index(2, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name, 'dog')
        obj_cls_id = model.index(2, header_index("object_class_id")).data()
        self.assertEqual(obj_cls_id, dog_class.id)
        # Parameter name and id
        parameter_name = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'water')
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, water_parameter.id)
        parameter_name = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'breed')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, breed_parameter.id)
        parameter_name = model.index(2, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'breed')
        parameter_id = model.index(2, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, breed_parameter.id)
        # Object name and id
        obj_name = model.index(0, header_index("object_name")).data()
        self.assertEqual(obj_name, 'nemo')
        obj_id = model.index(0, header_index("object_id")).data()
        self.assertEqual(obj_id, nemo_object.id)
        obj_name = model.index(1, header_index("object_name")).data()
        self.assertEqual(obj_name, 'pluto')
        obj_id = model.index(1, header_index("object_id")).data()
        self.assertEqual(obj_id, pluto_object.id)
        obj_name = model.index(2, header_index("object_name")).data()
        self.assertEqual(obj_name, 'scooby')
        obj_id = model.index(2, header_index("object_id")).data()
        self.assertEqual(obj_id, scooby_object.id)
        # Parameter value and id
        value = model.index(0, header_index("value")).data()
        self.assertEqual(value, 'salt')
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, water_parameter.id)
        value = model.index(1, header_index("value")).data()
        self.assertEqual(value, 'bloodhound')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, breed_parameter.id)
        value = model.index(2, header_index("value")).data()
        self.assertEqual(value, 'great dane')
        parameter_id = model.index(2, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, breed_parameter.id)

    @unittest.skipIf(sys.platform.startswith("win"), "QApplication.clipboard() tests do not work on Windows")
    def test_paste_add_relationship_parameter_definitions(self):
        """Test that data is pasted onto the view and relationship parameter definitions are added to the model.
        """
        fish_class, dog_class = self.add_mock_object_classes()
        nemo_object, pluto_object, scooby_object = self.add_mock_objects(fish_class.id, dog_class.id)
        fish_dog_class, dog_fish_class = self.add_mock_relationship_classes(fish_class.id, dog_class.id)
        self.tree_view_form.init_models()
        # Paste data
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header_index = model.horizontal_header_labels().index
        clipboard_text = "fish__dog\t\trelative_speed\ndog__fish\t\tcombined_mojo\n"
        QApplication.clipboard().setText(clipboard_text)
        rel_class_name_index = model.index(0, header_index('relationship_class_name'))
        view.setCurrentIndex(rel_class_name_index)
        view.paste()
        # Check model
        # Relationship class name and id
        rel_cls_name0 = model.index(0, header_index("relationship_class_name")).data()
        rel_cls_name1 = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name0, 'fish__dog')
        self.assertEqual(rel_cls_name1, 'dog__fish')
        rel_cls_id0 = model.index(0, header_index("relationship_class_id")).data()
        rel_cls_id1 = model.index(1, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id0, fish_dog_class.id)
        self.assertEqual(rel_cls_id1, dog_fish_class.id)
        # Object class name and id list
        obj_cls_name_lst0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst1 = model.index(1, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst0, 'fish,dog')
        self.assertEqual(obj_cls_name_lst1, 'dog,fish')
        obj_cls_id_lst0 = model.index(0, header_index("object_class_id_list")).data()
        obj_cls_id_lst1 = model.index(1, header_index("object_class_id_list")).data()
        self.assertEqual(obj_cls_id_lst0, str(fish_class.id) + "," + str(dog_fish_class.id))
        self.assertEqual(obj_cls_id_lst1, str(dog_fish_class.id) + "," + str(fish_class.id))
        # Parameter name
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        parameter_name1 = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, 'relative_speed')
        self.assertEqual(parameter_name1, 'combined_mojo')

    @unittest.skipIf(sys.platform.startswith("win"), "QApplication.clipboard() tests do not work on Windows")
    def test_paste_add_relationship_parameter_values(self):
        """Test that data is pasted onto the view and relationship parameter values are added to the model.
        """
        fish_class, dog_class = self.add_mock_object_classes()
        nemo_object, pluto_object, scooby_object = self.add_mock_objects(fish_class.id, dog_class.id)
        fish_dog_class, dog_fish_class = self.add_mock_relationship_classes(fish_class.id, dog_class.id)
        pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel = self.add_mock_relationships(
            fish_dog_class.id, dog_fish_class.id, pluto_object.id, nemo_object.id, scooby_object.id)
        relative_speed_parameter, combined_mojo_parameter = self.add_mock_relationship_parameter_definitions(
            fish_class.id, dog_class.id, fish_dog_class.id, dog_fish_class.id)
        self.tree_view_form.init_models()
        # Paste data
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header_index = model.horizontal_header_labels().index
        clipboard_text = "nemo,pluto\trelative_speed\t\t-1\npluto,nemo\tcombined_mojo\t\t100\n"
        QApplication.clipboard().setText(clipboard_text)
        obj_cls_name_lst_index = model.index(0, header_index('object_class_name_list'))
        view.setCurrentIndex(obj_cls_name_lst_index)
        view.paste()
        # Check model
        # Relationship class name and id
        rel_cls_name = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'fish__dog')
        rel_cls_id = model.index(0, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, fish_dog_class.id)
        rel_cls_name = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'dog__fish')
        rel_cls_id = model.index(1, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, dog_fish_class.id)
        # Parameter name and id
        parameter_name = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'relative_speed')
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, relative_speed_parameter.id)
        parameter_name = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'combined_mojo')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, combined_mojo_parameter.id)
        # Object name and id list
        obj_name_lst = model.index(0, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst, 'nemo,pluto')
        obj_id_lst = model.index(0, header_index("object_id_list")).data()
        self.assertEqual(obj_id_lst, str(nemo_object.id) + "," + str(pluto_object.id))
        obj_name_lst = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst, 'pluto,nemo')
        obj_id_lst = model.index(1, header_index("object_id_list")).data()
        self.assertEqual(obj_id_lst, str(pluto_object.id) + "," + str(nemo_object.id))
        # Parameter value and id
        value = model.index(0, header_index("value")).data()
        self.assertEqual(value, '-1')
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, relative_speed_parameter.id)
        value = model.index(1, header_index("value")).data()
        self.assertEqual(value, '100')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, combined_mojo_parameter.id)

    def test_copy_from_parameter_tables(self):
        """Test that data is copied from each parameter table into the clipboard."""
        self.add_mock_dataset()
        # Object parameter definition
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        item_selection = QItemSelection(top_left, bottom_right)
        view.selectionModel().select(item_selection, QItemSelectionModel.Select)
        view.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data[0][0:2], ['fish', 'water'])
        self.assertEqual(data[1][0:2], ['dog', 'breed'])
        # Object parameter value
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        item_selection = QItemSelection(top_left, bottom_right)
        view.selectionModel().select(item_selection, QItemSelectionModel.Select)
        view.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data[0][0:5], ['fish', 'nemo', 'water', '1', 'salt'])
        self.assertEqual(data[1][0:5], ['dog', 'pluto', 'breed', '1', 'bloodhound'])
        self.assertEqual(data[2][0:5], ['dog', 'scooby', 'breed', '1', 'great dane'])
        # Relationship parameter definition
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        item_selection = QItemSelection(top_left, bottom_right)
        view.selectionModel().select(item_selection, QItemSelectionModel.Select)
        view.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data[0][0:3], ['fish__dog', 'fish,dog', 'relative_speed'])
        self.assertEqual(data[1][0:3], ['dog__fish', 'dog,fish', 'combined_mojo'])
        # Relationship parameter value
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        item_selection = QItemSelection(top_left, bottom_right)
        view.selectionModel().select(item_selection, QItemSelectionModel.Select)
        view.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data[0][0:5], ['fish__dog', 'nemo,pluto', 'relative_speed', '1', '-1'])
        self.assertEqual(data[1][0:5], ['fish__dog', 'nemo,scooby', 'relative_speed', '1', '5'])
        self.assertEqual(data[2][0:5], ['dog__fish', 'pluto,nemo', 'combined_mojo', '1', '100'])

    def test_copy_from_object_tree(self):
        """Test that data is copied from object_tree into the clipboard."""
        self.add_mock_dataset()
        # Fetch entire object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        root_index = self.tree_view_form.object_tree_model.indexFromItem(root_item)
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.selectionModel().select(dog_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.selectionModel().select(nemo_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.selectionModel().select(scooby_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data, [['fish'], ['dog'], ['nemo'], ['scooby']])

    def test_set_object_parameter_definition_defaults(self):
        """Test that defaults are set in object parameter definition models according the object tree selection.
        """
        self.tree_view_form.db_map.object_parameter_fields.return_value = [
            'id', 'object_class_id', 'object_class_name', 'parameter_name']
        fish_class, dog_class = self.add_mock_object_classes()
        self.tree_view_form.init_models()
        # Select fish item in object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_tree_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_tree_index, QItemSelectionModel.Select)
        # Check default in object parameter definition
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'fish')
        # Deselected fish and select dog item in object tree
        dog_item = root_item.child(1)
        dog_tree_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(dog_tree_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_tree_index, QItemSelectionModel.Deselect)
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        # Clear object tree selection and select root
        self.tree_view_form.ui.treeView_object.selectionModel().clearSelection()
        root_tree_index = self.tree_view_form.object_tree_model.indexFromItem(root_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(root_tree_index, QItemSelectionModel.Select)
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertIsNone(obj_cls_name_index.data())

    @unittest.skip("TODO")
    def test_set_object_parameter_value_defaults(self):
        """Test that defaults are set in relationship parameter definition models according the object tree selection.
        """
        self.fail()

    @unittest.skip("TODO")
    def test_set_relationship_parameter_definition_defaults(self):
        """Test that defaults are set in relationship parameter definition models according the object tree selection.
        """
        self.fail()

    @unittest.skip("TODO")
    def test_set_relationship_parameter_value_defaults(self):
        """Test that defaults are set in relationship parameter definition models according the object tree selection.
        """
        self.fail()

    def test_update_object_classes(self):
        """Test that object classes are updated on all model/views.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        upd_fish_class = self.ObjectClass(fish_class.id, "octopus", "A fish.", 1)
        upd_dog_class = self.ObjectClass(dog_class.id, "god", "A fish.", 3)
        self.tree_view_form.db_map.object_class_list.return_value = [upd_fish_class, upd_dog_class]
        self.tree_view_form.update_object_classes([upd_fish_class, upd_dog_class])
        # Check object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_type = fish_item.data(Qt.UserRole)
        fish_name = fish_item.data(Qt.UserRole + 1)['name']
        dog_item = root_item.child(1)
        dog_type = dog_item.data(Qt.UserRole)
        dog_name = dog_item.data(Qt.UserRole + 1)['name']
        self.assertEqual(fish_type, "object_class")
        self.assertEqual(fish_name, "octopus")
        self.assertEqual(dog_type, "object_class")
        self.assertEqual(dog_name, "god")
        self.assertEqual(root_item.rowCount(), 2)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        obj_cls_name_1 = model.index(1, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'octopus')
        self.assertEqual(obj_cls_name_1, 'god')
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        obj_cls_name_1 = model.index(1, header_index("object_class_name")).data()
        obj_cls_name_2 = model.index(2, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'octopus')
        self.assertEqual(obj_cls_name_1, 'god')
        self.assertEqual(obj_cls_name_2, 'god')
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'octopus,god')
        self.assertEqual(obj_cls_name_lst_1, 'god,octopus')
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        obj_cls_name_lst_2 = model.index(2, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'octopus,god')
        self.assertEqual(obj_cls_name_lst_1, 'octopus,god')
        self.assertEqual(obj_cls_name_lst_2, 'god,octopus')

    def test_update_objects(self):
        """Test that objects are updated on all model/views.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch object classes
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        # Update objects
        upd_nemo_object = self.Object(nemo_object.id, fish_class.id, "dory", "")
        upd_pluto_object = self.Object(pluto_object.id, dog_class.id, "rascal", "")
        def side_effect(class_id=None):
            if class_id == fish_class.id:
                return [nemo_object]
            elif class_id == dog_class.id:
                return [pluto_object, scooby_object]
            elif class_id is None:
                return [nemo_object, pluto_object, scooby_object]
            else:
                return []
        self.tree_view_form.db_map.object_list.side_effect = side_effect
        self.tree_view_form.update_objects([upd_nemo_object, upd_pluto_object])
        # Check object tree
        nemo_item = fish_item.child(0)
        nemo_type = nemo_item.data(Qt.UserRole)
        nemo_name = nemo_item.data(Qt.UserRole + 1)['name']
        pluto_item = dog_item.child(0)
        pluto_type = pluto_item.data(Qt.UserRole)
        pluto_name = pluto_item.data(Qt.UserRole + 1)['name']
        self.assertEqual(nemo_type, "object")
        self.assertEqual(nemo_name, "dory")
        self.assertEqual(pluto_type, "object")
        self.assertEqual(pluto_name, "rascal")
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_0 = model.index(0, header_index("object_name")).data()
        obj_name_1 = model.index(1, header_index("object_name")).data()
        self.assertEqual(obj_name_0, 'dory')
        self.assertEqual(obj_name_1, 'rascal')
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        obj_name_lst_2 = model.index(2, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'dory,rascal')
        self.assertEqual(obj_name_lst_1, 'dory,scooby')
        self.assertEqual(obj_name_lst_2, 'rascal,dory')

    def test_update_relationship_classes(self):
        """Test that relationship classes are updated on all model/views.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch object classes and objects
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_index)
        # Update relationship classes
        upd_fish_dog_class = self.RelationshipClass(
                fish_dog_class.id, "octopus__god",
                str(fish_class.id) + "," + str(dog_class.id), "fish,dog")

        upd_dog_fish_class = self.RelationshipClass(
                dog_fish_class.id, "god__octopus",
                str(dog_class.id) + "," + str(fish_class.id), "dog,fish")
        # Make wide_relationship_class_list return something meaningful
        def side_effect(object_class_id=None):
            if object_class_id in (fish_class.id, dog_class.id):
                return [upd_fish_dog_class, upd_dog_fish_class]
            elif object_class_id is None:
                return [upd_fish_dog_class, upd_dog_fish_class]
            else:
                return []
        self.tree_view_form.db_map.wide_relationship_class_list.side_effect = side_effect
        self.tree_view_form.update_relationship_classes([upd_fish_dog_class, upd_dog_fish_class])
        # Check object tree
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_fish_dog_item = pluto_item.child(0)
        pluto_dog_fish_item = pluto_item.child(1)
        scooby_fish_dog_item = scooby_item.child(0)
        scooby_dog_fish_item = scooby_item.child(1)
        nemo_fish_dog_type = nemo_fish_dog_item.data(Qt.UserRole)
        nemo_fish_dog_name = nemo_fish_dog_item.data(Qt.UserRole + 1)['name']
        nemo_dog_fish_type = nemo_dog_fish_item.data(Qt.UserRole)
        nemo_dog_fish_name = nemo_dog_fish_item.data(Qt.UserRole + 1)['name']
        pluto_fish_dog_type = pluto_fish_dog_item.data(Qt.UserRole)
        pluto_fish_dog_name = pluto_fish_dog_item.data(Qt.UserRole + 1)['name']
        pluto_dog_fish_type = pluto_dog_fish_item.data(Qt.UserRole)
        pluto_dog_fish_name = pluto_dog_fish_item.data(Qt.UserRole + 1)['name']
        scooby_fish_dog_type = scooby_fish_dog_item.data(Qt.UserRole)
        scooby_fish_dog_name = scooby_fish_dog_item.data(Qt.UserRole + 1)['name']
        scooby_dog_fish_type = scooby_dog_fish_item.data(Qt.UserRole)
        scooby_dog_fish_name = scooby_dog_fish_item.data(Qt.UserRole + 1)['name']
        self.assertEqual(nemo_fish_dog_type, "relationship_class")
        self.assertEqual(nemo_fish_dog_name, "octopus__god")
        self.assertEqual(nemo_dog_fish_type, "relationship_class")
        self.assertEqual(nemo_dog_fish_name, "god__octopus")
        self.assertEqual(pluto_fish_dog_type, "relationship_class")
        self.assertEqual(pluto_fish_dog_name, "octopus__god")
        self.assertEqual(pluto_dog_fish_type, "relationship_class")
        self.assertEqual(pluto_dog_fish_name, "god__octopus")
        self.assertEqual(scooby_fish_dog_type, "relationship_class")
        self.assertEqual(scooby_fish_dog_name, "octopus__god")
        self.assertEqual(scooby_dog_fish_type, "relationship_class")
        self.assertEqual(scooby_dog_fish_name, "god__octopus")
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        rel_cls_name_0 = model.index(0, header_index("relationship_class_name")).data()
        rel_cls_name_1 = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name_0, 'octopus__god')
        self.assertEqual(rel_cls_name_1, 'god__octopus')
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        rel_cls_name_0 = model.index(0, header_index("relationship_class_name")).data()
        rel_cls_name_1 = model.index(1, header_index("relationship_class_name")).data()
        rel_cls_name_2 = model.index(2, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name_0, 'octopus__god')
        self.assertEqual(rel_cls_name_1, 'octopus__god')
        self.assertEqual(rel_cls_name_2, 'god__octopus')

    def test_update_relationships(self):
        """Test that relationships are updated on all model/views.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_index)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_dog_fish_item = pluto_item.child(1)
        scooby_dog_fish_item = scooby_item.child(1)
        nemo_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_dog_fish_item)
        pluto_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_dog_fish_item)
        scooby_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_dog_fish_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_dog_fish_index)
        # Update relationship
        upd_pluto_nemo_rel = self.Relationship(
            pluto_nemo_rel.id, dog_fish_class.id, "dog__fish_scooby__nemo",
            str(scooby_object.id) + "," + str(nemo_object.id), "scooby,nemo")
        def side_effect(class_id, object_id):
            if class_id == dog_fish_class.id:
                if object_id in (nemo_object.id, pluto_object.id):
                    return [upd_pluto_nemo_rel]
                else:
                    return []
            elif class_id == fish_dog_class.id:
                if object_id == nemo_object.id:
                    return [nemo_pluto_rel, nemo_scooby_rel]
                elif object_id == pluto_object.id:
                    return [nemo_pluto_rel]
                elif object_id == scooby_object.id:
                    return [nemo_scooby_rel]
                else:
                    return []
            else:
                return []
        self.tree_view_form.db_map.wide_relationship_list.side_effect = side_effect
        self.tree_view_form.update_relationships([upd_pluto_nemo_rel])
        # Check object tree
        scooby_nemo_item1 = nemo_dog_fish_item.child(0)
        scooby_nemo_item2 = scooby_dog_fish_item.child(0)
        scooby_nemo_item1_type = scooby_nemo_item1.data(Qt.UserRole)
        scooby_nemo_item1_name = scooby_nemo_item1.data(Qt.UserRole + 1)['name']
        scooby_nemo_item2_type = scooby_nemo_item2.data(Qt.UserRole)
        scooby_nemo_item2_name = scooby_nemo_item2.data(Qt.UserRole + 1)['name']
        self.assertEqual(scooby_nemo_item1_type, "relationship")
        self.assertEqual(scooby_nemo_item1_name, "dog__fish_scooby__nemo")
        self.assertEqual(scooby_nemo_item2_type, "relationship")
        self.assertEqual(scooby_nemo_item2_name, "dog__fish_scooby__nemo")
        self.assertEqual(pluto_dog_fish_item.rowCount(), 0)

    def test_remove_object_classes(self):
        """Test that object classes are removed from all model/views.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch pluto, so we can test that 'child' relationship classes are correctly removed
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.assertEqual(pluto_item.rowCount(), 2)
        # Select fish and call the removal method
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_index, QItemSelectionModel.Select)
        self.tree_view_form.remove_object_tree_items()
        # Check object tree
        dog_item = root_item.child(0)
        dog_type = dog_item.data(Qt.UserRole)
        dog_name = dog_item.data(Qt.UserRole + 1)['name']
        self.assertEqual(dog_type, "object_class")
        self.assertEqual(dog_name, "dog")
        self.assertEqual(root_item.rowCount(), 1)
        self.assertEqual(pluto_item.rowCount(), 0)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'dog')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        obj_cls_name_1 = model.index(1, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'dog')
        self.assertEqual(obj_cls_name_1, 'dog')
        self.assertEqual(model.rowCount(), 3)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        self.assertEqual(model.rowCount(), 1)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        self.assertEqual(model.rowCount(), 1)

    def test_remove_objects(self):
        """Test that objects are removed from all model/views.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch pluto's fish__dog and dog__fish relationship class items,
        # so we can test that 'child' relationships are correctly removed
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        pluto_fish_dog_item = pluto_item.child(0)
        pluto_dog_fish_item = pluto_item.child(1)
        pluto_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_fish_dog_item)
        pluto_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_dog_fish_item)
        self.tree_view_form.object_tree_model.fetchMore(pluto_fish_dog_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_dog_fish_index)
        self.assertEqual(pluto_fish_dog_item.rowCount(), 1)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 1)
        # Select nemo and call removal method
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(nemo_index, QItemSelectionModel.Select)
        self.tree_view_form.remove_object_tree_items()
        # Check object tree
        self.assertEqual(fish_item.rowCount(), 0)
        self.assertEqual(pluto_fish_dog_item.rowCount(), 0)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 0)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_0 = model.index(0, header_index("object_name")).data()
        obj_name_1 = model.index(1, header_index("object_name")).data()
        self.assertEqual(obj_name_0, 'pluto')
        self.assertEqual(obj_name_1, 'scooby')
        self.assertEqual(model.rowCount(), 3)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        self.assertEqual(model.rowCount(), 1)

    def test_remove_relationship_classes(self):
        """Test that relationship classes are removed from all model/views.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch object classes and objects, so we can test that relationship classes are removed from all objects
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_index)
        self.assertEqual(nemo_item.rowCount(), 2)
        self.assertEqual(nemo_item.rowCount(), 2)
        self.assertEqual(nemo_item.rowCount(), 2)
        # Select nemo's fish__dog relationship class item and call removal method
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(nemo_fish_dog_index, QItemSelectionModel.Select)
        self.tree_view_form.remove_object_tree_items()
        # Check object tree
        self.assertEqual(nemo_item.rowCount(), 1)
        self.assertEqual(nemo_item.rowCount(), 1)
        self.assertEqual(nemo_item.rowCount(), 1)
        nemo_dog_fish_item = nemo_item.child(0)
        pluto_dog_fish_item = pluto_item.child(0)
        scooby_dog_fish_item = scooby_item.child(0)
        nemo_dog_fish_type = nemo_dog_fish_item.data(Qt.UserRole)
        nemo_dog_fish_name = nemo_dog_fish_item.data(Qt.UserRole + 1)['name']
        pluto_dog_fish_type = pluto_dog_fish_item.data(Qt.UserRole)
        pluto_dog_fish_name = pluto_dog_fish_item.data(Qt.UserRole + 1)['name']
        scooby_dog_fish_type = scooby_dog_fish_item.data(Qt.UserRole)
        scooby_dog_fish_name = scooby_dog_fish_item.data(Qt.UserRole + 1)['name']
        self.assertEqual(nemo_dog_fish_type, "relationship_class")
        self.assertEqual(nemo_dog_fish_name, "dog__fish")
        self.assertEqual(pluto_dog_fish_type, "relationship_class")
        self.assertEqual(pluto_dog_fish_name, "dog__fish")
        self.assertEqual(scooby_dog_fish_type, "relationship_class")
        self.assertEqual(scooby_dog_fish_name, "dog__fish")
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        rel_cls_name_0 = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name_0, 'dog__fish')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        rel_cls_name_0 = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name_0, 'dog__fish')
        self.assertEqual(model.rowCount(), 2)

    def test_remove_relationships(self):
        """Test that relationships are removed from all model/views.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch nemo's and pluto's dog_fish relationship class,
        # to test that both intances of the relationship are removed.
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_dog_fish_item = pluto_item.child(1)
        nemo_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_dog_fish_item)
        pluto_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_dog_fish_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_dog_fish_index)
        self.assertEqual(nemo_dog_fish_item.rowCount(), 1)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 1)
        # Select nemo's pluto__nemo relationship item and call removal method
        pluto_nemo_item = nemo_dog_fish_item.child(0)
        pluto_nemo_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_nemo_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(pluto_nemo_index, QItemSelectionModel.Select)
        self.tree_view_form.remove_object_tree_items()
        # Check object tree
        self.assertEqual(nemo_dog_fish_item.rowCount(), 0)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 0)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'nemo,pluto')
        self.assertEqual(obj_name_lst_1, 'nemo,scooby')
        self.assertEqual(model.rowCount(), 3)

    def test_update_object_parameter_definitions(self):
        """Test that object parameter definitions are updated using the table delegate."""
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Update parameter name
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "water")
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.text(), "water")
        editor.setText("fire")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        # Check object parameter definition table
        self.assertEqual(parameter_name_index.data(), 'fire')
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        parameter_name_0 = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name_0, 'fire')

    def test_update_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions are updated using the table delegate."""
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Update parameter name
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header_index = model.horizontal_header_labels().index
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "relative_speed")
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.text(), "relative_speed")
        editor.setText("equivalent_ki")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        # Check relationship parameter definition table
        self.assertEqual(parameter_name_index.data(), 'equivalent_ki')
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        parameter_name1 = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, 'equivalent_ki')
        self.assertEqual(parameter_name1, 'equivalent_ki')

    def test_update_object_parameter_values(self):
        """Test that object parameter values are updated using the table delegate."""
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Update parameter value
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_value_index = model.index(0, header_index("value"))
        self.assertEqual(parameter_value_index.data(), "salt")
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_value_index)
        view.itemDelegate().setEditorData(editor, parameter_value_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.text(), "salt")
        editor.setText("pepper")
        view.itemDelegate().setModelData(editor, model, parameter_value_index)
        view.itemDelegate().destroyEditor(editor, parameter_value_index)
        # Check object parameter value table
        self.assertEqual(parameter_value_index.data(), 'pepper')

    def test_update_relationship_parameter_values(self):
        """Test that relationship parameter values are updated using the table delegate."""
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Update parameter value
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_value_index = model.index(0, header_index("value"))
        self.assertEqual(parameter_value_index.data(), -1)
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_value_index)
        view.itemDelegate().setEditorData(editor, parameter_value_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.text(), "-1")
        editor.setText("1")
        view.itemDelegate().setModelData(editor, model, parameter_value_index)
        view.itemDelegate().destroyEditor(editor, parameter_value_index)
        # Check object parameter value table
        self.assertEqual(parameter_value_index.data(), '1')

    def test_remove_object_parameter_definitions(self):
        """Test that object parameter definitions are removed."""
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Select parameter definition and call removal method
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "water")
        self.tree_view_form.ui.tableView_object_parameter_definition.selectionModel().select(
            parameter_name_index, QItemSelectionModel.Select)
        self.tree_view_form.remove_object_parameter_definitions()
        # Check object parameter definition table
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "breed")
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        parameter_name_0 = model.index(0, header_index("parameter_name")).data()
        parameter_name_1 = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name_0, 'breed')
        self.assertEqual(parameter_name_1, 'breed')
        self.assertEqual(model.rowCount(), 3)

    def test_remove_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions are removed."""
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Select parameter definition and call removal method
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header_index = model.horizontal_header_labels().index
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "relative_speed")
        self.tree_view_form.ui.tableView_relationship_parameter_definition.selectionModel().select(
            parameter_name_index, QItemSelectionModel.Select)
        self.tree_view_form.remove_relationship_parameter_definitions()
        # Check relationship parameter definition table
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "combined_mojo")
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        parameter_name = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'combined_mojo')
        self.assertEqual(model.rowCount(), 2)

    def test_remove_object_parameter_values(self):
        """Test that object parameter values are removed."""
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Select two parameter values and call removal method
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_name0_index = model.index(0, header_index("parameter_name"))
        parameter_name2_index = model.index(2, header_index("parameter_name"))
        self.assertEqual(parameter_name0_index.data(), "water")
        self.assertEqual(parameter_name2_index.data(), "breed")
        self.tree_view_form.ui.tableView_object_parameter_value.selectionModel().select(
            parameter_name0_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.tableView_object_parameter_value.selectionModel().select(
            parameter_name2_index, QItemSelectionModel.Select)
        self.tree_view_form.remove_object_parameter_values()
        # Check object parameter value table
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, "breed")
        self.assertEqual(model.rowCount(), 2)

    def test_remove_relationship_parameter_values(self):
        """Test that relationship parameter values are removed."""
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Select two parameter values and call removal method
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_name0_index = model.index(0, header_index("parameter_name"))
        parameter_name2_index = model.index(2, header_index("parameter_name"))
        self.assertEqual(parameter_name0_index.data(), "relative_speed")
        self.assertEqual(parameter_name2_index.data(), "combined_mojo")
        self.tree_view_form.ui.tableView_relationship_parameter_value.selectionModel().select(
            parameter_name0_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.tableView_relationship_parameter_value.selectionModel().select(
            parameter_name2_index, QItemSelectionModel.Select)
        self.tree_view_form.remove_relationship_parameter_values()
        # Check relationship parameter value table
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, "relative_speed")
        self.assertEqual(model.rowCount(), 2)

    def test_filter_parameter_tables_per_object_class(self):
        """Test that parameter value and definition tables are filtered
        when selecting object classes in the object tree.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        # Select fish object class in object tree
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_index, QItemSelectionModel.Select)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(obj_cls_name_lst_1, 'dog,fish')
        self.assertEqual(model.rowCount(), 3)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        obj_cls_name_lst_2 = model.index(2, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(obj_cls_name_lst_1, 'fish,dog')
        self.assertEqual(obj_cls_name_lst_2, 'dog,fish')
        self.assertEqual(model.rowCount(), 4)

    def test_filter_parameter_tables_per_object(self):
        """Test that parameter value and definition tables are filtered
        when selecting objects in the object tree.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        # Select pluto object in object tree
        self.tree_view_form.ui.treeView_object.selectionModel().select(pluto_index, QItemSelectionModel.Select)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'dog')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_0 = model.index(0, header_index("object_name")).data()
        self.assertEqual(obj_name_0, 'pluto')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(obj_cls_name_lst_1, 'dog,fish')
        self.assertEqual(model.rowCount(), 3)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'nemo,pluto')
        self.assertEqual(obj_name_lst_1, 'pluto,nemo')
        self.assertEqual(model.rowCount(), 3)

    def test_filter_parameter_tables_per_relationship_class(self):
        """Test that parameter value and definition tables are filtered
        when selecting relationship classes in the object tree.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        # Select nemo's fish__dog relationship class in object tree
        self.tree_view_form.ui.treeView_object.selectionModel().select(nemo_fish_dog_index, QItemSelectionModel.Select)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'nemo,pluto')
        self.assertEqual(obj_name_lst_1, 'nemo,scooby')
        self.assertEqual(model.rowCount(), 3)

    def test_filter_parameter_tables_per_relationship(self):
        """Test that parameter value and definition tables are filtered
        when selecting relationships in the object tree.
        """
        fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter = self.add_mock_dataset()
        # Fetch object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_fish_dog_index)
        nemo_pluto_item = nemo_fish_dog_item.child(0)
        nemo_pluto_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_pluto_item)
        # Select nemo__pluto relationship class in object tree
        self.tree_view_form.ui.treeView_object.selectionModel().select(nemo_pluto_index, QItemSelectionModel.Select)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'nemo,pluto')
        self.assertEqual(model.rowCount(), 2)

    def add_mock_object_classes(self):
        """Add fish and dog object classes."""
        fish_class = self.ObjectClass(1, "fish", "A fish.", 1)
        dog_class = self.ObjectClass(2, "dog", "A dog.", 3)
        self.tree_view_form.db_map.object_class_list.return_value = [fish_class, dog_class]
        return fish_class, dog_class

    def add_mock_objects(self, fish_class_id, dog_class_id):
        """Add nemo, pluto and scooby objects."""
        nemo_object = self.Object(1, fish_class_id, 'nemo', 'The lost one.')
        pluto_object = self.Object(2, dog_class_id, 'pluto', "Mickey's.")
        scooby_object = self.Object(3, dog_class_id, 'scooby', 'Scooby-Dooby-Doo.')
        def side_effect(class_id=None):
            if class_id == fish_class_id:
                return [nemo_object]
            elif class_id == dog_class_id:
                return [pluto_object, scooby_object]
            elif class_id is None:
                return [nemo_object, pluto_object, scooby_object]
            else:
                return []
        self.tree_view_form.db_map.object_list.side_effect = side_effect
        return nemo_object, pluto_object, scooby_object

    def add_mock_relationship_classes(self, fish_class_id, dog_class_id):
        """Add dog__fish and fish__dog relationship classes."""
        fish_dog_class = self.RelationshipClass(
            1, "fish__dog", str(fish_class_id) + "," + str(dog_class_id), "fish,dog")
        dog_fish_class = self.RelationshipClass(
            2, "dog__fish", str(dog_class_id) + "," + str(fish_class_id), "dog,fish")
        def side_effect(object_class_id=None):
            if object_class_id in (fish_class_id, dog_class_id):
                return [fish_dog_class, dog_fish_class]
            elif object_class_id is None:
                return [fish_dog_class, dog_fish_class]
            else:
                return []
        self.tree_view_form.db_map.wide_relationship_class_list.side_effect = side_effect
        return fish_dog_class, dog_fish_class

    def add_mock_relationships(
            self, fish_dog_class_id, dog_fish_class_id, pluto_object_id, nemo_object_id, scooby_object_id):
        """Add pluto_nemo, nemo_pluto and nemo_scooby relationships."""
        pluto_nemo_rel = self.Relationship(
            1, dog_fish_class_id, "dog__fish_pluto__nemo",
            str(pluto_object_id) + "," + str(nemo_object_id), "pluto,nemo")
        nemo_pluto_rel = self.Relationship(
            2, fish_dog_class_id, "fish__dog_nemo__pluto",
            str(nemo_object_id) + "," + str(pluto_object_id), "nemo,pluto")
        nemo_scooby_rel = self.Relationship(
            3, fish_dog_class_id, "fish__dog_nemo__scooby",
            str(nemo_object_id) + "," + str(scooby_object_id), "nemo,scooby")
        def side_effect(class_id=None, object_id=None):
            if class_id == dog_fish_class_id:
                if object_id in (nemo_object_id, pluto_object_id):
                    return [pluto_nemo_rel]
                else:
                    return []
            elif class_id == fish_dog_class_id:
                if object_id == nemo_object_id:
                    return [nemo_pluto_rel, nemo_scooby_rel]
                elif object_id == pluto_object_id:
                    return [nemo_pluto_rel]
                elif object_id == scooby_object_id:
                    return [nemo_scooby_rel]
                else:
                    return []
            elif class_id is None and object_id is None:
                return [pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel]
            else:
                return []
        self.tree_view_form.db_map.wide_relationship_list.side_effect = side_effect
        return pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel

    def add_mock_object_parameter_definitions(self, fish_class_id, dog_class_id):
        """Add water and breed object parameter definitions."""
        water_parameter = self.ObjectParameter(1, fish_class_id, "fish", "water")
        breed_parameter = self.ObjectParameter(2, dog_class_id, "dog", "breed")
        def side_effect(object_class_id=None):
            if object_class_id == fish_class_id:
                return [water_parameter]
            elif object_class_id == dog_class_id:
                return [breed_parameter]
            elif object_class_id is None:
                return [water_parameter, breed_parameter]
            else:
                return []
        self.tree_view_form.db_map.object_parameter_list.side_effect = side_effect
        return water_parameter, breed_parameter

    def add_mock_relationship_parameter_definitions(
            self, fish_class_id, dog_class_id, fish_dog_class_id, dog_fish_class_id):
        """Add relative speed and combined mojo relationship parameter definitions."""
        relative_speed_parameter = self.RelationshipParameter(
            1, fish_dog_class_id, "fish__dog", str(fish_class_id) + "," + str(dog_class_id),
            "fish,dog", "relative_speed")
        combined_mojo_parameter = self.RelationshipParameter(
            2, dog_fish_class_id, "dog__fish", str(dog_class_id) + "," + str(fish_class_id),
            "dog,fish", "combined_mojo")
        def side_effect(relationship_class_id=None):
            if relationship_class_id == fish_dog_class_id:
                return [relative_speed_parameter]
            elif relationship_class_id == dog_fish_class_id:
                return [combined_mojo_parameter]
            elif relationship_class_id is None:
                return [relative_speed_parameter, combined_mojo_parameter]
            else:
                return []
        self.tree_view_form.db_map.relationship_parameter_list.side_effect = side_effect
        return relative_speed_parameter, combined_mojo_parameter

    def add_mock_object_parameter_values(
            self, fish_class_id, dog_class_id, nemo_object_id, pluto_object_id, scooby_object_id,
            water_parameter_id, breed_parameter_id):
        """Add some object parameter values."""
        nemo_water = self.ObjectParameterValue(
            1, fish_class_id, "fish", nemo_object_id, "nemo", water_parameter_id, "water", 1, "salt")
        pluto_breed = self.ObjectParameterValue(
            2, dog_class_id, "dog", pluto_object_id, 'pluto', breed_parameter_id, "breed", 1, "bloodhound")
        scooby_breed = self.ObjectParameterValue(
            3, dog_class_id, "dog", scooby_object_id, "scooby", breed_parameter_id, "breed", 1, "great dane")
        def side_effect():
            return [nemo_water, pluto_breed, scooby_breed]
        self.tree_view_form.db_map.object_parameter_value_list.side_effect = side_effect

    def add_mock_relationship_parameter_values(
            self, fish_class_id, dog_class_id, nemo_object_id, pluto_object_id, scooby_object_id,
            fish_dog_class_id, dog_fish_class_id,
            nemo_pluto_rel_id, nemo_scooby_rel_id, pluto_nemo_rel_id,
            relative_speed_parameter_id, combined_mojo_parameter_id):
        """Add some relationship parameter values."""
        nemo_pluto_relative_speed = self.RelationshipParameterValue(
            1, fish_dog_class_id, "fish__dog", str(fish_class_id) + "," + str(dog_class_id), "fish,dog",
            nemo_pluto_rel_id, str(nemo_object_id) + "," + str(pluto_object_id), "nemo,pluto",
            relative_speed_parameter_id, "relative_speed", 1, -1)
        nemo_scooby_relative_speed = self.RelationshipParameterValue(
            2, fish_dog_class_id, "fish__dog", str(fish_class_id) + "," + str(dog_class_id), "fish,dog",
            nemo_scooby_rel_id, str(nemo_object_id) + "," + str(scooby_object_id), "nemo,scooby",
            relative_speed_parameter_id, "relative_speed", 1, 5)
        pluto_nemo_combined_mojo = self.RelationshipParameterValue(
            3, dog_fish_class_id, "dog__fish", str(dog_class_id) + "," + str(fish_class_id), "dog,fish",
            pluto_nemo_rel_id, str(pluto_object_id) + "," + str(nemo_object_id), "pluto,nemo",
            combined_mojo_parameter_id, "combined_mojo", 1, 100)
        def side_effect():
            return [nemo_pluto_relative_speed, nemo_scooby_relative_speed, pluto_nemo_combined_mojo]
        self.tree_view_form.db_map.relationship_parameter_value_list.side_effect = side_effect

    def add_mock_dataset(self):
        """Add mock dataset."""
        fish_class, dog_class = self.add_mock_object_classes()
        nemo_object, pluto_object, scooby_object = self.add_mock_objects(fish_class.id, dog_class.id)
        fish_dog_class, dog_fish_class = self.add_mock_relationship_classes(fish_class.id, dog_class.id)
        pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel = self.add_mock_relationships(
            fish_dog_class.id, dog_fish_class.id, pluto_object.id, nemo_object.id, scooby_object.id)
        water_parameter, breed_parameter = self.add_mock_object_parameter_definitions(
            fish_class.id, dog_class.id)
        relative_speed_parameter, combined_mojo_parameter = self.add_mock_relationship_parameter_definitions(
            fish_class.id, dog_class.id, fish_dog_class.id, dog_fish_class.id)
        self.add_mock_object_parameter_values(
            fish_class.id, dog_class.id, nemo_object.id, pluto_object.id, scooby_object.id,
            water_parameter.id, breed_parameter.id)
        self.add_mock_relationship_parameter_values(
            fish_class.id, dog_class.id, nemo_object.id, pluto_object.id, scooby_object.id,
            fish_dog_class.id, dog_fish_class.id,
            nemo_pluto_rel.id, nemo_scooby_rel.id, pluto_nemo_rel.id,
            relative_speed_parameter.id, combined_mojo_parameter.id)
        self.tree_view_form.init_models()
        return fish_class, dog_class, nemo_object, pluto_object, scooby_object, \
            fish_dog_class, dog_fish_class, \
            pluto_nemo_rel, nemo_pluto_rel, nemo_scooby_rel, \
            water_parameter, breed_parameter, \
            relative_speed_parameter, combined_mojo_parameter


if __name__ == '__main__':
    unittest.main()
