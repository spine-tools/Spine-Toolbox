# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QFileDialog
from PySide2.QtGui import QIcon
from PySide2.QtCore import QObject, Signal

from spinedb_api import read_with_mapping

class DataSourceImportTemplate(QObject):
    """
    Base class for interfaces to import data from different sources.
    
    """

    # Connector display name, str. If string is '' then connector will be skipped
    # REQUIRED
    DISPLAY_NAME = ''
    
    # Signal that a connection to the datasource is ready
    connectionReady = Signal()
    
    # error while reading data or connection to data source
    error = Signal(str)
    
    # signal that the data connection is getting data
    fetchingData = Signal()
    
    # data from source is ready, should send list of data and headers
    dataReady = Signal(list, list)
    
    # tables from source is ready, should send a list of str of availible tables
    tablesReady = Signal(dict)
    
    # mapped data read from data source
    mappedDataReady = Signal(dict, list)
    
    def __init__(self, parent=None):
        super(DataSourceImportTemplate, self).__init__(parent)
        self.parent = parent

    @property
    def source_icon(self):
        """
        Return source icon (QIcon instance)
        """
        return QIcon()
    
    def request_tables(self):
        """
        Method to request tables from data source, tables should be a list of 
        table names emitted in signal tablesReady
        
        should emit tablesReady signal when connection is ready.
        
        If error emit error signal with an error message.
        """
        raise NotImplementedError
    
    def request_data(self, table, max_rows=None):
        """Returns a data from data source table. If max_rows is defined then
        only that many rows should be returned in the dataReady event
        
        Should emit dataReady signal with data when ready.
        
        If error emit error signal with an error message.
        
        Args:
            table (str): name of table to read data from.
            max_rows (int or None): maximum number of rows that should be read
                from data source. If None read all rows in data source.
        """
        raise NotImplementedError
    
    def request_mapped_data(self, table_mapping_dict, max_rows=None):
        """
        Return mapped data from data source. If table_mapping_dict contains
        mappings to multiple tables then all tables should be merged.
        
        If succesfull then mapped data should be sent with the signal
        mappedDataReady
        
        If error emit error signal with an error message.
        
        Args:
            tabe_mapping_dict (dict(str: spinedatabase_api.DataMapping)):
                A dict with table names as key and and DataMapping as values.
            max_rows (int or None): maximum number of rows that should be read
                from data source. If None read all rows in data source.
        """

    def set_table(self, table):
        """
        Sets the current table of the data source.
        """
        raise NotImplementedError
    
    def connection_ui(self):
        """
        Should launch a ui widget for connection options, return True if user
        has choosen a valid connection, False if cancel
        """
        raise NotImplementedError

    def init_connection(self):
        """
        launches file/source select UI and initialize data connection
        return False if user cancels otherwise True
        
        Should emit connectionReady signal when connection is ready.
        
        If error emit error signal with an error message.
        """
        raise NotImplementedError
    
    def close_connection(self):
        """
        Close conneciton
        """
        raise NotImplementedError

    def option_widget(self):
        """
        Return a Qwidget with options for reading data from a table in source
        """
        raise NotImplementedError
    
    

class FileImportTemplate(DataSourceImportTemplate):
    """
    Base class for import interface which uses a file as input
    """
    
    def __init__(self):
        super(FileImportTemplate, self).__init__()

    @property
    def file_filter(self):
        """
        Return filter string for file, change return for specific filter.
        """
        return '*.*'
    
    def select_file(self):
        """
        Selects a single file as input data
        """
        return QFileDialog.getOpenFileName(self.parent, '', self.file_filter)
        


class IOWorker(QObject):
    """
    Class to read data from another QThread
    """
    
    error = Signal(str)
    connectionReady = Signal()
    tablesReady = Signal(list)
    dataReady = Signal(list, list)
    mappedDataReady = Signal(dict, list)

    def __init__(self, filename,parent=None):
        super(IOWorker, self).__init__(parent)

    def get_data_iterator(self, table, options, max_rows=-1):
        """
        Function that should return a data iterator, data header and number of
        columns.
        """
        raise NotImplementedError
    
    def read_data(self, table, options, max_rows=-1):
        """
        Return data read from data source table in table. If max_rows is 
        specified only that number of rows.
        """
        try:
            data_iter, header, num_cols = self.get_data_iterator(table, options, max_rows)
            data = [d for d in data_iter]
            self.dataReady.emit(data, header)
        except Exception as e:
            self.error.emit(f'Error when reading data: {e}')
            print(e)
    
    def read_mapped_data(self, tables_mappings, options, max_rows=-1):
        mapped_data = {'object_classes': [],
                       'objects': [],
                       'object_parameters': [],
                       'object_parameter_values': [],
                       'relationship_classes': [],
                       'relationships': [],
                       'relationship_parameters': [],
                       'relationship_parameter_values': []}
        errors = []
        for table, mapping in tables_mappings.items():
            try:
                opt = options.get(table, {})
                data, header, num_cols = self.get_data_iterator(table, opt)
                data, error = read_with_mapping(data, mapping, num_cols, header)
                print(data)
                for k, v in data.items():
                    mapped_data[k].extend(v)
                errors.extend(error)
            except Exception as e:
                self.error.emit(f'Error when reading data source: {table}, message: {e}')
                return
        self.mappedDataReady.emit(mapped_data, errors)
            
        
        


















