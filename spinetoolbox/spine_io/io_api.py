######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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

from spinedb_api import read_with_mapping, DateTime, Duration

TYPE_STRING_TO_CLASS = {"string": str, "datetime": DateTime, "duration": Duration, "float": float}

TYPE_CLASS_TO_STRING = {type_class: string for string, type_class in TYPE_STRING_TO_CLASS.items()}


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

    def get_mapped_data(self, tables_mappings, options, table_types, table_row_types, max_rows=-1):
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
            types = {col: spec.convert_function() for col, spec in table_types.get(table, {}).items()}
            row_types = {row: spec.convert_function() for row, spec in table_row_types.get(table, {}).items()}
            opt = options.get(table, {})
            data, header, num_cols = self.get_data_iterator(table, opt, max_rows)
            data, t_errors = read_with_mapping(data, mapping, num_cols, header, types, row_types)
            for key, value in data.items():
                mapped_data[key].extend(value)
            errors.extend([(table, f"Could not map row: {row_number}, Error: {err}") for row_number, err in t_errors])

        return mapped_data, errors
