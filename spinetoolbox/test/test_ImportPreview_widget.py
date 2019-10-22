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
Contains unit tests for ImportPreviewWidget.

:author: A. Soininen (VTT)
:date:   22.10.2019
"""

import csv
import os.path
from tempfile import TemporaryDirectory
import unittest
from PySide2.QtWidgets import QApplication, QWidget
from ..spine_io.connection_manager import ConnectionManager
from ..spine_io.importers.csv_reader import CSVConnector
from ..widgets.import_preview_widget import ImportPreviewWidget


class TestImportPreviewWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_missing_data_in_preview_table(self):
        class Selection:
            def __init__(self, file_path):
                self._text = file_path

            def text(self):
                return self._text

        with TemporaryDirectory() as data_directory:
            file_path = os.path.join(data_directory, "test_missing_data_in_preview_table.csv")
            with open(file_path, "w", newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(['a', 'b'])
                writer.writerow(['only'])
                writer.writerow(['d', 'e'])
            connection = ConnectionManager(CSVConnector)
            connection.source = file_path
            parent = QWidget()
            widget = ImportPreviewWidget(connection, parent)
            settings = {
                "table_mappings": {file_path: [{"map_type": "ObjectClass"}]},
                "table_options": {},
                "selected_tables": [],
                "source_type": ["CSVConnector"],
            }
            widget.use_settings(settings)
            connection.init_connection()
            QApplication.processEvents()
            QApplication.processEvents()
            widget.select_table(Selection(file_path))
            QApplication.processEvents()
            QApplication.processEvents()
            table = widget.table
            self.assertEqual(table.rowCount(), 3)
            self.assertEqual(table.columnCount(), 2)
            self.assertEqual(table.index(0, 0).data(), 'a')
            self.assertEqual(table.index(0, 1).data(), 'b')
            self.assertEqual(table.index(1, 0).data(), 'only')
            self.assertEqual(table.index(1, 1).data(), None)
            self.assertEqual(table.index(2, 0).data(), 'd')
            self.assertEqual(table.index(2, 1).data(), 'e')


if __name__ == '__main__':
    unittest.main()
