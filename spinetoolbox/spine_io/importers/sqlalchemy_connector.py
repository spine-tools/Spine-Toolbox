# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from PySide2.QtWidgets import QInputDialog

from spine_io.io_api import SourceConnection


def select_csv_file(parent=None):
    """
    Launches QFileDialog with .txt filter
    """
    return QInputDialog.getText(parent, "SqlAlchemy", "SqlAlchemy connection string:")


class SqlAlchemyConnector(SourceConnection):
    """
    Template class to read data from another QThread
    """

    # name of data source, ex: "Text/CSV"
    DISPLAY_NAME = "SqlAlchemy"

    # dict with option specification for source.
    OPTIONS = {}

    # Modal widget that that returns source object and action (OK, CANCEL)
    SELECT_SOURCE_UI = select_csv_file

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
        
        Raises:
            NotImplementedError: [description]
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
