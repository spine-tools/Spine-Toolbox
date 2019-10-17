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
Contains CSVConnector class and a help function.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""


import csv
from itertools import islice
from PySide2.QtWidgets import QFileDialog
from ..io_api import SourceConnection


def select_csv_file(parent=None):
    """
    Launches QFileDialog with no filter
    """
    return QFileDialog.getOpenFileName(parent, "", "*.*")


class CSVConnector(SourceConnection):
    """Template class to read data from another QThread."""

    # name of data source, ex: "Text/CSV"
    DISPLAY_NAME = "Text/CSV"

    # dict with option specification for source.
    OPTIONS = {
        "delimiter": {'type': str, 'label': 'Delimiter', 'MaxLength': 1, 'default': ','},
        "quotechar": {'type': str, 'label': 'Quotechar', 'MaxLength': 1, 'default': ''},
        "has_header": {'type': bool, 'label': 'Has header', 'default': False},
        "skip": {'type': int, 'label': 'Skip rows', 'Minimum': 0, 'default': 0},
    }

    # Modal widget that returns source object and action (OK, CANCEL)
    SELECT_SOURCE_UI = select_csv_file

    def __init__(self):
        super(CSVConnector, self).__init__()
        self._filename = None

    def connect_to_source(self, source):
        """saves filepath

        Arguments:
            source {str} -- filepath
        """
        self._filename = source

    def disconnect(self):
        """Disconnect from connected source.
        """

    def get_tables(self):
        """Method that should return a list of table names, list(str)

        Returns:
            list(str): Table names in list
        """
        tables = [self._filename]
        return tables

    @staticmethod
    def parse_options(options):
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
        delimiter = options.get("delimiter", ",")
        if not delimiter:
            delimiter = ','
        dialect = {"delimiter": delimiter}
        quotechar = options.get("quotechar", None)
        if quotechar:
            dialect.update({"quotechar": quotechar})
        has_header = options.get("has_header", False)
        skip = options.get("skip", 0)
        return dialect, has_header, skip

    def file_iterator(self, options, max_rows):
        """creates an iterator that reads max_rows number of rows from text file

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
        with open(self._filename) as text_file:
            csv_reader = csv.reader(text_file, **dialect)
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
        # Iterate once to get num_cols
        try:
            first_row = next(csv_iter)
        except StopIteration:
            return iter([]), [], 0
        num_cols = len(first_row)

        _dialect, has_header, _skip = self.parse_options(options)
        if has_header:
            # Very good, we already have the first row
            header = first_row
        else:
            header = []
            # reset iterator
            csv_iter = self.file_iterator(options, max_rows)
        return csv_iter, header, num_cols
