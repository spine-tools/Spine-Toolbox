######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains a class template for a data source connector used in import ui.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from spinedb_api import read_with_mapping, DateTime, Duration, ParameterValueFormatError

TYPE_STRING_TO_CLASS = {"string": str, "datetime": DateTime, "duration": Duration, "float": float}

TYPE_CLASS_TO_STRING = {type_class: string for string, type_class in TYPE_STRING_TO_CLASS.items()}


class TypeConversionException(Exception):
    def __init__(self, row_number, message):
        super(TypeConversionException, self).__init__()
        self.row_number = row_number
        self.message = message


class SourceConnection:
    """Template class to read data from another QThread."""

    # name of data source, ex: "Text/CSV"
    DISPLAY_NAME = "unnamed source"

    # dict with option specification for source.
    OPTIONS = {}

    # Modal widget that that returns action (OK, CANCEL) and source object
    SELECT_SOURCE_UI = NotImplemented

    def connect_to_source(self, source):
        """Connects to source, ex: connecting to a database where source is a connection string.

        Arguments:
            source {} -- object with information on source to be connected to, ex: filepath string for a csv connection
        """
        raise NotImplementedError()

    def disconnect(self):
        """Disconnect from connected source.
        """
        raise NotImplementedError()

    def get_tables(self):
        """Method that should return a list of table names, list(str)

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError()

    def get_data_iterator(self, table, options, max_rows=-1):
        """
        Function that should return a data iterator, data header and number of
        columns.
        """
        raise NotImplementedError()

    def get_data(self, table, options, max_rows=-1):
        """
        Return data read from data source table in table. If max_rows is
        specified only that number of rows.
        """
        data_iter, header, _num_cols = self.get_data_iterator(table, options, max_rows)
        data = list(data_iter)
        return data, header

    @staticmethod
    def convert_data_to_types_generator(column_types, data_iterator, num_cols):
        if not column_types:
            return data_iterator
        do_nothing = lambda x: x
        type_conv_list = []
        for c in range(num_cols):
            type_str = column_types.get(c, None)
            type_conv_list.append(TYPE_STRING_TO_CLASS.get(type_str, do_nothing))

        def convert_list(data):
            for row_number, row_data in enumerate(data):
                row_list = []
                for row_item, col_type in zip(row_data, type_conv_list):
                    try:
                        if isinstance(row_item, str) and not row_item:
                            row_item = None
                        if row_item is not None:
                            row_item = col_type(row_item)
                        row_list.append(row_item)
                    except (ValueError, ParameterValueFormatError):
                        raise TypeConversionException(
                            row_number,
                            f"Could not convert value: '{row_item}' to type: '{TYPE_CLASS_TO_STRING[col_type]}'",
                        )
                yield row_list

        return convert_list(data_iterator)

    def get_mapped_data(self, tables_mappings, options, table_types, max_rows=-1):
        """
        Reads all mappings in dict tables_mappings, where key is name of table
        and value is the mappings for that table.
        emits mapped data when ready.
        """
        mapped_data = {
            "object_classes": [],
            "objects": [],
            "object_parameters": [],
            "object_parameter_values": [],
            "relationship_classes": [],
            "relationships": [],
            "relationship_parameters": [],
            "relationship_parameter_values": [],
        }
        errors = []
        for table, mapping in tables_mappings.items():
            types = table_types.get(table, {})
            opt = options.get(table, {})
            data, header, num_cols = self.get_data_iterator(table, opt, max_rows)
            data = self.convert_data_to_types_generator(types, data, num_cols)
            try:
                data, t_errors = read_with_mapping(data, mapping, num_cols, header)
                for key, value in data.items():
                    mapped_data[key].extend(value)
                errors.extend([(table, err) for err in t_errors])
            except TypeConversionException as type_error:
                errors.append((table, f"Error on row: {type_error.row_number}: {type_error.message}"))

        return mapped_data, errors
