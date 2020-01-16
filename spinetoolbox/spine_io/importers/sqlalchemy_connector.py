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
Contains SqlAlchemyConnector class and a help function.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""


from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from PySide2.QtWidgets import QInputDialog
from ..io_api import SourceConnection


def select_sa_conn_string(parent=None):
    """
    Launches QInputDialog for entering connection string
    """
    return QInputDialog.getText(parent, "SqlAlchemy", "SqlAlchemy connection string:")


class SqlAlchemyConnector(SourceConnection):
    """Template class to read data from another QThread."""

    # name of data source, ex: "Text/CSV"
    DISPLAY_NAME = "SqlAlchemy"

    # dict with option specification for source.
    OPTIONS = {}

    # Modal widget that returns source object and action (OK, CANCEL)
    SELECT_SOURCE_UI = select_sa_conn_string

    def __init__(self):
        super(SqlAlchemyConnector, self).__init__()
        self._connection_string = None
        self._engine = None
        self._connection = None
        self._session = None
        self._metadata = MetaData()

    def connect_to_source(self, source):
        """saves filepath

        Arguments:
            source {str} -- filepath
        """
        self._connection_string = source
        self._engine = create_engine(source)
        self._connection = self._engine.connect()
        self._session = Session(self._engine)
        self._metadata.reflect(bind=self._engine)

    def disconnect(self):
        """Disconnect from connected source.
        """
        self._connection.close()
        self._connection_string = None
        self._engine = None
        self._connection = None
        self._session = None
        self._metadata = MetaData()

    def get_tables(self):
        """Method that should return a list of table names, list(str)

        Returns:
            list(str): Table names in list
        """
        tables = list(self._engine.table_names())
        return tables

    def get_data_iterator(self, table, options, max_rows=-1):
        """Creates a iterator for the file in self.filename

        Arguments:
            table {string} -- table name
            options {dict} -- dict with options, not used

        Keyword Arguments:
            max_rows {int} -- how many rows of data to read, if -1 read all rows (default: {-1})

        Returns:
            [type] -- [description]
        """
        db_table = self._metadata.tables[table]
        header = [str(name) for name in db_table.columns.keys()]
        num_cols = len(header)

        query = self._session.query(db_table)
        if max_rows > 0:
            query = query.limit(max_rows)

        return query, header, num_cols
