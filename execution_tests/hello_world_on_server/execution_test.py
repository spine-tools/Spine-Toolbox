import sys
from pathlib import Path
import shutil
import subprocess
import unittest
import zmq
from spine_engine.server.engine_server import EngineServer, ServerSecurityModel


class RunHelloWorldOnServer(unittest.TestCase):
    _root_path = Path(__file__).parent
    _tool_script_path = _root_path / "simple_script."
    _tool_output_path = _root_path / ".spinetoolbox" / "items" / "simple_tool" / "output"

    def setUp(self):
        if self._tool_output_path.exists():
            shutil.rmtree(self._tool_output_path)

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


if __name__ == '__main__':
    unittest.main()
