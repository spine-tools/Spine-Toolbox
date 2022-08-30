import csv
import sys
from spinedb_api import DatabaseMapping, from_database

url = sys.argv[1]
db_map = DatabaseMapping(url)
sq = db_map.object_parameter_value_sq
count_row = db_map.query(sq).filter(
    sq.c.object_class_name == "Counter", sq.c.object_name == "loop_counter", sq.c.parameter_name == "count"
).first()
count = int(from_database(count_row.value, count_row.type))
db_map.connection.close()
data = [[f"T{i:03}", i] for i in range(count, count + 11)]

with open("data.csv", "w", newline="") as data_file:
    writer = csv.writer(data_file)
    writer.writerows(data)
