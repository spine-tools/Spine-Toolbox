######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains facilities to open and execute projects without GUI."""
from __future__ import annotations
import argparse
from collections.abc import Callable
from copy import deepcopy
from enum import IntEnum, unique
import os
import pathlib
import sys
from typing import Any
import networkx as nx
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, Signal, Slot
from spine_engine import SpineEngineState
from spine_engine.exception import EngineInitFailed
from spine_engine.load_project_items import load_item_specification_factories
from spine_engine.logger_interface import LoggerInterface
from spine_engine.server.util.zip_handler import ZipHandler
from spine_engine.utils.helpers import ExecutionDirection, get_file_size
from spine_engine.utils.serialization import deserialize_path
from .config import (
    LATEST_PROJECT_VERSION,
    PROJECT_CONFIG_DIR_NAME,
    PROJECT_CONSUMER_REPLAY_FILENAME,
    PROJECT_LOCAL_DATA_DIR_NAME,
    PROJECT_ZIP_FILENAME,
)
from .helpers import (
    HTMLTagFilter,
    make_settings_dict_for_engine,
)
from .load_project import (
    ProjectLoadingFailed,
    load_local_project_dict,
    load_project_dict,
    merge_local_dict_to_project_dict,
)
from .load_project_items import load_project_items
from .load_specification import (
    SpecificationLoadingFailed,
    load_plugin_dict,
    load_specification_dict,
    load_specification_local_data,
    merge_local_dict_to_specification_dict,
    plugin_specifications_from_dict,
    plugins_dirs,
)
from .project_item.logging_connection import HeadlessConnection
from .project_settings import ProjectSettings
from .project_upgrader import (
    InvalidProjectDict,
    ProjectUpgradeFailed,
    VersionCheck,
    check_project_dict_valid,
    check_project_version,
    upgrade_project,
)
from .server.engine_client import ClientSecurityModel, EngineClient, RemoteEngineInitFailed
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
    def _log_message(self, message: str) -> None:
        """Prints an information message."""
        self._print(message, sys.stdout)

    @Slot(str)
    def _log_warning(self, message: str) -> None:
        """Prints a warning message."""
        self._print(message, sys.stdout)

    @Slot(str)
    def _log_error(self, message: str) -> None:
        """Prints an error message."""
        self._print(message, sys.stderr)

    @Slot(str, str)
    def _show_information_box(self, title: str, message: str) -> None:
        """Prints an information message with a title."""
        self._print(title + ": " + message, sys.stdout)

    @Slot(str, str)
    def _show_error_box(self, title: str, message: str) -> None:
        """Prints an error message with a title."""
        self._print(title + ": " + message, sys.stderr)

    def _print(self, message: str, out_stream) -> None:
        """Filters HTML tags from message before printing it to given file."""
        self._tag_filter.feed(message)
        print(self._tag_filter.drain(), file=out_stream)


class ModifiableProject:
    """A simple project that is available for modification script."""

    def __init__(self, project_dir: pathlib.Path, items_dict: dict, connection_dicts: list[dict]):
        """
        Args:
            project_dir: project directory
            items_dict: project item dictionaries
            connection_dicts: connection dictionaries
        """
        self._project_dir = project_dir
        self._items = deepcopy(items_dict)
        self._connections = [HeadlessConnection.from_dict(d) for d in connection_dicts]

    @property
    def project_dir(self) -> pathlib.Path:
        return self._project_dir

    def find_connection(self, source_name: str, destination_name: str) -> HeadlessConnection:
        """Searches for a connection between given items.

        Args:
            source_name: source item's name
            destination_name: destination item's name

        Returns:
            connection instance or None if there is no connection
        """
        return next(
            (c for c in self._connections if c.source == source_name and c.destination == destination_name), None
        )

    def find_item(self, name: str) -> dict:
        """Searches for a project item.

        Args:
            name: item's name

        Returns:
            item dict or None if no such item exists
        """
        return self._items.get(name)

    def items_to_dict(self) -> dict:
        """Stores project items back to dictionaries.

        Returns:
            item dictionaries
        """
        return self._items

    def connections_to_dict(self) -> list[dict]:
        """Stores connections back to dictionaries.

        Returns:
            connection dictionaries
        """
        return [c.to_dict() for c in self._connections]


class ActionsWithProject(QObject):
    """
    A 'task' which opens Toolbox project and operates on it.

    The execution of this task is triggered by sending it a 'startup' QEvent using e.g. QCoreApplication.postEvent()
    """

    _start = Signal()
    """A private signal to actually start execution. Not to be used directly. Post a startup event instead."""

    def __init__(self, args: argparse.Namespace, startup_event_type: int, parent: QObject | None):
        """
        Args:
            args: parsed command line arguments
            startup_event_type: expected type id for the event that starts this task
            parent: a parent object
        """
        super().__init__(parent)
        self._args = args
        self._logger = HeadlessLogger()
        self._startup_event_type = startup_event_type
        self._start.connect(self._execute)
        self._node_messages = {}
        self._project_dir: pathlib.Path | None = None
        self._app_settings: QSettings | None = None
        self._item_dicts: dict | None = None
        self._specification_dicts: dict | None = None
        self._plugin_specifications: dict | None = None
        self._connection_dicts: list[dict] | None = None
        self._jump_dicts: list[dict] | None = None
        self._server_config: dict | None = None

    def _dags(self) -> list[nx.DiGraph]:
        graph = nx.DiGraph()
        graph.add_nodes_from(self._item_dicts)
        connections = map(HeadlessConnection.from_dict, self._connection_dicts)
        graph.add_edges_from(((x.source, x.destination) for x in connections))
        return [graph.subgraph(nodes) for nodes in nx.weakly_connected_components(graph)]

    @Slot()
    def _execute(self) -> None:
        """Executes this task."""
        if not self._args.project:
            self._logger.msg_error.emit("project missing from command line arguments.")
            QCoreApplication.instance().exit(Status.ARGUMENT_ERROR)
            return
        try:
            status = self._open_project()
            if self._args.execute_remotely:
                self._server_config = self._read_server_config()
                if not self._server_config:
                    self._logger.msg_error.emit("Reading server config file failed.")
                    QCoreApplication.instance().exit(Status.ARGUMENT_ERROR)
                    return
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

    def _open_project(self) -> Status:
        """Opens a project.

        Returns:
            status code
        """
        self._app_settings = QSettings("SpineProject", "Spine Toolbox", self)
        spec_factories = load_item_specification_factories("spine_items")
        self._plugin_specifications = {}
        self._project_dir = pathlib.Path(self._args.project).resolve()
        specification_local_data = load_specification_local_data(self._project_dir)
        for plugin_dir in plugins_dirs(self._app_settings):
            try:
                plugin_dict = load_plugin_dict(plugin_dir)
                if plugin_dict is None:
                    continue
                specs = plugin_specifications_from_dict(
                    plugin_dict, specification_local_data, spec_factories, self._app_settings, self._logger
                )
            except SpecificationLoadingFailed as error:
                self._logger.msg_error.emit(str(error))
                continue
            for spec_list in specs.values():
                for spec in spec_list:
                    self._plugin_specifications.setdefault(spec.item_type, []).append(spec)
        try:
            project_dict = load_project_dict(self._project_dir)
            project_dict = self._ensure_project_is_up_to_date(project_dict)
            check_project_dict_valid(LATEST_PROJECT_VERSION, project_dict)
            local_data_dict = load_local_project_dict(self._project_dir)
        except (ProjectLoadingFailed, ProjectUpgradeFailed, InvalidProjectDict) as error:
            self._logger.msg_error.emit(str(error))
            return Status.ERROR
        merge_local_dict_to_project_dict(local_data_dict, project_dict)
        settings_dict, self._item_dicts, self._specification_dicts, self._connection_dicts, self._jump_dicts = (
            open_project(project_dict, self._project_dir, specification_local_data, self._logger)
        )
        settings = ProjectSettings.from_dict(settings_dict)
        if settings.mode == "consumer":
            replay_file_path = pathlib.Path(
                self._project_dir,
                PROJECT_CONFIG_DIR_NAME,
                PROJECT_LOCAL_DATA_DIR_NAME,
                PROJECT_CONSUMER_REPLAY_FILENAME,
            )
            if replay_file_path.exists():
                self._logger.msg_warning.emit(
                    "Warning: changes made to project in Consumer mode are not supported in headless mode."
                )
        return Status.OK

    def _ensure_project_is_up_to_date(self, project_dict: dict) -> dict:
        """Checks project dict version and updates it if necessary.

        Args:
            project_dict: project dict

        Returns:
            Up-to-date project dict.
        """
        match check_project_version(project_dict):
            case VersionCheck.OK:
                return project_dict
            case VersionCheck.UPGRADE_REQUIRED:
                item_factories = load_project_items("spine_items")
                return upgrade_project(project_dict, self._project_dir, item_factories, self._logger.msg_warning.emit)
            case VersionCheck.TOO_RECENT:
                version = project_dict["version"]
                raise ProjectUpgradeFailed(
                    f"Opening project {self._project_dir} failed. The project's version is {version}, while "
                    f"this version of Spine Toolbox supports project versions up to and "
                    f"including {LATEST_PROJECT_VERSION}. To open this project, you should "
                    f"upgrade Spine Toolbox."
                )
            case _:
                raise RuntimeError("logic error: check_project_version returned an unknown value")

    def _exec_mod_script(self) -> Status:
        """Executes project modification script given in command line arguments.

        Returns:
             status code
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

    def _execute_project(self) -> Status:
        """Executes all DAGs in a project.

        Returns:
            status code
        """
        for item_type, plugin_specs in self._plugin_specifications.items():
            for spec in plugin_specs:
                spec_dict = spec.to_dict()
                spec_dict["definition_file_path"] = spec.definition_file_path
                self._specification_dicts.setdefault(item_type, []).append(spec_dict)
        dags = self._dags()
        job_id = self._prepare_remote_execution()
        if not job_id:
            self._logger.msg_error.emit("Pinging the server or uploading the project failed.")
            return Status.ERROR
        settings = make_settings_dict_for_engine(self._app_settings)
        # Enable remote execution if server config file was given, else force local execution
        if self._server_config is not None:
            settings["engineSettings/remoteExecutionEnabled"] = "true"
            settings = self._insert_remote_engine_settings(settings)
        else:
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
                "project_dir": self._project_dir.as_posix(),
            }
            exec_remotely = bool(self._server_config)
            engine_manager = make_engine_manager(exec_remotely, job_id=job_id)
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

    def _process_engine_event(self, event_type: str, data: dict) -> None:
        try:
            handler: Callable[[dict], None] = {
                "exec_started": self._handle_node_execution_started,
                "exec_finished": self._handle_node_execution_finished,
                "event_msg": self._handle_event_msg,
                "process_msg": self._handle_process_msg,
                "standard_execution_msg": self._handle_standard_execution_msg,
                "persistent_execution_msg": self._handle_persistent_execution_msg,
                "kernel_execution_msg": self._handle_kernel_execution_msg,
                "server_status_msg": self._handle_server_status_msg,
            }[event_type]
        except KeyError:
            return
        handler(data)

    def event(self, e):
        if e.type() == self._startup_event_type:
            e.accept()
            self._start.emit()
            return True
        return super().event(e)

    def _handle_node_execution_started(self, data: dict) -> None:
        """Starts collecting messages from given node.

        Args:
            data: execution start data
        """
        if data["direction"] == ExecutionDirection.BACKWARD:
            # Currently there are no interesting messages when executing backwards.
            return
        self._node_messages[data["item_name"]] = {}

    def _handle_node_execution_finished(self, data: dict) -> None:
        """Prints messages for finished nodes.

        Args:
            data: execution end data
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

    def _handle_event_msg(self, data: dict) -> None:
        """Stores event messages for later printing.

        Args:
            data: event message data
        """
        messages = self._node_messages.get(data["item_name"])
        if messages is None:
            return
        messages.setdefault(data["filter_id"], []).append(data["msg_text"])

    def _handle_process_msg(self, data: dict) -> None:
        """Stores process messages for later printing.

        Args:
            data: process message data
        """
        messages = self._node_messages.get(data["item_name"])
        if messages is None:
            return
        messages.setdefault(data["filter_id"], []).append(data["msg_text"])

    def _handle_standard_execution_msg(self, data: dict) -> None:
        """Handles standard execution messages.

        Currently, these messages are ignored.

        Args:
            data: execution message data
        """

    def _handle_persistent_execution_msg(self, data: dict) -> None:
        """Handles persistent execution messages.

        Args:
            data: execution message data
        """
        if data["type"] == "stdout" or data["type"] == "stderr":
            messages = self._node_messages.get(data["item_name"])
            if messages is None:
                return
            messages.setdefault(data["filter_id"], []).append(data["data"])

    def _handle_kernel_execution_msg(self, data: dict) -> None:
        """Handles kernel messages.

        Currently, these messages are ignored.

        Args:
            data: message data
        """

    def _handle_server_status_msg(self, data: dict) -> None:
        """Handles received remote execution messages."""
        if data["msg_type"] == "success":
            self._logger.msg_success.emit(data["text"])
        elif data["msg_type"] == "neutral":
            self._logger.msg.emit(data["text"])
        elif data["msg_type"] == "fail":
            self._logger.msg_error.emit(data["text"])
        elif data["msg_type"] == "warning":
            self._logger.msg_warning.emit(data["text"])

    def _read_server_config(self) -> dict | None:
        """Reads the user provided server settings file that the client requires to establish connection.

        Returns:
            Dictionary containing the EngineClient settings or None if the given config file does not exist.
        """
        cfg_file = self._args.execute_remotely[0]
        cfg_fp = os.path.join(self._project_dir, cfg_file)
        if os.path.isfile(cfg_fp):
            with open(cfg_fp, encoding="utf-8") as fp:
                lines = fp.readlines()
            lines = [l.strip() for l in lines]
            host = lines[0]
            port = lines[1]
            smodel = lines[2]
            rel_sec_folder = lines[3]
            sec_model = "stonehouse" if smodel.lower() == "on" else ""
            if sec_model == "stonehouse":
                sec_folder = os.path.abspath(os.path.join(self._project_dir.as_posix(), rel_sec_folder))
            else:
                sec_folder = ""
            cfg_dict = {"host": host, "port": port, "security_model": sec_model, "security_folder": sec_folder}
            return cfg_dict
        self._logger.msg_error.emit(f"cfg file '{cfg_fp}' missing.")
        return None

    def _insert_remote_engine_settings(self, settings: dict) -> dict:
        """Inserts remote engine client settings into the settings dictionary that is delivered to the engine.

        Args:
            settings: Original settings dictionary

        Returns:
            Settings dictionary containing remote engine client settings
        """
        settings["engineSettings/remoteHost"] = self._server_config["host"]
        settings["engineSettings/remotePort"] = self._server_config["port"]
        settings["engineSettings/remoteSecurityModel"] = self._server_config["security_model"]
        settings["engineSettings/remoteSecurityFolder"] = self._server_config["security_folder"]
        return settings

    def _prepare_remote_execution(self) -> str:
        """If remote execution is enabled, makes an EngineClient for pinging and uploading the project.
        If ping is successful, the project is uploaded to the server. If the upload is successful, the
        server responds with a Job id, which is later used by the client to make a 'start execution'
        request.

        Returns:
            Job id if server is ready for remote execution, empty string if something went wrong
                or "1" if local execution is enabled.
        """
        if not self._server_config:
            return "1"
        host, port = self._server_config["host"], self._server_config["port"]
        security_on = self._server_config["security_model"].lower() != ""
        sec_model = ClientSecurityModel.STONEHOUSE if security_on else ClientSecurityModel.NONE
        try:
            engine_client = EngineClient(host, port, sec_model, self._server_config["security_folder"])
        except RemoteEngineInitFailed as e:
            self._logger.msg_error.emit(f"Server is not responding in {host}:{port}. {e}.")
            return ""
        engine_client.set_start_time()  # Set start_time for upload operation
        # Archive the project into a zip-file
        dest_dir = os.path.join(self._project_dir, os.pardir)  # Parent dir of project_dir
        _, project_name = os.path.split(self._project_dir)
        self._logger.msg.emit(f"Squeezing project <b>{project_name}</b> into {PROJECT_ZIP_FILENAME}.zip")
        try:
            ZipHandler.package(src_folder=self._project_dir, dst_folder=dest_dir, fname=PROJECT_ZIP_FILENAME)
        except Exception as e:
            self._logger.msg_error.emit(f"{e}")
            engine_client.close()
            return ""
        project_zip_file = os.path.abspath(os.path.join(self._project_dir, os.pardir, PROJECT_ZIP_FILENAME + ".zip"))
        if not os.path.isfile(project_zip_file):
            self._logger.msg_error.emit(f"Project zip-file {project_zip_file} does not exist")
            engine_client.close()
            return ""
        file_size = get_file_size(os.path.getsize(project_zip_file))
        self._logger.msg_warning.emit(f"Uploading project [{file_size}] ...")
        job_id = engine_client.upload_project(project_name, project_zip_file)
        t = engine_client.get_elapsed_time()
        self._logger.msg.emit(f"Upload time: {t}. Job ID: <b>{job_id}</b>")
        engine_client.close()
        return job_id


def headless_main(args: argparse.Namespace) -> int:
    """
    Executes a project using :class:`QCoreApplication`.

    Args:
        args: parsed command line arguments.

    Returns:
        exit status code; 0 for success, everything else for failure
    """
    application = QCoreApplication(sys.argv)
    startup_event_type = QEvent.Type(QEvent.registerEventType())
    task = ActionsWithProject(args, startup_event_type, application)
    application.postEvent(task, QEvent(startup_event_type))
    return application.exec()


def open_project(
    project_dict: dict, project_dir: pathlib.Path, local_specification_data: dict, logger: LoggerInterface
) -> tuple[dict[str, Any], dict[str, dict], dict[str, list[dict]], list[dict], list[dict]]:
    """
    Opens a project.

    Args:
        project_dict: a serialized project dictionary
        project_dir: path to a directory containing the ``.spinetoolbox`` dir
        local_specification_data: Local specification data.
        logger: a logger instance

    Returns:
        item dicts, specification dicts, connection dicts and jump dicts
    """
    specification_dicts = _specification_dicts(project_dict, project_dir, local_specification_data, logger)
    return (
        project_dict["project"]["settings"],
        project_dict["items"],
        specification_dicts,
        project_dict["project"]["connections"],
        project_dict["project"]["jumps"],
    )


def _specification_dicts(
    project_dict: dict, project_dir: str | pathlib.Path, local_specification_data: dict, logger: LoggerInterface
) -> dict[str, list[dict]]:
    """
    Loads project item specification dictionaries.

    Args:
        project_dict: a serialized project dictionary
        project_dir: path to a directory containing the ``.spinetoolbox`` dir
        local_specification_data: Local specification data.
        logger: A logger instance.

    Returns:
        a mapping from item type to a list of specification dicts
    """
    specification_dicts = {}
    specification_file_paths = {}
    for item_type, serialized_paths in project_dict["project"].get("specifications", {}).items():
        specification_file_paths[item_type] = [deserialize_path(path, project_dir) for path in serialized_paths]
    for item_type, paths in specification_file_paths.items():
        for path in paths:
            try:
                specification_dict = load_specification_dict(path)
                merge_local_dict_to_specification_dict(local_specification_data, specification_dict)
            except SpecificationLoadingFailed as error:
                logger.msg_error.emit(str(error))
                continue
            specification_dicts.setdefault(item_type, []).append(specification_dict)
    return specification_dicts


@unique
class Status(IntEnum):
    """Status codes returned from headless execution."""

    OK = 0
    ERROR = 1
    ARGUMENT_ERROR = 2
