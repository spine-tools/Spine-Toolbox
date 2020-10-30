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
Contains GDXConnector class and a help function.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from gdx2py import GdxFile, GAMSParameter, GAMSScalar, GAMSSet
from ..io_api import SourceConnection
from ..gdx_utils import find_gams_directory


class GdxConnector(SourceConnection):
    """Template class to read data from another QThread."""

    DISPLAY_NAME = "Gdx"
    """name of data source"""

    OPTIONS = {}
    """dict with option specification for source"""

    FILE_EXTENSIONS = "*.gdx"
    """File extensions for modal widget that returns source object and action (OK, CANCEL)."""

    def __init__(self, settings):
        """
        Args:
            settings (dict): a dict from "gams_directory" to GAMS path; if the argument is None
                or the path is empty or None, a default path is used
        """
        super().__init__(settings)
        self._filename = None
        self._gdx_file = None
        gams_directory = settings.get("gams_directory") if settings is not None else None
        if gams_directory is not None and gams_directory:
            self._gams_dir = gams_directory
        else:
            self._gams_dir = find_gams_directory()

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def __del__(self):
        self.disconnect()

    def connect_to_source(self, source):
        """
        Connects to given .gdx file.

        Args:
            source (str): path to .gdx file.
        """
        if self._gams_dir is None:
            raise IOError(f"Could not find GAMS directory. Make sure you have GAMS installed.")
        self._filename = source
        self._gdx_file = GdxFile(source, gams_dir=self._gams_dir)

    def disconnect(self):
        """Disconnects from connected source."""
        if self._gdx_file is not None:
            self._gdx_file.close()

    def get_tables(self):
        """
        Returns a list of table names.

        GAMS scalars are also regarded as tables.

        Returns:
            list(str): Table names in list
        """
        tables = []
        for symbol in self._gdx_file:
            tables.append(symbol[0])
        return tables

    def get_data_iterator(self, table, options, max_rows=-1):
        """Creates an iterator for the data source

        Arguments:
            table (string): table name
            options (dict): dict with options

        Keyword Arguments:
            max_rows (int): ignored

        Returns:
            tuple: data iterator, list of column names, number of columns
        """
        if table not in self._gdx_file:
            return iter([]), [], 0
        symbol = self._gdx_file[table]
        if isinstance(symbol, GAMSScalar):
            return iter([[float(symbol)]]), ["Value"], 1
        domains = symbol.domain if symbol.domain is not None else symbol.dimension * [None]
        header = [domain if domain is not None else f"dim{i}" for i, domain in enumerate(domains)]
        if isinstance(symbol, GAMSSet):
            if symbol.elements and isinstance(symbol.elements[0], str):
                return iter([[key] for key in symbol.elements]), header, len(header)
            return iter(list(keys) for keys in symbol.elements), header, len(header)
        if isinstance(symbol, GAMSParameter):
            header.append("Value")
            symbol_keys = list(symbol.keys())
            if symbol_keys and isinstance(symbol_keys[0], str):
                return (
                    iter([keys] + [value] for keys, value in zip(symbol_keys, symbol.values())),
                    header,
                    len(header),
                )
            return (
                iter(list(keys) + [value] for keys, value in zip(symbol_keys, symbol.values())),
                header,
                len(header),
            )
        raise RuntimeError("Unknown GAMS symbol type.")
