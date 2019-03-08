# -*- coding: utf-8 -*-

from io_api import FileImportTemplate

from PySide2.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QCheckBox, QSpinBox, QGroupBox, QVBoxLayout
from PySide2.QtCore import QObject, Signal

import csv
from itertools import islice

class CSVConnector(FileImportTemplate):
    def __init__(self):
        super(CSVConnector, self).__init__()
        
        self._filename = None
        self._option_widget = CSVOptionWidget()
        
        self._option_widget.optionsChanged.connect(self._new_options)

    def _new_options(self):
        self.refreshDataRequest.emit()
    
    def set_table(self, table):
        pass
    
    @property
    def tables(self):
        pass
    
    @property
    def source_name(self):
        """Name of data source, must return string"""
        return 'CSV/Text'
    
    @property
    def can_have_multiple_tables(self):
        return False
        
    def source_selector(self):
        filename, action = self.select_file()
        if not filename:
            return False
        self._filename = filename
        return True
    
    def preview_data(self, table):
        return self.read_data(table, max_rows=100)
    
    def read_data(self, table, max_rows=None):
        """
        Return data read from data source table in table. If max_rows is 
        specified only that number of rows.
        """
        if not self._filename:
            return [], []
        
        if max_rows != None and type(max_rows) != int:
            raise TypeError('max_rows must be int')
        
        dialect = {'delimiter': self._option_widget.delim}
        quotechar = self._option_widget.quote
        if quotechar:
            dialect.update({'quotechar': quotechar})
        has_header = self._option_widget.first_row_as_header
        skip = self._option_widget.skip_rows
        
        with open(self._filename) as f:
            csv_reader = csv.reader(f, **dialect)
            csv_reader = islice(csv_reader, skip, max_rows+skip)
            data = []
            header = []

            if has_header:
                header = next(csv_reader)
            for row in csv_reader:
                data.append(row)
        return data, header
    
    def option_widget(self):
        """
        Return a Qwidget with options for reading data from a table in source
        """
        return self._option_widget

class CSVOptionWidget(QWidget):
    optionsChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # state
        self.delim = ','
        self.quote = ''
        self.first_row_as_header = False
        self.skip_rows = 0
        
        # ui
        self._ui_delim = QLineEdit()
        self._ui_quote = QLineEdit()
        self._ui_skip = QSpinBox()
        self._ui_header = QCheckBox()
        
        self._ui_quote.setMaxLength(1)
        self._ui_skip.setMinimum(0)
        self._ui_delim.setText(self.delim)
        self._ui_quote.setText(self.quote)
        
        # layout
        groupbox = QGroupBox("CSV options")
        self.setLayout(QVBoxLayout())
        layout = QFormLayout()
        layout.addRow(QLabel("Delimeter:"), self._ui_delim)
        layout.addRow(QLabel("Quote char:"), self._ui_quote)
        layout.addRow(QLabel("Header in first row:"), self._ui_header)
        layout.addRow(QLabel("Skip rows:"), self._ui_skip)
        groupbox.setLayout(layout)
        self.layout().addWidget(groupbox)
        
        # connect signals
        self._ui_delim.textEdited.connect(self._delim_change)
        self._ui_quote.textEdited.connect(self._quote_change)
        self._ui_skip.valueChanged.connect(self._skip_change)
        self._ui_header.stateChanged.connect(self._header_change)
        
    def _delim_change(self, new_char):
        self.delim = new_char
        self.optionsChanged.emit()
    
    def _quote_change(self, new_char):
        self.quote = new_char
        self.optionsChanged.emit()
    
    def _header_change(self, new_bool):
        self.first_row_as_header = new_bool
        self.optionsChanged.emit()
    
    def _skip_change(self, new_num):
        self.skip_rows = new_num
        self.optionsChanged.emit()
            
        
        



