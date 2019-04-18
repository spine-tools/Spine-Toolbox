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
Unit tests for DirectedGraphHandler class.

:author: P. Savolainen (VTT)
:date:   18.4.2019
"""

import unittest
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication, QWidget
import networkx as nx
from ui_main import ToolboxUI
from project import SpineToolboxProject
from executioner import DirectedGraphHandler
from test.mock_helpers import MockQWidget, qsettings_value_side_effect


class TestDirectedGraphHandler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def setUp(self):
        """Runs before each test. Makes an instance of ToolboxUI class.
        We want the ToolboxUI to start with the default settings and without a project
        """
        with mock.patch("ui_main.JuliaREPLWidget") as mock_julia_repl, \
                mock.patch("ui_main.PythonReplWidget") as mock_python_repl, \
                mock.patch("project.create_dir") as mock_create_dir, \
                mock.patch("ui_main.ToolboxUI.save_project") as mock_save_project, \
                mock.patch("ui_main.QSettings.value") as mock_qsettings_value:
            # Replace Julia REPL Widget with a QWidget so that the DeprecationWarning from qtconsole is not printed
            mock_julia_repl.return_value = QWidget()
            mock_python_repl.return_value = MockQWidget()
            mock_qsettings_value.side_effect = qsettings_value_side_effect
            self.toolbox = ToolboxUI()
            self.toolbox.create_project("UnitTest Project", "")
            self.dag_handler = DirectedGraphHandler(self.toolbox)

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        self.toolbox.deleteLater()
        self.toolbox = None
        self.dag_handler = None

    def test_project_is_open(self):
        """Test that project is open and that it has no project items."""
        self.assertIsInstance(self.toolbox.project(), SpineToolboxProject)
        n = self.toolbox.project_item_model.n_items()
        self.assertTrue(n == 0)

    def test_dags(self):
        """Test that dag_handler has been created and dags() method returns an empty list."""
        d = self.dag_handler.dags()
        self.assertTrue(len(d) == 0)

    def test_add_dag_node(self):
        """Test that adding a graph with a single node."""
        self.dag_handler.add_dag_node("a")
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        self.assertTrue(g.has_node("a"))

    def test_unify_graphs(self):
        """Test that unifying graphs works when nodes are in different graphs."""
        # Make a dag with the source node and another with the destination node
        d = nx.DiGraph()
        h = nx.DiGraph()
        d.add_edges_from([("a", "b")])  # a->b
        h.add_edges_from([("c", "d")])  # c->d
        self.dag_handler.add_dag(d)
        self.dag_handler.add_dag(h)
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        self.dag_handler.unify_graphs("b", "c")
        # Now, there should only be one graph with nodes [a,b,c,d] and edges a->b, b->c, c->d
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        self.assertEqual(len(g.nodes()), 4)
        self.assertEqual(len(g.edges()), 3)
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_node("b"))
        self.assertTrue(g.has_node("c"))
        self.assertTrue(g.has_node("d"))
        self.assertTrue(g.has_edge("a", "b"))
        self.assertTrue(g.has_edge("b", "c"))
        self.assertTrue(g.has_edge("c", "d"))


    def test_remove_dag_edge(self):
        self.fail()

    def test_remove_node_from_graph(self):
        self.fail()

    def test_rename_node(self):
        self.fail()

    def test_dag_with_node(self):
        self.fail()

    def test_dag_with_edge(self):
        self.fail()

    def test_execution_order(self):
        self.fail()

    def test_source_nodes(self):
        self.fail()

    def test_node_is_isolated(self):
        self.fail()

    # # noinspection PyMethodMayBeStatic, PyPep8Naming,SpellCheckingInspection
    # def qsettings_value_side_effect(self, key, defaultValue="0"):
    #     """Side effect for calling QSettings.value() method. Used to
    #     override default value for key 'appSettings/openPreviousProject'
    #     so that previous project is not opened in background when
    #     ToolboxUI is instantiated.
    #
    #     Args:
    #         key (str): Key to read
    #         defaultValue (QVariant): Default value if key is missing
    #     """
    #     # logging.debug("q_side_effect key:{0}, defaultValue:{1}".format(key, defaultValue))
    #     if key == "appSettings/openPreviousProject":
    #         return "0"  # Do not open previos project when instantiating ToolboxUI
    #     return defaultValue
