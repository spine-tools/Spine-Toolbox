######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
import os.path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtCore import QVariantAnimation, QEventLoop
from PySide2.QtWidgets import QApplication
from spine_engine.project_item.executable_item_base import ExecutableItemBase
from spine_engine.project_item.connection import Connection
from spinetoolbox.metaobject import shorten
from .mock_helpers import (
    clean_up_toolbox,
    create_toolboxui_with_project,
    add_ds,
    add_dc,
    add_tool,
    add_view,
    add_importer,
    add_gdx_exporter,
)


# noinspection PyUnusedLocal
class TestSpineToolboxProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Makes a ToolboxUI instance and opens a project before each test."""
        self._temp_dir = TemporaryDirectory()
        self.toolbox = create_toolboxui_with_project(self._temp_dir.name)

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        clean_up_toolbox(self.toolbox)
        self._temp_dir.cleanup()

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
        Six items are added in order DS, DC, Tool, View, Importer, GdxExporter."""
        p = self.toolbox.project()
        # Add items
        ds_name = "DS"
        dc_name = "DC"
        tool_name = "Tool"
        view_name = "View"
        imp_name = "Importer"
        exp_name = "GdxExporter"
        add_ds(p, ds_name)
        add_dc(p, dc_name)
        add_tool(p, tool_name)
        add_view(p, view_name)
        add_importer(p, imp_name)
        add_gdx_exporter(p, exp_name)
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
        gdx_exporter = self.toolbox.project_item_model.get_item(exp_name)
        self.assertEqual(exp_name, gdx_exporter.name)
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

    def _wait_for_execution_finished(self):
        loop = QEventLoop()
        self.toolbox.project().project_execution_finished.connect(loop.quit)
        loop.exec_()

    def test_execute_project_with_single_item(self):
        _, view_executable = self._make_item(self.add_view)
        with mock.patch("spine_engine.spine_engine.SpineEngine._make_item") as mock_make_item:
            mock_make_item.return_value = view_executable
            self.toolbox.project().execute_project()
            self._wait_for_execution_finished()
        self.assertTrue(view_executable.execute_called)

    def test_execute_project_with_two_dags(self):
        item1, item1_executable = self._make_item(self.add_dc)
        item2, item2_executable = self._make_item(self.add_view)
        with mock.patch("spine_engine.spine_engine.SpineEngine._make_item") as mock_make_item:
            mock_make_item.side_effect = lambda name, *args: {
                item1.name: item1_executable,
                item2.name: item2_executable,
            }[name]
            self.toolbox.project().execute_project()
            self._wait_for_execution_finished()
        self.assertTrue(item1_executable.execute_called)
        self.assertTrue(item2_executable.execute_called)

    def test_execute_selected_dag(self):
        item1, item1_executable = self._make_item(self.add_dc)
        item2, item2_executable = self._make_item(self.add_view)
        self.toolbox.project().set_item_selected(item2)
        with mock.patch("spine_engine.spine_engine.SpineEngine._make_item") as mock_make_item:
            mock_make_item.side_effect = lambda name, *args: {
                item1.name: item1_executable,
                item2.name: item2_executable,
            }[name]
            self.toolbox.project().execute_selected()
            self._wait_for_execution_finished()
        self.assertFalse(item1_executable.execute_called)
        self.assertTrue(item2_executable.execute_called)

    def test_change_name(self):
        """Tests renaming a project."""
        new_name = "New Project Name"
        new_short_name = "new_project_name"
        with mock.patch("spinetoolbox.ui_main.ToolboxUI.update_recent_projects"):
            self.toolbox.project().set_name(new_name)
        self.assertEqual(self.toolbox.project().name, new_name)
        self.assertEqual(self.toolbox.project().short_name, new_short_name)

    def test_set_description(self):
        """Tests updating the description for a project."""
        desc = "Project Description"
        self.toolbox.project().set_description(desc)
        self.assertEqual(self.toolbox.project().description, desc)

    def test_execute_selected_item_within_single_dag(self):
        data_store, data_store_executable = self._make_item(self.add_ds)
        data_connection, data_connection_executable = self._make_item(self.add_dc)
        view, view_executable = self._make_item(self.add_view)
        self.toolbox.project().dag_handler.add_graph_edge(data_store.name, data_connection.name)
        self.toolbox.project().dag_handler.add_graph_edge(data_connection.name, view.name)
        self.toolbox.project().set_item_selected(data_connection)
        with mock.patch("spine_engine.spine_engine.SpineEngine._make_item") as mock_make_item:
            mock_make_item.side_effect = lambda name, *args: {
                data_store.name: data_store_executable,
                data_connection.name: data_connection_executable,
                view.name: view_executable,
            }[name]
            self.toolbox.project().execute_selected()
            self._wait_for_execution_finished()
        self.assertFalse(data_store_executable.execute_called)
        self.assertTrue(data_connection_executable.execute_called)
        self.assertFalse(view_executable.execute_called)

    def test_rename_item(self):
        project = self.toolbox.project()
        source_name = "source"
        destination_name = "destination"
        add_view(project, source_name)
        add_view(project, destination_name)
        source_item = project.get_item("source")
        project.add_connection(Connection(source_name, "left", destination_name, "right"))
        while project.is_busy():
            # Make sure we process all pending signals related to changes in DAG.
            # Otherwise me may rename the item while the old name is still in use.
            QApplication.processEvents()
        project.rename_item("source", "renamed source", "")
        self.assertTrue(bool(project.get_item("renamed source")))
        self.assertEqual(source_item.name, "renamed source")
        self.assertEqual(project.connections, [Connection("renamed source", "left", destination_name, "right")])
        dags = project.dag_handler.dags()
        self.assertEqual(len(dags), 1)
        self.assertEqual(
            project.dag_handler.node_successors(dags[0]), {"destination": [], "renamed source": ["destination"]}
        )
        self.assertEqual(source_item.get_icon().name(), "renamed source")
        self.assertEqual(os.path.split(source_item.data_dir)[1], shorten("renamed source"))

    def add_ds(self):
        """Helper method to add Data Store. Returns created items name."""
        item = {"DS": {"type": "Data Store", "description": "", "url": dict(), "x": 0, "y": 0}}
        with mock.patch("spinetoolbox.project_item.project_item.create_dir"):
            self.toolbox.project().add_project_items(item)
        return "DS"

    def add_dc(self):
        """Helper method to add Data Connection. Returns created items name."""
        item = {"DC": {"type": "Data Connection", "description": "", "references": list(), "x": 0, "y": 0}}
        with mock.patch("spinetoolbox.project_item.project_item.create_dir"):
            self.toolbox.project().add_project_items(item)
        return "DC"

    def add_tool(self):
        """Helper method to add Tool. Returns created items name."""
        item = {
            "tool": {"type": "Tool", "description": "", "specification": "", "execute_in_work": False, "x": 0, "y": 0}
        }
        with mock.patch("spinetoolbox.project_item.project_item.create_dir"):
            self.toolbox.project().add_project_items(item)
        return "tool"

    def add_view(self):
        """Helper method to add View. Returns created items name."""
        item = {"view": {"type": "View", "description": "", "x": 0, "y": 0}}
        with mock.patch("spinetoolbox.project_item.project_item.create_dir"):
            self.toolbox.project().add_project_items(item)
        return "view"

    def _make_item(self, add_item_function):
        item_name = add_item_function()
        item = self.toolbox.project_item_model.get_item(item_name).project_item
        item_executable = _MockExecutableItem(item_name, self.toolbox)
        item.execution_item = mock.MagicMock(return_value=item_executable)
        animation = QVariantAnimation()
        animation.setDuration(0)
        item.make_execution_leave_animation = mock.MagicMock(return_value=animation)
        return item, item_executable


class _MockExecutableItem(ExecutableItemBase):
    def __init__(self, name, logger):
        super().__init__(name, logger)
        self.execute_called = False

    @ExecutableItemBase.filter_id.setter
    def filter_id(self, _):
        pass

    @staticmethod
    def item_type():
        return "Mock item"

    def execute(self, _forward_resources, _backward_resources):
        self.execute_called = True
        return True

    @classmethod
    def from_dict(cls, item_dict, name, project_dir, app_settings, specifications, logger):
        raise NotImplementedError()


if __name__ == '__main__':
    unittest.main()
