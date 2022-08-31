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
from spinetoolbox.spine_engine_manager import RemoteSpineEngineManager


class TestRemoteSpineEngineManager(unittest.TestCase):

    def yield_event1(self):
        event_list = [(b'EVENTS', b'{"event_type": "exec_started", "data": "eydpdGVtX25hbWUnOiAnVDInLCAnZGlyZWN0aW9uJzogJ0JBQ0tXQVJEJ30="}'),
                      (b'EVENTS', b'{"event_type": "dag_exec_finished", "data": "Q09NUExFVEVE"}')]
        for event in event_list:
            yield event

    def yield_event2(self):
        """Test Data Store prompt event_type."""
        event_list = [(b'EVENTS', b'{"event_type": "prompt", "data": "eydpdGVtX25hbWUnOiAnRFMxJywgJ3R5cGUnOiAndXBncmFkZV9kYicsICd1cmwnOiBzcWxpdGU6Ly8vL2hvbWUvcGVra2EvZ2l0L1NQSU5FRU5HSU5FL3NwaW5lX2VuZ2luZS9zZXJ2ZXIvcmVjZWl2ZWRfcHJvamVjdHMvU2ltcGxlIEltcG9ydGVyX182ZmEwYjI5OTNhMzc0MWU1YjE2ZjJiZDlkMzU4YTlhOS8uc3BpbmV0b29sYm94L2l0ZW1zL2RzMS9EUzEuc3FsaXRlLCAnY3VycmVudCc6ICc5ODlmY2NmODA0NDEnLCAnZXhwZWN0ZWQnOiAnMWU0OTk3MTA1Mjg4J30="}'),
                      (b'EVENTS', b'{"event_type": "dag_exec_finished", "data": "Q09NUExFVEVE"}')]
        for event in event_list:
            yield event

        # prompt: {'item_name': 'DS1', 'type': 'upgrade_db',
        #          'url': sqlite: // // home / pekka / git / SPINEENGINE / spine_engine / server / received_projects / Simple
        # Importer__6fa0b2993a3741e5b16f2bd9d358a9a9 /.spinetoolbox / items / ds1 / DS1.sqlite, 'current': '989fccf80441', 'expected': '1e4997105288'}

    def test_remote_engine_manager_when_dag_execution_succeeds(self):
        # Mock return values for EngineClient methods
        event_yielder = self.yield_event1()
        attrs = {"start_execute.return_value": ("remote_execution_started", "12345"),
                 "connect_sub_socket.return_value": True,
                 "rcv_next_event.side_effect": event_yielder
                 }
        self._run_remote_engine_manager(attrs, ('exec_started', {'item_name': 'T2', 'direction': 'BACKWARD'}))

    def test_remote_engine_manager_ds_prompt_event_type_received(self):
        event_yielder = self.yield_event2()
        attrs = {"start_execute.return_value": ("remote_execution_started", "12345"),
                 "connect_sub_socket.return_value": True,
                 "rcv_next_event.side_effect": event_yielder
                 }
        self._run_remote_engine_manager(attrs, ('exec_started', {'item_name': 'T2', 'direction': 'BACKWARD'}))

    @unittest.skip("FixMe")
    def test_remote_engine_manager_when_dag_execution_fails(self):
        attrs = {"send.return_value": ("dag_exec_finished", "FAILED")}
        self._run_remote_engine_manager(attrs, ("dag_exec_finished", "FAILED"))

    @unittest.skip("FixMe")
    def test_remote_engine_manager_when_server_init_fails(self):
        attrs = {"send.return_value": ("remote_engine_failed", "Server init failed")}
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
            q_item = remote_engine_mngr.q.get()
            self.assertEqual(expected_thing_at_output_q, q_item)  # Check that item to SpineEngineWorker is as expected
            remote_engine_mngr.close()
            mock_client.assert_called()
            self.assertFalse(remote_engine_mngr._runner.is_alive())

    def test_add_quotes_to_state_str(self):
        """Adds quotes before < and after >."""
        s1 = "{'item_name': 'Data Connection 1', 'direction': 'FORWARD', 'state': 'RUNNING', 'item_state': <ItemExecutionFinishState.SUCCESS: 1>}"
        expected = "{'item_name': 'Data Connection 1', 'direction': 'FORWARD', 'state': 'RUNNING', 'item_state': '<ItemExecutionFinishState.SUCCESS: 1>'}"
        ret = RemoteSpineEngineManager._add_quotes_to_state_str(s1)
        self.assertEqual(expected, ret)
        # No < or > in string so the output should be the same as original
        s2 = "{'item_name': 'Data Connection 1', 'direction': 'FORWARD'}"
        ret = RemoteSpineEngineManager._add_quotes_to_state_str(s2)
        self.assertEqual(s2, ret)
        # Even though there are < and >, the output should be the same as original
        s3 = "{'item_name': 'Data Connection 1', 'filter_id': '', 'msg_type': 'msg', 'msg_text': '***Executing Data Connection <b>Data Connection 1</b>***'}"
        ret = RemoteSpineEngineManager._add_quotes_to_state_str(s3)
        self.assertEqual(s3, ret)
        # This should stay as the same as original as well
        s4 = '{\'item_name\': \'helloworld\', \'filter_id\': \'\', \'msg_type\': \'msg_warning\', \'msg_text\': "\\tNo output files defined for this Tool specification. <a style=\'color:#99CCFF;\' title=\'When you add output files to the Tool specification,\\n they will be archived into results directory. Also, output files are passed to\\n subsequent project items.\' href=\'#\'>Tip</a>"}'
        ret = RemoteSpineEngineManager._add_quotes_to_state_str(s4)
        self.assertEqual(s4, ret)


if __name__ == "__main__":
    unittest.main()
