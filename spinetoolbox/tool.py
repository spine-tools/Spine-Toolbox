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
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        tool_candidate (ToolCandidate): Tool of this Tool
    """
    def __init__(self, parent, name, description, project, tool_candidate):
        """Class constructor."""
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Tool"
        self._project = project
        self._widget = ToolSubWindowWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._tool = self.set_tool(tool_candidate)
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        self.extra_cmdline_args = ''  # This may be used for additional Tool specific command line arguments
        # Directory where results are saved
        self.output_dir = os.path.join(self._project.project_dir, TOOL_OUTPUT_DIR, self.short_name)
        self.connect_signals()

    def connect_signals(self):
        """Connect this tool's signals to slots."""
        self._widget.ui.pushButton_details.clicked.connect(self.show_details)
        self._widget.ui.pushButton_execute.clicked.connect(self.execute)
        self._widget.ui.pushButton_x.clicked.connect(self.remove_tool)

    @Slot(name='show_details')
    def show_details(self):
        """Details button clicked."""
        if not self.tool():
            self._parent.msg_warning.emit("No Tool Template")
            return
        # Print the tool definition file
        tool_def = self.tool().get_def_path()
        try:
            with open(tool_def, 'r') as fp:
                try:
                    definition = json.load(fp)
                except ValueError:
                    self._parent.msg_error.emit("Tool definition file not valid")
                    logging.exception("Loading JSON data failed")
                    return
        except FileNotFoundError:
            self._parent.msg_error.emit("Tool definition file <b>{0}</b> not found".format(tool_def))
            return
        self._parent.msg.emit("Tool definition file contents:\n{0}".format(json.dumps(definition, sort_keys=True, indent=4)))

    @Slot(name='execute')
    def execute(self):
        """Execute button clicked."""
        if not self.tool():
            self._parent.msg_warning.emit("No Tool to execute")
            return
        self._parent.msg.emit("Executing Tool <b>{0}</b>".format(self.name))
        try:
            self.instance = ToolInstance(self.tool(), self._parent, self.output_dir, self._project)
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
            self._parent.msg_success.emit("Tool {0} execution finished".format(self.tool().name))
        else:
            self._parent.msg_error.emit("Tool {0} execution failed".format(self.tool().name))

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    def tool(self):
        """Return Tool candidate."""
        return self._tool

    @Slot(name='remove_tool')
    def remove_tool(self):
        """Remove Tool from this Tool."""
        self._tool = self.set_tool(None)

    def set_tool(self, tool_candidate):
        """Set tool candidate for this Tool. Remove tool candidate by giving None as argument.

        Args:
            tool_candidate (ToolCandidate): Candidate for this Tool. None removes the candidate.

        Returns:
            ToolCandidate or None if no Tool Candidate set for this Tool.
        """
        if not tool_candidate:
            self._widget.ui.lineEdit_tool.setText("")
            self._widget.ui.lineEdit_tool_args.setText("")
            return None
        else:
            self._widget.ui.lineEdit_tool.setText(tool_candidate.name)
            self._widget.ui.lineEdit_tool_args.setText(tool_candidate.cmdline_args)
            return tool_candidate

    def update_instance(self):
        """Initialize and update instance so that it is ready for processing. Maybe this is where Tool
        type specific initialization should happen (whether instance is GAMS or Julia Model)."""
        gams_path = self._parent._config.get("settings", "gams_path")
        gams_exe_path = GAMS_EXECUTABLE
        if not gams_path == '':
            gams_exe_path = os.path.join(gams_path, GAMS_EXECUTABLE)
        main_dir = self.instance.basedir  # TODO: Is main_dir needed?
        command = '{} "{}" Curdir="{}" logoption=3'.format(gams_exe_path, self.tool().main_prgm, main_dir)
        # Append Tool specific command line arguments to command (if present and implemented)
        self.instance.command = self.append_cmdline_args(command)

    def append_cmdline_args(self, command):
        """Append command line arguments to a command.

        Args:
            command (str): Tool command
        """
        if (self.extra_cmdline_args is not None) and (not self.extra_cmdline_args == ''):
            if (self.tool().cmdline_args is not None) and (not self.tool().cmdline_args == ''):
                command += ' ' + self.tool().cmdline_args + ' ' + self.extra_cmdline_args
            else:
                command += ' ' + self.extra_cmdline_args
        else:
            if (self.tool().cmdline_args is not None) and (not self.tool().cmdline_args == ''):
                command += ' ' + self.tool().cmdline_args
        return command
