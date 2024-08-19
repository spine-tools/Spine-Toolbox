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
"""This module contains utilities for pasting data from Excel."""
from xml.etree import ElementTree
from spinedb_api import DateTime, to_database
from spinedb_api.parameter_value import join_value_and_type

# Ideally, we would use openpyxl to deal with Excel data.
# However, openpyxl is geared towards handling data from file,
# not from clipboard, and it seems to be very tedious to get it to work with the
# clipboard's XML blobs.

EXCEL_CLIPBOARD_MIME_TYPE = 'application/x-qt-windows-mime;value="XML Spreadsheet"'
URN_PREFIX = "{urn:schemas-microsoft-com:office:spreadsheet}"


def _convert_from_excel(data):
    """Converts cell data to Python.

    Args:
        data (Element): cell element

    Returns:
        Any: cell's data
    """

    def date_time_to_database(x):
        return bytes(join_value_and_type(*to_database(DateTime(x))), encoding="utf-8")

    def bool_to_database(x):
        return bytes(join_value_and_type(*to_database(bool(x))), encoding="utf-8")

    convert_function = {
        "Boolean": bool_to_database,
        "DateTime": date_time_to_database,
        "Number": float,
        "String": str,
    }[data.attrib[URN_PREFIX + "Type"]]
    return convert_function(data.text)


def clipboard_excel_as_table(clipboard_data):
    """Converts Excel XML blob to Python table.

    Args:
        clipboard_data (bytes): XML blob

    Returns:
        list of list: table
    """
    if clipboard_data.endswith(b"\00"):
        clipboard_data = clipboard_data[:-1]
    root = ElementTree.fromstring(clipboard_data)
    worksheet = root.find(URN_PREFIX + "Worksheet")
    if worksheet is None:
        raise ValueError("no worksheet")
    table = worksheet.find(URN_PREFIX + "Table")
    if table is None:
        raise ValueError("no table")
    converted_data = {}
    all_column_indexes = set()
    row_i = 0
    for row in table.findall(URN_PREFIX + "Row"):
        row_index = row.attrib.get(URN_PREFIX + "Index")
        if row_index is not None:
            row_i = int(row_index) - 1
        column_i = 0
        for cell in row.findall(URN_PREFIX + "Cell"):
            cell_index = cell.attrib.get(URN_PREFIX + "Index")
            if cell_index is not None:
                column_i = int(cell_index) - 1
            data = cell.find(URN_PREFIX + "Data")
            converted_data[(row_i, column_i)] = _convert_from_excel(data)
            all_column_indexes.add(column_i)
            column_i += 1
        row_i += 1
    if not converted_data:
        return []
    result_table = []
    row_count = row_i
    column_count = max(all_column_indexes) + 1
    for row_i in range(row_count):
        result_row = []
        result_table.append(result_row)
        for column_i in range(column_count):
            result_row.append(converted_data.get((row_i, column_i)))
    return result_table
