import pathlib
import subprocess
import sys
from spinedb_api import DatabaseMapping


class TestRemovingDBItemsFromUpstreamTool:
    _root_path = pathlib.Path(__file__).parent
    _database_path = _root_path / ".spinetoolbox" / "items" / "data_store" / "Data Store.sqlite"

    def _set_up(self):
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        if self._database_path.exists():
            self._database_path.unlink()
        url = "sqlite:///" + str(self._database_path)
        with DatabaseMapping(url, create=True) as db_map:
            db_map.add_entity_class(name="Fish")
            db_map.add_entity(entity_class_name="Fish", name="gold_fish")
            db_map.add_parameter_definition(entity_class_name="Fish", name="buoyancy")
            db_map.add_parameter_value(
                entity_class_name="Fish",
                entity_byname=("gold_fish",),
                parameter_definition_name="buoyancy",
                alternative_name="Base",
                parsed_value=23.0,
            )
            db_map.commit_session("Add test data.")

    def test_no_orphan_records_are_left_in_the_database(self):
        self._set_up()
        this_file = pathlib.Path(__file__)
        completed = subprocess.run((sys.executable, "-m", "spinetoolbox", "--execute-only", str(this_file.parent)))
        assert completed.returncode == 0
