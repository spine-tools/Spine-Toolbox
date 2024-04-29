from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from spinedb_api import create_new_spine_database, DatabaseMapping, from_database, Map


class LoopConditionWithCmdLineArgs(unittest.TestCase):
    _root_path = Path(__file__).parent
    _loop_counter_database_path = _root_path / ".spinetoolbox" / "items" / "loop_counter_store" / "counter.sqlite"
    _output_database_path = _root_path / ".spinetoolbox" / "items" / "store" / "Store.sqlite"
    _tool_output_path = _root_path / ".spinetoolbox" / "items" / "write_data" / "output"

    def setUp(self):
        if self._tool_output_path.exists():
            shutil.rmtree(self._tool_output_path)
        self._loop_counter_database_url = "sqlite:///" + str(self._loop_counter_database_path)
        self._output_database_url = "sqlite:///" + str(self._output_database_path)
        for database_path, url in (
            (self._loop_counter_database_path, self._loop_counter_database_url),
            (self._output_database_path, self._output_database_url),
        ):
            database_path.parent.mkdir(parents=True, exist_ok=True)
            if database_path.exists():
                database_path.unlink()
            create_new_spine_database(url)

    def test_execution(self):
        completed = subprocess.run((sys.executable, "-m", "spinetoolbox", "--execute-only", str(self._root_path)))
        self.assertEqual(completed.returncode, 0)
        with DatabaseMapping(self._loop_counter_database_url) as db_map:
            value_rows = db_map.query(db_map.parameter_value_sq).all()
            self.assertEqual(len(value_rows), 1)
            loop_counter = from_database(value_rows[0].value, value_rows[0].type)
        self.assertEqual(loop_counter, 20.0)
        with DatabaseMapping(self._output_database_url) as db_map:
            value_rows = db_map.query(db_map.parameter_value_sq).all()
            self.assertEqual(len(value_rows), 1)
            output_value = from_database(value_rows[0].value, value_rows[0].type)
        expected_x = [f"T{i:03}" for i in range(31)]
        expected_y = [float(i) for i in range(31)]
        self.assertEqual(output_value, Map(expected_x, expected_y))


if __name__ == '__main__':
    unittest.main()
