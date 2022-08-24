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
from spinetoolbox.server.engine_client import EngineClientConnectionState
from spine_engine.spine_engine import ItemExecutionFinishState


class TestRemoteSpineEngineManager(unittest.TestCase):

    def test_remote_engine_manager_when_dag_execution_succeeds(self):
        # Mock return values for EngineClient methods
        attrs = {"get_connection_state.return_value": EngineClientConnectionState.CONNECTED,
                 "send.return_value": ("dag_exec_finished", "COMPLETED")}
        self._run_remote_engine_manager(attrs, ("dag_exec_finished", "COMPLETED"))

    def test_remote_engine_manager_when_dag_execution_fails(self):
        attrs = {"get_connection_state.return_value": EngineClientConnectionState.CONNECTED,
                 "send.return_value": ("dag_exec_finished", "FAILED")}
        self._run_remote_engine_manager(attrs, ("dag_exec_finished", "FAILED"))

    def test_remote_engine_manager_when_server_init_fails(self):
        attrs = {"get_connection_state.return_value": EngineClientConnectionState.CONNECTED,
                 "send.return_value": ("remote_engine_failed", "Server init failed")}
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
