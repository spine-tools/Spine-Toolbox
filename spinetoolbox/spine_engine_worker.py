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

from PySide2.QtCore import Signal, Slot, QObject, QThread


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


@Slot(object, object, object, bool)
def _handle_node_execution_finished(item, direction, state, success):
    icon = item.get_icon()
    if direction == "FORWARD":
        icon.execution_icon.mark_execution_finished(success)
        if hasattr(icon, "animation_signaller"):
            icon.animation_signaller.animation_stopped.emit()
        if state == "RUNNING":
            icon.run_execution_leave_animation()


@Slot(object, str, str)
def _handle_log_message_arrived(item, msg_type, msg_text):
    item.get_icon().execution_icon.add_log_message(msg_type, msg_text)


@Slot(object, str, str)
def _handle_process_message_arrived(item, msg_type, msg_text):
    item.get_icon().execution_icon.add_process_message(msg_type, msg_text)


class SpineEngineWorker(QObject):

    finished = Signal()
    _dag_execution_started = Signal(list)
    _node_execution_started = Signal(object, object)
    _node_execution_finished = Signal(object, object, object, bool)
    _log_message_arrived = Signal(object, str, str)
    _process_message_arrived = Signal(object, str, str)

    def __init__(self, toolbox, data, dag, dag_identifier, project_items):
        """
        Args:
            toolbox (ToolboxUI)
            engine_id (str): uuid of engine in server
            dag (DirectedGraphHandler)
            dag_identifier (str)
            project_items (list(ProjectItemBase))
        """
        super().__init__()
        self._toolbox = toolbox
        self._data = data
        self.dag = dag
        self.dag_identifier = dag_identifier
        self._engine_final_state = "UNKNOWN"
        self._engine_stopped = False
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

    def stop_engine(self):
        self._engine_stopped = True

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
        engine_client = self._toolbox.get_engine_client()
        engine_id = engine_client.run_engine(self._data)
        while True:
            if self._engine_stopped:
                engine_client.stop_engine(engine_id)
            event_type, data = engine_client.get_engine_event(engine_id)
            self._process_event(event_type, data)
            if event_type == "dag_exec_finished":
                self._engine_final_state = data
                break
        self.finished.emit()

    def _process_event(self, event_type, data):
        handler = {
            'exec_started': self._handle_node_execution_started,
            'exec_finished': self._handle_node_execution_finished,
            'log_msg': self._handle_log_msg,
            'process_msg': self._handle_process_msg,
            'standard_execution_msg': self._handle_standard_execution_msg,
            'kernel_execution_msg': self._handle_kernel_execution_msg,
        }.get(event_type)
        if handler is None:
            return
        handler(data)

    def _handle_standard_execution_msg(self, msg):
        if msg["type"] == "execution_failed_to_start":
            self._toolbox.msg_error.emit(f"Program <b>{msg['program']}</b> failed to start: {msg['error']}")
        elif msg["type"] == "execution_started":
            self._toolbox.msg.emit(f"\tStarting program <b>{msg['program']}</b>")
            self._toolbox.msg.emit(f"\tArguments: <b>{msg['args']}</b>")
            self._toolbox.msg_warning.emit(
                "\tExecution is in progress. See Process Log for messages " "(stdout&stderr)"
            )

    def _handle_kernel_execution_msg(self, msg):
        language = msg["language"].capitalize()
        if msg["type"] == "kernel_started":
            console = {"julia": self._toolbox.julia_repl, "python": self._toolbox.python_repl}.get(msg["language"])
            if console is not None:
                console.connect_to_kernel(msg["kernel_name"], msg["connection_file"])
        elif msg["type"] == "kernel_spec_not_found":
            self._toolbox.msg_error.emit(
                f"\tUnable to find specification for {language} kernel <b>{msg['kernel_name']}</b>. "
                f"Go to Settings->Tools to select a valid {language} kernel."
            )
        elif msg["type"] == "execution_failed_to_start":
            self._toolbox.msg_error.emit(
                f"\tExecution on {language} kernel <b>{msg['kernel_name']}</b> failed to start: {msg['error']} "
            )
        elif msg["type"] == "execution_started":
            self._toolbox.msg.emit(f"\tStarting program on {language} kernel <b>{msg['kernel_name']}</b>")
            self._toolbox.msg_warning.emit(f"See {language} Console for messages.")

    def _handle_process_msg(self, data):
        self._do_handle_process_msg(**data)

    def _do_handle_process_msg(self, author, msg_type, msg_text):
        item = self._project_items[author]
        self._process_message_arrived.emit(item, msg_type, msg_text)

    def _handle_log_msg(self, data):
        self._do_handle_log_msg(**data)

    def _do_handle_log_msg(self, author, msg_type, msg_text):
        item = self._project_items[author]
        self._log_message_arrived.emit(item, msg_type, msg_text)

    def _handle_node_execution_started(self, data):
        self._do_handle_node_execution_started(**data)

    def _do_handle_node_execution_started(self, item_name, direction):
        """Starts item icon animation when executing forward."""
        item = self._project_items[item_name]
        self._executing_items.append(item)
        self._node_execution_started.emit(item, direction)

    def _handle_node_execution_finished(self, data):
        self._do_handle_node_execution_finished(**data)

    def _do_handle_node_execution_finished(self, item_name, direction, state, success):
        item = self._project_items[item_name]
        if success:
            self.sucessful_executions.append((item, direction, state))
        self._executing_items.remove(item)
        self._node_execution_finished.emit(item, direction, state, success)

    def clean_up(self):
        for item in self._executing_items:
            self._node_execution_finished.emit(item, None, None, False)
        self._thread.quit()
        self._thread.wait()
