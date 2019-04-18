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
Unit tests for ToolboxUI class.

:author: P. Savolainen (VTT)
:date:   22.8.2018
"""

import unittest
from unittest import mock
import logging
import os
import sys
from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtCore import SIGNAL, Qt
from ui_main import ToolboxUI
from project import SpineToolboxProject
from test.mock_helpers import MockQWidget, qsettings_value_side_effect


# noinspection PyUnusedLocal
class TestToolboxUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def setUp(self):
        """Overridden method. Runs before each test. Makes an instance of ToolboxUI class
        without opening previous project."""
        with mock.patch("ui_main.JuliaREPLWidget") as mock_julia_repl, \
                mock.patch("ui_main.PythonReplWidget") as mock_python_repl, \
                mock.patch("ui_main.QSettings.value") as mock_qsettings_value:
            # Replace Julia and Python REPLs with a QWidget so that the DeprecationWarning from qtconsole is not printed
            mock_julia_repl.return_value = QWidget()
            mock_python_repl.return_value = MockQWidget()  # Hack, because QWidget does not have test_push_vars()
            mock_qsettings_value.side_effect = qsettings_value_side_effect  # override 'open previous project' setting
            self.toolbox = ToolboxUI()

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.toolbox.deleteLater()
        self.toolbox = None

    def test_init_project_item_model_without_project(self):
        """Test that a new project item model contains 4 items (Data Stores, Data Connections, Tools, and Views).
        Note: This test is done WITHOUT a project open.
        """
        self.assertIsNone(self.toolbox.project())  # Make sure that there is no project open
        self.toolbox.init_project_item_model()
        self.check_init_project_item_model()

    def test_init_project_item_model_with_project(self):
        """Test that a new project item model contains 4 items (Data Stores, Data Connections, Tools, and Views).
        Note: This test is done WITH a project.
        Mock save_project() and create_dir() so that .proj file and project directory (and work directory) are
        not actually created.
        """
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, \
                mock.patch("project.create_dir") as mock_create_dir:
            self.toolbox.create_project("Unit Test Project", "Project for unit tests.")
        self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)  # Check that a project is open
        self.toolbox.init_project_item_model()
        self.check_init_project_item_model()

    def check_init_project_item_model(self):
        """Checks that category items are created as expected."""
        n = self.toolbox.project_item_model.rowCount()
        self.assertEqual(n, 4)
        # Check that there's only one column
        self.assertEqual(self.toolbox.project_item_model.columnCount(), 1)
        # Check that the items DisplayRoles are (In this particular order)
        item1 = self.toolbox.project_item_model.root().child(0)
        self.assertTrue(item1.name == "Data Stores", "Item on row 0 is not 'Data Stores'")
        self.assertTrue(item1.parent().is_root, "Parent item of category item on row 0 should be root")
        item2 = self.toolbox.project_item_model.root().child(1)
        self.assertTrue(item2.name == "Data Connections", "Item on row 1 is not 'Data Connections'")
        self.assertTrue(item2.parent().is_root, "Parent item of category item on row 1 should be root")
        item3 = self.toolbox.project_item_model.root().child(2)
        self.assertTrue(item3.name == "Tools", "Item on row 2 is not 'Tools'")
        self.assertTrue(item3.parent().is_root, "Parent item of category item on row 2 should be root")
        item4 = self.toolbox.project_item_model.root().child(3)
        self.assertTrue(item4.name == "Views", "Item on row 3 is not 'Views'")
        self.assertTrue(item4.parent().is_root, "Parent item of category item on row 3 should be root")

    def test_init_tool_template_model(self):
        """Check that tool template model has no items after init and that
        signals are connected just once.
        """
        self.assertIsNone(self.toolbox.project())  # Make sure that there is no project open
        self.toolbox.init_tool_template_model(list())
        self.assertEqual(self.toolbox.tool_template_model.rowCount(), 0)
        # Test that QLisView signals are connected only once.
        n_dbl_clicked_recv = self.toolbox.ui.listView_tool_templates.receivers(SIGNAL("doubleClicked(QModelIndex)"))
        self.assertEqual(n_dbl_clicked_recv, 1)
        n_context_menu_recv = self.toolbox.ui.listView_tool_templates.\
            receivers(SIGNAL("customContextMenuRequested(QPoint)"))
        self.assertEqual(n_context_menu_recv, 1)
        # Initialize ToolTemplateModel again and see that the signals are connected only once
        self.toolbox.init_tool_template_model(list())
        # Test that QLisView signals are connected only once.
        n_dbl_clicked_recv = self.toolbox.ui.listView_tool_templates.receivers(SIGNAL("doubleClicked(QModelIndex)"))
        self.assertEqual(n_dbl_clicked_recv, 1)
        n_context_menu_recv = self.toolbox.ui.listView_tool_templates.\
            receivers(SIGNAL("customContextMenuRequested(QPoint)"))
        self.assertEqual(n_context_menu_recv, 1)
        # Check that there's still no items in the model
        self.assertEqual(self.toolbox.tool_template_model.rowCount(), 0)

    def test_init_connection_model(self):
        """Test that ConnectionModel is empty when initialized."""
        self.assertIsNone(self.toolbox.project())  # Make sure that there is no project open
        self.toolbox.init_connection_model()
        rows = self.toolbox.connection_model.rowCount()
        columns = self.toolbox.connection_model.columnCount()
        self.assertEqual(rows, 0)
        self.assertEqual(columns, 0)

    def test_create_project(self):
        """Test that create_project method makes a SpineToolboxProject instance.
        Skips creating a .proj file and creating directories.
        """
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, \
                mock.patch("project.create_dir") as mock_create_dir:
            self.toolbox.create_project("Unit Test Project", "Project for unit tests.")
        self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)  # Check that a project is open

    def test_open_project(self):
        """Test that opening a project file works.
        The project should contain four items. Data Store 'a',
        Data Connection 'b', Tool 'c', and View 'd'. The items are connected
        a->b->c->d.
        """
        load_path = os.path.join(os.getcwd(), "project_files", "unit_test_project.proj")
        self.assertIsNone(self.toolbox.project())
        with mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, \
                mock.patch("project.create_dir") as mock_create_dir, \
                mock.patch("data_store.create_dir") as mock_create_dir, \
                mock.patch("data_connection.create_dir") as mock_create_dir, \
                mock.patch("tool.create_dir") as mock_create_dir, \
                mock.patch("view.create_dir") as mock_create_dir:
            self.toolbox.open_project(load_path)
        self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)
        # Check that project contains four items
        self.assertEqual(self.toolbox.project_item_model.n_items(), 4)
        # Check that connection model has four rows and columns
        rows = self.toolbox.connection_model.rowCount()
        columns = self.toolbox.connection_model.columnCount()
        self.assertEqual(rows, 4)
        self.assertEqual(columns, 4)
        # Check that connection model headers are equal and they are in order a, b, c, d
        # Note: orientation is not actually used in headerData (on purpose)
        self.assertEqual(self.toolbox.connection_model.headerData(0, Qt.Vertical, role=Qt.DisplayRole), "a")
        self.assertEqual(self.toolbox.connection_model.headerData(1, Qt.Vertical, role=Qt.DisplayRole), "b")
        self.assertEqual(self.toolbox.connection_model.headerData(2, Qt.Vertical, role=Qt.DisplayRole), "c")
        self.assertEqual(self.toolbox.connection_model.headerData(3, Qt.Vertical, role=Qt.DisplayRole), "d")
        self.assertEqual(self.toolbox.connection_model.headerData(0, Qt.Horizontal, role=Qt.DisplayRole), "a")
        self.assertEqual(self.toolbox.connection_model.headerData(1, Qt.Horizontal, role=Qt.DisplayRole), "b")
        self.assertEqual(self.toolbox.connection_model.headerData(2, Qt.Horizontal, role=Qt.DisplayRole), "c")
        self.assertEqual(self.toolbox.connection_model.headerData(3, Qt.Horizontal, role=Qt.DisplayRole), "d")
        # Check input and output items of each project item
        a_inputs = self.toolbox.connection_model.input_items("a")  # []
        b_inputs = self.toolbox.connection_model.input_items("b")  # [a]
        c_inputs = self.toolbox.connection_model.input_items("c")  # [b]
        d_inputs = self.toolbox.connection_model.input_items("d")  # [c]
        a_outputs = self.toolbox.connection_model.output_items("a")  # [b]
        b_outputs = self.toolbox.connection_model.output_items("b")  # [c]
        c_outputs = self.toolbox.connection_model.output_items("c")  # [d]
        d_outputs = self.toolbox.connection_model.output_items("d")  # []
        # Input items
        self.assertEqual(len(a_inputs), 0)
        self.assertEqual(len(b_inputs), 1)
        self.assertEqual(b_inputs[0], "a")
        self.assertEqual(len(c_inputs), 1)
        self.assertEqual(c_inputs[0], "b")
        self.assertEqual(len(d_inputs), 1)
        self.assertEqual(d_inputs[0], "c")
        # Output items
        self.assertEqual(len(a_outputs), 1)
        self.assertEqual(a_outputs[0], "b")
        self.assertEqual(len(b_outputs), 1)
        self.assertEqual(b_outputs[0], "c")
        self.assertEqual(len(c_outputs), 1)
        self.assertEqual(c_outputs[0], "d")
        self.assertEqual(len(d_outputs), 0)
        # Check that DAG graph is correct
        dag_hndlr = self.toolbox.project().dag_handler
        self.assertTrue(len(dag_hndlr.dags()) == 1)  # Only one graph
        g = dag_hndlr.dags()[0]
        self.assertTrue(len(g.nodes()) == 4)  # graph has four nodes
        self.assertTrue(len(g.edges()) == 3)  # graph has three edges
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_node("b"))
        self.assertTrue(g.has_node("c"))
        self.assertTrue(g.has_node("d"))
        self.assertTrue(g.has_edge("a", "b"))
        self.assertTrue(g.has_edge("b", "c"))
        self.assertTrue(g.has_edge("c", "d"))

    @unittest.skip("TODO")
    def test_remove_item(self):
        self.fail()

    @unittest.skip("TODO")
    def test_add_tool_template(self):
        self.fail()

    @unittest.skip("TODO")
    def test_remove_tool_template(self):
        self.fail()


if __name__ == '__main__':
    unittest.main()
