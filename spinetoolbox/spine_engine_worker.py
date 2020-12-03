######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Items.
# Spine Items is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains SpineEngineWorker.

:authors: M. Marin (KTH)
:date:   14.10.2020
"""

import socket
import json
from PySide2.QtCore import Signal, Slot, QObject, QThread
from spine_engine.spine_engine_experimental import SpineEngineExperimental


@Slot(list)
def _handle_dag_execution_started(project_items):
    for item in project_items:
        item.get_icon().execution_icon.mark_execution_wating()


@Slot(object, object)
def _handle_node_execution_started(item, direction):
    icon = item.get_icon()
    if direction == "FORWARD":
        icon.execution_icon.mark_execution_started()
        if hasattr(icon, "animation_signaller"):
            icon.animation_signaller.animation_started.emit()


@Slot(object, object, object, bool, bool)
def _handle_node_execution_finished(item, direction, state, success, skipped):
    icon = item.get_icon()
    if direction == "FORWARD":
        icon.execution_icon.mark_execution_finished(success, skipped)
        if hasattr(icon, "animation_signaller"):
            icon.animation_signaller.animation_stopped.emit()
        if state == "RUNNING":
            icon.run_execution_leave_animation(skipped)


@Slot(object, str, str)
def _handle_log_message_arrived(item, filter_id, msg_type, msg_text):
    item.add_log_message(filter_id, msg_type, msg_text)


@Slot(object, str, str)
def _handle_process_message_arrived(item, filter_id, msg_type, msg_text):
    item.add_process_message(filter_id, msg_type, msg_text)


class SpineEngineWorker(QObject):

    finished = Signal()
    _dag_execution_started = Signal(list)
    _node_execution_started = Signal(object, object)
    _node_execution_finished = Signal(object, object, object, bool, bool)
    _log_message_arrived = Signal(object, str, str, str)
    _process_message_arrived = Signal(object, str, str, str)

    def __init__(self, toolbox, engine_data, dag, dag_identifier, project_items):
        """
        Args:
            toolbox (ToolboxUI)
            engine_data (dict): engine data
            dag (DirectedGraphHandler)
            dag_identifier (str)
            project_items (dict): mapping from project item name to :class:`ProjectItem`
        """
        super().__init__()
        self._toolbox = toolbox
        self._engine_mngr = self._make_engine_manager(engine_data)
        self.dag = dag
        self.dag_identifier = dag_identifier
        self._engine_final_state = "UNKNOWN"
        self._executing_items = []
        self._project_items = project_items
        self.sucessful_executions = []
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self.do_work)
        self._dag_execution_started.connect(_handle_dag_execution_started)
        self._node_execution_started.connect(_handle_node_execution_started)
        self._node_execution_finished.connect(_handle_node_execution_finished)
        self._log_message_arrived.connect(_handle_log_message_arrived)
        self._process_message_arrived.connect(_handle_process_message_arrived)

    def _make_engine_manager(self, engine_data):
        engine_server_address = self._toolbox.qsettings().value("appSettings/engineServerAddress", defaultValue="")
        if not engine_server_address:
            return LocalSpineEngineManager(engine_data)
        return RemoteSpineEngineManager(engine_server_address, engine_data)

    def stop_engine(self):
        self._engine_mngr.stop_engine()

    def engine_final_state(self):
        return self._engine_final_state

    def thread(self):
        return self._thread

    def start(self):
        self._dag_execution_started.emit(list(self._project_items.values()))
        self._thread.start()

    @Slot()
    def do_work(self):
        """Does the work and emits finished when done."""
        self._engine_mngr.run_engine()
        while True:
            event_type, data = self._engine_mngr.get_engine_event()
            self._process_event(event_type, data)
            if event_type == "dag_exec_finished":
                self._engine_final_state = data
                break
        self.finished.emit()

    def _process_event(self, event_type, data):
        handler = {
            "exec_started": self._handle_node_execution_started,
            "exec_finished": self._handle_node_execution_finished,
            "log_msg": self._handle_log_msg,
            "process_msg": self._handle_process_msg,
            "standard_execution_msg": self._handle_standard_execution_msg,
            "kernel_execution_msg": self._handle_kernel_execution_msg,
        }.get(event_type)
        if handler is None:
            return
        handler(data)

    def _handle_standard_execution_msg(self, msg):
        item = self._project_items[msg["item_name"]]
        if msg["type"] == "execution_failed_to_start":
            msg_text = f"Program <b>{msg['program']}</b> failed to start: {msg['error']}"
            self._log_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "execution_started":
            self._log_message_arrived.emit(item, msg["filter_id"], "msg", f"\tStarting program <b>{msg['program']}</b>")
            self._log_message_arrived.emit(item, msg["filter_id"], "msg", f"\tArguments: <b>{msg['args']}</b>")
            self._log_message_arrived.emit(
                item,
                msg["filter_id"],
                "msg_warning",
                "\tExecution is in progress. See Process Log for messages (stdout&stderr)",
            )

    def _handle_kernel_execution_msg(self, msg):
        item = self._project_items[msg["item_name"]]
        language = msg["language"].capitalize()
        if msg["type"] == "kernel_started":
            console = {"julia": item.julia_console, "python": item.python_console}.get(msg["language"])
            if console is not None:
                console.connect_to_kernel(msg["kernel_name"], msg["connection_file"])
        elif msg["type"] == "kernel_spec_not_found":
            msg_text = (
                f"\tUnable to find specification for {language} kernel <b>{msg['kernel_name']}</b>. "
                f"Go to Settings->Tools to select a valid {language} kernel."
            )
            self._log_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "execution_failed_to_start":
            msg_text = f"\tExecution on {language} kernel <b>{msg['kernel_name']}</b> failed to start: {msg['error']}"
            self._log_message_arrived.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "execution_started":
            self._log_message_arrived.emit(
                item, msg["filter_id"], "msg", f"\tStarting program on {language} kernel <b>{msg['kernel_name']}</b>"
            )
            self._log_message_arrived.emit(
                item, msg["filter_id"], "msg_warning", f"See {language} Console for messages."
            )

    def _handle_process_msg(self, data):
        self._do_handle_process_msg(**data)

    def _do_handle_process_msg(self, item_name, filter_id, msg_type, msg_text):
        item = self._project_items[item_name]
        self._process_message_arrived.emit(item, filter_id, msg_type, msg_text)

    def _handle_log_msg(self, data):
        self._do_handle_log_msg(**data)

    def _do_handle_log_msg(self, item_name, filter_id, msg_type, msg_text):
        item = self._project_items[item_name]
        self._log_message_arrived.emit(item, filter_id, msg_type, msg_text)

    def _handle_node_execution_started(self, data):
        self._do_handle_node_execution_started(**data)

    def _do_handle_node_execution_started(self, item_name, direction):
        """Starts item icon animation when executing forward."""
        item = self._project_items[item_name]
        self._executing_items.append(item)
        self._node_execution_started.emit(item, direction)

    def _handle_node_execution_finished(self, data):
        self._do_handle_node_execution_finished(**data)

    def _do_handle_node_execution_finished(self, item_name, direction, state, success, skipped):
        item = self._project_items[item_name]
        if success and not skipped:
            self.sucessful_executions.append((item, direction, state))
        self._executing_items.remove(item)
        self._node_execution_finished.emit(item, direction, state, success, skipped)

    def clean_up(self):
        for item in self._executing_items:
            self._node_execution_finished.emit(item, None, None, False)
        self._thread.quit()
        self._thread.wait()
        self.deleteLater()


class SpineEngineManagerBase:
    def run_engine(self):
        raise NotImplementedError()

    def get_engine_event(self):
        raise NotImplementedError()

    def stop_engine(self):
        raise NotImplementedError()


class RemoteSpineEngineManager(SpineEngineManagerBase):
    _ENCODING = "ascii"

    def __init__(self, engine_server_address, engine_data):
        """
        Sends a run_engine request to the server.

        Args:
            engine_data (dict): The engine data.

        Returns:
            str: engine id, for further calls
        """
        self._engine_server_address = engine_server_address
        self._engine_data = engine_data
        self.request = None
        self._engine_id = None

    def run_engine(self):
        """
        Sends a run_engine request to the server.
        """
        self._engine_id = self._send("run_engine", self._engine_data)

    def get_engine_event(self):
        """
        Sends a get_engine_event request to the server.

        Returns:
            tuple(str,dict): two element tuple: event type identifier string, and event data dictionary
        return self._send("run_engine", data)
        """
        return self._send("get_engine_event", self._engine_id)

    def stop_engine(self):
        """
        Sends a stop_engine request to the server.
        """
        self._send("stop_engine", self._engine_id, receive=False)

    def _send(self, request, *args, receive=True):
        """
        Sends a request to the server with the given arguments.

        Args:
            request (str): One of the supported engine server requests
            args: Request arguments
            receive (bool, optional): If True (the default) also receives the response and returns it.

        Returns:
            str or NoneType: response, or None if receive is False
        """
        msg = json.dumps((request, args))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.request:
            self.request.connect(self._engine_server_address)
            self.request.sendall(bytes(msg, "ascii"))
            if receive:
                response = self._recvall()
                return json.loads(response)

    def _recvall(self):
        """
        Receives and returns all data in the current request.

        Returns:
            str
        """
        BUFF_SIZE = 4096
        fragments = []
        while True:
            chunk = str(self.request.recv(BUFF_SIZE), self._ENCODING)
            fragments.append(chunk)
            if len(chunk) < BUFF_SIZE:
                break
        return "".join(fragments)


class LocalSpineEngineManager(SpineEngineManagerBase):
    def __init__(self, engine_data):
        self._engine = None
        self._engine_data = engine_data

    def run_engine(self):
        self._engine = SpineEngineExperimental(**self._engine_data, debug=True)

    def get_engine_event(self):
        return self._engine.get_event()

    def stop_engine(self):
        self._engine.stop()
