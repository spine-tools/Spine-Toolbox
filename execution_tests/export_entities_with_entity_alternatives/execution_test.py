import subprocess
import sys
from pathlib import Path
import shutil
import unittest

from spinedb_api import DatabaseMapping


class ExportEntitiesWithEntityAlternatives(unittest.TestCase):
    _root_path = Path(__file__).parent
    _database_path = _root_path / ".spinetoolbox" / "items" / "source" / "Source.sqlite"
    _exporter_output_path = _root_path / ".spinetoolbox" / "items" / "export_entities" / "output"

    def setUp(self):
        if self._exporter_output_path.exists():
            shutil.rmtree(self._exporter_output_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        if self._database_path.exists():
            self._database_path.unlink()
        url = "sqlite:///" + str(self._database_path)
        with DatabaseMapping(url, create=True) as db_map:
            self._assert_item_added(db_map.add_entity_class_item(name="Object", active_by_default=True))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="none_none"))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="true_none"))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="none_true"))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="true_true"))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="false_true"))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="true_false"))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="false_false"))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="none_false"))
            self._assert_item_added(db_map.add_entity_item(entity_class_name="Object", name="false_none"))
            self._assert_item_added(db_map.add_scenario_item(name="scenario"))
            self._assert_item_added(db_map.add_alternative_item(name="first"))
            self._assert_item_added(db_map.add_alternative_item(name="second"))
            self._assert_item_added(
                db_map.add_scenario_alternative_item(scenario_name="scenario", alternative_name="first", rank=0)
            )
            self._assert_item_added(
                db_map.add_scenario_alternative_item(scenario_name="scenario", alternative_name="second", rank=1)
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("true_none",), alternative_name="first", active=True
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("none_true",), alternative_name="second", active=True
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("true_true",), alternative_name="first", active=True
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("true_true",), alternative_name="second", active=True
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("false_true",), alternative_name="first", active=False
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("false_true",), alternative_name="second", active=True
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("true_false",), alternative_name="first", active=True
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("true_false",), alternative_name="second", active=False
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("false_false",), alternative_name="first", active=False
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("false_false",), alternative_name="second", active=False
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("none_false",), alternative_name="second", active=False
                )
            )
            self._assert_item_added(
                db_map.add_entity_alternative_item(
                    entity_class_name="Object", entity_byname=("false_none",), alternative_name="first", active=False
                )
            )
            db_map.commit_session("Add test data.")

    def _assert_item_added(self, result):
        self.assertIsNone(result[1])
        self.assertIsNotNone(result[0])

    def test_execution(self):
        this_file = Path(__file__)
        completed = subprocess.run((sys.executable, "-m", "spinetoolbox", "--execute-only", str(this_file.parent)))
        self.assertEqual(completed.returncode, 0)
        self.assertTrue(self._exporter_output_path.exists())
        self.assertEqual(len(list(self._exporter_output_path.iterdir())), 1)
        output_dir = next(iter(self._exporter_output_path.iterdir()))
        filter_id = (output_dir / ".filter_id").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(filter_id), 1)
        self.assertEqual(filter_id, ["scenario - Source"])
        entities = (output_dir / "entities.csv").read_text(encoding="utf-8").splitlines()
        expected = ["Object,none_none", "Object,none_true", "Object,true_none", "Object,true_true", "Object,false_true"]
        self.assertCountEqual(entities, expected)


if __name__ == '__main__':
    unittest.main()
