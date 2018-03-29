using SpineData
using JSON

dc = JSON.parsefile("input/rawCSV.json")
path = dc["path"]

pkg_desc = infer(path)

set_primary_key!(pkg_desc, "Plants", ["station_index"])

add_foreign_key!(pkg_desc, "Plants", ["downstream"], "Plants", ["station_index"])
add_foreign_key!(pkg_desc, "Constraints", ["constraint_station"], "Plants", ["station_name"])

save_datapackage(pkg_desc, path)
