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
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
from PySide2.QtCore import QCoreApplication
from spine_engine import ExecutionDirection
from spinetoolbox.project_items.gimlet.executable_item import ExecutableItem
from spinetoolbox.project_item_resource import ProjectItemResource


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

    @unittest.skipIf(sys.platform != "win32", "Windows test")
    def test_execute_backward(self):
        executable = ExecutableItem("name", mock.MagicMock(), "cmd.exe", ["cd"], "", selected_files=[])
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))

    @unittest.skipIf(sys.platform != "win32", "Windows test")
    def test_execute_forward1(self):
        """Test executing command 'cd' in cmd.exe."""
        with TemporaryDirectory() as temp_dir:
            executable = ExecutableItem("name", mock.MagicMock(), "cmd.exe", ["cd"], temp_dir, selected_files=[])
            self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))

    @unittest.skipIf(sys.platform != "win32", "Windows test")
    def test_execute_forward2(self):
        """Test that bash shell execution fails on Windows."""
        with TemporaryDirectory() as temp_dir:
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

        # specification.cmdline_args = ["@@url:ds1@@"]
        # args = specification.get_cmdline_args([], {"ds1": "sqlite:///Q:\\databases\\base.sqlite"}, {})
        # self.assertEqual(args, ["sqlite:///Q:\\databases\\base.sqlite"])
        # specification.cmdline_args = ["--url=@@url:ds1@@"]
        # args = specification.get_cmdline_args([], {}, {"ds1": "sqlite:///Q:\\databases\\base.sqlite"})
        # self.assertEqual(args, ["--url=sqlite:///Q:\\databases\\base.sqlite"])


class FakeProvider:
    def __init__(self, name):
        self.name = name


if __name__ == '__main__':
    unittest.main()
