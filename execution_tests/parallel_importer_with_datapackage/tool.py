import csv
import sys
from spinedb_api import DatabaseMapping, from_database

url = sys.argv[1]
db_map = DatabaseMapping(url)
try:
    value_row = db_map.query(db_map.object_parameter_value_sq).first()
    value = from_database(value_row.value, value_row.type)
finally:
    db_map.connection.close()
with open("out.csv", "w", newline="") as out_file:
    out_writer = csv.writer(out_file)
    out_writer.writerow(["final_value"])
    out_writer.writerow([value])
