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
Contains JSONConnector class.

:author: M. Marin (KTH)
:date:   10.2.2020
"""

import sys
import os
import ijson
from PySide2.QtWidgets import QFileDialog
from ..io_api import SourceConnection


def select_json_file(parent=None):
    """
    Launches QFileDialog with .json filter
    """
    return QFileDialog.getOpenFileName(parent, "", "*.json")


class JSONConnector(SourceConnection):
    """Template class to read data from another QThread."""

    # name of data source, ex: "Text/CSV"
    DISPLAY_NAME = "JSON"

    # dict with option specification for source.
    OPTIONS = {"max_depth": {'type': int, 'label': 'Maximum depth', 'default': 8}}

    # Modal widget that that returns source object and action (OK, CANCEL)
    SELECT_SOURCE_UI = select_json_file

    def __init__(self):
        super().__init__()
        self._filename = None
        self._root_prefix = None

    def connect_to_source(self, source):
        """saves filepath

        Arguments:
            source {str} -- filepath
        """
        self._filename = source
        self._root_prefix = os.path.splitext(os.path.basename(source))[0]

    def disconnect(self):
        """Disconnect from connected source.
        """

    def get_tables(self):
        prefixes = dict()
        with open(self._filename) as f:
            for prefix, event, _ in ijson.parse(f):
                if event in ("start_map", "start_array"):
                    prefixes[".".join([self._root_prefix, prefix])] = None
        return [self._root_prefix] + list(prefixes.keys())[1:]

    def file_iterator(self, table, options, max_rows=-1):
        if max_rows == -1:
            max_rows = sys.maxsize
        max_depth = options["max_depth"]
        prefix = ".".join(table.split(".")[1:])
        with open(self._filename) as f:
            row = 0
            for obj in ijson.items(f, prefix):
                for x in _tabulize_json(obj):
                    if row > max_rows:
                        return
                    yield x[:max_depth]
                    row += 1

    def get_data_iterator(self, table, options, max_rows=-1):
        """
        Return data read from data source table in table. If max_rows is
        specified only that number of rows.
        """
        return self.file_iterator(table, options, max_rows=max_rows), [], options["max_depth"]


def _tabulize_json(obj):
    if isinstance(obj, dict):
        yield from _tabulize_json_object(obj)
    elif isinstance(obj, list):
        yield from _tabulize_json_array(obj)
    else:
        yield [obj]


def _tabulize_json_object(obj):
    for key, value in obj.items():
        for x in _tabulize_json(value):
            yield [key] + x


def _tabulize_json_array(arr):
    for i, item in enumerate(arr):
        for x in _tabulize_json(item):
            yield [i] + x
