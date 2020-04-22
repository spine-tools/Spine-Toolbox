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
from pathlib import Path
import logging
import os
import sys
import shutil
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem, QStandardItemModel
from PySide2.QtWidgets import QApplication
from networkx import DiGraph
from spinetoolbox.tool_specifications import ExecutableTool
from spinetoolbox.project_items.tool.tool import Tool
from spinetoolbox.project_item import ProjectItemResource
from spinetoolbox import tool_specifications
from spinetoolbox.config import TOOL_OUTPUT_DIR
from ...mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestTool(unittest.TestCase):
    def setUp(self):
        """Set up."""
        self.toolbox = create_toolboxui_with_project()
        item_dict = dict(name="T", description="", x=0, y=0)
        self.toolbox.project().add_project_items("Tools", item_dict)
        index = self.toolbox.project_item_model.find_item("T")
        self.tool = self.toolbox.project_item_model.item(index).project_item

    def tearDown(self):
        """Clean up."""
        clean_up_toolboxui_with_project(self.toolbox)

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        self.assertEqual(self.tool.item_type(), "Tool")

    def test_notify_destination(self):
        self.toolbox.msg = mock.MagicMock()
        self.toolbox.msg.attach_mock(mock.MagicMock(), "emit")
        self.toolbox.msg_warning = mock.MagicMock()
        self.toolbox.msg_warning.attach_mock(mock.MagicMock(), "emit")
        source_item = mock.NonCallableMagicMock()
        source_item.name = "source name"
        source_item.item_type = mock.MagicMock(return_value="Data Connection")
        self.tool.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. Tool <b>T</b> will look for input "
            "files from <b>source name</b>'s references and data directory."
        )
        source_item.item_type = mock.MagicMock(return_value="Importer")
        self.tool.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a " "<b>Importer</b> and a <b>Tool</b> has not been implemented yet."
        )
        source_item.item_type = mock.MagicMock(return_value="Data Store")
        self.tool.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. Data Store <b>source name</b> url will " "be passed to Tool <b>T</b> when executing."
        )
        source_item.item_type = mock.MagicMock(return_value="Exporter")
        self.tool.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with(
            "Link established. The file exported by <b>source name</b> will "
            "be passed to Tool <b>T</b> when executing."
        )
        source_item.item_type = mock.MagicMock(return_value="Tool")
        self.tool.notify_destination(source_item)
        self.toolbox.msg.emit.assert_called_with("Link established.")
        source_item.item_type = mock.MagicMock(return_value="View")
        self.tool.notify_destination(source_item)
        self.toolbox.msg_warning.emit.assert_called_with(
            "Link established. Interaction between a " "<b>View</b> and a <b>Tool</b> has not been implemented yet."
        )

    def test_default_name_prefix(self):
        self.assertEqual(Tool.default_name_prefix(), "Tool")

    def test_rename(self):
        """Tests renaming a self.tool."""
        self.tool.activate()
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = self.tool.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, self.tool.name)  # item name
        self.assertEqual(expected_name, self.tool._properties_ui.label_tool_name.text())  # name label in props
        self.assertEqual(expected_name, self.tool.get_icon().name_item.text())  # name item on Design View
        # Check data_dir
        expected_data_dir = os.path.join(self.toolbox.project().items_dir, expected_short_name)
        self.assertEqual(expected_data_dir, self.tool.data_dir)  # Check data dir
        # Check that output_dir has been updated
        expected_output_dir = os.path.join(self.tool.data_dir, TOOL_OUTPUT_DIR)
        self.assertEqual(expected_output_dir, self.tool.output_dir)

    def test_find_optional_files(self):
        """Tests finding optional input file paths that match a pattern with '*' or a '?' character."""
        fake_dc_dir = os.path.join("C:", os.path.sep, "fake_dc")
        fake_fnames = ["a.ini", "bc.ini", "xyz.txt", "123.txt"]
        fake_available_filepaths = [os.path.join(fake_dc_dir, fname) for fname in fake_fnames]
        # Test with a.ini
        matches = self.tool._find_optional_files("a.ini", fake_available_filepaths)
        expected_matches = [os.path.join(fake_dc_dir, "a.ini")]
        self.assertEqual(expected_matches, matches)
        # Test with a.*
        matches = self.tool._find_optional_files("a.*", fake_available_filepaths)
        expected_matches = [os.path.join(fake_dc_dir, "a.ini")]
        self.assertEqual(expected_matches, matches)
        # Test with *.ini
        matches = self.tool._find_optional_files("*.ini", fake_available_filepaths)
        expected_matches = [os.path.join(fake_dc_dir, fn) for fn in ("a.ini", "bc.ini")]
        self.assertEqual(expected_matches, matches)
        # Test with *
        matches = self.tool._find_optional_files("*", fake_available_filepaths)
        expected_matches = fake_available_filepaths
        self.assertEqual(expected_matches, matches)
        # Test with ?.ini
        matches = self.tool._find_optional_files("?.ini", fake_available_filepaths)
        expected_matches = [os.path.join(fake_dc_dir, "a.ini")]
        self.assertEqual(expected_matches, matches)
        # Test with ???.txt
        matches = self.tool._find_optional_files("???.txt", fake_available_filepaths)
        expected_matches = [os.path.join(fake_dc_dir, fn) for fn in ("xyz.txt", "123.txt")]
        self.assertEqual(expected_matches, matches)
        # Test with ??.txt
        matches = self.tool._find_optional_files("??.txt", fake_available_filepaths)
        expected_matches = []
        self.assertEqual(expected_matches, matches)
        # Test with x?z
        matches = self.tool._find_optional_files("x?z", fake_available_filepaths)
        expected_matches = []
        self.assertEqual(expected_matches, matches)
        # Test with x?z.*
        matches = self.tool._find_optional_files("x?z.*", fake_available_filepaths)
        expected_matches = [os.path.join(fake_dc_dir, "xyz.txt")]
        self.assertEqual(expected_matches, matches)


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
        self.find_tool_specification = specification_dict.get
        self.tool_specification = specifications.__getitem__
        self.tool_specification_row = specification_names.index
        self.invisibleRootItem().appendRows([QStandardItem(x) for x in specification_dict])


class TestToolExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        cls.basedir = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        """Overridden method. Runs once after all tests in this class."""
        shutil.rmtree(cls.basedir)

    def setUp(self):
        """setUp for tests in TestToolExecution."""
        self.toolbox = create_toolboxui_with_project()
        self.toolbox.tool_specification_model = _MockToolSpecModel(self.toolbox, self.basedir)
        self.toolbox.tool_specification_model_changed.emit(self.toolbox.tool_specification_model)

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        clean_up_toolboxui_with_project(self.toolbox)

    def assert_is_simple_exec_tool(self, tool):
        """Assert that the given tool has the simple_exec specification."""
        # Check internal models
        source_files = [x.text() for x in tool.source_file_model.findItems("*", Qt.MatchWildcard)]
        input_files = [x.text() for x in tool.input_file_model.findItems("*", Qt.MatchWildcard)]
        opt_input_files = [x.text() for x in tool.opt_input_file_model.findItems("*", Qt.MatchWildcard)]
        output_files = [x.text() for x in tool.output_file_model.findItems("*", Qt.MatchWildcard)]
        self.assertEqual(source_files, ['main.sh'])
        self.assertTrue('input1.csv' in input_files)
        self.assertTrue('input2.csv' in input_files)
        self.assertEqual(opt_input_files, ['opt_input.csv'])
        self.assertTrue('output1.csv' in output_files)
        self.assertTrue('output2.csv' in output_files)
        # Check specification model
        model = tool.specification_model
        root = model.invisibleRootItem()
        categories = [root.child(i).text() for i in range(model.rowCount())]
        self.assertTrue('Source files' in categories)
        self.assertTrue('Input files' in categories)
        self.assertTrue('Optional input files' in categories)
        self.assertTrue('Output files' in categories)
        source_files_cat = model.findItems('Source files', Qt.MatchExactly)[0]
        input_files_cat = model.findItems('Input files', Qt.MatchExactly)[0]
        opt_input_files_cat = model.findItems('Optional input files', Qt.MatchExactly)[0]
        output_files_cat = model.findItems('Output files', Qt.MatchExactly)[0]
        source_files = [source_files_cat.child(i).text() for i in range(source_files_cat.rowCount())]
        input_files = [input_files_cat.child(i).text() for i in range(input_files_cat.rowCount())]
        opt_input_files = [opt_input_files_cat.child(i).text() for i in range(opt_input_files_cat.rowCount())]
        output_files = [output_files_cat.child(i).text() for i in range(output_files_cat.rowCount())]
        self.assertEqual(source_files, ['main.sh'])
        self.assertTrue('input1.csv' in input_files)
        self.assertTrue('input2.csv' in input_files)
        self.assertEqual(opt_input_files, ['opt_input.csv'])
        self.assertTrue('output1.csv' in output_files)
        self.assertTrue('output2.csv' in output_files)
        # Check ui
        combox_text = tool._properties_ui.comboBox_tool.currentText()
        cmdline_args = tool._properties_ui.lineEdit_tool_spec_args.text()
        in_work = tool._properties_ui.radioButton_execute_in_work.isChecked()
        in_source = tool._properties_ui.radioButton_execute_in_source.isChecked()
        self.assertEqual(combox_text, "simple_exec")
        self.assertEqual(cmdline_args, '<args>')
        self.assertFalse(in_work)
        self.assertTrue(in_source)

    def assert_is_no_tool(self, tool):
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
        self.assertTrue('Source files' in categories)
        self.assertTrue('Input files' in categories)
        self.assertTrue('Optional input files' in categories)
        self.assertTrue('Output files' in categories)
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

    def test_load_tool_specification(self):
        """Test that specification is loaded into selections on Tool creation,
        and then shown in the ui when Tool is activated.
        """
        item = dict(name="Tool", description="", x=0, y=0, tool="simple_exec")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.item(ind).project_item
        tool.activate()
        self.assert_is_simple_exec_tool(tool)

    def test_save_and_restore_selections(self):
        """Test that selections are saved and restored when deactivating a Tool and activating it again.
        """
        item = dict(name="Tool", description="", x=0, y=0, tool="")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.item(ind).project_item
        tool.activate()
        self.assert_is_no_tool(tool)
        tool._properties_ui.comboBox_tool.setCurrentIndex(0)  # Set the simple_exec tool specification
        self.assert_is_simple_exec_tool(tool)
        tool.deactivate()
        tool.activate()
        self.assert_is_simple_exec_tool(tool)

    def test_execute_tool_with_no_specification(self):
        """Tests Tools with no specification are not executed."""
        item = dict(name="Tool", description="", x=0, y=0, tool="")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.item(ind).project_item
        self.assertFalse(tool.execute_forward(resources=[]))

    def test_input_file_not_found_at_execution(self):
        """Tests that execution fails if one input file is not found."""
        item = dict(name="Tool", description="", x=0, y=0, tool="simple_exec")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.item(ind).project_item
        # Collect some information
        input_files = [x.text() for x in tool.input_file_model.findItems("*", Qt.MatchWildcard)]
        project_dir = tool._project.project_dir
        # Make sure we have two input files
        self.assertEqual(len(input_files), 2)
        # Create a mock data connection directory in the project
        dc_dir = os.path.join(project_dir, "input_dc")
        os.makedirs(dc_dir)
        # Create first input file but not the second in the above dir
        input_file = input_files[0]
        input_path = os.path.join(dc_dir, input_file)
        Path(input_path).touch()
        resources = [ProjectItemResource(None, "file", url=Path(input_path).as_uri())]
        # Create a mock execution instance and make the above one path available for the tool
        self.assertFalse(tool.execute_forward(resources))
        self.assertIsNone(tool.instance)
        # Check that no resources are advertised

    def test_execute_simple_tool_in_source_dir(self):
        """Tests execution of a Tool with the 'simple_exec' specification."""
        item = dict(name="Tool", description="", x=0, y=0, tool="simple_exec")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        self.toolbox.project().execution_instance = mock.NonCallableMagicMock()
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.item(ind).project_item
        # Collect some information
        basedir = tool.tool_specification().path
        project_dir = tool._project.project_dir
        input_files = [x.text() for x in tool.input_file_model.findItems("*", Qt.MatchWildcard)]
        output_files = [x.text() for x in tool.output_file_model.findItems("*", Qt.MatchWildcard)]
        # Create a mock data connection directory in the project
        dc_dir = os.path.join(project_dir, "input_dc")
        os.makedirs(dc_dir)
        # Create all mandatory input files in that directory
        input_paths = [os.path.join(dc_dir, fn) for fn in input_files]
        for filepath in input_paths:
            Path(filepath).touch()
        resources = [ProjectItemResource(None, "file", url=Path(fp).as_uri()) for fp in input_paths]
        # Mock some more stuff needed and execute the tool
        with mock.patch("spinetoolbox.project_items.tool.tool.shutil") as mock_shutil, mock.patch(
            "spinetoolbox.project_items.tool.tool.create_output_dir_timestamp"
        ) as mock_create_output_dir_timestamp, mock.patch.object(
            tool_specifications.ExecutableToolInstance, "execute"
        ) as mock_execute_tool_instance:
            mock_create_output_dir_timestamp.return_value = "mock_timestamp"

            def mock_execute_tool_instance_side_effect():
                """Provides a side effect for ToolInstance execute method."""
                # Check that input files were copied to the base directory
                expected_calls = [mock.call(os.path.join(dc_dir, fn), os.path.join(basedir, fn)) for fn in input_files]
                mock_shutil.copyfile.assert_has_calls(expected_calls, any_order=True)
                # Create all output files in base dir
                output_paths = [os.path.join(basedir, fn) for fn in output_files]
                for filepath in output_paths:
                    Path(filepath).touch()
                # Emit signal as if the tool had failed
                tool.instance.instance_finished.emit(-1)

            mock_execute_tool_instance.side_effect = mock_execute_tool_instance_side_effect
            self.assertFalse(tool.execute_forward(resources))
        self.assertEqual(tool.basedir, basedir)
        # Check that output files were copied to the output dir
        result_dir = os.path.abspath(os.path.join(tool.output_dir, "failed", "mock_timestamp"))
        expected_calls = [mock.call(os.path.join(basedir, fn), os.path.join(result_dir, fn)) for fn in output_files]
        mock_shutil.copyfile.assert_has_calls(expected_calls, any_order=True)
        # Check that no resources are advertised

    def test_execute_complex_tool_in_work_dir(self):
        """Tests execution of a Tool with the 'complex_exec' specification."""
        # Make work directory in case it does not exist. This may be needed by Travis CI.
        work_dir = self.toolbox.work_dir
        os.makedirs(work_dir, exist_ok=True)
        item = dict(name="Tool", description="", x=0, y=0, tool="complex_exec")
        self.toolbox.project().add_project_items("Tools", item)
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.item(ind).project_item
        self.toolbox.project().execution_instance = mock.NonCallableMagicMock()
        project_dir = self.toolbox.project().project_dir
        source_files = [x.text() for x in tool.source_file_model.findItems("*", Qt.MatchWildcard)]
        input_files = [x.text() for x in tool.input_file_model.findItems("*", Qt.MatchWildcard)]
        output_files = [x.text() for x in tool.output_file_model.findItems("*", Qt.MatchWildcard)]
        # Create a mock data connection directory in the project
        dc_dir = os.path.join(project_dir, "input_dc")
        # Create input files in the above dir
        # Start with mandatory input files
        input_paths = [os.path.join(dc_dir, fn) for fn in input_files]
        # Add some optional input files that match "opt/*.ini"
        opt_input_ini_fnames = ["a.ini", "b.ini", "c.ini"]
        input_paths += [os.path.join(dc_dir, ini_fname) for ini_fname in opt_input_ini_fnames]
        # Add some optional input files that match "?abc.txt"
        opt_input_txt_fnames = ["1abc.txt", "2abc.txt", "3abc.txt"]
        input_paths += [os.path.join(dc_dir, txt_fname) for txt_fname in opt_input_txt_fnames]
        # Make all input files
        for filepath in input_paths:
            dirname, _ = os.path.split(filepath)
            os.makedirs(dirname, exist_ok=True)
            Path(filepath).touch()
        resources = [ProjectItemResource(None, "file", url=Path(fp).as_uri()) for fp in input_paths]
        # Create source files in tool specification source directory
        src_dir = tool.tool_specification().path
        source_paths = [os.path.join(src_dir, path) for path in source_files]
        for filepath in source_paths:
            dirname, _ = os.path.split(filepath)
            os.makedirs(dirname, exist_ok=True)
            Path(filepath).touch()
        # Mock some more stuff needed and execute the tool
        with mock.patch("spinetoolbox.project_items.tool.tool.shutil") as mock_shutil, mock.patch(
            "spinetoolbox.project_items.tool.tool.create_output_dir_timestamp"
        ) as mock_create_output_dir_timestamp, mock.patch.object(
            tool_specifications.ExecutableToolInstance, "execute"
        ) as mock_execute_tool_instance, mock.patch(
            "spinetoolbox.project_items.tool.tool.create_dir"
        ):
            mock_create_output_dir_timestamp.return_value = "mock_timestamp"

            def mock_execute_tool_instance_side_effect():
                """Provides a side effect for ToolInstance execute method."""
                # Check that source and input files were copied to the base directory
                # Expected calls for copying source files to work dir
                expected_calls = [
                    mock.call(
                        os.path.abspath(os.path.join(src_dir, fn)), os.path.abspath(os.path.join(tool.basedir, fn))
                    )
                    for fn in source_files
                ]
                # Expected calls for copying required input files to work dir
                expected_calls += [
                    mock.call(
                        os.path.abspath(os.path.join(dc_dir, fn)), os.path.abspath(os.path.join(tool.basedir, fn))
                    )
                    for fn in input_files
                ]
                # Expected calls for copying optional input files to work dir, matching pattern 'opt/*.ini'
                # Note: *.ini files should be copied to /opt subdirectory in work dir
                expected_calls += [
                    mock.call(
                        os.path.abspath(os.path.join(dc_dir, opt_ini_file)),
                        os.path.abspath(os.path.join(tool.basedir, "opt", opt_ini_file)),
                    )
                    for opt_ini_file in opt_input_ini_fnames
                ]
                # Expected calls for copying optional input files to work dir, matching pattern '?abc.txt'
                expected_calls += [
                    mock.call(
                        os.path.abspath(os.path.join(dc_dir, opt_abc_file)), os.path.join(tool.basedir, opt_abc_file)
                    )
                    for opt_abc_file in opt_input_txt_fnames
                ]
                mock_shutil.copyfile.assert_has_calls(expected_calls, any_order=True)
                # Create all output files in base dir
                output_paths = [os.path.join(tool.basedir, fn) for fn in output_files]
                for output_filepath in output_paths:
                    output_dirname, _ = os.path.split(output_filepath)
                    os.makedirs(output_dirname, exist_ok=True)
                    Path(output_filepath).touch()
                # Emit signal as if the tool had succeeded
                tool.instance.instance_finished.emit(0)

            mock_execute_tool_instance.side_effect = mock_execute_tool_instance_side_effect
            self.assertTrue(tool.execute_forward(resources))
        # Check that output files were copied to the output dir
        result_dir = os.path.join(tool.output_dir, "mock_timestamp")
        expected_calls = [
            mock.call(os.path.abspath(os.path.join(tool.basedir, fn)), os.path.abspath(os.path.join(result_dir, fn)))
            for fn in output_files
        ]
        mock_shutil.copyfile.assert_has_calls(expected_calls, any_order=True)


if __name__ == '__main__':
    unittest.main()
