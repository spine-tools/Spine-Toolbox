# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QFileDialog
from PySide2.QtGui import QIcon
from PySide2.QtCore import QObject, Signal

class DataSourceImportTemplate(QObject):
    """
    Base class for interfaces to import data from different sources.
    
    """
    refreshDataRequest = Signal()
    def __init__(self, parent=None):
        super(DataSourceImportTemplate, self).__init__(parent)
        self.parent = parent

    @property
    def source_icon(self):
        """
        Return source icon (QIcon instance)
        """
        return QIcon()
    
    @property
    def source_name(self):
        """Name of data source, must return string"""
        raise NotImplementedError
    
    @property
    def tables(self):
        """Return a list of table names if source has multiple tables"""
        raise NotImplementedError
    
    @property
    def can_have_multiple_tables(self):
        """
        Return boolean if data source can contain multiple tables
        """
        raise NotImplementedError
    
    def set_table(self, table):
        """
        Sets the current table of the data source. If data source doesn't have
        mulitple tables just pass this function.
        """
        raise NotImplementedError

    def source_selector(self):
        """
        launches file/source select UI
        return True if successful, otherwise False
        """
        raise NotImplementedError
    
    def read_data(self, table):
        """
        Return data read from data source table in table. If max_rows is 
        specified only that number of rows.
        """
        raise NotImplementedError
    
    def option_widget(self):
        """
        Return a Qwidget with options for reading data from a table in source
        """
        raise NotImplementedError
    
    def preview_data(self, table):
        """Returns a preview of the table in data source"""
        return self._preview_data

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
        
        
