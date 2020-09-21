import unittest

from PySide2.QtCore import Slot
from spine_engine import ExecutionDirection, SpineEngineState

from spinetoolbox.subscribers import NodeExecFinishedSubscriber, NodeExecStartedSubscriber, LoggingSubscriber

"""
Unit tests for Subscriber classes.

:author: R. Brady (UCD)
:date:   21.9.2020
"""


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
