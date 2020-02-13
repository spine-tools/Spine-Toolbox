:mod:`spinetoolbox.dag_handler`
===============================

.. py:module:: spinetoolbox.dag_handler

.. autoapi-nested-parse::

   Contains classes for handling DAGs.

   :author: P. Savolainen (VTT)
   :date:   8.4.2019



Module Contents
---------------

.. py:class:: DirectedGraphHandler

   Bases: :class:`PySide2.QtCore.QObject`

   Class for manipulating graphs according to user's actions.

   .. attribute:: dag_simulation_requested
      

      

   .. method:: dags(self)


      Returns a list of graphs (DiGraph) in the project.


   .. method:: add_dag(self, dag, request_simulation=True)


      Add graph to list.

      :param dag: Graph to add
      :type dag: DiGraph
      :param request_simulation: if True, emits dag_simulation_requested
      :type request_simulation: bool


   .. method:: remove_dag(self, dag)


      Remove graph from instance variable list.

      :param dag: Graph to remove
      :type dag: DiGraph


   .. method:: add_dag_node(self, node_name)


      Create directed graph with one node and add it to list.

      :param node_name: Project item name to add as a node
      :type node_name: str


   .. method:: add_graph_edge(self, src_node, dst_node)


      Adds an edge between the src and dst nodes. If nodes are in
      different graphs, the reference to union graph is saved and the
      references to the original graphs are removed. If src and dst
      nodes are already in the same graph, the edge is added to the graph.
      If src and dst are the same node, a self-loop (feedback) edge is
      added.

      :param src_node: Source project item node name
      :type src_node: str
      :param dst_node: Destination project item node name
      :type dst_node: str


   .. method:: remove_graph_edge(self, src_node, dst_node)


      Removes edge from a directed graph.

      :param src_node: Source project item node name
      :type src_node: str
      :param dst_node: Destination project item node name
      :type dst_node: str


   .. method:: remove_node_from_graph(self, node_name)


      Removes node from a graph that contains
      it. Called when project item is removed from project.

      :param node_name: Project item name
      :type node_name: str


   .. method:: rename_node(self, old_name, new_name)


      Handles renaming the node and edges in a graph when a project item is renamed.

      :param old_name: Old project item name
      :type old_name: str
      :param new_name: New project item name
      :type new_name: str

      :returns: True if successful, False if renaming failed
      :rtype: bool


   .. method:: dag_with_node(self, node_name)


      Returns directed graph that contains given node.

      :param node_name: Node to look for
      :type node_name: str

      :returns: Directed graph that contains node or None if not found.
      :rtype: (DiGraph)


   .. method:: dag_with_edge(self, src_node, dst_node)


      Returns directed graph that contains given edge.

      :param src_node: Source node name
      :type src_node: str
      :param dst_node: Destination node name
      :type dst_node: str

      :returns: Directed graph that contains edge or None if not found.
      :rtype: (DiGraph)


   .. method:: node_successors(g)
      :staticmethod:


      Returns a dict mapping nodes in the given graph to a list of its direct successors.
      The nodes are in topological sort order.
      Topological sort in the words of networkx:
      "a nonunique permutation of the nodes, such that an edge from u to v
      implies that u appears before v in the topological sort order."

      :param g: Directed graph to process
      :type g: DiGraph

      :returns: key is the node name, value is list of successor names
                Empty dict if given graph is not a DAG.
      :rtype: dict


   .. method:: successors_til_node(self, g, node)


      Like node_successors but only until the given node,
      and ignoring all nodes that are not its ancestors.


   .. method:: node_is_isolated(self, node, allow_self_loop=False)


      Checks if the project item with the given name has any connections.

      :param node: Project item name
      :type node: str
      :param allow_self_loop: If default (False), Self-loops are considered as an
                              in-neighbor or an out-neighbor so the method returns False. If True,
                              single node with a self-loop is considered isolated.
      :type allow_self_loop: bool

      :returns:

                True if project item has no in-neighbors nor out-neighbors, False if it does.
                    Single node with a self-loop is NOT isolated (returns False).
      :rtype: bool


   .. method:: source_nodes(g)
      :staticmethod:


      Returns a list of source nodes in given graph.
      A source node has no incoming edges. This is determined
      by calculating the in-degree of each node in the graph.
      If nodes in-degree == 0, it is a source node

      :param g: Graph to examine
      :type g: DiGraph

      :returns: List of source node names or an empty list is there are none.
      :rtype: list


   .. method:: edges_causing_loops(g)
      :staticmethod:


      Returns a list of edges whose removal from g results in it becoming acyclic.


   .. method:: export_to_graphml(g, path)
      :staticmethod:


      Export given graph to a path in GraphML format.

      :param g: Graph to export
      :type g: DiGraph
      :param path: Full output path for GraphML file
      :type path: str

      :returns: Operation success status
      :rtype: bool


   .. method:: receive_item_execution_finished(self, item_finish_state)


      TODO: Method obsolete?
      Pop next project item to execute or finish current graph if there are no items left.

      :param item_finish_state: an enumeration to indicate if execution should continue or not
      :type item_finish_state: ExecutionState



