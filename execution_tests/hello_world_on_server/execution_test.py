import os
import sys
from pathlib import Path
import shutil
import subprocess
import unittest
import zmq
from spinetoolbox.config import PROJECT_ZIP_FILENAME
from spine_items.tool.utils import find_last_output_files
from spine_engine.server.engine_server import EngineServer, ServerSecurityModel


class RunHelloWorldOnServer(unittest.TestCase):
    _root_path = Path(__file__).parent
    _tool_output_path = _root_path / ".spinetoolbox" / "items" / "simple_tool" / "output"
    _output_fname = "output_file.txt"
    _output_fpath = _root_path / _output_fname
    _zip_fname = PROJECT_ZIP_FILENAME + ".zip"
    _zip_fpath = _root_path.parent / _zip_fname
    _server_secfolder_path = _root_path / "server_secfolder"

    def setUp(self):
        test_name = self.id().split(".")[-1]
        if test_name == "test_execution_with_stonehouse_security":
            self.service = EngineServer("tcp", 50002, ServerSecurityModel.STONEHOUSE, str(self._server_secfolder_path))
        else:
            self.service = EngineServer("tcp", 50002, ServerSecurityModel.NONE, "")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.identity = "Worker1".encode("ascii")
        self.socket.connect("tcp://localhost:50002")
        self.pull_socket = self.context.socket(zmq.PULL)
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.poller.register(self.pull_socket, zmq.POLLIN)

    def tearDown(self):
        self.service.close()
        if not self.socket.closed:
            self.socket.close()
        if not self.pull_socket.closed:
            self.pull_socket.close()
        if not self.context.closed:
            self.context.term()
        if self._zip_fpath.exists():
            os.remove(self._zip_fpath)
        if self._output_fpath.exists():
            os.remove(self._output_fpath)
        if self._tool_output_path.exists():
            shutil.rmtree(self._tool_output_path)

    def test_execution(self):
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "spinetoolbox",
                "--execute-only",
                "--execute-remotely",
                "server.cfg",
                str(self._root_path),
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.check_output_file_contents()

    def test_execution_with_stonehouse_security(self):
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "spinetoolbox",
                "--execute-only",
                "--execute-remotely",
                "server_secure.cfg",
                str(self._root_path),
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.check_output_file_contents()

    def check_output_file_contents(self):
        """Finds the directory where the output file has been downloaded from the server and checks the contents."""
        a = find_last_output_files([self._output_fname], str(self._tool_output_path))
        output_fpath = a[self._output_fname][0]
        with open(output_fpath) as ofile:
            lines = ofile.readlines()
        text = ""
        for l in lines:
            text += l.strip() + " "
        text = text.strip()
        self.assertEqual("Hello! World!", text)


if __name__ == '__main__':
    unittest.main()
