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
Unit tests for Gimlet ExecutableItem.

:author: P. Savolainen (VTT)
:date:   25.5.2020
"""
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
from PySide2.QtCore import QCoreApplication
from spine_engine import ExecutionDirection
from spinetoolbox.project_items.gimlet.executable_item import ExecutableItem
from spinetoolbox.project_item_resource import ProjectItemResource
from spinetoolbox.execution_managers import QProcessExecutionManager


class TestGimletExecutable(unittest.TestCase):
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
        self.assertEqual(ExecutableItem.item_type(), "Gimlet")

    def test_from_dict(self):
        selections = [
            [{"type": "path", "relative": True, "path": ".spinetoolbox/items/input_files/a.txt"}, True],
            [{"type": "path", "relative": True, "path": ".spinetoolbox/items/input_files/b.txt"}, False],
        ]
        item_dict = {
            "type": "Gimlet",
            "x": 0,
            "y": 0,
            "description": "",
            "use_shell": True,
            "shell_index": 0,
            "cmd": "dir",
            "selections": selections,
            "work_dir_mode": True,
        }
        mock_settings = _MockSettings()
        with TemporaryDirectory() as temp_dir:
            item = ExecutableItem.from_dict(
                item_dict,
                name="G",
                project_dir=temp_dir,
                app_settings=mock_settings,
                specifications=dict(),
                logger=mock.MagicMock(),
            )
            self.assertIsInstance(item, ExecutableItem)
            self.assertEqual("Gimlet", item.item_type())
            self.assertEqual("cmd.exe", item.shell_name)
            self.assertTrue(os.path.join(temp_dir, "G", "work"), item._work_dir)
            self.assertIsInstance(item._selected_files, list)
            self.assertEqual(item.cmd_list, ["dir"])
            # Modify item_dict
            item_dict["use_shell"] = False
            item_dict["work_dir_mode"] = False
            item = ExecutableItem.from_dict(
                item_dict,
                name="G",
                project_dir=temp_dir,
                app_settings=mock_settings,
                specifications=dict(),
                logger=mock.MagicMock(),
            )
            self.assertIsInstance(item, ExecutableItem)
            self.assertEqual("Gimlet", item.item_type())
            self.assertEqual("", item.shell_name)
            prefix, work_dir_name = os.path.split(item._work_dir)
            self.assertEqual("some_path", prefix)
            self.assertEqual("g__", work_dir_name[0:3])  # work dir name must start with 'g__'
            self.assertEqual("__toolbox", work_dir_name[-9:])  # work dir name must end with '__toolbox'
            self.assertEqual(
                [os.path.abspath(os.path.join(temp_dir, ".spinetoolbox/items/input_files/a.txt"))], item._selected_files
            )
            # Modify item_dict
            item_dict["use_shell"] = True
            item_dict["shell_index"] = 99  # Unsupported shell
            item = ExecutableItem.from_dict(
                item_dict,
                name="G",
                project_dir=temp_dir,
                app_settings=mock_settings,
                specifications=dict(),
                logger=mock.MagicMock(),
            )
            self.assertIsNone(item)

    @unittest.skipIf(sys.platform != "win32", "Windows test")
    def test_execute_backward(self):
        executable = ExecutableItem("name", mock.MagicMock(), "cmd.exe", ["cd"], "", selected_files=[])
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))

    @unittest.skipIf(sys.platform != "win32", "Windows test")
    def test_execute_forward(self):
        with TemporaryDirectory() as temp_dir:
            # Test executing command 'cd' in cmd.exe.
            executable = ExecutableItem("name", mock.MagicMock(), "cmd.exe", ["cd"], temp_dir, selected_files=[])
            self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))
            # Test that bash shell execution fails on Windows.
            executable = ExecutableItem("name", mock.MagicMock(), "bash", ["ls"], temp_dir, selected_files=[])
            self.assertFalse(executable.execute([], ExecutionDirection.FORWARD))

    def test_output_resources_backward(self):
        executable = ExecutableItem("name", mock.MagicMock(), "cmd.exe", ["cd"], "", selected_files=[])
        self.assertEqual(executable.output_resources(ExecutionDirection.BACKWARD), [])

    def test_output_resources_forward(self):
        with TemporaryDirectory() as temp_dir:
            executable = ExecutableItem("name", mock.MagicMock(), "cmd.exe", ["cd"], temp_dir, selected_files=[])
            self.assertEqual(executable.output_resources(ExecutionDirection.FORWARD), [])

    def test_expand_gimlet_tags(self):

        with TemporaryDirectory() as temp_dir:
            executable = ExecutableItem("name", mock.MagicMock(), "cmd.exe", ["cd"], temp_dir, selected_files=[])
            expanded = executable._expand_gimlet_tags(["a"], [])
            self.assertEqual(["a"], expanded)
            expanded = executable._expand_gimlet_tags(["a", "b"], [])
            self.assertEqual(["a", "b"], expanded)

            # Make predecessor resources
            db1_path = Path(temp_dir).joinpath("input_db1.sqlite")
            db1_url = 'sqlite:///' + str(db1_path)
            db2_path = Path(temp_dir).joinpath("input_db2.sqlite")
            db2_url = 'sqlite:///' + str(db2_path)
            db3_path = Path(temp_dir).joinpath("output_db.sqlite")
            db3_url = 'sqlite:///' + str(db3_path)
            resources = [
                ProjectItemResource(FakeProvider("DATA STORE 1"), "database", db1_url),
                ProjectItemResource(FakeProvider("DATA STORE 2"), "database", db2_url),
            ]
            # Add a resource for the executable that comes from a successor Data Store
            executable._successor_resources = [ProjectItemResource(FakeProvider("DATA STORE 3"), "database", db3_url)]
            expanded = executable._expand_gimlet_tags(["@@url_inputs@@"], resources)
            self.assertEqual([db1_url, db2_url], expanded)
            expanded = executable._expand_gimlet_tags(["@@url_inputs@@", "@@url_outputs@@"], resources)
            self.assertEqual([db1_url, db2_url, db3_url], expanded)

            expanded = executable._expand_gimlet_tags(["@@url:DATA STORE 1@@"], resources)
            self.assertEqual([db1_url], expanded)
            expanded = executable._expand_gimlet_tags(["@@url:DATA STORE 1@@", "@@url:DATA STORE 3@@"], resources)
            self.assertEqual([db1_url, db3_url], expanded)
            expanded = executable._expand_gimlet_tags(["@@url_inputs@@", "@@url:DATA STORE 2@@"], resources)
            self.assertEqual([db1_url, db2_url, db2_url], expanded)
            expanded = executable._expand_gimlet_tags(["a", "-z", "@@url:DATA STORE 3@@", "--output"], resources)
            self.assertEqual(["a", "-z", db3_url, "--output"], expanded)

    def test_stop_execution(self):
        logger = mock.MagicMock()
        prgm = "cmd.exe"
        cmd_list = ["dir"]
        executable = ExecutableItem("name", logger, prgm, cmd_list, "", selected_files=[])
        executable._gimlet_process = QProcessExecutionManager(logger, prgm, cmd_list)
        executable.stop_execution()
        self.assertIsNone(executable._gimlet_process)


class FakeProvider:
    def __init__(self, name):
        self.name = name


class _MockSettings:
    @staticmethod
    def value(key, defaultValue=None):
        return {"appSettings/workDir": "some_path"}.get(key, defaultValue)


if __name__ == '__main__':
    unittest.main()
