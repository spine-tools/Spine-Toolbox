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
from spine_engine import SpineEngine, SpineEngineState
from .dag_handler import DirectedGraphHandler
from .helpers import deserialize_path
from .load_project_items import load_executable_items, load_item_specification_factories


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
        self._startup_event_type = startup_event_type
        self._start.connect(self._execute)

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
        """Opens a project and executes all DAGs in that project."""
        logger = HeadlessLogger()
        project_dir = self._args.project
        project_file_path = pathlib.Path(project_dir, ".spinetoolbox", "project.json").resolve()
        try:
            with project_file_path.open() as project_file:
                try:
                    project_dict = json.load(project_file)
                except json.decoder.JSONDecodeError:
                    logger.msg_error.emit(f"Error in project file {project_file_path}. Invalid JSON.")
                    return _Status.ERROR
        except OSError:
            logger.msg_error.emit(f"Project file {project_file_path} missing")
            return _Status.ERROR
        executable_items, dag_handler = open_project(project_dict, project_dir, logger)
        if executable_items is None:
            return _Status.ERROR
        dags = dag_handler.dags()
        for dag in dags:
            node_successors = dag_handler.node_successors(dag)
            if not node_successors:
                logger.msg_error("The project contains a graph that is not a Directed Acyclic Graph.")
                return _Status.ERROR
            items_in_dag = tuple(item for item in executable_items if item.name in dag.nodes)
            execution_permits = {item_name: True for item_name in dag.nodes}
            engine = SpineEngine(items_in_dag, node_successors, execution_permits)
            engine.run()
            if engine.state() == SpineEngineState.FAILED:
                return _Status.ERROR
        return _Status.OK

    def event(self, e):
        if e.type() == self._startup_event_type:
            e.accept()
            self._start.emit()
            return True
        return super().event(e)


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
        tuple: a list of executable items, a dict of item specifications, and a DagHandler object
    """
    app_settings = QSettings("SpineProject", "Spine Toolbox")
    specification_factories = load_item_specification_factories()
    item_specifications = _specifications(project_dict, project_dir, specification_factories, app_settings, logger)
    executable_classes = load_executable_items()
    executable_items = list()
    dag_handler = DirectedGraphHandler()
    for item_name, item_dict in project_dict["items"].items():
        dag_handler.add_dag_node(item_name)
        try:
            item_type = item_dict["type"]
        except KeyError:
            logger.msg_error.emit(
                "Project item is missing the 'type' attribute in the project.json file."
                " This might be caused by an outdated project file."
            )
            return None, None
        executable_class = executable_classes[item_type]
        try:
            item = executable_class.from_dict(
                item_dict, item_name, project_dir, app_settings, item_specifications, logger
            )
        except KeyError as missing_key:
            logger.msg_error.emit(f"'{missing_key}' is missing in the project.json file.")
            item = None
        if item is None:
            return None, None
        executable_items.append(item)
    for connection in project_dict["project"]["connections"]:
        from_name = connection["from"][0]
        to_name = connection["to"][0]
        dag_handler.add_graph_edge(from_name, to_name)
    return executable_items, dag_handler


def _specifications(project_dict, project_dir, specification_factories, app_settings, logger):
    """
    Creates project item specifications.

    Args:
        project_dict (dict): a serialized project dictionary
        project_dir (str): path to a directory containing the ``.spinetoolbox`` dir
        specification_factories (dict): a mapping from item type to specification factory
        app_settings (QSettings): Toolbox settings
        logger (LoggerInterface): a logger
    Returns:
        dict: a mapping from item type and specification name to specification
    """
    specifications = dict()
    specifications_dict = project_dict["project"].get("specifications", {})
    definition_file_paths = dict()
    for item_type, serialized_paths in specifications_dict.items():
        definition_file_paths[item_type] = [deserialize_path(path, project_dir) for path in serialized_paths]
    for item_type, paths in definition_file_paths.items():
        for definition_path in paths:
            try:
                with open(definition_path, "r") as definition_file:
                    try:
                        definition = json.load(definition_file)
                    except ValueError:
                        logger.msg_error.emit(f"Item specification file '{definition_path}' not valid")
                        continue
            except FileNotFoundError:
                logger.msg_error.emit(f"Specification file <b>{definition_path}</b> does not exist")
                continue
            factory = specification_factories.get(item_type)
            if factory is None:
                continue
            specification = factory.make_specification(
                definition, definition_path, app_settings, logger, embedded_julia_console=None, embedded_python_console=None
            )
            specifications.setdefault(item_type, dict())[specification.name] = specification
    return specifications


@unique
class _Status(IntEnum):
    """Status codes returned from headless execution."""

    OK = 0
    ERROR = 1
