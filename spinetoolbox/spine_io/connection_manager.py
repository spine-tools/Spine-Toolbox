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
Contains ConnectionManager class.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from PySide2.QtCore import QObject, Signal, QThread
from ..widgets.options_widget import OptionsWidget


class ConnectionManager(QObject):
    """Class to manage data connections in another thread.

    Args:
        connection (class): A class derived from `SourceConnection`, e.g. `CSVConnector`
    """

    startTableGet = Signal()
    startDataGet = Signal(str, dict, int)
    startMappedDataGet = Signal(dict, dict, dict, dict, int)

    # Signal with error message if connection fails
    connectionFailed = Signal(str)

    # Signal that a connection to the datasource is ready
    connectionReady = Signal()

    # Signal that connection is being closed
    closeConnection = Signal()

    # error while reading data or connection to data source
    error = Signal(str)

    # signal that the data connection is getting data
    fetchingData = Signal()

    # data from source is ready, should send list of data and headers
    dataReady = Signal(list, list)

    # tables from source is ready, should send a list of str of available tables
    tablesReady = Signal(dict)

    # mapped data read from data source
    mappedDataReady = Signal(dict, list)

    def __init__(self, connection, parent=None):
        super(ConnectionManager, self).__init__(parent)
        self._thread = None
        self._worker = None
        self._source = None
        self._current_table = None
        self._table_options = {}
        self._table_types = {}
        self._table_row_types = {}
        self._connection = connection
        self._options_widget = OptionsWidget(self._connection.OPTIONS)
        self._options_widget.optionsChanged.connect(self._new_options)
        self._is_connected = False

    @property
    def current_table(self):
        return self._current_table

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def table_options(self):
        return self._table_options

    @property
    def table_types(self):
        return self._table_types

    @property
    def table_row_types(self):
        return self._table_row_types

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        self._source = source

    @property
    def source_type(self):
        return self._connection.__name__

    def set_table(self, table):
        """Sets the current table of the data source.

        Arguments:
            table {str} -- str with table name
        """
        # save current options if a table is selected
        if self._current_table:
            options = self._options_widget.get_options()
            self._table_options.update({self._current_table: options})
        # check if table has options
        self._current_table = table
        if table in self._table_options:
            self._options_widget.set_options(self._table_options[table])
        else:
            # restore default values
            self._options_widget.set_options()

    def request_tables(self):
        """Get tables tables from source, emits two singals,
        fetchingData: ConnectionManager is busy waiting for data
        startTableGet: a signal that the worker in another thread is listening
        to know when to run get a list of table names.
        """
        if self.is_connected:
            self.fetchingData.emit()
            self.startTableGet.emit()

    def request_data(self, table=None, max_rows=-1):
        """Request data from emits dataReady to with data

        Keyword Arguments:
            table {str} -- which table to get data from (default: {None})
            max_rows {int} -- how many rows to read (default: {-1})
        """
        if self.is_connected:
            options = self._options_widget.get_options()
            self.fetchingData.emit()
            self.startDataGet.emit(table, options, max_rows)

    def request_mapped_data(self, table_mappings, max_rows=-1):
        """Get mapped data from csv file

        Arguments:
            table_mappings {dict} -- dict with filename as key and a list of mappings as value

        Keyword Arguments:
            max_rows {int} -- number of rows to read, if -1 read all rows (default: {-1})
        """
        if self.is_connected:
            options = {}
            types = {}
            row_types = {}
            self._table_options[self._current_table] = self._options_widget.get_options()
            for table_name in table_mappings:
                if table_name in self._table_options:
                    options[table_name] = self._table_options[table_name]
                else:
                    options[table_name] = {}
                types.setdefault(table_name, self._table_types.get(table_name, {}))
                row_types.setdefault(table_name, self._table_row_types.get(table_name, {}))
            self.fetchingData.emit()
            self.startMappedDataGet.emit(table_mappings, options, types, row_types, max_rows)

    def connection_ui(self):
        """
        launches a modal ui that prompts the user to select source.

        ex: fileselect if source is a file.
        """
        source, action = self._connection.SELECT_SOURCE_UI()
        if not source or not action:
            return False
        self._source = source
        return True

    def init_connection(self):
        """Creates a Worker and a new thread to read source data.
        If there is an existing thread close that one.
        """
        # close existing thread
        self.close_connection()
        # create new thread and worker
        self._thread = QThread()
        self._worker = ConnectionWorker(self._source, self._connection)
        self._worker.moveToThread(self._thread)
        # connect worker signals
        self._worker.connectionReady.connect(self._handle_connection_ready)
        self._worker.tablesReady.connect(self._handle_tables_ready)
        self._worker.dataReady.connect(self.dataReady.emit)
        self._worker.mappedDataReady.connect(self.mappedDataReady.emit)
        self._worker.error.connect(self.error.emit)
        self._worker.connectionFailed.connect(self.connectionFailed.emit)
        # connect start working signals
        self.startTableGet.connect(self._worker.tables)
        self.startDataGet.connect(self._worker.data)
        self.startMappedDataGet.connect(self._worker.mapped_data)
        self.closeConnection.connect(self._worker.disconnect)

        # when thread is started, connect worker to source
        self._thread.started.connect(self._worker.init_connection)
        self._thread.start()

    def _handle_connection_ready(self):
        self._is_connected = True
        self.connectionReady.emit()

    def _handle_tables_ready(self, table_options):
        if isinstance(table_options, list):
            table_options = {name: {} for name in table_options}

        # save table options if they don't already exists
        for key, table_settings in table_options.items():
            options = table_settings.get("options", {})
            if options is not None:
                self._table_options.setdefault(key, options)

        # save table types if they don't already exists
        for key, table_settings in table_options.items():
            types = table_settings.get("types", {})
            if types is not None:
                self._table_types.setdefault(key, types)

        # save table row types if they don't already exists
        for key, table_settings in table_options.items():
            row_types = table_settings.get("row_types", {})
            if row_types is not None:
                self._table_row_types.setdefault(key, row_types)

        tables = {k: t.get("mapping", None) for k, t in table_options.items()}
        self.tablesReady.emit(tables)
        # update options if a sheet is selected
        if self._current_table and self._current_table in self._table_options:
            self._options_widget.set_options(self._table_options[self._current_table])

    def _new_options(self):
        if self._current_table:
            options = self._options_widget.get_options()
            self._table_options.update({self._current_table: options})
        self.request_data(self._current_table, 100)

    def set_table_options(self, options):
        """Sets connection manager options for current connector

        Arguments:
            options {dict} -- Dict with option settings
        """
        self._table_options.update(options)
        if self._current_table:
            self._options_widget.set_options(options=self._table_options.get(self._current_table, {}))

    def set_table_types(self, types):
        """Sets connection manager types for current connector

        Arguments:
            types {dict} -- Dict with types settings, column (int) as key, type as value
        """
        self._table_types.update(types)

    def set_table_row_types(self, types):
        """Sets connection manager types for current connector

        Arguments:
            types {dict} -- Dict with types settings, row (int) as key, type as value
        """
        self._table_row_types.update(types)

    def option_widget(self):
        """
        Return a Qwidget with options for reading data from a table in source
        """
        return self._options_widget

    def close_connection(self):
        """Close and delete thread and worker
        """
        self._is_connected = False
        self.closeConnection.emit()
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        if self._thread:
            self._thread.quit()
            self._thread.wait()


class ConnectionWorker(QObject):
    """A class for delegating SourceConnection operations to another QThread.

    Args:
        source (str): path of the source file
        connection (class): A class derived from `SourceConnection` for connecting to the source file
    """

    # Signal with error message if connection fails
    connectionFailed = Signal(str)
    # Signal with error message if something errors
    error = Signal(str)
    # Signal that connection is ready to be read
    connectionReady = Signal()
    # Signal when tables from source is ready, list of tablenames
    tablesReady = Signal(list)
    # Signal when data from a specific table in source is ready, list of data and list of headers
    dataReady = Signal(list, list)
    # Signal when data is read an mapped, dict with data and list of errors when reading data with mappings
    mappedDataReady = Signal(dict, list)

    def __init__(self, source, connection, parent=None):
        super(ConnectionWorker, self).__init__(parent)
        self._source = source
        self._connection = connection()

    def init_connection(self):
        """
        Connect to data source
        """
        if self._source:
            try:
                self._connection.connect_to_source(self._source)
                self.connectionReady.emit()
            except Exception as error:
                self.connectionFailed.emit(f"Could not connect to source: {error}")
                raise error
        else:
            self.connectionFailed.emit("Connection has no source")

    def tables(self):
        try:
            tables = self._connection.get_tables()
            self.tablesReady.emit(tables)
        except Exception as error:
            self.error.emit(f"Could not get tables from source: {error}")
            raise error

    def data(self, table, options, max_rows):
        try:
            data, header = self._connection.get_data(table, options, max_rows)
            self.dataReady.emit(data, header)
        except Exception as error:
            self.error.emit(f"Could not get data from source: {error}")
            raise error

    def mapped_data(self, table_mappings, options, types, table_row_types, max_rows):
        try:
            data, errors = self._connection.get_mapped_data(table_mappings, options, types, table_row_types, max_rows)
            self.mappedDataReady.emit(data, errors)
        except Exception as error:
            self.error.emit(f"Could not get mapped data from source: {error}")
            raise error

    def disconnect(self):
        try:
            self._connection.disconnect()
        except Exception as error:
            self.error.emit(f"Could not disconnect from source: {error}")
            raise error
