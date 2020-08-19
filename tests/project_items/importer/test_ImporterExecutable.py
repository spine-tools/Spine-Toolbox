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
import time
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtCore import Signal, QCoreApplication, QObject
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
        executable = ExecutableItem("name", {}, "", "", True, mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))
        # Check that _loop, _worker, and _worker_thread are None after execution
        self.assertIsNone(executable._worker)
        self.assertIsNone(executable._worker_thread)
        self.assertIsNone(executable._loop)

    def test_execute_forward_simplest_case(self):
        executable = ExecutableItem("name", {}, "", "", True, mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))
        # Check that _loop, _worker, and _worker_thread are None after execution
        self.assertIsNone(executable._worker)
        self.assertIsNone(executable._worker_thread)
        self.assertIsNone(executable._loop)

    def test_execute_forward_import_small_file(self):
        with TemporaryDirectory() as temp_dir:
            data_file = Path(temp_dir, "data.dat")
            self._write_simple_data(data_file)
            mappings = self._simple_input_data_mappings(str(data_file))
            database_path = Path(temp_dir).joinpath("database.sqlite")
            database_url = 'sqlite:///' + str(database_path)
            create_new_spine_database(database_url)
            gams_path = ""
            executable = ExecutableItem("name", mappings, temp_dir, gams_path, True, mock.MagicMock())
            database_resources = [ProjectItemResource(None, "database", database_url)]
            self.assertTrue(executable.execute(database_resources, ExecutionDirection.BACKWARD))
            file_resources = [ProjectItemResource(None, "file", data_file.as_uri())]
            self.assertTrue(executable.execute(file_resources, ExecutionDirection.FORWARD))
            # Check that _loop, _worker, and _worker_thread are None after execution
            self.assertIsNone(executable._worker)
            self.assertIsNone(executable._worker_thread)
            self.assertIsNone(executable._loop)
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
            executable = ExecutableItem("name", mappings, temp_dir, gams_path, True, mock.MagicMock())
            database_resources = [ProjectItemResource(None, "database", database_url)]
            self.assertTrue(executable.execute(database_resources, ExecutionDirection.BACKWARD))
            file_resources = [ProjectItemResource(None, "file", data_file.as_uri())]
            self.assertTrue(executable.execute(file_resources, ExecutionDirection.FORWARD))
            # Check that _loop, _worker, and _worker_thread are None after execution
            self.assertIsNone(executable._worker)
            self.assertIsNone(executable._worker_thread)
            self.assertIsNone(executable._loop)
            database_map = DatabaseMapping(database_url)
            class_list = database_map.object_class_list().all()
            self.assertEqual(len(class_list), 0)
            database_map.connection.close()

    def test_stop_execution(self):
        """ImporterWorker is replaced with a custom QThread based worker for this test."""
        with mock.patch("spinetoolbox.project_items.importer.executable_item.ImporterWorker") as custom_importer_worker:
            # Replace ImporterWorker
            custom_importer_worker.side_effect = UnitTestImporterWorker
            with TemporaryDirectory() as temp_dir:
                data_file = Path(temp_dir, "data.dat")
                self._write_simple_data(data_file)
                mappings = {data_file: "deselected"}
                database_path = Path(temp_dir).joinpath("database.sqlite")
                database_url = 'sqlite:///' + str(database_path)
                create_new_spine_database(database_url)
                executable = ExecutableItem("name", mappings, temp_dir, "", True, mock.MagicMock())
                database_resources = [ProjectItemResource(None, "database", database_url)]
                self.assertTrue(executable.execute(database_resources, ExecutionDirection.BACKWARD))
                file_resources = [ProjectItemResource(None, "file", data_file.as_uri())]
                self.assertFalse(executable.execute(file_resources, ExecutionDirection.FORWARD))
                custom_importer_worker.assert_called_once()
                executable.stop_execution()
                self.assertIsNone(executable._worker)
                self.assertIsNone(executable._worker_thread)
                self.assertIsNone(executable._loop)

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


class UnitTestImporterWorker(QObject):

    import_finished = Signal(int)

    def __init__(
        self,
        checked_files,
        all_import_settings,
        all_source_settings,
        urls_downstream,
        logs_dir,
        cancel_on_error,
        logger,
    ):
        """
        Args:
            checked_files (list(str)): List of paths to checked source files
            all_import_settings (dict): Maps source file to setting for that file
            all_source_settings (dict): Maps source type to setting for that type
            urls_downstream (list(str)): List of urls to import data into
            logs_dir (str): path to the directory where logs should be written
            cancel_on_error (bool): whether or not to rollback and stop execution if errors
            logger (LoggerInterface): somewhere to log important messages
        """
        super().__init__()
        self._checked_files = checked_files
        self._all_import_settings = all_import_settings
        self._all_source_settings = all_source_settings
        self._urls_downstream = urls_downstream
        self._logs_dir = logs_dir
        self._cancel_on_error = cancel_on_error
        self._logger = logger

    def do_work(self):
        """Does the work and emits import_finished or failed when done."""
        a = 0
        step = 0.05
        while a > 3:
            time.sleep(step)
            a += step
        self.import_finished.emit(-1)


if __name__ == '__main__':
    unittest.main()
