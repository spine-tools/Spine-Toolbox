# -*- coding: utf-8 -*-
"""
Class template for a data source connector used in the import ui.
"""
from spinedb_api import read_with_mapping


class SourceConnection:
    """
    Template class to read data from another QThread
    """

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
        raise NotImplementedError

    def disconnect(self):
        """Disconnect from connected source.
        """
        raise NotImplementedError

    def get_tables(self):
        """Method that should return a list of table names, list(str)
        
        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def get_data_iterator(self, table, options, max_rows=-1):
        """
        Function that should return a data iterator, data header and number of
        columns.
        """
        raise NotImplementedError

    def get_data(self, table, options, max_rows=-1):
        """
        Return data read from data source table in table. If max_rows is
        specified only that number of rows.
        """
        data_iter, header, _num_cols = self.get_data_iterator(table, options, max_rows)
        data = [d for d in data_iter]
        return data, header

    def get_mapped_data(self, tables_mappings, options, max_rows=-1):
        """
        Reads all mappings in dict table_mappings, where key is name of table
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
            opt = options.get(table, {})
            data, header, num_cols = self.get_data_iterator(table, opt, max_rows)
            data, error = read_with_mapping(data, mapping, num_cols, header)
            for key, value in data.items():
                mapped_data[key].extend(value)
            errors.extend(error)
        return mapped_data, errors
