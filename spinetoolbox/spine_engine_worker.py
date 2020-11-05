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
from spine_engine import ExecutionDirection, SpineEngineState


class _SignalHandler(QObject):
    def __init__(self, toolbox):
        self._toolbox = toolbox
        self._project_items = {}

    @Slot(list)
    def _handle_dag_execution_started(self, item_names):
        self._project_items.clear()
        for item_name in item_names:
            item = self._toolbox.project_item_model.get_item(item_name)
            if item is None:
                continue
            self._project_items[item_name] = item.project_item
        for item in self._project_items.values():
            item.get_icon().execution_icon.mark_execution_wating()

    @Slot(str, object)
    def _handle_node_execution_started(self, item_name, direction):
        icon = self._project_items[item_name].get_icon()
        if direction == ExecutionDirection.FORWARD:
            icon.execution_icon.mark_execution_started()
            if hasattr(icon, "animation_signaller"):
                icon.animation_signaller.animation_started.emit()

    @Slot(str, object, object, bool)
    def _handle_node_execution_finished(self, item_name, direction, state, success):
        item = self._project_items[item_name]
        item.item_executed.emit(direction, state)
        icon = item.get_icon()
        if direction == ExecutionDirection.FORWARD:
            icon.execution_icon.mark_execution_finished(success)
            if hasattr(icon, "animation_signaller"):
                icon.animation_signaller.animation_stopped.emit()
            if state == SpineEngineState.RUNNING:
                icon.run_execution_leave_animation()

    @Slot(str, str, str)
    def _handle_log_message_arrived(self, item_name, msg_type, msg_text):
        self._project_items[item_name].get_icon().execution_icon.add_log_message(msg_type, msg_text)

    @Slot(str, str, str)
    def _handle_process_message_arrived(self, item_name, msg_type, msg_text):
        self._project_items[item_name].get_icon().execution_icon.add_process_message(msg_type, msg_text)


class SpineEngineWorker(QObject):

    finished = Signal()
    _dag_execution_started = Signal(list)
    _node_execution_started = Signal(str, object)
    _node_execution_finished = Signal(str, object, object, bool)
    _log_message_arrived = Signal(str, str, str)
    _process_message_arrived = Signal(str, str, str)

    def __init__(self, engine, dag_identifier, toolbox):
        """
        Args:
            engine (SpineEngine): engine to run
        """
        super().__init__()
        self.engine = engine
        self.dag_identifier = dag_identifier
        self._toolbox = toolbox
        self._executing_items = []
        self._signal_handler = _SignalHandler(toolbox)
        self.engine.publisher.register('exec_started', self, self._handle_node_execution_started)
        self.engine.publisher.register('exec_finished', self, self._handle_node_execution_finished)
        self.engine.publisher.register('log_msg', self, self._handle_log_msg)
        self.engine.publisher.register('process_msg', self, self._handle_process_msg)
        self.engine.publisher.register('standard_execution_msg', self, self._handle_standard_execution_msg)
        self.engine.publisher.register('kernel_execution_msg', self, self._handle_kernel_execution_msg)
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self.do_work)
        self._dag_execution_started.connect(self._signal_handler._handle_dag_execution_started)
        self._node_execution_started.connect(self._signal_handler._handle_node_execution_started)
        self._node_execution_finished.connect(self._signal_handler._handle_node_execution_finished)
        self._log_message_arrived.connect(self._signal_handler._handle_log_message_arrived)
        self._process_message_arrived.connect(self._signal_handler._handle_process_message_arrived)

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
        self._process_message_arrived.emit(author, msg_type, msg_text)

    def _handle_log_msg(self, data):
        self._do_handle_log_msg(**data)

    def _do_handle_log_msg(self, author, msg_type, msg_text):
        self._log_message_arrived.emit(author, msg_type, msg_text)

    def _handle_node_execution_started(self, data):
        self._do_handle_node_execution_started(**data)

    def _do_handle_node_execution_started(self, item_name, direction):
        """Starts item icon animation when executing forward."""
        self._executing_items.append(item_name)
        self._node_execution_started.emit(item_name, direction)

    def _handle_node_execution_finished(self, data):
        self._do_handle_node_execution_finished(**data)

    def _do_handle_node_execution_finished(self, item_name, direction, state, success):
        self._executing_items.remove(item_name)
        self._node_execution_finished.emit(item_name, direction, state, success)

    def thread(self):
        return self._thread

    def start(self):
        self._dag_execution_started.emit(list(self.engine.item_names))
        self._thread.start()

    @Slot()
    def do_work(self):
        """Does the work and emits finished when done."""
        self.engine.run()
        self.finished.emit()

    def clean_up(self):
        for item in self._executing_items:
            self._node_execution_finished.emit(item, None, None, False)
        self.engine.publisher.unregister('exec_started', self)
        self.engine.publisher.unregister('exec_finished', self)
        self.engine.publisher.unregister('log_msg', self)
        self.engine.publisher.unregister('process_msg', self)
        self.engine.publisher.unregister('standard_execution_msg', self)
        self.engine.publisher.unregister('kernel_execution_msg', self)
        self._thread.quit()
        self._thread.wait()
        self.deleteLater()
