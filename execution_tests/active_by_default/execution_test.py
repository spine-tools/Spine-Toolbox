from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from spinedb_api import DatabaseMapping

class ActiveByDefault(unittest.TestCase):
    _root_path = Path(__file__).parent
    _database_path = _root_path / "Test data.sqlite"
    _exporter_output_path = _root_path / ".spinetoolbox" / "items" / "exporter" / "output"

    def _check_addition(self, result):
        error = result[1]
        self.assertIsNone(error)

    def setUp(self):
        if self._exporter_output_path.exists():
            shutil.rmtree(self._exporter_output_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        if self._database_path.exists():
            self._database_path.unlink()
        url = "sqlite:///" + str(self._database_path)
        with DatabaseMapping(url, create=True) as db_map:
            self._check_addition(db_map.add_entity_class_item(name="HiddenByDefault", active_by_default=False))
            self._check_addition(db_map.add_entity_item(name="hidden", entity_class_name="HiddenByDefault"))
            self._check_addition(db_map.add_entity_class_item(name="VisibleByDefault", active_by_default=True))
            self._check_addition(db_map.add_entity_item(name="visible", entity_class_name="VisibleByDefault"))
            self._check_addition(db_map.add_scenario_item(name="base_scenario"))
            self._check_addition(db_map.add_scenario_alternative_item(scenario_name="base_scenario", alternative_name="Base", rank=0))
            db_map.commit_session("Add test data.")

    def test_execution(self):
        this_file = Path(__file__)
        completed = subprocess.run((sys.executable, "-m", "spinetoolbox", "--execute-only", str(this_file.parent)))
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(self._exporter_output_path.exists())
        self.assertEqual(len(list(self._exporter_output_path.iterdir())), 1)
        output_dir = next(iter(self._exporter_output_path.iterdir()))
        filter_id = (output_dir / ".filter_id").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(filter_id), 1)
        self.assertEqual(filter_id, ["base_scenario - Test data"])
        entities = (output_dir / "data.csv").read_text(encoding="utf-8").splitlines()
        expected = ["VisibleByDefault,visible"]
        self.assertCountEqual(entities, expected)


if __name__ == '__main__':
    unittest.main()
