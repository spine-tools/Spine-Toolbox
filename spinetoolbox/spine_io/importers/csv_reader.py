# -*- coding: utf-8 -*-

from spine_io.io_api import FileImportTemplate, IOWorker

from PySide2.QtWidgets import QWidget, QFormLayout, QLabel, QLineEdit, QCheckBox, QSpinBox, QGroupBox, QVBoxLayout
from PySide2.QtCore import Signal, QThread

import csv
from itertools import islice

class CSVConnector(FileImportTemplate):
    DISPLAY_NAME = 'Text/CSV file'

    startDataGet = Signal(str, dict, int)
    startMappedDataGet = Signal(dict, dict, int)
    def __init__(self):
        super(CSVConnector, self).__init__()
        
        self._filename = None
        self._option_widget = CSVOptionWidget()
        self._option_widget.optionsChanged.connect(lambda : self.request_data(None, 100))

    def set_table(self, table):
        pass

    def request_tables(self):
        self.tablesReady.emit([self._filename])
    
    def request_data(self, table=None, max_rows=-1):
        options = {'delim': self._option_widget.delim,
                   'quotechar': self._option_widget.quote,
                   'has_header': self._option_widget.first_row_as_header,
                   'skip': self._option_widget.skip_rows}
        self.fetchingData.emit()
        self.startDataGet.emit(self._filename, options, max_rows)
    
    def request_mapped_data(self, tables_mappings, max_rows=-1):
        options = {self._filename: {'delim': self._option_widget.delim,
                                    'quotechar': self._option_widget.quote,
                                    'has_header': self._option_widget.first_row_as_header,
                                    'skip': self._option_widget.skip_rows}}
        self.fetchingData.emit()
        self.startMappedDataGet.emit(tables_mappings, options, max_rows)

    def connection_ui(self):
        """
        launches a file selector ui and returns True if file is selected
        """
        filename, action = self.select_file()
        if not filename or not action:
            return False
        self._filename = filename
        return True

    def init_connection(self):
        self.thread = QThread()
        self.worker = CSVWorker(self._filename)
        self.worker.moveToThread(self.thread)
        # close existing thread
        self.close_connection()
        # connect worker signals
        self.worker.dataReady.connect(lambda data, header: self.dataReady.emit(data, header))
        self.worker.mappedDataReady.connect(lambda data, error: self.mappedDataReady.emit(data, error))
        self.worker.error.connect(lambda error_str: self.error.emit(error_str))
        # connect start working signals
        self.startDataGet.connect(self.worker.read_data)
        self.startMappedDataGet.connect(self.worker.read_mapped_data)
        self.thread.started.connect(lambda: self.connectionReady.emit())
        self.thread.start()

    def option_widget(self):
        """
        Return a Qwidget with options for reading data from a table in source
        """
        return self._option_widget
    
    def close_connection(self):
        if self.thread:
            self.thread.quit()
            self.thread.wait()


class CSVWorker(IOWorker):
    def __init__(self, filename,parent=None):
        super(CSVWorker, self).__init__(parent)
        self._filename = filename
        
    def parse_options(self, options):
        dialect = {'delimiter': options.get('delim', ',')}
        quotechar = options.get('quotechar', None)
        if quotechar:
            dialect.update({'quotechar': quotechar})
        has_header = options.get('has_header', False)
        skip = options.get('skip', 0)
        return dialect, has_header, skip
    
    def file_iterator(self, options, max_rows):
        if not self._filename:
            return []
        dialect, has_header, skip = self.parse_options(options)
        if max_rows == -1:
            max_rows = None
        else:
            max_rows += skip
        with open(self._filename) as f:
            csv_reader = csv.reader(f, **dialect)
            csv_reader = islice(csv_reader, skip, max_rows)
            yield from csv_reader
        
    def get_data_iterator(self, table, options, max_rows=-1):
        csv_iter = self.file_iterator(options, max_rows)
        try:
            first_row = next(csv_iter)
        except StopIteration:
            return [], [], 0
        
        dialect, has_header, skip = self.parse_options(options)
        num_cols = len(first_row)
        if has_header:
            header = first_row
        else:
            # reset iterator
            header = []
            csv_iter = self.file_iterator(options, max_rows)
        return csv_iter, header, num_cols


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
            
        
        



