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
Contains GDXConnector class and a help function.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from enum import Enum
from collections import defaultdict
import sys
from PySide2.QtWidgets import QFileDialog
from spine_io.io_api import SourceConnection

IMPORT_ERROR = ""
try:
    import gdxcc

    class GamsDataType(Enum):
        Set = gdxcc.GMS_DT_SET
        Parameter = gdxcc.GMS_DT_PAR
        Variable = gdxcc.GMS_DT_VAR
        Equation = gdxcc.GMS_DT_EQU
        Alias = gdxcc.GMS_DT_ALIAS

    class GamsValueType(Enum):
        Level = gdxcc.GMS_VAL_LEVEL  # .l
        Marginal = gdxcc.GMS_VAL_MARGINAL  # .m
        Lower = gdxcc.GMS_VAL_LOWER  # .lo
        Upper = gdxcc.GMS_VAL_UPPER  # .ub
        Scale = gdxcc.GMS_VAL_SCALE  # .scale

    GAMS_VALUE_COLS_MAP = defaultdict(lambda: [('Value', GamsValueType.Level.value)])
    GAMS_VALUE_COLS_MAP[GamsDataType.Variable] = [(value_type.name, value_type.value) for value_type in GamsValueType]
    GAMS_VALUE_COLS_MAP[GamsDataType.Equation] = GAMS_VALUE_COLS_MAP[GamsDataType.Variable]
except ImportError as err:
    IMPORT_ERROR = err


def select_csv_file(parent=None):
    """
    Launches QFileDialog with .txt filter
    """
    return QFileDialog.getOpenFileName(parent, "", "*.gdx")


class GdxConnector(SourceConnection):
    """
    Template class to read data from another QThread
    """

    # name of data source, ex: "Text/CSV"
    DISPLAY_NAME = "Gdx"

    # dict with option specification for source.
    OPTIONS = {}

    # Modal widget that that returns source object and action (OK, CANCEL)
    SELECT_SOURCE_UI = select_csv_file

    def __init__(self):
        super(GdxConnector, self).__init__()
        self._filename = None
        self._handle = None
        self._file_handle = None
        self._gams_dir = r"c:\GAMS\win64\27.2"

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def __del__(self):
        self.disconnect()

    def connect_to_source(self, source):
        """saves filepath
        
        Arguments:
            source {str} -- filepath
        """
        # create gdx pointer
        if "gdxcc" not in sys.modules:
            raise IOError(
                f"Could not find gdxcc, make sure that you have installed the gams python plugin. Error message: {IMPORT_ERROR}"
            )

        self._filename = source
        self._handle = gdxcc.new_gdxHandle_tp()
        rc = gdxcc.gdxCreateD(self._handle, self._gams_dir, gdxcc.GMS_SSSIZE)
        if not rc:
            self._handle = None
            self._filename = None
            msg = (
                "Could not create Gdx object: "
                + rc[1]
                + " "
                + gdxcc.gdxErrorStr(self._handle, gdxcc.gdxGetLastError(self._handle))[1]
                + "."
            )
            raise IOError(msg)

        rc = gdxcc.gdxOpenRead(self._handle, self._filename)
        if not rc[0]:
            self._handle = None
            self._filename = None
            raise IOError(f"Could not open file {self._filename}")

    def disconnect(self):
        """Disconnect from connected source.
        """
        if self._handle:
            gdxcc.gdxFree(self._handle)
            self._handle = None

    def get_tables(self):
        """Method that should return a list of table names, list(str)
        
        Raises:
            NotImplementedError: [description]
        """
        tables = []
        _ret, symbol_count, _element_count = gdxcc.gdxSystemInfo(self._handle)
        for i in range(symbol_count):
            _ret, name, _dims, _data_type = gdxcc.gdxSymbolInfo(self._handle, i)
            tables.append(name)

        return tables

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
        _ret, symbol_count, _element_count = gdxcc.gdxSystemInfo(self._handle)

        symbol_found = False
        symbol_index = None
        header = []
        for i in range(symbol_count):
            _ret, name, _dims, data_type = gdxcc.gdxSymbolInfo(self._handle, i)
            if name == table:
                symbol_found = True
                symbol_index = i
                _ret, gdx_domain = gdxcc.gdxSymbolGetDomainX(self._handle, i)
                header = list(gdx_domain)
                data_type = GamsDataType(data_type)
                break
        if not symbol_found:
            return iter([]), [], 0

        _ret, records = gdxcc.gdxDataReadStrStart(self._handle, symbol_index)
        if data_type == GamsDataType.Set:

            def gdx_data():
                for _ in range(records):
                    _ret, elements, _values, _afdim = gdxcc.gdxDataReadStr(self._handle)
                    yield elements

        else:
            header = header + [col_name for col_name, col_ind in GAMS_VALUE_COLS_MAP[data_type]]

            def gdx_data():
                for _ in range(records):
                    _ret, elements, values, _afdim = gdxcc.gdxDataReadStr(self._handle)
                    yield elements + [values[col_ind] for col_name, col_ind in GAMS_VALUE_COLS_MAP[data_type]]

        return gdx_data(), header, len(header)
