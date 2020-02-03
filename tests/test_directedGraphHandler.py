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
Unit tests for DirectedGraphHandler class.

:author: P. Savolainen (VTT)
:date:   18.4.2019
"""

import unittest
import logging
import sys
from PySide2.QtWidgets import QApplication
import networkx as nx
from spinetoolbox.project import SpineToolboxProject
from spinetoolbox.dag_handler import DirectedGraphHandler
from .mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestDirectedGraphHandler(unittest.TestCase):
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
        """Runs before each test. Makes an instance of ToolboxUI class.
        We want the ToolboxUI to start with the default settings and without a project
        """
        self.toolbox = create_toolboxui_with_project()
        self.dag_handler = DirectedGraphHandler()

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        clean_up_toolboxui_with_project(self.toolbox)
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
        """Test creating a graph with one node."""
        self.dag_handler.add_dag_node("a")
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        self.assertTrue(g.has_node("a"))

    def test_add_graph_edge1(self):
        """Test adding an edge when src and dst nodes are in different graphs.
        Graph 1: Nodes: [a, b]. Edges: [a->b]
        Graph 2: Nodes: [c, d]. Edges: [c->d]
        Add edge: b->c
        Result graph: Nodes: [a, b, c, d]. Edges: [a->b, b->c, c->d]
        """
        d = nx.DiGraph()
        h = nx.DiGraph()
        d.add_edges_from([("a", "b")])
        h.add_edges_from([("c", "d")])
        self.dag_handler.add_dag(d)
        self.dag_handler.add_dag(h)
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        self.dag_handler.add_graph_edge("b", "c")
        # Now, there should only be one graph with nodes [a,b,c,d] and edges a->b, b->c, c->d
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(g.nodes()), 4)
        self.assertEqual(len(g.edges()), 3)
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_node("b"))
        self.assertTrue(g.has_node("c"))
        self.assertTrue(g.has_node("d"))
        self.assertTrue(g.has_edge("a", "b"))
        self.assertTrue(g.has_edge("b", "c"))
        self.assertTrue(g.has_edge("c", "d"))

    def test_add_graph_edge2(self):
        """Test adding an edge when src and dst nodes are in the same graph.
        Graph 1: Nodes: [a, b, c]. Edges: [a->b, b->c]
        Add edge: a->c
        Result graph: Nodes: [a, b, c]. Edges: [a->b, b->c, a->c]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        self.assertEqual(len(d.nodes()), 3)  # a, b, c
        self.assertEqual(len(d.edges()), 2)  # a->b, b->c
        self.dag_handler.add_graph_edge("a", "c")
        # Now, there should only be one graph with nodes [a,b,c] and edges a->b, b->c, a->c
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(g.nodes()), 3)
        self.assertEqual(len(g.edges()), 3)
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_node("b"))
        self.assertTrue(g.has_node("c"))
        self.assertTrue(g.has_edge("a", "b"))
        self.assertTrue(g.has_edge("b", "c"))
        self.assertTrue(g.has_edge("a", "c"))

    def test_add_graph_edge3(self):
        """Test adding an edge when src and dst nodes are in different graphs.
        Graph 1: Nodes: [a]. Edges: []
        Graph 2: Nodes: [b, c]. Edges: [b->c]
        Add edge: a->c
        Result graph: Nodes: [a, b, c]. Edges: [b->c, a->c]
        """
        d = nx.DiGraph()
        h = nx.DiGraph()
        d.add_node("a")
        h.add_edges_from([("b", "c")])
        self.dag_handler.add_dag(d)
        self.dag_handler.add_dag(h)
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        self.dag_handler.add_graph_edge("a", "c")
        # Now, there should only be one graph with nodes [a,b,c] and edges b->c, a->c
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(g.nodes()), 3)
        self.assertEqual(len(g.edges()), 2)
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_node("b"))
        self.assertTrue(g.has_node("c"))
        self.assertTrue(g.has_edge("b", "c"))
        self.assertTrue(g.has_edge("a", "c"))

    def test_add_graph_edge4(self):
        """Test adding an edge when src and dst nodes are in different graphs.
        Graph 1: Nodes: [a, b]. Edges: [a->b]
        Graph 2: Nodes: [c]. Edges: []
        Add edge: a->c
        Result graph: Nodes: [a, b, c]. Edges: [a->b, a->c]
        """
        d = nx.DiGraph()
        h = nx.DiGraph()
        d.add_edges_from([("a", "b")])
        h.add_node("c")
        self.dag_handler.add_dag(d)
        self.dag_handler.add_dag(h)
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        self.dag_handler.add_graph_edge("a", "c")
        # Now, there should only be one graph with nodes [a,b,c] and edges a->b, a->c
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(g.nodes()), 3)
        self.assertEqual(len(g.edges()), 2)
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_node("b"))
        self.assertTrue(g.has_node("c"))
        self.assertTrue(g.has_edge("a", "b"))
        self.assertTrue(g.has_edge("a", "c"))

    def test_add_graph_edge5(self):
        """Test adding an edge when src and dst nodes are in different graphs.
        Graph 1: Nodes: [a]. Edges: []
        Graph 2: Nodes: [b]. Edges: []
        Add edge: a->b
        Result graph: Nodes: [a, b]. Edges: [a->b]
        """
        d = nx.DiGraph()
        h = nx.DiGraph()
        d.add_node("a")
        h.add_node("b")
        self.dag_handler.add_dag(d)
        self.dag_handler.add_dag(h)
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        self.dag_handler.add_graph_edge("a", "b")
        # Now, there should only be one graph with nodes [a,b,c] and edges a->b, a->c
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(g.nodes()), 2)
        self.assertEqual(len(g.edges()), 1)
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_node("b"))
        self.assertTrue(g.has_edge("a", "b"))

    def test_add_graph_edge6(self):
        """Test adding a feedback edge, i.e. src and dst nodes are the same.
        Graph 1: Nodes: [a]. Edges: []
        Add edge: a->a
        Result graph: Nodes: [a]. Edges: []
        """
        d = nx.DiGraph()
        d.add_node("a")
        self.dag_handler.add_dag(d)
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        self.dag_handler.add_graph_edge("a", "a")
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        g = self.dag_handler.dags()[0]
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(g.nodes()), 1)
        self.assertEqual(len(g.edges()), 1)
        self.assertTrue(g.has_node("a"))
        self.assertTrue(g.has_edge("a", "a"))

    def test_add_graph_edge7(self):
        """Test adding more feedback loops to more complex graphs.
        Graph 1: Nodes: [a, b, c]. Edges: [a->b, b->c]
        Graph 2: Nodes: [d, e, f]. Edges: [d->f, e->f]
        Add edges: a->a, b->b, c->c, d->d, e->e, f->f
        Result graph 1: Nodes: [a, b, c]. Edges: [a->b, b->c, a->a, b->b, c->c]
        Result graph 2: Nodes: [d, e, f]. Edges: [d->f, e->f, d->d, e->e, f->f]
        """
        d = nx.DiGraph()
        h = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c")])
        h.add_edges_from([("d", "f"), ("e", "f")])
        self.dag_handler.add_dag(d)
        self.dag_handler.add_dag(h)
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        self.dag_handler.add_graph_edge("a", "a")
        self.dag_handler.add_graph_edge("b", "b")
        self.dag_handler.add_graph_edge("c", "c")
        self.dag_handler.add_graph_edge("d", "d")
        self.dag_handler.add_graph_edge("e", "e")
        self.dag_handler.add_graph_edge("f", "f")
        # There should still be two graphs
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("d")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 3)
        self.assertEqual(len(result_d.edges()), 5)
        self.assertTrue(result_d.has_node("a"))
        self.assertTrue(result_d.has_node("b"))
        self.assertTrue(result_d.has_node("c"))
        self.assertTrue(result_d.has_edge("a", "b"))
        self.assertTrue(result_d.has_edge("b", "c"))
        self.assertTrue(result_d.has_edge("a", "a"))
        self.assertTrue(result_d.has_edge("b", "b"))
        self.assertTrue(result_d.has_edge("c", "c"))
        self.assertEqual(len(result_h.nodes()), 3)
        self.assertEqual(len(result_h.edges()), 5)
        self.assertTrue(result_h.has_node("d"))
        self.assertTrue(result_h.has_node("e"))
        self.assertTrue(result_h.has_node("f"))
        self.assertTrue(result_h.has_edge("d", "f"))
        self.assertTrue(result_h.has_edge("e", "f"))
        self.assertTrue(result_h.has_edge("d", "d"))
        self.assertTrue(result_h.has_edge("e", "e"))
        self.assertTrue(result_h.has_edge("f", "f"))

    def test_add_graph_edge8(self):
        """Test adding an edge which makes the graph not a DAG.
        Graph 1: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d]
        Add edge: c->b
        Result graph: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d, c->b]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("c", "d")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 3)
        self.dag_handler.add_graph_edge("c", "b")
        # Now, there should still be just one graph
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        result_d = self.dag_handler.dag_with_node("a")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 4)
        self.assertEqual(len(result_d.edges()), 4)
        self.assertTrue(result_d.has_node("a"))
        self.assertTrue(result_d.has_node("b"))
        self.assertTrue(result_d.has_node("c"))
        self.assertTrue(result_d.has_node("d"))
        self.assertTrue(result_d.has_edge("a", "c"))
        self.assertTrue(result_d.has_edge("b", "c"))
        self.assertTrue(result_d.has_edge("c", "d"))
        self.assertTrue(result_d.has_edge("c", "b"))

    def test_remove_graph_edge1(self):
        """Test removing an edge from a graph. Splits the graph
        into two separate graphs if the nodes are not connected
        after removing the edge.
        Graph 1: Nodes: [a, b]. Edges: [a->b]
        Remove edge: a->b
        Result graph 1: Nodes: [a]. Edges: []
        Result graph 2: Nodes: [b]. Edges: []
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 2)  # a, b
        self.assertEqual(len(d.edges()), 1)  # a->b
        self.assertTrue(d.has_edge("a", "b"))
        # Now remove the edge
        self.dag_handler.remove_graph_edge("a", "b")
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("b")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 1)
        self.assertEqual(len(result_d.edges()), 0)
        self.assertTrue(result_d.has_node("a"))
        self.assertEqual(len(result_h.nodes()), 1)
        self.assertEqual(len(result_h.edges()), 0)
        self.assertTrue(result_h.has_node("b"))

    def test_remove_graph_edge2(self):
        """Test removing an edge from a graph. Splits the graph
        into two separate graphs if the nodes are not connected
        after removing the edge.
        Graph 1: Nodes: [a, b, c]. Edges: [a->b->c]
        Remove edge: a->b
        Result graph 1: Nodes: [a]. Edges: []
        Result graph 2: Nodes: [b, c]. Edges: [b->c]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)  # a, b, c
        self.assertEqual(len(d.edges()), 2)  # a->b, b->c
        self.assertTrue(d.has_edge("a", "b"))
        self.assertTrue(d.has_edge("b", "c"))
        # Now remove the edge
        self.dag_handler.remove_graph_edge("a", "b")
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("b")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 1)
        self.assertEqual(len(result_d.edges()), 0)
        self.assertTrue(result_d.has_node("a"))
        self.assertEqual(len(result_h.nodes()), 2)
        self.assertEqual(len(result_h.edges()), 1)
        self.assertTrue(result_h.has_node("b"))
        self.assertTrue(result_h.has_node("c"))
        self.assertTrue(result_h.has_edge("b", "c"))

    def test_remove_graph_edge3(self):
        """Test removing an edge from a graph. Splits the graph
        into two separate graphs if the nodes are not connected
        after removing the edge.
        Graph 1: Nodes: [a, b, c]. Edges: [a->b->c]
        Remove edge: b->c
        Result graph 1: Nodes: [a, b]. Edges: [a->b]
        Result graph 2: Nodes: [c]. Edges: []
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)  # a, b, c
        self.assertEqual(len(d.edges()), 2)  # a->b, b->c
        self.assertTrue(d.has_edge("a", "b"))
        self.assertTrue(d.has_edge("b", "c"))
        # Now remove the edge
        self.dag_handler.remove_graph_edge("b", "c")
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("c")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 2)
        self.assertEqual(len(result_d.edges()), 1)
        self.assertTrue(result_d.has_node("a"))
        self.assertTrue(result_d.has_node("b"))
        self.assertTrue(result_d.has_edge("a", "b"))
        self.assertEqual(len(result_h.nodes()), 1)
        self.assertEqual(len(result_h.edges()), 0)
        self.assertTrue(result_h.has_node("c"))

    def test_remove_graph_edge4(self):
        """Test removing an edge from a graph. Splits the graph
        into two separate graphs if the nodes are not connected
        after removing the edge.
        Graph 1: Nodes: [a, b, c, d]. Edges: [a->b->c->d]
        Remove edge: b->c
        Result graph 1: Nodes: [a, b]. Edges: [a->b]
        Result graph 2: Nodes: [c, d]. Edges: [c->d]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c"), ("c", "d")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 4)  # a, b, c
        self.assertEqual(len(d.edges()), 3)  # a->b, b->c
        self.assertTrue(d.has_edge("a", "b"))
        self.assertTrue(d.has_edge("b", "c"))
        self.assertTrue(d.has_edge("c", "d"))
        # Now remove the edge
        self.dag_handler.remove_graph_edge("b", "c")
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("c")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 2)
        self.assertEqual(len(result_d.edges()), 1)
        self.assertTrue(result_d.has_node("a"))
        self.assertTrue(result_d.has_node("b"))
        self.assertTrue(result_d.has_edge("a", "b"))
        self.assertEqual(len(result_h.nodes()), 2)
        self.assertEqual(len(result_h.edges()), 1)
        self.assertTrue(result_h.has_node("c"))
        self.assertTrue(result_h.has_node("d"))
        self.assertTrue(result_h.has_edge("c", "d"))

    def test_remove_graph_edge5(self):
        """Test removing an edge from a graph. Splits the graph
        into two separate graphs if the nodes are not connected
        after removing the edge.
        Graph 1: Nodes: [a, b, c, d, e]. Edges: [a->c, b->c, c->d, d->e]
        Remove edge: c->d
        Result graph 1: Nodes: [a, b, c]. Edges: [a->c, b->c]
        Result graph 2: Nodes: [d, e]. Edges: [d->e]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("c", "d"), ("d", "e")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 5)
        self.assertEqual(len(d.edges()), 4)
        self.assertTrue(d.has_edge("a", "c"))
        self.assertTrue(d.has_edge("b", "c"))
        self.assertTrue(d.has_edge("c", "d"))
        self.assertTrue(d.has_edge("d", "e"))
        # Now remove the edge
        self.dag_handler.remove_graph_edge("c", "d")
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("d")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 3)
        self.assertEqual(len(result_d.edges()), 2)
        self.assertTrue(result_d.has_edge("a", "c"))
        self.assertTrue(result_d.has_edge("b", "c"))
        self.assertEqual(len(result_h.nodes()), 2)
        self.assertEqual(len(result_h.edges()), 1)
        self.assertTrue(result_h.has_node("d"))
        self.assertTrue(result_h.has_node("e"))
        self.assertTrue(result_h.has_edge("d", "e"))

    def test_remove_graph_edge6(self):
        """Test removing an edge from a graph. Splits the graph
        into two separate graphs if the nodes are not connected
        after removing the edge.
        Graph 1: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d, a->d]
        Remove edge: a->d
        Result graph 1: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("c", "d"), ("a", "d")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 4)
        self.assertTrue(d.has_edge("a", "c"))
        self.assertTrue(d.has_edge("b", "c"))
        self.assertTrue(d.has_edge("c", "d"))
        self.assertTrue(d.has_edge("a", "d"))
        # Now remove the edge
        self.dag_handler.remove_graph_edge("a", "d")
        # There should still be just one graph
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        result_d = self.dag_handler.dag_with_node("a")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 4)
        self.assertEqual(len(result_d.edges()), 3)
        self.assertTrue(result_d.has_edge("a", "c"))
        self.assertTrue(result_d.has_edge("b", "c"))
        self.assertTrue(result_d.has_edge("c", "d"))

    def test_remove_graph_edge7(self):
        """Test removing an edge from a graph. Splits the graph
        into two separate graphs if the nodes are not connected
        after removing the edge.
        Graph 1: Nodes: [a, b, c]. Edges: [a->c, b->c, a->a, b->b, c->c]
        Remove edges: a->a, b->b, c->c
        Result graph 1: Nodes: [a, b, c]. Edges: [a->c, b->c]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("a", "a"), ("b", "b"), ("c", "c")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)
        self.assertEqual(len(d.edges()), 5)
        self.assertTrue(d.has_edge("a", "c"))
        self.assertTrue(d.has_edge("b", "c"))
        self.assertTrue(d.has_edge("a", "a"))
        self.assertTrue(d.has_edge("b", "b"))
        self.assertTrue(d.has_edge("c", "c"))
        # Now remove all feedback links
        self.dag_handler.remove_graph_edge("a", "a")
        self.dag_handler.remove_graph_edge("b", "b")
        self.dag_handler.remove_graph_edge("c", "c")
        # There should still be just one graph
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        result_d = self.dag_handler.dag_with_node("a")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 3)
        self.assertEqual(len(result_d.edges()), 2)
        self.assertTrue(result_d.has_edge("a", "c"))
        self.assertTrue(result_d.has_edge("b", "c"))

    def test_remove_graph_edge8(self):
        """Test removing an edge from a graph. Splits the graph
        into two separate graphs if the nodes are not connected
        after removing the edge. Test that self-loops remain in result graphs.
        Graph 1: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d, a->a, b->b, c->c, d->d]
        Remove edge: c->d
        Result graph 1: Nodes: [a, b, c]. Edges: [a->c, b->c, a->a, b->b, c->c]
        Result graph 2: Nodes: [d]. Edges: [d->d]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("c", "d"), ("a", "a"), ("b", "b"), ("c", "c"), ("d", "d")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 7)
        self.assertTrue(d.has_edge("a", "c"))
        self.assertTrue(d.has_edge("b", "c"))
        self.assertTrue(d.has_edge("c", "d"))
        self.assertTrue(d.has_edge("a", "a"))
        self.assertTrue(d.has_edge("b", "b"))
        self.assertTrue(d.has_edge("c", "c"))
        self.assertTrue(d.has_edge("d", "d"))
        # Now remove edge
        self.dag_handler.remove_graph_edge("c", "d")
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("d")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 3)
        self.assertEqual(len(result_d.edges()), 5)
        self.assertTrue(result_d.has_edge("a", "c"))
        self.assertTrue(result_d.has_edge("b", "c"))
        self.assertTrue(result_d.has_edge("a", "a"))
        self.assertTrue(result_d.has_edge("b", "b"))
        self.assertTrue(result_d.has_edge("c", "c"))
        self.assertEqual(len(result_h.nodes()), 1)
        self.assertEqual(len(result_h.edges()), 1)
        self.assertTrue(result_h.has_edge("d", "d"))

    def test_remove_graph_edge9(self):
        """Test removing an edge from a graph that is not a DAG.
        Graph 1: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d, c->b]
        Remove edge: c->b
        Result graph: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("c", "d"), ("c", "b")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 4)
        # Now remove edge
        self.dag_handler.remove_graph_edge("c", "b")
        # There should still be just one graph (that is a DAG)
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        result_d = self.dag_handler.dag_with_node("a")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 4)
        self.assertEqual(len(result_d.edges()), 3)
        self.assertTrue(result_d.has_node("a"))
        self.assertTrue(result_d.has_node("b"))
        self.assertTrue(result_d.has_node("c"))
        self.assertTrue(result_d.has_node("d"))
        self.assertTrue(result_d.has_edge("a", "c"))
        self.assertTrue(result_d.has_edge("b", "c"))
        self.assertTrue(result_d.has_edge("c", "d"))

    def test_remove_graph_edge10(self):
        """Test removing an edge from a graph that is not a DAG.
        Graph 1: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d, d->a]
        Remove edge: d->a
        Result graph: Nodes: [a, b, c, d]. Edges: [a->c, b->c, c->d]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("c", "d"), ("d", "a")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 4)
        # Now remove edge
        self.dag_handler.remove_graph_edge("d", "a")
        # There should still be just one graph (that is a DAG)
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        # logging.debug("n dags:{0}".format(len(self.dag_handler.dags())))
        # out1 = self.dag_handler.dags()[0]
        # out2 = self.dag_handler.dags()[1]
        # logging.debug("out1 nodes:{0} edges:{1}".format(out1.nodes(), out1.edges()))
        # logging.debug("out2 nodes:{0} edges:{1}".format(out2.nodes(), out2.edges()))
        result_d = self.dag_handler.dag_with_node("a")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 4)
        self.assertEqual(len(result_d.edges()), 3)
        self.assertTrue(result_d.has_node("a"))
        self.assertTrue(result_d.has_node("b"))
        self.assertTrue(result_d.has_node("c"))
        self.assertTrue(result_d.has_node("d"))
        self.assertTrue(result_d.has_edge("a", "c"))
        self.assertTrue(result_d.has_edge("b", "c"))
        self.assertTrue(result_d.has_edge("c", "d"))

    def test_remove_graph_edge11(self):
        """Test removing an edge from a graph.
        Graph 1: Nodes: [a, b, c, d]. Edges: [a->b, b->d, a->c, c->d]
        Remove edge: a->c
        Result graph: Nodes: [a, b, c, d]. Edges: [a->b, b->d, c->d]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "d"), ("a", "c"), ("c", "d")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 4)
        # Now remove edge
        self.dag_handler.remove_graph_edge("a", "c")
        # There should still be just one graph (that is a DAG)
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        result_d = self.dag_handler.dag_with_node("a")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 4)
        self.assertEqual(len(result_d.edges()), 3)
        self.assertTrue(result_d.has_node("a"))
        self.assertTrue(result_d.has_node("b"))
        self.assertTrue(result_d.has_node("c"))
        self.assertTrue(result_d.has_node("d"))
        self.assertTrue(result_d.has_edge("a", "b"))
        self.assertTrue(result_d.has_edge("b", "d"))
        self.assertTrue(result_d.has_edge("c", "d"))

    def test_remove_graph_edge12(self):
        """Test removing an edge from a graph.
        Graph 1: Nodes: [a, b, c, d, e, f]. Edges: [a->b, b->c, d->e, e->f, d->b]
        Remove edge: d->b
        Result graph 1: Nodes: [a, b, c]. Edges: [a->b, b->c]
        Result graph 2: Nodes: [d, e, f]. Edges: [d->e, e->f]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c"), ("d", "e"), ("e", "f"), ("d", "b")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        self.assertEqual(len(d.nodes()), 6)
        self.assertEqual(len(d.edges()), 5)
        # Now remove edge
        self.dag_handler.remove_graph_edge("d", "b")
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("d")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 3)
        self.assertEqual(len(result_d.edges()), 2)
        self.assertTrue(result_d.has_edge("a", "b"))
        self.assertTrue(result_d.has_edge("b", "c"))
        self.assertEqual(len(result_h.nodes()), 3)
        self.assertEqual(len(result_h.edges()), 2)
        self.assertTrue(result_h.has_edge("d", "e"))
        self.assertTrue(result_h.has_edge("e", "f"))

    def test_remove_graph_edge13(self):
        """Test removing an edge from a graph.
        Graph 1: Nodes: [a, b, c, d]. Edges: [a->b, c->d, c->b]
        Remove edge: c->b
        Result graph 1: Nodes: [a, b]. Edges: [a->b]
        Result graph 2: Nodes: [c, d]. Edges: [c->d]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("c", "d"), ("c", "b")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 3)
        # Now remove edge
        self.dag_handler.remove_graph_edge("c", "b")
        # There should be two graphs now
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        result_d = self.dag_handler.dag_with_node("a")
        result_h = self.dag_handler.dag_with_node("c")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(result_d.nodes()), 2)
        self.assertEqual(len(result_d.edges()), 1)
        self.assertTrue(result_d.has_edge("a", "b"))
        self.assertEqual(len(result_h.nodes()), 2)
        self.assertEqual(len(result_h.edges()), 1)
        self.assertTrue(result_h.has_edge("c", "d"))

    def test_execution_order1(self):
        """Test that execution order is correct with all kinds of graphs.
        Graph Nodes: [a, b, c]. Edges: [a->b, b->c]
        Expected order: a-b-c
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)  # a, b, c
        self.assertEqual(len(d.edges()), 2)  # a->b, b->c
        self.assertTrue(d.has_edge("a", "b"))
        self.assertTrue(d.has_edge("b", "c"))
        successors = self.dag_handler.node_successors(d)
        self.assertEqual(len(successors), 3)
        self.assertEqual(list(successors.keys()), ["a", "b", "c"])
        self.assertEqual(list(successors.values()), [["b"], ["c"], []])

    def test_execution_order2(self):
        """Test that execution order is correct with all kinds of graphs.
        Graph Nodes: [a, b, c]. Edges: [a->c, b->c]
        Expected order: a-b-c or b-a-c
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)  # a, b, c
        self.assertEqual(len(d.edges()), 2)  # a->b, b->c
        self.assertTrue(d.has_edge("a", "c"))
        self.assertTrue(d.has_edge("b", "c"))
        successors = self.dag_handler.node_successors(d)
        self.assertEqual(len(successors), 3)
        exec_list = list(successors)
        self.assertTrue(exec_list in (["a", "b", "c"], ["b", "a", "c"]))
        self.assertTrue(successors["a"] == ["c"])
        self.assertTrue(successors["b"] == ["c"])
        self.assertTrue(successors["c"] == [])

    def test_execution_order3(self):
        """Test that execution order is correct with all kinds of graphs.
        Graph Nodes: [a, b, c, d]. Edges: [a->b, b->d, c->d]
        Expected order: a-b-c-d or a-c-b-d or c-a-b-d
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "d"), ("c", "d")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 3)
        successors = self.dag_handler.node_successors(d)
        self.assertEqual(4, len(successors))
        exec_list = list(successors)
        self.assertTrue(exec_list in (["a", "b", "c", "d"], ["a", "c", "b", "d"], ["c", "a", "b", "d"]))
        self.assertTrue(successors["a"] == ["b"])
        self.assertTrue(successors["b"] == ["d"])
        self.assertTrue(successors["c"] == ["d"])

    def test_execution_order4(self):
        """Test that execution order is correct with all kinds of graphs.
        Graph Nodes: [a, b, c, d]. Edges: [a->b, a->c, b->d, c->d]
        Expected order: a-b-c-d or a-c-b-d
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 4)
        self.assertEqual(len(d.edges()), 4)
        successors = self.dag_handler.node_successors(d)
        self.assertEqual(4, len(successors))
        exec_list = list(successors)
        self.assertTrue(exec_list in (["a", "b", "c", "d"], ["a", "c", "b", "d"]))
        self.assertTrue(successors["a"] in (["b", "c"], ["c", "b"]))
        self.assertTrue(successors["b"] == ["d"])
        self.assertTrue(successors["c"] == ["d"])

    def test_execution_order5(self):
        """Test that execution order is correct with all kinds of graphs.
        Graph Nodes: [a]. Edges: []
        Expected order: a
        """
        d = nx.DiGraph()
        d.add_node("a")
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 1)
        self.assertEqual(len(d.edges()), 0)
        successors = self.dag_handler.node_successors(d)
        self.assertEqual(1, len(successors))
        self.assertTrue(successors["a"] == [])

    def test_execution_order6(self):
        """Test that execution order is correct with all kinds of graphs.
        Graph Nodes: [a, b]. Edges: [a->b, b->b]  Has self-loop (feedback)
        Expected order: None
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "b")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 2)
        self.assertEqual(len(d.edges()), 2)
        successors = self.dag_handler.node_successors(d)
        # Execution order for this graph should be empty since it's not a DAG
        self.assertEqual(0, len(successors))

    def test_execution_order7(self):
        """Test that execution order is correct with all kinds of graphs.
        Graph Nodes: [a, b, c]. Edges: [a->b, b->c, c->b]  Note: Has loop
        Expected order: None
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c"), ("c", "b")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)
        self.assertEqual(len(d.edges()), 3)
        successors = self.dag_handler.node_successors(d)
        # Execution order for this graph should be empty since it's not a DAG
        self.assertEqual(0, len(successors))

    def test_execution_order_to_node_1(self):
        """Test that execution order to node is correct with all kinds of graphs.
        Graph Nodes: [a, b, c, d]. Edges: [a->b, a->c, b->d]
        Expected order: a-b-c-d or a-c-b-d
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("a", "c"), ("b", "d")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        successors = self.dag_handler.successors_til_node(d, "d")
        self.assertEqual(successors, {'a': ['b'], 'b': ['d'], 'd': []})

    def test_remove_node_from_graph1(self):
        """Test that graphs are updated correctly when project items are removed.
        Make a Star graph and remove the center.
        Graph 1: Nodes: [a, b, c, d, e]. Edges: [a->c, b->c, c->d, c->e]
        Remove node "c"
        Expected Result Graphs:
        Result Graph 1: Nodes:[a], Edges:[]
        Result Graph 2: Nodes:[b], Edges:[]
        Result Graph 3: Nodes:[d], Edges:[]
        Result Graph 4: Nodes:[e], Edges:[]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("c", "d"), ("c", "e")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 5)
        self.assertEqual(len(d.edges()), 4)
        self.dag_handler.remove_node_from_graph("c")
        # Check that the resulting graphs are correct
        self.assertTrue(len(self.dag_handler.dags()) == 4)
        out1 = self.dag_handler.dag_with_node("a")
        out2 = self.dag_handler.dag_with_node("b")
        out3 = self.dag_handler.dag_with_node("d")
        out4 = self.dag_handler.dag_with_node("e")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(out1.nodes()), 1)
        self.assertEqual(len(out1.edges()), 0)
        self.assertTrue(out1.has_node("a"))
        self.assertEqual(len(out2.nodes()), 1)
        self.assertEqual(len(out2.edges()), 0)
        self.assertTrue(out2.has_node("b"))
        self.assertEqual(len(out3.nodes()), 1)
        self.assertEqual(len(out3.edges()), 0)
        self.assertTrue(out3.has_node("d"))
        self.assertEqual(len(out4.nodes()), 1)
        self.assertEqual(len(out4.edges()), 0)
        self.assertTrue(out4.has_node("e"))

    def test_remove_node_from_graph2(self):
        """Test that graphs are updated correctly when project items are removed.
        Graph 1: Nodes: [a, b, c]. Edges: [a->b, b->c]
        Remove node "a"
        Expected Result Graph: Nodes:[b, c], Edges:[b->c]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)
        self.assertEqual(len(d.edges()), 2)
        self.dag_handler.remove_node_from_graph("a")
        # Check that the resulting graphs are correct
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        out1 = self.dag_handler.dag_with_node("b")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(out1.nodes()), 2)
        self.assertEqual(len(out1.edges()), 1)
        self.assertTrue(out1.has_node("b"))
        self.assertTrue(out1.has_node("c"))
        self.assertTrue(out1.has_edge("b", "c"))

    def test_remove_node_from_graph3(self):
        """Test that graphs are updated correctly when project items are removed.
        Graph 1: Nodes: [a, b, c]. Edges: [a->b, b->c, a->a, b->b, c->c]
        Remove node "b"
        Expected Result Graph 1: Nodes:[a], Edges:[a->a]
        Expected Result Graph 2: Nodes:[c], Edges:[c->c]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c"), ("a", "a"), ("b", "b"), ("c", "c")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)
        self.assertEqual(len(d.edges()), 5)
        self.dag_handler.remove_node_from_graph("b")
        # Check that the resulting graphs are correct
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        out1 = self.dag_handler.dag_with_node("a")
        out2 = self.dag_handler.dag_with_node("c")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(out1.nodes()), 1)
        self.assertEqual(len(out1.edges()), 1)
        self.assertTrue(out1.has_node("a"))
        self.assertTrue(out1.has_edge("a", "a"))
        self.assertEqual(len(out2.nodes()), 1)
        self.assertEqual(len(out2.edges()), 1)
        self.assertTrue(out2.has_node("c"))
        self.assertTrue(out2.has_edge("c", "c"))

    def test_remove_node_from_graph4(self):
        """Test that graphs are updated correctly when project items are removed.
        Graph 1: Nodes: [a, b, c]. Edges: [a->b, b->c, b->b]
        Remove node "c"
        Expected Result Graph 1: Nodes:[a, b], Edges:[a->b, b->b]
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "b"), ("b", "c"), ("b", "b")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)
        self.assertEqual(len(d.edges()), 3)
        self.dag_handler.remove_node_from_graph("c")
        # Check that the resulting graphs are correct
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        out1 = self.dag_handler.dag_with_node("a")
        # Check that the number of nodes and edges match and they are correct
        self.assertEqual(len(out1.nodes()), 2)
        self.assertEqual(len(out1.edges()), 2)
        self.assertTrue(out1.has_node("a"))
        self.assertTrue(out1.has_node("b"))
        self.assertTrue(out1.has_edge("a", "b"))
        self.assertTrue(out1.has_edge("b", "b"))

    def test_remove_node_from_graph5(self):
        """Test that graphs are updated correctly when project items are removed.
        Graph 1: Nodes: [a, b, c]. Edges: [a->c, b->c, a->a, b->b]
        Remove nodes "a" -> "b" -> "c"
        Expected Result Graph 1: None
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("a", "a"), ("b", "b")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 3)
        self.assertEqual(len(d.edges()), 4)
        self.dag_handler.remove_node_from_graph("a")
        self.dag_handler.remove_node_from_graph("b")
        self.dag_handler.remove_node_from_graph("c")
        # There should be no DAGs left
        self.assertTrue(len(self.dag_handler.dags()) == 0)

    def test_remove_node_from_graph6(self):
        """Test that graphs are updated correctly when project items are removed.
        Graph 1: Nodes: [a, b, c, d, e]. Edges: [a->c, b->c, c->d, c->e]
        Remove nodes in order "c" -> "a" -> "b"-> "d"-> "e"
        Check that the number of saved dags is correct after each node removal
        """
        d = nx.DiGraph()
        d.add_edges_from([("a", "c"), ("b", "c"), ("c", "d"), ("c", "e")])
        self.dag_handler.add_dag(d)
        # Check that the graph was created successfully
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        d = self.dag_handler.dags()[0]
        self.assertEqual(len(d.nodes()), 5)
        self.assertEqual(len(d.edges()), 4)
        # Remove node c
        self.dag_handler.remove_node_from_graph("c")
        self.assertTrue(len(self.dag_handler.dags()) == 4)
        # Remove node a
        self.dag_handler.remove_node_from_graph("a")
        self.assertTrue(len(self.dag_handler.dags()) == 3)
        # Remove node b
        self.dag_handler.remove_node_from_graph("b")
        self.assertTrue(len(self.dag_handler.dags()) == 2)
        # Remove node d
        self.dag_handler.remove_node_from_graph("d")
        self.assertTrue(len(self.dag_handler.dags()) == 1)
        # Remove node e
        self.dag_handler.remove_node_from_graph("e")
        self.assertTrue(len(self.dag_handler.dags()) == 0)
