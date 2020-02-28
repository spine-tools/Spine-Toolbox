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
Contains classes for handling DAGs.

:author: P. Savolainen (VTT)
:date:   8.4.2019
"""

import logging
import random
from PySide2.QtCore import Signal, Slot, QObject, QTimer
import networkx as nx


class DirectedGraphHandler(QObject):
    """Class for manipulating graphs according to user's actions."""

    dag_simulation_requested = Signal("QVariant")

    def __init__(self):
        super().__init__()
        self._dags = list()

    def dags(self):
        """Returns a list of graphs (DiGraph) in the project."""
        return self._dags

    def add_dag(self, dag, request_simulation=True):
        """Add graph to list.

        Args:
            dag (DiGraph): Graph to add
            request_simulation (bool): if True, emits dag_simulation_requested
        """
        self._dags.append(dag)
        if request_simulation:
            self.dag_simulation_requested.emit(dag)

    def remove_dag(self, dag):
        """Remove graph from instance variable list.

        Args:
            dag (DiGraph): Graph to remove
        """
        self._dags.remove(dag)

    def add_dag_node(self, node_name):
        """Create directed graph with one node and add it to list.

        Args:
            node_name (str): Project item name to add as a node
        """
        dag = nx.DiGraph()
        dag.add_node(node_name)
        self.add_dag(dag)

    def add_graph_edge(self, src_node, dst_node):
        """Adds an edge between the src and dst nodes. If nodes are in
        different graphs, the reference to union graph is saved and the
        references to the original graphs are removed. If src and dst
        nodes are already in the same graph, the edge is added to the graph.
        If src and dst are the same node, a self-loop (feedback) edge is
        added.

        Args:
            src_node (str): Source project item node name
            dst_node (str): Destination project item node name
        """
        src_graph = self.dag_with_node(src_node)
        dst_graph = self.dag_with_node(dst_node)
        if src_graph == dst_graph:
            # src and dst are already in same graph. Just add edge to src_graph and return
            src_graph.add_edge(src_node, dst_node)
            self.dag_simulation_requested.emit(src_graph)
        else:
            # Unify graphs
            union_dag = nx.union(src_graph, dst_graph)
            union_dag.add_edge(src_node, dst_node)
            # Remove src and dst graphs
            self.remove_dag(src_graph)
            self.remove_dag(dst_graph)
            # Add union graph
            self.add_dag(union_dag)

    def remove_graph_edge(self, src_node, dst_node):
        """Removes edge from a directed graph.

        Args:
            src_node (str): Source project item node name
            dst_node (str): Destination project item node name
        """
        dag = self.dag_with_edge(src_node, dst_node)
        dag.remove_edge(src_node, dst_node)
        components = list(nx.weakly_connected_components(dag))
        if len(components) == 1:
            # Graph wasn't splitted, we're fine
            self.dag_simulation_requested.emit(dag)
            return
        # Graph was splitted into two
        left_nodes, right_nodes = components
        left_edges = nx.edges(dag, left_nodes)
        right_edges = nx.edges(dag, right_nodes)
        # Make left graph.
        left_graph = nx.DiGraph()
        left_graph.add_nodes_from(left_nodes)
        left_graph.add_edges_from(left_edges)
        # Make right graph.
        right_graph = nx.DiGraph()
        right_graph.add_nodes_from(right_nodes)
        right_graph.add_edges_from(right_edges)
        # Remove old graph and add new graphs instead
        self.remove_dag(dag)
        self.add_dag(left_graph)
        self.add_dag(right_graph)

    def remove_node_from_graph(self, node_name):
        """Removes node from a graph that contains it. Called when project item is removed from project.

        Args:
            node_name (str): Project item name
        """
        # This is called every time a previous project is closed and another is opened. --Really?
        g = self.dag_with_node(node_name)
        edges_to_remove = list()
        for edge in g.edges():
            if node_name in (edge[0], edge[1]):
                edges_to_remove.append(edge)
        g.remove_edges_from(edges_to_remove)
        # Now remove the node itself
        g.remove_node(node_name)
        # Loop through remaining nodes and check if any of them are isolated now
        nodes_to_remove = list()
        for node in g.nodes():
            if self.node_is_isolated(node, allow_self_loop=True):
                nodes_to_remove.append(node)
                h = nx.DiGraph()
                h.add_node(node)
                if g.has_edge(node, node):
                    h.add_edge(node, node)
                self.add_dag(h)
        g.remove_nodes_from(nodes_to_remove)
        if not g.nodes():
            self.remove_dag(g)
        else:
            self.dag_simulation_requested.emit(g)

    def rename_node(self, old_name, new_name):
        """Handles renaming the node and edges in a graph when a project item is renamed.

        Args:
            old_name (str): Old project item name
            new_name (str): New project item name

        Returns:
            bool: True if successful, False if renaming failed
        """
        g = self.dag_with_node(old_name)
        mapping = {old_name: new_name}  # old_name->new_name
        nx.relabel_nodes(g, mapping, copy=False)  # copy=False modifies g in place

    def dag_with_node(self, node_name):
        """Returns directed graph that contains given node.

        Args:
            node_name (str): Node to look for

        Returns:
            (DiGraph): Directed graph that contains node or None if not found.
        """
        for dag in self.dags():
            if dag.has_node(node_name):
                return dag
        # logging.error("Graph containing node %s not found. Something is wrong.", node_name)
        return None

    def dag_with_edge(self, src_node, dst_node):
        """Returns directed graph that contains given edge.

        Args:
            src_node (str): Source node name
            dst_node (str): Destination node name

        Returns:
            (DiGraph): Directed graph that contains edge or None if not found.
        """
        for dag in self.dags():
            if dag.has_edge(src_node, dst_node):
                return dag
        logging.error("Graph containing edge %s->%s not found. Something is wrong.", src_node, dst_node)
        return None

    @staticmethod
    def node_successors(g):
        """Returns a dict mapping nodes in the given graph to a list of its direct successors.
        The nodes are in topological sort order.
        Topological sort in the words of networkx:
        "a nonunique permutation of the nodes, such that an edge from u to v
        implies that u appears before v in the topological sort order."

        Args:
            g (DiGraph): Directed graph to process

        Returns:
            dict: key is the node name, value is list of successor names
            Empty dict if given graph is not a DAG.
        """
        if not nx.is_directed_acyclic_graph(g):
            return {}
        return {n: list(g.successors(n)) for n in nx.topological_sort(g)}

    def successors_til_node(self, g, node):
        """Like node_successors but only until the given node,
        and ignoring all nodes that are not its ancestors."""
        bunch = list(nx.ancestors(g, node)) + [node]
        return self.node_successors(g.subgraph(bunch))

    def node_is_isolated(self, node, allow_self_loop=False):
        """Checks if the project item with the given name has any connections.

        Args:
            node (str): Project item name
            allow_self_loop (bool): If default (False), Self-loops are considered as an
                in-neighbor or an out-neighbor so the method returns False. If True,
                single node with a self-loop is considered isolated.

        Returns:
            bool: True if project item has no in-neighbors nor out-neighbors, False if it does.
                Single node with a self-loop is NOT isolated (returns False).
        """
        g = self.dag_with_node(node)
        if not allow_self_loop:
            return nx.is_isolate(g, node)
        has_self_loop = g.has_edge(node, node)
        if not has_self_loop:
            return nx.is_isolate(g, node)
        # The node has a self-loop.
        # Node degree is the number of edges that are connected to it. A self-loop increases the degree by 2
        deg = g.degree(node)
        if deg - 2 == 0:  # If degree - 2 is zero, it is isolated.
            return True
        return False

    @staticmethod
    def source_nodes(g):
        """Returns a list of source nodes in given graph.
        A source node has no incoming edges. This is determined
        by calculating the in-degree of each node in the graph.
        If nodes in-degree == 0, it is a source node

        Args:
            g (DiGraph): Graph to examine

        Returns:
            list: List of source node names or an empty list is there are none.
        """
        s = list()
        for node in g.nodes():
            in_deg = g.in_degree(node)
            if in_deg == 0:
                # logging.debug("node:{0} is a source node".format(node))
                s.append(node)
        return s

    @staticmethod
    def edges_causing_loops(g):
        """Returns a list of edges whose removal from g results in it becoming acyclic."""
        result = list()
        h = g.copy()  # Let's work on a copy of the graph
        while True:
            try:
                cycle = list(nx.find_cycle(h))
            except nx.NetworkXNoCycle:
                break
            edge = random.choice(cycle)
            h.remove_edge(*edge)
            result.append(edge)
        return result

    @staticmethod
    def export_to_graphml(g, path):
        """Export given graph to a path in GraphML format.

        Args:
            g (DiGraph): Graph to export
            path (str): Full output path for GraphML file

        Returns:
            bool: Operation success status
        """
        if not nx.is_directed_acyclic_graph(g):
            return False
        nx.write_graphml(g, path, prettyprint=True)
        return True

    @Slot("QVariant")
    def receive_item_execution_finished(self, item_finish_state):
        """TODO: Method obsolete?
        Pop next project item to execute or finish current graph if there are no items left.

        Args:
            item_finish_state (ExecutionState): an enumeration to indicate if execution should continue or not
        """
        anim = self.running_item.make_execution_leave_animation()
        anim.finished.connect(lambda: QTimer.singleShot(0, self._execute_next_item))
        anim.start()
