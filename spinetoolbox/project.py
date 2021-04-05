######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
from itertools import takewhile
import os
import json
import logging
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QMessageBox
from spine_engine.project_item.connection import Connection
from spine_engine.spine_engine import ExecutionDirection
from spine_engine.utils.helpers import shorten
from spinetoolbox.metaobject import MetaObject
from spinetoolbox.helpers import create_dir, erase_dir, make_settings_dict_for_engine
from .config import LATEST_PROJECT_VERSION, PROJECT_FILENAME, INVALID_CHARS
from .dag_handler import DirectedGraphHandler
from .project_tree_item import LeafProjectTreeItem
from .project_commands import (
    SetProjectNameCommand,
    SetProjectDescriptionCommand,
    AddProjectItemsCommand,
    RemoveProjectItemsCommand,
    RemoveAllProjectItemsCommand,
)
from .spine_engine_worker import SpineEngineWorker


class SpineToolboxProject(MetaObject):
    """Class for Spine Toolbox projects."""

    dag_execution_finished = Signal()
    """Emitted after a single DAG execution has finished."""
    project_execution_about_to_start = Signal()
    """Emitted just before the entire project is executed."""
    project_execution_finished = Signal()
    """Emitted after the entire project execution finishes."""
    connection_established = Signal(object)
    """Emitted after new connection has been added to project."""
    connection_about_to_be_removed = Signal(object)
    """Emitted before connection removal."""
    connection_replaced = Signal(object, object)
    """Emitted after a connection has been replaced by another."""
    item_added = Signal(str)
    """Emitted after a project item has been added."""
    item_about_to_be_removed = Signal(str)
    """Emitted before project item removal."""

    def __init__(self, toolbox, name, description, p_dir, project_item_model, settings, logger):
        """
        Args:
            toolbox (ToolboxUI): toolbox of this project
            name (str): Project name
            description (str): Project description
            p_dir (str): Project directory
            project_item_model (ProjectItemModel): project item tree model
            settings (QSettings): Toolbox settings
            logger (LoggerInterface): a logger instance
        """
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project_item_model = project_item_model
        self._connections = list()
        self._logger = logger
        self._settings = settings
        self.dag_handler = DirectedGraphHandler()
        self._engine_workers = []
        self._execution_stopped = True
        self.project_dir = None  # Full path to project directory
        self.config_dir = None  # Full path to .spinetoolbox directory
        self.items_dir = None  # Full path to items directory
        self.specs_dir = None  # Full path to specs directory
        self.config_file = None  # Full path to .spinetoolbox/project.json file
        self._toolbox.undo_stack.clear()
        p_dir = os.path.abspath(p_dir)
        if not self._create_project_structure(p_dir):
            self._logger.msg_error.emit("Creating project directory structure in <b>{0}</b> failed".format(p_dir))

    def toolbox(self):
        """Returns Toolbox main window.

        Returns:
            ToolboxUI: main window
        """
        return self._toolbox

    def _create_project_structure(self, directory):
        """Makes the given directory a Spine Toolbox project directory.
        Creates directories and files that are common to all projects.

        Args:
            directory (str): Abs. path to a directory that should be made into a project directory

        Returns:
            bool: True if project structure was created successfully, False otherwise
        """
        self.project_dir = directory
        self.config_dir = os.path.abspath(os.path.join(self.project_dir, ".spinetoolbox"))
        self.items_dir = os.path.abspath(os.path.join(self.config_dir, "items"))
        self.specs_dir = os.path.abspath(os.path.join(self.config_dir, "specifications"))
        self.config_file = os.path.abspath(os.path.join(self.config_dir, PROJECT_FILENAME))
        for dir_ in (self.project_dir, self.config_dir, self.items_dir, self.specs_dir):
            try:
                create_dir(dir_)
            except OSError:
                self._logger.msg_error.emit("Creating directory {0} failed".format(dir_))
                return False
        return True

    def call_set_name(self, name):
        self._toolbox.undo_stack.push(SetProjectNameCommand(self, name))

    def call_set_description(self, description):
        self._toolbox.undo_stack.push(SetProjectDescriptionCommand(self, description))

    def set_name(self, name):
        """Changes project name.

        Args:
            name (str): New project name
        """
        super().set_name(name)
        self._toolbox.update_window_title()
        # Remove entry with the old name from File->Open recent menu
        self._toolbox.remove_path_from_recent_projects(self.project_dir)
        # Add entry with the new name back to File->Open recent menu
        self._toolbox.update_recent_projects()
        self._logger.msg.emit("Project name changed to <b>{0}</b>".format(self.name))

    def set_description(self, description):
        super().set_description(description)
        msg = "Project description "
        if description:
            msg += f"changed to <b>{description}</b>"
        else:
            msg += "cleared"
        self._logger.msg.emit(msg)

    def save(self, spec_paths):
        """Collects project information and objects
        into a dictionary and writes it to a JSON file.

        Args:
            spec_paths (dict): List of absolute paths to specification files keyed by item type

        Returns:
            bool: True or False depending on success
        """
        project_dict = dict()  # Dictionary for storing project info
        project_dict["version"] = LATEST_PROJECT_VERSION
        project_dict["name"] = self.name
        project_dict["description"] = self.description
        project_dict["specifications"] = spec_paths
        project_dict["connections"] = [connection.to_dict() for connection in self._connections]
        items_dict = dict()  # Dictionary for storing project items
        # Traverse all items in project model by category
        for category_item in self._project_item_model.root().children():
            category = category_item.name
            # Store item dictionaries with item name as key and item_dict as value
            for item in self._project_item_model.items(category):
                items_dict[item.name] = item.project_item.item_dict()
        # Save project to file
        saved_dict = dict(project=project_dict, items=items_dict)
        # Write into JSON file
        with open(self.config_file, "w") as fp:
            json.dump(saved_dict, fp, indent=4)
        return True

    def load(self, items_dict, connection_dicts):
        """Populates project item model with items loaded from project file.

        Args:
            items_dict (dict): Dictionary containing all project items in JSON format
            connection_dicts (list of dict): List containing all connections in JSON format
        """
        self._logger.msg.emit("Loading project items...")
        if not items_dict:
            self._logger.msg_warning.emit("Project has no items")
        self.make_and_add_project_items(items_dict, verbosity=False)
        self._logger.msg.emit("Restoring connections...")
        for connection in map(Connection.from_dict, connection_dicts):
            self.add_connection(connection)

    def get_item(self, name):
        """Returns project item.

        Args:
            name (str): item's name

        Returns:
            ProjectItem: project item
        """
        return self._project_item_model.get_item(name).project_item

    def get_items(self):
        """ Returns all project items.

        Returns:
            list of ProjectItem: all project items
        """
        return [item.project_item for item in self._project_item_model.items()]

    def add_project_items(self, items_dict, set_selected=False, verbosity=True):
        """Pushes an AddProjectItemsCommand to the toolbox undo stack.
        """
        if not items_dict:
            return
        self._toolbox.undo_stack.push(
            AddProjectItemsCommand(self, items_dict, set_selected=set_selected, verbosity=verbosity)
        )

    def make_project_tree_items(self, items_dict):
        """Creates and returns a dictionary mapping category indexes to a list of corresponding LeafProjectTreeItem instances.

        Args:
            items_dict (dict): a mapping from item name to item dict

        Returns:
            dict(QModelIndex, list(LeafProjectTreeItem))
        """
        project_items_by_category = {}
        for item_name, item_dict in items_dict.items():
            item_type = item_dict["type"]
            factory = self._toolbox.item_factories.get(item_type)
            if factory is None:
                self._logger.msg_error.emit(f"Unknown item type <b>{item_type}</b>")
                self._logger.msg_error.emit(f"Loading project item <b>{item_name}</b> failed")
                return {}
            try:
                project_item = factory.make_item(item_name, item_dict, self._toolbox, self)
            except TypeError as error:
                self._logger.msg_error.emit(
                    f"Creating <b>{item_type}</b> project item <b>{item_name}</b> failed. "
                    "This is most likely caused by an outdated project file."
                )
                logging.debug(error)
                continue
            except KeyError as error:
                self._logger.msg_error.emit(
                    f"Creating <b>{item_type}</b> project item <b>{item_name}</b> failed. "
                    f"This is most likely caused by an outdated or corrupted project file "
                    f"(missing JSON key: {str(error)})."
                )
                logging.debug(error)
                continue
            original_data_dir = item_dict.get("original_data_dir")
            original_db_url = item_dict.get("original_db_url")
            duplicate_files = item_dict.get("duplicate_files")
            if original_data_dir is not None and original_db_url is not None and duplicate_files is not None:
                project_item.copy_local_data(original_data_dir, original_db_url, duplicate_files)
            project_items_by_category.setdefault(project_item.item_category(), list()).append(project_item)
        project_tree_items = {}
        for category, project_items in project_items_by_category.items():
            category_ind = self._project_item_model.find_category(category)
            # NOTE: category_ind might be None, and needs to be handled caller side
            project_tree_items[category_ind] = [
                LeafProjectTreeItem(project_item, self._toolbox) for project_item in project_items
            ]
        return project_tree_items

    def _do_add_project_tree_items(self, category_ind, *project_tree_items, set_selected=False, verbosity=True):
        """Adds LeafProjectTreeItem instances to project.

        Args:
            category_ind (QModelIndex): The category index
            project_tree_items (LeafProjectTreeItem): one or more LeafProjectTreeItem instances to add
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        for project_tree_item in project_tree_items:
            project_item = project_tree_item.project_item
            self._project_item_model.insert_item(project_tree_item, category_ind)
            self.dag_handler.add_dag_node(project_item.name)
            self.item_added.emit(project_item.name)
            project_item.set_up()
            if verbosity:
                self._logger.msg.emit(
                    "{0} <b>{1}</b> added to project".format(project_item.item_type(), project_item.name)
                )
        if set_selected:
            item = list(project_tree_items)[-1]
            self.set_item_selected(item)

    def rename_item(self, previous_name, new_name, rename_data_dir_message):
        """Renames a project item

         Args:
             previous_name (str): item's current name
             new_name (str): item's new name
             rename_data_dir_message (str): message to show when renaming item's data directory

         Returns:
             bool: True if item was renamed successfully, False otherwise
         """
        if not new_name.strip() or new_name == previous_name:
            return False
        if any(x in INVALID_CHARS for x in new_name):
            msg = f"<b>{new_name}</b> contains invalid characters."
            self._logger.error_box.emit("Invalid characters", msg)
            return False
        if self._project_item_model.find_item(new_name):
            msg = f"Project item <b>{new_name}</b> already exists"
            self._logger.error_box.emit("Invalid name", msg)
            return False
        new_short_name = shorten(new_name)
        if self._toolbox.project_item_model.short_name_reserved(new_short_name):
            msg = f"Project item using directory <b>{new_short_name}</b> already exists"
            self._logger.error_box("Invalid name", msg)
            return False
        item_index = self._project_item_model.find_item(previous_name)
        item = self._project_item_model.item(item_index).project_item
        if not item.rename(new_name, rename_data_dir_message):
            return False
        self._project_item_model.set_leaf_item_name(item_index, new_name)
        self.dag_handler.rename_node(previous_name, new_name)
        for connection in self._connections:
            if connection.source == previous_name:
                connection.source = new_name
            if connection.destination == previous_name:
                connection.destination = new_name
        self._logger.msg_success.emit(f"Project item <b>{previous_name}</b> renamed to <b>{new_name}</b>.")
        return True

    @property
    def connections(self):
        return self._connections

    def find_connection(self, source_name, destination_name):
        """Searches for a connection between given items.

        Args:
            source_name (str): source item's name
            destination_name (str): destination item's name

        Returns:
            Connection: connection instance or None if there is no connection
        """
        i = len(
            list(takewhile(lambda c: source_name != c.source or destination_name != c.destination, self._connections))
        )
        if i == len(self._connections):
            return None
        return self._connections[i]

    def connections_for_item(self, item_name):
        """Returns connections that have given item as source or destination.

        Args:
            item_name (str): item's name

        Returns:
            list of Connection: connections connected to item
        """
        return [c for c in self._connections if item_name in (c.source, c.destination)]

    def add_connection(self, connection):
        """Adds a connection to the project.

        Args:
            connection (Connection): connection to add

        Returns:
            bool: True if connection was added successfully, False otherwise
        """
        if connection in self._connections:
            return False
        if not self.dag_handler.add_graph_edge(connection.source, connection.destination):
            return False
        self._connections.append(connection)
        dag = self.dag_handler.dag_with_node(connection.source)
        self.connection_established.emit(connection)
        if not self._is_dag_valid(dag):
            return True  # Connection was added successfully even though DAG is not valid.
        destination = self._project_item_model.get_item(connection.destination).project_item
        self.notify_resource_changes_to_predecessors(destination)
        source = self._project_item_model.get_item(connection.source).project_item
        self.notify_resource_changes_to_successors(source)
        destination.notify_destination(source)
        self._update_ranks(dag)
        return True

    def remove_connection(self, connection):
        """Removes a connection from the project.

        Args:
            connection (Connection): connection to remove
        """
        self.connection_about_to_be_removed.emit(connection)
        self._connections.remove(connection)
        dags = self.dag_handler.remove_graph_edge(connection.source, connection.destination)
        for dag in dags:
            if not self._is_dag_valid(dag):
                continue
            destination = self._project_item_model.get_item(connection.destination).project_item
            self._update_item_resources(destination, ExecutionDirection.FORWARD)
            source = self._project_item_model.get_item(connection.source).project_item
            self._update_item_resources(source, ExecutionDirection.BACKWARD)
            self._update_ranks(dag)

    def replace_connection(self, existing_connection, new_connection):
        """Replaces an existing connection between items.

        Replacing does not trigger any updates to the DAG or project items.

        Args:
            existing_connection (Connection): an established connection
            new_connection (Connection): connection to replace by
        """
        self._connections.remove(existing_connection)
        self._connections.append(new_connection)
        self.connection_replaced.emit(existing_connection, new_connection)

    def set_item_selected(self, item):
        """
        Selects the given item.

        Args:
            item (LeafProjectTreeItem)
        """
        ind = self._project_item_model.find_item(item.name)
        self._toolbox.ui.treeView_project.setCurrentIndex(ind)

    def make_and_add_project_items(self, items_dict, set_selected=False, verbosity=True):
        """Adds items to project at loading.

        Args:
            items_dict (dict): a mapping from item name to item dict
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        for category_ind, project_tree_items in self.make_project_tree_items(items_dict).items():
            self._do_add_project_tree_items(
                category_ind, *project_tree_items, set_selected=set_selected, verbosity=verbosity
            )

    def remove_all_items(self):
        """Pushes a RemoveAllProjectItemsCommand to the Toolbox undo stack."""
        items_per_category = self._project_item_model.items_per_category()
        if not any(v for v in items_per_category.values()):
            self._logger.msg.emit("No project items to remove")
            return
        delete_data = int(self._settings.value("appSettings/deleteData", defaultValue="0")) != 0
        msg = "Remove all items from project?"
        if not delete_data:
            msg += "Item data directory will still be available in the project directory after this operation."
        else:
            msg += "<br><br><b>Warning: Item data will be permanently lost after this operation.</b>"
        message_box = QMessageBox(
            QMessageBox.Question,
            "Remove All Items",
            msg,
            buttons=QMessageBox.Ok | QMessageBox.Cancel,
            parent=self._toolbox,
        )
        message_box.button(QMessageBox.Ok).setText("Remove Items")
        answer = message_box.exec_()
        if answer != QMessageBox.Ok:
            return
        self._toolbox.undo_stack.push(RemoveAllProjectItemsCommand(self, delete_data=delete_data))

    def remove_project_items(self, *indexes, ask_confirmation=False):
        """Pushes a RemoveProjectItemsCommand to the toolbox undo stack.

        Args:
            *indexes (QModelIndex): Indexes of the items in project item model
            ask_confirmation (bool): If True, shows 'Are you sure?' message box
        """
        names = [i.data() for i in indexes]
        delete_data = int(self._settings.value("appSettings/deleteData", defaultValue="0")) != 0
        if ask_confirmation:
            msg = f"Remove item(s) <b>{', '.join(names)}</b> from project? "
            if not delete_data:
                msg += "Item data directory will still be available in the project directory after this operation."
            else:
                msg += "<br><br><b>Warning: Item data will be permanently lost after this operation.</b>"
            msg += "<br><br>Tip: Remove items by pressing 'Delete' key to bypass this dialog."
            # noinspection PyCallByClass, PyTypeChecker
            message_box = QMessageBox(
                QMessageBox.Question,
                "Remove Item",
                msg,
                buttons=QMessageBox.Ok | QMessageBox.Cancel,
                parent=self._toolbox,
            )
            message_box.button(QMessageBox.Ok).setText("Remove Item")
            answer = message_box.exec_()
            if answer != QMessageBox.Ok:
                return
        self._toolbox.undo_stack.push(RemoveProjectItemsCommand(self, names, delete_data=delete_data))

    def remove_item_by_name(self, item_name, delete_data=False):
        """Removes project item by its name.

        Args:
            item_name (str): Item's name
            delete_data (bool): If set to True, deletes the directories and data associated with the item
        """
        for c in self.connections_for_item(item_name):
            self.remove_connection(c)
        self.dag_handler.remove_node_from_graph(item_name)
        index = self._project_item_model.find_item(item_name)
        self.item_about_to_be_removed.emit(item_name)
        tree_item = self._project_item_model.item(index)
        self._project_item_model.remove_item(tree_item, parent=index.parent())
        item = tree_item.project_item
        item.tear_down()
        if delete_data:
            try:
                data_dir = item.data_dir
            except AttributeError:
                data_dir = None
            if data_dir:
                # Remove data directory and all its contents
                self._logger.msg.emit(f"Removing directory <b>{data_dir}</b>")
                try:
                    if not erase_dir(data_dir):
                        self._logger.msg_error.emit("Directory does not exist")
                except OSError:
                    self._logger.msg_error.emit("[OSError] Removing directory failed. Check directory permissions.")
        if self._project_item_model.n_items() == 0:
            self._logger.msg.emit("All items removed from project.")

    def do_remove_project_tree_items(self, *items, delete_data=False, silent=False):
        """Removes LeafProjectTreeItem instances from project.

        Args:
            *items (LeafProjectTreeItem): the items to remove
            delete_data (bool): If set to True, deletes the directories and data associated with the item
            silent (bool): Used to prevent unnecessary log messages when switching projects
        """
        for item in items:
            self.remove_item_by_name(item.name, delete_data)
        if not silent:
            self._logger.msg.emit(f"Item(s) <b>{', '.join(item.name for item in items)}</b> removed from project")

    def execute_dags(self, dags, execution_permits, msg):
        """Executes given dags.

        Args:
            dags (Sequence(DiGraph))
            execution_permits (Sequence(dict))
        """
        self.project_execution_about_to_start.emit()
        self._logger.msg.emit("")
        self._logger.msg.emit("-------------------------------------------------")
        self._logger.msg.emit(f"<b>{msg}</b>")
        self._logger.msg.emit("-------------------------------------------------")
        self._execution_stopped = False
        self._execute_dags(dags, execution_permits)

    def get_node_successors(self, dag, dag_identifier):
        node_successors = self.dag_handler.node_successors(dag)
        if not node_successors:
            self._logger.msg_warning.emit("<b>Graph {0} is not a Directed Acyclic Graph</b>".format(dag_identifier))
            self._logger.msg.emit("Items in graph: {0}".format(", ".join(dag.nodes())))
            edges = ["{0} -> {1}".format(*edge) for edge in self.dag_handler.edges_causing_loops(dag)]
            self._logger.msg.emit(
                "Please edit connections in Design View to execute it. "
                "Possible fix: remove connection(s) {0}.".format(", ".join(edges))
            )
            return None
        return node_successors

    def _execute_dags(self, dags, execution_permits_list):
        if self._engine_workers:
            self._logger.msg_error.emit("Execution already in progress.")
            return
        settings = make_settings_dict_for_engine(self._settings)
        for k, (dag, execution_permits) in enumerate(zip(dags, execution_permits_list)):
            dag_identifier = f"{k + 1}/{len(dags)}"
            worker = self.create_engine_worker(dag, execution_permits, dag_identifier, settings)
            worker.finished.connect(lambda worker=worker: self._handle_engine_worker_finished(worker))
            self._engine_workers.append(worker)
        # NOTE: Don't start the workers as they are created. They may finish too quickly, before the others
        # are added to ``_engine_workers``, and thus ``_handle_engine_worker_finished()`` will believe
        # that the project is done executing before it's fully loaded.
        for worker in self._engine_workers:
            self._logger.msg.emit("<b>Starting DAG {0}</b>".format(worker.dag_identifier))
            self._logger.msg.emit("Order: {0}".format(" -> ".join(worker.engine_data["node_successors"])))
            worker.start()

    def create_engine_worker(self, dag, execution_permits, dag_identifier, settings):
        node_successors = self.get_node_successors(dag, dag_identifier)
        if node_successors is None:
            return
        project_items = {name: self._project_item_model.get_item(name).project_item for name in node_successors}
        items = {}
        specifications = {}
        for name, project_item in project_items.items():
            items[name] = project_item.item_dict()
            spec = project_item.specification()
            if spec is not None:
                spec_dict = spec.to_dict().copy()
                spec_dict["definition_file_path"] = spec.definition_file_path
                specifications.setdefault(project_item.item_type(), list()).append(spec_dict)
        connections = [c.to_dict() for c in self._connections]
        data = {
            "items": items,
            "specifications": specifications,
            "connections": connections,
            "node_successors": node_successors,
            "execution_permits": execution_permits,
            "settings": settings,
            "project_dir": self.project_dir,
        }
        server_address = self._settings.value("appSettings/engineServerAddress", defaultValue="")
        worker = SpineEngineWorker(server_address, data, dag, dag_identifier, project_items)
        return worker

    def _handle_engine_worker_finished(self, worker):
        finished_outcomes = {
            "USER_STOPPED": "stopped by the user",
            "FAILED": "failed",
            "COMPLETED": "completed successfully",
        }
        outcome = finished_outcomes.get(worker.engine_final_state())
        if outcome is not None:
            self._logger.msg.emit("<b>DAG {0} {1}</b>".format(worker.dag_identifier, outcome))
        if any(worker.engine_final_state() not in finished_outcomes for worker in self._engine_workers):
            return
        # Only after all workers have finished, notify changes and handle successful executions.
        # Doing it *while* executing leads to deadlocks at acquiring sqlalchemy's infamous _CONFIGURE_MUTEX
        # (needed to create DatabaseMapping instances). It seems that the lock gets confused when
        # being acquired by threads from different processes or maybe even different QThreads.
        # Can't say I really understand the whole extent of it.
        for finished_worker in self._engine_workers:
            for item, direction, state in finished_worker.successful_executions:
                item.handle_execution_successful(direction, state)
            finished_worker.clean_up()
        self._engine_workers.clear()
        self.project_execution_finished.emit()

    def dag_with_node(self, item_name):
        dag = self.dag_handler.dag_with_node(item_name)
        if not dag:
            self._logger.msg_error.emit(
                "[BUG] Could not find a graph containing {0}. <b>Please reopen the project.</b>".format(item_name)
            )
        return dag

    def execute_selected(self):
        """Executes DAGs corresponding to all selected project items."""
        if not self.dag_handler.dags():
            self._logger.msg_warning.emit("Project has no items to execute")
            return
        # Get selected item
        selected_indexes = self._toolbox.ui.treeView_project.selectedIndexes()
        if not selected_indexes:
            self._logger.msg_warning.emit("Please select a project item and try again.")
            return
        dags = set()
        executable_item_names = list()
        for ind in selected_indexes:
            item = self._project_item_model.item(ind)
            executable_item_names.append(item.name)
            dag = self.dag_with_node(item.name)
            if not dag:
                continue
            dags.add(dag)
        execution_permit_list = list()
        for dag in dags:
            execution_permits = dict()
            for item_name in dag.nodes:
                execution_permits[item_name] = item_name in executable_item_names
            execution_permit_list.append(execution_permits)
        self.execute_dags(dags, execution_permit_list, "Executing Selected Directed Acyclic Graphs")

    def execute_project(self):
        """Executes all dags in the project."""
        dags = self.dag_handler.dags()
        if not dags:
            self._logger.msg_warning.emit("Project has no items to execute")
            return
        execution_permit_list = list()
        for dag in dags:
            execution_permit_list.append({item_name: True for item_name in dag.nodes})
        self.execute_dags(dags, execution_permit_list, "Executing All Directed Acyclic Graphs")

    def stop(self):
        """Stops execution. Slot for the main window Stop tool button in the toolbar."""
        if self._execution_stopped:
            self._logger.msg.emit("No execution in progress")
            return
        self._logger.msg.emit("Stopping...")
        self._execution_stopped = True
        # Stop experimental engines
        for worker in self._engine_workers:
            worker.stop_engine()

    def notify_resource_changes_to_predecessors(self, item):
        """Updates resources for direct predecessors of given item.

        Args:
            item (ProjectItem): item whose resources have changed
        """
        item_name = item.name
        predecessor_names = {c.source for c in self._incoming_connections(item_name)}
        succesor_connections = self._outgoing_connections
        update_resources = self._update_predecessor
        trigger_resources = item.resources_for_direct_predecessors()
        self._notify_resource_changes(
            item_name, predecessor_names, succesor_connections, update_resources, trigger_resources
        )

    def notify_resource_changes_to_successors(self, item):
        """Updates resources for direct successors and outgoing connections of given item.

        Args:
            item (ProjectItem): item whose resources have changed
        """
        item_name = item.name
        sucessor_names = {c.destination for c in self._outgoing_connections(item_name)}
        predecessor_connections = self._incoming_connections
        update_resources = self._update_successor
        trigger_resources = item.resources_for_direct_successors()
        self._notify_resource_changes(
            item_name, sucessor_names, predecessor_connections, update_resources, trigger_resources
        )
        for connection in self._outgoing_connections(item_name):
            connection.receive_resources_from_source(trigger_resources)

    def _notify_resource_changes(
        self, trigger_name, target_names, provider_connections, update_resources, trigger_resources
    ):
        """Updates resources in given direction for immediate neighbours of an item.

        Args:
            trigger_name (str): item whose resources have changed
            target_names (list(str)): items to be notified
            provider_connections (function): function that receives a target item name and returns a list of
                Connections from resource providers
            update_resources (function): function that takes an item name, a list of provider names, and a dictionary
                of resources, and does the updating
            trigger_resources (list(ProjectItemResources)): resources from the trigger item
        """
        resource_cache = {trigger_name: trigger_resources}
        for target_name in target_names:
            target_item = self._project_item_model.get_item(target_name).project_item
            connections = provider_connections(target_name)
            update_resources(target_item, connections, resource_cache)

    def _update_item_resources(self, target_item, direction):
        """Updates up or downstream resources for a single project item.
        Called in both directions after removing a Connection.

        Args:
            target_item (ProjectItem): item whose resource need update
            direction (ExecutionDirection): FORWARD updates resources from upstream, BACKWARD from downstream
        """
        target_name = target_item.name
        if direction == ExecutionDirection.FORWARD:
            connections = self._incoming_connections(target_name)
            self._update_successor(target_item, connections, resource_cache={})
        else:
            connections = self._outgoing_connections(target_name)
            self._update_predecessor(target_item, connections, resource_cache={})

    def successor_names(self, name):
        """Collects direct successor item names.

        Args:
            name (str): name of the project item whose successors to collect

        Returns:
            set of str: direct successor names
        """
        return {c.destination for c in self._outgoing_connections(name)}

    def _outgoing_connections(self, name):
        """Collects outgoing connections.

        Args:
            name (str): name of the project item whose connections to collect

        Returns:
            set of Connection: outgoing connections
        """
        return [c for c in self._connections if c.source == name]

    def _incoming_connections(self, name):
        """Collects incoming connections.

        Args:
            name (str): name of the project item whose connections to collect

        Returns:
            set of Connection: incoming connections
        """
        return [c for c in self._connections if c.destination == name]

    def _update_successor(self, successor, incoming_connections, resource_cache):
        combined_resources = list()
        for conn in incoming_connections:
            item_name = conn.source
            predecessor = self._project_item_model.get_item(item_name).project_item
            resources = resource_cache.get(item_name)
            if resources is None:
                resources = predecessor.resources_for_direct_successors()
                resource_cache[item_name] = resources
            resources = conn.convert_resources(resources)
            combined_resources += resources
        successor.upstream_resources_updated(combined_resources)

    def _update_predecessor(self, predecessor, outgoing_connections, resource_cache):
        combined_resources = list()
        for conn in outgoing_connections:
            item_name = conn.destination
            successor = self._project_item_model.get_item(item_name).project_item
            resources = resource_cache.get(item_name)
            if resources is None:
                resources = successor.resources_for_direct_predecessors()
                resource_cache[item_name] = resources
            combined_resources += resources
        predecessor.downstream_resources_updated(combined_resources)

    def _is_dag_valid(self, dag):
        node_successors = self.dag_handler.node_successors(dag)
        items = {item.name: item.project_item for item in self._project_item_model.items()}
        if not node_successors:
            edges = self.dag_handler.edges_causing_loops(dag)
            for node in dag.nodes():
                items[node].invalidate_workflow(edges)
            return False
        for node in dag.nodes():
            items[node].revalidate_workflow()
        return True

    def _update_ranks(self, dag):
        node_successors = self.dag_handler.node_successors(dag)
        ranks = _ranks(node_successors)
        for item_name in node_successors:
            item = self._project_item_model.get_item(item_name).project_item
            item.set_rank(ranks[item_name])

    @property
    def settings(self):
        return self._settings

    def tear_down(self, silent=False):
        """Cleans up project."""
        for project_tree_items in self._project_item_model.items_per_category().values():
            self.do_remove_project_tree_items(*project_tree_items, delete_data=False, silent=silent)


def _ranks(node_successors):
    """
    Calculates node ranks.

    Args:
        node_successors (dict): a mapping from successor name to a list of predecessor names

    Returns:
        dict: a mapping from node name to rank
    """
    node_predecessors = dict()
    for predecessor, successors in node_successors.items():
        node_predecessors.setdefault(predecessor, list())
        for successor in successors:
            node_predecessors.setdefault(successor, list()).append(predecessor)
    ranking = []
    while node_predecessors:
        same_ranks = [node for node, predecessor in node_predecessors.items() if not predecessor]
        for ranked_node in same_ranks:
            del node_predecessors[ranked_node]
            for node, successors in node_predecessors.items():
                node_predecessors[node] = [s for s in successors if s != ranked_node]
        ranking.append(same_ranks)
    return {node: rank for rank, nodes in enumerate(ranking) for node in nodes}
