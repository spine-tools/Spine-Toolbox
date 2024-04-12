######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Engine is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Tests for Remote Spine Engine Manager."""
import unittest
from unittest import mock
from spinetoolbox.spine_engine_manager import RemoteSpineEngineManager
from spine_engine import ItemExecutionFinishState
from spine_engine.server.util.event_data_converter import EventDataConverter


class TestRemoteSpineEngineManager(unittest.TestCase):
    def test_remote_engine_manager_execution_fails(self):
        """Test that engine manager does not crash when DAG execution fails on server."""
        event_yielder = self.yield_events_dag_fails()
        attribs = {
            "start_execution.return_value": ("remote_execution_started", "12345", "abcdefg123"),
            "rcv_next.side_effect": event_yielder,
        }
        self._run_engine(attribs)

    def test_remote_engine_manager_init_fails(self):
        """Test receiving error msg when start_execution request fails
        because project_dir is not found on server for some reason."""
        event_yielder = self.yield_events_dag_succeeds()
        attribs = {
            "start_execution.return_value": ("server_init_failed", "Couldn't find project dir."),
            "rcv_next.side_effect": event_yielder,
        }
        self._run_engine(attribs)

    def test_remote_engine_manager(self):
        event_yielder = self.yield_events_dag_succeeds()
        attribs = {
            "start_execution.return_value": ("remote_execution_started", "12345", "abcdefg123"),
            "rcv_next.side_effect": event_yielder,
        }
        self._run_engine(attribs)

    def _run_engine(self, attribs):
        remote_engine_mngr = RemoteSpineEngineManager()
        engine_data = {"settings": dict(), "project_dir": ""}
        # NOTE: This patch does not work without spec=True
        with mock.patch("spinetoolbox.spine_engine_manager.EngineClient", **attribs, spec=True) as mock_client:
            remote_engine_mngr.run_engine(engine_data)
            remote_engine_mngr.stop_engine()
            mock_client.assert_called()
            self.assertFalse(remote_engine_mngr._runner.is_alive())

    @staticmethod
    def yield_events_dag_succeeds():
        """Received event generator. Yields events that look like they were PULLed from server."""
        # Convert some events fresh from SpineEngine first into
        # (bytes) json strings to simulate events that arrive to EngineClient
        engine_events = [
            ("exec_started", {"item_name": "Data Connection 1", "direction": "BACKWARD"}),
            (
                "exec_finished",
                {
                    "item_name": "Data Connection 1",
                    "direction": "BACKWARD",
                    "state": "RUNNING",
                    "item_state": ItemExecutionFinishState.SUCCESS,
                },
            ),
            ("exec_started", {"item_name": "Data Connection 1", "direction": "FORWARD"}),
            (
                "event_msg",
                {
                    "item_name": "Data Connection 1",
                    "filter_id": "",
                    "msg_type": "msg_success",
                    "msg_text": "Executing Data Connection Data Connection 1 finished",
                },
            ),
            (
                "exec_finished",
                {
                    "item_name": "Data Connection 1",
                    "direction": "FORWARD",
                    "state": "RUNNING",
                    "item_state": ItemExecutionFinishState.SUCCESS,
                },
            ),
            ("dag_exec_finished", "COMPLETED"),
        ]
        rcv_events_list = list()
        for event_type, data in engine_events:
            json_event = EventDataConverter.convert(event_type, data)
            rcv_events_list.append([json_event.encode("utf-8")])
        for event in rcv_events_list:
            yield event

    @staticmethod
    def yield_events_dag_fails():
        """Received event generator. Yields events that look like they were PULLed from server."""
        engine_events = [
            ("exec_started", {"item_name": "Data Connection 1", "direction": "BACKWARD"}),
            (
                "exec_finished",
                {
                    "item_name": "Data Connection 1",
                    "direction": "BACKWARD",
                    "state": "RUNNING",
                    "item_state": ItemExecutionFinishState.FAILURE,
                },
            ),
            ("exec_started", {"item_name": "Data Connection 1", "direction": "FORWARD"}),
            (
                "event_msg",
                {
                    "item_name": "Data Connection 1",
                    "filter_id": "",
                    "msg_type": "msg_success",
                    "msg_text": "Executing Data Connection Data Connection 1 finished",
                },
            ),
            (
                "exec_finished",
                {
                    "item_name": "Data Connection 1",
                    "direction": "FORWARD",
                    "state": "RUNNING",
                    "item_state": ItemExecutionFinishState.FAILURE,
                },
            ),
            ("dag_exec_finished", "FAILED"),
        ]
        rcv_events_list = list()
        for event_type, data in engine_events:
            json_event = EventDataConverter.convert(event_type, data)
            rcv_events_list.append([json_event.encode("utf-8")])
        for event in rcv_events_list:
            yield event


if __name__ == "__main__":
    unittest.main()
