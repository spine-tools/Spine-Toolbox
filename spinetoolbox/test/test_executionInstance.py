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
Unit tests for ExecutionInstance class.

:author: M. Marin (KTH)
:date:   11.9.2019
"""

import unittest
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication, QWidget
from ..ui_main import ToolboxUI
from ..executioner import ExecutionInstance
from ..project_item import ProjectItemResource
from .mock_helpers import MockQWidget, qsettings_value_side_effect, create_toolboxui_with_project


class TestExecutionInstance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Runs once before any tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def setUp(self):
        """Runs before each test. Makes an instance of ToolboxUI class.
        We want the ToolboxUI to start with the default settings and without a project
        """
        self.toolbox = create_toolboxui_with_project()
        # Mock `project_item_model` so `find_item()` and `project_item()` are just the identity function
        mock_proj_item_model = mock.Mock()
        mock_proj_item_model.find_item.side_effect = lambda item: item
        mock_proj_item_model.project_item.side_effect = lambda item: item
        self.toolbox.project_item_model = mock_proj_item_model

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        self.toolbox.deleteLater()
        self.toolbox = None

    def test_advertising_files_from_two_data_connections_to_a_data_interface(self):
        """Test that advertising files from a DC to a DI works fine."""
        dc1 = mock.Mock()
        dc2 = mock.Mock()
        di3 = mock.Mock()
        exec_order = {dc1: [di3], dc2: [di3]}
        inst = ExecutionInstance(self.toolbox, exec_order)
        resource1 = ProjectItemResource(None, "data_connection_file", "file1")
        resource2 = ProjectItemResource(None, "data_connection_file", "file2")
        dc1.simulate_execution.side_effect = lambda inst: inst.advertise_resources(dc1, resource1)
        dc2.simulate_execution.side_effect = lambda inst: inst.advertise_resources(dc2, resource2)
        inst.simulate_execution()
        self.assertEqual(inst.available_resources(di3), [resource1, resource2])

    def test_advertising_file_and_reference_from_a_data_connection_to_a_data_interface(self):
        """Test that the same file in dc refs and data is advertised only once."""
        dc0 = mock.Mock()
        di1 = mock.Mock()
        exec_order = {dc0: [di1]}
        inst = ExecutionInstance(self.toolbox, exec_order)
        resource1 = ProjectItemResource(None, "data_connection_reference", "ref1")
        resource2 = ProjectItemResource(None, "data_connection_file", "file2")
        dc0.simulate_execution.side_effect = lambda inst: inst.advertise_resources(dc0, resource1, resource2)
        inst.simulate_execution()
        self.assertEqual(inst.available_resources(di1), [resource1, resource2])


if __name__ == '__main__':
    unittest.main()
