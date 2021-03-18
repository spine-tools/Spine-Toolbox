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
from pathlib import Path
import unittest
from unittest import mock
from PySide2.QtCore import QVariantAnimation, QEventLoop
from PySide2.QtWidgets import QApplication
from spine_engine.project_item.executable_item_base import ExecutableItemBase
from spine_engine.project_item.connection import Connection
from spine_engine.utils.helpers import shorten
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

    def test_add_all_available_items(self):
        """Test that adding multiple items works as expected.
        Multiple items are added in order DS, DC, Tool, Gimlet, View, Importer, Exporter, GdxExporter."""
        p = self.toolbox.project()
        # Add items
        ds_name = "DS"
        dc_name = "DC"
        tool_name = "Tool"
        gimlet_name = "Gimlet"
        view_name = "View"
        imp_name = "Importer"
        exporter_name = "Exporter"
        gdx_exporter_name = "GdxExporter"
        add_ds(p, ds_name)
        add_dc(p, dc_name)
        add_tool(p, tool_name)
        add_view(p, view_name)
        add_importer(p, imp_name)
        add_gdx_exporter(p, gdx_exporter_name)
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
        gdx_exporter = self.toolbox.project_item_model.get_item(gdx_exporter_name)
        self.assertEqual(gdx_exporter_name, gdx_exporter.name)
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
        exporter_graph = dag_hndlr.dag_with_node(gdx_exporter_name)
        self.assertIsNotNone(exporter_graph)

    def test_remove_item_by_name(self):
        view_name = "View"
        add_view(self.toolbox.project(), view_name)
        view = self.toolbox.project_item_model.get_item(view_name)
        self.assertEqual(view_name, view.name)
        self.toolbox.project().remove_item_by_name(view_name)
        self.assertEqual(self.toolbox.project_item_model.n_items(), 0)

    def test_remove_item_by_name_removes_outgoing_connections(self):
        project = self.toolbox.project()
        view1_name = "View 1"
        add_view(project, view1_name)
        view2_name = "View 2"
        add_view(project, view2_name)
        project.add_connection(Connection(view1_name, "top", view2_name, "bottom"))
        view = self.toolbox.project_item_model.get_item(view1_name)
        self.assertEqual(view1_name, view.name)
        view = self.toolbox.project_item_model.get_item(view2_name)
        self.assertEqual(view2_name, view.name)
        self.assertEqual(len(project.connections), 1)
        project.remove_item_by_name(view1_name)
        self.assertEqual(self.toolbox.project_item_model.n_items(), 1)
        self.assertEqual(len(project.connections), 0)
        view = self.toolbox.project_item_model.get_item(view2_name)
        self.assertEqual(view2_name, view.name)
        self.assertTrue(project.dag_handler.node_is_isolated(view2_name))

    def test_remove_item_by_name_removes_incoming_connections(self):
        project = self.toolbox.project()
        view1_name = "View 1"
        add_view(project, view1_name)
        view2_name = "View 2"
        add_view(project, view2_name)
        project.add_connection(Connection(view1_name, "top", view2_name, "bottom"))
        view = self.toolbox.project_item_model.get_item(view1_name)
        self.assertEqual(view1_name, view.name)
        view = self.toolbox.project_item_model.get_item(view2_name)
        self.assertEqual(view2_name, view.name)
        self.assertEqual(len(project.connections), 1)
        project.remove_item_by_name(view2_name)
        self.assertEqual(self.toolbox.project_item_model.n_items(), 1)
        self.assertEqual(len(project.connections), 0)
        view = self.toolbox.project_item_model.get_item(view1_name)
        self.assertEqual(view1_name, view.name)
        self.assertTrue(project.dag_handler.node_is_isolated(view1_name))

    def _wait_for_execution_finished(self):
        loop = QEventLoop()
        self.toolbox.project().project_execution_finished.connect(loop.quit)
        loop.exec_()

    def test_execute_project_with_single_item(self):
        view = add_view(self.toolbox.project(), "View")
        view_executable = self._make_mock_executable(view)
        with mock.patch("spine_engine.spine_engine.SpineEngine._make_item") as mock_make_item:
            mock_make_item.return_value = view_executable
            self.toolbox.project().execute_project()
            self._wait_for_execution_finished()
        self.assertTrue(view_executable.execute_called)

    def test_execute_project_with_two_dags(self):
        item1 = add_dc(self.toolbox.project(), "DC")
        item1_executable = self._make_mock_executable(item1)
        item2 = add_view(self.toolbox.project(), "View")
        item2_executable = self._make_mock_executable(item2)
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
        item1 = add_dc(self.toolbox.project(), "DC")
        item1_executable = self._make_mock_executable(item1)
        item2 = add_view(self.toolbox.project(), "View")
        item2_executable = self._make_mock_executable(item2)
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
        data_store = add_ds(self.toolbox.project(), "DS")
        data_store_executable = self._make_mock_executable(data_store)
        data_connection = add_dc(self.toolbox.project(), "DC")
        data_connection_executable = self._make_mock_executable(data_connection)
        view = add_view(self.toolbox.project(), "View")
        view_executable = self._make_mock_executable(view)
        self.toolbox.project().add_connection(Connection(data_store.name, "right", data_connection.name, "left"))
        self.toolbox.project().add_connection(Connection(data_connection.name, "bottom", view.name, "top"))
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

    def test_connections_for_item_no_connections(self):
        project = self.toolbox.project()
        dc_name = "DC"
        add_dc(project, dc_name)
        self.assertEqual(project.connections_for_item(dc_name), [])

    def test_connections_for_item(self):
        project = self.toolbox.project()
        dc1_name = "My first DC"
        add_dc(project, dc1_name)
        dc2_name = "My second DC"
        add_dc(project, dc2_name)
        dc3_name = "My third and last DC"
        add_dc(project, dc3_name)
        project.add_connection(Connection(dc1_name, "bottom", dc2_name, "top"))
        project.add_connection(Connection(dc2_name, "top", dc3_name, "bottom"))
        self.assertEqual(project.connections_for_item(dc1_name), [Connection(dc1_name, "bottom", dc2_name, "top")])
        self.assertEqual(
            project.connections_for_item(dc2_name),
            [Connection(dc1_name, "bottom", dc2_name, "top"), Connection(dc2_name, "top", dc3_name, "bottom")],
        )
        self.assertEqual(project.connections_for_item(dc3_name), [Connection(dc2_name, "top", dc3_name, "bottom")])

    def test_add_connection_updates_dag_handler(self):
        project = self.toolbox.project()
        dc_name = "DC"
        add_dc(project, dc_name)
        importer_name = "Importer"
        add_importer(project, importer_name)
        project.add_connection(Connection(dc_name, "right", importer_name, "left"))
        self.assertEqual(len(project.connections), 1)
        dag = project.dag_handler.dag_with_node(dc_name)
        self.assertEqual(project.dag_handler.node_successors(dag), {dc_name: [importer_name], importer_name: []})

    def test_add_connection_updates_resources(self):
        project = self.toolbox.project()
        dc_name = "DC"
        add_dc(project, dc_name)
        tool_name = "Tool"
        add_tool(project, tool_name)
        dc = project.get_item(dc_name)
        data_file = Path(self._temp_dir.name, "a.txt")
        data_file.touch()
        dc.add_data_files([data_file])
        tool = project.get_item(tool_name)
        self.assertEqual(tool._input_file_model.rowCount(), 0)
        project.add_connection(Connection(dc_name, "left", tool_name, "right"))
        self.assertEqual(tool._input_file_model.rowCount(), 1)

    def test_modifying_connected_item_updates_resources(self):
        project = self.toolbox.project()
        dc_name = "DC"
        add_dc(project, dc_name)
        tool_name = "Tool"
        add_tool(project, tool_name)
        tool = project.get_item(tool_name)
        project.add_connection(Connection(dc_name, "left", tool_name, "right"))
        self.assertEqual(tool._input_file_model.rowCount(), 0)
        dc = project.get_item(dc_name)
        data_file = Path(self._temp_dir.name, "a.txt")
        data_file.touch()
        dc.add_data_files([data_file])
        QApplication.processEvents()  # DC's file system watcher updates DC here
        self.assertEqual(tool._input_file_model.rowCount(), 1)

    def test_remove_connection(self):
        """Tests issue #1310"""
        # Make two DC's connected to a tool and provide a resource from both to Tool.
        # Remove one connection, and test that the other one still provides the resource to Tool
        project = self.toolbox.project()
        add_dc(project, "dc1")
        add_dc(project, "dc2")
        add_tool(project, "t")
        dc1 = project.get_item("dc1")
        dc2 = project.get_item("dc2")
        t = project.get_item("t")
        a = Path(self._temp_dir.name, "a.txt")
        a.touch()
        b = Path(self._temp_dir.name, "b.txt")
        b.touch()
        dc1.add_data_files([a])
        dc2.add_data_files([b])
        project.add_connection(Connection("dc1", "right", "t", "left"))
        project.add_connection(Connection("dc2", "right", "t", "left"))
        self.assertEqual(t._input_file_model.rowCount(), 2)  # There should 2 files in Available resources
        connection = project.find_connection("dc2", "t")
        project.remove_connection(connection)
        self.assertEqual(t._input_file_model.rowCount(), 1)  # There should 1 resource left

    def test_replace_connection(self):
        project = self.toolbox.project()
        dc1_name = "DC 1"
        add_dc(project, dc1_name)
        dc2_name = "DC 2"
        add_dc(project, dc2_name)
        project.add_connection(Connection(dc1_name, "left", dc2_name, "right"))
        project.replace_connection(
            Connection(dc1_name, "left", dc2_name, "right"), Connection(dc1_name, "top", dc2_name, "bottom")
        )
        self.assertEqual(project.connections_for_item(dc1_name), [Connection(dc1_name, "top", dc2_name, "bottom")])
        self.assertEqual(project.connections_for_item(dc2_name), [Connection(dc1_name, "top", dc2_name, "bottom")])
        dag = project.dag_handler.dag_with_node(dc1_name)
        self.assertEqual(project.dag_handler.node_successors(dag), {dc1_name: [dc2_name], dc2_name: []})

    def _make_mock_executable(self, item):
        item_name = item.name
        item = self.toolbox.project_item_model.get_item(item_name).project_item
        item_executable = _MockExecutableItem(item_name, self.toolbox.project().project_dir, self.toolbox)
        animation = QVariantAnimation()
        animation.setDuration(0)
        item.make_execution_leave_animation = mock.MagicMock(return_value=animation)
        return item_executable


class _MockExecutableItem(ExecutableItemBase):
    def __init__(self, name, project_dir, logger):
        super().__init__(name, project_dir, logger)
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
