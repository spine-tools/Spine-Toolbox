import csv
import sys
from pathlib import Path
import shutil
import subprocess
import unittest
from spinedb_api import (
    DatabaseMapping,
    import_alternatives,
    import_entities,
    import_entity_alternatives,
    import_entity_classes,
    import_parameter_definitions,
    import_parameter_values,
    import_scenario_alternatives,
    import_scenarios,
)


class ModifyConnectionFilterByScript(unittest.TestCase):
    _root_path = Path(__file__).parent
    _mod_script_path = _root_path / "mod.py"
    _database_path = _root_path / ".spinetoolbox" / "items" / "data" / "Data.sqlite"
    _exporter_output_path = _root_path / ".spinetoolbox" / "items" / "export_values" / "output"

    def setUp(self):
        if self._exporter_output_path.exists():
            shutil.rmtree(self._exporter_output_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        if self._database_path.exists():
            self._database_path.unlink()
        url = "sqlite:///" + str(self._database_path)
        with DatabaseMapping(url, create=True) as db_map:
            import_entity_classes(db_map, (("object_class",),))
            import_entities(db_map, (("object_class", "object"),))
            import_parameter_definitions(db_map, (("object_class", "parameter"),))
            import_alternatives(db_map, ("alternative",))
            import_entity_alternatives(db_map, (("object_class", "object", "alternative", True),))
            import_parameter_values(
                db_map,
                (
                    ("object_class", "object", "parameter", 1.0, "Base"),
                    ("object_class", "object", "parameter", 2.0, "alternative"),
                ),
            )
            import_scenarios(db_map, (("scenario", True),))
            import_scenario_alternatives(db_map, (("scenario", "alternative"),))
            db_map.commit_session("Add test data.")

    def test_execution(self):
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "spinetoolbox",
                "--mod-script",
                str(self._mod_script_path),
                "--execute-only",
                str(self._root_path),
            )
        )
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(self._exporter_output_path.exists())
        out_dirs = list(self._exporter_output_path.iterdir())
        self.assertEqual(len(out_dirs), 1)
        out_dir = out_dirs[0]
        filter_id = self._read_filter_id(out_dir)
        if filter_id == "scenario - Data":
            self._check_out_file(out_dir, [["alternative", "2.0"]])
        else:
            self.fail("Unexpected filter id in Export value's output directory.")

    def _check_out_file(self, path, expected_file_contests):
        out_path = path / "out.csv"
        self.assertTrue(out_path.exists())
        with open(out_path, encoding="utf-8") as out_file:
            reader = csv.reader(out_file)
            contents = [r for r in reader]
        self.assertEqual(contents, expected_file_contests)

    @staticmethod
    def _read_filter_id(path):
        with (path / ".filter_id").open() as filter_id_file:
            return filter_id_file.readline().strip()


if __name__ == '__main__':
    unittest.main()
