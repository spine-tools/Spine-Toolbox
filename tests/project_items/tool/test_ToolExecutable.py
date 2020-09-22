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
import os
import sys
import pathlib
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtCore import QCoreApplication
from spine_engine import ExecutionDirection
from spinetoolbox.project_item_resource import ProjectItemResource
from spinetoolbox.project_items.tool.executable_item import ExecutableItem, _count_files_and_dirs
from spinetoolbox.project_items.tool.tool_specifications import ToolSpecification, PythonTool
from spinetoolbox.config import DEFAULT_WORK_DIR
from spinetoolbox.project_items.tool.utils import _LatestOutputFile
from spinetoolbox.execution_managers import ConsoleExecutionManager


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
        self.assertEqual(ExecutableItem.item_type(), "Tool")

    def test_from_dict(self):
        """Tests that from_dict creates an ExecutableItem."""
        mock_settings = _MockSettings()
        item_dict = {"type": "Tool", "description": "", "x": 0, "y": 0,
                     "specification": "Python Tool", "execute_in_work": True, "cmd_line_args": ["a", "b"]}
        with TemporaryDirectory() as temp_dir:
            script_dir = pathlib.Path(temp_dir, "scripts")
            script_dir.mkdir()
            script_file_name = self._write_output_script(script_dir)
            script_files = [script_file_name]
            python_tool_spec = PythonTool(
                name="Python Tool",
                tooltype="Python",
                path=str(script_dir),
                includes=script_files,
                settings=mock_settings,
                embedded_python_console=None,
                logger=mock.MagicMock(),
                execute_in_work=True
            )
            specs_in_project = {"Tool": {"Python Tool": python_tool_spec}}
            with TemporaryDirectory() as temp_project_dir:
                item = ExecutableItem.from_dict(item_dict, name="T", project_dir=temp_project_dir,
                                                app_settings=mock_settings, specifications=specs_in_project,
                                                logger=mock.MagicMock())
                self.assertIsInstance(item, ExecutableItem)
                self.assertEqual("Tool", item.item_type())
                self.assertTrue(item._tool_specification.name, "Python Tool")
                self.assertEqual("some_work_dir", item._work_dir)
                self.assertEqual(["a", "b"], item._cmd_line_args)
                # Test that DEFAULT_WORK_DIR is used if "appSettings/workDir" key is missing from qsettings
                item = ExecutableItem.from_dict(item_dict, name="T", project_dir=temp_project_dir,
                                                app_settings=_EmptyMockSettings(), specifications=specs_in_project,
                                                logger=mock.MagicMock())
                self.assertIsInstance(item, ExecutableItem)
                self.assertEqual("Tool", item.item_type())
                self.assertEqual(DEFAULT_WORK_DIR, item._work_dir)
                self.assertEqual(["a", "b"], item._cmd_line_args)
                # This time the project dict does not have any specifications
                item = ExecutableItem.from_dict(item_dict, name="T", project_dir=temp_project_dir,
                                                app_settings=mock_settings, specifications=dict(),
                                                logger=mock.MagicMock())
                self.assertIsNone(item)
                # Modify item_dict
                item_dict["execute_in_work"] = False
                item = ExecutableItem.from_dict(item_dict, name="T", project_dir=temp_project_dir,
                                                app_settings=mock_settings, specifications=specs_in_project,
                                                logger=mock.MagicMock())
                self.assertIsInstance(item, ExecutableItem)
                self.assertEqual("Tool", item.item_type())
                self.assertEqual(["a", "b"], item._cmd_line_args)
                self.assertIsNone(item._work_dir)
                # Modify item_dict
                item_dict["specification"] = ""
                item = ExecutableItem.from_dict(item_dict, name="T", project_dir=temp_project_dir,
                                                app_settings=mock_settings, specifications=specs_in_project,
                                                logger=mock.MagicMock())
                self.assertIsNone(item)

    def test_execute_forward_without_specification_fails(self):
        logger = mock.MagicMock()
        executable = ExecutableItem(
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
            executable = ExecutableItem("Create files", str(work_dir), str(archive_dir), tool_specification, [], logger)
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
            executable = ExecutableItem(
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
            executable = ExecutableItem(
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
            executable = ExecutableItem(
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

    def test_output_resources_forward(self):
        with TemporaryDirectory() as temp_dir:
            logger = mock.MagicMock()
            tool_specification = PythonTool(
                name="Python Tool",
                tooltype="Python",
                path=temp_dir,
                includes=["script.py"],
                settings=None,
                embedded_python_console=None,
                logger=mock.MagicMock(),
                outputfiles=["results.gdx", "report.txt"]
            )
            output_dir = "tool/output_dir/"  # Latest output dir
            executable = ExecutableItem("name", temp_dir, output_dir, tool_specification, [], logger)
            with mock.patch(
                    "spinetoolbox.project_items.tool.executable_item.find_last_output_files") \
                    as mock_find_last_output_files:
                mock_find_last_output_files.return_value = {
                    "results.gdx": [_LatestOutputFile("label", os.path.join(temp_dir, "output_dir/results.gdx"))],
                    "report.txt": [_LatestOutputFile("label2", os.path.join(temp_dir, "output_dir/report.txt"))]
                }
                resources = executable._output_resources_forward()
                mock_find_last_output_files.assert_called_once()
                self.assertIsInstance(resources, list)
                self.assertEqual(2, len(resources))
                self.assertIsInstance(resources[0], ProjectItemResource)
                self.assertIsInstance(resources[1], ProjectItemResource)
                self.assertEqual("transient_file", resources[0].type_)
                self.assertEqual("transient_file", resources[1].type_)

    def test_stop_execution(self):
        with TemporaryDirectory() as temp_dir:
            logger = mock.MagicMock()
            tool_specification = PythonTool(
                name="Python Tool",
                tooltype="Python",
                path=temp_dir,
                includes=["script.py"],
                settings=None,
                embedded_python_console=None,
                logger=mock.MagicMock(),
                outputfiles=["results.gdx", "report.txt"]
            )
            executable = ExecutableItem("name", temp_dir, "", tool_specification, [], logger)
            executable._tool_instance = executable._tool_specification.create_tool_instance(temp_dir)
            executable._tool_instance.exec_mngr = ConsoleExecutionManager(mock.MagicMock(), [], logger)
            executable.stop_execution()
            self.assertIsNone(executable._tool_instance)

    def test_count_files_and_dirs(self):
        """Tests protected function in tool/executable_item.py."""
        paths = ["data/a.txt", "data/output", "data/input_dir/", "inc/b.txt", "directory/"]  # 3 files, 2 dirs
        n_dir, n_files = _count_files_and_dirs(paths)
        self.assertEqual(2, n_dir)
        self.assertEqual(3, n_files)

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


class _EmptyMockSettings:
    @staticmethod
    def value(key, defaultValue=None):
        return {None: None}.get(key, defaultValue)


class _MockSettings:
    @staticmethod
    def value(key, defaultValue=None):
        return {
            "appSettings/pythonPath": sys.executable,
            "appSettings/useEmbeddedPython": "0",  # Don't use embedded Python
            "appSettings/workDir": "some_work_dir",
        }.get(key, defaultValue)


if __name__ == '__main__':
    unittest.main()
