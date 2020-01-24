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
Unit tests for View project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

import os
import unittest
from unittest.mock import MagicMock, NonCallableMagicMock
from PySide2.QtWidgets import QApplication
from networkx import DiGraph
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.project_items.view.view import View
from ...mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestView(unittest.TestCase):
    def setUp(self):
        """Set up."""
        self.toolbox = create_toolboxui_with_project()
        item_dict = dict(name="V", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Views", item_dict)
        index = self.toolbox.project_item_model.find_item("V")
        self.view = self.toolbox.project_item_model.item(index).project_item

    def tearDown(self):
        """Clean up."""
        clean_up_toolboxui_with_project(self.toolbox)

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        self.assertEqual(self.view.item_type(), "View")

    def test_default_name_prefix(self):
        self.assertEqual(View.default_name_prefix(), "View")

    def test_notify_destination(self):
        self.toolbox.msg = MagicMock()
        self.toolbox.msg.attach_mock(MagicMock(), "emit")
        self.toolbox.msg_warning = MagicMock()
        self.toolbox.msg_warning.attach_mock(MagicMock(), "emit")
        source_item = NonCallableMagicMock()
        source_item.name = "source name"
        source_item.item_type = MagicMock(return_value="Data Connection")
        self.view.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a <b>Data Connection</b> and"
            " a <b>View</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="Importer")
        self.view.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a <b>Importer</b> and a <b>View</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="Data Store")
        self.view.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. You can visualize Data Store <b>source name</b> in View <b>V</b>."
        )
        source_item.item_type = MagicMock(return_value="Exporter")
        self.view.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a <b>Exporter</b> and a <b>View</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="Tool")
        self.view.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. You can visualize the ouput from Tool <b>source name</b> in View <b>V</b>."
        )

    def test_rename(self):
        """Tests renaming a View."""
        self.view.activate()
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = self.view.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, self.view.name)  # item name
        self.assertEqual(expected_name, self.view._properties_ui.label_view_name.text())  # name label in props
        self.assertEqual(expected_name, self.view.get_icon().name_item.text())  # name item on Design View
        # Check data_dir
        expected_data_dir = os.path.join(self.toolbox.project().items_dir, expected_short_name)
        self.assertEqual(expected_data_dir, self.view.data_dir)  # Check data dir


if __name__ == '__main__':
    unittest.main()
