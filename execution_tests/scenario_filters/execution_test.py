import sys
from pathlib import Path
import shutil
import subprocess
import unittest
from spinedb_api import DatabaseMapping, import_alternatives, import_scenario_alternatives, import_scenarios


class ScenarioFilters(unittest.TestCase):
    _root_path = Path(__file__).parent
    _database_path = _root_path / ".spinetoolbox" / "items" / "data_store" / "database.sqlite"
    _tool_output_path = _root_path / ".spinetoolbox" / "items" / "output_writer" / "output"

    def setUp(self):
        if self._tool_output_path.exists():
            shutil.rmtree(self._tool_output_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        if self._database_path.exists():
            self._database_path.unlink()
        url = "sqlite:///" + str(self._database_path)
        with DatabaseMapping(url, create=True) as db_map:
            import_alternatives(db_map, ("alternative_1", "alternative_2"))
            import_scenarios(db_map, (("scenario_1", True), ("scenario_2", True)))
            import_scenario_alternatives(db_map, (("scenario_1", "alternative_1"), ("scenario_2", "alternative_2")))
            db_map.commit_session("Add test data.")

    def test_execution(self):
        this_file = Path(__file__)
        completed = subprocess.run((sys.executable, "-m", "spinetoolbox", "--execute-only", str(this_file.parent)))
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(self._tool_output_path.exists())
        self.assertEqual(len(list(self._tool_output_path.iterdir())), 2)
        scenario_1_checked = False
        scenario_2_checked = False
        for results_path in self._tool_output_path.iterdir():
            self.assertEqual(list(results_path.rglob("failed")), [])
            filter_id = self._read_filter_id(results_path)
            if filter_id == "scenario_1 - Data store":
                self.assertFalse(scenario_1_checked)
                self._check_out_file(results_path, ["-1.0"])
                scenario_1_checked = True
            elif filter_id == "scenario_2 - Data store":
                self.assertFalse(scenario_2_checked)
                self._check_out_file(results_path, ["-2.0"])
                scenario_2_checked = True
            else:
                self.fail("Unexpected filter id in Output Writer's output directory.")
        self.assertTrue(scenario_1_checked and scenario_2_checked)

    def _check_out_file(self, fork_path, expected_file_contests):
        for path in fork_path.iterdir():
            if path.is_dir():
                out_path = path / "out.dat"
                self.assertTrue(out_path.exists())
                with open(out_path) as out_file:
                    contents = out_file.readlines()
                self.assertEqual(contents, expected_file_contests)
                return
        self.fail("Could not find out.dat.")

    @staticmethod
    def _read_filter_id(path):
        with (path / ".filter_id").open() as filter_id_file:
            return filter_id_file.readline().strip()


if __name__ == '__main__':
    unittest.main()
