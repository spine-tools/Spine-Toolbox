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
from .subscribers import NodeExecStartedSubscriber, NodeExecFinishedSubscriber


class SpineEngineWorker(QObject):

    finished = Signal()
    msg = Signal(str)
    msg_success = Signal(str)
    msg_warning = Signal(str)
    msg_error = Signal(str)
    msg_proc = Signal(str)
    msg_proc_error = Signal(str)

    def __init__(self, engine, project_item_model, design_view, logger):
        """
        Args:
            engine (SpineEngine): engine to run
        """
        super().__init__()
        self._engine = engine
        self._project_item_model = project_item_model
        self._design_view = design_view
        self._logger = logger
        self._start_subscriber = NodeExecStartedSubscriber()
        self._finish_subscriber = NodeExecFinishedSubscriber()
        self._engine.publisher.register('exec_started', self._start_subscriber)
        self._engine.publisher.register('exec_finished', self._finish_subscriber)
        self._engine.publisher.register('msg', self, self.msg.emit)
        self._engine.publisher.register('msg_success', self, self.msg_success.emit)
        self._engine.publisher.register('msg_warning', self, self.msg_warning.emit)
        self._engine.publisher.register('msg_error', self, self.msg_error.emit)
        self._engine.publisher.register('msg_proc', self, self.msg_proc.emit)
        self._engine.publisher.register('msg_proc_error', self, self.msg_proc_error.emit)
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._start_subscriber.moveToThread(self._thread)
        self._finish_subscriber.moveToThread(self._thread)
        self._thread.started.connect(self.do_work)
        self._start_subscriber.dag_node_execution_started.connect(self._handle_dag_node_execution_started)
        self._finish_subscriber.dag_node_execution_finished.connect(self._handle_dag_node_execution_finished)
        self.msg.connect(self._logger.msg)
        self.msg_success.connect(self._logger.msg_success)
        self.msg_warning.connect(self._logger.msg_warning)
        self.msg_error.connect(self._logger.msg_error)
        self.msg_proc.connect(self._logger.msg_proc)
        self.msg_proc_error.connect(self._logger.msg_proc_error)

    @Slot(str, object)
    def _handle_dag_node_execution_started(self, item_name, direction):
        """Starts item icon animation when executing forward."""
        self._design_view._start_animation(item_name, direction)

    @Slot(str, object, object)
    def _handle_dag_node_execution_finished(self, item_name, execution_direction, engine_state):
        self._design_view._stop_animation(item_name, execution_direction, None)
        self._design_view._run_leave_animation(item_name, execution_direction, engine_state)
        item = self._project_item_model.get_item(item_name)
        if item is None:
            return
        item.project_item.item_executed.emit(execution_direction, engine_state)

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
        self._engine.publisher.unregister('exec_started', self._start_subscriber)
        self._engine.publisher.unregister('exec_finished', self._finish_subscriber)
        self._engine.publisher.unregister('msg', self)
        self._engine.publisher.unregister('msg_success', self)
        self._engine.publisher.unregister('msg_warning', self)
        self._engine.publisher.unregister('msg_error', self)
        self._engine.publisher.unregister('msg_proc', self)
        self._engine.publisher.unregister('msg_proc_error', self)
        self._thread.quit()
        self._thread.wait()
        self.deleteLater()
        self._start_subscriber.deleteLater()
        self._finish_subscriber.deleteLater()
