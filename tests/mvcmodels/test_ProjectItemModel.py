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
Unit tests for ProjectItemModel class.

:author: A. Soininen (VTT)
:date:   14.10.2019
"""

import unittest
from unittest.mock import MagicMock, NonCallableMagicMock
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinetoolbox.mvcmodels.project_item_model import ProjectItemModel
from spinetoolbox.project_tree_item import CategoryProjectTreeItem, LeafProjectTreeItem, RootProjectTreeItem
from spinetoolbox.project_item import ProjectItem
from ..mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestProjectItemModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Sets up toolbox."""
        self.toolbox = create_toolboxui_with_project()

    def tearDown(self):
        """Cleans up."""
        clean_up_toolboxui_with_project(self.toolbox)

    def test_empty_model(self):
        root = RootProjectTreeItem()
        model = ProjectItemModel(self.toolbox, root)
        self.assertEqual(model.rowCount(), 0)
        self.assertEqual(model.columnCount(), 1)
        self.assertEqual(model.n_items(), 0)
        self.assertFalse(model.items())

    def test_insert_item_category_item(self):
        root = RootProjectTreeItem()
        model = ProjectItemModel(self.toolbox, root)
        category = CategoryProjectTreeItem("category", "category description", None, MagicMock(), None, None)
        model.insert_item(category)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.n_items(), 0)
        category_index = model.find_category("category")
        self.assertTrue(category_index.isValid())
        self.assertEqual(category_index.row(), 0)
        self.assertEqual(category_index.column(), 0)
        self.assertEqual(model.data(category_index, Qt.DisplayRole), "category")

    def test_insert_item_leaf_item(self):
        root = RootProjectTreeItem()
        model = ProjectItemModel(self.toolbox, root)
        category = CategoryProjectTreeItem("category", "category description", None, MagicMock(), None, None)
        model.insert_item(category)
        category_index = model.find_category("category")
        mock_project_item = NonCallableMagicMock()
        mock_project_item.name = "project item"
        mock_project_item.description = "project item description"
        leaf = LeafProjectTreeItem(mock_project_item, self.toolbox)
        model.insert_item(leaf, category_index)
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.rowCount(category_index), 1)
        self.assertEqual(model.n_items(), 1)
        self.assertEqual(model.items("category"), [leaf])

    def test_setData(self):
        model = self.toolbox.project_item_model
        item_dict = dict(name="view", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Views", item_dict)
        leaf_index = model.find_item("view")
        status = model.setData(leaf_index, "new view item name")
        self.assertTrue(status)
        leaf_item = model.get_item("new view item name")
        self.assertIsNotNone(leaf_item)
        dag_with_new_node_name = self.toolbox.project().dag_handler.dag_with_node("new view item name")
        self.assertIsNotNone(dag_with_new_node_name)
        dag_with_old_node_name = self.toolbox.project().dag_handler.dag_with_node("View")
        self.assertIsNone(dag_with_old_node_name)

    def test_category_of_item(self):
        root = RootProjectTreeItem()
        category = CategoryProjectTreeItem("category", "category description", None, MagicMock(), None, None)
        root.add_child(category)
        model = ProjectItemModel(self.toolbox, root)
        self.assertEqual(model.category_of_item("nonexistent item"), None)
        project_item = ProjectItem("item", "item description", 0.0, 0.0, self.toolbox.project(), self.toolbox)
        item = LeafProjectTreeItem(project_item, self.toolbox)
        category.add_child(item)
        found_category = model.category_of_item("item")
        self.assertEqual(found_category.name, category.name)


if __name__ == '__main__':
    unittest.main()
