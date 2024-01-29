from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from spinedb_api import DatabaseMapping, to_database


class AlternativeFilters(unittest.TestCase):
    _root_path = Path(__file__).parent
    _database_path = _root_path / ".spinetoolbox" / "items" / "data_store" / "Data Store.sqlite"
    _exporter_output_file_path = _root_path / ".spinetoolbox" / "items" / "exporter" / "output" / "out.dat"

    def _check_addition(self, result):
        error = result[1]
        self.assertIsNone(error)

    def setUp(self):
        if self._exporter_output_file_path.exists():
            shutil.rmtree(self._exporter_output_file_path.parent)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        if self._database_path.exists():
            self._database_path.unlink()
        url = "sqlite:///" + str(self._database_path)
        with DatabaseMapping(url, create=True) as db_map:
            self._check_addition(db_map.add_entity_class_item(name="Widget"))
            self._check_addition(db_map.add_entity_item(name="gadget", entity_class_name="Widget"))
            self._check_addition(db_map.add_parameter_definition_item(name="measurable", entity_class_name="Widget"))
            self._check_addition(db_map.add_alternative_item(name="alt1"))
            self._check_addition(db_map.add_alternative_item(name="alt2"))
            value, value_type = to_database(2.0)
            self._check_addition(
                db_map.add_parameter_value_item(
                    entity_class_name="Widget",
                    entity_byname=("gadget",),
                    parameter_definition_name="measurable",
                    alternative_name="Base",
                    value=value,
                    type=value_type,
                )
            )
            value, value_type = to_database(22.0)
            self._check_addition(
                db_map.add_parameter_value_item(
                    entity_class_name="Widget",
                    entity_byname=("gadget",),
                    parameter_definition_name="measurable",
                    alternative_name="alt1",
                    value=value,
                    type=value_type,
                )
            )
            value, value_type = to_database(222.0)
            self._check_addition(
                db_map.add_parameter_value_item(
                    entity_class_name="Widget",
                    entity_byname=("gadget",),
                    parameter_definition_name="measurable",
                    alternative_name="alt2",
                    value=value,
                    type=value_type,
                )
            )
            db_map.commit_session("Add test data.")

    def test_execution(self):
        this_file = Path(__file__)
        completed = subprocess.run((sys.executable, "-m", "spinetoolbox", "--execute-only", str(this_file.parent)))
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(self._exporter_output_file_path.exists())
        entities = self._exporter_output_file_path.read_text(encoding="utf-8").splitlines()
        expected = ["Widget,measurable,gadget,Base,2.0", "Widget,measurable,gadget,alt2,222.0"]
        self.assertCountEqual(entities, expected)


if __name__ == '__main__':
    unittest.main()
