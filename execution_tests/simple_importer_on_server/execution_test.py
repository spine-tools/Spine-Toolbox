import os
import sys
from pathlib import Path
import subprocess
import unittest
import zmq
from spinetoolbox.config import PROJECT_ZIP_FILENAME
from spine_engine.server.engine_server import EngineServer, ServerSecurityModel
from spinedb_api import create_new_spine_database, DatabaseMapping


class RunSimpleImporterOnServer(unittest.TestCase):
    _root_path = Path(__file__).parent
    _db_path = _root_path / ".spinetoolbox" / "items" / "ds1" / "DS1.sqlite"
    _zip_fname = PROJECT_ZIP_FILENAME + ".zip"
    _zip_fpath = _root_path.parent / _zip_fname

    def setUp(self):
        self.service = EngineServer("tcp", 50003, ServerSecurityModel.NONE, "")
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.identity = "Worker1".encode("ascii")
        self.socket.connect("tcp://localhost:50003")
        self.pull_socket = self.context.socket(zmq.PULL)
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.poller.register(self.pull_socket, zmq.POLLIN)
        self.make_db_for_ds1(self._db_path)

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

    def make_db_for_ds1(self, p):
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        if self._db_path.exists():
            self._db_path.unlink()
        self._db_url = "sqlite:///" + str(self._db_path)
        create_new_spine_database(self._db_url)

    def test_execution(self):
        # Check that DS1.sqlite is empty
        with DatabaseMapping(self._db_url) as db_map:
            entities = db_map.get_items("entity")
            self.assertEqual(0, len(entities))
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
        # Check that entities are now in DB
        with DatabaseMapping(self._db_url) as db_map:
            entities = db_map.get_items("entity")
            self.assertEqual(3, len(entities))
            for entity in entities:
                if entity["id"].db_id == 1:
                    self.assertEqual("Factory1", entity["name"])
                elif entity["id"].db_id == 2:
                    self.assertEqual("Factory2", entity["name"])
                elif entity["id"].db_id == 3:
                    self.assertEqual("Factory3", entity["name"])
                else:
                    self.fail()


if __name__ == '__main__':
    unittest.main()
