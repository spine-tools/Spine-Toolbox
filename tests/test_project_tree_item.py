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

import unittest
from networkx import DiGraph
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinetoolbox.project_items.view.view import View
from spinetoolbox.project_items.view.view_icon import ViewIcon
from spinetoolbox.project_items.view.widgets.view_properties_widget import ViewPropertiesWidget
from spinetoolbox.project_tree_item import (
    BaseProjectTreeItem,
    CategoryProjectTreeItem,
    LeafProjectTreeItem,
    RootProjectTreeItem,
)
from spinetoolbox.widgets.add_project_item_widget import AddProjectItemWidget
from .mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


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
        toolbox, item = self._category_item()
        self.assertEqual(item.flags(), Qt.ItemIsEnabled)
        self._destroy_toolbox(toolbox)

    def test_LeafProjectTreeItem_flags(self):
        toolbox, item = self._leaf_item()
        self.assertEqual(item.flags(), Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        self._destroy_toolbox(toolbox)

    def test_RootProjectTreeItem_initial_name_and_description(self):
        item = RootProjectTreeItem()
        self.assertEqual(item.name, "root")
        self.assertEqual(item.description, "The Root Project Tree Item.")

    def test_RootProjectTreeItem_parent_child_hierarchy(self):
        parent = RootProjectTreeItem()
        toolbox, child = self._category_item()
        parent.add_child(child)
        self.assertEqual(parent.child_count(), 1)
        self.assertEqual(parent.children()[0], child)
        self.assertEqual(child.parent(), parent)
        self.assertEqual(child.row(), 0)
        parent.remove_child(0)
        self.assertEqual(parent.child_count(), 0)
        self.assertFalse(parent.children())
        self.assertIsNone(child.parent())
        self._destroy_toolbox(toolbox)

    def test_CategoryProjectTreeItem_parent_child_hierarchy(self):
        toolbox, parent = self._category_item()
        toolbox, leaf = self._leaf_item(toolbox)
        parent.add_child(leaf)
        self.assertEqual(parent.child_count(), 1)
        self.assertEqual(parent.children()[0], leaf)
        self.assertEqual(leaf.parent(), parent)
        self.assertEqual(leaf.row(), 0)
        parent.remove_child(0)
        self.assertEqual(parent.child_count(), 0)
        self.assertFalse(parent.children())
        self.assertIsNone(leaf.parent())
        self._destroy_toolbox(toolbox)

    def test_LeafProjectTreeItem_rename(self):
        """Tests renaming a leaf project tree item and its project item."""
        expected_name = "ABC"
        expected_short_name = "abc"
        toolbox = create_toolboxui_with_project()
        project_item_dict = dict(name="View", description="", x=0, y=0)
        toolbox.project().add_project_items("Views", project_item_dict)
        index = toolbox.project_item_model.find_item("View")
        leaf = toolbox.project_item_model.item(index)
        leaf.rename(expected_name)
        cmd = toolbox.undo_stack.command(toolbox.undo_stack.index() - 1)
        self.assertFalse(cmd.isObsolete())
        # Check name
        self.assertEqual(expected_name, leaf.name)
        self.assertEqual(expected_short_name, leaf.short_name)
        self.assertEqual(expected_name, leaf.project_item.name)
        self.assertEqual(expected_short_name, leaf.project_item.short_name)
        # Check there's a dag containing a node with the new name and that no dag contains a node with the old name
        dag_with_new_node_name = toolbox.project().dag_handler.dag_with_node(expected_name)
        self.assertIsInstance(dag_with_new_node_name, DiGraph)
        dag_with_old_node_name = toolbox.project().dag_handler.dag_with_node("View")
        self.assertIsNone(dag_with_old_node_name)
        self._destroy_toolbox(toolbox)

    @staticmethod
    def _category_item():
        """Set up toolbox."""
        toolbox = create_toolboxui_with_project()
        properties_ui = ViewPropertiesWidget(toolbox).ui
        item = CategoryProjectTreeItem(
            "category item", "A category tree item", View, ViewIcon, AddProjectItemWidget, properties_ui
        )
        return toolbox, item

    @staticmethod
    def _leaf_item(toolbox=None):
        if toolbox is None:
            toolbox = create_toolboxui_with_project()
        project_item = View("View", "A View item", 0.0, 0.0, toolbox, toolbox.project(), toolbox)
        item = LeafProjectTreeItem(project_item, toolbox)
        return toolbox, item

    @staticmethod
    def _destroy_toolbox(toolbox):
        clean_up_toolboxui_with_project(toolbox)


if __name__ == '__main__':
    unittest.main()
