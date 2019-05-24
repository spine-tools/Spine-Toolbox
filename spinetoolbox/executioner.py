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
Contains classes for handling project item execution.

:author: P. Savolainen (VTT)
:date:   8.4.2019
"""

import logging
import os
import copy
from PySide2.QtCore import Signal, Slot, QObject
import networkx as nx


class DirectedGraphHandler:
    """Class for manipulating graphs according to user's actions.

    Args:
        toolbox (ToolboxUI): QMainWindow instance
    """
    def __init__(self, toolbox):
        """Class constructor."""
        self._toolbox = toolbox
        self.running_dag = None
        self.running_item = None
        self._dags = list()

    def dags(self):
        """Returns a list of graphs (DiGraph) in the project."""
        return self._dags

    def add_dag(self, dag):
        """Add graph to list.

        Args:
            dag (DiGraph): Graph to add
        """
        self._dags.append(dag)

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
        self._dags.append(dag)

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
        if src_node == dst_node:
            # Add self-loop to src graph and return
            src_graph.add_edge(src_node, dst_node)
            return
        if src_graph == dst_graph:
            # src and dst are already in same graph. Just add edge to src_graph and return
            src_graph.add_edge(src_node, dst_node)
            return
        # Unify graphs
        union_dag = nx.union(src_graph, dst_graph)
        union_dag.add_edge(src_node, dst_node)
        self.add_dag(union_dag)
        # Remove src and dst graphs
        self.remove_dag(src_graph)
        self.remove_dag(dst_graph)
        return

    def remove_graph_edge(self, src_node, dst_node):
        """Removes edge from a directed graph.

        Args:
            src_node (str): Source project item node name
            dst_node (str): Destination project item node name
        """
        dag = self.dag_with_edge(src_node, dst_node)
        if src_node == dst_node:  # Removing self-loop
            dag.remove_edge(src_node, dst_node)
            return
        dag_copy = copy.deepcopy(dag)  # Make a copy before messing with the graph
        dag.remove_edge(src_node, dst_node)
        # Check if src or dst node is isolated (without connections) after removing the edge
        if self.node_is_isolated(src_node):
            dag.remove_node(src_node)  # Remove node from original dag
            g = nx.DiGraph()
            g.add_node(src_node)  # Make a new graph containing only the isolated node
            self.add_dag(g)
            return
        if self.node_is_isolated(dst_node):
            dag.remove_node(dst_node)
            g = nx.DiGraph()
            g.add_node(dst_node)
            self.add_dag(g)
            return
        # If src node still has a path (ignoring edge directions) to dst node -> return, we're fine
        if self.nodes_connected(dag, src_node, dst_node):
            return
        # Now for the fun part
        src_descendants = nx.descendants(dag_copy, src_node)  # From copy since edge has been removed from dag already
        src_descendant_edges = nx.edges(dag_copy, src_descendants)  # to descendant graph
        src_ancestors = nx.ancestors(dag, dst_node)  # note: from dag
        src_ancestor_edges = nx.edges(dag, src_ancestors)  # to descendant graph (note: from dag)
        # Build new graph from the remaining edges in the original DAG
        # This is the graph that is now upstream (left-side) from the removed edge
        descendant_graph = nx.DiGraph()
        # Populate descendant graph with src descendant and src ancestor edges
        descendant_graph.add_edges_from(src_descendant_edges)
        descendant_graph.add_edges_from(src_ancestor_edges)
        # Build another graph from the edges in the original graph that are not in descendant graph already
        # This is the graph that is now downstream (right-side) from the removed edge
        ancestor_graph = nx.DiGraph()
        # Remove all edges that are already in descendant graph
        for edge in descendant_graph.edges():
            dag.remove_edge(edge[0], edge[1])
        # Add remaining edges to a new graph
        # Another option is to leave the original dag in the list but
        # then we would also need to remove isolated nodes from it (dag) as well
        ancestor_graph.add_edges_from(dag.edges())
        # Add new graph
        self.remove_dag(dag)
        self.add_dag(descendant_graph)
        self.add_dag(ancestor_graph)

    def remove_node_from_graph(self, node_name):
        """Removes node from a graph that contains
        it. Called when project item is removed from project.

        Args:
            node_name (str): Project item name
        """
        # This is called every time a previous project is closed and another is opened.
        g = self.dag_with_node(node_name)
        edges_to_remove = list()
        for edge in g.edges():
            if edge[0] == node_name or edge[1] == node_name:
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
        if len(g.nodes()) == 0:
            self.remove_dag(g)

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
        return

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
        logging.error("Graph containing node {0} not found. Something is wrong.".format(node_name))
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
        logging.error("Graph containing edge {0}->{1} not found. Something is wrong.".format(src_node, dst_node))
        return None

    def execution_order(self, sources):
        """Builds a list or an iterator of all graphs in the project.
        Returns a dictionary of project item names in the breadth-first
        search order.

        Args:
            sources (list-of-str): Source project items in project. I.e items that do not have input items.

        Returns:
            dict: Key is the index number of the graph starting from 1.
            Value is an ordered list of project item names.
        """
        n = len(self.dags())
        t = 1
        exec_dict = dict()
        for dag in self.dags():
            exec_order = list()
            if not nx.is_directed_acyclic_graph(dag):
                logging.debug("This graph is not a DAG")
                # TODO: Do something here
            else:

                # TODO: Try fixing this by adding a source node for all 'sources' (the argument)
                # TODO: Then use this dummy source as the source for the bfs-algorithm

                # logging.debug("Executing dag ({0}/{1}) n nodes:{2} n edges:{3}"
                #               .format(t, n, len(dag.nodes()), len(dag.edges())))
                # Intersection of source items and nodes in current graph
                sources_in_dag = sources & dag.nodes()
                # logging.debug("Sources in current dag:{0}".format(sources_in_dag))
                if len(sources_in_dag) == 0:
                    # Should not happen if nx.is_directed_acyclic_graph() works
                    logging.error("No sources for this graph found. Execution failed.")
                else:
                    source = sources_in_dag.pop()
                    # logging.debug("Using {0} as source".format(source))
                    edges_to_execute = list(nx.bfs_edges(dag, source))
                    # successor_iter = list(nx.bfs_successors(dag, source))  # TODO: Test bfs_successors(G, source)
                    exec_order = list()

                    # stack = [source]
                    # while stack:
                    #     node = stack.pop()
                    #     succs = dag.successors(node)
                    #     stack += succs
                    #     logging.debug('%s -> %s' % (node, stack))
                    #     exec_order.append(node)
                    #     for suc in stack:
                    #         logging.debug("Adding node:{0}".format(suc))
                    #         exec_order.append(suc)

                    exec_order.append(source)
                    # Add other source nodes to exec_order
                    # TODO: This does not work if other sources have children
                    exec_order += sources_in_dag
                    for edge in edges_to_execute:
                        src, dst = edge
                        # logging.debug("src:{0} dst:{1}".format(src, dst))
                        if src not in exec_order:
                            exec_order.append(src)
                        if dst not in exec_order:
                            exec_order.append(dst)
            exec_dict[t] = exec_order
            t += 1
        return exec_dict

    # def get_successors(self, graph, start_node):
    #     stack = [start_node]
    #     while stack:
    #         node = stack.pop()
    #         succs = g.successors(node)
    #         stack += succs
    #         print('%s -> %s' % (node, succs))

    def calc_exec_order(self, node_name):
        """Returns an ordered list of node names of the graph that contains given node.

        Args:
            node_name (str): Node whose graph is processed

        Returns:
            list: bfs-ordered list of node names
        """
        g = self.dag_with_node(node_name)
        if not nx.is_directed_acyclic_graph(g):
            return None
        # Get source nodes by calculating in-degrees. If in-degree == 0 -> source node
        sources = list()
        for node in g.nodes():
            in_deg = g.in_degree(node)
            if in_deg == 0:
                logging.debug("node:{0} is a source node".format(node))
                sources.append(node)
        if len(sources) == 0:
            # Should not happen if nx.is_directed_acyclic_graph() works
            logging.error("This graph has no source nodes. Execution failed.")
            return None
        # Get execution order
        src = sources.pop()
        edges_to_execute = list(nx.bfs_edges(g, src))
        exec_order = list()
        exec_order.append(src)
        # Add other source nodes to exec_order
        # TODO: This does not work if other sources have children
        exec_order += sources
        for src, dst in edges_to_execute:
            # src, dst = edge
            # logging.debug("src:{0} dst:{1}".format(src, dst))
            if src not in exec_order:
                exec_order.append(src)
            if dst not in exec_order:
                exec_order.append(dst)
        return exec_order

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

    def nodes_connected(self, dag, a, b):
        """Checks if node a is connected to node b. Edge directions are ignored.
        If any of source node a's ancestors or descendants have a path to destination
        node b, returns True. Also returns True if destination node b has a path to
        any of source node a's ancestors or descendants.

        Args:
            dag (DiGraph): Graph that contains nodes a and b
            a (str): Node name
            b (str): Another node name

        Returns:
            bool: True if a and b are connected, False otherwise
        """
        src_anc = nx.ancestors(dag, a)
        src_des = nx.descendants(dag, a)
        # logging.debug("src {0} ancestors:{1}. descendants:{2}".format(a, src_anc, src_des))
        # Check ancestors
        for anc in src_anc:
            # Check if any src ancestor has a path to dst node
            if nx.has_path(dag, anc, b):
                # logging.debug("Found path from anc {0} to dst {1}".format(anc, b))
                return True
            # Check if dst node has a path to any src ancestor
            if nx.has_path(dag, b, anc):
                # logging.debug("Found path from dst {0} to anc {1}".format(b, anc))
                return True
        # Check descendants
        for des in src_des:
            # Check if any src descendant has a path to dst node
            if nx.has_path(dag, des, b):
                # logging.debug("Found path from des {0} to dst {1}".format(des, b))
                return True
            # Check if dst node has a path to any src descendant
            if nx.has_path(dag, b, des):
                # logging.debug("Found path from dst {0} to des {1}".format(b, des))
                return True
        return False


class ExecutionInstance(QObject):
    """Class for the graph that is being executed. Contains references to
    files and resources advertised by project items so that project items downstream can find them.

    Args:
        toolbox (ToolboxUI): QMainWindow instance
        dag (DiGraph): Graph that is executed
        execution_list (list): Ordered list of nodes to execute
    """
    graph_execution_finished_signal = Signal(name="graph_execution_finished_signal")
    project_item_execution_finished_signal = Signal(int, name="project_item_execution_finished_signal")

    def __init__(self, toolbox, dag, execution_list):
        """Class constructor."""
        QObject.__init__(self)
        self._toolbox = toolbox
        self.dag = dag  # networkx.DiGraph() instance that is being executed
        self.execution_list = execution_list  # Ordered list of nodes to execute. First node at index 0
        self.running_item = None
        self.dc_refs = list()  # Data Connection reference list
        self.dc_files = list()  # Data Connection file list
        self.tool_output_files = list()  # Paths to result files from ToolInstance

    def start_execution(self):
        """Pops the next item from the execution list and starts executing it."""
        logging.debug("dc refs:{0}".format(self.dc_refs))
        logging.debug("dc files:{0}".format(self.dc_files))
        self.running_item = self.execution_list.pop(0)
        self.execute_project_item()

    def execute_project_item(self):
        """Starts executing project item."""
        self.project_item_execution_finished_signal.connect(self.item_execution_finished)
        item_ind = self._toolbox.project_item_model.find_item(self.running_item)
        item = self._toolbox.project_item_model.project_item(item_ind)
        item.execute()

    @Slot(int, name="item_execution_finished")
    def item_execution_finished(self, abort):
        """Pop next project item to execute or finish current graph if there are no items left.

        Args:
            abort (int): 0=Continue to next project item. 1=Abort execution (when e.g. Tool crashes or something)
        """
        self.project_item_execution_finished_signal.disconnect()
        if abort == 1:
            self._toolbox.msg.emit("Execution aborted due to an error")
            self.graph_execution_finished_signal.emit()
            return
        try:
            self.running_item = self.execution_list.pop(0)
        except IndexError:
            self.graph_execution_finished_signal.emit()
            return
        self.execute_project_item()

    def append_dc_refs(self, refs):
        """Adds given file paths (Data Connection file references) to a list."""
        self.dc_refs += refs

    def append_dc_files(self, files):
        """Adds given project data file paths to a list."""
        self.dc_files += files

    def append_tool_output_file(self, filepath):
        """Adds given file path to a list containing paths to Tool output files."""
        self.tool_output_files.append(filepath)

    def find_file(self, filename):
        """Returns the first occurrence to full path to given file name or None if file was not found.

        Args:
            filename (str): Searched file name (no path) TODO: Change to pattern
        """
        for dc_ref in self.dc_refs:
            _, file_candidate = os.path.split(dc_ref)
            if file_candidate == filename:
                logging.debug("Found path for {0} from dc refs: {1}".format(filename, dc_ref))
                return dc_ref
        for dc_file in self.dc_files:
            _, file_candidate = os.path.split(dc_file)
            if file_candidate == filename:
                logging.debug("Found path for {0} from dc files: {1}".format(filename, dc_file))
                return dc_file
        for tool_file in self.tool_output_files:
            _, file_candidate = os.path.split(tool_file)
            if file_candidate == filename:
                logging.debug("Found path for {0} from Tool result files: {1}".format(filename, tool_file))
                return tool_file
        return None
