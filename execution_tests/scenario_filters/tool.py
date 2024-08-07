import sys
from spinedb_api import DatabaseMapping, from_database

url = sys.argv[1]
with DatabaseMapping(url) as db_map:
    value_row = db_map.query(db_map.parameter_value_sq).first()
    parameter_value = from_database(value_row.value, value_row.type)
with open("out.dat", "w") as out_file:
    out_file.write(f"{parameter_value}")
