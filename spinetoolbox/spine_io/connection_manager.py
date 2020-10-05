######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Items.
# Spine Items is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
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

from PySide2.QtCore import QObject, QThread, Signal, Slot


class ConnectionManager(QObject):
    """Class to manage data connections in another thread.

    Args:
        connection (class): A class derived from `SourceConnection`, e.g. `CSVConnector`
    """

    start_table_get = Signal()
    start_data_get = Signal(str, dict, int)
    start_mapped_data_get = Signal(dict, dict, dict, dict, int)

    # Signal with error message if connection fails
    connection_failed = Signal(str)

    # Signal that a connection to the datasource is ready
    connection_ready = Signal()

    # Signal that connection is being closed
    connection_closed = Signal()

    # error while reading data or connection to data source
    error = Signal(str)

    # signal that the data connection is getting data
    fetching_data = Signal()

    # data from source is ready, should send list of data and headers
    data_ready = Signal(list, list)

    # tables from source is ready, should send a list of str of available tables
    tables_ready = Signal(dict)

    # mapped data read from data source
    mapped_data_ready = Signal(dict, list)

    current_table_changed = Signal()
    """Emitted when the current table has changed."""

    def __init__(self, connection, connection_settings, parent=None):
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._source = None
        self._current_table = None
        self._table_options = {}
        self._table_types = {}
        self._table_row_types = {}
        self._connection = connection
        self._connection_settings = connection_settings
        self._is_connected = False

    @property
    def connection(self):
        return self._connection

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

        Args:
            table (str): table name
        """
        # check if table has options
        self._current_table = table
        self.current_table_changed.emit()

    def request_tables(self):
        """Get tables tables from source, emits two singals,
        fetchingData: ConnectionManager is busy waiting for data
        startTableGet: a signal that the worker in another thread is listening
        to know when to run get a list of table names.
        """
        if self.is_connected:
            self.fetching_data.emit()
            self.start_table_get.emit()

    def request_data(self, table=None, max_rows=-1):
        """Request data from emits dataReady to with data

        Keyword Arguments:
            table {str} -- which table to get data from (default: {None})
            max_rows {int} -- how many rows to read (default: {-1})
        """
        if self.is_connected:
            options = self._table_options.get(self._current_table, {})
            self.fetching_data.emit()
            self.start_data_get.emit(table, options, max_rows)

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
            for table_name in table_mappings:
                options[table_name] = self._table_options.get(table_name, {})
                types.setdefault(table_name, self._table_types.get(table_name, {}))
                row_types.setdefault(table_name, self._table_row_types.get(table_name, {}))
            self.fetching_data.emit()
            self.start_mapped_data_get.emit(table_mappings, options, types, row_types, max_rows)

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
        self._worker = ConnectionWorker(self._source, self._connection, self._connection_settings)
        self._worker.moveToThread(self._thread)
        # connect worker signals
        self._worker.connectionReady.connect(self._handle_connection_ready)
        self._worker.tablesReady.connect(self._handle_tables_ready)
        self._worker.dataReady.connect(self.data_ready.emit)
        self._worker.mappedDataReady.connect(self.mapped_data_ready.emit)
        self._worker.error.connect(self.error.emit)
        self._worker.connectionFailed.connect(self.connection_failed.emit)
        # connect start working signals
        self.start_table_get.connect(self._worker.tables)
        self.start_data_get.connect(self._worker.data)
        self.start_mapped_data_get.connect(self._worker.mapped_data)
        self.connection_closed.connect(self._worker.disconnect)

        # when thread is started, connect worker to source
        self._thread.started.connect(self._worker.init_connection)
        self._thread.start()

    def _handle_connection_ready(self):
        self._is_connected = True
        self.connection_ready.emit()

    @Slot("QVariant")
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
        self.tables_ready.emit(tables)
        # update options if a sheet is selected
        if self._current_table in self._table_options:
            self.current_table_changed.emit()

    @Slot()
    def update_options(self, options):
        if not self._current_table:
            return
        self._table_options.setdefault(self._current_table, {}).update(options)
        self.request_data(self._current_table, 100)

    def get_current_options(self):
        if not self._current_table:
            return {}
        return self._table_options.get(self._current_table, {})

    def get_current_option_value(self, option_key):
        """Returns the value for option_key for the current table or the default value."""
        current_options = self._table_options.get(self._current_table, {})
        option_value = current_options.get(option_key)
        if option_value is None:
            option_specification = self._connection.OPTIONS[option_key]
            return option_specification["default"]
        return option_value

    def set_table_options(self, options):
        """Sets connection manager options for current connector

        Args:
            options (dict): settings for the tables
        """
        self._table_options.update(options)
        if self._current_table in self._table_options:
            self.current_table_changed.emit()

    def set_table_types(self, types):
        """Sets connection manager types for current connector

        Args:
            types (dict): dict with types settings, column (int) as key, type as value
        """
        self._table_types.update(types)

    def set_table_row_types(self, types):
        """Sets connection manager types for current connector

        Arguments:
            types {dict} -- Dict with types settings, row (int) as key, type as value
        """
        self._table_row_types.update(types)

    def close_connection(self):
        """Closes and deletes thread and worker
        """
        self._is_connected = False
        self.connection_closed.emit()
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
    # Signal when data is read and mapped, dict with data and list of errors when reading data with mappings
    mappedDataReady = Signal(dict, list)

    def __init__(self, source, connection, connection_settings, parent=None):
        super().__init__(parent)
        self._source = source
        self._connection = connection(connection_settings)

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
