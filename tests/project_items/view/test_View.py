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
Unit tests for View project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

import os
import shutil
from tempfile import TemporaryDirectory
import unittest
from PySide2.QtWidgets import QApplication
from networkx import DiGraph
from spinetoolbox.project_items.view.view import View
from ...mock_helpers import create_toolboxui_with_project


class _MockProject:
    def __init__(self, temp_directory):
        self.project_dir = temp_directory


class _MockToolbox:
    def __init__(self, project):
        self._project = project

    def project(self):
        return self._project


class TestView(unittest.TestCase):
    def _set_up(self):
        """Set up before test_rename()."""
        self.toolbox = create_toolboxui_with_project()

    def tearDown(self):
        """Clean up."""
        if not hasattr(self, "toolbox"):
            return
        try:
            shutil.rmtree(self.toolbox.project().project_dir)  # Remove project directory
        except OSError as e:
            print("Failed to remove project directory. {0}".format(e))
            pass
        try:
            os.remove(self.toolbox.project().path)  # Remove project file
        except OSError:
            print("Failed to remove project file")
            pass
        self.toolbox.deleteLater()
        self.toolbox = None

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        with TemporaryDirectory() as project_dir:
            project = _MockProject(project_dir)
            item = View(_MockToolbox(project), "name", "description", 0.0, 0.0)
            self.assertEqual(item.item_type, "View")

    def test_default_name_prefix(self):
        self.assertEqual(View.default_name_prefix(), "View")

    def test_rename(self):
        """Tests renaming a View."""
        self._set_up()
        item_dict = dict(name="V", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Views", item_dict)
        index = self.toolbox.project_item_model.find_item("V")
        view = self.toolbox.project_item_model.project_item(index)
        view.activate()
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = view.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, view.name)  # item name
        self.assertEqual(expected_name, view._properties_ui.label_view_name.text())  # name label in props
        self.assertEqual(expected_name, view.get_icon().name_item.text())  # name item on Design View
        # Check data_dir
        expected_data_dir = os.path.join(self.toolbox.project().project_dir, expected_short_name)
        self.assertEqual(expected_data_dir, view.data_dir)  # Check data dir
        # Check there's a dag containing a node with the new name and that no dag contains a node with the old name
        dag_with_new_node_name = self.toolbox.project().dag_handler.dag_with_node(expected_name)
        self.assertIsInstance(dag_with_new_node_name, DiGraph)
        dag_with_old_node_name = self.toolbox.project().dag_handler.dag_with_node("V")
        self.assertIsNone(dag_with_old_node_name)
        self.toolbox.remove_item(index, delete_item=True)


if __name__ == '__main__':
    unittest.main()
