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
Unit tests for ToolExecutable item.

:author: A. Soininen (VTT)
:date:   2.4.2020
"""
import pathlib
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtCore import QCoreApplication
from spine_engine import ExecutionDirection
from spinetoolbox.project_item import ProjectItemResource
from spinetoolbox.project_items.tool.tool_executable import ToolExecutable
from spinetoolbox.project_items.tool.tool_specifications import ToolSpecification, PythonTool


class TestToolExecutable(unittest.TestCase):
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
        self.assertEqual(ToolExecutable.item_type(), "Tool")

    def test_execute_forward_without_specification_fails(self):
        logger = mock.MagicMock()
        executable = ToolExecutable(
            "executable name", work_dir="", output_dir="", tool_specification=None, cmd_line_args=[], logger=logger
        )
        self.assertFalse(executable.execute([], ExecutionDirection.FORWARD))
        logger.msg_warning.emit.assert_called_with("Tool <b>executable name</b> has no Tool specification to execute")

    def test_execute_forward_archives_output_files(self):
        with TemporaryDirectory() as temp_dir:
            script_dir = pathlib.Path(temp_dir, "scripts")
            script_dir.mkdir()
            script_file_name = self._write_output_script(script_dir)
            script_files = [script_file_name]
            output_files = ["out.dat", "subdir/out.txt"]
            app_settings = _MockSettings()
            logger = mock.MagicMock()
            tool_specification = PythonTool(
                "Python tool",
                "Python",
                str(script_dir),
                script_files,
                app_settings,
                None,
                logger,
                outputfiles=output_files,
            )
            work_dir = pathlib.Path(temp_dir, "work")
            work_dir.mkdir()
            archive_dir = pathlib.Path(temp_dir, "archive")
            archive_dir.mkdir()
            executable = ToolExecutable("Create files", str(work_dir), str(archive_dir), tool_specification, [], logger)
            executable.execute([], ExecutionDirection.FORWARD)
            while executable._tool_instance is not None:
                QCoreApplication.processEvents()
            archives = list(archive_dir.iterdir())
            self.assertEqual(len(archives), 1)
            self.assertNotEqual(archives[0].name, "failed")
            self.assertTrue(pathlib.Path(archives[0], "out.dat").exists())
            self.assertTrue(pathlib.Path(archives[0], "subdir", "out.txt").exists())

    def test_find_optional_input_files_without_wildcards(self):
        with TemporaryDirectory() as temp_dir:
            optional_file = pathlib.Path(temp_dir, "1.txt")
            optional_file.touch()
            pathlib.Path(temp_dir, "should_not_be_found.txt").touch()
            logger = mock.MagicMock()
            optional_input_files = ["1.txt", "does_not_exist.dat"]
            tool_specification = ToolSpecification(
                "spec name", "Python", temp_dir, [], None, logger, inputfiles_opt=optional_input_files
            )
            executable = ToolExecutable(
                "executable name",
                work_dir=temp_dir,
                output_dir="",
                tool_specification=tool_specification,
                cmd_line_args=[],
                logger=logger,
            )
            resources = [ProjectItemResource(None, "file", optional_file.as_uri())]
            file_paths = executable._find_optional_input_files(resources)
            self.assertEqual(file_paths, {"1.txt": [str(optional_file)]})

    def test_find_optional_input_files_with_wildcards(self):
        with TemporaryDirectory() as temp_dir:
            optional_file1 = pathlib.Path(temp_dir, "1.txt")
            optional_file1.touch()
            optional_file2 = pathlib.Path(temp_dir, "2.txt")
            optional_file2.touch()
            pathlib.Path(temp_dir, "should_not_be_found.jpg").touch()
            logger = mock.MagicMock()
            optional_input_files = ["*.txt"]
            tool_specification = ToolSpecification(
                "spec name", "Python", temp_dir, [], None, logger, inputfiles_opt=optional_input_files
            )
            executable = ToolExecutable(
                "executable name",
                work_dir=temp_dir,
                output_dir="",
                tool_specification=tool_specification,
                cmd_line_args=[],
                logger=logger,
            )
            resources = [
                ProjectItemResource(None, "file", optional_file1.as_uri()),
                ProjectItemResource(None, "file", optional_file2.as_uri()),
            ]
            file_paths = executable._find_optional_input_files(resources)
            self.assertEqual(file_paths, {"*.txt": [str(optional_file1), str(optional_file2)]})

    def test_find_optional_input_files_in_sub_directory(self):
        with TemporaryDirectory() as temp_dir:
            pathlib.Path(temp_dir, "subdir").mkdir()
            optional_file1 = pathlib.Path(temp_dir, "subdir", "1.txt")
            optional_file1.touch()
            optional_file2 = pathlib.Path(temp_dir, "subdir", "data.dat")
            optional_file2.touch()
            pathlib.Path(temp_dir, "should_not_be_found.jpg").touch()
            logger = mock.MagicMock()
            optional_input_files = ["subdir/*.txt", "subdir/data.dat"]
            tool_specification = ToolSpecification(
                "spec name", "Python", temp_dir, [], None, logger, inputfiles_opt=optional_input_files
            )
            executable = ToolExecutable(
                "executable name",
                work_dir=temp_dir,
                output_dir="",
                tool_specification=tool_specification,
                cmd_line_args=[],
                logger=logger,
            )
            resources = [
                ProjectItemResource(None, "file", optional_file1.as_uri()),
                ProjectItemResource(None, "file", optional_file2.as_uri()),
            ]
            file_paths = executable._find_optional_input_files(resources)
            self.assertEqual(
                file_paths, {"subdir/*.txt": [str(optional_file1)], "subdir/data.dat": [str(optional_file2)]}
            )

    @staticmethod
    def _write_output_script(script_dir):
        file_path = pathlib.Path(script_dir, "script.py")
        with open(file_path, "w") as script_file:
            script_file.writelines(
                [
                    "from pathlib import Path\n",
                    "Path('out.dat').touch()\n",
                    "Path('subdir').mkdir(exist_ok=True)\n",
                    "Path('subdir', 'out.txt').touch()\n",
                ]
            )
        return "script.py"


class _MockSettings:
    @staticmethod
    def value(key, defaultValue=None):
        return {
            "appSettings/pythonPath": sys.executable,
            "appSettings/useEmbeddedPython": "0",  # Don't use embedded Python
        }.get(key, defaultValue)


if __name__ == '__main__':
    unittest.main()
