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
Unit tests for ResourceMap class.

:author: A. Soininen (VTT)
:date:   11.9.2019
"""

import unittest
from unittest.mock import NonCallableMagicMock
from PySide2.QtCore import QModelIndex
from PySide2.QtWidgets import QApplication
from spinetoolbox.executioner import ResourceMap
from spinetoolbox.project_item import ProjectItemResource
from .mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestResourceMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Runs before each test. Makes an instance of ToolboxUI class.
        We want the ToolboxUI to start with the default settings and without a project
        """
        self.toolbox = create_toolboxui_with_project()
        # Mock `project_item_model` so `find_item()` and `project_item()` are just the identity function
        self.mock_upstream_item = self._mock_item("upstream item")
        self.mock_downstream_item = self._mock_item("downstream item")
        mock_proj_item_model = NonCallableMagicMock()
        mock_proj_item_model.find_item.return_value = QModelIndex()
        mock_proj_item_model.project_item.side_effect = 2 * [self.mock_upstream_item, self.mock_downstream_item]
        self.toolbox.project_item_model = mock_proj_item_model

    @staticmethod
    def _mock_item(name):
        """Returns a mock project item."""
        item = NonCallableMagicMock()
        item.name = name
        resources_upstream = [ProjectItemResource(item, "type", "url")]
        resources_downstream = [ProjectItemResource(item, "type", "url")]
        item.available_resources_upstream.return_value = resources_upstream
        item.available_resources_downstream.return_value = resources_downstream
        return item

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        clean_up_toolboxui_with_project(self.toolbox)

    def test_update(self):
        ordered_nodes = {
            self.mock_upstream_item.name: [self.mock_downstream_item.name],
            self.mock_downstream_item.name: [],
        }
        resource_map = ResourceMap(ordered_nodes, self.toolbox.project_item_model)
        resource_map.update()


if __name__ == '__main__':
    unittest.main()
