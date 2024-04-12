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

"""Contains tests for the EngineClient class."""
import unittest
import os
from unittest import mock
from tempfile import TemporaryDirectory
from pathlib import Path
import zmq
from PySide6.QtWidgets import QApplication
from spinetoolbox.server.engine_client import EngineClient, ClientSecurityModel
from spine_engine.server.engine_server import EngineServer, ServerSecurityModel
from spine_engine.execution_managers.persistent_execution_manager import PythonPersistentExecutionManager
from spine_engine.exception import RemoteEngineInitFailed
from tests.mock_helpers import create_toolboxui_with_project, clean_up_toolbox


client_sec_dir = os.path.join(str(Path(__file__).parent), "client_secfolder")
server_sec_dir = os.path.join(str(Path(__file__).parent), "server_secfolder")


def _security_folder_exists():
    """Security folder and allowEndpoints.txt must exist to test security."""
    return os.path.exists(client_sec_dir) and os.path.exists(server_sec_dir)


class TestEngineClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self.toolbox = create_toolboxui_with_project(self._temp_dir.name)
        self.project = self.toolbox.project()
        self.service = EngineServer("tcp", 5601, ServerSecurityModel.NONE, "")
        self.context = zmq.Context()

    def tearDown(self):
        if self.service is not None:
            self.service.close()
        if not self.context.closed:
            self.context.term()
        self.project = None
        clean_up_toolbox(self.toolbox)
        self._temp_dir.cleanup()

    def test_engine_client_ping(self):
        client = EngineClient("localhost", 5601, ClientSecurityModel.NONE, "")
        self.assertFalse(client.dealer_socket.closed)
        self.assertFalse(client.pull_socket.closed)
        client.close()
        self.assertTrue(client.dealer_socket.closed)
        self.assertTrue(client.pull_socket.closed)
        self.assertTrue(client._context.closed)

    @unittest.skipIf(not _security_folder_exists(), "Test requires a security folder")
    def test_engine_client_ping_with_security(self):
        self.service.close()
        self.service = None
        secure_server = EngineServer("tcp", 5700, ServerSecurityModel.STONEHOUSE, server_sec_dir)
        client = EngineClient("localhost", 5700, ClientSecurityModel.STONEHOUSE, client_sec_dir)
        self.assertFalse(client.dealer_socket.closed)
        self.assertFalse(client.pull_socket.closed)
        client.close()
        self.assertTrue(client.dealer_socket.closed)
        self.assertTrue(client.pull_socket.closed)
        self.assertTrue(client._context.closed)
        secure_server.close()

    def test_engine_client_ping_fails(self):
        with self.assertRaises(RemoteEngineInitFailed):
            EngineClient("localhost", 5602, ClientSecurityModel.NONE, "")  # Note: wrong port

    def test_multiple_engine_clients(self):
        client1 = EngineClient("localhost", 5601, ClientSecurityModel.NONE, "", ping=False)
        client2 = EngineClient("localhost", 5601, ClientSecurityModel.NONE, "", ping=False)
        client3 = EngineClient("localhost", 5601, ClientSecurityModel.NONE, "", ping=False)
        client1._check_connectivity(500)
        client2._check_connectivity(500)
        client3._check_connectivity(500)
        self.assertFalse(client1.dealer_socket.closed)
        self.assertFalse(client1.pull_socket.closed)
        self.assertFalse(client2.dealer_socket.closed)
        self.assertFalse(client2.pull_socket.closed)
        self.assertFalse(client3.dealer_socket.closed)
        self.assertFalse(client3.pull_socket.closed)
        client1.close()
        client2.close()
        client3.close()
        self.assertTrue(client1.dealer_socket.closed)
        self.assertTrue(client1.pull_socket.closed)
        self.assertTrue(client1._context.closed)
        self.assertTrue(client2.dealer_socket.closed)
        self.assertTrue(client2.pull_socket.closed)
        self.assertTrue(client2._context.closed)
        self.assertTrue(client3.dealer_socket.closed)
        self.assertTrue(client3.pull_socket.closed)
        self.assertTrue(client3._context.closed)

    def test_engine_client_send_issue_persistent_command(self):
        client = EngineClient("localhost", 5601, ClientSecurityModel.NONE, "")
        logger = mock.MagicMock()
        logger.msg_warning = mock.MagicMock()
        exec_mngr1 = PythonPersistentExecutionManager(
            logger, ["python"], [], "alias", kill_completed_processes=False, group_id="SomeGroup"
        )
        # Make exec_mngr live on the server, then send command from client to server for processing and check output
        self.service.persistent_exec_mngrs["123"] = exec_mngr1
        gener = client.send_issue_persistent_command("123", "print('hi')")
        n_stdin_msgs = 0
        n_stdout_msgs = 0
        n_msgs = 0
        for msg in gener:
            if msg["type"] == "stdin":
                n_stdin_msgs += 1
            elif msg["type"] == "stdout":
                n_stdout_msgs += 1
            n_msgs += 1
        self.assertEqual(1, n_stdin_msgs)
        self.assertEqual(1, n_stdout_msgs)
        self.assertEqual(2, n_msgs)
        client.close()

    def test_engine_client_send_is_complete(self):
        client = EngineClient("localhost", 5601, ClientSecurityModel.NONE, "")
        logger = mock.MagicMock()
        logger.msg_warning = mock.MagicMock()
        exec_mngr1 = PythonPersistentExecutionManager(
            logger, ["python"], [], "alias", kill_completed_processes=False, group_id="SomeGroup"
        )
        self.service.persistent_exec_mngrs["123"] = exec_mngr1
        should_be_true = client.send_is_complete("123", "print('hi')")
        self.assertTrue(should_be_true)
        should_be_false = client.send_is_complete("123", "if True:")
        self.assertFalse(should_be_false)
        client.close()

    @mock.patch(
        "spine_engine.server.project_extractor_service.ProjectExtractorService.INTERNAL_PROJECT_DIR",
        new_callable=mock.PropertyMock,
    )
    def test_upload_project(self, mock_proj_dir):
        mock_proj_dir.return_value = self._temp_dir.name
        project_zip_fpath = os.path.join(str(Path(__file__).parent), "helloworld.zip")
        client = EngineClient("localhost", 5601, ClientSecurityModel.NONE, "")
        job_id = client.upload_project("Hello World", project_zip_fpath)
        self.assertTrue(isinstance(job_id, str))
        self.assertTrue(len(job_id) == 32)
        client.close()

    def test_remove_project_from_server(self):
        project_zip_fpath = os.path.join(str(Path(__file__).parent), "helloworld.zip")
        client = EngineClient("localhost", 5601, ClientSecurityModel.NONE, "")
        job_id = client.upload_project("Hello World", project_zip_fpath)
        self.assertTrue(isinstance(job_id, str))
        self.assertTrue(len(job_id) == 32)
        client.remove_project_from_server(job_id)
        client.close()


if __name__ == "__main__":
    unittest.main()
