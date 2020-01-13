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
Unit tests for Exporter project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

import os
import unittest
from unittest.mock import MagicMock, NonCallableMagicMock
from PySide2.QtWidgets import QApplication
from networkx import DiGraph
from spinetoolbox.project_items.exporter.exporter import Exporter
from ...mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestExporter(unittest.TestCase):
    def setUp(self):
        """Set up."""
        self.toolbox = create_toolboxui_with_project()
        item_dict = dict(name="exporter", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Exporters", item_dict)
        index = self.toolbox.project_item_model.find_item("exporter")
        self.exporter = self.toolbox.project_item_model.project_item(index)

    def tearDown(self):
        """Clean up."""
        clean_up_toolboxui_with_project(self.toolbox)

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        self.assertEqual(self.exporter.item_type(), "Exporter")

    def test_notify_destination(self):
        self.toolbox.msg = MagicMock()
        self.toolbox.msg.attach_mock(MagicMock(), "emit")
        self.toolbox.msg_warning = MagicMock()
        self.toolbox.msg_warning.attach_mock(MagicMock(), "emit")
        source_item = NonCallableMagicMock()
        source_item.name = "source name"
        source_item.item_type = MagicMock(return_value="Data Connection")
        self.exporter.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a "
            "<b>Data Connection</b> and a <b>Exporter</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="Importer")
        self.exporter.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a "
            "<b>Importer</b> and a <b>Exporter</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="Data Store")
        self.exporter.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. Data Store <b>source name</b> will be "
            "exported to a .gdx file by <b>exporter</b> when executing."
        )
        source_item.item_type = MagicMock(return_value="Tool")
        self.exporter.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a " "<b>Tool</b> and a <b>Exporter</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="View")
        self.exporter.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a " "<b>View</b> and a <b>Exporter</b> has not been implemented yet."
        )

    def test_default_name_prefix(self):
        self.assertEqual(Exporter.default_name_prefix(), "Exporter")

    def test_rename(self):
        """Tests renaming an Exporter."""
        self.exporter.activate()
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = self.exporter.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, self.exporter.name)  # item name
        self.assertEqual(expected_name, self.exporter._properties_ui.item_name_label.text())  # name label in props
        self.assertEqual(expected_name, self.exporter.get_icon().name_item.text())  # name item on Design View
        # Check data_dir
        expected_data_dir = os.path.join(self.toolbox.project().items_dir, expected_short_name)
        self.assertEqual(expected_data_dir, self.exporter.data_dir)  # Check data dir
        # Check there's a dag containing a node with the new name and that no dag contains a node with the old name
        dag_with_new_node_name = self.toolbox.project().dag_handler.dag_with_node(expected_name)
        self.assertIsInstance(dag_with_new_node_name, DiGraph)
        dag_with_old_node_name = self.toolbox.project().dag_handler.dag_with_node("Exporter")
        self.assertIsNone(dag_with_old_node_name)


if __name__ == '__main__':
    unittest.main()
