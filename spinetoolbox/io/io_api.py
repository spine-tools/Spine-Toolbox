# -*- coding: utf-8 -*-

from pyside2.QtWidgets import QFileDialog
from pyside2.QtQui import QIcon

class DataSourceImportTemplate():
    """
    Base class for interfaces to import data from different sources.
    
    """
    
    def __init__(self, parent=None):
        self.parent = parent
        self._preview_data = {} # store data for preview for each table
        self._tables = [] # lits of strings of avaliable tables in data source
    
    @property
    def tables(self):
        """Read only"""
        return self._tables

    @property
    def preview_data(self):
        """Read only"""
        return self._preview_data
    
    @property
    def source_icon(self):
        """
        Return source icon (QIcon instance)
        """
        return QIcon()
    
    @property
    def source_name(self):
        """Name of data source, must return string"""
        return NotImplementedError
    
    @property
    def can_have_multiple_tables(self):
        """
        Return boolean if data source can contain multiple tables
        """
        raise NotImplementedError

    def source_selector(self):
        """
        Select launches file/source UI
        """
        raise NotImplementedError
    
    def read_data(self, table, max_rows=100):
        """
        Return data read from data source table in table. If max_rows is 
        specified only that number of rows.
        """
        raise NotImplementedError
    
    def option_widget(self, table):
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
        
        
