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
Unit tests for the Combiner project item.

:author: P. Savolainen (VTT)
:date:   12.8.2020
"""

import os
import unittest
from unittest.mock import MagicMock, NonCallableMagicMock
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinetoolbox.project_items.combiner.combiner import Combiner
from spinetoolbox.project_items.combiner.executable_item import ExecutableItem
from spinetoolbox.project_items.combiner.item_info import ItemInfo
from spinetoolbox.project_item_resource import ProjectItemResource
from ...mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestCombiner(unittest.TestCase):
    def setUp(self):
        """Set up."""
        self.toolbox = create_toolboxui_with_project()
        item_dict = dict(name="combiner", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Combiner", item_dict)
        index = self.toolbox.project_item_model.find_item("combiner")
        self.combiner = self.toolbox.project_item_model.item(index).project_item

    def tearDown(self):
        """Clean up."""
        clean_up_toolboxui_with_project(self.toolbox)

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        self.assertEqual(Combiner.item_type(), ItemInfo.item_type())

    def test_item_category(self):
        self.assertEqual(Combiner.item_category(), ItemInfo.item_category())

    def test_execution_item(self):
        """Tests that the ExecutableItem counterpart is created successfully."""
        exec_item = self.combiner.execution_item()
        self.assertIsInstance(exec_item, ExecutableItem)

    def test_item_dict(self):
        """Tests Item dictionary creation."""
        d = self.combiner.item_dict()
        a = ["type", "short name", "description", "x", "y", "cancel_on_error"]
        for k in a:
            self.assertTrue(k in d, f"Key '{k}' not in dict {d}")

    def test_notify_destination(self):
        self.toolbox.msg = MagicMock()
        self.toolbox.msg.attach_mock(MagicMock(), "emit")
        self.toolbox.msg_warning = MagicMock()
        self.toolbox.msg_warning.attach_mock(MagicMock(), "emit")
        source_item = NonCallableMagicMock()
        source_item.name = "source name"
        source_item.item_type = MagicMock(return_value="Data Store")
        self.combiner.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. "
            f"Data from<b>{source_item.name}</b> will be merged "
            f"into <b>{self.combiner.name}</b>'s successor Data Stores upon execution."
        )
        source_item.item_type = MagicMock(return_value="Data Connection")
        self.combiner.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a "
            f"<b>{source_item.item_type()}</b> and a <b>{self.combiner.item_type()}</b> has not been "
            "implemented yet."
        )

    def test_default_name_prefix(self):
        self.assertEqual(Combiner.default_name_prefix(), "Combiner")

    def test_rename(self):
        self.combiner.activate()
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = self.combiner.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, self.combiner.name)  # item name
        self.assertEqual(expected_name, self.combiner._properties_ui.label_name.text())  # name label in props
        self.assertEqual(expected_name, self.combiner.get_icon().name_item.text())  # name item on Design View
        # Check data_dir
        expected_data_dir = os.path.join(self.toolbox.project().items_dir, expected_short_name)
        self.assertEqual(expected_data_dir, self.combiner.data_dir)  # Check data dir

    def test_handle_dag_changed(self):
        """Tests that predecessors resource db's are listed in the Combiner tree view."""
        self.combiner.activate()
        item = NonCallableMagicMock()
        expected_file_list = ["db1.sqlite", "db2.sqlite"]
        resources = [
            ProjectItemResource(item, "database", "sqlite:///db1.sqlite"),
            ProjectItemResource(item, "database", "sqlite:///db2.sqlite"),
        ]
        rank = 0
        self.combiner.handle_dag_changed(rank, resources)
        model = self.combiner._properties_ui.treeView_files.model()
        file_list = [model.index(row, 0).data(Qt.DisplayRole) for row in range(model.rowCount())]
        self.assertEqual(sorted(file_list), sorted(expected_file_list))

    def test_handle_dag_changed_updates_previous_list_items(self):
        self.combiner.activate()
        item = NonCallableMagicMock()
        resources = [ProjectItemResource(item, "file", url) for url in ["db1.sqlite", "db2.sqlite"]]
        rank = 0
        # Add initial files
        self.combiner.handle_dag_changed(rank, resources)
        model = self.combiner._properties_ui.treeView_files.model()
        # Update with one existing, one new file
        resources = [ProjectItemResource(item, "file", url) for url in ["db2.sqlite", "db3.sqlite"]]
        self.combiner.handle_dag_changed(rank, resources)
        file_list = [model.index(row, 0).data(Qt.DisplayRole) for row in range(model.rowCount())]
        # NOTE: The item list order is now vice versa for some reason
        self.assertEqual(file_list, ["db3.sqlite", "db2.sqlite"])


if __name__ == '__main__':
    unittest.main()
