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
from tempfile import TemporaryDirectory, mkdtemp
import unittest
from unittest import mock
from pathlib import Path
import logging
import os
import sys
import shutil
import tempfile

from PySide2.QtCore import Qt, QSettings
from PySide2.QtGui import QStandardItem, QStandardItemModel
from PySide2.QtWidgets import QApplication, QWidget
from networkx import DiGraph

from .mock_helpers import MockQWidget, qsettings_value_side_effect
from ..ui_main import ToolboxUI
from ..tool_specifications import ExecutableTool
from ..project_items.tool.tool import Tool
from ..project import SpineToolboxProject
from ..mvcmodels.tool_specification_model import ToolSpecificationModel
from ..project_item import ProjectItemResource
from .. import tool_specifications
from spinetoolbox.config import TOOL_OUTPUT_DIR


class _MockToolbox:
    class Message:
        def __init__(self):
            self.text = None

        def emit(self, text):
            self.text = text

    def __init__(self, project_dir, base_dir=None):
        if base_dir is None:
            base_dir = ""
        self._qsettings = QSettings()
        self._qsettings.setValue("appSettings/projectsDir", project_dir)
        self.tool_specification_model = _MockToolSpecModel(self, base_dir)
        self._project = SpineToolboxProject(self, "name", "description", project_dir)
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
        with mock.patch("spinetoolbox.ui_main.JuliaREPLWidget") as mock_julia_repl, mock.patch(
            "spinetoolbox.ui_main.PythonReplWidget"
        ) as mock_python_repl, mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            # Replace Julia REPL Widget with a QWidget so that the DeprecationWarning from qtconsole is not printed
            mock_julia_repl.return_value = QWidget()
            mock_python_repl.return_value = MockQWidget()
            mock_qsettings_value.side_effect = qsettings_value_side_effect
            self.toolbox = ToolboxUI()
            self.toolbox.create_project("UnitTest Project", "")

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


class _MockToolSpecModel(QStandardItemModel):
    # Create a dictionary of tool specifications to 'populate' the mock model
    def __init__(self, toolbox, path):
        super().__init__()
        specifications = [
            ExecutableTool(
                toolbox=toolbox,
                name="simple_exec",
                tooltype="executable",
                path=path,
                includes=['main.sh'],
                description="A simple executable tool.",
                inputfiles=['input1.csv', 'input2.csv'],
                inputfiles_opt=['opt_input.csv'],
                outputfiles=['output1.csv', 'output2.csv'],
                cmdline_args='<args>',
                execute_in_work=False,
            ),
            ExecutableTool(
                toolbox=toolbox,
                name="complex_exec",
                tooltype="executable",
                path=path,
                includes=['MakeFile', 'src/a.c', 'src/a.h', 'src/subunit/x.c', 'src/subunit/x.h'],
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
        """Overridden method. Runs before each test. Makes instance of ToolboxUI class.
        """
        with mock.patch("spinetoolbox.ui_main.JuliaREPLWidget") as mock_julia_repl, mock.patch(
            "spinetoolbox.ui_main.PythonReplWidget"
        ) as mock_python_repl, mock.patch("spinetoolbox.ui_main.QSettings.value") as mock_qsettings_value:
            # Replace Julia REPL Widget with a QWidget so that the DeprecationWarning from qtconsole is not printed
            mock_julia_repl.return_value = QWidget()
            mock_python_repl.return_value = MockQWidget()
            mock_qsettings_value.side_effect = qsettings_value_side_effect
            self.toolbox = ToolboxUI()
            self.toolbox.create_project("UnitTest Project", "")
            self.toolbox.tool_specification_model = _MockToolSpecModel(self.toolbox, self.basedir)
            self.toolbox.tool_specification_model_changed.emit(self.toolbox.tool_specification_model)

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        try:
            shutil.rmtree(self.toolbox.project().project_dir)  # Remove project directory
        except OSError:
            pass
        try:
            os.remove(self.toolbox.project().path)  # Remove project file
        except OSError:
            pass
        self.toolbox.deleteLater()
        self.toolbox = None

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
        cmdline_args = tool._properties_ui.lineEdit_tool_args.text()
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
        tool = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        tool.activate()
        self.assert_is_simple_exec_tool(tool)

    def test_save_and_restore_selections(self):
        """Test that selections are saved and restored when deactivating a Tool and activating it again.
        """
        item = dict(name="Tool", description="", x=0, y=0, tool="")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
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
        tool = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        mock_exec_inst = tool._project.execution_instance = mock.Mock()
        tool.execute()
        mock_exec_inst.project_item_execution_finished_signal.emit.assert_called_with(0)
        self.assertIsNone(tool.instance)

    def test_input_file_not_found_at_execution(self):
        """Tests that execution fails if one input file is not found."""
        item = dict(name="Tool", description="", x=0, y=0, tool="simple_exec")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
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
        # Create a mock execution instance and make the above one path available for the tool
        mock_exec_inst = tool._project.execution_instance = mock.Mock()
        mock_exec_inst.available_resources.side_effect = lambda n: [
            ProjectItemResource(None, "file", url=Path(input_path).as_uri())
        ]
        tool.execute()
        mock_exec_inst.project_item_execution_finished_signal.emit.assert_called_with(-1)
        self.assertIsNone(tool.instance)
        # Check that no resources are advertised
        mock_exec_inst.advertise_resources.assert_not_called()

    def test_execute_simple_tool_in_source_dir(self):
        """Tests execution of a Tool with the 'simple_exec' specification."""
        item = dict(name="Tool", description="", x=0, y=0, tool="simple_exec")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
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
        # Create a mock execution instance and make the above paths available for the tool
        mock_exec_inst = tool._project.execution_instance = mock.Mock()
        mock_exec_inst.available_resources.side_effect = lambda n: [
            ProjectItemResource(None, "file", url=Path(fp).as_uri()) for fp in input_paths
        ]
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
                mock_shutil.copyfile.assert_has_calls(expected_calls)
                # Create all output files in base dir
                output_paths = [os.path.join(basedir, fn) for fn in output_files]
                for filepath in output_paths:
                    Path(filepath).touch()
                # Emit signal as if the tool had failed
                tool.instance.instance_finished_signal.emit(-1)

            mock_execute_tool_instance.side_effect = mock_execute_tool_instance_side_effect
            tool.execute()
        self.assertEqual(tool.basedir, basedir)
        # Check that output files were copied to the output dir
        result_dir = os.path.abspath(os.path.join(tool.output_dir, "failed", "mock_timestamp"))
        expected_calls = [mock.call(os.path.join(basedir, fn), os.path.join(result_dir, fn)) for fn in output_files]
        mock_shutil.copyfile.assert_has_calls(expected_calls)
        # Check that no resources are advertised
        mock_exec_inst.advertise_resources.assert_not_called()

    def test_execute_complex_tool_in_work_dir(self):
        """Tests execution of a Tool with the 'complex_exec' specification."""
        item = dict(name="Tool", description="", x=0, y=0, tool="complex_exec")
        self.toolbox.project().add_project_items("Tools", item)  # Add Tool to project
        ind = self.toolbox.project_item_model.find_item("Tool")
        tool = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        # Collect some information
        work_dir = tool._project.work_dir
        basedir = tempfile.mkdtemp(suffix='__toolbox', prefix=tool.tool_specification().short_name + '__', dir=work_dir)
        project_dir = tool._project.project_dir
        source_files = [x.text() for x in tool.source_file_model.findItems("*", Qt.MatchWildcard)]
        input_files = [x.text() for x in tool.input_file_model.findItems("*", Qt.MatchWildcard)]
        output_files = [x.text() for x in tool.output_file_model.findItems("*", Qt.MatchWildcard)]
        # Create a mock data connection directory in the project
        dc_dir = os.path.join(project_dir, "input_dc")
        # Create input files in the above dir
        # Start with mandatory input files
        input_paths = [os.path.join(dc_dir, fn) for fn in input_files]
        # Add some optional input files that match "opt/*.ini"
        dc_opt_dir = os.path.join(dc_dir, "opt")
        input_paths += [os.path.join(dc_opt_dir, fn + ".ini") for fn in ('a', 'b', 'c')]
        # Add some optional input files that match "?abc.txt"
        input_paths += [os.path.join(dc_dir, prefix + "abc.txt") for prefix in ('1', '2', '3')]
        # Make all input files
        for filepath in input_paths:
            dirname, _ = os.path.split(filepath)
            os.makedirs(dirname, exist_ok=True)
            Path(filepath).touch()
        # Create a mock execution instance and make the above paths available for the tool
        mock_exec_inst = tool._project.execution_instance = mock.Mock()
        mock_exec_inst.available_resources.side_effect = lambda n: [
            ProjectItemResource(None, "file", url=Path(fp).as_uri()) for fp in input_paths
        ]
        # Create source files in tool specification source directory
        src_dir = tool.tool_specification().path
        source_paths = [os.path.join(src_dir, path) for path in source_files]
        for filepath in source_paths:
            dirname, _ = os.path.split(filepath)
            os.makedirs(dirname, exist_ok=True)
            Path(filepath).touch()
        # Mock some more stuff needed and execute the tool
        with mock.patch("spinetoolbox.project_items.tool.tool.shutil") as mock_shutil, mock.patch(
            "spinetoolbox.project_items.tool.tool.tempfile"
        ) as mock_tempfile, mock.patch(
            "spinetoolbox.project_items.tool.tool.create_output_dir_timestamp"
        ) as mock_create_output_dir_timestamp, mock.patch.object(
            tool_specifications.ExecutableToolInstance, "execute"
        ) as mock_execute_tool_instance:
            mock_create_output_dir_timestamp.return_value = "mock_timestamp"
            mock_tempfile.mkdtemp.return_value = basedir

            def mock_execute_tool_instance_side_effect():
                """Provides a side effect for ToolInstance execute method."""
                # Check that source and input files were copied to the base directory
                expected_calls = [
                    mock.call(os.path.join(src_dir, fn), os.path.join(basedir, fn)) for fn in source_files
                ]
                expected_calls += [mock.call(os.path.join(dc_dir, fn), os.path.join(basedir, fn)) for fn in input_files]
                mock_shutil.copyfile.assert_has_calls(expected_calls)
                # Create all output files in base dir
                output_paths = [os.path.join(basedir, fn) for fn in output_files]
                for filepath in output_paths:
                    Path(filepath).touch()
                # Emit signal as if the tool had succeeded
                tool.instance.instance_finished_signal.emit(0)

            mock_execute_tool_instance.side_effect = mock_execute_tool_instance_side_effect
            tool.execute()
        self.assertEqual(tool.basedir, basedir)
        # Check that output files were copied to the output dir
        result_dir = os.path.abspath(os.path.join(tool.output_dir, "mock_timestamp"))
        expected_calls = [mock.call(os.path.join(basedir, fn), os.path.join(result_dir, fn)) for fn in output_files]
        mock_shutil.copyfile.assert_has_calls(expected_calls)
        # Check that output files were advertised
        expected_calls = [
            mock.call(
                "Tool",
                ProjectItemResource(
                    tool, "file", url=Path(os.path.join(result_dir, fn)).as_uri(), metadata=dict(is_output=True)
                ),
            )
            for fn in output_files
        ]
        mock_exec_inst.advertise_resources.assert_has_calls(expected_calls)


if __name__ == '__main__':
    unittest.main()
