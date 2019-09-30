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
Contains ToolInstance class.

:authors: P. Savolainen (VTT), E. Rinne (VTT)
:date:   1.2.2018
"""

import os
import shutil
import glob
import logging
from PySide2.QtCore import QObject, Signal, Slot
import qsubprocess
from helpers import create_dir


class ToolInstance(QObject):
    """Class for Tool instances.

    Args:
        tool (Tool): Tool for which this instance is created

    Class Variables:
        instance_finished_signal (Signal): Signal to emit when a Tool instance has finished processing
    """

    instance_finished_signal = Signal(int, name="instance_finished_signal")

    def __init__(self, toolbox, tool_template, basedir):
        """class constructor."""
        super().__init__()  # TODO: Should this be QObject.__init__(self) like in MetaObject class?
        self._toolbox = toolbox
        self.tool_template = tool_template
        self.basedir = basedir
        self.tool_process = None
        self.julia_repl_command = None
        self.ipython_command_list = list()
        self.program = None  # Program to start in the subprocess
        self.args = list()  # List of command line arguments for the program
        # Checkout Tool template to work directory

    def execute(self):
        """Starts executing Tool template instance in Julia Console, Python Console or in a sub-process."""
        self._toolbox.msg.emit("*** Starting Tool template <b>{0}</b> ***".format(self.tool_template.name))
        if self.tool_template.tooltype == "julia":
            if self._toolbox.qsettings().value("appSettings/useEmbeddedJulia", defaultValue="2") == "2":
                self.tool_process = self._toolbox.julia_repl
                self.tool_process.execution_finished_signal.connect(self.julia_repl_tool_finished)
                # self._toolbox.msg.emit("\tCommand:<b>{0}</b>".format(self.julia_repl_command))
                self.tool_process.execute_instance(self.julia_repl_command)
            else:
                self.tool_process = qsubprocess.QSubProcess(self._toolbox, self.program, self.args)
                self.tool_process.subprocess_finished_signal.connect(self.julia_tool_finished)
                # On Julia the Qprocess workdir must be set to the path where the main script is
                # Otherwise it doesn't find input files in subdirectories
                self.tool_process.start_process(workdir=self.basedir)
        if self.tool_template.tooltype == "python":
            if self._toolbox.qsettings().value("appSettings/useEmbeddedPython", defaultValue="0") == "2":
                self.tool_process = self._toolbox.python_repl
                self.tool_process.execution_finished_signal.connect(self.python_console_tool_finished)
                k_tuple = self.tool_process.python_kernel_name()
                if not k_tuple:
                    self.python_console_tool_finished(-999)
                    return
                kern_name = k_tuple[0]
                kern_display_name = k_tuple[1]
                # Check if this kernel is already running
                if self.tool_process.kernel_manager and self.tool_process.kernel_name == kern_name:
                    self.tool_process.execute_instance(self.ipython_command_list)
                else:
                    # Append command to buffer and start executing when kernel is up and running
                    self.tool_process.commands = self.ipython_command_list
                    self.tool_process.launch_kernel(kern_name, kern_display_name)
            else:
                self.tool_process = qsubprocess.QSubProcess(self._toolbox, self.program, self.args)
                self.tool_process.subprocess_finished_signal.connect(self.python_tool_finished)
                self.tool_process.start_process(workdir=self.basedir)
        elif self.tool_template.tooltype == "gams":
            self.tool_process = qsubprocess.QSubProcess(self._toolbox, self.program, self.args)
            self.tool_process.subprocess_finished_signal.connect(self.gams_tool_finished)
            # self.tool_process.start_process(workdir=os.path.split(self.program)[0])
            # TODO: Check if this sets the curDir argument. Is the curDir arg now useless?
            self.tool_process.start_process(workdir=self.basedir)
        elif self.tool_template.tooltype == "executable":
            self.tool_process = qsubprocess.QSubProcess(self._toolbox, self.program, self.args)
            self.tool_process.subprocess_finished_signal.connect(self.executable_tool_finished)
            self.tool_process.start_process(workdir=self.basedir)

    @Slot(int, name="julia_repl_tool_finished")
    def julia_repl_tool_finished(self, ret):
        """Runs when Julia tool using Julia Console has finished processing.

        Args:
            ret (int): Tool template process return value
        """
        self.tool_process.execution_finished_signal.disconnect(self.julia_repl_tool_finished)  # Disconnect after exec.
        if ret != 0:
            if self.tool_process.execution_failed_to_start:
                # TODO: This should be a choice given to the user. It's a bit confusing now.
                self._toolbox.msg.emit("")
                self._toolbox.msg_warning.emit("\tSpawning a new process for executing the Tool template")
                self.tool_process = qsubprocess.QSubProcess(self._toolbox, self.program, self.args)
                self.tool_process.subprocess_finished_signal.connect(self.julia_tool_finished)
                self.tool_process.start_process(workdir=self.basedir)
                return
            try:
                return_msg = self.tool_template.return_codes[ret]
                self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
            except KeyError:
                self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:
            self._toolbox.msg.emit("\tTool template execution finished")
        self.tool_process = None
        self.instance_finished_signal.emit(ret)

    @Slot(int, name="julia_tool_finished")
    def julia_tool_finished(self, ret):
        """Runs when Julia tool from command line (without REPL) has finished processing.

        Args:
            ret (int): Tool template process return value
        """
        self.tool_process.subprocess_finished_signal.disconnect(self.julia_tool_finished)  # Disconnect signal
        if self.tool_process.process_failed:  # process_failed should be True if ret != 0
            if self.tool_process.process_failed_to_start:
                self._toolbox.msg_error.emit(
                    "\t<b>{0}</b> failed to start. Make sure that "
                    "Julia is installed properly on your computer.".format(self.tool_process.program())
                )
            else:
                try:
                    return_msg = self.tool_template.return_codes[ret]
                    self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self._toolbox.msg.emit("\tTool template execution finished")
        self.tool_process.deleteLater()
        self.tool_process = None
        self.instance_finished_signal.emit(ret)

    @Slot(int, name="python_console_tool_finished")
    def python_console_tool_finished(self, ret):
        """Runs when Python Tool in Python Console has finished processing.

        Args:
            ret (int): Tool template process return value
        """
        self.tool_process.execution_finished_signal.disconnect(self.python_console_tool_finished)
        if ret != 0:
            if self.tool_process.execution_failed_to_start:
                # TODO: This should be a choice given to the user. It's a bit confusing now.
                self._toolbox.msg.emit("")
                self._toolbox.msg_warning.emit("\tSpawning a new process for executing the Tool template")
                self.tool_process = qsubprocess.QSubProcess(self._toolbox, self.program, self.args)
                self.tool_process.subprocess_finished_signal.connect(self.python_tool_finished)
                self.tool_process.start_process(workdir=self.basedir)
                return
            try:
                return_msg = self.tool_template.return_codes[ret]
                self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
            except KeyError:
                self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:
            self._toolbox.msg.emit("\tTool template execution finished")
        self.tool_process = None
        self.instance_finished_signal.emit(ret)

    @Slot(int, name="python_tool_finished")
    def python_tool_finished(self, ret):
        """Runs when Python tool from command line has finished processing.

        Args:
            ret (int): Tool template process return value
        """
        self.tool_process.subprocess_finished_signal.disconnect(self.python_tool_finished)  # Disconnect signal
        if self.tool_process.process_failed:  # process_failed should be True if ret != 0
            if self.tool_process.process_failed_to_start:
                self._toolbox.msg_error.emit(
                    "\t<b>{0}</b> failed to start. Make sure that "
                    "Python is installed properly on your computer.".format(self.tool_process.program())
                )
            else:
                try:
                    return_msg = self.tool_template.return_codes[ret]
                    self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self._toolbox.msg.emit("\tTool template execution finished")
        self.tool_process.deleteLater()
        self.tool_process = None
        self.instance_finished_signal.emit(ret)

    @Slot(int, name="gams_tool_finished")
    def gams_tool_finished(self, ret):
        """Runs when GAMS tool has finished processing.

        Args:
            ret (int): Tool template process return value
        """
        self.tool_process.subprocess_finished_signal.disconnect(self.gams_tool_finished)  # Disconnect after execution
        if self.tool_process.process_failed:  # process_failed should be True if ret != 0
            if self.tool_process.process_failed_to_start:
                self._toolbox.msg_error.emit(
                    "\t<b>{0}</b> failed to start. Make sure that "
                    "GAMS is installed properly on your computer "
                    "and GAMS directory is given in Settings (F1).".format(self.tool_process.program())
                )
            else:
                try:
                    return_msg = self.tool_template.return_codes[ret]
                    self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self._toolbox.msg.emit("\tTool template execution finished")
        self.tool_process.deleteLater()
        self.tool_process = None
        self.instance_finished_signal.emit(ret)

    @Slot(int, name="executable_tool_finished")
    def executable_tool_finished(self, ret):
        """Runs when an executable tool has finished processing.

        Args:
            ret (int): Tool template process return value
        """
        self.tool_process.subprocess_finished_signal.disconnect(self.executable_tool_finished)
        if self.tool_process.process_failed:  # process_failed should be True if ret != 0
            if self.tool_process.process_failed_to_start:
                self._toolbox.msg_error.emit("\t<b>{0}</b> failed to start.".format(self.tool_process.program()))
            else:
                try:
                    return_msg = self.tool_template.return_codes[ret]
                    self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self._toolbox.msg.emit("\tTool template execution finished")
        self.tool_process.deleteLater()
        self.tool_process = None
        self.instance_finished_signal.emit(ret)

    def terminate_instance(self):
        """Terminates Tool instance execution."""
        if not self.tool_process:
            self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-2)
            return
        # Disconnect tool_process signals
        try:
            self.tool_process.execution_finished_signal.disconnect()
        except AttributeError:
            pass
        try:
            self.tool_process.subprocess_finished_signal.disconnect()
        except AttributeError:
            pass
        self.tool_process.terminate_process()

    def remove(self):
        """[Obsolete] Removes Tool instance files from work directory."""
        shutil.rmtree(self.basedir, ignore_errors=True)
