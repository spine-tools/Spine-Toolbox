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
Unit tests for Exporter project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

import os
import unittest
from unittest.mock import MagicMock, NonCallableMagicMock
from PySide2.QtWidgets import QApplication
from networkx import DiGraph
from spinetoolbox.project_item import ProjectItemResource
from spinetoolbox.project_items.exporter.exporter import Exporter
from ...mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestExporter(unittest.TestCase):
    def setUp(self):
        """Set up."""
        self.toolbox = create_toolboxui_with_project()
        item_dict = dict(name="exporter", description="", settings_packs=None, x=0, y=0)
        self.toolbox.project().add_project_items("Exporters", item_dict)
        index = self.toolbox.project_item_model.find_item("exporter")
        self.exporter = self.toolbox.project_item_model.item(index).project_item

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

    def test_activation_populates_properties_tab(self):
        self.exporter._start_worker = MagicMock()
        resources = [
            ProjectItemResource(None, "database", "first url to database"),
            ProjectItemResource(None, "database", "second url to database"),
        ]
        self.exporter.handle_dag_changed(0, resources)
        self.exporter.activate()
        urls_in_properties_tab = list()
        for i in range(self.exporter._properties_ui.databases_list_layout.count()):
            database_item = self.exporter._properties_ui.databases_list_layout.itemAt(i).widget()
            urls_in_properties_tab.append(database_item.url_field.text())
        self.assertEqual(len(urls_in_properties_tab), 2)
        self.assertTrue("first url to database" in urls_in_properties_tab)
        self.assertTrue("second url to database" in urls_in_properties_tab)

    def test_activating_second_exporter_with_less_database_urls_does_not_crash(self):
        self.exporter._start_worker = MagicMock()
        item_dict = dict(name="2nd exporter", description="", settings_packs=None, x=0, y=0)
        self.toolbox.project().add_project_items("Exporters", item_dict)
        index = self.toolbox.project_item_model.find_item("2nd exporter")
        exporter2 = self.toolbox.project_item_model.item(index).project_item
        exporter2._start_worker = MagicMock()
        resources = [
            ProjectItemResource(None, "database", "first url to database"),
            ProjectItemResource(None, "database", "second url to database"),
        ]
        self.exporter.handle_dag_changed(0, resources)
        self.exporter.activate()
        urls_in_properties_tab = list()
        for i in range(self.exporter._properties_ui.databases_list_layout.count()):
            database_item = self.exporter._properties_ui.databases_list_layout.itemAt(i).widget()
            urls_in_properties_tab.append(database_item.url_field.text())
        self.assertEqual(len(urls_in_properties_tab), 2)
        self.assertTrue("first url to database" in urls_in_properties_tab)
        self.assertTrue("second url to database" in urls_in_properties_tab)
        resources = [ProjectItemResource(None, "database", "url to a database in the clouds")]
        exporter2.handle_dag_changed(1, resources)
        exporter2.activate()
        self.assertEqual(exporter2._properties_ui.databases_list_layout.count(), 1)
        database_item = self.exporter._properties_ui.databases_list_layout.itemAt(0).widget()
        self.assertEqual(database_item.url_field.text(), "url to a database in the clouds")

    def test_handle_dag_changed_does_not_overwrite_properties_tab_when_no_urls_change(self):
        self.exporter._start_worker = MagicMock()
        self.exporter.activate()
        self.exporter._update_properties_tab = MagicMock()
        resources = [ProjectItemResource(None, "database", "url to database")]
        self.exporter.handle_dag_changed(0, resources)
        self.exporter._update_properties_tab.assert_called_once()
        self.exporter._update_properties_tab.reset_mock()
        self.exporter.handle_dag_changed(0, resources)
        self.exporter._update_properties_tab.assert_not_called()


if __name__ == '__main__':
    unittest.main()
