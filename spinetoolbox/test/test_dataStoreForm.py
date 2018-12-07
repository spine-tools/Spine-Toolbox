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

:author: M. Marin (VTT)
:date:   6.12.2018
"""

import unittest
import os
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
from widgets.data_store_widgets import TreeViewForm, GraphViewForm
from spinedatabase_api import DiffDatabaseMapping, create_new_spine_database


class TestDataStoreForm(unittest.TestCase):

    app = QApplication()  # QApplication must be instantiated here unless you want a segmentation fault

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
            db_map = DiffDatabaseMapping(db_url, "Spine-Toolbox-test-suite")
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
        self.assertTrue(fish_type == "object_class", "Fish type is not 'object_class'")
        self.assertTrue(fish_name == "fish", "Fish name is not 'fish'")
        self.assertTrue(dog_type == "object_class", "Dog type is not 'object_class'")
        self.assertTrue(dog_name == "dog", "Dog name is not 'dog'")
        self.assertTrue(cat_type == "object_class", "Cat type is not 'object_class'")
        self.assertTrue(cat_name == "cat", "Cat name is not 'cat'")
        self.assertTrue(root_item.rowCount() == 3, "Row count is not 3")

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
        self.assertTrue(nemo_type == "object", "Nemo type is not 'object'")
        self.assertTrue(nemo_class_id == fish_class_id, "Nemo class_id is not {}".format(fish_class_id))
        self.assertTrue(nemo_id == 1, "Nemo id is not 1")
        self.assertTrue(nemo_name == "nemo", "Nemo name is not 'nemo'")
        self.assertTrue(dory_type == "object", "Dory type is not 'object'")
        self.assertTrue(dory_class_id == fish_class_id, "Dory class_id is not {}".format(fish_class_id))
        self.assertTrue(dory_id == 2, "Dory id is not 2")
        self.assertTrue(dory_name == "dory", "Dory name is not 'dory'")
        self.assertTrue(fish_item.rowCount() == 2, "Fish count is not 2")
        self.assertTrue(pluto_type == "object", "Pluto type is not 'object'")
        self.assertTrue(pluto_class_id == dog_class_id, "Pluto class_id is not {}".format(dog_class_id))
        self.assertTrue(pluto_id == 3, "Pluto id is not 3")
        self.assertTrue(pluto_name == "pluto", "Pluto name is not 'pluto'")
        self.assertTrue(scooby_type == "object", "Pluto type is not 'object'")
        self.assertTrue(scooby_class_id == dog_class_id, "Scooby class_id is not {}".format(dog_class_id))
        self.assertTrue(scooby_id == 4, "Scooby id is not 4")
        self.assertTrue(scooby_name == "scooby", "Scooby name is not 'scooby'")
        self.assertTrue(fish_item.rowCount() == 2, "Dog count is not 2")

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
        self.assertTrue(can_nemo_fetch_more is False, "Nemo can fetch more.")
        # Check that pluto *can* fetch more (since it wasn't there when adding the relationship class)
        dog_item = root_item.child(1)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        can_pluto_fetch_more = self.tree_view_form.object_tree_model.canFetchMore(pluto_index)
        self.assertTrue(can_pluto_fetch_more is True, "Pluto can't fetch more.")
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        # Check relationship class items are good
        # The first one under nemo
        nemo_dog_fish_item = nemo_item.child(0)
        nemo_dog_fish_type = nemo_dog_fish_item.data(Qt.UserRole)
        nemo_dog_fish_name = nemo_dog_fish_item.data(Qt.UserRole + 1)['name']
        nemo_dog_fish_object_class_id_list = nemo_dog_fish_item.data(Qt.UserRole + 1)['object_class_id_list']
        nemo_dog_fish_object_class_name_list = nemo_dog_fish_item.data(Qt.UserRole + 1)['object_class_name_list']
        self.assertTrue(nemo_dog_fish_type == "relationship_class", "Nemo_dog_fish type is not 'relationship_class'")
        self.assertTrue(nemo_dog_fish_name == "dog__fish", "Nemo_dog_fish name is not 'dog__fish'")
        split_nemo_dog_fish_object_class_id_list = [int(x) for x in nemo_dog_fish_object_class_id_list.split(",")]
        self.assertTrue(split_nemo_dog_fish_object_class_id_list == [dog_class_id, fish_class_id],
                        "Nemo_dog_fish object_class_id_list is not {}".format([dog_class_id, fish_class_id]))
        self.assertTrue(nemo_dog_fish_object_class_name_list == "dog,fish",
                        "Nemo_dog_fish name is not 'dog,fish'")
        self.assertTrue(nemo_item.rowCount() == 2, "Nemo_dog_fish count is not 2")
        # The second one under pluto
        pluto_fish_dog_item = pluto_item.child(1)
        pluto_fish_dog_type = pluto_fish_dog_item.data(Qt.UserRole)
        pluto_fish_dog_name = pluto_fish_dog_item.data(Qt.UserRole + 1)['name']
        pluto_fish_dog_object_class_id_list = pluto_fish_dog_item.data(Qt.UserRole + 1)['object_class_id_list']
        pluto_fish_dog_object_class_name_list = pluto_fish_dog_item.data(Qt.UserRole + 1)['object_class_name_list']
        self.assertTrue(pluto_fish_dog_type == "relationship_class", "Pluto_fish_dog type is not 'relationship_class'")
        self.assertTrue(pluto_fish_dog_name == "fish__dog", "Pluto_fish_dog name is not 'fish__dog'")
        split_pluto_fish_dog_object_class_id_list = [int(x) for x in pluto_fish_dog_object_class_id_list.split(",")]
        self.assertTrue(split_pluto_fish_dog_object_class_id_list == [fish_class_id, dog_class_id],
                        "Pluto_fish_dog object_class_id_list is not {}".format([fish_class_id, dog_class_id]))
        self.assertTrue(pluto_fish_dog_object_class_name_list == "fish,dog",
                        "Pluto_fish_dog name is not 'fish,dog'")
        self.assertTrue(pluto_item.rowCount() == 2, "Pluto_fish_dog count is not 2")

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
        self.assertTrue(nemo_dog_fish_item.rowCount() == 1, "nemo_dog_fish_item count is not 1")
        self.assertTrue(nemo_fish_dog_item.rowCount() == 2, "nemo_fish_dog_item count is not 2")
        self.assertTrue(pluto_dog_fish_item.rowCount() == 1, "pluto_dog_fish_item count is not 1")
        self.assertTrue(pluto_fish_dog_item.rowCount() == 1, "pluto_fish_dog_item count is not 1")
        self.assertTrue(scooby_dog_fish_item.rowCount() == 0, "scooby_dog_fish_item count is not 0")
        self.assertTrue(scooby_fish_dog_item.rowCount() == 1, "scooby_fish_dog_item count is not 1")
        # Check relationship items are good
        # pluto_nemo_item1
        pluto_nemo_item1_type = pluto_nemo_item1.data(Qt.UserRole)
        pluto_nemo_item1_name = pluto_nemo_item1.data(Qt.UserRole + 1)['name']
        pluto_nemo_item1_class_id = pluto_nemo_item1.data(Qt.UserRole + 1)['class_id']
        pluto_nemo_item1_object_id_list = pluto_nemo_item1.data(Qt.UserRole + 1)['object_id_list']
        pluto_nemo_item1_object_name_list = pluto_nemo_item1.data(Qt.UserRole + 1)['object_name_list']
        self.assertTrue(pluto_nemo_item1_type == "relationship", "Pluto_nemo item1 type is not 'relationship'")
        self.assertTrue(pluto_nemo_item1_name == 'dog__fish_pluto__nemo',
                        "Pluto_nemo item1 name is not dog__fish_pluto__nemo")
        self.assertTrue(pluto_nemo_item1_class_id == dog_fish_relationship_class.id,
                        "Pluto_nemo item1 class_id is not {}".format(dog_fish_relationship_class.id))
        split_pluto_nemo_object_id_list = [int(x) for x in pluto_nemo_item1_object_id_list.split(",")]
        self.assertTrue(split_pluto_nemo_object_id_list == [pluto_object.id, nemo_object.id],
                        "Pluto_nemo item1 object_id_list is not {}".format([pluto_object.id, nemo_object.id]))
        self.assertTrue(pluto_nemo_item1_object_name_list == "pluto,nemo",
                        "Pluto_nemo item1 object_name_list is not 'pluto,nemo'")
        # pluto_nemo_item2
        pluto_nemo_item2_type = pluto_nemo_item2.data(Qt.UserRole)
        pluto_nemo_item2_name = pluto_nemo_item2.data(Qt.UserRole + 1)['name']
        pluto_nemo_item2_class_id = pluto_nemo_item2.data(Qt.UserRole + 1)['class_id']
        pluto_nemo_item2_object_id_list = pluto_nemo_item2.data(Qt.UserRole + 1)['object_id_list']
        pluto_nemo_item2_object_name_list = pluto_nemo_item2.data(Qt.UserRole + 1)['object_name_list']
        self.assertTrue(pluto_nemo_item2_type == "relationship", "Pluto_nemo item2 type is not 'relationship'")
        self.assertTrue(pluto_nemo_item2_name == 'dog__fish_pluto__nemo',
                        "Pluto_nemo item2 name is not dog__fish_pluto__nemo")
        self.assertTrue(pluto_nemo_item2_class_id == dog_fish_relationship_class.id,
                        "Pluto_nemo item2 class_id is not {}".format(dog_fish_relationship_class.id))
        split_pluto_nemo_object_id_list = [int(x) for x in pluto_nemo_item2_object_id_list.split(",")]
        self.assertTrue(split_pluto_nemo_object_id_list == [pluto_object.id, nemo_object.id],
                        "Pluto_nemo item2 object_id_list is not {}".format([pluto_object.id, nemo_object.id]))
        self.assertTrue(pluto_nemo_item2_object_name_list == "pluto,nemo",
                        "Pluto_nemo item2 object_name_list is not 'pluto,nemo'")
        # nemo_pluto_item1
        nemo_pluto_item1_type = nemo_pluto_item1.data(Qt.UserRole)
        nemo_pluto_item1_name = nemo_pluto_item1.data(Qt.UserRole + 1)['name']
        nemo_pluto_item1_class_id = nemo_pluto_item1.data(Qt.UserRole + 1)['class_id']
        nemo_pluto_item1_object_id_list = nemo_pluto_item1.data(Qt.UserRole + 1)['object_id_list']
        nemo_pluto_item1_object_name_list = nemo_pluto_item1.data(Qt.UserRole + 1)['object_name_list']
        self.assertTrue(nemo_pluto_item1_type == "relationship", "Nemo_pluto item1 type is not 'relationship'")
        self.assertTrue(nemo_pluto_item1_name == 'fish__dog_nemo__pluto',
                        "Nemo_pluto item1 name is not fish__dog_nemo__pluto")
        self.assertTrue(nemo_pluto_item1_class_id == fish_dog_relationship_class.id,
                        "Nemo_pluto item1 class_id is not {}".format(fish_dog_relationship_class.id))
        split_pluto_nemo_object_id_list = [int(x) for x in nemo_pluto_item1_object_id_list.split(",")]
        self.assertTrue(split_pluto_nemo_object_id_list == [nemo_object.id, pluto_object.id],
                        "Nemo_pluto item1 object_id_list is not {}".format([nemo_object.id, pluto_object.id]))
        self.assertTrue(nemo_pluto_item1_object_name_list == "nemo,pluto",
                        "Nemo_pluto item1 object_name_list is not 'nemo,pluto'")
        # nemo_pluto_item2
        nemo_pluto_item2_type = nemo_pluto_item2.data(Qt.UserRole)
        nemo_pluto_item2_name = nemo_pluto_item2.data(Qt.UserRole + 1)['name']
        nemo_pluto_item2_class_id = nemo_pluto_item2.data(Qt.UserRole + 1)['class_id']
        nemo_pluto_item2_object_id_list = nemo_pluto_item2.data(Qt.UserRole + 1)['object_id_list']
        nemo_pluto_item2_object_name_list = nemo_pluto_item2.data(Qt.UserRole + 1)['object_name_list']
        self.assertTrue(nemo_pluto_item2_type == "relationship", "Nemo_pluto item2 type is not 'relationship'")
        self.assertTrue(nemo_pluto_item2_name == 'fish__dog_nemo__pluto',
                        "Nemo_pluto item2 name is not fish__dog_nemo__pluto")
        self.assertTrue(nemo_pluto_item2_class_id == fish_dog_relationship_class.id,
                        "Nemo_pluto item2 class_id is not {}".format(fish_dog_relationship_class.id))
        split_pluto_nemo_object_id_list = [int(x) for x in nemo_pluto_item2_object_id_list.split(",")]
        self.assertTrue(split_pluto_nemo_object_id_list == [nemo_object.id, pluto_object.id],
                        "Nemo_pluto item2 object_id_list is not {}".format([nemo_object.id, pluto_object.id]))
        self.assertTrue(nemo_pluto_item2_object_name_list == "nemo,pluto",
                        "Nemo_pluto item2 object_name_list is not 'nemo,pluto'")
        # nemo_scooby_item1
        nemo_scooby_item1_type = nemo_scooby_item1.data(Qt.UserRole)
        nemo_scooby_item1_name = nemo_scooby_item1.data(Qt.UserRole + 1)['name']
        nemo_scooby_item1_class_id = nemo_scooby_item1.data(Qt.UserRole + 1)['class_id']
        nemo_scooby_item1_object_id_list = nemo_scooby_item1.data(Qt.UserRole + 1)['object_id_list']
        nemo_scooby_item1_object_name_list = nemo_scooby_item1.data(Qt.UserRole + 1)['object_name_list']
        self.assertTrue(nemo_scooby_item1_type == "relationship", "Nemo_scooby item1 type is not 'relationship'")
        self.assertTrue(nemo_scooby_item1_name == 'fish__dog_nemo__scooby',
                        "Nemo_scooby item1 name is not fish__dog_nemo__scooby")
        self.assertTrue(nemo_scooby_item1_class_id == fish_dog_relationship_class.id,
                        "Nemo_scooby item1 class_id is not {}".format(fish_dog_relationship_class.id))
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item1_object_id_list.split(",")]
        self.assertTrue(split_scooby_nemo_object_id_list == [nemo_object.id, scooby_object.id],
                        "Nemo_scooby item1 object_id_list is not {}".format([nemo_object.id, scooby_object.id]))
        self.assertTrue(nemo_scooby_item1_object_name_list == "nemo,scooby",
                        "Nemo_scooby item1 object_name_list is not 'nemo,scooby'")
        # nemo_scooby_item2
        nemo_scooby_item2_type = nemo_scooby_item2.data(Qt.UserRole)
        nemo_scooby_item2_name = nemo_scooby_item2.data(Qt.UserRole + 1)['name']
        nemo_scooby_item2_class_id = nemo_scooby_item2.data(Qt.UserRole + 1)['class_id']
        nemo_scooby_item2_object_id_list = nemo_scooby_item2.data(Qt.UserRole + 1)['object_id_list']
        nemo_scooby_item2_object_name_list = nemo_scooby_item2.data(Qt.UserRole + 1)['object_name_list']
        self.assertTrue(nemo_scooby_item2_type == "relationship", "Nemo_scooby item2 type is not 'relationship'")
        self.assertTrue(nemo_scooby_item2_name == 'fish__dog_nemo__scooby',
                        "Nemo_scooby item2 name is not fish__dog_nemo__scooby")
        self.assertTrue(nemo_scooby_item2_class_id == fish_dog_relationship_class.id,
                        "Nemo_scooby item2 class_id is not {}".format(fish_dog_relationship_class.id))
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item2_object_id_list.split(",")]
        self.assertTrue(split_scooby_nemo_object_id_list == [nemo_object.id, scooby_object.id],
                        "Nemo_scooby item2 object_id_list is not {}".format([nemo_object.id, scooby_object.id]))
        self.assertTrue(nemo_scooby_item2_object_name_list == "nemo,scooby",
                        "Nemo_scooby item2 object_name_list is not 'nemo,scooby'")

if __name__ == '__main__':
    unittest.main()
