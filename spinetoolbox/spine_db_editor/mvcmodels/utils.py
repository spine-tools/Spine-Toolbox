######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""General helper functions and classes for DB editor's models."""
import csv
from io import StringIO
from typing import Optional
from PySide6.QtCore import QModelIndex, QSize
from spinedb_api import DatabaseMapping, SpineDBAPIError
from spinedb_api.temp_id import TempId
from spinetoolbox.mvcmodels.minimal_table_model import MinimalTableModel

PARAMETER_DEFINITION_MODEL_HEADER = [
    "entity_class_name",
    "parameter_name",
    "valid types",
    "value_list_name",
    "default_value",
    "description",
    "database",
]
PARAMETER_DEFINITION_FIELD_MAP = {
    "parameter_name": "name",
    "valid types": "parameter_type_list",
    "value_list_name": "parameter_value_list_name",
}
PARAMETER_VALUE_MODEL_HEADER = [
    "entity_class_name",
    "entity_byname",
    "parameter_name",
    "alternative_name",
    "value",
    "database",
]
PARAMETER_VALUE_FIELD_MAP = {"parameter_name": "parameter_definition_name"}
ENTITY_ALTERNATIVE_MODEL_HEADER = [
    "entity_class_name",
    "entity_byname",
    "alternative_name",
    "active",
    "database",
]


def two_column_as_csv(indexes):
    """Writes data in given indexes into a CSV table.

    Expects the source table to have two columns.

    Args:
        indexes (Sequence of QModelIndex): model indexes

    Returns:
        str: data as CSV table
    """
    first_column = indexes[0].column()
    single_column = all(i.column() == first_column for i in indexes[1:])
    with StringIO(newline="") as out:
        writer = csv.writer(out, delimiter="\t", quotechar="'")
        rows = {}
        for index in indexes:
            if single_column:
                rows[index.row()] = [index.data()]
            else:
                rows.setdefault(index.row(), ["", ""])[index.column()] = index.data()
        for row in sorted(rows):
            content = rows[row]
            writer.writerow(content)
        return out.getvalue()


def entity_class_id_for_row(index: QModelIndex, db_map: DatabaseMapping) -> Optional[TempId]:
    model: MinimalTableModel = index.model()
    entity_class_name = index.sibling(index.row(), model.header.index("entity_class_name")).data()
    try:
        entity_class = db_map.entity_class(name=entity_class_name)
    except SpineDBAPIError:
        return None
    return entity_class["id"]


def make_entity_on_the_fly(item: dict, db_map: DatabaseMapping) -> tuple[Optional[dict], list[str]]:
    """Returns a database entity item (id-based) from the given model parameter_value item (name-based).

    Args:
        item: the model parameter_value item
        db_map: the database where the resulting item belongs

    Returns:
        the db entity item and error log
    """
    entity_class_name = item.get("entity_class_name")
    entity_class = db_map.get_item("entity_class", name=entity_class_name)
    if not entity_class:
        return None, [f"Unknown entity_class {entity_class_name}"] if entity_class_name else []
    entity_byname = item.get("entity_byname")
    if not entity_byname:
        return None, []
    item = {"entity_class_name": entity_class_name, "entity_byname": entity_byname}
    return None if db_map.get_item("entity", **item) else item, []
