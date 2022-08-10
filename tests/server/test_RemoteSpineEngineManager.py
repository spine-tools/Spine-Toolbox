######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Engine is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Tests for Remote Spine Engine Manager.
:authors: P. Savolainen (VTT)
:date:   16.6.2022
"""

import unittest
from unittest import mock
from spinetoolbox.spine_engine_manager import RemoteSpineEngineManager, RemoteEngineEventGetter
from spinetoolbox.server.engine_client import EngineClientConnectionState
from spine_engine.spine_engine import ItemExecutionFinishState


class TestRemoteSpineEngineManager(unittest.TestCase):

    def test_remote_engine_manager_when_dag_execution_succeeds(self):
        # Mock return values for EngineClient methods
        attrs = {"get_connection_state.return_value": EngineClientConnectionState.CONNECTED,
                 "send.return_value": [("dag_exec_finished", "COMPLETED")]}
        self._run_remote_engine_manager(attrs, ("dag_exec_finished", "COMPLETED"))

    def test_remote_engine_manager_when_dag_execution_fails(self):
        attrs = {"get_connection_state.return_value": EngineClientConnectionState.CONNECTED,
                 "send.return_value": [("dag_exec_finished", "FAILED")]}
        self._run_remote_engine_manager(attrs, ("dag_exec_finished", "FAILED"))

    def test_remote_engine_manager_when_server_init_fails(self):
        attrs = {"get_connection_state.return_value": EngineClientConnectionState.CONNECTED,
                 "send.return_value": "Server init failed"}
        self._run_remote_engine_manager(attrs, ("remote_engine_failed", "Server init failed"))

    def _run_remote_engine_manager(self, attribs, expected_thing_at_output_q):
        remote_engine_mngr = RemoteSpineEngineManager()
        engine_data = {
            "settings": dict(),
            "project_dir": "",
        }
        # NOTE: This patch does not work without spec=True
        with mock.patch("spinetoolbox.spine_engine_manager.EngineClient", **attribs, spec=True) as mock_client:
            remote_engine_mngr.run_engine(engine_data)
            q_item = remote_engine_mngr.engine_event_getter_thread.q.get()
            self.assertEqual(expected_thing_at_output_q, q_item)  # Check that item to SpineEngineWorker is as expected
            remote_engine_mngr.close()
            mock_client.assert_called()
            self.assertFalse(remote_engine_mngr._runner.is_alive())
            self.assertFalse(remote_engine_mngr.engine_event_getter_thread.is_alive())

    def test_remote_engine_event_getter_parse_server_init_failed(self):
        ev_getter = RemoteEngineEventGetter()
        ev_getter.server_output_msg_q.put("Server failed at initialization")
        p = ev_getter.q.get()
        self.assertEqual("remote_engine_failed", p[0])
        self.assertEqual(p[1], "Server failed at initialization")

    def test_remote_engine_event_getter_parse_dag_exec_finished(self):
        ev_getter = RemoteEngineEventGetter()
        ev_getter.server_output_msg_q.put([("dag_exec_finished", "COMPLETED")])
        p = ev_getter.q.get()
        self.assertEqual("dag_exec_finished", p[0])
        self.assertEqual(p[1], "COMPLETED")

    def test_remote_engine_event_getter_parse_exec_started(self):
        ev_getter = RemoteEngineEventGetter()
        ev_getter.server_output_msg_q.put([('exec_started', "{'item_name': 'Data Connection 1', 'direction': 'FORWARD'}")])
        p = ev_getter.q.get()
        self.assertEqual("exec_started", p[0])
        self.assertTrue(isinstance(p[1], dict))
        self.assertTrue("item_name" and "direction" in p[1].keys())

    def test_remote_engine_event_getter_parse_event_msg1(self):
        ev_getter = RemoteEngineEventGetter()
        ev_getter.server_output_msg_q.put([('event_msg', "{'item_name': 'Data Connection 1', 'filter_id': '', 'msg_type': 'msg', 'msg_text': '***Executing Data Connection <b>Data Connection 1</b>***'}")])
        p = ev_getter.q.get()
        self.assertEqual("event_msg", p[0])
        self.assertTrue(isinstance(p[1], dict))
        self.assertTrue("item_name" and "filter_id" and "msg_type" and "msg_text" in p[1].keys())

    def test_remote_engine_event_getter_parse_event_msg2(self):
        # Parses event_msg where special chars are escaped. They are escaped when msg_text is HTML
        ev_getter = RemoteEngineEventGetter()
        ev_getter.server_output_msg_q.put([('event_msg', '{\'item_name\': \'helloworld\', \'filter_id\': \'\', \'msg_type\': \'msg_warning\', \'msg_text\': "\\tNo output files defined for this Tool specification. <a style=\'color:#99CCFF;\' title=\'When you add output files to the Tool specification,\\n they will be archived into results directory. Also, output files are passed to\\n subsequent project items.\' href=\'#\'>Tip</a>"}')])
        p = ev_getter.q.get()
        self.assertEqual("event_msg", p[0])
        self.assertTrue(isinstance(p[1], dict))
        self.assertTrue("item_name" and "filter_id" and "msg_type" and "msg_text" in p[1].keys())

    def test_remote_engine_event_getter_parse_exec_finished(self):
        ev_getter = RemoteEngineEventGetter()
        ev_getter.server_output_msg_q.put([('exec_finished', "{'item_name': 'Data Connection 1', 'direction': 'FORWARD', 'state': 'RUNNING', 'item_state': <ItemExecutionFinishState.SUCCESS: 1>}")])
        p = ev_getter.q.get()
        self.assertEqual("exec_finished", p[0])
        self.assertTrue(isinstance(p[1], dict))
        self.assertTrue("item_name" and "direction" and "state" and "item_state" in p[1].keys())
        self.assertTrue(isinstance(p[1]["item_state"], ItemExecutionFinishState))

    def test_remote_engine_event_getter_parse_persistent_execution_msg(self):
        ev_getter = RemoteEngineEventGetter()
        ev_getter.server_output_msg_q.put([('persistent_execution_msg', "{'item_name': 'helloworld', 'filter_id': '', 'type': 'persistent_started', 'key': ('C:\\\\Python38\\\\python.exe', 'helloworld'), 'language': 'python'}")])
        p = ev_getter.q.get()
        self.assertEqual("persistent_execution_msg", p[0])
        self.assertTrue(isinstance(p[1], dict))
        self.assertTrue("item_name" and "filter_id" and "type" and "key" and "language" in p[1].keys())

    def test_add_quotes_to_state_str(self):
        # Add quotes before < and after >
        s1 = "{'item_name': 'Data Connection 1', 'direction': 'FORWARD', 'state': 'RUNNING', 'item_state': <ItemExecutionFinishState.SUCCESS: 1>}"
        expected = "{'item_name': 'Data Connection 1', 'direction': 'FORWARD', 'state': 'RUNNING', 'item_state': '<ItemExecutionFinishState.SUCCESS: 1>'}"
        ret = RemoteEngineEventGetter._add_quotes_to_state_str(s1)
        self.assertEqual(expected, ret)
        # No < or > in string so the output should be the same as original
        s2 = "{'item_name': 'Data Connection 1', 'direction': 'FORWARD'}"
        ret = RemoteEngineEventGetter._add_quotes_to_state_str(s2)
        self.assertEqual(s2, ret)
        # Even though there are < and >, the output should be the same as original
        s3 = "{'item_name': 'Data Connection 1', 'filter_id': '', 'msg_type': 'msg', 'msg_text': '***Executing Data Connection <b>Data Connection 1</b>***'}"
        ret = RemoteEngineEventGetter._add_quotes_to_state_str(s3)
        self.assertEqual(s3, ret)
        # This should stay as the same as original as well
        s4 = '{\'item_name\': \'helloworld\', \'filter_id\': \'\', \'msg_type\': \'msg_warning\', \'msg_text\': "\\tNo output files defined for this Tool specification. <a style=\'color:#99CCFF;\' title=\'When you add output files to the Tool specification,\\n they will be archived into results directory. Also, output files are passed to\\n subsequent project items.\' href=\'#\'>Tip</a>"}'
        ret = RemoteEngineEventGetter._add_quotes_to_state_str(s4)
        self.assertEqual(s4, ret)


if __name__ == "__main__":
    unittest.main()
