#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Tool class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.12.2017
"""

import logging
import os
import json
from metaobject import MetaObject
from widgets.sw_tool_widget import ToolSubWindowWidget
from PySide2.QtCore import Slot
from tool_instance import ToolInstance
from config import TOOL_OUTPUT_DIR, GAMS_EXECUTABLE


class Tool(MetaObject):
    """Tool class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        tool_template (ToolTemplate): Template for this Tool
    """
    def __init__(self, parent, name, description, project, tool_template):
        """Class constructor."""
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Tool"
        self.item_category = "Tools"
        self._project = project
        self._widget = ToolSubWindowWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._tool_template = None
        self.set_tool_template(tool_template)
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        self.extra_cmdline_args = ''  # This may be used for additional Tool specific command line arguments
        # Directory where results are saved
        self.output_dir = os.path.join(self._project.project_dir, TOOL_OUTPUT_DIR, self.short_name)
        self.connect_signals()

    def connect_signals(self):
        """Connect this tool's signals to slots."""
        self._widget.ui.pushButton_details.clicked.connect(self.show_details)
        self._widget.ui.pushButton_connections.clicked.connect(self.show_connections)
        self._widget.ui.pushButton_execute.clicked.connect(self.execute)
        self._widget.ui.pushButton_x.clicked.connect(self.remove_tool_template)

    @Slot(name='show_details')
    def show_details(self):
        """Details button clicked."""
        if not self.tool_template():
            self._parent.msg_warning.emit("No Tool Template")
            return
        definition = self.read_tool_def(self.tool_template().get_def_path())
        if not definition:
            return
        self._parent.msg.emit("Tool template file contents:\n{0}"
                              .format(json.dumps(definition, sort_keys=True, indent=4)))

    @Slot(name="show_connections")
    def show_connections(self):
        """Show connections of this Tool."""
        inputs = self._parent.connection_model.input_items(self.name)
        outputs = self._parent.connection_model.output_items(self.name)
        self._parent.msg.emit("<br/><b>{0}</b>".format(self.name))
        self._parent.msg.emit("Input items")
        if not inputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in inputs:
                self._parent.msg_warning.emit("{0}".format(item))
        self._parent.msg.emit("Output items")
        if not outputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in outputs:
                self._parent.msg_warning.emit("{0}".format(item))

    def tool_template(self):
        """Returns Tool template."""
        return self._tool_template

    @Slot(name='remove_tool_template')
    def remove_tool_template(self):
        """Removes Template from this Tool. Needed as an 'X' button slot"""
        self.set_tool_template(None)

    def set_tool_template(self, tool_template):
        """Sets Tool Template for this Tool. Removes Tool Template if None given as argument.

        Args:
            tool_template (ToolTemplate): Template for this Tool. None removes the template.

        Returns:
            ToolTemplate or None if no Tool Template set for this Tool.
        """
        self._tool_template = tool_template
        self.update_tool_ui()

    def update_tool_ui(self):
        """Update Tool UI to show Tool template details."""
        if not self.tool_template():
            self._widget.ui.lineEdit_tool.setText("")
            self._widget.ui.lineEdit_tool_args.setText("")
            self._widget.populate_input_files_list(None)
            self._widget.populate_output_files_list(None)
        else:
            self._widget.ui.lineEdit_tool.setText(self.tool_template().name)
            self._widget.ui.lineEdit_tool_args.setText(self.tool_template().cmdline_args)
            self.update_input_files()
            self.update_output_files()

    def update_input_files(self):
        """Show input files in QListView."""
        if not self.tool_template():
            return
        def_path = self.tool_template().get_def_path()
        definition = self.read_tool_def(def_path)
        if not definition:
            return
        try:
            input_files = definition["inputfiles"]
        except KeyError:
            logging.error("Key 'inputfiles' not found in file {0}".format(def_path))
            return
        self._widget.populate_input_files_list(input_files)

    def update_output_files(self):
        """Show output files in QListView."""
        if not self.tool_template():
            return
        def_path = self.tool_template().get_def_path()
        definition = self.read_tool_def(def_path)
        if not definition:
            return
        try:
            output_files = definition["outputfiles"]
        except KeyError:
            logging.error("Key 'outputfiles' not found in file {0}".format(def_path))
            return
        self._widget.populate_output_files_list(output_files)

    def read_tool_def(self, tool_def_file):
        """Return tool template definition file contents or None if operation failed."""
        try:
            with open(tool_def_file, 'r') as fp:
                try:
                    definition = json.load(fp)
                except ValueError:
                    self._parent.msg_error.emit("Tool definition file not valid")
                    logging.exception("Loading JSON data failed")
                    return None
        except FileNotFoundError:
            self._parent.msg_error.emit("Tool definition file <b>{0}</b> not found".format(tool_def_file))
            return None
        return definition

    @Slot(name='execute')
    def execute(self):
        """Execute button clicked."""
        if not self.tool_template():
            self._parent.msg_warning.emit("No Tool to execute")
            return
        self._parent.msg.emit("Executing Tool <b>{0}</b>".format(self.name))
        try:
            self.instance = ToolInstance(self.tool_template(), self._parent, self.output_dir, self._project)
        except OSError as e:
            self._parent.msg_error.emit("Tool instance creation failed. {0}".format(e))
            return
        self.update_instance()  # Make command and stuff
        self.instance.instance_finished_signal.connect(self.execution_finished)
        self.instance.execute()

    @Slot(int, name="execution_finished")
    def execution_finished(self, return_code):
        """Tool execution finished."""
        if return_code == 0:
            self._parent.msg_success.emit("Tool {0} execution finished".format(self.tool_template().name))
        else:
            self._parent.msg_error.emit("Tool {0} execution failed".format(self.tool_template().name))

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    def update_instance(self):
        """Initialize and update instance so that it is ready for processing. Maybe this is where Tool
        type specific initialization should happen (whether instance is GAMS or Julia Model)."""
        gams_path = self._parent._config.get("settings", "gams_path")
        gams_exe_path = GAMS_EXECUTABLE
        if not gams_path == '':
            gams_exe_path = os.path.join(gams_path, GAMS_EXECUTABLE)
        main_dir = self.instance.basedir  # TODO: Is main_dir needed?
        command = '{} "{}" Curdir="{}" logoption=3'.format(gams_exe_path, self.tool_template().main_prgm, main_dir)
        # Append Tool specific command line arguments to command (if present and implemented)
        self.instance.command = self.append_cmdline_args(command)

    def append_cmdline_args(self, command):
        """Append command line arguments to a command.

        Args:
            command (str): Command that starts processing the Tool in a subprocess
        """
        if (self.extra_cmdline_args is not None) and (not self.extra_cmdline_args == ''):
            if (self.tool_template().cmdline_args is not None) and (not self.tool_template().cmdline_args == ''):
                command += ' ' + self.tool_template().cmdline_args + ' ' + self.extra_cmdline_args
            else:
                command += ' ' + self.extra_cmdline_args
        else:
            if (self.tool_template().cmdline_args is not None) and (not self.tool_template().cmdline_args == ''):
                command += ' ' + self.tool_template().cmdline_args
        return command
