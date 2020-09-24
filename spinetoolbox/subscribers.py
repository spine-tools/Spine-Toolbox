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
Module contains subscriber classes that subscribe to the spine engine EventPublisher.
Each subscriber is created to handle a specific event in the engine.

:author: R. Brady (UCD)
:date:   21.9.2020
"""

from PySide2.QtCore import QObject, Signal


class NodeExecStartedSubscriber(QObject):
    """
     A subscriber class for the exec_started event which is a named event in the EventPublisher class of spine_engine.py
    """
    # Signal moved from SpineEngine
    dag_node_execution_started = Signal(str, "QVariant")
    """Emitted just before a named DAG node execution starts."""

    def __init__(self):
        super().__init__()

    def update(self, node_data):
        """
        emits dag_node_execution_started when the publisher dispatch method is called for the exec_started event
        Args:
             node_data (dict()): node_data passed from spine engine
             contains item_name (name of the solid which has started execution)
             and direction (current direction of the pipeline being executed)
        """
        self.dag_node_execution_started.emit(node_data['item_name'], node_data['direction'])


class NodeExecFinishedSubscriber(QObject):
    """
     A subscriber class for the exec_finished event which is a named event in the EventPublisher class of spine_engine.py
    """
    # Signal moved from SpineEngine
    dag_node_execution_finished = Signal(str, "QVariant", "QVariant")
    """Emitted after a named DAG node has finished execution."""

    def __init__(self):
        super().__init__()

    def update(self, node_data):
        """
        emits dag_node_execution_finished when the publisher dispatch method is called for the exec_finished event
        Args:
             node_data (dict()): node_data passed from spine engine
                contains:
                   item_name (name of the solid which has started execution),
                   direction (current direction of the pipeline being executed),
                   state (the state in which the node finished)
        """
        self.dag_node_execution_finished.emit(node_data['item_name'], node_data['direction'], node_data['state'])


class LoggingSubscriber(QObject):
    """
     A subscriber class for the log_event event which is a named event in the EventPublisher class of spine_engine.py
     A simple class to test logging a message originating from SpineEngine to a toolbox widget.
    """

    def __init__(self, logger):
        """
        Args:
            logger (LoggerInterface): logger instance passed from SpineToolboxProject.__init__()
        """
        super().__init__()
        self._logger = logger

    def update(self, log_msg):
        """
        emits a log message when the publisher dispatch method is called for the log_event event
        Args:
             log_msg (str): a message originating from SpineEngine
        """
        self._logger.msg.emit("This is a log message from spine engine: {}".format(log_msg))
