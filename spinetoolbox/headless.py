######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains facilities to open and execute projects without GUI.
"""
from copy import deepcopy
from enum import IntEnum, unique
import json
import pathlib
import sys
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, Signal, Slot
import networkx as nx

from spine_engine import SpineEngineState
from spine_engine.exception import EngineInitFailed
from spine_engine.load_project_items import load_item_specification_factories
from spine_engine.utils.serialization import deserialize_path
from .project_item.logging_connection import HeadlessConnection
from .config import LATEST_PROJECT_VERSION
from .helpers import (
    make_settings_dict_for_engine,
    plugins_dirs,
    load_plugin_dict,
    load_plugin_specifications,
    load_project_dict,
    load_local_project_data,
    merge_dicts,
    HTMLTagFilter,
    load_specification_local_data,
)
from .spine_engine_manager import make_engine_manager


class HeadlessLogger(QObject):
    """A :class:`LoggerInterface` compliant logger that uses Python's standard logging facilities."""

    msg = Signal(str)
    """Emits a notification message."""
    msg_success = Signal(str)
    """Emits a message on success"""
    msg_warning = Signal(str)
    """Emits a warning message."""
    msg_error = Signal(str)
    """Emits an error message."""
    msg_proc = Signal(str)
    """Emits a message originating from a subprocess (usually something printed to stdout)."""
    msg_proc_error = Signal(str)
    """Emits an error message originating from a subprocess (usually something printed to stderr)."""
    information_box = Signal(str, str)
    """Requests an 'information message box' (e.g. a message window) to be opened with a given title and message."""
    error_box = Signal(str, str)
    """Requests an 'error message box' to be opened with a given title and message."""

    def __init__(self):
        super().__init__()
        self.msg.connect(self._log_message)
        self.msg_success.connect(self._log_message)
        self.msg_warning.connect(self._log_warning)
        self.msg_error.connect(self._log_error)
        self.msg_proc.connect(self._log_message)
        self.msg_proc_error.connect(self._log_error)
        self.information_box.connect(self._show_information_box)
        self.error_box.connect(self._show_error_box)
        self._tag_filter = HTMLTagFilter()

    @Slot(str)
    def _log_message(self, message):
        """Prints an information message."""
        self._print(message, sys.stdout)

    @Slot(str)
    def _log_warning(self, message):
        """Prints a warning message."""
        self._print(message, sys.stdout)

    @Slot(str)
    def _log_error(self, message):
        """Prints an error message."""
        self._print(message, sys.stderr)

    @Slot(str, str)
    def _show_information_box(self, title, message):
        """Prints an information message with a title."""
        self._print(title + ": " + message, sys.stdout)

    @Slot(str, str)
    def _show_error_box(self, title, message):
        """Prints an error message with a title."""
        self._print(title + ": " + message, sys.stderr)

    def _print(self, message, out_stream):
        """Filters HTML tags from message before printing it to given file."""
        self._tag_filter.feed(message)
        print(self._tag_filter.drain(), file=out_stream)


class ModifiableProject:
    """A simple project that is available for modification script."""

    def __init__(self, project_dir, items_dict, connection_dicts):
        """
        Args:
            project_dir (Path): project directory
            items_dict (dict): project item dictionaries
            connection_dicts (list of dict): connection dictionaries
        """
        self._project_dir = project_dir
        self._items = deepcopy(items_dict)
        self._connections = [HeadlessConnection.from_dict(d) for d in connection_dicts]

    @property
    def project_dir(self):
        return self._project_dir

    def find_connection(self, source_name, destination_name):
        """Searches for a connection between given items.

        Args:
            source_name (str): source item's name
            destination_name (str): destination item's name

        Returns:
            Connection: connection instance or None if there is no connection
        """
        return next(
            (c for c in self._connections if c.source == source_name and c.destination == destination_name), None
        )

    def find_item(self, name):
        """Searches for a project item.

        Args:
            name (str): item's name

        Returns:
            dict: item dict or None if no such item exists
        """
        return self._items.get(name)

    def items_to_dict(self):
        """Stores project items back to dictionaries.

        Returns:
            dict: item dictionaries
        """
        return self._items

    def connections_to_dict(self):
        """Stores connections back to dictionaries.

        Returns:
            list of dict: connection dictionaries
        """
        return [c.to_dict() for c in self._connections]


class ActionsWithProject(QObject):
    """
    A 'task' which opens Toolbox project and operates on it.

    The execution of this task is triggered by sending it a 'startup' QEvent using e.g. QCoreApplication.postEvent()
    """

    _start = Signal()
    """A private signal to actually start execution. Not to be used directly. Post a startup event instead."""

    def __init__(self, args, startup_event_type, parent):
        """
        Args:
            args (argparse.Namespace): parsed command line arguments
            startup_event_type (int): expected type id for the event that starts this task
            parent (QObject): a parent object
        """
        super().__init__(parent)
        self._args = args
        self._logger = HeadlessLogger()
        self._startup_event_type = startup_event_type
        self._start.connect(self._execute)
        self._node_messages = dict()
        self._project_dir = None
        self._app_settings = None
        self._item_dicts = None
        self._specification_dicts = None
        self._plugin_specifications = None
        self._connection_dicts = None
        self._jump_dicts = None

    def _dags(self):
        graph = nx.DiGraph()
        graph.add_nodes_from(self._item_dicts)
        connections = map(HeadlessConnection.from_dict, self._connection_dicts)
        graph.add_edges_from(((x.source, x.destination) for x in connections))
        return [graph.subgraph(nodes) for nodes in nx.weakly_connected_components(graph)]

    @Slot()
    def _execute(self):
        """Executes this task."""
        if not self._args.project:
            self._logger.msg_error.emit("project missing from command line arguments.")
            QCoreApplication.instance().exit(Status.ARGUMENT_ERROR)
            return
        try:
            status = self._open_project()
            if status != Status.OK:
                QCoreApplication.instance().exit(status)
                return
            if self._args.mod_script:
                status = self._exec_mod_script()
                if status != Status.OK:
                    QCoreApplication.instance().exit(status)
                    return
            if self._args.list_items:
                dags = self._dags()
                for dag_number, dag in enumerate(dags):
                    print(f"DAG {dag_number + 1}/{len(dags)}:")
                    print(" ".join(sorted(dag.nodes)))
            if self._args.execute_only:
                status = self._execute_project()
                if status != Status.OK:
                    QCoreApplication.instance().exit(status)
                    return
        except Exception:
            QCoreApplication.instance().exit(Status.ERROR)
            raise
        QCoreApplication.instance().exit(Status.OK)

    def _open_project(self):
        """Opens a project.

        Returns:
            Status: status code
        """
        self._app_settings = QSettings("SpineProject", "Spine Toolbox", self)
        spec_factories = load_item_specification_factories("spine_items")
        self._plugin_specifications = dict()
        self._project_dir = pathlib.Path(self._args.project).resolve()
        config_dir = self._project_dir / ".spinetoolbox"
        specification_local_data = load_specification_local_data(config_dir)
        for plugin_dir in plugins_dirs(self._app_settings):
            plugin_dict = load_plugin_dict(plugin_dir, self._logger)
            if plugin_dict is None:
                continue
            specs = load_plugin_specifications(
                plugin_dict, specification_local_data, spec_factories, self._app_settings, self._logger
            )
            if specs is None:
                continue
            for spec_list in specs.values():
                for spec in spec_list:
                    self._plugin_specifications.setdefault(spec.item_type, []).append(spec)
        project_dict = load_project_dict(str(config_dir), self._logger)
        version_status = self._check_project_version(project_dict)
        if version_status != Status.OK:
            return version_status
        local_data_dict = load_local_project_data(config_dir, self._logger)
        merge_dicts(local_data_dict, project_dict)
        self._item_dicts, self._specification_dicts, self._connection_dicts, self._jump_dicts = open_project(
            project_dict, self._project_dir, self._logger
        )
        return Status.OK

    def _check_project_version(self, project_dict):
        """Checks project dict version.

        Args:
            project_dict (dict): project dict

        Returns:
            Status: status code
        """
        version = project_dict["project"]["version"]
        if version > LATEST_PROJECT_VERSION:
            self._logger.msg_error.emit(
                "Failed to open a project that is newer than what is supported by this version of Toolbox."
            )
            return Status.ERROR
        if version < LATEST_PROJECT_VERSION:
            self._logger.msg_error.emit("Unsupported project version. Open project in Toolbox GUI to upgrade it.")
            return Status.ERROR
        return Status.OK

    def _exec_mod_script(self):
        """Executes project modification script given in command line arguments.

        Returns:
             Status: status code
        """
        script_path = pathlib.Path(self._args.mod_script)
        if not script_path.exists() or not script_path.is_file():
            self._logger.msg_error.emit("Modification script doesn't exist.")
            return Status.ERROR
        with open(script_path, encoding="utf-8") as script_file:
            script_code = script_file.read()
        self._logger.msg.emit(f"Applying {script_path.name} to project.")
        project = ModifiableProject(self._project_dir, self._item_dicts, self._connection_dicts)
        exec(script_code, {"project": project})
        self._item_dicts = project.items_to_dict()
        self._connection_dicts = project.connections_to_dict()
        return Status.OK

    def _execute_project(self):
        """Executes all DAGs in a project.

        Returns:
            Status: status code
        """
        for item_type, plugin_specs in self._plugin_specifications.items():
            for spec in plugin_specs:
                spec_dict = spec.to_dict()
                spec_dict["definition_file_path"] = spec.definition_file_path
                self._specification_dicts.setdefault(item_type, []).append(spec_dict)
        dags = self._dags()
        settings = make_settings_dict_for_engine(self._app_settings)
        # Force local execution in headless mode
        if not settings.get("engineSettings/remoteExecutionEnabled", "false") == "false":
            settings["engineSettings/remoteExecutionEnabled"] = "false"
        selected = {name for name_list in self._args.select for name in name_list} if self._args.select else None
        deselected = {name for name_list in self._args.deselect for name in name_list} if self._args.deselect else None
        executed_items = set()
        skipped_items = set()
        for dag in dags:
            item_names_in_dag = set(dag.nodes)
            if not nx.is_directed_acyclic_graph(dag):
                self._logger.msg_error.emit("The project contains a graph that is not a Directed Acyclic Graph.")
                return Status.ERROR
            item_dicts_in_dag = {
                name: item_dict for name, item_dict in self._item_dicts.items() if name in item_names_in_dag
            }
            execution_permits = {
                item_name: (selected is None or item_name in selected)
                and (deselected is None or item_name not in deselected)
                for item_name in item_names_in_dag
            }
            skipped_items |= {name for name, selected in execution_permits.items() if not selected}
            if all(not permitted for permitted in execution_permits.values()):
                continue
            executed_items |= {name for name, selected in execution_permits.items() if selected}
            engine_data = {
                "items": item_dicts_in_dag,
                "specifications": self._specification_dicts,
                "connections": self._connection_dicts,
                "jumps": self._jump_dicts,
                "execution_permits": execution_permits,
                "items_module_name": "spine_items",
                "settings": settings,
                "project_dir": self._project_dir,
            }
            # exec_remotely is forced to False (see above)
            exec_remotely = settings.get("engineSettings/remoteExecutionEnabled", "false") == "true"
            engine_manager = make_engine_manager(exec_remotely)
            try:
                engine_manager.run_engine(engine_data)
            except EngineInitFailed as error:
                self._logger.msg_error.emit(f"Engine failed to start: {error}")
                return Status.ERROR
            while True:
                event_type, data = engine_manager.get_engine_event()
                self._process_engine_event(event_type, data)
                if event_type == "dag_exec_finished":
                    if data == str(SpineEngineState.FAILED):
                        return Status.ERROR
                    break
        selected_invalid = selected - executed_items if selected is not None else None
        deselected_invalid = deselected - skipped_items if deselected is not None else None
        if selected_invalid:
            self._logger.msg_warning.emit(
                f"The following selected items don't exist in the project: {', '.join(selected_invalid)}"
            )
        if deselected_invalid:
            self._logger.msg_warning.emit(
                f"The following deselected items don't exist in the project: {', '.join(deselected_invalid)}"
            )
        return Status.OK

    def _process_engine_event(self, event_type, data):
        handler = {
            "exec_started": self._handle_node_execution_started,
            "exec_finished": self._handle_node_execution_finished,
            "event_msg": self._handle_event_msg,
            "process_msg": self._handle_process_msg,
            "standard_execution_msg": self._handle_standard_execution_msg,
            "persistent_execution_msg": self._handle_persistent_execution_msg,
            "kernel_execution_msg": self._handle_kernel_execution_msg,
        }.get(event_type)
        if handler is None:
            return
        handler(data)

    def event(self, e):
        if e.type() == self._startup_event_type:
            e.accept()
            self._start.emit()
            return True
        return super().event(e)

    def _handle_node_execution_started(self, data):
        """Starts collecting messages from given node.

        Args:
            data (dict): execution start data
        """
        if data["direction"] == "BACKWARD":
            # Currently there are no interesting messages when executing backwards.
            return
        self._node_messages[data["item_name"]] = dict()

    def _handle_node_execution_finished(self, data):
        """Prints messages for finished nodes.

        Args:
            data (dict): execution end data
        """
        item_name = data["item_name"]
        messages = self._node_messages.get(item_name)
        if messages is None:
            return
        for filter_id, message in messages.items():
            if filter_id:
                self._logger.msg.emit(f"--- Output from filter id '{filter_id}' START")
            for line in message:
                self._logger.msg.emit(line)
        del self._node_messages[item_name]

    def _handle_event_msg(self, data):
        """Stores event messages for later printing.

        Args:
            data (dict): event message data
        """
        messages = self._node_messages.get(data["item_name"])
        if messages is None:
            return
        messages.setdefault(data["filter_id"], []).append(data["msg_text"])

    def _handle_process_msg(self, data):
        """Stores process messages for later printing.

        Args:
            data (dict): process message data
        """
        messages = self._node_messages.get(data["item_name"])
        if messages is None:
            return
        messages.setdefault(data["filter_id"], []).append(data["msg_text"])

    def _handle_standard_execution_msg(self, data):
        """Handles standard execution messages.

        Currently, these messages are ignored.

        Args:
            data (dict): execution message data
        """

    def _handle_persistent_execution_msg(self, data):
        """Handles persistent execution messages.

        Args:
            data (dict): execution message data
        """
        if data["type"] == "stdout" or data["type"] == "stderr":
            messages = self._node_messages.get(data["item_name"])
            if messages is None:
                return
            messages.setdefault(data["filter_id"], []).append(data["data"])

    def _handle_kernel_execution_msg(self, data):
        """Handles kernel messages.

        Currently, these messages are ignored.

        Args:
            data (dict): message data
        """


def headless_main(args):
    """
    Executes a project using :class:`QCoreApplication`.

    Args:
        args (argparser.Namespace): parsed command line arguments.
    Returns:
        int: exit status code; 0 for success, everything else for failure
    """
    application = QCoreApplication(sys.argv)
    startup_event_type = QEvent.Type(QEvent.registerEventType())
    task = ActionsWithProject(args, startup_event_type, application)
    application.postEvent(task, QEvent(startup_event_type))
    return application.exec()


def open_project(project_dict, project_dir, logger):
    """
    Opens a project.

    Args:
        project_dict (dict): a serialized project dictionary
        project_dir (Path): path to a directory containing the ``.spinetoolbox`` dir
        logger (LoggerInterface): a logger
    Returns:
        tuple: item dicts, specification dicts, connection dicts, jump dicts and a DagHandler object
    """
    specification_dicts = _specification_dicts(project_dict, project_dir, logger)
    return (
        project_dict["items"],
        specification_dicts,
        project_dict["project"]["connections"],
        project_dict["project"]["jumps"],
    )


def _specification_dicts(project_dict, project_dir, logger):
    """
    Loads project item specification dictionaries.

    Args:
        project_dict (dict): a serialized project dictionary
        project_dir (str): path to a directory containing the ``.spinetoolbox`` dir
        logger (LoggerInterface): a logger
    Returns:
        dict: a mapping from item type to a list of specification dicts
    """
    specification_dicts = dict()
    specification_file_paths = dict()
    for item_type, serialized_paths in project_dict["project"].get("specifications", {}).items():
        specification_file_paths[item_type] = [deserialize_path(path, project_dir) for path in serialized_paths]
    for item_type, paths in specification_file_paths.items():
        for path in paths:
            try:
                with open(path, "r") as definition_file:
                    try:
                        specification_dict = json.load(definition_file)
                    except ValueError:
                        logger.msg_error.emit(f"Item specification file '{path}' not valid")
                        continue
            except FileNotFoundError:
                logger.msg_error.emit(f"Specification file <b>{path}</b> does not exist")
                continue
            specification_dict["definition_file_path"] = path
            specification_dicts.setdefault(item_type, list()).append(specification_dict)
    return specification_dicts


@unique
class Status(IntEnum):
    """Status codes returned from headless execution."""

    OK = 0
    ERROR = 1
    ARGUMENT_ERROR = 2
