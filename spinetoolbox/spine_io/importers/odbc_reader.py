######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains ODBCConnector class.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

import pyodbc
from spine_io.io_api import FileImportTemplate
from PySide2.QtWidgets import (
    QWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QVBoxLayout,
    QInputDialog,
    QErrorMessage,
)
from PySide2.QtCore import QObject, Signal


class ODBCConnector(FileImportTemplate):

    HAS_TABLES = True
    DISPLAY_NAME = 'ODBC'

    def __init__(self):
        super(ODBCConnector, self).__init__()

        self._connection = None
        self._options = {}
        self._option_widget = QWidget()

    def _new_options(self):
        self.refreshDataRequest.emit()

    def set_table(self, table):
        pass

    def source_selector(self, parent=None):
        value, ok = QInputDialog.getText(parent, "ODBC", "ODBC connection string:")
        if not ok and value == '':
            return False
        try:
            self._connection = pyodbc.connect(value)
        except Exception as e:
            self._connection = None
            error_dialog = QErrorMessage()
            error_dialog.showMessage(str(e))
            return False
        return True

    def read_data(self, table, max_rows=100):
        """
        Return data read from data source table in table. If max_rows is 
        specified only that number of rows.
        """
        if not self._connection:
            return [], []

        cursor = self._connection.cursor()

        data = [[row.table_name, row.table_type] for row in cursor.tables()]

        return data, []

    def preview_data(self, table):
        if not table:
            return [], []
        if not table in self.tables:
            return [], []
        cursor = self._connection.cursor()
        cursor.execute(f"SELECT TOP 100 * FROM [{table}]")
        header = [column[0] for column in cursor.description]
        data = [row for row in cursor.fetchall()]
        print(data)
        return data, header

    def option_widget(self):
        """
        Return a Qwidget with options for reading data from a table in source
        """
        return self._option_widget

    @property
    def tables(self):
        if not self._connection:
            return []
        cursor = self._connection.cursor()
        tables = [row.table_name for row in cursor.tables() if row.table_type != "SYSTEM TABLE"]
        return tables
