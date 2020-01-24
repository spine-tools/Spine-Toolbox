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
Contains unit tests for CSVConnector.

:author: A. Soininen (VTT)
:date:   22.10.2019
"""

import csv
import os.path
from tempfile import TemporaryDirectory
import unittest
from spinetoolbox.spine_io.importers.csv_reader import CSVConnector


class TestCSVConnector(unittest.TestCase):
    @staticmethod
    def _write_basic_csv(file_name):
        with open(file_name, "w", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['1a', '1b', '1c'])
            writer.writerow(['2a', '2b', '2c'])

    def test_get_tables(self):
        with TemporaryDirectory() as data_directory:
            file_name = os.path.join(data_directory, "test_get_tables.csv")
            self._write_basic_csv(file_name)
            connector = CSVConnector()
            connector.connect_to_source(file_name)
            tables = connector.get_tables()
            self.assertEqual(len(tables), 1)
            self.assertTrue("csv" in tables)
            options = tables["csv"]["options"]
            self.assertEqual(options["encoding"], "ascii")
            self.assertEqual(options["delimiter"], ",")
            self.assertEqual(options["quotechar"], '"')
            self.assertEqual(options["skip"], 0)
            self.assertTrue(not "has_header" in options)

    def test_get_data_iterator(self):
        with TemporaryDirectory() as data_directory:
            file_name = os.path.join(data_directory, "test_get_data_iterator.csv")
            self._write_basic_csv(file_name)
            connector = CSVConnector()
            connector.connect_to_source(file_name)
            tables = connector.get_tables()
            options = tables["csv"]["options"]
            _, header, num_cols = connector.get_data_iterator("", options)
            self.assertTrue(not header)
            self.assertEqual(num_cols, 3)

    def test_get_data(self):
        with TemporaryDirectory() as data_directory:
            file_name = os.path.join(data_directory, "test_get_data.csv")
            self._write_basic_csv(file_name)
            connector = CSVConnector()
            connector.connect_to_source(file_name)
            tables = connector.get_tables()
            options = tables["csv"]["options"]
            data, header = connector.get_data("", options)
            self.assertTrue(not header)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0], ['1a', '1b', '1c'])
            self.assertEqual(data[1], ['2a', '2b', '2c'])


if __name__ == '__main__':
    unittest.main()
