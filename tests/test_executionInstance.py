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
from PySide2.QtCore import QVariantAnimation
from PySide2.QtWidgets import QApplication
from spinetoolbox.executioner import ExecutionInstance, ExecutionState
from spinetoolbox.project_item import ProjectItemResource
from .mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


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
        self.mock_upstream_item = self._mock_item("upstream item")
        self.mock_downstream_item = self._mock_item("downstream item")
        mock_proj_item_model = mock.NonCallableMagicMock()
        mock_upstream_index = mock.NonCallableMagicMock()
        mock_downstream_index = mock.NonCallableMagicMock()
        mock_proj_item_model.find_item.side_effect = lambda name: {
            "upstream item": mock_upstream_index,
            "downstream item": mock_downstream_index,
        }[name]
        mock_proj_item_model.project_item.side_effect = lambda index: {
            mock_upstream_index: self.mock_upstream_item,
            mock_downstream_index: self.mock_downstream_item,
        }[index]
        self.toolbox.project_item_model = mock_proj_item_model

    @staticmethod
    def _mock_item(name):
        """Returns a mock project item."""
        item = mock.NonCallableMagicMock()
        item.name = name
        item.execute = mock.MagicMock()
        resources_upstream = [ProjectItemResource(item, "type", "url")]
        resources_downstream = [ProjectItemResource(item, "type", "url")]
        item.available_resources_upstream.return_value = resources_upstream
        item.available_resources_downstream.return_value = resources_downstream
        item.make_execution_leave_animation.return_value = leave_anim = QVariantAnimation()
        leave_anim.setDuration(0)
        return item

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        clean_up_toolboxui_with_project(self.toolbox)

    def test_start_execution_with_two_items_forwards_resources_correctly(self):
        ordered_nodes = {
            self.mock_upstream_item.name: [self.mock_downstream_item.name],
            self.mock_downstream_item.name: [],
        }
        execution_instance = ExecutionInstance(self.toolbox, ordered_nodes)
        execution_instance.start_execution()
        # Need to manually push the execution forward.
        execution_instance.project_item_execution_finished_signal.emit(ExecutionState.CONTINUE)
        self.mock_upstream_item.execute.assert_called_with([], self.mock_downstream_item.available_resources_upstream())
        qApp.processEvents()
        self.mock_downstream_item.execute.assert_called_with(
            self.mock_upstream_item.available_resources_downstream(), []
        )


if __name__ == '__main__':
    unittest.main()
