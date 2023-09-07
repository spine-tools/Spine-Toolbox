import csv
import sys
from spinedb_api import DatabaseMapping, from_database

url = sys.argv[1]
with DatabaseMapping(url) as db_map:
    sq = db_map.entity_parameter_value_sq
    count_row = (
        db_map.query(sq)
        .filter(sq.c.entity_class_name == "Counter", sq.c.entity_name == "loop_counter", sq.c.parameter_name == "count")
        .first()
    )
count = int(from_database(count_row.value, count_row.type))
data = [[f"T{i:03}", i] for i in range(count, count + 11)]

with open("data.csv", "w", newline="") as data_file:
    writer = csv.writer(data_file)
    writer.writerows(data)
