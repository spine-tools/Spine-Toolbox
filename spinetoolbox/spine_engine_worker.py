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


class SpineEngineWorker(QObject):

    finished = Signal()
    _dag_node_execution_started = Signal(str, object)
    _dag_node_execution_finished = Signal(str, object, object)

    def __init__(self, engine, toolbox):
        """
        Args:
            engine (SpineEngine): engine to run
        """
        super().__init__()
        self._engine = engine
        self._toolbox = toolbox
        self._executing_item_name = None
        self._engine.publisher.register('exec_started', self, self._handle_dag_node_execution_started)
        self._engine.publisher.register('exec_finished', self, self._handle_dag_node_execution_finished)
        self._engine.publisher.register('msg', self, self._handle_msg)
        self._engine.publisher.register('msg_standard_execution', self, self._handle_msg_standard_execution)
        self._engine.publisher.register('msg_kernel_execution', self, self._handle_msg_kernel_execution)
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self.do_work)
        self._dag_node_execution_started.connect(self._toolbox.ui.graphicsView._start_animation)
        self._dag_node_execution_finished.connect(self._toolbox.ui.graphicsView._stop_animation)
        self._dag_node_execution_finished.connect(self._toolbox.ui.graphicsView._run_leave_animation)

    def _handle_msg_standard_execution(self, msg):
        if msg["type"] == "execution_failed_to_start":
            self._toolbox.msg_error.emit(f"Program <b>{msg['program']}</b> failed to start: {msg['error']}")
        elif msg["type"] == "execution_started":
            self._toolbox.msg.emit(f"\tStarting program <b>{msg['program']}</b>")
            self._toolbox.msg.emit(f"\tArguments: <b>{msg['args']}</b>")
            self._toolbox.msg_warning.emit(
                "\tExecution is in progress. See Process Log for messages " "(stdout&stderr)"
            )

    def _handle_msg_kernel_execution(self, msg):
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

    def _handle_msg(self, data):
        self._do_handle_msg(**data)

    def _do_handle_msg(self, msg_type, msg_text):
        getattr(self._toolbox, msg_type).emit(msg_text)

    def _handle_dag_node_execution_started(self, data):
        self._do_handle_dag_node_execution_started(**data)

    def _do_handle_dag_node_execution_started(self, item_name, direction):
        """Starts item icon animation when executing forward."""
        self._executing_item_name = item_name
        self._dag_node_execution_started.emit(item_name, direction)

    def _handle_dag_node_execution_finished(self, data):
        self._do_handle_dag_node_execution_finished(**data)

    def _do_handle_dag_node_execution_finished(self, item_name, direction, state):
        self._dag_node_execution_finished.emit(item_name, direction, state)
        item = self._toolbox.project_item_model.get_item(item_name)
        if item is None:
            return
        item.project_item.item_executed.emit(direction, state)

    def thread(self):
        return self._thread

    def start(self):
        self._thread.start()

    @Slot()
    def do_work(self):
        """Does the work and emits finished when done."""
        self._engine.run()
        self.finished.emit()

    def clean_up(self):
        if self._executing_item_name:
            self._dag_node_execution_finished.emit(self._executing_item_name, None, None)
        self._engine.publisher.unregister('exec_started', self)
        self._engine.publisher.unregister('exec_finished', self)
        self._engine.publisher.unregister('msg', self)
        self._engine.publisher.unregister('msg_standard_execution', self)
        self._engine.publisher.unregister('msg_kernel_execution', self)
        self._thread.quit()
        self._thread.wait()
        self.deleteLater()
