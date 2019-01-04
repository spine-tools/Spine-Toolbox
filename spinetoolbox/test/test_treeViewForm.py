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
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication, QStyleOptionViewItem
from PySide2.QtCore import Qt, QItemSelectionModel
from widgets.data_store_widgets import TreeViewForm
from spinedatabase_api import DiffDatabaseMapping, create_new_spine_database
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

    def setUp(self):
        """Overridden method. Runs before each test. Makes instances of TreeViewForm and GraphViewForm classes.
        """
        # Set logging level to Error to silence "Logging level: All messages" print
        with mock.patch("data_store.DataStore") as mock_data_store:
            logging.disable(level=logging.ERROR)  # Disable logging
            try:
                os.remove('mock_db.sqlite')
            except OSError:
                pass
            db_url = "sqlite:///mock_db.sqlite"
            create_new_spine_database(db_url)
            db_map = DiffDatabaseMapping(db_url, "UnitTest")
            db_map.reset_mapping()
            self.tree_view_form = TreeViewForm(mock_data_store, db_map, "mock_db")
            logging.disable(level=logging.NOTSET)  # Enable logging

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.tree_view_form.close()
        try:
            os.remove('mock_db.sqlite')
        except OSError:
            pass

    def test_add_object_classes(self):
        """Test that object classes are added to the object tree model in the right positions.
        """
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        cat = dict(
            name='cat',
            description='A cat.',
            display_order=2
        )
        object_classes = self.tree_view_form.db_map.add_object_classes(fish, dog, cat)
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
        # Add classes and objects
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        fish_object_class = self.tree_view_form.db_map.add_object_class(**fish)
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        self.tree_view_form.add_object_classes([fish_object_class, dog_object_class])
        fish_class_id = fish_object_class.id
        dog_class_id = dog_object_class.id
        nemo = dict(
            class_id=fish_class_id,
            name='nemo',
            description='The lost one.'
        )
        dory = dict(
            class_id=fish_class_id,
            name='dory',
            description="Nemo's girl."
        )
        pluto = dict(
            class_id=dog_class_id,
            name='pluto',
            description="Mickey's."
        )
        scooby = dict(
            class_id=dog_class_id,
            name='scooby',
            description="Scooby-Dooby-Doo."
        )
        objects = self.tree_view_form.db_map.add_objects(nemo, dory, pluto, scooby)
        self.tree_view_form.add_objects(objects)
        # Check tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
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
        self.assertEqual(nemo_class_id, fish_class_id)
        self.assertEqual(nemo_id, 1)
        self.assertEqual(nemo_name, "nemo")
        self.assertEqual(dory_type, "object")
        self.assertEqual(dory_class_id, fish_class_id)
        self.assertEqual(dory_id, 2)
        self.assertEqual(dory_name, "dory")
        self.assertEqual(fish_item.rowCount(), 2)
        self.assertEqual(pluto_type, "object")
        self.assertEqual(pluto_class_id, dog_class_id)
        self.assertEqual(pluto_id, 3)
        self.assertEqual(pluto_name, "pluto")
        self.assertEqual(scooby_type, "object")
        self.assertEqual(scooby_class_id, dog_class_id)
        self.assertEqual(scooby_id, 4)
        self.assertEqual(scooby_name, "scooby")
        self.assertEqual(fish_item.rowCount(), 2)

    def test_add_relationship_classes(self):
        """Test that relationship classes are added to the object tree model.
        """
        # Add fish and dog object classes
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        fish_object_class = self.tree_view_form.db_map.add_object_class(**fish)
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        self.tree_view_form.add_object_classes([fish_object_class, dog_object_class])
        fish_class_id = fish_object_class.id
        dog_class_id = dog_object_class.id
        # Add nemo object before adding the relationships to test fetch more
        nemo = dict(
            class_id=fish_class_id,
            name='nemo',
            description='The lost one.'
        )
        nemo_object = self.tree_view_form.db_map.add_object(**nemo)
        self.tree_view_form.add_objects([nemo_object])
        # Add dog__fish and fish__dog relationship classes
        dog_fish = dict(
            name="dog__fish",
            object_class_id_list=[dog_class_id, fish_class_id]
        )
        fish_dog = dict(
            name="fish__dog",
            object_class_id_list=[fish_class_id, dog_class_id]
        )
        relationship_classes = self.tree_view_form.db_map.add_wide_relationship_classes(dog_fish, fish_dog)
        self.tree_view_form.add_relationship_classes(relationship_classes)
        # Add pluto object after adding the relationships to test fetch more
        pluto = dict(
            class_id=dog_class_id,
            name='pluto',
            description="Mickey's."
        )
        pluto_object = self.tree_view_form.db_map.add_object(**pluto)
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
        self.assertEqual(split_nemo_dog_fish_object_class_id_list, [dog_class_id, fish_class_id])
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
        self.assertEqual(split_pluto_fish_dog_object_class_id_list, [fish_class_id, dog_class_id])
        self.assertEqual(pluto_fish_dog_object_class_name_list, "fish,dog")
        self.assertEqual(pluto_item.rowCount(), 2)

    def test_add_relationships(self):
        """Test that relationships are added to the object tree model.
        """
        # Add fish and dog object classes
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        fish_object_class = self.tree_view_form.db_map.add_object_class(**fish)
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        self.tree_view_form.add_object_classes([fish_object_class, dog_object_class])
        fish_class_id = fish_object_class.id
        dog_class_id = dog_object_class.id
        # Add nemo, pluto and scooby objects
        nemo = dict(
            class_id=fish_class_id,
            name='nemo',
            description='The lost one.'
        )
        nemo_object = self.tree_view_form.db_map.add_object(**nemo)
        pluto = dict(
            class_id=dog_class_id,
            name='pluto',
            description="Mickey's."
        )
        pluto_object = self.tree_view_form.db_map.add_object(**pluto)
        scooby = dict(
            class_id=dog_class_id,
            name='scooby',
            description="Scooby-Dooby-Doo."
        )
        scooby_object = self.tree_view_form.db_map.add_object(**scooby)
        self.tree_view_form.add_objects([nemo_object, pluto_object, scooby_object])
        # Add dog__fish and fish__dog relationship classes
        dog_fish = dict(
            name="dog__fish",
            object_class_id_list=[dog_class_id, fish_class_id]
        )
        fish_dog = dict(
            name="fish__dog",
            object_class_id_list=[fish_class_id, dog_class_id]
        )
        dog_fish_relationship_class = self.tree_view_form.db_map.add_wide_relationship_class(**dog_fish)
        fish_dog_relationship_class = self.tree_view_form.db_map.add_wide_relationship_class(**fish_dog)
        # Add relationship classes
        self.tree_view_form.add_relationship_classes([fish_dog_relationship_class, dog_fish_relationship_class])
        # Add pluto_nemo, nemo_pluto and nemo_scooby relationships
        pluto_nemo = dict(
            class_id=dog_fish_relationship_class.id,
            object_id_list=[pluto_object.id, nemo_object.id],
            name='dog__fish_pluto__nemo'
        )
        nemo_pluto = dict(
            class_id=fish_dog_relationship_class.id,
            object_id_list=[nemo_object.id, pluto_object.id],
            name='fish__dog_nemo__pluto'
        )
        nemo_scooby = dict(
            class_id=fish_dog_relationship_class.id,
            object_id_list=[nemo_object.id, scooby_object.id],
            name='fish__dog_nemo__scooby'
        )
        relationships = self.tree_view_form.db_map.add_wide_relationships(pluto_nemo, nemo_pluto, nemo_scooby)
        self.tree_view_form.add_relationships(relationships)
        # Get items
        root_item = self.tree_view_form.object_tree_model.root_item
        # Object class items
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        # Object items
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        # Relationship class items
        nemo_dog_fish_item = nemo_item.child(0)
        nemo_fish_dog_item = nemo_item.child(1)
        pluto_dog_fish_item = pluto_item.child(0)
        pluto_fish_dog_item = pluto_item.child(1)
        scooby_dog_fish_item = scooby_item.child(0)
        scooby_fish_dog_item = scooby_item.child(1)
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
        self.assertEqual(pluto_nemo_item1_name, 'dog__fish_pluto__nemo')
        self.assertEqual(pluto_nemo_item1_class_id, dog_fish_relationship_class.id)
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
        self.assertEqual(pluto_nemo_item2_name, 'dog__fish_pluto__nemo')
        self.assertEqual(pluto_nemo_item2_class_id, dog_fish_relationship_class.id)
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
        self.assertEqual(nemo_pluto_item1_name, 'fish__dog_nemo__pluto')
        self.assertEqual(nemo_pluto_item1_class_id, fish_dog_relationship_class.id)
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
        self.assertEqual(nemo_pluto_item2_name, 'fish__dog_nemo__pluto')
        self.assertEqual(nemo_pluto_item2_class_id, fish_dog_relationship_class.id)
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
        self.assertEqual(nemo_scooby_item1_name, 'fish__dog_nemo__scooby')
        self.assertEqual(nemo_scooby_item1_class_id, fish_dog_relationship_class.id)
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
        self.assertEqual(nemo_scooby_item2_name, 'fish__dog_nemo__scooby')
        self.assertEqual(nemo_scooby_item2_class_id, fish_dog_relationship_class.id)
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item2_object_id_list.split(",")]
        self.assertEqual(split_scooby_nemo_object_id_list, [nemo_object.id, scooby_object.id])
        self.assertEqual(nemo_scooby_item2_object_name_list, "nemo,scooby")

    def test_add_object_parameter_definitions(self):
        """Test that object parameter definitions are added to the model.
        """
        # Add fish and dog object classes
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        fish_object_class = self.tree_view_form.db_map.add_object_class(**fish)
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        self.tree_view_form.add_object_classes([fish_object_class, dog_object_class])
        fish_class_id = fish_object_class.id
        dog_class_id = dog_object_class.id
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
        self.assertEqual(obj_cls_id_index.data(), dog_class_id)
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
        # Check the db
        parameter_id = model.index(0, header_index("id")).data()
        parameter = self.tree_view_form.db_map.single_parameter(id=parameter_id).one_or_none()
        self.assertEqual(parameter.name, 'breed')
        self.assertEqual(parameter.object_class_id, dog_class_id)
        self.assertIsNone(parameter.relationship_class_id)

    def test_add_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions are added to the model.
        """
        # Add fish and dog object classes
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        fish_object_class = self.tree_view_form.db_map.add_object_class(**fish)
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        self.tree_view_form.add_object_classes([fish_object_class, dog_object_class])
        fish_class_id = fish_object_class.id
        dog_class_id = dog_object_class.id
        # Add nemo and scooby objects
        nemo = dict(
            class_id=fish_class_id,
            name='nemo',
            description='The lost one.'
        )
        scooby = dict(
            class_id=dog_class_id,
            name='scooby',
            description="Scooby-Dooby-Doo."
        )
        nemo_object = self.tree_view_form.db_map.add_object(**nemo)
        scooby_object = self.tree_view_form.db_map.add_object(**scooby)
        self.tree_view_form.add_objects([nemo_object, scooby_object])
        # Add fish__dog and dog__fish relationship classes
        fish_dog = dict(
            name="fish__dog",
            object_class_id_list=[fish_class_id, dog_class_id]
        )
        dog_fish = dict(
            name="dog__fish",
            object_class_id_list=[dog_class_id, fish_class_id]
        )
        fish_dog_relationship_class = self.tree_view_form.db_map.add_wide_relationship_class(**fish_dog)
        dog_fish_relationship_class = self.tree_view_form.db_map.add_wide_relationship_class(**dog_fish)
        fish_dog_class_id = fish_dog_relationship_class.id
        dog_fish_class_id = dog_fish_relationship_class.id
        self.tree_view_form.add_relationship_classes([fish_dog_relationship_class, dog_fish_relationship_class])
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
        self.assertEqual(rel_cls_id_index.data(), dog_fish_class_id)
        obj_cls_name_list_index = model.index(0, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'dog,fish')
        obj_cls_id_list_index = model.index(0, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [dog_class_id, fish_class_id])
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
        # Check the db
        parameter_id = model.index(0, header_index("id")).data()
        parameter = self.tree_view_form.db_map.single_parameter(id=parameter_id).one_or_none()
        self.assertEqual(parameter.name, 'combined_mojo')
        self.assertEqual(parameter.relationship_class_id, dog_fish_class_id)
        self.assertIsNone(parameter.object_class_id)

    def test_add_object_parameter_values(self):
        """Test that object parameter values are added to the model.
        """
        # Add dog object class
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        self.tree_view_form.add_object_classes([dog_object_class])
        dog_class_id = dog_object_class.id
        # Add pluto and scooby objects
        pluto = dict(
            class_id=dog_class_id,
            name='pluto',
            description="Mickey's."
        )
        scooby = dict(
            class_id=dog_class_id,
            name='scooby',
            description="Scooby-Dooby-Doo."
        )
        pluto_object = self.tree_view_form.db_map.add_object(**pluto)
        scooby_object = self.tree_view_form.db_map.add_object(**scooby)
        self.tree_view_form.add_objects([pluto_object, scooby_object])
        # Add object parameter definition
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        # Enter object class name
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_cls_name_index)
        view.itemDelegate().setEditorData(editor, obj_cls_name_index)
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, obj_cls_name_index)
        view.itemDelegate().destroyEditor(editor, obj_cls_name_index)
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        editor.setText("breed")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
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
        self.assertEqual(editor.count(), 2)
        self.assertEqual(editor.itemText(0), 'pluto')
        self.assertEqual(editor.itemText(1), 'scooby')
        editor.setCurrentIndex(1)
        view.itemDelegate().setModelData(editor, model, obj_name_index)
        view.itemDelegate().destroyEditor(editor, obj_name_index)
        self.assertEqual(obj_name_index.data(), 'scooby')
        obj_id_index = model.index(0, header_index("object_id"))
        self.assertEqual(obj_id_index.data(), scooby_object.id)
        # Check objet class
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        obj_cls_id_index = model.index(0, header_index("object_class_id"))
        self.assertEqual(obj_cls_id_index.data(), dog_class_id)
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
        self.assertEqual(editor.count(), 1)
        self.assertEqual(editor.itemText(0), 'breed')
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'breed')
        # Check objet class
        obj_cls_name_index = model.index(1, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        obj_cls_id_index = model.index(1, header_index("object_class_id"))
        self.assertEqual(obj_cls_id_index.data(), dog_class_id)
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
        # Check the db
        # First (scooby)
        parameter_id = model.index(0, header_index("parameter_id")).data()
        parameter_value_id = model.index(0, header_index("id")).data()
        parameter_value = self.tree_view_form.db_map.single_parameter_value(id=parameter_value_id).one_or_none()
        self.assertEqual(parameter_value.id, parameter_value_id)
        self.assertEqual(parameter_value.parameter_id, parameter_id)
        self.assertEqual(parameter_value.object_id, scooby_object.id)
        self.assertIsNone(parameter_value.relationship_id)
        # Second (pluto)
        parameter_id = model.index(1, header_index("parameter_id")).data()
        parameter_value_id = model.index(1, header_index("id")).data()
        parameter_value = self.tree_view_form.db_map.single_parameter_value(id=parameter_value_id).one_or_none()
        self.assertEqual(parameter_value.id, parameter_value_id)
        self.assertEqual(parameter_value.parameter_id, parameter_id)
        self.assertEqual(parameter_value.object_id, pluto_object.id)
        self.assertIsNone(parameter_value.relationship_id)

    def test_add_relationship_parameter_values(self):
        """Test that relationship parameter values are added to the model.
        """
        # Add fish and dog object classes
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        fish_object_class = self.tree_view_form.db_map.add_object_class(**fish)
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        self.tree_view_form.add_object_classes([fish_object_class, dog_object_class])
        fish_class_id = fish_object_class.id
        dog_class_id = dog_object_class.id
        # Add nemo, pluto and scooby objects
        nemo = dict(
            class_id=fish_class_id,
            name='nemo',
            description='The lost one.'
        )
        nemo_object = self.tree_view_form.db_map.add_object(**nemo)
        pluto = dict(
            class_id=dog_class_id,
            name='pluto',
            description="Mickey's."
        )
        pluto_object = self.tree_view_form.db_map.add_object(**pluto)
        scooby = dict(
            class_id=dog_class_id,
            name='scooby',
            description="Scooby-Dooby-Doo."
        )
        scooby_object = self.tree_view_form.db_map.add_object(**scooby)
        self.tree_view_form.add_objects([nemo_object, pluto_object, scooby_object])
        # Add fish__dog relationship class
        fish_dog = dict(
            name="fish__dog",
            object_class_id_list=[fish_class_id, dog_class_id]
        )
        fish_dog_relationship_class = self.tree_view_form.db_map.add_wide_relationship_class(**fish_dog)
        self.tree_view_form.add_relationship_classes([fish_dog_relationship_class])
        # Fetch fish__dog
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        nemo_item = fish_item.child(0)
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_fish__dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_fish__dog_index)
        # Add nemo_pluto relationship
        nemo_pluto = dict(
            class_id=fish_dog_relationship_class.id,
            object_id_list=[nemo_object.id, pluto_object.id],
            name='fish__dog_nemo__pluto'
        )
        # Don't add nemo_scooby since that one we want to add 'on the fly'
        nemo_pluto_relationship = self.tree_view_form.db_map.add_wide_relationship(**nemo_pluto)
        self.tree_view_form.add_relationships([nemo_pluto_relationship])
        # Add relationship parameter definition
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header_index = model.horizontal_header_labels().index
        # Enter relationship class name
        rel_cls_name_index = model.index(0, header_index("relationship_class_name"))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), rel_cls_name_index)
        view.itemDelegate().setEditorData(editor, rel_cls_name_index)
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, rel_cls_name_index)
        view.itemDelegate().destroyEditor(editor, rel_cls_name_index)
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        editor.setText("combined_mojo")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
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
        self.assertEqual(editor.count(), 1)
        self.assertEqual(editor.itemText(0), 'combined_mojo')
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'combined_mojo')
        # Check relationship class
        rel_cls_name = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'fish__dog')
        rel_cls_id = model.index(0, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, fish_dog_relationship_class.id)
        obj_cls_name_list_index = model.index(0, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'fish,dog')
        obj_cls_id_list_index = model.index(0, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [fish_class_id, dog_class_id])
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
        self.assertEqual(editor.count(), 1)
        self.assertEqual(editor.itemText(0), 'combined_mojo')
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'combined_mojo')
        # Check relationship class
        rel_cls_name = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'fish__dog')
        rel_cls_id = model.index(1, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, fish_dog_relationship_class.id)
        obj_cls_name_list_index = model.index(1, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'fish,dog')
        obj_cls_id_list_index = model.index(1, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [fish_class_id, dog_class_id])
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
        # Check the db
        # First (nemo_pluto)
        parameter_id = model.index(0, header_index("parameter_id")).data()
        parameter_value_id = model.index(0, header_index("id")).data()
        parameter_value = self.tree_view_form.db_map.single_parameter_value(id=parameter_value_id).one_or_none()
        self.assertEqual(parameter_value.id, parameter_value_id)
        self.assertEqual(parameter_value.parameter_id, parameter_id)
        self.assertEqual(parameter_value.relationship_id, nemo_pluto_relationship.id)
        self.assertIsNone(parameter_value.object_id)
        # Second (nemo_scooby)
        nemo_scooby_relationship_id = model.index(1, header_index("relationship_id")).data()
        nemo_scooby_relationship = self.tree_view_form.db_map.single_wide_relationship(
            id=nemo_scooby_relationship_id).one_or_none()
        split_obj_id_list = [int(x) for x in nemo_scooby_relationship.object_id_list.split(',')]
        self.assertEqual(split_obj_id_list, [nemo_object.id, scooby_object.id])
        self.assertEqual(nemo_scooby_relationship.object_name_list, 'nemo,scooby')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        parameter_value_id = model.index(1, header_index("id")).data()
        parameter_value = self.tree_view_form.db_map.single_parameter_value(id=parameter_value_id).one_or_none()
        self.assertEqual(parameter_value.id, parameter_value_id)
        self.assertEqual(parameter_value.parameter_id, parameter_id)
        self.assertEqual(parameter_value.relationship_id, nemo_scooby_relationship_id)
        self.assertIsNone(parameter_value.object_id)
        # Last, check that relationship is in object tree
        nemo_scooby_item = nemo_fish_dog_item.child(1)
        nemo_scooby_item_type = nemo_scooby_item.data(Qt.UserRole)
        nemo_scooby_item_name = nemo_scooby_item.data(Qt.UserRole + 1)['name']
        nemo_scooby_item_class_id = nemo_scooby_item.data(Qt.UserRole + 1)['class_id']
        nemo_scooby_item_object_id_list = nemo_scooby_item.data(Qt.UserRole + 1)['object_id_list']
        nemo_scooby_item_object_name_list = nemo_scooby_item.data(Qt.UserRole + 1)['object_name_list']
        self.assertEqual(nemo_scooby_item_type, "relationship")
        self.assertEqual(nemo_scooby_item_class_id, fish_dog_relationship_class.id)
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item_object_id_list.split(",")]
        self.assertEqual(split_scooby_nemo_object_id_list, [nemo_object.id, scooby_object.id])
        self.assertEqual(nemo_scooby_item_object_name_list, "nemo,scooby")

    @unittest.skip("TODO")
    def test_paste_add_object_parameter_definitions(self):
        """Test that data is pasted onto the view and object parameter definitions are added to the model.
        """
        self.fail()

    def test_paste_add_object_parameter_values(self):
        """Test that data is pasted onto the view and object parameter values are added to the model.
        """
        # Add dog object class
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        self.tree_view_form.add_object_classes([dog_object_class])
        dog_class_id = dog_object_class.id
        # Add pluto and scooby objects
        pluto = dict(
            class_id=dog_class_id,
            name='pluto',
            description="Mickey's."
        )
        scooby = dict(
            class_id=dog_class_id,
            name='scooby',
            description="Scooby-Dooby-Doo."
        )
        brian = dict(
            class_id=dog_class_id,
            name='brian',
            description="Brian Griffin."
        )
        pluto_object = self.tree_view_form.db_map.add_object(**pluto)
        scooby_object = self.tree_view_form.db_map.add_object(**scooby)
        brian_object = self.tree_view_form.db_map.add_object(**brian)
        self.tree_view_form.add_objects([pluto_object, scooby_object, brian_object])
        # Add object parameter definition
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        # Enter object class name
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_cls_name_index)
        view.itemDelegate().setEditorData(editor, obj_cls_name_index)
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, obj_cls_name_index)
        view.itemDelegate().destroyEditor(editor, obj_cls_name_index)
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        editor.setText("breed")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        breed_parameter_id = model.index(0, header_index('id')).data()
        # Paste data
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
        clipboard_text = "pluto\tbreed\t\tbloodhound\nscooby\tbreed\t\tgreat dane\nbrian\tbreed\t\tlabrador\n"
        QApplication.clipboard().setText(clipboard_text)
        obj_name_index = model.index(0, header_index('object_name'))
        view.setCurrentIndex(obj_name_index)
        view.paste()
        # Check model
        for row in range(3):
            # Object class name and id
            obj_cls_name = model.index(row, header_index("object_class_name")).data()
            self.assertEqual(obj_cls_name, 'dog')
            obj_cls_id = model.index(row, header_index("object_class_id")).data()
            self.assertEqual(obj_cls_id, dog_class_id)
            # Parameter name and id
            parameter_name = model.index(row, header_index("parameter_name")).data()
            self.assertEqual(parameter_name, 'breed')
            parameter_id = model.index(row, header_index("parameter_id")).data()
            self.assertEqual(parameter_id, breed_parameter_id)
        # Object name and id
        obj_name = model.index(0, header_index("object_name")).data()
        self.assertEqual(obj_name, 'pluto')
        obj_id = model.index(0, header_index("object_id")).data()
        self.assertEqual(obj_id, pluto_object.id)
        obj_name = model.index(1, header_index("object_name")).data()
        self.assertEqual(obj_name, 'scooby')
        obj_id = model.index(1, header_index("object_id")).data()
        self.assertEqual(obj_id, scooby_object.id)
        obj_name = model.index(2, header_index("object_name")).data()
        self.assertEqual(obj_name, 'brian')
        obj_id = model.index(2, header_index("object_id")).data()
        self.assertEqual(obj_id, brian_object.id)
        # Parameter value and id
        value = model.index(0, header_index("value")).data()
        self.assertEqual(value, 'bloodhound')
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, breed_parameter_id)
        value = model.index(1, header_index("value")).data()
        self.assertEqual(value, 'great dane')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, breed_parameter_id)
        value = model.index(2, header_index("value")).data()
        self.assertEqual(value, 'labrador')
        parameter_id = model.index(2, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, breed_parameter_id)
        # Check db
        pluto_breed, scooby_breed, brian_breed = self.tree_view_form.db_map.parameter_value_list().all()
        # Object id
        self.assertEqual(pluto_breed.object_id, pluto_object.id)
        self.assertEqual(scooby_breed.object_id, scooby_object.id)
        self.assertEqual(brian_breed.object_id, brian_object.id)
        # Relationship id (None)
        self.assertIsNone(pluto_breed.relationship_id)
        self.assertIsNone(scooby_breed.relationship_id)
        self.assertIsNone(brian_breed.relationship_id)
        # Parameter id
        self.assertEqual(pluto_breed.parameter_id, breed_parameter_id)
        self.assertEqual(scooby_breed.parameter_id, breed_parameter_id)
        self.assertEqual(brian_breed.parameter_id, breed_parameter_id)
        # Value
        self.assertEqual(pluto_breed.value, 'bloodhound')
        self.assertEqual(scooby_breed.value, 'great dane')
        self.assertEqual(brian_breed.value, 'labrador')

    @unittest.skip("TODO")
    def test_paste_add_relationship_parameter_definitions(self):
        """Test that data is pasted onto the view and relationship parameter definitions are added to the model.
        """
        self.fail()

    @unittest.skip("TODO")
    def test_paste_add_relationship_parameter_values(self):
        """Test that data is pasted onto the view and relationship parameter values are added to the model.
        """
        self.fail()

    def test_set_object_parameter_definition_defaults(self):
        """Test that defaults are set in object parameter definition models according the object tree selection.
        """
        # Add fish and dog object classes
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        object_classes = self.tree_view_form.db_map.add_object_classes(fish, dog)
        self.tree_view_form.add_object_classes(object_classes)
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

    def add_minimal_dataset(self):
        """Add a minimal amount of items to test editing and removal."""
        # Add fish and dog object classes
        fish = dict(
            name='fish',
            description='A fish.',
            display_order=1
        )
        dog = dict(
            name='dog',
            description='A dog.',
            display_order=3
        )
        fish_object_class = self.tree_view_form.db_map.add_object_class(**fish)
        dog_object_class = self.tree_view_form.db_map.add_object_class(**dog)
        fish_class_id = fish_object_class.id
        dog_class_id = dog_object_class.id
        # Add nemo, pluto and scooby objects
        nemo = dict(
            class_id=fish_class_id,
            name='nemo',
            description='The lost one.'
        )
        pluto = dict(
            class_id=dog_class_id,
            name='pluto',
            description="Mickey's."
        )
        scooby = dict(
            class_id=dog_class_id,
            name='scooby',
            description="Scooby-Dooby-Doo."
        )
        nemo_object = self.tree_view_form.db_map.add_object(**nemo)
        pluto_object = self.tree_view_form.db_map.add_object(**pluto)
        scooby_object = self.tree_view_form.db_map.add_object(**scooby)
        # Add fish__dog and dog__fish relationship classes
        fish_dog = dict(
            name="fish__dog",
            object_class_id_list=[fish_class_id, dog_class_id]
        )
        dog_fish = dict(
            name="dog__fish",
            object_class_id_list=[dog_class_id, fish_class_id]
        )
        fish_dog_relationship_class = self.tree_view_form.db_map.add_wide_relationship_class(**fish_dog)
        dog_fish_relationship_class = self.tree_view_form.db_map.add_wide_relationship_class(**dog_fish)
        # Add pluto_nemo, nemo_pluto and nemo_scooby relationships
        pluto_nemo = dict(
            class_id=dog_fish_relationship_class.id,
            object_id_list=[pluto_object.id, nemo_object.id],
            name='dog__fish_pluto__nemo'
        )
        nemo_pluto = dict(
            class_id=fish_dog_relationship_class.id,
            object_id_list=[nemo_object.id, pluto_object.id],
            name='fish__dog_nemo__pluto'
        )
        nemo_scooby = dict(
            class_id=fish_dog_relationship_class.id,
            object_id_list=[nemo_object.id, scooby_object.id],
            name='fish__dog_nemo__scooby'
        )
        pluto_nemo_relationship = self.tree_view_form.db_map.add_wide_relationship(**pluto_nemo)
        nemo_pluto_relationship = self.tree_view_form.db_map.add_wide_relationship(**nemo_pluto)
        nemo_scooby_relationship = self.tree_view_form.db_map.add_wide_relationship(**nemo_scooby)
        # Add water and breed object parameter definitions
        water = dict(object_class_id=fish_class_id, name='water')
        breed = dict(object_class_id=dog_class_id, name='breed')
        water_parameter = self.tree_view_form.db_map.add_parameter(**water)
        breed_parameter = self.tree_view_form.db_map.add_parameter(**breed)
        # Add relative speed and combined mojo relationship parameter definitions.
        relative_speed = dict(relationship_class_id=fish_dog_relationship_class.id, name='relative_speed')
        combined_mojo = dict(relationship_class_id=dog_fish_relationship_class.id, name='combined_mojo')
        relative_speed_parameter = self.tree_view_form.db_map.add_parameter(**relative_speed)
        combined_mojo_parameter = self.tree_view_form.db_map.add_parameter(**combined_mojo)
        # Add parameter values
        nemo_water = dict(
            object_id=nemo_object.id,
            parameter_id=water_parameter.id,
            value='salt'
        )
        pluto_breed = dict(
            object_id=pluto_object.id,
            parameter_id=breed_parameter.id,
            value='bloodhound'
        )
        scooby_breed = dict(
            object_id=scooby_object.id,
            parameter_id=breed_parameter.id,
            value='great dane'
        )
        nemo_pluto_relative_speed = dict(
            relationship_id=nemo_pluto_relationship.id,
            parameter_id=relative_speed_parameter.id,
            value=-1
        )
        nemo_scooby_relative_speed = dict(
            relationship_id=nemo_scooby_relationship.id,
            parameter_id=relative_speed_parameter.id,
            value=5
        )
        pluto_nemo_combined_mojo = dict(
            relationship_id=pluto_nemo_relationship.id,
            parameter_id=combined_mojo_parameter.id,
            value=100
        )
        self.tree_view_form.db_map.add_parameter_values(
            nemo_water, pluto_breed, scooby_breed,
            nemo_pluto_relative_speed, nemo_scooby_relative_speed, pluto_nemo_combined_mojo)
        self.tree_view_form.init_models()
        return fish_object_class.id, dog_object_class.id, nemo_object.id, pluto_object.id, scooby_object.id, \
            dog_fish_relationship_class.id, fish_dog_relationship_class.id, \
            pluto_nemo_relationship.id, nemo_pluto_relationship.id, nemo_scooby_relationship.id, \
            combined_mojo_parameter.id, relative_speed_parameter.id

    def test_update_object_classes(self):
        """Test that object classes are updated on all model/views.
        """
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
        upd_fish_obj_cls = dict(
            id=fish_object_class_id,
            name='octopus'
        )
        upd_dog_obj_cls = dict(
            id=dog_object_class_id,
            name='god'
        )
        updated_object_classes = self.tree_view_form.db_map.update_object_classes(upd_fish_obj_cls, upd_dog_obj_cls)
        self.tree_view_form.update_object_classes(updated_object_classes)
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
        # Fetch object classes
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        # Update objects
        upd_nemo_obj = dict(
            id=nemo_object_id,
            name='dory'
        )
        upd_pluto_obj = dict(
            id=pluto_object_id,
            name='rascal'
        )
        updated_objects = self.tree_view_form.db_map.update_objects(upd_nemo_obj, upd_pluto_obj)
        self.tree_view_form.update_objects(updated_objects)
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        upd_dog_fish_relationship_cls = dict(
            id=dog_fish_relationship_class_id,
            name='god__octopus'
        )
        upd_fish_dog_relationship_cls = dict(
            id=fish_dog_relationship_class_id,
            name='octopus__god'
        )
        updated_relationship_classes = self.tree_view_form.db_map.update_wide_relationship_classes(
            upd_dog_fish_relationship_cls, upd_fish_dog_relationship_cls)
        self.tree_view_form.update_relationship_classes(updated_relationship_classes)
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        upd_pluto_nemo_relationship = dict(
            id=pluto_nemo_relationship_id,
            name='dog__fish_scooby__nemo',
            object_id_list=[scooby_object_id, nemo_object_id]
        )
        updated_relationships = self.tree_view_form.db_map.update_wide_relationships(upd_pluto_nemo_relationship)
        self.tree_view_form.update_relationships(updated_relationships)
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
        # Update parameter value
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_value_index = model.index(0, header_index("value"))
        self.assertEqual(parameter_value_index.data(), '-1')
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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
        fish_object_class_id, dog_object_class_id, nemo_object_id, pluto_object_id, scooby_object_id, \
            dog_fish_relationship_class_id, fish_dog_relationship_class_id, \
            pluto_nemo_relationship_id, nemo_pluto_relationship_id, nemo_scooby_relationship_id, \
            combined_mojo_parameter_id, relative_speed_parameter_id = self.add_minimal_dataset()
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


if __name__ == '__main__':
    unittest.main()
