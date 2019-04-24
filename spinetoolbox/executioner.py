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
import copy
import networkx as nx


class DirectedGraphHandler:
    def __init__(self, toolbox):
        """Constructor."""
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
        # logging.debug("dag nodes:{0} edges:{1}".format(dag.nodes(), dag.edges()))
        # logging.debug("Removing edge {0}->{1}".format(src_node, dst_node))
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
        # If src node still has a path to dst node, return and we're fine
        if nx.has_path(dag, src_node, dst_node):
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
        # logging.debug("descendant_graph nodes:{0} edges:{1}"
        #               .format(descendant_graph.nodes(), descendant_graph.edges()))
        # logging.debug("ancestor_graph nodes:{0} edges:{1}"
        #               .format(ancestor_graph.nodes(), ancestor_graph.edges()))
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
        g = self.dag_with_node(node_name)
        edges_to_remove = list()
        # Loop through edges and remove all that has the node
        logging.debug("Removing node {0}. g nodes:{1} and edges:{2}"
                      .format(node_name, g.nodes(), g.edges()))
        for edge in g.edges():
            if edge[0] == node_name or edge[1] == node_name:
                edges_to_remove.append(edge)
        g.remove_edges_from(edges_to_remove)
        # Now remove the node itself
        g.remove_node(node_name)
        logging.debug("after removal g nodes:{1} and edges:{2}"
                      .format(node_name, g.nodes(), g.edges()))
        # If only a single node with no edges remains -> return
        if len(g.nodes()) == 1 and len(g.edges()) == 0:
            return
        # Loop through remaining nodes and check if any of them are isolated now
        nodes_to_remove = list()
        for node in g.nodes():
            if self.node_is_isolated(node):
                logging.debug("Creating a new graph for node {0}".format(node))
                nodes_to_remove.append(node)
                h = nx.DiGraph()
                h.add_node(node)
                self.add_dag(h)
        g.remove_nodes_from(nodes_to_remove)
        if len(g.nodes()) == 0:
            logging.debug("Removing g from dag list since its empty")
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

    def execution_order(self):
        """Builds a list or an iterator of all graphs in the project.
        Returns a dictionary of project item names in the breadth-first
        search order.

        Returns:
            dict: Key is the index number of the graph starting from 1.
            Value is an ordered list of project item names.
        """
        sources = self._toolbox.connection_model.source_items()  # Give this as argument for this method
        n = len(self.dags())
        t = 1
        exec_dict = dict()
        for dag in self.dags():
            exec_order = list()
            if not nx.is_directed_acyclic_graph(dag):  # TODO: Does this work?
                logging.debug("This graph is not a DAG")
            else:
                logging.debug("Executing dag ({0}/{1}) n nodes:{2} n edges:{3}"
                              .format(t, n, len(dag.nodes()), len(dag.edges())))
                logging.debug("nodes:{0}".format(dag.nodes()))
                if len(dag.edges()) > 0:
                    logging.debug("edges:{0}".format(dag.edges()))
                # Intersection of source items and nodes in current graph
                sources_in_dag = sources & dag.nodes()
                logging.debug("Source items in this graph:{0}".format(sources_in_dag))
                if len(sources_in_dag) == 0:
                    logging.error("No sources for this graph found. Execution failed.")
                else:
                    source = sources_in_dag.pop()
                    logging.debug("Using {0} as source".format(source))
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
                        logging.debug("src:{0} dst:{1}".format(src, dst))
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

    def node_is_isolated(self, node):
        """Checks if the project item with the given name has any connections.

        Args:
            node (str): Project item name

        Returns:
            bool: True if project item has no in-neighbors nor out-neighbors, False if it does
        """
        g = self.dag_with_node(node)
        return nx.is_isolate(g, node)
