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
Unit tests for project_tree_item module.

:author: A. Soininen (VTT)
:date:   17.1.2020
"""

from tempfile import TemporaryDirectory
import unittest
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinetoolbox.project_item.project_item import ProjectItem
from spinetoolbox.project_tree_item import (
    BaseProjectTreeItem,
    CategoryProjectTreeItem,
    LeafProjectTreeItem,
    RootProjectTreeItem,
)
from .mock_helpers import clean_up_toolbox, create_toolboxui_with_project


class TestLeafProjectTreeItem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_BaseProjectTreeItem_initial_state(self):
        item = BaseProjectTreeItem("items name", "description")
        self.assertEqual(item.name, "items name")
        self.assertEqual(item.description, "description")
        self.assertEqual(item.short_name, "items_name")
        self.assertIsNone(item.parent())
        self.assertEqual(item.child_count(), 0)
        self.assertFalse(item.children())

    def test_BaseProjectTreeItem_flags(self):
        item = BaseProjectTreeItem("name", "description")
        self.assertEqual(item.flags(), Qt.NoItemFlags)

    def test_CategoryProjectTreeItem_flags(self):
        with TemporaryDirectory() as project_dir:
            toolbox, item = self._category_item(project_dir)
            self.assertEqual(item.flags(), Qt.ItemIsEnabled)
            clean_up_toolbox(toolbox)

    def test_LeafProjectTreeItem_flags(self):
        with TemporaryDirectory() as project_dir:
            toolbox = create_toolboxui_with_project(project_dir)
            item = self._leaf_item(toolbox)
            self.assertEqual(item.flags(), Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            clean_up_toolbox(toolbox)

    def test_RootProjectTreeItem_initial_name_and_description(self):
        item = RootProjectTreeItem()
        self.assertEqual(item.name, "root")
        self.assertEqual(item.description, "The Root Project Tree Item.")

    def test_RootProjectTreeItem_parent_child_hierarchy(self):
        parent = RootProjectTreeItem()
        with TemporaryDirectory() as project_dir:
            toolbox, child = self._category_item(project_dir)
            parent.add_child(child)
            self.assertEqual(parent.child_count(), 1)
            self.assertEqual(parent.children()[0], child)
            self.assertEqual(child.parent(), parent)
            self.assertEqual(child.row(), 0)
            parent.remove_child(0)
            self.assertEqual(parent.child_count(), 0)
            self.assertFalse(parent.children())
            self.assertIsNone(child.parent())
            clean_up_toolbox(toolbox)

    def test_CategoryProjectTreeItem_parent_child_hierarchy(self):
        with TemporaryDirectory() as project_dir:
            toolbox, parent = self._category_item(project_dir)
            leaf = self._leaf_item(toolbox)
            parent.add_child(leaf)
            self.assertEqual(parent.child_count(), 1)
            self.assertEqual(parent.children()[0], leaf)
            self.assertEqual(leaf.parent(), parent)
            self.assertEqual(leaf.row(), 0)
            parent.remove_child(0)
            self.assertEqual(parent.child_count(), 0)
            self.assertFalse(parent.children())
            self.assertIsNone(leaf.parent())
            clean_up_toolbox(toolbox)

    @staticmethod
    def _category_item(project_dir):
        """Set up toolbox."""
        toolbox = create_toolboxui_with_project(project_dir)
        item = CategoryProjectTreeItem("category item", "A category tree item")
        return toolbox, item

    @staticmethod
    def _leaf_item(toolbox):
        project_item = ProjectItem("PI", "A Project item", 0.0, 0.0, toolbox.project())
        item = LeafProjectTreeItem(project_item, toolbox)
        return item


if __name__ == '__main__':
    unittest.main()
