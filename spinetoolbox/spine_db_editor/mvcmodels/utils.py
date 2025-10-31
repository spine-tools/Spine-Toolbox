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
from collections.abc import Sequence
import csv
from io import StringIO
from itertools import takewhile
from typing import TYPE_CHECKING, Optional, TypeAlias
from PySide6.QtCore import QModelIndex
from spinedb_api import DatabaseMapping, SpineDBAPIError
from spinedb_api.db_mapping_base import PublicItem
from spinedb_api.temp_id import TempId

if TYPE_CHECKING:
    from spinetoolbox.spine_db_editor.mvcmodels.compound_models import CompoundStackedModel

FilterIds: TypeAlias = dict[tuple[DatabaseMapping, TempId], set[TempId]]

PARAMETER_DEFINITION_FIELD_MAP = {
    "class": "entity_class_name",
    "parameter name": "name",
    "valid types": "parameter_type_list",
    "value list": "parameter_value_list_name",
    "default value": "default_value",
    "description": "description",
    "database": "database",
}
PARAMETER_VALUE_FIELD_MAP = {
    "class": "entity_class_name",
    "entity byname": "entity_byname",
    "parameter name": "parameter_definition_name",
    "alternative": "alternative_name",
    "value": "value",
    "database": "database",
}
ENTITY_ALTERNATIVE_FIELD_MAP = {
    "class": "entity_class_name",
    "entity byname": "entity_byname",
    "alternative": "alternative_name",
    "active": "active",
    "database": "database",
}
ENTITY_FIELD_MAP = {
    "class": "entity_class_name",
    "name": "name",
    "byname": "entity_byname",
    "description": "description",
    "latitude": "lat",
    "longitude": "lon",
    "altitude": "alt",
    "shape name": "shape_name",
    "shape blob": "shape_blob",
    "database": "database",
}


def two_column_as_csv(indexes: Sequence[QModelIndex]) -> str:
    """Writes data in given indexes into a CSV table.

    Expects the source table to have two columns.

    Args:
        indexes: model indexes

    Returns:
        data as CSV table
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
    model: CompoundStackedModel = index.model()
    entity_class_name = index.sibling(
        index.row(), model.header.index(model.field_to_header("entity_class_name"))
    ).data()
    try:
        entity_class = db_map.entity_class(name=entity_class_name)
    except SpineDBAPIError:
        return None
    return entity_class["id"]


def make_entity_on_the_fly(item: dict, db_map: DatabaseMapping) -> tuple[Optional[PublicItem], list[str]]:
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


def field_index(field: str, field_map: dict[str, str]) -> int:
    index = len(list(takewhile(lambda x: x != field, field_map.values())))
    if index == len(field_map):
        raise RuntimeError(f"field {field} not found")
    return index


def field_header(field: str, field_map: dict[str, str]) -> str:
    return next(header for header, mapped_field in field_map.items() if mapped_field == field)
