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
Unit tests for Subscriber classes.

:author: R. Brady (UCD)
:date:   21.9.2020
"""

import unittest

from PySide2.QtCore import Slot
from spine_engine import ExecutionDirection, SpineEngineState

from spinetoolbox.subscribers import NodeExecFinishedSubscriber, NodeExecStartedSubscriber, LoggingSubscriber


class TestSubscribers(unittest.TestCase):
    _started_name = None
    _started_direction = None
    _finished_name = None
    _finished_direction = None
    _finished_state = None

    @Slot(str, "QVariant")
    def exec_started_test_slot(self, item_name, direction):
        self._started_name = item_name
        self._started_direction = direction

    @Slot(str, "QVariant", "QVariant")
    def exec_finished_test_slot(self, item_name, direction, state):
        self._finished_name = item_name
        self._finished_direction = direction
        self._finished_state = state

    def setUp(self):
        self.exec_started_subscriber = NodeExecStartedSubscriber()
        self.exec_finished_subscriber = NodeExecFinishedSubscriber()
        self.exec_started_subscriber.dag_node_execution_started.connect(self.exec_started_test_slot)
        self.exec_finished_subscriber.dag_node_execution_finished.connect(self.exec_finished_test_slot)

    def tearDown(self):
        self.exec_started_subscriber.dag_node_execution_started.disconnect(self.exec_started_test_slot)
        self.exec_finished_subscriber.dag_node_execution_finished.disconnect(self.exec_finished_test_slot)

    def test_exec_started_update(self):
        self.assertIsNone(self._started_name)
        self.assertIsNone(self._started_direction)
        node_data = {"item_name": "test_started", "direction": ExecutionDirection.BACKWARD}
        self.exec_started_subscriber.update(node_data)
        self.assertEqual(self._started_name, "test_started")
        self.assertEqual(self._started_direction, ExecutionDirection.BACKWARD)

    def test_exec_finished_update(self):
        self.assertIsNone(self._finished_name)
        self.assertIsNone(self._finished_direction)
        self.assertIsNone(self._finished_state)
        node_data = {"item_name": "test_finished", "direction": ExecutionDirection.BACKWARD,
                     "state": SpineEngineState.COMPLETED}
        self.exec_finished_subscriber.update(node_data)
        self.assertEqual(self._finished_name, "test_finished")
        self.assertEqual(self._finished_direction, ExecutionDirection.BACKWARD)
        self.assertEqual(self._finished_state, SpineEngineState.COMPLETED)
