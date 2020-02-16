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
Unit tests for SpineToolboxProject class.

:author: P. Savolainen (VTT)
:date:   14.11.2018
"""

import os
import unittest
from unittest import mock
import logging
import sys
from PySide2.QtCore import QItemSelectionModel, QVariantAnimation
from PySide2.QtWidgets import QApplication
from .mock_helpers import (
    clean_up_toolboxui_with_project,
    create_toolboxui_with_project,
    add_ds,
    add_dc,
    add_tool,
    add_view,
    add_importer,
    add_exporter,
)
from spinetoolbox.tool_specifications import PythonTool


# noinspection PyUnusedLocal
class TestSpineToolboxProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def setUp(self):
        """Makes a ToolboxUI instance and opens a project before each test."""
        self.toolbox = create_toolboxui_with_project()

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        clean_up_toolboxui_with_project(self.toolbox)

    def test_add_data_store(self):
        """Test adding a Data Store to project."""
        name = "DS"
        add_ds(self.toolbox.project(), name)
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.item(found_index).project_item
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Data Store
        self.assertEqual(found_item.item_type(), "Data Store")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def check_dag_handler(self, name):
        """Check that project dag handler contains only one
        graph, which has one node and its name matches the
        given argument."""
        dag = self.toolbox.project().dag_handler
        self.assertTrue(len(dag.dags()) == 1)
        g = dag.dag_with_node(name)
        self.assertTrue(len(g.nodes()) == 1)
        for node_name in g.nodes():
            self.assertTrue(node_name == name)

    def test_add_data_connection(self):
        """Test adding a Data Connection to project."""
        name = "DC"
        add_dc(self.toolbox.project(), name)
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.item(found_index).project_item
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Data Connection
        self.assertEqual(found_item.item_type(), "Data Connection")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_tool(self):
        """Test adding a Tool to project."""
        name = "Tool"
        add_tool(self.toolbox.project(), name)
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.item(found_index).project_item
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Tool
        self.assertEqual(found_item.item_type(), "Tool")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_view(self):
        """Test adding a View to project."""
        name = "View"
        add_view(self.toolbox.project(), name)
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.item(found_index).project_item
        self.assertEqual(found_item.name, name)
        # Check that the created item is a View
        self.assertEqual(found_item.item_type(), "View")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_six_items(self):
        """Test that adding multiple items works as expected.
        Six items are added in order DS, DC, Tool, View, Importer, Exporter."""
        p = self.toolbox.project()
        # Add items
        ds_name = "DS"
        dc_name = "DC"
        tool_name = "Tool"
        view_name = "View"
        imp_name = "Importer"
        exp_name = "Exporter"
        add_ds(p, ds_name)
        add_dc(p, dc_name)
        add_tool(p, tool_name)
        add_view(p, view_name)
        add_importer(p, imp_name)
        add_exporter(p, exp_name)
        # Check that the items are found from project item model
        ds = self.toolbox.project_item_model.get_item(ds_name)
        self.assertEqual(ds_name, ds.name)
        dc = self.toolbox.project_item_model.get_item(dc_name)
        self.assertEqual(dc_name, dc.name)
        tool = self.toolbox.project_item_model.get_item(tool_name)
        self.assertEqual(tool_name, tool.name)
        view = self.toolbox.project_item_model.get_item(view_name)
        self.assertEqual(view_name, view.name)
        importer = self.toolbox.project_item_model.get_item(imp_name)
        self.assertEqual(imp_name, importer.name)
        exporter = self.toolbox.project_item_model.get_item(exp_name)
        self.assertEqual(exp_name, exporter.name)
        # DAG handler should now have six graphs, each with one item
        dag_hndlr = self.toolbox.project().dag_handler
        n_dags = len(dag_hndlr.dags())
        self.assertEqual(6, n_dags)
        # Check that all created items are in graphs
        ds_graph = dag_hndlr.dag_with_node(ds_name)  # Returns None if graph is not found
        self.assertIsNotNone(ds_graph)
        dc_graph = dag_hndlr.dag_with_node(dc_name)
        self.assertIsNotNone(dc_graph)
        tool_graph = dag_hndlr.dag_with_node(tool_name)
        self.assertIsNotNone(tool_graph)
        view_graph = dag_hndlr.dag_with_node(view_name)
        self.assertIsNotNone(view_graph)
        importer_graph = dag_hndlr.dag_with_node(imp_name)
        self.assertIsNotNone(importer_graph)
        exporter_graph = dag_hndlr.dag_with_node(exp_name)
        self.assertIsNotNone(exporter_graph)

    def test_execute_project_with_single_item(self):
        item_name = self.add_tool()
        item = self.toolbox.project_item_model.get_item(item_name).project_item
        item.execute_forward = mock.MagicMock(return_value=True)
        anim = QVariantAnimation()
        anim.setDuration(0)
        item.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        self.toolbox.project().execute_project()
        item.execute_forward.assert_called_with([])

    def test_execute_project_with_two_dags(self):
        item1_name = self.add_tool()
        item1 = self.toolbox.project_item_model.get_item(item1_name).project_item
        item1.execute_forward = mock.MagicMock(return_value=True)
        item2_name = self.add_view()
        item2 = self.toolbox.project_item_model.get_item(item2_name).project_item
        item2.execute_forward = mock.MagicMock(return_value=True)
        anim = QVariantAnimation()
        anim.setDuration(0)
        item1.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        item2.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        self.toolbox.project().execute_project()
        item1.execute_forward.assert_called_with([])
        item2.execute_forward.assert_called_with([])

    def test_execute_selected_dag(self):
        item1_name = self.add_tool()
        item1 = self.toolbox.project_item_model.get_item(item1_name).project_item
        item1.execute_forward = mock.MagicMock(return_value=True)
        item2_name = self.add_view()
        item2 = self.toolbox.project_item_model.get_item(item2_name).project_item
        item2.execute_forward = mock.MagicMock(return_value=True)
        anim = QVariantAnimation()
        anim.setDuration(0)
        item1.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        item2.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        self.toolbox.project().set_item_selected(item2)
        self.toolbox.project().execute_selected()
        item1.execute_forward.assert_not_called()
        item2.execute_forward.assert_called_with([])

    def test_change_name(self):
        """Tests renaming a project."""
        new_name = "New Project Name"
        new_short_name = "new_project_name"
        self.toolbox.project().set_name(new_name)
        self.assertEqual(self.toolbox.project().name, new_name)
        self.assertEqual(self.toolbox.project().short_name, new_short_name)

    def test_set_description(self):
        """Tests updating the description for a project."""
        desc = "Project Description"
        self.toolbox.project().set_description(desc)
        self.assertEqual(self.toolbox.project().description, desc)

    def test_load_tool_specification_from_file(self):
        """Tests creating a PythonTool (specification) instance from a valid tool specification file."""
        spec_path = os.path.abspath(os.path.join(os.curdir, "tests", "test_resources", "test_tool_spec.json"))
        tool_spec = self.toolbox.project().load_tool_specification_from_file(spec_path)
        self.assertIsInstance(tool_spec, PythonTool)

    def test_execute_selected_item_within_single_dag(self):
        data_store_name = self.add_ds()
        data_store = self.toolbox.project_item_model.get_item(data_store_name).project_item
        data_store.execute_forward = mock.MagicMock(return_value=True)
        tool_name = self.add_tool()
        tool = self.toolbox.project_item_model.get_item(tool_name).project_item
        tool.execute_forward = mock.MagicMock(return_value=True)
        view_name = self.add_view()
        view = self.toolbox.project_item_model.get_item(view_name).project_item
        view.execute_forward = mock.MagicMock(return_value=True)
        anim = QVariantAnimation()
        anim.setDuration(0)
        tool.make_execution_leave_animation = mock.MagicMock(return_value=anim)
        self.toolbox.project().dag_handler.add_graph_edge(data_store_name, tool_name)
        self.toolbox.project().dag_handler.add_graph_edge(tool_name, view_name)
        self.toolbox.project().set_item_selected(tool)
        self.toolbox.project().execute_selected()
        data_store.execute_forward.assert_not_called()
        tool.execute_forward.assert_called()
        view.execute_forward.assert_not_called()

    def add_ds(self):
        """Helper method to add Data Store. Returns created items name."""
        item = dict(name="DS", description="", url=dict(), x=0, y=0)
        with mock.patch("spinetoolbox.project_item.create_dir"):
            self.toolbox.project().add_project_items("Data Stores", item)
        return "DS"

    def add_dc(self):
        """Helper method to add Data Connection. Returns created items name."""
        item = dict(name="DC", description="", references=list(), x=0, y=0)
        with mock.patch("spinetoolbox.project_item.create_dir"):
            self.toolbox.project().add_project_items("Data Connections", item)
        return "DC"

    def add_tool(self):
        """Helper method to add Tool. Returns created items name."""
        item = dict(name="tool", description="", tool="", execute_in_work=False, x=0, y=0)
        with mock.patch("spinetoolbox.project_item.create_dir"):
            self.toolbox.project().add_project_items("Tools", item)
        return "tool"

    def add_view(self):
        """Helper method to add View. Returns created items name."""
        item = dict(name="view", description="", x=0, y=0)
        with mock.patch("spinetoolbox.project_item.create_dir"):
            self.toolbox.project().add_project_items("Views", item)
        return "view"


if __name__ == '__main__':
    unittest.main()
