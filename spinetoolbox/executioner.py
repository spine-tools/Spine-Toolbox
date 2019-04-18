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

    def unify_graphs(self, src_node, dst_node):
        """Makes a union between graphs that contain the
        given nodes and saves a reference of the resulting
        graph. Removes the graphs that were unionized.

        Args:
            src_node (str): Source project item node name
            dst_node (str): Destination project item node name
        """
        src_graph = self.dag_with_node(src_node)
        dst_graph = self.dag_with_node(dst_node)
        common_nodes = src_graph.nodes() & dst_graph.nodes()
        if len(common_nodes) > 0:
            logging.debug("Common nodes detected:{0}".format(common_nodes))  # TODO: Does not work
            if src_graph.nodes() == dst_graph.nodes():
                logging.debug("src_graph==dst_graph. Adding edge")
                # Just add edge to src_graph
                src_graph.add_edge(src_node, dst_node)
                return
            else:
                logging.debug("src graph:{0} dst_graph:{1}".format(src_graph.nodes(), dst_graph.nodes()))
                common_graph = nx.intersection(src_graph, dst_graph)
                common_graph.add_edge(src_node, dst_node)
                self.add_dag(common_graph)
        else:
            union_dag = nx.union(src_graph, dst_graph)
            union_dag.add_edge(src_node, dst_node)
            self.add_dag(union_dag)
        # Remove src and dst graphs
        self.remove_dag(src_graph)
        self.remove_dag(dst_graph)
        return

    def remove_dag_edge(self, src_node, dst_node):
        """Removes edge from a directed graph.
        # TODO: Handle case when graph is not a dag (has a cycle) and the offending edge is removed

        # TODO: Clean up and change method name to split_graphs() or something

        Args:
            src_node (str): Source project item node name
            dst_node (str): Destination project item node name
        """
        dag = self.dag_with_edge(src_node, dst_node)
        dag_copy = copy.deepcopy(dag)
        logging.debug("dag nodes:{0} edges:{1}".format(dag.nodes(), dag.edges()))
        logging.debug("Removing edge {0}->{1}".format(src_node, dst_node))
        dag.remove_edge(src_node, dst_node)
        # Check if src or dst node is without connections (isolated) after removing the edge
        if self.node_is_isolated(src_node):
            # Remove node from original dag and make a new graph with this node
            logging.debug("src node is isolated")
            dag.remove_node(src_node)
            g = nx.DiGraph()
            g.add_node(src_node)
            self.add_dag(g)
            return
        if self.node_is_isolated(dst_node):
            # Remove node from original dag and make a new graph with this node
            logging.debug("dst node is isolated")
            dag.remove_node(dst_node)
            g = nx.DiGraph()
            g.add_node(dst_node)
            self.add_dag(g)
            return
        # Now for the fun part.
        # If src node is still in any edge in the original graph, the src
        # node is still part of the same graph, return and we're fine
        if nx.has_path(dag, src_node, dst_node):
            logging.debug("There's still a path from {0}->{1}".format(src_node, dst_node))
            return
        src_descendants = nx.descendants(dag_copy, src_node)  # From copy since edge has been removed in dag already
        src_desc_edges = nx.edges(dag_copy, src_descendants)  # to descendant graph
        other_desc_edges = dag.edges()

        src_ancestors = nx.ancestors(dag, dst_node)  # note: from dag
        src_ancestor_edges = nx.edges(dag, src_ancestors)  # to descendant graph
        dst_ancestors = nx.ancestors(dag_copy, dst_node)
        dst_ancestor_edges = nx.edges(dag_copy, dst_ancestors)  # to ancestor graph

        logging.debug("src_descendants:{0} src_desc_edges:{1}".format(src_descendants, src_desc_edges))
        logging.debug("src_ancestors:{0} src_ancestor_edges:{1}".format(src_ancestors, src_ancestor_edges))
        logging.debug("other_desc_edges:{0}".format(other_desc_edges))
        logging.debug("dst_ancestors:{0} dst_ancestor_edges:{1}".format(dst_ancestors, dst_ancestor_edges))

        # Build new graph from the remaining edges in the original DAG
        descendant_graph = nx.DiGraph()
        # If there are no edges left, the remaining graph contains only one node
        if len(src_desc_edges) == 0 and len(other_desc_edges) == 0:
            logging.debug("Descendant graph is a single node")
            descendant_graph.add_node(dst_node)
        else:
            # The remaining DAG has edges. Add them all to a graph
            descendant_graph.add_edges_from(src_desc_edges)
            descendant_graph.add_edges_from(src_ancestor_edges)
            logging.debug("Descendant graph edges: {0}".format(descendant_graph.edges()))

        # Build another graph from nodes and edges that are connected to src_node
        ancestor_graph = nx.DiGraph()
        # Remove all edges that are already in descendant graph
        for edge in descendant_graph.edges():
            logging.debug("Removing edge:{0} from dag copy".format(edge))
            dag_copy.remove_edge(edge[0], edge[1])
        # Remove also the edge we are trying to remove from the dag copy
        logging.debug("Removing edge {0}->{1} from dag copy".format(src_node, dst_node))
        dag_copy.remove_edge(src_node, dst_node)
        # If there are no edges left, the remaining graph contains only one node
        if len(dag_copy.edges()) == 0:
            logging.debug("Ancestor graph is a single node")
            ancestor_graph.add_node(src_node)
        else:
            # The remaining DAG has edges. Add them all to a graph
            logging.debug("Ancestor graph has edges:{0}".format(dag_copy.edges()))
            ancestor_graph.add_edges_from(dag_copy.edges())

        # logging.debug("dag nodes:{0} edges:{1}".format(dag.nodes(), dag.edges()))
        # logging.debug("dag copy nodes:{0} edges:{1}".format(dag_copy.nodes(), dag_copy.edges()))
        logging.debug("descendant_graph nodes:{0} edges:{1}"
                      .format(descendant_graph.nodes(), descendant_graph.edges()))
        logging.debug("ancestor_graph nodes:{0} edges:{1}"
                      .format(ancestor_graph.nodes(), ancestor_graph.edges()))
        # Add new graph
        self.remove_dag(dag)
        self.add_dag(descendant_graph)
        self.add_dag(ancestor_graph)

    def remove_node_from_graph(self, node_name):
        """Removes node from a graph that contains
        it when the project item is deleted.

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
        sources = self.source_nodes()
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

    def get_successors(self, graph, start_node):
        stack = [start_node]
        while stack:
            node = stack.pop()
            succs = g.successors(node)
            stack += succs
            print('%s -> %s' % (node, succs))

    def source_nodes(self):
        """Returns a set of project item names that do not have input items,
        i.e. they are source nodes as required by the bfs-search algorithm.

        Returns:
            obj:'set' of obj:'str': List of source project item names
        """
        # TODO: This method should probably be in ConnectionModel class
        names = self._toolbox.project_item_model.item_names()
        sources = set()
        for name in names:  # Iterate all project items
            input_items = self._toolbox.connection_model.input_items(name)
            if len(input_items) == 0:
                sources.add(name)
            elif len(input_items) == 1 and input_items[0] == name:
                # It only has a feedback link
                sources.add(name)
        return sources

    def node_is_isolated(self, pi_name):
        """Checks if the project item with the given name has any connections.

        Args:
            pi_name (str): Project item name

        Returns:
            bool: True if project item has no input nor output connections, False if it does
        """
        inputs = self._toolbox.connection_model.input_items(pi_name)
        outputs = self._toolbox.connection_model.output_items(pi_name)
        if len(inputs) == 0 and len(outputs) == 0:
            return True
        elif len(inputs) == 1 and len(outputs) == 1:
            if inputs[0] == outputs[0]:
                logging.debug("Node is isolated since it only has a feedback loop")
                return True
        else:
            return False
