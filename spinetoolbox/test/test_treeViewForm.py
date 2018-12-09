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
from widgets.data_store_widgets import TreeViewForm, GraphViewForm
from spinedatabase_api import DiffDatabaseMapping, create_new_spine_database
from widgets.custom_editors import CustomComboEditor, CustomLineEditor, ObjectNameListEditor


class TestDataStoreForm(unittest.TestCase):

    app = QApplication()  # must create a QApplication before creating QWidgets

    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def setUp(self):
        """Overridden method. Runs before each test. Makes instances of TreeViewForm and GraphViewForm classes.
        """
        # # Set logging level to Error to silence "Logging level: All messages" print
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
            self.graph_view_form = GraphViewForm(mock_data_store, db_map, "mock_db")
            logging.disable(level=logging.NOTSET)  # Enable logging

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.tree_view_form.close()
        self.graph_view_form.close()
        try:
            os.remove('mock_db.sqlite')
        except OSError:
            pass

    # @unittest.skip("DONE")
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

    # @unittest.skip("DONE")
    def test_add_objects(self):
        """Test that objects are added to the object tree model.
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

    # @unittest.skip("DONE")
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
        # Add nemo object before adding the relationships
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
        # Add pluto object after adding the relationships
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

    # @unittest.skip("DONE")
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
        self.assertEqual(pluto_nemo_item2_type, "relationship", "Pluto_nemo item2 type is not 'relationship'")
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
        self.assertEqual(nemo_pluto_item1_type, "relationship", "Nemo_pluto item1 type is not 'relationship'")
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
        self.assertEqual(nemo_pluto_item2_type, "relationship", "Nemo_pluto item2 type is not 'relationship'")
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
        self.assertEqual(nemo_scooby_item1_type, "relationship", "Nemo_scooby item1 type is not 'relationship'")
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
        self.assertEqual(nemo_scooby_item2_type, "relationship", "Nemo_scooby item2 type is not 'relationship'")
        self.assertEqual(nemo_scooby_item2_name, 'fish__dog_nemo__scooby')
        self.assertEqual(nemo_scooby_item2_class_id, fish_dog_relationship_class.id)
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item2_object_id_list.split(",")]
        self.assertEqual(split_scooby_nemo_object_id_list, [nemo_object.id, scooby_object.id])
        self.assertEqual(nemo_scooby_item2_object_name_list, "nemo,scooby")

    # @unittest.skip("DONE")
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

    # @unittest.skip("DONE")
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

    # @unittest.skip("DONE")
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
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
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

    # @unittest.skip("DONE")
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
        # Add nemo and scooby objects
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
        self.tree_view_form.add_objects([nemo_object, scooby_object])
        # Add fish__dog relationship class
        fish_dog = dict(
            name="fish__dog",
            object_class_id_list=[fish_class_id, dog_class_id]
        )
        fish_dog_relationship_class = self.tree_view_form.db_map.add_wide_relationship_class(**fish_dog)
        self.tree_view_form.add_relationship_classes([fish_dog_relationship_class])
        # Add nemo_pluto and nemo_scooby relationships
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
        nemo_pluto_relationship = self.tree_view_form.db_map.add_wide_relationship(**nemo_pluto)
        nemo_scooby_relationship = self.tree_view_form.db_map.add_wide_relationship(**nemo_scooby)
        self.tree_view_form.add_relationships([nemo_pluto_relationship, nemo_scooby_relationship])
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
        # Add relationship parameter value
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
        # Check the db
        parameter_id = model.index(0, header_index("parameter_id")).data()
        parameter_value_id = model.index(0, header_index("id")).data()
        parameter_value = self.tree_view_form.db_map.single_parameter_value(id=parameter_value_id).one_or_none()
        self.assertEqual(parameter_value.id, parameter_value_id)
        self.assertEqual(parameter_value.parameter_id, parameter_id)
        self.assertEqual(parameter_value.relationship_id, nemo_pluto_relationship.id)
        self.assertIsNone(parameter_value.object_id)

    # @unittest.skip("DONE")
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

    # @unittest.skip("DONE")
    def test_set_object_parameter_definition_defaults(self):
        """Test that defaults are set in parameter definition models according the object tree selection.
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
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_tree_index, QItemSelectionModel.Deselect)
        self.tree_view_form.ui.treeView_object.selectionModel().select(dog_tree_index, QItemSelectionModel.Select)
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        # Clear object tree selection and select root
        self.tree_view_form.ui.treeView_object.selectionModel().clearSelection()
        root_tree_index = self.tree_view_form.object_tree_model.indexFromItem(root_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(root_tree_index, QItemSelectionModel.Select)
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertIsNone(obj_cls_name_index.data())


if __name__ == '__main__':
    unittest.main()
