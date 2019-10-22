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
Unit tests for Tool project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

import os
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtWidgets import QApplication
from networkx import DiGraph
from ..project_items.tool.tool import Tool
from ..project import SpineToolboxProject
from ..mvcmodels.tool_specification_model import ToolSpecificationModel
from .mock_helpers import create_toolboxui_with_project
from spinetoolbox.config import TOOL_OUTPUT_DIR


class _MockToolbox:
    class Message:
        def __init__(self):
            self.text = None

        def emit(self, text):
            self.text = text

    def __init__(self, temp_directory):
        self._qsettings = mock.MagicMock()
        self.tool_specification_model = ToolSpecificationModel(self)
        with mock.patch("spinetoolbox.project.project_dir") as mock_project_dir:
            mock_project_dir.return_value = temp_directory
            self._project = SpineToolboxProject(self, "name", "description", temp_directory)
        self.msg = _MockToolbox.Message()
        self.msg_warning = _MockToolbox.Message()

    def project(self):
        return self._project

    def qsettings(self):
        return self._qsettings

    def reset_messages(self):
        self.msg = _MockToolbox.Message()
        self.msg_warning = _MockToolbox.Message()


class _MockItem:
    def __init__(self, item_type, name):
        self.item_type = item_type
        self.name = name


class TestTool(unittest.TestCase):
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
            toolbox = _MockToolbox(project_dir)
            item = Tool(toolbox, "name", "description", 0.0, 0.0)
            self.assertEqual(item.item_type, "Tool")

    def test_notify_destination(self):
        with TemporaryDirectory() as project_dir:
            toolbox = _MockToolbox(project_dir)
            item = Tool(toolbox, "name", "description", 0.0, 0.0)
            source_item = _MockItem("Data Connection", "source name")
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg.text,
                "Link established. Tool <b>name</b> will look for input "
                "files from <b>source name</b>'s references and data directory.",
            )
            toolbox.reset_messages()
            source_item = _MockItem("Data Interface", "source name")
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg_warning.text,
                "Link established. Interaction between a "
                "<b>Data Interface</b> and a <b>Tool</b> has not been implemented yet.",
            )
            toolbox.reset_messages()
            source_item.item_type = "Data Store"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg.text,
                "Link established. Data Store <b>source name</b> url will "
                "be passed to Tool <b>name</b> when executing.",
            )
            toolbox.reset_messages()
            source_item.item_type = "Gdx Export"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg.text,
                "Link established. Gdx Export <b>source name</b> exported file will "
                "be passed to Tool <b>name</b> when executing.",
            )
            toolbox.reset_messages()
            source_item.item_type = "Tool"
            item.notify_destination(source_item)
            self.assertEqual(toolbox.msg.text, "Link established.")
            toolbox.reset_messages()
            source_item.item_type = "View"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg_warning.text,
                "Link established. Interaction between a "
                "<b>View</b> and a <b>Tool</b> has not been implemented yet.",
            )

    def test_default_name_prefix(self):
        self.assertEqual(Tool.default_name_prefix(), "Tool")

    def test_rename(self):
        """Tests renaming a Tool."""
        self._set_up()
        item_dict = dict(name="T", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Tools", item_dict)
        index = self.toolbox.project_item_model.find_item("T")
        tool = self.toolbox.project_item_model.project_item(index)
        tool.activate()
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = tool.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, tool.name)  # item name
        self.assertEqual(expected_name, tool._properties_ui.label_tool_name.text())  # name label in props
        self.assertEqual(expected_name, tool.get_icon().name_item.text())  # name item on Design View
        # Check data_dir
        expected_data_dir = os.path.join(self.toolbox.project().project_dir, expected_short_name)
        self.assertEqual(expected_data_dir, tool.data_dir)  # Check data dir
        # Check there's a dag containing a node with the new name and that no dag contains a node with the old name
        dag_with_new_node_name = self.toolbox.project().dag_handler.dag_with_node(expected_name)
        self.assertIsInstance(dag_with_new_node_name, DiGraph)
        dag_with_old_node_name = self.toolbox.project().dag_handler.dag_with_node("T")
        self.assertIsNone(dag_with_old_node_name)
        # Check that output_dir has been updated
        expected_output_dir = os.path.join(tool.data_dir, TOOL_OUTPUT_DIR)
        self.assertEqual(expected_output_dir, tool.output_dir)
        self.toolbox.remove_item(index, delete_item=True)


if __name__ == '__main__':
    unittest.main()
