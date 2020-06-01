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
Unit tests for ImporterExecutable.

:authors: A. Soininen (VTT)
:date:    6.4.2020
"""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtCore import QCoreApplication
from spinedb_api import create_new_spine_database, DatabaseMapping
from spine_engine import ExecutionDirection
from spinetoolbox.project_item_resource import ProjectItemResource
from spinetoolbox.project_items.importer.executable_item import ExecutableItem


class TestImporterExecutable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QCoreApplication.instance():
            QCoreApplication()
        else:
            # Undo stack's cleanChanged signals might still be on their way if we're running all Toolbox's tests.
            # Here they cause trouble because they try to invoke a method in non-existent ToolboxUI object.
            # To remedy the situation we purge all events from the event queue here.
            QCoreApplication.removePostedEvents(None)

    def test_item_type(self):
        self.assertEqual(ExecutableItem.item_type(), "Importer")

    def test_execute_backward(self):
        executable = ExecutableItem("name", {}, "", "", "", True, mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))

    def test_execute_forward_simplest_case(self):
        executable = ExecutableItem("name", {}, "", "", "", True, mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))

    def test_execute_forward_import_small_file(self):
        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir, "data.dat")
            self._write_simple_data(data_file)
            mappings = self._simple_input_data_mappings(str(data_file))
            database_path = Path(temp_dir).joinpath("database.sqlite")
            database_url = 'sqlite:///' + str(database_path)
            create_new_spine_database(database_url)
            gams_path = ""
            executable = ExecutableItem("name", mappings, temp_dir, sys.executable, gams_path, True, mock.MagicMock())
            database_resources = [ProjectItemResource(None, "database", database_url)]
            self.assertTrue(executable.execute(database_resources, ExecutionDirection.BACKWARD))
            file_resources = [ProjectItemResource(None, "file", data_file.as_uri())]
            self.assertTrue(executable.execute(file_resources, ExecutionDirection.FORWARD))
            database_map = DatabaseMapping(database_url)
            class_list = database_map.object_class_list().all()
            self.assertEqual(len(class_list), 1)
            self.assertEqual(class_list[0].name, "class")
            object_list = database_map.object_list(class_id=class_list[0].id).all()
            self.assertEqual(len(object_list), 1)
            self.assertEqual(object_list[0].name, "entity")
            database_map.connection.close()

    def test_execute_forward_skip_deselected_file(self):
        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir, "data.dat")
            self._write_simple_data(data_file)
            mappings = {data_file: "deselected"}
            database_path = Path(temp_dir).joinpath("database.sqlite")
            database_url = 'sqlite:///' + str(database_path)
            create_new_spine_database(database_url)
            gams_path = ""
            executable = ExecutableItem("name", mappings, temp_dir, sys.executable, gams_path, True, mock.MagicMock())
            database_resources = [ProjectItemResource(None, "database", database_url)]
            self.assertTrue(executable.execute(database_resources, ExecutionDirection.BACKWARD))
            file_resources = [ProjectItemResource(None, "file", data_file.as_uri())]
            self.assertTrue(executable.execute(file_resources, ExecutionDirection.FORWARD))
            database_map = DatabaseMapping(database_url)
            class_list = database_map.object_class_list().all()
            self.assertEqual(len(class_list), 0)
            database_map.connection.close()

    @staticmethod
    def _write_simple_data(file_name):
        with open(file_name, "w") as out_file:
            out_file.write("class,entity\n")

    @staticmethod
    def _simple_input_data_mappings(file_name):
        return {
            file_name: {
                "table_mappings": {
                    "csv": [
                        {
                            "map_type": "ObjectClass",
                            "name": {"map_type": "column", "reference": 0},
                            "parameters": {"map_type": "None"},
                            "skip_columns": [],
                            "read_start_row": 0,
                            "objects": {"map_type": "column", "reference": 1},
                        }
                    ]
                },
                "table_options": {
                    "csv": {
                        "encoding": "ascii",
                        "delimeter": ",",
                        "delimiter_custom": "",
                        "quotechar": '"',
                        "skip_header": False,
                        "skip": 0,
                    }
                },
                "table_types": {"csv": {0: "string", 1: "string"}},
                "table_row_types": {},
                "selected_tables": ["csv"],
                "source_type": "CSVConnector",
            }
        }


if __name__ == '__main__':
    unittest.main()
