######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""
import json
import os.path
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide6.QtCore import QVariantAnimation
from PySide6.QtWidgets import QApplication
import networkx as nx
from spine_engine.project_item.project_item_specification import ProjectItemSpecification
from spine_engine.spine_engine import ItemExecutionFinishState
from spine_engine.project_item.executable_item_base import ExecutableItemBase
from spine_engine.utils.helpers import shorten
from spinetoolbox.helpers import SignalWaiter
from spinetoolbox.project_item.project_item import ProjectItem
from spinetoolbox.project_item.project_item_factory import ProjectItemFactory
from spinetoolbox.project_item.logging_connection import LoggingConnection
from spinetoolbox.config import PROJECT_LOCAL_DATA_DIR_NAME, PROJECT_LOCAL_DATA_FILENAME
from spinetoolbox.project import node_successors
from tests.mock_helpers import (
    clean_up_toolbox,
    create_toolboxui_with_project,
    add_ds,
    add_dc,
    add_tool,
    add_view,
    add_importer,
    add_exporter,
    add_data_transformer,
    add_merger,
    qsettings_value_side_effect,
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

    @staticmethod
    def node_is_isolated(project, node):
        """Checks if the project item in given project with the given name has any connections.

        Args:
            project (SpineToolboxProject): Project with project items
            node (str): Project item name

        Returns:
            bool: True if node is isolated, False otherwise
        """
        g = project.dag_with_node(node)
        return nx.is_isolate(g, node)

    def test_add_data_store(self):
        name = "DS"
        add_ds(self.toolbox.project(), self.toolbox.item_factories, name)
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.item(found_index).project_item
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Data Store
        self.assertEqual(found_item.item_type(), "Data Store")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def check_dag_handler(self, name):
        """Checks that project dag handler contains only one
        graph, which has one node and its name matches the
        given argument."""
        dags = [dag for dag in self.toolbox.project()._dag_iterator()]
        self.assertTrue(len(dags) == 1)
        g = self.toolbox.project().dag_with_node(name)
        self.assertTrue(len(g.nodes()) == 1)
        for node_name in g.nodes():
            self.assertTrue(node_name == name)

    def test_add_data_connection(self):
        name = "DC"
        add_dc(self.toolbox.project(), self.toolbox.item_factories, name)
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.item(found_index).project_item
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Data Connection
        self.assertEqual(found_item.item_type(), "Data Connection")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_tool(self):
        name = "Tool"
        add_tool(self.toolbox.project(), self.toolbox.item_factories, name)
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.item(found_index).project_item
        self.assertEqual(found_item.name, name)
        # Check that the created item is a Tool
        self.assertEqual(found_item.item_type(), "Tool")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_view(self):
        name = "View"
        add_view(self.toolbox.project(), self.toolbox.item_factories, name)
        # Check that an item with the created name is found from project item model
        found_index = self.toolbox.project_item_model.find_item(name)
        found_item = self.toolbox.project_item_model.item(found_index).project_item
        self.assertEqual(found_item.name, name)
        # Check that the created item is a View
        self.assertEqual(found_item.item_type(), "View")
        # Check that dag handler has this and only this node
        self.check_dag_handler(name)

    def test_add_all_available_items(self):
        p = self.toolbox.project()
        ds_name = "DS"
        dc_name = "DC"
        dt_name = "DT"
        tool_name = "Tool"
        view_name = "View"
        imp_name = "Importer"
        exporter_name = "Exporter"
        merger_name = "Merger"
        add_ds(p, self.toolbox.item_factories, ds_name)
        add_dc(p, self.toolbox.item_factories, dc_name)
        add_data_transformer(p, self.toolbox.item_factories, dt_name)
        add_tool(p, self.toolbox.item_factories, tool_name)
        add_view(p, self.toolbox.item_factories, view_name)
        add_importer(p, self.toolbox.item_factories, imp_name)
        add_exporter(p, self.toolbox.item_factories, exporter_name)
        add_merger(p, self.toolbox.item_factories, merger_name)
        # Check that the items are found from project item model
        ds = p.get_item(ds_name)
        self.assertEqual(ds_name, ds.name)
        dc = p.get_item(dc_name)
        self.assertEqual(dc_name, dc.name)
        dt = p.get_item(dt_name)
        self.assertEqual(dt_name, dt.name)
        tool = p.get_item(tool_name)
        self.assertEqual(tool_name, tool.name)
        view = p.get_item(view_name)
        self.assertEqual(view_name, view.name)
        importer = p.get_item(imp_name)
        self.assertEqual(imp_name, importer.name)
        exporter = p.get_item(exporter_name)
        self.assertEqual(exporter_name, exporter.name)
        merger = p.get_item(merger_name)
        self.assertEqual(merger_name, merger.name)
        # DAG handler should now have eight graphs, each with one item
        dags = [dag for dag in self.toolbox.project()._dag_iterator()]
        self.assertEqual(8, len(dags))
        # Check that all created items are in graphs
        ds_graph = self.toolbox.project().dag_with_node(ds_name)
        self.assertIsNotNone(ds_graph)
        dc_graph = self.toolbox.project().dag_with_node(dc_name)
        self.assertIsNotNone(dc_graph)
        dt_graph = self.toolbox.project().dag_with_node(dt_name)
        self.assertIsNotNone(dt_graph)
        tool_graph = self.toolbox.project().dag_with_node(tool_name)
        self.assertIsNotNone(tool_graph)
        view_graph = self.toolbox.project().dag_with_node(view_name)
        self.assertIsNotNone(view_graph)
        importer_graph = self.toolbox.project().dag_with_node(imp_name)
        self.assertIsNotNone(importer_graph)
        exporter_graph = self.toolbox.project().dag_with_node(exporter_name)
        self.assertIsNotNone(exporter_graph)
        merger_graph = self.toolbox.project().dag_with_node(merger_name)
        self.assertIsNotNone(merger_graph)

    def test_remove_item_by_name(self):
        view_name = "View"
        add_view(self.toolbox.project(), self.toolbox.item_factories, view_name)
        view = self.toolbox.project_item_model.get_item(view_name)
        self.assertEqual(view_name, view.name)
        self.toolbox.project().remove_item_by_name(view_name)
        self.assertEqual(self.toolbox.project_item_model.n_items(), 0)

    def test_remove_item_by_name_removes_outgoing_connections(self):
        project = self.toolbox.project()
        view1_name = "View 1"
        add_view(project, self.toolbox.item_factories, view1_name)
        view2_name = "View 2"
        add_view(project, self.toolbox.item_factories, view2_name)
        project.add_connection(LoggingConnection(view1_name, "top", view2_name, "bottom", toolbox=self.toolbox))
        view = self.toolbox.project_item_model.get_item(view1_name)
        self.assertEqual(view1_name, view.name)
        view = self.toolbox.project_item_model.get_item(view2_name)
        self.assertEqual(view2_name, view.name)
        self.assertEqual(self.toolbox.project_item_model.n_items(), 2)
        self.assertEqual(len(project.connections), 1)
        project.remove_item_by_name(view1_name)
        self.assertEqual(self.toolbox.project_item_model.n_items(), 1)
        self.assertEqual(len(project.connections), 0)
        view = self.toolbox.project_item_model.get_item(view2_name)
        self.assertEqual(view2_name, view.name)
        self.assertTrue(self.node_is_isolated(project, view2_name))

    def test_remove_item_by_name_removes_incoming_connections(self):
        project = self.toolbox.project()
        view1_name = "View 1"
        add_view(project, self.toolbox.item_factories, view1_name)
        view2_name = "View 2"
        add_view(project, self.toolbox.item_factories, view2_name)
        project.add_connection(LoggingConnection(view1_name, "top", view2_name, "bottom", toolbox=self.toolbox))
        view = self.toolbox.project_item_model.get_item(view1_name)
        self.assertEqual(view1_name, view.name)
        view = self.toolbox.project_item_model.get_item(view2_name)
        self.assertEqual(view2_name, view.name)
        self.assertEqual(self.toolbox.project_item_model.n_items(), 2)
        self.assertEqual(len(project.connections), 1)
        project.remove_item_by_name(view2_name)
        self.assertEqual(self.toolbox.project_item_model.n_items(), 1)
        self.assertEqual(len(project.connections), 0)
        view = self.toolbox.project_item_model.get_item(view1_name)
        self.assertEqual(view1_name, view.name)
        self.assertTrue(self.node_is_isolated(project, view1_name))

    def _execute_project(self, names=None):
        """Executes only the selected items or the whole project.

        Args:
            names (list): List of selected item names to execute, or None to execute the whole project.
        """
        waiter = SignalWaiter()
        self.toolbox.project().project_execution_finished.connect(waiter.trigger)
        with mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value, mock.patch(
            "spinetoolbox.project.make_settings_dict_for_engine"
        ) as mock_settings_dict:
            # Make sure that the test uses LocalSpineEngineManager
            # This mocks the check for engineSettings/remoteEngineEnabled in SpineToolboxProject.execute_dags()
            mock_qsettings_value.side_effect = qsettings_value_side_effect
            # This mocks the call to make_settings_dict_for_engine in SpineToolboxProject._execute_dags()
            mock_settings_dict.return_value = dict()
            if not names:
                self.toolbox.project().execute_project()
            else:
                self.toolbox.project().execute_selected(names)
            mock_qsettings_value.assert_called()
            mock_settings_dict.assert_called()
        waiter.wait()
        self.toolbox.project().project_execution_finished.disconnect(waiter.trigger)

    def test_execute_project_with_single_item(self):
        view = add_view(self.toolbox.project(), self.toolbox.item_factories, "View")
        view_executable = self._make_mock_executable(view)
        with mock.patch("spine_engine.spine_engine.SpineEngine.make_item") as mock_make_item:
            mock_make_item.return_value = view_executable
            self._execute_project()
        self.assertTrue(view_executable.execute_called)

    def test_execute_project_with_two_dags(self):
        item1 = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC")
        item1_executable = self._make_mock_executable(item1)
        item2 = add_view(self.toolbox.project(), self.toolbox.item_factories, "View")
        item2_executable = self._make_mock_executable(item2)
        with mock.patch("spine_engine.spine_engine.SpineEngine.make_item") as mock_make_item:
            mock_make_item.side_effect = lambda name, *args, **kwargs: {
                item1.name: item1_executable,
                item2.name: item2_executable,
            }[name]
            self._execute_project()
        self.assertTrue(item1_executable.execute_called)
        self.assertTrue(item2_executable.execute_called)

    def test_execute_selected_dag(self):
        item1 = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC")
        item1_executable = self._make_mock_executable(item1)
        item2 = add_view(self.toolbox.project(), self.toolbox.item_factories, "View")
        item2_executable = self._make_mock_executable(item2)
        with mock.patch("spine_engine.spine_engine.SpineEngine.make_item") as mock_make_item:
            mock_make_item.side_effect = lambda name, *args, **kwargs: {
                item1.name: item1_executable,
                item2.name: item2_executable,
            }[name]
            self._execute_project(["View"])
        self.assertFalse(item1_executable.execute_called)
        self.assertTrue(item2_executable.execute_called)

    def test_execute_selected_item_within_single_dag(self):
        data_store = add_ds(self.toolbox.project(), self.toolbox.item_factories, "DS")
        data_store_executable = self._make_mock_executable(data_store)
        data_connection = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC")
        data_connection_executable = self._make_mock_executable(data_connection)
        view = add_view(self.toolbox.project(), self.toolbox.item_factories, "View")
        view_executable = self._make_mock_executable(view)
        self.toolbox.project().add_connection(
            LoggingConnection(data_store.name, "right", data_connection.name, "left", toolbox=self.toolbox)
        )
        self.toolbox.project().add_connection(
            LoggingConnection(data_connection.name, "bottom", view.name, "top", toolbox=self.toolbox)
        )
        with mock.patch("spine_engine.spine_engine.SpineEngine.make_item") as mock_make_item:
            mock_make_item.side_effect = lambda name, *args, **kwargs: {
                data_store.name: data_store_executable,
                data_connection.name: data_connection_executable,
                view.name: view_executable,
            }[name]
            self._execute_project(["DC"])
        self.assertFalse(data_store_executable.execute_called)
        self.assertTrue(data_connection_executable.execute_called)
        self.assertFalse(view_executable.execute_called)

    def test_execute_selected_items_within_single_dag(self):
        dc1 = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC1")
        dc1_executable = self._make_mock_executable(dc1)
        dc2 = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC2")
        dc2_executable = self._make_mock_executable(dc2)
        dc3 = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC3")
        dc3_executable = self._make_mock_executable(dc3)
        dc4 = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC4")
        dc4_executable = self._make_mock_executable(dc4)
        dc5 = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC5")
        dc5_executable = self._make_mock_executable(dc5)
        self.toolbox.project().add_connection(
            LoggingConnection(dc1.name, "right", dc2.name, "left", toolbox=self.toolbox)
        )
        self.toolbox.project().add_connection(
            LoggingConnection(dc2.name, "bottom", dc3.name, "top", toolbox=self.toolbox)
        )
        self.toolbox.project().add_connection(
            LoggingConnection(dc1.name, "right", dc4.name, "left", toolbox=self.toolbox)
        )
        self.toolbox.project().add_connection(
            LoggingConnection(dc4.name, "right", dc5.name, "left", toolbox=self.toolbox)
        )
        # DAG contains 5 items and 4 connections. dc1->dc2->dc3 and dc1->dc4->dc5.
        # Test selected execution when dc3 and dc5 are selected. The items are not connected, so the DAG should
        # be split into two DAG's before invoking SpineEngineWorker.
        with mock.patch("spine_engine.spine_engine.SpineEngine.make_item") as mock_make_item:
            mock_make_item.side_effect = lambda name, *args, **kwargs: {
                dc1.name: dc1_executable,
                dc2.name: dc2_executable,
                dc3.name: dc3_executable,
                dc4.name: dc4_executable,
                dc5.name: dc5_executable,
            }[name]
            self._execute_project(["DC3", "DC5"])
            self.assertTrue(dc3_executable.execute_called)
            self.assertTrue(dc5_executable.execute_called)

    def test_executing_cyclic_dag_fails_graciously(self):
        item1 = add_dc(self.toolbox.project(), self.toolbox.item_factories, "DC")
        item2 = add_view(self.toolbox.project(), self.toolbox.item_factories, "View")
        self.toolbox.project().add_connection(
            LoggingConnection(item1.name, "right", item2.name, "left", toolbox=self.toolbox)
        )
        self.toolbox.project().add_connection(
            LoggingConnection(item2.name, "bottom", item1.name, "top", toolbox=self.toolbox)
        )
        self.toolbox.project().execute_project()
        self.assertFalse(self.toolbox.project()._execution_in_progress)

    def test_rename_project(self):
        new_name = "New Project Name"
        new_short_name = "new_project_name"
        with mock.patch("spinetoolbox.ui_main.ToolboxUI.update_recent_projects"):
            self.toolbox.project().set_name(new_name)
        self.assertEqual(self.toolbox.project().name, new_name)
        self.assertEqual(self.toolbox.project().short_name, new_short_name)

    def test_set_project_description(self):
        desc = "Project Description"
        self.toolbox.project().set_description(desc)
        self.assertEqual(self.toolbox.project().description, desc)

    def test_rename_item(self):
        project = self.toolbox.project()
        source_name = "source"
        destination_name = "destination"
        add_view(project, self.toolbox.item_factories, source_name)
        add_view(project, self.toolbox.item_factories, destination_name)
        source_item = project.get_item("source")
        project.add_connection(LoggingConnection(source_name, "left", destination_name, "right", toolbox=self.toolbox))
        project.rename_item("source", "renamed source", "")
        self.assertTrue(bool(project.get_item("renamed source")))
        self.assertEqual(source_item.name, "renamed source")
        self.assertEqual(
            project.connections,
            [LoggingConnection("renamed source", "left", destination_name, "right", toolbox=self.toolbox)],
        )
        dags = [dag for dag in project._dag_iterator()]
        self.assertEqual(len(dags), 1)
        self.assertEqual(node_successors(dags[0]), {"destination": [], "renamed source": ["destination"]})
        self.assertEqual(source_item.get_icon().name(), "renamed source")
        self.assertEqual(os.path.split(source_item.data_dir)[1], shorten("renamed source"))

    def test_connections_for_item_no_connections(self):
        project = self.toolbox.project()
        dc_name = "DC"
        add_dc(project, self.toolbox.item_factories, dc_name)
        self.assertEqual(project.connections_for_item(dc_name), [])

    def test_connections_for_item(self):
        project = self.toolbox.project()
        dc1_name = "My first DC"
        add_dc(project, self.toolbox.item_factories, dc1_name)
        dc2_name = "My second DC"
        add_dc(project, self.toolbox.item_factories, dc2_name)
        dc3_name = "My third and last DC"
        add_dc(project, self.toolbox.item_factories, dc3_name)
        project.add_connection(LoggingConnection(dc1_name, "bottom", dc2_name, "top", toolbox=self.toolbox))
        project.add_connection(LoggingConnection(dc2_name, "top", dc3_name, "bottom", toolbox=self.toolbox))
        self.assertEqual(
            project.connections_for_item(dc1_name),
            [LoggingConnection(dc1_name, "bottom", dc2_name, "top", toolbox=self.toolbox)],
        )
        self.assertEqual(
            project.connections_for_item(dc2_name),
            [
                LoggingConnection(dc1_name, "bottom", dc2_name, "top", toolbox=self.toolbox),
                LoggingConnection(dc2_name, "top", dc3_name, "bottom", toolbox=self.toolbox),
            ],
        )
        self.assertEqual(
            project.connections_for_item(dc3_name),
            [LoggingConnection(dc2_name, "top", dc3_name, "bottom", toolbox=self.toolbox)],
        )

    def test_add_connection_updates_dag_handler(self):
        project = self.toolbox.project()
        dc_name = "DC"
        add_dc(project, self.toolbox.item_factories, dc_name)
        importer_name = "Importer"
        add_importer(project, self.toolbox.item_factories, importer_name)
        project.add_connection(LoggingConnection(dc_name, "right", importer_name, "left", toolbox=self.toolbox))
        self.assertEqual(len(project.connections), 1)
        dag = project.dag_with_node(dc_name)
        self.assertEqual(node_successors(dag), {dc_name: [importer_name], importer_name: []})

    def test_add_connection_updates_resources(self):
        project = self.toolbox.project()
        dc_name = "DC"
        add_dc(project, self.toolbox.item_factories, dc_name)
        tool_name = "Tool"
        add_tool(project, self.toolbox.item_factories, tool_name)
        dc = project.get_item(dc_name)
        data_file = Path(self._temp_dir.name, "a.txt")
        data_file.touch()
        dc.add_data_files([data_file])
        tool = project.get_item(tool_name)
        self.assertEqual(tool._input_file_model.rowCount(), 0)
        project.add_connection(LoggingConnection(dc_name, "left", tool_name, "right", toolbox=self.toolbox))
        self.assertEqual(tool._input_file_model.rowCount(), 1)

    def test_modifying_connected_item_updates_resources(self):
        project = self.toolbox.project()
        dc_name = "DC"
        add_dc(project, self.toolbox.item_factories, dc_name)
        tool_name = "Tool"
        add_tool(project, self.toolbox.item_factories, tool_name)
        tool = project.get_item(tool_name)
        project.add_connection(LoggingConnection(dc_name, "left", tool_name, "right", toolbox=self.toolbox))
        self.assertEqual(tool._input_file_model.rowCount(), 0)
        dc = project.get_item(dc_name)
        data_file = Path(self._temp_dir.name, "a.txt")
        data_file.touch()
        dc.add_data_files([data_file])
        while dc.data_model.rowCount() == 0:
            QApplication.processEvents()  # DC's file system watcher updates DC here
        self.assertEqual(tool._input_file_model.rowCount(), 1)

    def test_removing_connection_does_not_break_available_resources(self):
        # Tests issue #1310.
        # Make two DC's connected to a tool and provide a resource from both to Tool.
        # Remove one connection, and test that the other one still provides the resource to Tool
        project = self.toolbox.project()
        add_dc(project, self.toolbox.item_factories, "dc1")
        add_dc(project, self.toolbox.item_factories, "dc2")
        add_tool(project, self.toolbox.item_factories, "t")
        dc1 = project.get_item("dc1")
        dc2 = project.get_item("dc2")
        t = project.get_item("t")
        a = Path(self._temp_dir.name, "a.txt")
        a.touch()
        b = Path(self._temp_dir.name, "b.txt")
        b.touch()
        dc1.add_data_files([a])
        dc2.add_data_files([b])
        project.add_connection(LoggingConnection("dc1", "right", "t", "left", toolbox=self.toolbox))
        project.add_connection(LoggingConnection("dc2", "right", "t", "left", toolbox=self.toolbox))
        self.assertEqual(t._input_file_model.rowCount(), 2)  # There should be 2 files in Available resources
        connection = project.find_connection("dc2", "t")
        project.remove_connection(connection)
        self.assertEqual(t._input_file_model.rowCount(), 1)  # There should be 1 resource left

    def test_update_connection(self):
        project = self.toolbox.project()
        dc1_name = "DC 1"
        add_dc(project, self.toolbox.item_factories, dc1_name)
        dc2_name = "DC 2"
        add_dc(project, self.toolbox.item_factories, dc2_name)
        conn = LoggingConnection(dc1_name, "left", dc2_name, "right", toolbox=self.toolbox)
        project.add_connection(conn)
        project.update_connection(conn, "top", "bottom")
        self.assertEqual(
            project.connections_for_item(dc1_name),
            [LoggingConnection(dc1_name, "top", dc2_name, "bottom", toolbox=self.toolbox)],
        )
        self.assertEqual(
            project.connections_for_item(dc2_name),
            [LoggingConnection(dc1_name, "top", dc2_name, "bottom", toolbox=self.toolbox)],
        )
        dag = project.dag_with_node(dc1_name)
        self.assertEqual(node_successors(dag), {dc1_name: [dc2_name], dc2_name: []})

    def test_save_when_storing_item_local_data(self):
        project = self.toolbox.project()
        item = _MockItemWithLocalData(project)
        with mock.patch.object(self.toolbox, "project_item_properties_ui"), mock.patch.object(
            self.toolbox, "project_item_icon"
        ):
            project.add_item(item)
        project.save()
        with open(project.config_file) as fp:
            project_dict = json.load(fp)
        self.assertEqual(
            project_dict,
            {
                "items": {"test item": {"type": "Tester", "a": {"c": 2}}},
                "project": {
                    "connections": [],
                    "description": "",
                    "jumps": [],
                    "settings": {"enable_execute_all": True},
                    "specifications": {},
                    "version": 11,
                },
            },
        )
        with Path(project.config_dir, PROJECT_LOCAL_DATA_DIR_NAME, PROJECT_LOCAL_DATA_FILENAME).open() as fp:
            local_data_dict = json.load(fp)
        self.assertEqual(local_data_dict, {'items': {'test item': {'a': {'b': 1, 'd': 3}}}})

    def test_load_when_storing_item_local_data(self):
        project = self.toolbox.project()
        item = _MockItemWithLocalData(project)
        with mock.patch.object(self.toolbox, "project_item_properties_ui"), mock.patch.object(
            self.toolbox, "project_item_icon"
        ):
            project.add_item(item)
        project.save()
        self.assertTrue(self.toolbox.close_project(ask_confirmation=False))
        self.toolbox.item_factories = {"Tester": _MockItemFactoryForLocalDataTests()}
        with mock.patch.object(self.toolbox, "update_recent_projects"), mock.patch.object(
            self.toolbox, "project_item_properties_ui"
        ), mock.patch.object(self.toolbox, "project_item_icon"):
            self.assertTrue(self.toolbox.restore_project(self._temp_dir.name, ask_confirmation=False))
        item = self.toolbox.project().get_item("test item")
        self.assertEqual(item.kwargs, {"type": "Tester", "a": {"b": 1, "c": 2, "d": 3}})

    def test_add_and_save_specification(self):
        project = self.toolbox.project()
        specification = _MockSpecification(
            "a specification", "Specification for testing.", "Tester", "Testing category"
        )
        project.add_specification(specification)
        self.assertTrue(specification.is_equivalent(project.get_specification("a specification")))
        specification_dir = Path(self._temp_dir.name) / ".spinetoolbox" / "specifications" / "Tester"
        self.assertTrue(specification_dir.exists())
        specification_file = specification_dir / (specification.short_name + ".json")
        self.assertEqual(specification_file, Path(specification.definition_file_path))
        self.assertTrue(specification_file.exists())
        with open(specification_file) as specification_input:
            specification_dict = json.load(specification_input)
        self.assertEqual(specification_dict, specification.to_dict())
        local_data_dir = Path(self._temp_dir.name) / ".spinetoolbox" / "local"
        self.assertFalse(local_data_dir.exists())

    def test_add_and_save_specification_with_local_data(self):
        project = self.toolbox.project()
        specification = _MockSpecificationWithLocalData(
            "a specification", "Specification for testing.", "Tester", "Testing category", "my precious data"
        )
        project.add_specification(specification)
        self.assertTrue(specification.is_equivalent(project.get_specification("a specification")))
        specification_dir = Path(self._temp_dir.name) / ".spinetoolbox" / "specifications" / "Tester"
        self.assertTrue(specification_dir.exists())
        specification_file = specification_dir / (specification.short_name + ".json")
        self.assertEqual(specification_file, Path(specification.definition_file_path))
        self.assertTrue(specification_file.exists())
        with open(specification_file) as specification_input:
            specification_dict = json.load(specification_input)
        expected = specification.to_dict()
        expected.pop("data")
        self.assertEqual(specification_dict, expected)
        local_data_dir = Path(self._temp_dir.name) / ".spinetoolbox" / "local"
        self.assertTrue(local_data_dir.exists())
        local_data_file = local_data_dir / "specification_local_data.json"
        self.assertTrue(local_data_file.exists())
        with open(local_data_file) as data_input:
            local_data = json.load(data_input)
        self.assertEqual(local_data, {"Tester": {"a specification": {"data": "my precious data"}}})

    def test_renaming_specification_with_local_data_updates_local_data_file(self):
        project = self.toolbox.project()
        original_specification = _MockSpecificationWithLocalData(
            "a specification", "Specification for testing.", "Tester", "Testing category", "my precious data"
        )
        project.add_specification(original_specification)
        local_data_file = Path(self._temp_dir.name) / ".spinetoolbox" / "local" / "specification_local_data.json"
        self.assertTrue(local_data_file.exists())
        specification = _MockSpecificationWithLocalData(
            "another specification", "Specification for testing.", "Tester", "Testing category", "my precious data"
        )
        project.replace_specification("a specification", specification)
        specification_dir = Path(self._temp_dir.name) / ".spinetoolbox" / "specifications" / "Tester"
        self.assertTrue(specification_dir.exists())
        specification_file = specification_dir / (specification.short_name + ".json")
        self.assertEqual(specification_file, Path(specification.definition_file_path))
        self.assertTrue(specification_file.exists())
        self.assertTrue(Path(original_specification.definition_file_path).exists())
        with open(specification_file) as specification_input:
            specification_dict = json.load(specification_input)
        expected = specification.to_dict()
        expected.pop("data")
        self.assertEqual(specification_dict, expected)
        with open(local_data_file) as data_input:
            local_data = json.load(data_input)
        self.assertEqual(local_data, {"Tester": {"another specification": {"data": "my precious data"}}})

    def test_replace_specification_with_local_data_by_one_without_removes_local_data_from_the_file(self):
        project = self.toolbox.project()
        specification_with_local_data = _MockSpecificationWithLocalData(
            "a specification", "Specification for testing.", "Tester", "Testing category", "my precious data"
        )
        project.add_specification(specification_with_local_data)
        local_data_file = Path(self._temp_dir.name) / ".spinetoolbox" / "local" / "specification_local_data.json"
        self.assertTrue(local_data_file.exists())
        specification = _MockSpecification(
            "another specification", "Specification without local data", "Tester", "Testing category"
        )
        project.replace_specification("a specification", specification)
        specification_dir = Path(self._temp_dir.name) / ".spinetoolbox" / "specifications" / "Tester"
        self.assertTrue(specification_dir.exists())
        specification_file = specification_dir / (specification.short_name + ".json")
        self.assertEqual(specification_file, Path(specification.definition_file_path))
        self.assertTrue(specification_file.exists())
        with open(specification_file) as specification_input:
            specification_dict = json.load(specification_input)
        self.assertEqual(specification_dict, specification.to_dict())
        with open(local_data_file) as data_input:
            local_data = json.load(data_input)
        self.assertEqual(local_data, {})

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

    def ready_to_execute(self, _settings):
        return True

    def execute(self, _forward_resources, _backward_resources, lock):
        self.execute_called = True
        return ItemExecutionFinishState.SUCCESS

    @classmethod
    def from_dict(cls, item_dict, name, project_dir, app_settings, specifications, logger):
        raise NotImplementedError()


class _MockItemWithLocalData(ProjectItem):
    def __init__(self, project, **kwargs):
        super().__init__("test item", "a mock item for testing project items' local data", 0.0, 0.0, project)
        self.kwargs = kwargs

    def item_dict(self):
        return {"type": self.item_type(), "a": {"b": 1, "c": 2, "d": 3}}

    @staticmethod
    def item_dict_local_entries():
        return [("a", "b"), ("a", "d")]

    @staticmethod
    def item_type():
        return "Tester"

    @staticmethod
    def item_category():
        return "Tools"

    def set_rank(self, rank):
        pass

    def set_icon(self, icon):
        return


class _MockItemFactoryForLocalDataTests(ProjectItemFactory):
    @staticmethod
    def make_item(name, item_dict, toolbox, project):
        return _MockItemWithLocalData(project, **item_dict)


class _MockSpecification(ProjectItemSpecification):
    def to_dict(self):
        return {"name": self.name, "description": self.description}

    def is_equivalent(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.name == other.name and self.item_type == other.item_type and self.description == other.description


class _MockSpecificationWithLocalData(ProjectItemSpecification):
    def __init__(self, name, description, item_type, item_category, local_data):
        super().__init__(name, description, item_type, item_category)
        self._local_data = local_data

    def to_dict(self):
        return {"name": self.name, "description": self.description, "data": self._local_data}

    def is_equivalent(self, other):
        if not isinstance(other, type(self)):
            return False
        return (
            self.name == other.name
            and self.item_type == other.item_type
            and self.description == other.description
            and self._local_data == other._local_data
        )

    @staticmethod
    def _definition_local_entries():
        return [("data",)]


if __name__ == '__main__':
    unittest.main()
