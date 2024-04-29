from spinedb_api import DatabaseMapping
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE

db_path = project.project_dir / ".spinetoolbox" / "items" / "data" / "Data.sqlite"
db_url = "sqlite:///" + str(db_path)
with DatabaseMapping(db_url) as db_map:
    scenario_ids = {r.name: r.id for r in db_map.query(db_map.scenario_sq).all()}
    connection = project.find_connection("Data", "Export values")
    connection.set_filter_enabled("db_url@Data", SCENARIO_FILTER_TYPE, "scenario", True)
