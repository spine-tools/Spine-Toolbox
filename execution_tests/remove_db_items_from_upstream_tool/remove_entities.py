import sys
from spinedb_api import DatabaseMapping

url = sys.argv[1]
with DatabaseMapping(url) as db_map:
    for entity in db_map.find_entities():
        entity.remove()
    db_map.commit_session("Removed entities.")
