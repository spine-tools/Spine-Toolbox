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
Unit tests for Importer project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

import os
import unittest
from unittest.mock import MagicMock, NonCallableMagicMock
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from networkx import DiGraph
from spinetoolbox.project_items.importer.importer import Importer
from spinetoolbox.project_item import ProjectItemResource
from ...mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestImporter(unittest.TestCase):
    def setUp(self):
        """Set up."""
        self.toolbox = create_toolboxui_with_project()
        item_dict = dict(name="importer", description="", mappings=dict(), x=0, y=0)
        self.toolbox.project().add_project_items("Importers", item_dict)
        index = self.toolbox.project_item_model.find_item("importer")
        self.importer = self.toolbox.project_item_model.item(index).project_item

    def tearDown(self):
        """Clean up."""
        clean_up_toolboxui_with_project(self.toolbox)

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        self.assertEqual(self.importer.item_type(), "Importer")

    def test_notify_destination(self):
        self.toolbox.msg = MagicMock()
        self.toolbox.msg.attach_mock(MagicMock(), "emit")
        self.toolbox.msg_warning = MagicMock()
        self.toolbox.msg_warning.attach_mock(MagicMock(), "emit")
        source_item = NonCallableMagicMock()
        source_item.name = "source name"
        source_item.item_type = MagicMock(return_value="Data Connection")
        self.importer.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. You can define mappings on data from <b>source name</b> using item <b>importer</b>."
        )
        source_item.item_type = MagicMock(return_value="Data Store")
        self.importer.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with("Link established.")
        source_item.item_type = MagicMock(return_value="Exporter")
        self.importer.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a "
            "<b>Exporter</b> and a <b>Importer</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="Tool")
        self.importer.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a " "<b>Tool</b> and a <b>Importer</b> has not been implemented yet."
        )
        source_item.item_type = MagicMock(return_value="View")
        self.importer.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a " "<b>View</b> and a <b>Importer</b> has not been implemented yet."
        )

    def test_default_name_prefix(self):
        self.assertEqual(Importer.default_name_prefix(), "Importer")

    def test_rename(self):
        """Tests renaming an Importer."""
        self.importer.activate()
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = self.importer.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, self.importer.name)  # item name
        self.assertEqual(expected_name, self.importer._properties_ui.label_name.text())  # name label in props
        self.assertEqual(expected_name, self.importer.get_icon().name_item.text())  # name item on Design View
        # Check data_dir
        expected_data_dir = os.path.join(self.toolbox.project().items_dir, expected_short_name)
        self.assertEqual(expected_data_dir, self.importer.data_dir)  # Check data dir

    def test_handle_dag_changed(self):
        """Tests that upstream resource files are listed in the Importer view."""
        self.importer.activate()
        item = NonCallableMagicMock()
        expected_file_list = ["url1", "url2"]
        resources = [ProjectItemResource(item, "file", url) for url in expected_file_list]
        self.importer._do_handle_dag_changed(resources)
        model = self.importer._properties_ui.treeView_files.model()
        file_list = [model.index(row, 0).data(Qt.DisplayRole) for row in range(model.rowCount())]
        self.assertEqual(sorted(file_list), sorted(expected_file_list))


if __name__ == '__main__':
    unittest.main()
