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
from PySide2.QtWidgets import QApplication, QWidget, QStyleOptionViewItem
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
        header_index = model.header.index
        # Enter object class name
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        self.assertTrue(obj_cls_name_index.data() is None,
                        "Object class name is '{}' rather than None".format(obj_cls_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_cls_name_index)
        view.itemDelegate().setEditorData(editor, obj_cls_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor), "Editor is not a 'CustomComboEditor'")
        self.assertTrue(editor.count() == 2, "Editor count is '{}' rather than 2".format(editor.count()))
        self.assertTrue(editor.itemText(0) == 'fish', "Item 0 is '{}' rather than 'fish'".format(editor.itemText(0)))
        self.assertTrue(editor.itemText(1) == 'dog', "Item 1 is '{}' rather than 'dog'".format(editor.itemText(1)))
        editor.setCurrentIndex(1)
        view.itemDelegate().setModelData(editor, model, obj_cls_name_index)
        view.itemDelegate().destroyEditor(editor, obj_cls_name_index)
        self.assertTrue(obj_cls_name_index.data() == 'dog',
                        "Object class name is '{}' rather than 'dog'".format(obj_cls_name_index.data()))
        obj_cls_id_index = model.index(0, header_index("object_class_id"))
        self.assertTrue(obj_cls_id_index.data() == dog_class_id,
                        "Object class id is '{}' rather than '{}'".format(obj_cls_id_index.data(), dog_class_id))
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertTrue(parameter_name_index.data() is None,
                        "Parameter name is '{}' rather than None".format(parameter_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertTrue(editor.text() is "", "Editor text is '{}' rather than ''".format(editor.text()))
        editor.setText("breed")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertTrue(parameter_name_index.data() == 'breed',
                        "Parameter name is '{}' rather than 'breed'".format(parameter_name_index.data()))
        # Check the db
        parameter_id = model.index(0, header_index("id")).data()
        parameter = self.tree_view_form.db_map.single_parameter(id=parameter_id).one_or_none()
        self.assertTrue(parameter.name == 'breed',
                        "Parameter name is '{}' rather than 'breed'".format(parameter.name))
        self.assertTrue(parameter.object_class_id == dog_class_id,
                        "Parameter object class id is '{}' rather than '{}'".\
                            format(parameter.object_class_id, dog_class_id))
        self.assertTrue(parameter.relationship_class_id is None,
                        "Parameter relationship class id is '{}' rather than None".\
                            format(parameter.relationship_class_id))

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
        header_index = model.header.index
        # Enter relationship class name
        rel_cls_name_index = model.index(0, header_index("relationship_class_name"))
        self.assertTrue(rel_cls_name_index.data() is None,
                        "Relationship class name is '{}' rather than None".format(rel_cls_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), rel_cls_name_index)
        view.itemDelegate().setEditorData(editor, rel_cls_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor), "Editor is not a 'CustomComboEditor'")
        self.assertTrue(editor.count() == 2, "Editor count is '{}' rather than 2".format(editor.count()))
        self.assertTrue(editor.itemText(0) == 'fish__dog',
                        "Item 0 is '{}' rather than 'fish__dog'".format(editor.itemText(0)))
        self.assertTrue(editor.itemText(1) == 'dog__fish',
                        "Item 1 is '{}' rather than 'dog__fish'".format(editor.itemText(1)))
        editor.setCurrentIndex(1)
        view.itemDelegate().setModelData(editor, model, rel_cls_name_index)
        view.itemDelegate().destroyEditor(editor, rel_cls_name_index)
        self.assertTrue(rel_cls_name_index.data() == 'dog__fish',
                        "Relationship class name is '{}' rather than 'dog__fish'".format(rel_cls_name_index.data()))
        rel_cls_id_index = model.index(0, header_index("relationship_class_id"))
        self.assertTrue(rel_cls_id_index.data() == dog_fish_class_id,
                        "Relationship class id is '{}' rather than '{}'".\
                            format(rel_cls_id_index.data(), dog_fish_class_id))
        obj_cls_name_list_index = model.index(0, header_index("object_class_name_list"))
        self.assertTrue(obj_cls_name_list_index.data() == 'dog,fish',
                        "Object class name list is '{}' rather than 'dog,fish'".format(obj_cls_name_list_index.data()))
        obj_cls_id_list_index = model.index(0, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertTrue(split_obj_cls_id_list == [dog_class_id, fish_class_id],
                        "Object class id list is '{}' rather than '{}'".\
                            format(split_obj_cls_id_list, [dog_class_id, fish_class_id]))
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertTrue(parameter_name_index.data() is None,
                        "Parameter name is '{}' rather than None".format(parameter_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertTrue(editor.text() is "", "Editor text is '{}' rather than ''".format(editor.text()))
        editor.setText("combined_mojo")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertTrue(parameter_name_index.data() == 'combined_mojo',
                        "Parameter name is '{}' rather than 'combined_mojo'".format(parameter_name_index.data()))
        # Check the db
        parameter_id = model.index(0, header_index("id")).data()
        parameter = self.tree_view_form.db_map.single_parameter(id=parameter_id).one_or_none()
        self.assertTrue(parameter.name == 'combined_mojo',
                        "Parameter name is '{}' rather than 'combined_mojo'".format(parameter.name))
        self.assertTrue(parameter.relationship_class_id == dog_fish_class_id,
                        "Parameter relationship class id is '{}' rather than '{}'".\
                            format(parameter.relationship_class_id, dog_fish_class_id))
        self.assertTrue(parameter.object_class_id is None,
                        "Parameter object class id is '{}' rather than None".format(parameter.object_class_id))

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
        header_index = model.header.index
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
        header_index = model.header.index
        # Enter object name
        obj_name_index = model.index(0, header_index("object_name"))
        self.assertTrue(obj_name_index.data() is None,
                        "Object name is '{}' rather than None".format(obj_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_index)
        view.itemDelegate().setEditorData(editor, obj_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor), "Editor is not a 'CustomComboEditor'")
        self.assertTrue(editor.count() == 2, "Editor count is '{}' rather than 2".format(editor.count()))
        self.assertTrue(editor.itemText(0) == 'pluto', "Item 0 is '{}' rather than 'pluto'".format(editor.itemText(0)))
        self.assertTrue(editor.itemText(1) == 'scooby',
                        "Item 1 is '{}' rather than 'scooby'".format(editor.itemText(1)))
        editor.setCurrentIndex(1)
        view.itemDelegate().setModelData(editor, model, obj_name_index)
        view.itemDelegate().destroyEditor(editor, obj_name_index)
        self.assertTrue(obj_name_index.data() == 'scooby',
                        "Object name is '{}' rather than 'scooby'".format(obj_name_index.data()))
        obj_id_index = model.index(0, header_index("object_id"))
        self.assertTrue(obj_id_index.data() == scooby_object.id,
                        "Object id is '{}' rather than '{}'".format(obj_id_index.data(), scooby_object.id))
        # Check objet class
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        self.assertTrue(obj_cls_name_index.data() == 'dog',
                        "Object class name is '{}' rather than 'dog'".format(obj_cls_name_index.data()))
        obj_cls_id_index = model.index(0, header_index("object_class_id"))
        self.assertTrue(obj_cls_id_index.data() == dog_class_id,
                        "Object class id is '{}' rather than '{}'".format(obj_cls_id_index.data(), dog_class_id))
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertTrue(parameter_name_index.data() is None,
                        "Parameter name is '{}' rather than None".format(parameter_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor), "Editor is not a 'CustomComboEditor'")
        self.assertTrue(editor.count() == 1, "Editor count is '{}' rather than 1".format(editor.count()))
        self.assertTrue(editor.itemText(0) == 'breed',
                        "Editor text is '{}' rather than 'breed'".format(editor.itemText(0)))
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertTrue(parameter_name_index.data() == 'breed',
                        "Parameter name is '{}' rather than 'breed'".format(parameter_name_index.data()))
        # Add second object parameter value (for pluto), to test autofilling of object class from *parameter*
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.header.index
        # Enter parameter name
        parameter_name_index = model.index(1, header_index("parameter_name"))
        self.assertTrue(parameter_name_index.data() is None,
                "Parameter name is '{}' rather than None".format(parameter_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor), "Editor is not a 'CustomComboEditor'")
        self.assertTrue(editor.count() == 1, "Editor count is '{}' rather than 1".format(editor.count()))
        self.assertTrue(editor.itemText(0) == 'breed',
                "Editor text is '{}' rather than 'breed'".format(editor.itemText(0)))
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertTrue(parameter_name_index.data() == 'breed',
                "Parameter name is '{}' rather than 'breed'".format(parameter_name_index.data()))
        # Check objet class
        obj_cls_name_index = model.index(1, header_index("object_class_name"))
        self.assertTrue(obj_cls_name_index.data() == 'dog',
                        "Object class name is '{}' rather than 'dog'".format(obj_cls_name_index.data()))
        obj_cls_id_index = model.index(1, header_index("object_class_id"))
        self.assertTrue(obj_cls_id_index.data() == dog_class_id,
                        "Object class id is '{}' rather than '{}'".format(obj_cls_id_index.data(), dog_class_id))
        # Enter object name
        obj_name_index = model.index(1, header_index("object_name"))
        self.assertTrue(obj_name_index.data() is None,
                        "Object name is '{}' rather than None".format(obj_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_index)
        view.itemDelegate().setEditorData(editor, obj_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor), "Editor is not a 'CustomComboEditor'")
        self.assertTrue(editor.count() == 2, "Editor count is '{}' rather than 2".format(editor.count()))
        self.assertTrue(editor.itemText(0) == 'pluto', "Item 0 is '{}' rather than 'pluto'".format(editor.itemText(0)))
        self.assertTrue(editor.itemText(1) == 'scooby',
                        "Item 1 is '{}' rather than 'scooby'".format(editor.itemText(1)))
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, obj_name_index)
        view.itemDelegate().destroyEditor(editor, obj_name_index)
        self.assertTrue(obj_name_index.data() == 'pluto',
                        "Object name is '{}' rather than 'pluto'".format(obj_name_index.data()))
        obj_id_index = model.index(1, header_index("object_id"))
        self.assertTrue(obj_id_index.data() == pluto_object.id,
                        "Object id is '{}' rather than '{}'".format(obj_id_index.data(), pluto_object.id))
        # Check the db
        # First (scooby)
        parameter_id = model.index(0, header_index("parameter_id")).data()
        parameter_value_id = model.index(0, header_index("id")).data()
        parameter_value = self.tree_view_form.db_map.single_parameter_value(id=parameter_value_id).one_or_none()
        self.assertTrue(parameter_value.id == parameter_value_id,
                        "Parameter value id is {} rather than {}".format(parameter_value.id, parameter_value_id))
        self.assertTrue(parameter_value.parameter_id == parameter_id,
                        "Parameter id is {} rather than {}".format(parameter_value.parameter_id, parameter_id))
        self.assertTrue(parameter_value.object_id == scooby_object.id,
                        "Parameter object id is '{}' rather than '{}'".\
                            format(parameter_value.object_id, scooby_object.id))
        self.assertTrue(parameter_value.relationship_id is None,
                        "Parameter relationship id is '{}' rather than None".format(parameter_value.relationship_id))
        # First (pluto)
        parameter_id = model.index(1, header_index("parameter_id")).data()
        parameter_value_id = model.index(1, header_index("id")).data()
        parameter_value = self.tree_view_form.db_map.single_parameter_value(id=parameter_value_id).one_or_none()
        self.assertTrue(parameter_value.id == parameter_value_id,
                        "Parameter value id is {} rather than {}".format(parameter_value.id, parameter_value_id))
        self.assertTrue(parameter_value.parameter_id == parameter_id,
                        "Parameter id is {} rather than {}".format(parameter_value.parameter_id, parameter_id))
        self.assertTrue(parameter_value.object_id == pluto_object.id,
                        "Parameter object id is '{}' rather than '{}'".\
                            format(parameter_value.object_id, pluto_object.id))
        self.assertTrue(parameter_value.relationship_id is None,
                        "Parameter relationship id is '{}' rather than None".format(parameter_value.relationship_id))

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
        header_index = model.header.index
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
        header_index = model.header.index
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertTrue(parameter_name_index.data() is None,
                        "Parameter name is '{}' rather than None".format(parameter_name_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomComboEditor), "Editor is not a 'CustomComboEditor'")
        self.assertTrue(editor.count() == 1, "Editor count is '{}' rather than 1".format(editor.count()))
        self.assertTrue(editor.itemText(0) == 'combined_mojo',
                        "Editor text is '{}' rather than 'combined_mojo'".format(editor.itemText(0)))
        editor.setCurrentIndex(0)
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertTrue(parameter_name_index.data() == 'combined_mojo',
                        "Parameter name is '{}' rather than 'combined_mojo'".format(parameter_name_index.data()))
        # Check relationship class
        rel_cls_name = model.index(0, header_index("relationship_class_name")).data()
        self.assertTrue(rel_cls_name == 'fish__dog',
                        "Relationship class name is '{}' rather than 'fish__dog'".format(rel_cls_name))
        rel_cls_id = model.index(0, header_index("relationship_class_id")).data()
        self.assertTrue(rel_cls_id == fish_dog_relationship_class.id,
                        "Relationship class id is '{}' rather than '{}'".\
                            format(rel_cls_id, fish_dog_relationship_class.id))
        obj_cls_name_list_index = model.index(0, header_index("object_class_name_list"))
        self.assertTrue(obj_cls_name_list_index.data() == 'fish,dog',
                        "Object class name list is '{}' rather than 'fish,dog'".format(obj_cls_name_list_index.data()))
        obj_cls_id_list_index = model.index(0, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertTrue(split_obj_cls_id_list == [fish_class_id, dog_class_id],
                        "Object class id list is '{}' rather than '{}'".\
                            format(split_obj_cls_id_list, [fish_class_id, dog_class_id]))
        # Enter object name list
        obj_name_list_index = model.index(0, header_index("object_name_list"))
        self.assertTrue(obj_name_list_index.data() is None,
                        "Object name list is '{}' rather than None".format(obj_name_list_index.data()))
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_list_index)
        view.itemDelegate().setEditorData(editor, obj_name_list_index)
        self.assertTrue(isinstance(editor, ObjectNameListEditor), "Editor is not a 'ObjectNameListEditor'")
        combos = editor.combos
        self.assertTrue(len(combos) == 2, "Editor combos count is '{}' rather than 2".format(len(combos)))
        self.assertTrue(combos[0].count() == 3,
                        "Editor combo 0 count is '{}' rather than 3".format(combos[0].count()))
        self.assertTrue(combos[0].itemText(0) == 'fish',
                        "Editor combo 0 item 0 is '{}' rather than 'fish'".format(combos[0].itemText(0)))
        self.assertTrue(combos[0].itemText(2) == 'nemo',
                        "Editor combo 0 item 2 is '{}' rather than 'nemo'".format(combos[0].itemText(2)))
        self.assertTrue(combos[1].count() == 4,
                        "Editor combo 1 count is '{}' rather than 4".format(combos[1].count()))
        self.assertTrue(combos[1].itemText(0) == 'dog',
                        "Editor combo 1 item 0 is '{}' rather than 'dog'".format(combos[1].itemText(0)))
        self.assertTrue(combos[1].itemText(2) == 'pluto',
                        "Editor combo 1 item 2 is '{}' rather than 'pluto'".format(combos[1].itemText(2)))
        self.assertTrue(combos[1].itemText(3) == 'scooby',
                        "Editor combo 1 item 3 is '{}' rather than 'scooby'".format(combos[1].itemText(3)))
        combos[0].setCurrentIndex(2)
        combos[1].setCurrentIndex(2)
        view.itemDelegate().setModelData(editor, model, obj_name_list_index)
        view.itemDelegate().destroyEditor(editor, obj_name_list_index)
        # Check relationship
        relationship_id = model.index(0, header_index("relationship_id")).data()
        self.assertTrue(relationship_id == nemo_pluto_relationship.id,
                        "Relationship id is {} rather than {}".format(relationship_id, nemo_pluto_relationship.id))
        obj_id_list_index = model.index(0, header_index("object_id_list"))
        split_obj_id_list = [int(x) for x in obj_id_list_index.data().split(',')]
        self.assertTrue(split_obj_id_list == [nemo_object.id, pluto_object.id],
                        "Obj id list is {} rather than {}".\
                            format(split_obj_id_list, [nemo_object.id, pluto_object.id]))
        # Check the db
        parameter_id = model.index(0, header_index("parameter_id")).data()
        parameter_value_id = model.index(0, header_index("id")).data()
        parameter_value = self.tree_view_form.db_map.single_parameter_value(id=parameter_value_id).one_or_none()
        self.assertTrue(parameter_value.id == parameter_value_id,
                        "Parameter value id is {} rather than {}".format(parameter_value.id, parameter_value_id))
        self.assertTrue(parameter_value.parameter_id == parameter_id,
                        "Parameter id is {} rather than {}".format(parameter_value.parameter_id, parameter_id))
        self.assertTrue(parameter_value.relationship_id == nemo_pluto_relationship.id,
                        "Parameter relationship id is '{}' rather than '{}'".\
                            format(parameter_value.object_id, nemo_pluto_relationship.id))
        self.assertTrue(parameter_value.object_id is None,
                        "Parameter object id is '{}' rather than None".format(parameter_value.object_id))

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
        header_index = model.header.index
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertTrue(obj_cls_name_index.data() == 'fish',
                        "Object class name is '{}' rather than 'fish'".format(obj_cls_name_index.data()))
        # Deselected fish and select dog item in object tree
        dog_item = root_item.child(1)
        dog_tree_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_tree_index, QItemSelectionModel.Deselect)
        self.tree_view_form.ui.treeView_object.selectionModel().select(dog_tree_index, QItemSelectionModel.Select)
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertTrue(obj_cls_name_index.data() == 'dog',
                        "Object class name is '{}' rather than 'dog'".format(obj_cls_name_index.data()))
        # Clear object tree selection and select root
        self.tree_view_form.ui.treeView_object.selectionModel().clearSelection()
        root_tree_index = self.tree_view_form.object_tree_model.indexFromItem(root_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(root_tree_index, QItemSelectionModel.Select)
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertTrue(obj_cls_name_index.data() is None,
                        "Object class name is '{}' rather than None".format(obj_cls_name_index.data()))


if __name__ == '__main__':
    unittest.main()
