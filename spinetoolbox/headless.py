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
Contains facilities to open and execute projects without GUI.

:authors: A. Soininen (VTT)
:date:   29.4.2020
"""
from enum import IntEnum, unique
import json
import logging
import pathlib
import sys
from PySide2.QtCore import QCoreApplication, QEvent, QObject, QSettings, Signal, Slot
from spine_engine import SpineEngineState
from spine_engine.utils.serialization import deserialize_path
from .dag_handler import DirectedGraphHandler
from .helpers import make_settings_dict_for_engine
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

    # pylint: disable=no-self-use
    @Slot(str)
    def _log_message(self, message):
        """Writes an information message to Python's logging system."""
        logging.info(message)

    # pylint: disable=no-self-use
    @Slot(str)
    def _log_warning(self, message):
        """Writes a warning message to Python's logging system."""
        logging.warning(message)

    # pylint: disable=no-self-use
    @Slot(str)
    def _log_error(self, message):
        """Writes an error message to Python's logging system."""
        logging.error(message)

    # pylint: disable=no-self-use
    @Slot(str, str)
    def _show_information_box(self, title, message):
        """Writes an information message with a title to Python's logging system."""
        logging.info(title + ": " + message)

    # pylint: disable=no-self-use
    @Slot(str, str)
    def _show_error_box(self, title, message):
        """Writes an error message with a title to Python's logging system."""
        logging.error(title + ": " + message)


class ExecuteProject(QObject):
    """
    A 'task' which opens and executes a Toolbox project when triggered to do so.

    The execution of this task is triggered by sending it a 'startup' QEvent using, e.g. QCoreApplication.postEvent()
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

    @Slot()
    def _execute(self):
        """Executes this task."""
        try:
            status = self._open_and_execute_project()
            QCoreApplication.instance().exit(status)
        except Exception:
            QCoreApplication.instance().exit(_Status.ERROR)
            raise

    def _open_and_execute_project(self):
        """Opens a project and executes all DAGs in that project.

        Returns:
            _Status: status code
        """
        project_dir = pathlib.Path(self._args.project).resolve()
        project_file_path = project_dir / ".spinetoolbox" / "project.json"
        try:
            with project_file_path.open() as project_file:
                try:
                    project_dict = json.load(project_file)
                except json.decoder.JSONDecodeError:
                    self._logger.msg_error.emit(f"Error in project file {project_file_path}. Invalid JSON.")
                    return _Status.ERROR
        except OSError:
            self._logger.msg_error.emit(f"Project file {project_file_path} missing")
            return _Status.ERROR
        item_dicts, specification_dicts, connection_dicts, dag_handler = open_project(
            project_dict, project_dir, self._logger
        )
        dags = dag_handler.dags()
        app_settings = QSettings("SpineProject", "Spine Toolbox")
        settings = make_settings_dict_for_engine(app_settings)
        for dag in dags:
            node_successors = dag_handler.node_successors(dag)
            if not node_successors:
                self._logger.msg_error.emit("The project contains a graph that is not a Directed Acyclic Graph.")
                return _Status.ERROR
            execution_permits = {item_name: True for item_name in dag.nodes}
            engine_data = {
                "items": item_dicts,
                "specifications": specification_dicts,
                "connections": connection_dicts,
                "node_successors": node_successors,
                "execution_permits": execution_permits,
                "settings": settings,
                "project_dir": project_dir,
            }
            engine_server_address = app_settings.value("appSettings/engineServerAddress", defaultValue="")
            engine_manager = make_engine_manager(engine_server_address)
            engine_manager.run_engine(engine_data)
            while True:
                event_type, data = engine_manager.get_engine_event()
                self._process_engine_event(event_type, data)
                if event_type == "dag_exec_finished":
                    if data == SpineEngineState.FAILED:
                        return _Status.ERROR
                    break
        return _Status.OK

    def _process_engine_event(self, event_type, data):
        handler = {
            "exec_started": self._handle_node_execution_started,
            "exec_finished": self._handle_node_execution_finished,
            "event_msg": self._handle_event_msg,
            "process_msg": self._handle_process_msg,
            "standard_execution_msg": self._handle_standard_execution_msg,
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
        self._node_messages[data["item_name"]] = list()

    def _handle_node_execution_finished(self, data):
        """Prints messages for finished nodes.

        Args:
            data (dict): execution end data
        """
        item_name = data["item_name"]
        messages = self._node_messages.get(item_name)
        if messages is None:
            return
        for message in messages:
            self._logger.msg.emit(message)
        del self._node_messages[item_name]

    def _handle_event_msg(self, data):
        """Stores event messages for later printing.

        Args:
            data (dict): event message data
        """
        messages = self._node_messages.get(data["item_name"])
        if messages is None:
            return
        messages.append(data["msg_text"])

    def _handle_process_msg(self, data):
        """Stores process messages for later printing.

        Args:
            data (dict): process message data
        """
        messages = self._node_messages.get(data["item_name"])
        if messages is None:
            return
        messages.append(data["msg_text"])

    def _handle_standard_execution_msg(self, data):
        """Handles standard execution messages.

        Currently, these messages are ignored.

        Args:
            data (dict): execution message data
        """

    def _handle_kernel_execution_msg(self, data):
        """Handles kernel messages.

        Currently, these messages are ignored.

        Args:
            data (dict): execution message data
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
    task = ExecuteProject(args, startup_event_type, application)
    application.postEvent(task, QEvent(startup_event_type))
    return application.exec_()


def open_project(project_dict, project_dir, logger):
    """
    Opens a project.

    Args:
        project_dict (dict): a serialized project dictionary
        project_dir (str): path to a directory containing the ``.spinetoolbox`` dir
        logger (LoggerInterface): a logger
    Returns:
        tuple: item dicts, specification dicts, connection dicts and a DagHandler object
    """
    specification_dicts = _specification_dicts(project_dict, project_dir, logger)
    item_dicts = dict()
    dag_handler = DirectedGraphHandler()
    for item_name, item_dict in project_dict["items"].items():
        dag_handler.add_dag_node(item_name)
        item_dicts[item_name] = item_dict
    for connection in project_dict["project"]["connections"]:
        from_name = connection["from"][0]
        to_name = connection["to"][0]
        dag_handler.add_graph_edge(from_name, to_name)
    return project_dict["items"], specification_dicts, project_dict["project"]["connections"], dag_handler


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
class _Status(IntEnum):
    """Status codes returned from headless execution."""

    OK = 0
    ERROR = 1
