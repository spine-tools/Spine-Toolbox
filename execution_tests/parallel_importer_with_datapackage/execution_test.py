import sys
from pathlib import Path
import shutil
import subprocess
import unittest
from spinedb_api import (
    create_new_spine_database,
    DatabaseMapping,
    from_database,
    import_alternatives,
    import_entities,
    import_entity_classes,
    import_parameter_definitions,
    import_parameter_values,
    import_scenario_alternatives,
    import_scenarios,
)


class ParallelImporterWithDatapackage(unittest.TestCase):
    _root_path = Path(__file__).parent
    _source_database_path = _root_path / ".spinetoolbox" / "items" / "source" / "Source.sqlite"
    _sink_database_path = _root_path / ".spinetoolbox" / "items" / "sink" / "Sink.sqlite"
    _tool_output_path = _root_path / ".spinetoolbox" / "items" / "write_output" / "output"

    def setUp(self):
        if self._tool_output_path.exists():
            shutil.rmtree(self._tool_output_path)
        self._source_database_path.parent.mkdir(parents=True, exist_ok=True)
        if self._source_database_path.exists():
            self._source_database_path.unlink()
        url = "sqlite:///" + str(self._source_database_path)
        with DatabaseMapping(url, create=True) as db_map:
            import_alternatives(db_map, ("alternative_1", "alternative_2"))
            import_scenarios(db_map, (("scenario_1", True), ("scenario_2", True)))
            import_scenario_alternatives(db_map, (("scenario_1", "alternative_1"), ("scenario_2", "alternative_2")))
            import_entity_classes(db_map, ("content",))
            import_entities(db_map, (("content", "test_data"),))
            import_parameter_definitions(db_map, (("content", "only_value"),))
            import_parameter_values(
                db_map,
                (
                    ("content", "test_data", "only_value", 11.0, "alternative_1"),
                    ("content", "test_data", "only_value", 22.0, "alternative_2"),
                ),
            )
            db_map.commit_session("Add test data.")
        self._sink_database_path.parent.mkdir(parents=True, exist_ok=True)
        if self._sink_database_path.exists():
            self._sink_database_path.unlink()
        self._sink_url = "sqlite:///" + str(self._sink_database_path)
        create_new_spine_database(self._sink_url)

    def test_execution(self):
        this_file = Path(__file__)
        completed = subprocess.run((sys.executable, "-m", "spinetoolbox", "--execute-only", str(this_file.parent)))
        self.assertEqual(completed.returncode, 0)
        with DatabaseMapping(self._sink_url) as db_map:
            value_rows = db_map.query(db_map.entity_parameter_value_sq).all()
        self.assertEqual(len(value_rows), 2)
        expected_common_data = {
            "entity_class_name": "result",
            "entity_name": "test_data",
            "parameter_name": "final_value",
        }
        scenario_1_checked = False
        scenario_2_checked = False
        for value_row in value_rows:
            for key, expected_value in expected_common_data.items():
                self.assertEqual(value_row[key], expected_value)
            value = from_database(value_row.value, value_row.type)
            if value == 11.0:
                self.assertTrue(value_row.alternative_name.startswith("scenario_1__Import@"))
                scenario_1_checked = True
            elif value == 22.0:
                self.assertTrue(value_row.alternative_name.startswith("scenario_2__Import@"))
                scenario_2_checked = True
        self.assertTrue(scenario_1_checked)
        self.assertTrue(scenario_2_checked)


if __name__ == '__main__':
    unittest.main()
