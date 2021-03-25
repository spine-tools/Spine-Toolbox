from pathlib import Path
import shutil
import subprocess
import unittest
from spinedb_api import DiffDatabaseMapping, import_alternatives, import_scenario_alternatives, import_scenarios


class ScenarioFilters(unittest.TestCase):
    _root_path = Path(__file__).parent
    _database_path = _root_path / ".spinetoolbox" / "items" / "data_store" / "database.sqlite"
    _tool_output_path = _root_path / ".spinetoolbox" / "items" / "output_writer" / "output"

    def setUp(self):
        if self._tool_output_path.exists():
            shutil.rmtree(self._tool_output_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._database_path.unlink()
        url = "sqlite:///" + str(self._database_path)
        db_map = DiffDatabaseMapping(url, create=True)
        import_alternatives(db_map, ("alternative_1", "alternative_2"))
        import_scenarios(db_map, (("scenario_1", True), ("scenario_2", True)))
        import_scenario_alternatives(
            db_map, (("scenario_1", "alternative_1"), ("scenario_2", "alternative_2"))
        )
        db_map.commit_session("Add test data.")
        db_map.connection.close()

    def test_execution(self):
        this_file = Path(__file__)
        completed = subprocess.run(("python", "-m", "spinetoolbox", "--execute-only", str(this_file.parent)))
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(self._tool_output_path.exists())
        results_path = self._tool_output_path / "database.sqlite with scenario_1"
        self._check_out_file(results_path, ["-1.0"])
        results_path = self._tool_output_path / "database.sqlite with scenario_2"
        self._check_out_file(results_path, ["-2.0"])

    def _check_out_file(self, fork_path, expected_file_contests):
        self.assertTrue(fork_path.exists())
        out_path = next(fork_path.iterdir()) / "out.dat"
        self.assertTrue(out_path.exists())
        with open(out_path) as out_file:
            contents = out_file.readlines()
        self.assertEqual(contents, expected_file_contests)


if __name__ == '__main__':
    unittest.main()
