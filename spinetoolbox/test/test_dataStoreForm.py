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
Unit tests for TreeViewForm class.

:author: M. Marin (VTT)
:date:   6.12.2018
"""

import unittest
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
from widgets.data_store_widgets import TreeViewForm, GraphViewForm
from sqlalchemy.util import KeyedTuple


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
        with mock.patch("data_store.DataStore") as mock_data_store, \
                mock.patch("spinedatabase_api.DiffDatabaseMapping") as mock_db_map:
            logging.disable(level=logging.ERROR)  # Disable logging
            self.tree_view_form = TreeViewForm(mock_data_store, mock_db_map, "mock_db")
            self.graph_view_form = GraphViewForm(mock_data_store, mock_db_map, "mock_db")
            logging.disable(level=logging.NOTSET)  # Enable logging

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.tree_view_form = None
        self.graph_view_form = None

    def test_add_object_classes(self):
        """Test that object classes are added to the object tree model in the right positions.
        """
        fish = KeyedTuple([1, 'fish', 'A fish.', 1], labels=['id', 'name', 'description', 'display_order'])
        dog = KeyedTuple([2, 'dog', 'A dog.', 3], labels=['id', 'name', 'description', 'display_order'])
        cat = KeyedTuple([3, 'cat', 'A cat.', 2], labels=['id', 'name', 'description', 'display_order'])
        object_classes= [fish, dog, cat]
        self.tree_view_form.add_object_classes(object_classes)
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_type = fish_item.data(Qt.UserRole)
        fish_id = fish_item.data(Qt.UserRole + 1)['id']
        fish_name = fish_item.data(Qt.UserRole + 1)['name']
        dog_item = root_item.child(2)
        dog_type = dog_item.data(Qt.UserRole)
        dog_id = dog_item.data(Qt.UserRole + 1)['id']
        dog_name = dog_item.data(Qt.UserRole + 1)['name']
        cat_item = root_item.child(1)
        cat_type = cat_item.data(Qt.UserRole)
        cat_id = cat_item.data(Qt.UserRole + 1)['id']
        cat_name = cat_item.data(Qt.UserRole + 1)['name']
        self.assertTrue(fish_type == "object_class", "Fish type is not 'object_class'")
        self.assertTrue(fish_id == 1, "Fish id is not 1")
        self.assertTrue(fish_name == "fish", "Fish name is not 'fish'")
        self.assertTrue(dog_type == "object_class", "Dog type is not 'object_class'")
        self.assertTrue(dog_id == 2, "Dog id is not 2")
        self.assertTrue(dog_name == "dog", "Dog name is not 'dog'")
        self.assertTrue(cat_type == "object_class", "Cat type is not 'object_class'")
        self.assertTrue(cat_id == 3, "Cat id is not 3")
        self.assertTrue(cat_name == "cat", "Cat name is not 'cat'")


if __name__ == '__main__':
    unittest.main()
