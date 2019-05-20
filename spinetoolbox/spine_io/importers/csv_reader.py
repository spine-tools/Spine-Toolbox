# -*- coding: utf-8 -*-

import csv
from itertools import islice

from PySide2.QtWidgets import (
    QWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QVBoxLayout,
)
from PySide2.QtCore import Signal, QThread

from spine_io.io_api import FileImportTemplate, IOWorker


class CSVConnector(FileImportTemplate):
    """Class to read csv/text files in import_widget
    """
    DISPLAY_NAME = "Text/CSV file"
    startDataGet = Signal(str, dict, int)
    startMappedDataGet = Signal(dict, dict, int)

    def __init__(self):
        super(CSVConnector, self).__init__()
        self._thread = None
        self._worker = None
        self._filename = None
        self._option_widget = CSVOptionWidget()
        self._option_widget.optionsChanged.connect(lambda: self.request_data(None, 100))

    def set_table(self, table):
        """Unused since we only have one file

        Arguments:
            table {str} -- unused
        """

    def request_tables(self):
        """Get tables, for a csv/text file this is just the filename
        """
        self.tablesReady.emit([self._filename])

    def request_data(self, table=None, max_rows=-1):
        """Request data from connector, connect to dataReady to recive data

        Keyword Arguments:
            table {str} -- unused, used by abstract class (default: {None})
            max_rows {int} -- how many rows to read (default: {-1})
        """
        options = self._option_widget.get_options_dict()
        self.fetchingData.emit()
        self.startDataGet.emit(self._filename, options, max_rows)

    def request_mapped_data(self, tables_mappings, max_rows=-1):
        """Get mapped data from csv file

        Arguments:
            tables_mappings {dict} -- dict with filename as key and a list of mappings as value

        Keyword Arguments:
            max_rows {int} -- number of rows to read, if -1 read all rows (default: {-1})
        """
        options = {self._filename: self._option_widget.get_options_dict()}
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
        """Creates a Worker and a new thread to read csv file.
        If there is a existing thread close that one.
        """
        # close existing thread
        self.close_connection()
        # create new thread and worker
        self._thread = QThread()
        self._worker = CSVWorker(self._filename)
        self._worker.moveToThread(self._thread)
        # connect worker signals
        self._worker.dataReady.connect(
            lambda data, header: self.dataReady.emit(data, header)
        )
        self._worker.mappedDataReady.connect(
            lambda data, error: self.mappedDataReady.emit(data, error)
        )
        self._worker.error.connect(lambda error_str: self.error.emit(error_str))
        # connect start working signals
        self.startDataGet.connect(self._worker.read_data)
        self.startMappedDataGet.connect(self._worker.read_mapped_data)
        self._thread.started.connect(lambda: self.connectionReady.emit())
        self._thread.start()

    def option_widget(self):
        """
        Return a Qwidget with options for reading data from a table in source
        """
        return self._option_widget

    def close_connection(self):
        """Close and delete thread and worker
        """
        if self._thread:
            self._thread.quit()
            self._thread.wait()
        if self._worker:
            self._worker.deleteLater()
            self._worker = None


class CSVWorker(IOWorker):
    """Worker to read a csv/text file in another thread
    """
    def __init__(self, filename, parent=None):
        super(CSVWorker, self).__init__(parent)
        self._filename = filename

    def parse_options(self, options):
        """Parses options dict to dialect and quotechar options for csv.reader

        Arguments:
            options {dict} -- dict with options:
                "delimiter": file delimiter
                "quotechar": file quotechar
                "has_header": if first row should be treated as a header
                "skip": how many rows should be skipped

        Returns:
            tuple(dict, bool, integer) -- tuple dialect for csv.reader,
                                          quotechar for csv.reader and
                                          number of rows to skip
        """
        dialect = {"delimiter": options.get("delim", ",")}
        quotechar = options.get("quotechar", None)
        if quotechar:
            dialect.update({"quotechar": quotechar})
        has_header = options.get("has_header", False)
        skip = options.get("skip", 0)
        return dialect, has_header, skip

    def file_iterator(self, options, max_rows):
        """creates a iterator that reads max_rows number of rows from text file

        Arguments:
            options {dict} -- dict with options:
            max_rows {integer} -- max number of rows to read, if -1 then read all rows

        Returns:
            iterator -- iterator of csv file
        """
        if not self._filename:
            return []
        dialect, _has_header, skip = self.parse_options(options)
        if max_rows == -1:
            max_rows = None
        else:
            max_rows += skip
        with open(self._filename) as f:
            csv_reader = csv.reader(f, **dialect)
            csv_reader = islice(csv_reader, skip, max_rows)
            yield from csv_reader

    def get_data_iterator(self, table, options, max_rows=-1):
        """Creates a iterator for the file in self.filename

        Arguments:
            table {string} -- ignored, used in abstract IOWorker class
            options {dict} -- dict with options

        Keyword Arguments:
            max_rows {int} -- how many rows of data to read, if -1 read all rows (default: {-1})

        Returns:
            [type] -- [description]
        """
        csv_iter = self.file_iterator(options, max_rows)
        try:
            first_row = next(csv_iter)
        except StopIteration:
            return iter([]), [], 0

        _dialect, has_header, _skip = self.parse_options(options)
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
        self.delim = ","
        self.quote = ""
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

    def get_options_dict(self):
        """gets selected options from widget

        Returns:
            dict -- dict with options and values
        """
        return {
            "delim": self.delim,
            "quotechar": self.quote,
            "has_header": self.first_row_as_header,
            "skip": self.skip_rows,
        }

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
