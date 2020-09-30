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
Contains unit tests for the tool_instance module.

:authors: A. Soininen (VTT)
:date:   18.3.2020
"""

import unittest
from unittest import mock
from spine_items.tool.tool_specifications import PythonTool


class TestPythonToolInstance(unittest.TestCase):
    def test_prepare_with_cmd_line_arguments_in_embedded_console(self):
        instance = self._make_tool_instance(True)
        instance.prepare(
            optional_input_files=[], input_database_urls={}, output_database_urls={}, tool_args=["arg1", "arg2"]
        )
        self.assertEqual(instance.ipython_command_list, ["%cd -q path/", '%run "main.py" "arg1" "arg2"'])

    def test_prepare_with_empty_cmd_line_arguments_in_embedded_console(self):
        instance = self._make_tool_instance(True)
        instance.prepare(optional_input_files=[], input_database_urls={}, output_database_urls={}, tool_args=[])
        self.assertEqual(instance.ipython_command_list, ["%cd -q path/", '%run "main.py"'])

    def test_prepare_with_cmd_line_arguments(self):
        instance = self._make_tool_instance(False)
        instance.prepare(
            optional_input_files=[], input_database_urls={}, output_database_urls={}, tool_args=["arg1", "arg2"]
        )
        self.assertEqual(instance.program, "python_path/python.exe")
        self.assertEqual(instance.args, ["path/main.py", "arg1", "arg2"])

    def test_prepare_without_cmd_line_arguments(self):
        instance = self._make_tool_instance(False)
        instance.prepare(optional_input_files=[], input_database_urls={}, output_database_urls={}, tool_args=[])
        self.assertEqual(instance.program, "python_path/python.exe")
        self.assertEqual(instance.args, ["path/main.py"])

    @staticmethod
    def _make_tool_instance(execute_in_embedded_console):
        python_repl = mock.MagicMock()
        settings = mock.NonCallableMagicMock()
        if execute_in_embedded_console:
            settings.value = mock.MagicMock(return_value="2")
        else:

            def get_setting(name, defaultValue):
                return {"appSettings/pythonPath": "python_path/python.exe", "appSettings/useEmbeddedPython": "0"}.get(
                    name, defaultValue
                )

            settings.value = mock.MagicMock(side_effect=get_setting)
        logger = None
        path = ""
        source_files = ["main.py"]
        specification = PythonTool("specification name", "python", path, source_files, settings, python_repl, logger)
        base_directory = "path/"
        return specification.create_tool_instance(base_directory)


if __name__ == '__main__':
    unittest.main()
