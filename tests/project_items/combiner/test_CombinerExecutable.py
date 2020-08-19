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
Unit tests for CombinerExecutable.

:authors: A. Soininen (VTT), P. Savolainen (VTT)
:date:    13.8.2020
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtCore import QCoreApplication
from spinedb_api import create_new_spine_database, DatabaseMapping, DiffDatabaseMapping, import_functions
from spine_engine import ExecutionDirection
from spinetoolbox.project_item_resource import ProjectItemResource
from spinetoolbox.project_items.combiner.executable_item import ExecutableItem


class TestCombinerExecutable(unittest.TestCase):
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
        self.assertEqual(ExecutableItem.item_type(), "Combiner")

    def test_execute_backward(self):
        # name, logs_dir, cancel_on_error, logger
        executable = ExecutableItem("name", "", True, mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))
        # Check that _loop, _worker, and _worker_thread are None after execution
        self.assertIsNone(executable._worker)
        self.assertIsNone(executable._worker_thread)
        self.assertIsNone(executable._loop)

    def test_execute_forward_simplest_case(self):
        executable = ExecutableItem("name", "", True, mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))
        # Check that _loop, _worker, and _worker_thread are None after execution
        self.assertIsNone(executable._worker)
        self.assertIsNone(executable._worker_thread)
        self.assertIsNone(executable._loop)

    def test_execute_forward_merge_two_dbs(self):
        """Creates two db's with some data and merges them to a third db."""
        with TemporaryDirectory() as temp_dir:
            db1_path = Path(temp_dir).joinpath("db1.sqlite")
            db1_url = 'sqlite:///' + str(db1_path)
            create_new_spine_database(db1_url)
            # Add some data to db1
            db1_map = DiffDatabaseMapping(db1_url)
            import_functions.import_object_classes(db1_map, ["a"])
            import_functions.import_objects(db1_map, [("a", "a_1")])
            # Commit to db1
            db1_map.commit_session("Add an object class 'a' and an object for unit tests.")
            db2_path = Path(temp_dir).joinpath("db2.sqlite")
            db2_url = 'sqlite:///' + str(db2_path)
            create_new_spine_database(db2_url)
            # Add some data to db2
            db2_map = DiffDatabaseMapping(db2_url)
            import_functions.import_object_classes(db2_map, ["b"])
            import_functions.import_objects(db2_map, [("b", "b_1")])
            # Commit to db2
            db2_map.commit_session("Add an object class 'b' and an object for unit tests.")
            # Close connections
            db1_map.connection.close()
            db2_map.connection.close()
            # Make an empty output db
            db3_path = Path(temp_dir).joinpath("db3.sqlite")
            db3_url = 'sqlite:///' + str(db3_path)
            create_new_spine_database(db3_url)
            executable = ExecutableItem("name", temp_dir, True, mock.MagicMock())
            input_db_resources = [
                ProjectItemResource(None, "database", db1_url),
                ProjectItemResource(None, "database", db2_url),
            ]
            output_db_resource = [ProjectItemResource(None, "database", db3_url)]
            self.assertTrue(executable.execute(output_db_resource, ExecutionDirection.BACKWARD))
            self.assertTrue(executable.execute(input_db_resources, ExecutionDirection.FORWARD))
            # Check that _loop, _worker, and _worker_thread are None after execution
            self.assertIsNone(executable._worker)
            self.assertIsNone(executable._worker_thread)
            self.assertIsNone(executable._loop)
            # Check output db
            output_db_map = DatabaseMapping(db3_url)
            class_list = output_db_map.object_class_list().all()
            self.assertEqual(len(class_list), 2)
            self.assertEqual(class_list[0].name, "a")
            self.assertEqual(class_list[1].name, "b")
            object_list_a = output_db_map.object_list(class_id=class_list[0].id).all()
            self.assertEqual(len(object_list_a), 1)
            self.assertEqual(object_list_a[0].name, "a_1")
            object_list_b = output_db_map.object_list(class_id=class_list[1].id).all()
            self.assertEqual(len(object_list_b), 1)
            self.assertEqual(object_list_b[0].name, "b_1")
            output_db_map.connection.close()


if __name__ == '__main__':
    unittest.main()
