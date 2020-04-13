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
Unit tests for Tool project item.

:author: A. Soininen (VTT), P. Savolainen (VTT), M. Marin (KTH)
:date:   4.10.2019
"""

from tempfile import mkdtemp
import unittest
from unittest import mock
import os
import shutil
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem, QStandardItemModel
from PySide2.QtWidgets import QApplication
from spinetoolbox.project_items.tool.tool_specifications import ExecutableTool
from spinetoolbox.project_items.tool.tool import Tool
from spinetoolbox.config import TOOL_OUTPUT_DIR
from ...mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestTool(unittest.TestCase):
    def setUp(self):
        """Set up."""
        self.basedir = mkdtemp()
        self.toolbox = create_toolboxui_with_project()
        model = _MockToolSpecModel(self.toolbox, self.basedir)
        self.toolbox.specification_model = self.toolbox.category_filtered_spec_models["Tools"] = model
        self.toolbox.specification_model_changed.emit()

    def tearDown(self):
        """Clean up."""
        clean_up_toolboxui_with_project(self.toolbox)
        shutil.rmtree(self.basedir)

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        tool = self._add_tool()
        self.assertEqual(tool.item_type(), "Tool")

    def test_notify_destination(self):
        self.toolbox.msg = mock.MagicMock()
        self.toolbox.msg.attach_mock(mock.MagicMock(), "emit")
        self.toolbox.msg_warning = mock.MagicMock()
        self.toolbox.msg_warning.attach_mock(mock.MagicMock(), "emit")
        source_item = mock.NonCallableMagicMock()
        source_item.name = "source name"
        source_item.item_type = mock.MagicMock(return_value="Data Connection")
        tool = self._add_tool()
        tool.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. Tool <b>T</b> will look for input "
            "files from <b>source name</b>'s references and data directory."
        )
        source_item.item_type = mock.MagicMock(return_value="Importer")
        tool.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a " "<b>Importer</b> and a <b>Tool</b> has not been implemented yet."
        )
        source_item.item_type = mock.MagicMock(return_value="Data Store")
        tool.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. Data Store <b>source name</b> url will " "be passed to Tool <b>T</b> when executing."
        )
        source_item.item_type = mock.MagicMock(return_value="Exporter")
        tool.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. The file exported by <b>source name</b> will "
            "be passed to Tool <b>T</b> when executing."
        )
        source_item.item_type = mock.MagicMock(return_value="Tool")
        tool.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with("Link established.")
        source_item.item_type = mock.MagicMock(return_value="View")
        tool.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a " "<b>View</b> and a <b>Tool</b> has not been implemented yet."
        )

    def test_default_name_prefix(self):
        self.assertEqual(Tool.default_name_prefix(), "Tool")

    def test_rename(self):
        """Tests renaming a self.tool."""
        tool = self._add_tool()
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
        expected_data_dir = os.path.join(self.toolbox.project().items_dir, expected_short_name)
        self.assertEqual(expected_data_dir, tool.data_dir)  # Check data dir
        # Check that output_dir has been updated
        expected_output_dir = os.path.join(tool.data_dir, TOOL_OUTPUT_DIR)
        self.assertEqual(expected_output_dir, tool.output_dir)

    def test_load_tool_specification(self):
        """Test that specification is loaded into selections on Tool creation,
        and then shown in the ui when Tool is activated.
        """
        item = dict(name="Tool", description="", x=0, y=0, tool="simple_exec", execute_in_work=False)
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.item(ind).project_item
        tool.activate()
        self._assert_is_simple_exec_tool(tool)

    def test_save_and_restore_selections(self):
        """Test that selections are saved and restored when deactivating a Tool and activating it again.
        """
        item = dict(name="Tool", description="", x=0, y=0, tool="")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.item(ind).project_item
        tool.activate()
        self._assert_is_no_tool(tool)
        tool._properties_ui.comboBox_tool.setCurrentIndex(0)  # Set the simple_exec tool specification
        self._assert_is_simple_exec_tool(tool)
        tool.deactivate()
        tool.activate()
        self._assert_is_simple_exec_tool(tool)

    def _add_tool(self):
        item_dict = dict(name="T", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Tools", item_dict)
        index = self.toolbox.project_item_model.find_item("T")
        return self.toolbox.project_item_model.item(index).project_item

    def _assert_is_simple_exec_tool(self, tool):
        """Assert that the given tool has the simple_exec specification."""
        # Check internal models
        source_files = [x.text() for x in tool.source_file_model.findItems("*", Qt.MatchWildcard)]
        input_files = [x.text() for x in tool.input_file_model.findItems("*", Qt.MatchWildcard)]
        opt_input_files = [x.text() for x in tool.opt_input_file_model.findItems("*", Qt.MatchWildcard)]
        output_files = [x.text() for x in tool.output_file_model.findItems("*", Qt.MatchWildcard)]
        self.assertEqual(source_files, ['main.sh'])
        self.assertIn('input1.csv', input_files)
        self.assertIn('input2.csv', input_files)
        self.assertEqual(opt_input_files, ['opt_input.csv'])
        self.assertIn('output1.csv', output_files)
        self.assertIn('output2.csv', output_files)
        # Check specification model
        model = tool.specification_model
        root = model.invisibleRootItem()
        categories = [root.child(i).text() for i in range(model.rowCount())]
        self.assertIn('Source files', categories)
        self.assertIn('Input files', categories)
        self.assertIn('Optional input files', categories)
        self.assertIn('Output files', categories)
        source_files_cat = model.findItems('Source files', Qt.MatchExactly)[0]
        input_files_cat = model.findItems('Input files', Qt.MatchExactly)[0]
        opt_input_files_cat = model.findItems('Optional input files', Qt.MatchExactly)[0]
        output_files_cat = model.findItems('Output files', Qt.MatchExactly)[0]
        source_files = [source_files_cat.child(i).text() for i in range(source_files_cat.rowCount())]
        input_files = [input_files_cat.child(i).text() for i in range(input_files_cat.rowCount())]
        opt_input_files = [opt_input_files_cat.child(i).text() for i in range(opt_input_files_cat.rowCount())]
        output_files = [output_files_cat.child(i).text() for i in range(output_files_cat.rowCount())]
        self.assertEqual(source_files, ['main.sh'])
        self.assertIn('input1.csv', input_files)
        self.assertIn('input2.csv', input_files)
        self.assertEqual(opt_input_files, ['opt_input.csv'])
        self.assertIn('output1.csv', output_files)
        self.assertIn('output2.csv', output_files)
        # Check ui
        combox_text = tool._properties_ui.comboBox_tool.currentText()
        cmdline_args = tool._properties_ui.lineEdit_tool_spec_args.text()
        in_work = tool._properties_ui.radioButton_execute_in_work.isChecked()
        in_source = tool._properties_ui.radioButton_execute_in_source.isChecked()
        self.assertEqual(combox_text, "simple_exec")
        self.assertEqual(cmdline_args, '<args>')
        self.assertFalse(in_work)
        self.assertTrue(in_source)

    def _assert_is_no_tool(self, tool):
        """Assert that the given tool has no tool specification."""
        # Check internal models
        source_files = [x.text() for x in tool.source_file_model.findItems("*", Qt.MatchWildcard)]
        input_files = [x.text() for x in tool.input_file_model.findItems("*", Qt.MatchWildcard)]
        opt_input_files = [x.text() for x in tool.opt_input_file_model.findItems("*", Qt.MatchWildcard)]
        output_files = [x.text() for x in tool.output_file_model.findItems("*", Qt.MatchWildcard)]
        self.assertEqual(source_files, [])
        self.assertEqual(input_files, [])
        self.assertEqual(opt_input_files, [])
        self.assertEqual(output_files, [])
        # Check specification model
        model = tool.specification_model
        root = model.invisibleRootItem()
        categories = [root.child(i).text() for i in range(model.rowCount())]
        self.assertIn('Source files', categories)
        self.assertIn('Input files', categories)
        self.assertIn('Optional input files', categories)
        self.assertIn('Output files', categories)
        source_files_cat = model.findItems('Source files', Qt.MatchExactly)[0]
        input_files_cat = model.findItems('Input files', Qt.MatchExactly)[0]
        opt_input_files_cat = model.findItems('Optional input files', Qt.MatchExactly)[0]
        output_files_cat = model.findItems('Output files', Qt.MatchExactly)[0]
        source_files = [source_files_cat.child(i).text() for i in range(source_files_cat.rowCount())]
        input_files = [input_files_cat.child(i).text() for i in range(input_files_cat.rowCount())]
        opt_input_files = [opt_input_files_cat.child(i).text() for i in range(opt_input_files_cat.rowCount())]
        output_files = [output_files_cat.child(i).text() for i in range(output_files_cat.rowCount())]
        self.assertEqual(source_files, [])
        self.assertEqual(input_files, [])
        self.assertEqual(opt_input_files, [])
        self.assertEqual(output_files, [])
        # Check ui
        combox_text = tool._properties_ui.comboBox_tool.currentText()
        cmdline_args = tool._properties_ui.lineEdit_tool_args.text()
        in_work = tool._properties_ui.radioButton_execute_in_work.isChecked()
        in_source = tool._properties_ui.radioButton_execute_in_source.isChecked()
        self.assertEqual(combox_text, "")
        self.assertEqual(cmdline_args, '')
        self.assertTrue(in_work)
        self.assertFalse(in_source)


class _MockToolSpecModel(QStandardItemModel):
    # Create a dictionary of tool specifications to 'populate' the mock model
    def __init__(self, toolbox, path):
        super().__init__()
        specifications = [
            ExecutableTool(
                name="simple_exec",
                tooltype="executable",
                path=path,
                includes=['main.sh'],
                settings=toolbox.qsettings(),
                logger=toolbox,
                description="A simple executable tool.",
                inputfiles=['input1.csv', 'input2.csv'],
                inputfiles_opt=['opt_input.csv'],
                outputfiles=['output1.csv', 'output2.csv'],
                cmdline_args='<args>',
                execute_in_work=False,
            ),
            ExecutableTool(
                name="complex_exec",
                tooltype="executable",
                path=path,
                includes=['MakeFile', 'src/a.c', 'src/a.h', 'src/subunit/x.c', 'src/subunit/x.h'],
                settings=toolbox.qsettings(),
                logger=toolbox,
                description="A more complex executable tool.",
                inputfiles=['input1.csv', 'input/input2.csv'],
                inputfiles_opt=['opt/*.ini', '?abc.txt'],
                outputfiles=['output1.csv', 'output/output2.csv'],
                cmdline_args='subunit',
                execute_in_work=True,
            ),
        ]
        specification_names = [x.name for x in specifications]
        specification_dict = dict(zip(specification_names, specifications))
        self.find_specification = specification_dict.get
        self.specification = specifications.__getitem__
        self.specification_row = specification_names.index
        self.invisibleRootItem().appendRows([QStandardItem(x) for x in specification_dict])

    def specification_index(self, spec_name):
        row = self.specification_row(spec_name)
        return self.invisibleRootItem().child(row)


if __name__ == '__main__':
    unittest.main()
