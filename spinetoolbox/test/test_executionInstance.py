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
from ui_main import ToolboxUI
from project import SpineToolboxProject
from executioner import ExecutionInstance
from test.mock_helpers import MockQWidget, qsettings_value_side_effect


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
        with mock.patch("ui_main.JuliaREPLWidget") as mock_julia_repl, mock.patch(
            "ui_main.PythonReplWidget"
        ) as mock_python_repl, mock.patch("project.create_dir") as mock_create_dir, mock.patch(
            "ui_main.ToolboxUI.save_project"
        ) as mock_save_project, mock.patch(
            "ui_main.QSettings.value"
        ) as mock_qsettings_value:
            # Replace Julia REPL Widget with a QWidget so that the DeprecationWarning from qtconsole is not printed
            mock_julia_repl.return_value = QWidget()
            mock_python_repl.return_value = MockQWidget()
            mock_qsettings_value.side_effect = qsettings_value_side_effect
            self.toolbox = ToolboxUI()
            self.toolbox.create_project("UnitTest Project", "")
            # Mock `project_item_model` so `find_item()` and `project_item()` are just the identity function
            mock_proj_item_model = mock.Mock()
            mock_proj_item_model.find_item.side_effect = lambda item: item
            mock_proj_item_model.project_item.side_effect = lambda item: item
            self.toolbox.project_item_model = mock_proj_item_model

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        self.toolbox.deleteLater()
        self.toolbox = None

    def test_advertising_same_file_through_merging_branches(self):
        """Test that the same file coming through merging branches is advertised only once."""
        dc0 = mock.Mock()
        dc1 = mock.Mock()
        dc2 = mock.Mock()
        di3 = mock.Mock()
        exec_order = {dc0: [dc1, dc2], dc1: [di3], dc2: [di3]}
        inst = ExecutionInstance(self.toolbox, exec_order)
        dc0.simulate_execution.side_effect = lambda x: x.append_dc_refs(dc0, ["file1"])
        inst.simulate_execution()
        self.assertEqual(inst.dc_refs_at_sight(dc1), {"file1"})
        self.assertEqual(inst.dc_refs_at_sight(dc2), {"file1"})
        self.assertEqual(inst.dc_refs_at_sight(di3), {"file1"})

    def test_advertising_same_file_in_dc_refs_and_data(self):
        """Test that the same file in dc refs and data is advertised only once."""
        dc0 = mock.Mock()
        di1 = mock.Mock()
        exec_order = {dc0: [di1]}
        inst = ExecutionInstance(self.toolbox, exec_order)

        def dc0_simul_exec_side_effect(x):
            x.append_dc_refs(dc0, ["file1"])
            x.append_dc_files(dc0, ["file1"])

        dc0.simulate_execution.side_effect = dc0_simul_exec_side_effect
        inst.simulate_execution()
        self.assertEqual(inst.dc_refs_at_sight(di1), {"file1"})
