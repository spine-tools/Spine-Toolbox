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
Unit tests for ProjectItem base class.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

import unittest
from unittest.mock import MagicMock, NonCallableMagicMock
from PySide2.QtWidgets import QApplication
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.project_item import ProjectItem
from .mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestProjectItem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Set up toolbox."""
        self.toolbox = create_toolboxui_with_project()
        item_dict = dict(name="DC", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Data Connections", item_dict)
        index = self.toolbox.project_item_model.find_item("DC")
        self.data_connection = self.toolbox.project_item_model.item(index).project_item

    def tearDown(self):
        """Clean up."""
        self.data_connection.data_dir_watcher.removePath(self.data_connection.data_dir)
        clean_up_toolboxui_with_project(self.toolbox)

    def test_notify_destination(self):
        self.toolbox.msg_warning = NonCallableMagicMock()
        self.toolbox.msg_warning.attach_mock(MagicMock(), "emit")
        item = ProjectItem("name", "description", 0.0, 0.0, self.toolbox.project(), self.toolbox)
        item.item_type = MagicMock(return_value="item_type")
        item.notify_destination(item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established."
            " Interaction between a <b>item_type</b> and a <b>item_type</b> has not been implemented yet."
        )


if __name__ == '__main__':
    unittest.main()
