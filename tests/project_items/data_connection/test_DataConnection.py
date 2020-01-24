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
Unit tests for Data Connection project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

import os
import unittest
from unittest.mock import MagicMock, NonCallableMagicMock
from PySide2.QtWidgets import QApplication
from networkx import DiGraph
from spinetoolbox.project_items.data_connection.data_connection import DataConnection
from ...mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestDataConnection(unittest.TestCase):
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

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        self.assertEqual(self.data_connection.item_type(), "Data Connection")

    def test_notify_destination(self):
        self.toolbox.msg = MagicMock()
        self.toolbox.msg.attach_mock(MagicMock(), "emit")
        self.toolbox.msg_warning = MagicMock()
        self.toolbox.msg_warning.attach_mock(MagicMock(), "emit")
        source_item = NonCallableMagicMock()
        source_item.name = "source name"
        source_item.item_type = MagicMock(return_value="Importer")
        self.data_connection.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with("Link established.")
        source_item.item_type = MagicMock(return_value="Data Store")
        self.data_connection.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with("Link established.")
        source_item.item_type = MagicMock(return_value="Exporter")
        self.data_connection.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a <b>Exporter</b> and"
            " a <b>Data Connection</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="Tool")
        self.data_connection.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. Tool <b>source name</b> output files"
            " will be passed as references to item <b>DC</b> after execution."
        )
        source_item.item_type = MagicMock(return_value="View")
        self.data_connection.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a <b>View</b> and"
            " a <b>Data Connection</b> has not been implemented yet."
        )

    def test_default_name_prefix(self):
        self.assertEqual(DataConnection.default_name_prefix(), "Data Connection")

    def test_rename(self):
        """Tests renaming a Data Connection."""
        self.data_connection.activate()
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = self.data_connection.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, self.data_connection.name)  # item name
        self.assertEqual(expected_name, self.data_connection._properties_ui.label_dc_name.text())  # name label in props
        self.assertEqual(expected_name, self.data_connection.get_icon().name_item.text())  # name item on Design View
        # Check data_dir
        expected_data_dir = os.path.join(self.toolbox.project().items_dir, expected_short_name)
        self.assertEqual(expected_data_dir, self.data_connection.data_dir)  # Check data dir
        # Check that data_dir_watcher has one path (new data_dir)
        watched_dirs = self.data_connection.data_dir_watcher.directories()
        self.assertEqual(1, len(watched_dirs))
        self.assertEqual(self.data_connection.data_dir, watched_dirs[0])


if __name__ == '__main__':
    unittest.main()
