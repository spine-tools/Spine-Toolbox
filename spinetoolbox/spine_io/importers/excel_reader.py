# -*- coding: utf-8 -*-

from itertools import islice

from spine_io.io_api import FileImportTemplate, IOWorker

from PySide2.QtWidgets import QWidget, QFormLayout, QLabel, QCheckBox, QSpinBox, QGroupBox, QVBoxLayout
from PySide2.QtCore import Signal, QThread

from openpyxl import load_workbook

class ExcelConnector(FileImportTemplate):
    DISPLAY_NAME = 'Excel file'

    startTableGet = Signal()
    startDataGet = Signal(str, dict, int)
    startMappedDataGet = Signal(dict, dict, int)
    def __init__(self):
        super(ExcelConnector, self).__init__()
        
        # thread and worker
        self.thread = None
        self.worker = None
        
        self._filename = None
        
        self.sheet_options = {}
        self._option_widget = ExcelOptionWidget()
        self.current_sheet = None
        
        self._option_widget.optionsChanged.connect(self._new_options)

    def _new_options(self):
        if self.current_sheet:
            options = {"header": self._option_widget.first_row_as_header,
                       "row": self._option_widget.skip_rows,
                       "column": self._option_widget.skip_columns,
                       "read_until_col": self._option_widget.read_until_col,
                       "read_until_row": self._option_widget.read_until_row}
            self.sheet_options.update({self.current_sheet: options})
        self.request_data(self.current_sheet, 100)
    
    def set_table(self, sheet):
        if self.current_sheet:
            options = {"header": self._option_widget.first_row_as_header,
                       "row": self._option_widget.skip_rows,
                       "column": self._option_widget.skip_columns,
                       "read_until_col": self._option_widget.read_until_col,
                       "read_until_row": self._option_widget.read_until_row}
            self.sheet_options.update({self.current_sheet: options})
        self.current_sheet = sheet
        if sheet in self.sheet_options:
            self._option_widget.update_values(**self.sheet_options[sheet])
        else:
            self._option_widget.update_values()
    
    @property
    def file_filter(self):
        """
        Return filter string for file, change return for specific filter.
        """
        return '*.xlsx;*.xlsm;*.xltx;*.xltm'
    
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
        self.worker = ExcelWorker(self._filename)
        self.worker.moveToThread(self.thread)
        # close existing thread
        self.close_connection()
        # connect worker signals
        self.worker.connectionReady.connect(lambda: self.connectionReady.emit())
        self.worker.tablesReady.connect(lambda tables: self.tablesReady.emit(tables))
        self.worker.dataReady.connect(lambda data, header: self.dataReady.emit(data, header))
        self.worker.mappedDataReady.connect(lambda data, error: self.mappedDataReady.emit(data, error))
        self.worker.error.connect(lambda error_str: self.error.emit(error_str))
        # connect start working signals
        self.startTableGet.connect(self.worker.tables)
        self.startDataGet.connect(self.worker.read_data)
        self.startMappedDataGet.connect(self.worker.read_mapped_data)
        self.thread.started.connect(self.worker.connect_excel)
        self.thread.start()
    
    def request_tables(self):
        self.fetchingData.emit()
        self.startTableGet.emit()
    
    def request_mapped_data(self, tables_mappings, max_rows=-1):
        options = {}
        for t in tables_mappings:
            if t in self.sheet_options:
                options[t] = self.sheet_options[t]
            else:
                options[t] = {}
        self.fetchingData.emit()
        self.startMappedDataGet.emit(tables_mappings, options, max_rows)
    
    def request_data(self, table, max_rows=-1):
        options = {"header": self._option_widget.first_row_as_header,
                   "row": self._option_widget.skip_rows,
                   "column": self._option_widget.skip_columns,
                   "read_until_col": self._option_widget.read_until_col,
                   "read_until_row": self._option_widget.read_until_row}
        self.fetchingData.emit()
        self.startDataGet.emit(table, options, max_rows)
    
    def option_widget(self):
        """
        Return a Qwidget with options for reading data from a table in source
        """
        return self._option_widget
    
    def close_connection(self):
        if self.thread:
            self.thread.quit()
            self.thread.wait()


class ExcelWorker(IOWorker):
    
    def __init__(self, filename,parent=None):
        super(ExcelWorker, self).__init__(parent)
        
        self._filename = filename
        self._wb = None
    
    def connect_excel(self):
        """
        Connect to data source
        """
        if self._filename:
            try:
                self._wb = load_workbook(self._filename, read_only=True)
                self.connectionReady.emit()
            except Exception as e:
                print(e)
                self.error.emit('Could not connect to excel file!')
    
    def tables(self):
        if not self._wb:
            self.tablesReady.emit([])
        else:
            try:
                sheets = self._wb.sheetnames
                self.tablesReady.emit(sheets)
            except:
                self.error.emit('could not get sheets from excel file')
    
    def get_data_iterator(self, table, options, max_rows=-1):
        """
        Return data read from data source table in table. If max_rows is 
        specified only that number of rows.
        """       
        if not self._wb:
            return [], [], 0

        if not table in self._wb:
            # table not found
            return [], [], 0
        ws = self._wb[table]
        
        # get options
        has_header = options.get('header', False)
        skip_rows = options.get('row', 0)
        skip_columns = options.get('column', 0)
        stop_at_empty_col = options.get('read_until_col', False)
        stop_at_empty_row =options.get('read_until_row', False)
        
        if max_rows == -1:
            max_rows = None
        else:
            max_rows += skip_rows

        # find first empty col in top row and use that as a stop
        read_to_col = None
        
        try:
            first_row = next(islice(ws.iter_rows(), skip_rows, max_rows))
            if stop_at_empty_col:
                for i, c in enumerate(islice(first_row,skip_columns, None)):
                    if c.value is None:
                        read_to_col = i + skip_columns
                        break
                num_cols = read_to_col - skip_columns
            else:
                num_cols = len(first_row)
        except StopIteration:
            # no data
            pass
        
        header = []
        rows = ws.iter_rows()
        rows = islice(rows, skip_rows, max_rows)
        # find header if it has one
        if has_header:
            try:
                header = [c.value for c in islice(next(rows),skip_columns, read_to_col)]
            except StopIteration:
                # no data
                return [], [], 0

        # iterator for selected columns and and skipped rows
        data_iterator = (list(cell.value for cell in islice(row, skip_columns, read_to_col)) for row in rows)
        if stop_at_empty_row:
            # add condition to iterator
            condition = lambda row: row[0] is not None
            data_iterator = filter(data_iterator, condition)
        
        return data_iterator, header, num_cols


class ExcelOptionWidget(QWidget):
    optionsChanged = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # state
        self.block_signals = False
        self.first_row_as_header = False
        self.skip_rows = 0
        self.skip_columns = 0
        self.read_until_row = False
        self.read_until_col = False
        
        # ui
        self._ui_skip_row = QSpinBox()
        self._ui_skip_col = QSpinBox()
        self._ui_header = QCheckBox()
        self._ui_read_until_col = QCheckBox()
        self._ui_read_until_row = QCheckBox()
        
        self._ui_skip_row.setMinimum(0)
        self._ui_skip_col.setMinimum(0)
        
        # layout
        groupbox = QGroupBox("Excel options")
        self.setLayout(QVBoxLayout())
        layout = QFormLayout()
        layout.addRow(QLabel("Skip rows:"), self._ui_skip_row)
        layout.addRow(QLabel("Skip columns:"), self._ui_skip_col)
        layout.addRow(QLabel("Header in first row:"), self._ui_header)
        layout.addRow(QLabel("Read until first empty column:"), self._ui_read_until_col)
        layout.addRow(QLabel("Read until first empty row:"), self._ui_read_until_row)
        groupbox.setLayout(layout)
        self.layout().addWidget(groupbox)
        
        # connect signals
        self._ui_skip_row.valueChanged.connect(self._skip_row_change)
        self._ui_skip_col.valueChanged.connect(self._skip_col_change)
        self._ui_header.stateChanged.connect(self._header_change)
        self._ui_read_until_col.stateChanged.connect(self._read_until_col_change)
        self._ui_read_until_row.stateChanged.connect(self._read_until_row_change)
        
    def update_values(self, header=False, row=0, column=0, read_until_row=False, read_until_col=False):
        self.block_signals = True
        self._ui_skip_row.setValue(row)
        self._ui_skip_col.setValue(column)
        self._ui_header.setChecked(header)
        self._ui_read_until_row.setChecked(read_until_row)
        self._ui_read_until_col.setChecked(read_until_col)
        self.block_signals = False
        
    def _header_change(self, new_bool):
        self.first_row_as_header = new_bool
        if not self.block_signals:
            self.optionsChanged.emit()
    
    def _read_until_row_change(self, new_bool):
        self.read_until_row = new_bool
        if not self.block_signals:
            self.optionsChanged.emit()
    
    def _read_until_col_change(self, new_bool):
        self.read_until_col = new_bool
        if not self.block_signals:
            self.optionsChanged.emit()
    
    def _skip_row_change(self, new_num):
        self.skip_rows = new_num
        if not self.block_signals:
            self.optionsChanged.emit()
    
    def _skip_col_change(self, new_num):
        self.skip_columns = new_num
        if not self.block_signals:
            self.optionsChanged.emit()
            
        
        

