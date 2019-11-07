######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Spine Toolbox project class.

:authors: P. Savolainen (VTT), E. Rinne (VTT)
:date:   10.1.2018
"""

import os
import logging
import json
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QMessageBox
from .metaobject import MetaObject
from .helpers import DEFAULT_PROJECT_DIR, create_dir, copy_dir
from .tool_specifications import JuliaTool, PythonTool, GAMSTool, ExecutableTool
from .config import DEFAULT_WORK_DIR, INVALID_CHARS
from .executioner import DirectedGraphHandler, ExecutionInstance


class SpineToolboxProject(MetaObject):
    """Class for Spine Toolbox projects."""

    def __init__(self, toolbox, name, description, work_dir=None, ext='.proj', location=""):
        """

        Args:
            toolbox (ToolboxUI): toolbox of this project
            name (str): Project name
            description (str): Project description
            work_dir (str): Project work directory
            ext (str): Project save file extension(.proj)
            location (str): If this is given, create a new style project
        """
        super().__init__(name, description)
        self._toolbox = toolbox
        self._qsettings = self._toolbox.qsettings()
        self.dag_handler = DirectedGraphHandler(self._toolbox)
        self._ordered_dags = dict()  # Contains all ordered lists of items to execute in the project
        self.execution_instance = None
        self._graph_index = 0
        self._n_graphs = 0
        self._executed_graph_index = 0
        self._invalid_graphs = list()
        self.path = None  # Old style projects initialize this. Not in use with new style projects
        self.filename = None
        self.dirty = False  # TODO: Indicates if project has changed since loading
        if location == "":
            self.init_old_style_project(work_dir, ext)
        else:
            self.project_dir = None
            self.project_conf_dir = None
            self.project_items_dir = None
            self.project_filename = None
            self.project_file = None
            self.work_dir = None
            if not self.__create_project_structure(location):
                self._toolbox.msg_error.emit("Creating project directory "
                                             "structure to <b>{0}</b> failed"
                                             .format(location))
            if not self.create_work_directory(DEFAULT_WORK_DIR):
                self._toolbox.msg_error.emit("Creating work directory failed".format(self.project_dir))

    def connect_signals(self):
        """Connect signals to slots."""
        self.dag_handler.dag_simulation_requested.connect(self.simulate_dag_execution)

    def init_old_style_project(self, work_dir, ext):
        """Initialize project from the old .proj file."""
        self.project_dir = os.path.join(DEFAULT_PROJECT_DIR, self.short_name)
        if not work_dir:
            self.work_dir = DEFAULT_WORK_DIR
        else:
            self.work_dir = work_dir
        self.filename = self.short_name + ext
        self.path = os.path.join(DEFAULT_PROJECT_DIR, self.filename)
        # Make project directory
        try:
            create_dir(self.project_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating project directory {0} failed. Check permissions.".format(self.project_dir)
            )
        # Make work directory
        try:
            create_dir(self.work_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating work directory {0} failed. Check permissions.".format(self.work_dir)
            )

    def _create_project_structure(self, directory):
        """Makes the given directory a Spine Toolbox project directory.
        Creates directories and files that are common to all projects.

        Args:
            directory (str): Abs. path to a directory that should be made into a project directory
        """
        self.project_dir = directory
        self.project_conf_dir = os.path.abspath(os.path.join(self.project_dir, ".spinetoolbox"))
        self.project_items_dir = os.path.abspath(os.path.join(self.project_conf_dir, "items"))
        self.project_filename = "project.json"  # Project file
        self.project_file = os.path.abspath(os.path.join(self.project_conf_dir, self.project_filename))
        self.path = None
        self.filename = None
        try:
            create_dir(self.project_dir)  # Make project directory
        except OSError:
            self._toolbox.msg_error.emit("Creating directory {0} failed".format(self.project_dir))
            return False
        try:
            create_dir(self.project_conf_dir)  # Make project conf directory
        except OSError:
            self._toolbox.msg_error.emit("Creating directory {0} failed".format(self.project_dir))
            return False
        try:
            create_dir(self.project_items_dir)  # Make project items directory
        except OSError:
            self._toolbox.msg_error.emit("Creating directory {0} failed".format(self.project_dir))
            return False
        return True

    def make_work_directory(self, work_dir=None):
        """Creates work directory.

        Args:
            work_dir (str): Absolute path to a directory that should be created for a work directory
        """
        if not work_dir:
            self.work_dir = DEFAULT_WORK_DIR
        else:
            self.work_dir = work_dir
        try:
            create_dir(self.work_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating work directory {0} failed. Check permissions.".format(self.work_dir)
            )
            return False
        return True

    def change_name(self, name):
        """Changes project name and updates project dir and save file name.

        Args:
            name (str): Project (long) name
        """
        super().set_name(name)
        # Update project dir instance variable
        self.project_dir = os.path.join(DEFAULT_PROJECT_DIR, self.short_name)
        # Update file name and path
        self.change_filename(self.short_name + ".proj")

    def change_filename(self, new_filename):
        """Change the save filename associated with this project.

        Args:
            new_filename (str): Filename used in saving the project. No full path. Example 'project.proj'
        """
        self.filename = new_filename
        self.path = os.path.join(DEFAULT_PROJECT_DIR, self.filename)

    def change_work_dir(self, new_work_path):
        """Change project work directory.

        Args:
            new_work_path (str): Absolute path to new work directory
        """
        if not new_work_path:
            self.work_dir = DEFAULT_WORK_DIR
            return False
        if not create_dir(new_work_path):
            return False
        self.work_dir = new_work_path
        return True

    def rename_project(self, name):
        """Save project under a new name. Used with File->Save As... menu command.
        Checks if given project name is valid.

        Args:
            name (str): New (long) name for project
        """
        # Check for illegal characters
        if name.strip() == '' or name.lower() == self.name.lower():
            self._toolbox.msg_warning.emit("Renaming project cancelled")
            return False
        # Check if new short name is the same as the current one
        new_short_name = name.lower().replace(" ", "_")
        if new_short_name == self.short_name:
            msg = "<b>{0}</b> project directory already taken.".format(new_short_name)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Try again", msg)
            return False
        # Check that new name is legal
        if any(True for x in name if x in INVALID_CHARS):
            msg = "<b>{0}</b> contains invalid characters.".format(name)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Invalid characters", msg)
            return False
        # Check that the new project name directory is not taken
        projects_path = DEFAULT_PROJECT_DIR  # Path to directory where project files (.proj) are
        new_project_dir = os.path.join(projects_path, new_short_name)  # New project directory
        taken_dirs = list()
        dir_contents = [os.path.join(projects_path, x) for x in os.listdir(projects_path)]
        for path in dir_contents:
            if os.path.isdir(path):
                taken_dirs.append(os.path.split(path)[1])
        if new_short_name in taken_dirs:
            msg = "Project directory <b>{0}</b> already exists.".format(new_project_dir)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Try again", msg)
            return False
        # Copy project directory to new project directory
        if not copy_dir(self._toolbox, self.project_dir, new_project_dir):
            self._toolbox.msg_error.emit("Copying project directory failed")
            return False
        # Change name
        self.change_name(name)
        return True

    def save(self, tool_def_paths, directory=None):
        """Collect project information and objects
        into a dictionary and write to a JSON file.

        Args:
            tool_def_paths (list): List of paths to tool definition files
            directory (str): Abs. path to project directory. Used
            when converting old style projects to new style, and
            when project is saved to a new location (Save as...)

        Returns:
            bool: True or False depending on success
        """
        # Clear dictionary
        project_dict = dict()  # Dictionary for storing project info
        project_dict['name'] = self.name
        project_dict['description'] = self.description
        project_dict['work_dir'] = self.work_dir
        project_dict['tool_specifications'] = tool_def_paths
        # Compute connections directly from Links in scene
        connections = list()
        for link in self._toolbox.ui.graphicsView.links():
            src_connector = link.src_connector
            src_anchor = src_connector.position
            src_name = src_connector.parent_name()
            dst_connector = link.dst_connector
            dst_anchor = dst_connector.position
            dst_name = dst_connector.parent_name()
            conn = {"from": [src_name, src_anchor], "to": [dst_name, dst_anchor]}
            connections.append(conn)
        # Save connections in old format, to keep compatibility with old toolbox versions
        # If and when we're ready to adopt the new format, this can be removed
        item_names = [item.name for item in self._toolbox.project_item_model.items()]
        n_items = len(item_names)
        connections_old = [[False for _ in range(n_items)] for __ in range(n_items)]
        for conn in connections:
            src_name, src_anchor = conn["from"]
            dst_name, dst_anchor = conn["to"]
            i = item_names.index(src_name)
            j = item_names.index(dst_name)
            connections_old[i][j] = [src_anchor, dst_anchor]
        project_dict['connections'] = connections_old
        scene_rect = self._toolbox.ui.graphicsView.scene().sceneRect()
        project_dict["scene_y"] = scene_rect.y()
        project_dict["scene_w"] = scene_rect.width()
        project_dict["scene_h"] = scene_rect.height()
        project_dict["scene_x"] = scene_rect.x()
        items_dict = dict()  # Dictionary for storing project items
        # Traverse all items in project model by category
        for category_item in self._toolbox.project_item_model.root().children():
            category = category_item.name
            category_dict = items_dict[category] = dict()
            for item in self._toolbox.project_item_model.items(category):
                category_dict[item.name] = item.item_dict()
        # Write project on disk
        saved_dict = dict(project=project_dict, objects=items_dict)
        if directory:
            if not self._create_project_structure(directory):
                return False
        # Write into JSON file
        with open(self.project_file, 'w') as fp:
            json.dump(saved_dict, fp, indent=4)
        return True

    def load(self, objects_dict):
        """Populate project item model with items loaded from project file.

        Args:
            objects_dict (dict): Dictionary containing all project items in JSON format

        Returns:
            Boolean value depending on operation success.
        """
        self._toolbox.msg.emit("Loading project items...")
        empty = True
        for category_name, category_dict in objects_dict.items():
            items = []
            for name, item_dict in category_dict.items():
                item_dict.pop("short name", None)
                item_dict["name"] = name
                items.append(item_dict)
                empty = False
            self.add_project_items(category_name, *items, verbosity=False)
        if empty:
            self._toolbox.msg_warning.emit("Project has no items")
        return True

    def load_tool_specification_from_file(self, jsonfile):
        """Create a Tool specification according to a tool definition file.

        Args:
            jsonfile (str): Path of the tool specification definition file

        Returns:
            Instance of a subclass if Tool
        """
        try:
            with open(jsonfile, 'r') as fp:
                try:
                    definition = json.load(fp)
                except ValueError:
                    self._toolbox.msg_error.emit("Tool specification file not valid")
                    logging.exception("Loading JSON data failed")
                    return None
        except FileNotFoundError:
            self._toolbox.msg_error.emit("Tool specification file <b>{0}</b> does not exist".format(jsonfile))
            return None
        # Path to main program relative to definition file
        includes_main_path = definition.get("includes_main_path", ".")
        path = os.path.normpath(os.path.join(os.path.dirname(jsonfile), includes_main_path))
        return self.load_tool_specification_from_dict(definition, path)

    def load_tool_specification_from_dict(self, definition, path):
        """Create a Tool specification according to a dictionary.

        Args:
            definition (dict): Dictionary with the tool definition
            path (str): Folder of the main program file

        Returns:
            Instance of a subclass if Tool
        """
        try:
            _tooltype = definition["tooltype"].lower()
        except KeyError:
            self._toolbox.msg_error.emit(
                "No tool type defined in tool definition file. Supported types are " "'gams', 'julia' and 'executable'"
            )
            return None
        if _tooltype == "julia":
            return JuliaTool.load(self._toolbox, path, definition)
        if _tooltype == "python":
            return PythonTool.load(self._toolbox, path, definition)
        if _tooltype == "gams":
            return GAMSTool.load(self._toolbox, path, definition)
        if _tooltype == "executable":
            return ExecutableTool.load(self._toolbox, path, definition)
        self._toolbox.msg_warning.emit("Tool type <b>{}</b> not available".format(_tooltype))
        return None

    def add_project_items(self, category_name, *items, set_selected=False, verbosity=True):
        """Adds item to project.

        Args:
            category_name (str): The items' category
            items (dict): one or more dict of items to add
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        category_ind = self._toolbox.project_item_model.find_category(category_name)
        if not category_ind:
            self._toolbox.msg_error.emit("Category {0} not found".format(category_name))
            return
        category_item = self._toolbox.project_item_model.project_item(category_ind)
        item_maker = category_item.item_maker()
        for item_dict in items:
            try:
                item = item_maker(self._toolbox, **item_dict)
            except TypeError:
                self._toolbox.msg_error.emit(
                    "Loading project item <b>{0}</b> into category <b>{1}</b> failed. "
                    "This is most likely caused by an outdated project file.".format(item_dict["name"], category_name)
                )
                continue
            self._toolbox.project_item_model.insert_item(item, category_ind)
            # Append new node to networkx graph
            self.add_to_dag(item.name)
            if verbosity:
                self._toolbox.msg.emit("{0} <b>{1}</b> added to project.".format(item.item_type, item.name))
            if set_selected:
                self.set_item_selected(item)

    def add_to_dag(self, item_name):
        """Add new directed graph object."""
        self.dag_handler.add_dag_node(item_name)

    def set_item_selected(self, item):
        """Sets item selected and shows its info screen.

        Args:
            item (ProjectItem): Project item to select
        """
        ind = self._toolbox.project_item_model.find_item(item.name)
        self._toolbox.ui.treeView_project.setCurrentIndex(ind)

    def execute_selected(self):
        """Starts executing selected directed acyclic graph. Selected graph is
        determined by the selected project item(s). Aborts, if items from multiple
        graphs are selected."""
        self._toolbox.ui.textBrowser_eventlog.verticalScrollBar().setValue(
            self._toolbox.ui.textBrowser_eventlog.verticalScrollBar().maximum()
        )
        if not self.dag_handler.dags():
            self._toolbox.msg_warning.emit("Project has no items to execute")
            return
        # Get selected item
        selected_indexes = self._toolbox.ui.treeView_project.selectedIndexes()
        if not selected_indexes:
            self._toolbox.msg_warning.emit("Please select a project item and try again")
            return
        if len(selected_indexes) == 1:
            selected_item = self._toolbox.project_item_model.project_item(selected_indexes[0])
        else:
            # More than one item selected. Make sure they part of the same graph or abort
            selected_item = self._toolbox.project_item_model.project_item(selected_indexes.pop())
            selected_item_graph = self.dag_handler.dag_with_node(selected_item.name)
            for ind in selected_indexes:
                # Check that other selected nodes are in the same graph
                i = self._toolbox.project_item_model.project_item(ind)
                if not self.dag_handler.dag_with_node(i.name) == selected_item_graph:
                    self._toolbox.msg_warning.emit("Please select items from only one graph")
                    return
        self._executed_graph_index = 0  # Needed in execute_selected() just for printing the number
        self._n_graphs = 1
        # Calculate bfs-ordered list of project items to execute
        dag = self.dag_handler.dag_with_node(selected_item.name)
        if not dag:
            self._toolbox.msg_error.emit(
                "[BUG] Could not find a graph containing {0}. "
                "<b>Please reopen the project.</b>".format(selected_item.name)
            )
            return
        ordered_nodes = self.dag_handler.calc_exec_order(dag)
        if not ordered_nodes:
            self._toolbox.msg.emit("")
            self._toolbox.msg_warning.emit(
                "Selected graph is not a directed acyclic graph. "
                "Please edit connections in Design View and try again."
            )
            return
        # Make execution instance, connect signals and start execution
        self.execution_instance = ExecutionInstance(self._toolbox, ordered_nodes)
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("--------------------------------------------------")
        self._toolbox.msg.emit("<b>Executing Selected Directed Acyclic Graph</b>")
        self._toolbox.msg.emit("Order: {0}".format(" -> ".join(list(ordered_nodes))))
        self._toolbox.msg.emit("--------------------------------------------------")
        self.execution_instance.graph_execution_finished_signal.connect(self.graph_execution_finished)
        self.execution_instance.start_execution()
        return

    def execute_project(self):
        """Determines the number of directed acyclic graphs to execute in the project.
        Determines the execution order of project items in each graph. Creates an
        instance for executing the first graph and starts executing it.
        """
        self._toolbox.ui.textBrowser_eventlog.verticalScrollBar().setValue(
            self._toolbox.ui.textBrowser_eventlog.verticalScrollBar().maximum()
        )
        if not self.dag_handler.dags():
            self._toolbox.msg_warning.emit("Project has no items to execute")
            return
        self._n_graphs = len(self.dag_handler.dags())
        i = 0  # Key for self._ordered_dags dictionary
        for g in self.dag_handler.dags():
            bfs_ordered_nodes = self.dag_handler.calc_exec_order(g)
            if not bfs_ordered_nodes:
                self._invalid_graphs.append(g)
                continue
            self._ordered_dags[i] = bfs_ordered_nodes
            i += 1
        if not self._ordered_dags.keys():
            self._toolbox.msg_error.emit(
                "There are no valid Directed Acyclic Graphs to execute. Please modify connections."
            )
            self._invalid_graphs.clear()
            return
        self._executed_graph_index = 0
        # Get first graph, connect signals and start executing it
        ordered_nodes = self._ordered_dags.pop(self._executed_graph_index)  # Pop first set of items to execute
        self.execution_instance = ExecutionInstance(self._toolbox, ordered_nodes)
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("---------------------------------------")
        self._toolbox.msg.emit("<b>Executing All Directed Acyclic Graphs</b>")
        self._toolbox.msg.emit("<b>Starting DAG {0}/{1}</b>".format(self._executed_graph_index + 1, self._n_graphs))
        self._toolbox.msg.emit("Order: {0}".format(" -> ".join(list(ordered_nodes))))
        self._toolbox.msg.emit("---------------------------------------")
        self.execution_instance.graph_execution_finished_signal.connect(self.graph_execution_finished)
        self.execution_instance.start_execution()

    @Slot(int, name="graph_execution_finished")
    def graph_execution_finished(self, state):
        """Releases resources from previous execution and prepares the next
        graph for execution if there are still graphs left. Otherwise,
        finishes the run.

        Args:
            state (int): 0: Ended normally. -1: User pressed Stop button
        """
        self.execution_instance.graph_execution_finished_signal.disconnect()
        self.execution_instance.deleteLater()
        self.execution_instance = None
        if state == -1:
            # Execution failed due to some error in executing the project item. E.g. Tool is missing an input file
            pass
        elif state == -2:
            self._toolbox.msg_error.emit("Execution stopped")
            self._ordered_dags.clear()
            self._invalid_graphs.clear()
            return
        self._toolbox.msg.emit("<b>DAG {0}/{1} finished</b>".format(self._executed_graph_index + 1, self._n_graphs))
        self._executed_graph_index += 1
        # Pop next graph
        execution_list = self._ordered_dags.pop(self._executed_graph_index, None)  # Pop next graph
        if not execution_list:
            # All valid DAGs have been executed. Check if there are invalid DAGs and report these to user
            self.handle_invalid_graphs()
            # No more graphs to execute
            self._toolbox.msg_success.emit("Execution complete")
            return
        # Execute next graph
        self.execution_instance = ExecutionInstance(self._toolbox, execution_list)
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("---------------------------------------")
        self._toolbox.msg.emit("<b>Starting DAG {0}/{1}</b>".format(self._executed_graph_index + 1, self._n_graphs))
        self._toolbox.msg.emit("Order: {0}".format(" -> ".join(execution_list)))
        self._toolbox.msg.emit("---------------------------------------")
        self.execution_instance.graph_execution_finished_signal.connect(self.graph_execution_finished)
        self.execution_instance.start_execution()

    def stop(self):
        """Stops execution of the current DAG. Slot for the main window Stop tool button
        in the toolbar."""
        if not self.execution_instance:
            self._toolbox.msg.emit("No execution in progress")
            return
        self._toolbox.msg.emit("Stopping...")
        self.execution_instance.stop()

    def handle_invalid_graphs(self):
        """Prints messages to Event Log if there are invalid DAGs (e.g. contain self-loops) in the project."""
        if self._invalid_graphs:
            for g in self._invalid_graphs:
                # Some graphs in the project are not DAGs. Report to user that these will not be executed.
                self._toolbox.msg.emit("")
                self._toolbox.msg.emit("---------------------------------------")
                self._toolbox.msg_warning.emit(
                    "<b>Graph {0}/{1} is not a Directed Acyclic Graph</b>".format(
                        self._executed_graph_index + 1, self._n_graphs
                    )
                )
                self._toolbox.msg.emit("Items in graph: {0}".format(", ".join(g.nodes())))
                edges = ["{0} -> {1}".format(*edge) for edge in self.dag_handler.edges_causing_loops(g)]
                self._toolbox.msg.emit(
                    "Please edit connections in Design View to execute it. "
                    "Possible fix: remove connection(s) {0}.".format(", ".join(edges))
                )
                self._toolbox.msg.emit("---------------------------------------")
                self._executed_graph_index += 1
        self._invalid_graphs.clear()

    def export_graphs(self):
        """Export all valid directed acyclic graphs in project to GraphML files."""
        if not self.dag_handler.dags():
            self._toolbox.msg_warning.emit("Project has no graphs to export")
            return
        i = 0
        for g in self.dag_handler.dags():
            fn = str(i) + ".graphml"
            path = os.path.join(self.project_dir, fn)
            if not self.dag_handler.export_to_graphml(g, path):
                self._toolbox.msg_warning.emit("Exporting graph nr. {0} failed. Not a directed acyclic graph".format(i))
            else:
                self._toolbox.msg.emit("Graph nr. {0} exported to {1}".format(i, path))
            i += 1

    @Slot("QVariant", name="simulate_dag_execution")
    def simulate_dag_execution(self, dag):
        """Simulates the execution of the given dag."""
        ordered_nodes = self.dag_handler.calc_exec_order(dag)
        if not ordered_nodes:
            # Not a dag, invalidate workflow
            edges = self.dag_handler.edges_causing_loops(dag)
            for node in dag.nodes():
                ind = self._toolbox.project_item_model.find_item(node)
                project_item = self._toolbox.project_item_model.project_item(ind)
                project_item.invalidate_workflow(edges)
            return
        # Make execution instance and run simulation
        execution_instance = ExecutionInstance(self._toolbox, ordered_nodes)
        execution_instance.simulate_execution()

    def simulate_project_execution(self):
        """Simulates the execution of all dags in the project."""
        for g in self.dag_handler.dags():
            self.simulate_dag_execution(g)

    def simulate_item_execution(self, item):
        """Simulates the execution of the dag containing given item."""
        dag = self.dag_handler.dag_with_node(item)
        if not dag:
            self._toolbox.msg_error.emit(
                "[BUG] Could not find a graph containing {0}. " "<b>Please reopen the project.</b>".format(item)
            )
            return
        self.simulate_dag_execution(dag)
