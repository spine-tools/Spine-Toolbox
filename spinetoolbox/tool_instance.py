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
import sys
import shutil
from PySide2.QtCore import QObject, Signal, Slot
from .config import GAMS_EXECUTABLE, JULIA_EXECUTABLE, PYTHON_EXECUTABLE
from .execution_managers import ConsoleExecutionManager, QProcessExecutionManager


class ToolInstance(QObject):
    """Tool instance base class."""

    instance_finished_signal = Signal(int, name="instance_finished_signal")
    """Signal to emit when a Tool instance has finished processing"""

    def __init__(self, toolbox, tool_specification, basedir):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            tool_specification (ToolSpecification): the tool specification for this instance
            basedir (str): the path to the directory where this instance should run
        """
        super().__init__()  # TODO: Should this be QObject.__init__(self) like in MetaObject class?
        self._toolbox = toolbox
        self.tool_specification = tool_specification
        self.basedir = basedir
        self.exec_mngr = None
        self.program = None  # Program to start in the subprocess
        self.args = list()  # List of command line arguments for the program

    def is_running(self):
        return self.exec_mngr is not None

    def terminate_instance(self):
        """Terminates Tool instance execution."""
        if not self.exec_mngr:
            return
        self.exec_mngr.stop_execution()
        self.exec_mngr = None

    def remove(self):
        """[Obsolete] Removes Tool instance files from work directory."""
        shutil.rmtree(self.basedir, ignore_errors=True)

    def prepare(self):
        """Prepares this instance for execution.
        Implement in subclasses to perform specific initialization.
        """
        raise NotImplementedError()

    def execute(self, **kwargs):
        """Executes a prepared instance. Implement in subclasses."""
        raise NotImplementedError()

    @Slot(int, name="handle_execution_finished")
    def handle_execution_finished(self, ret):
        """Handles execution finished.

        Args:
            ret (int)
        """
        raise NotImplementedError()

    def append_cmdline_args(self):
        """Appends Tool specification command line args into instance args list."""
        self.args += self.tool_specification.get_cmdline_args()


class GAMSToolInstance(ToolInstance):
    """Class for GAMS Tool instances."""

    def prepare(self):
        """Prepares this instance for execution."""
        gams_path = self._toolbox.qsettings().value("appSettings/gamsPath", defaultValue="")
        if gams_path != '':
            gams_exe = gams_path
        else:
            gams_exe = GAMS_EXECUTABLE
        self.program = gams_exe
        self.args.append(self.tool_specification.main_prgm)
        self.args.append("curDir=")
        self.args.append("{0}".format(self.basedir))
        self.args.append("logoption=3")  # TODO: This should be an option in Settings
        self.append_cmdline_args()  # Append Tool specific cmd line args into args list

    def execute(self, **kwargs):
        """Executes a prepared instance."""
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.program, self.args, **kwargs)
        self.exec_mngr.execution_finished.connect(self.handle_execution_finished)
        # TODO: Check if this sets the curDir argument. Is the curDir arg now useless?
        self.exec_mngr.start_execution(workdir=self.basedir)

    @Slot(int)
    def handle_execution_finished(self, ret):
        """Handles execution finished.

        Args:
            ret (int)
        """
        self.exec_mngr.deleteLater()
        if self.exec_mngr.process_failed:  # process_failed should be True if ret != 0
            if self.exec_mngr.process_failed_to_start:
                self._toolbox.msg_error.emit(
                    "\t<b>{0}</b> failed to start. Make sure that "
                    "GAMS is installed properly on your computer "
                    "and GAMS directory is given in Settings (F1).".format(self.exec_mngr.program())
                )
            else:
                try:
                    return_msg = self.tool_specification.return_codes[ret]
                    self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self._toolbox.msg.emit("\tTool specification execution finished")
        self.exec_mngr = None
        self.instance_finished_signal.emit(ret)


class JuliaToolInstance(ToolInstance):
    """Class for Julia Tool instances."""

    def __init__(self, toolbox, tool_specification, basedir):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            tool_specification (ToolSpecification): the tool specification for this instance
            basedir (str): the path to the directory where this instance should run
        """
        super().__init__(toolbox, tool_specification, basedir)
        self.ijulia_command_list = list()

    def prepare(self):
        """Prepares this instance for execution."""
        work_dir = self.basedir
        use_embedded_julia = self._toolbox.qsettings().value("appSettings/useEmbeddedJulia", defaultValue="2")
        if use_embedded_julia == "2":
            # Prepare Julia REPL command
            # TODO: See if this can be simplified
            mod_work_dir = work_dir.__repr__().strip("'")
            args = r'["' + r'", "'.join(self.tool_specification.get_cmdline_args()) + r'"]'
            self.ijulia_command_list += [
                r'cd("{}");'.format(mod_work_dir),
                r'empty!(ARGS);',
                r'append!(ARGS, {});'.format(args),
                r'include("{}")'.format(self.tool_specification.main_prgm),
            ]
        else:
            # Prepare command "julia --project={PROJECT_DIR} script.jl"
            julia_path = self._toolbox.qsettings().value("appSettings/juliaPath", defaultValue="")
            if julia_path != "":
                julia_exe = julia_path
            else:
                julia_exe = JULIA_EXECUTABLE
            julia_project_path = self._toolbox.qsettings().value("appSettings/juliaProjectPath", defaultValue="")
            if julia_project_path == "":
                julia_project_path = "@."
            script_path = os.path.join(work_dir, self.tool_specification.main_prgm)
            self.program = julia_exe
            self.args.append(f"--project={julia_project_path}")
            self.args.append(script_path)
            self.append_cmdline_args()

    def execute(self, **kwargs):
        """Executes a prepared instance."""
        if self._toolbox.qsettings().value("appSettings/useEmbeddedJulia", defaultValue="2") == "2":
            self.exec_mngr = ConsoleExecutionManager(self._toolbox, self._toolbox.julia_repl, self.ijulia_command_list)
            self.exec_mngr.execution_finished.connect(self.handle_repl_execution_finished)
            self.exec_mngr.start_execution()
        else:
            self.exec_mngr = QProcessExecutionManager(self._toolbox, self.program, self.args, **kwargs)
            self.exec_mngr.execution_finished.connect(self.handle_execution_finished)
            # On Julia the Qprocess workdir must be set to the path where the main script is
            # Otherwise it doesn't find input files in subdirectories
            self.exec_mngr.start_execution(workdir=self.basedir)

    @Slot(int)
    def handle_repl_execution_finished(self, ret):
        """Handles repl-execution finished.

        Args:
            ret (int): Tool specification process return value
        """
        self.exec_mngr.deleteLater()
        if ret != 0:
            try:
                return_msg = self.tool_specification.return_codes[ret]
                self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code: {1}]".format(return_msg, ret))
            except KeyError:
                self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:
            self._toolbox.msg.emit("\tTool specification execution finished")
        self.exec_mngr = None
        self.instance_finished_signal.emit(ret)

    @Slot(int)
    def handle_execution_finished(self, ret):
        """Handles execution finished.

        Args:
            ret (int): Tool specification process return value
        """
        self.exec_mngr.deleteLater()
        if self.exec_mngr.process_failed:  # process_failed should be True if ret != 0
            if self.exec_mngr.process_failed_to_start:
                self._toolbox.msg_error.emit(
                    "\t<b>{0}</b> failed to start. Make sure that "
                    "Julia is installed properly on your computer.".format(self.exec_mngr.program())
                )
            else:
                try:
                    return_msg = self.tool_specification.return_codes[ret]
                    self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self._toolbox.msg.emit("\tTool specification execution finished")
        self.exec_mngr = None
        self.instance_finished_signal.emit(ret)


class PythonToolInstance(ToolInstance):
    """Class for Python Tool instances."""

    def __init__(self, toolbox, tool_specification, basedir):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            tool_specification (ToolSpecification): the tool specification for this instance
            basedir (str): the path to the directory where this instance should run
        """
        super().__init__(toolbox, tool_specification, basedir)
        self.ipython_command_list = list()

    def prepare(self):
        """Prepares this instance for execution."""
        work_dir = self.basedir
        use_embedded_python = self._toolbox.qsettings().value("appSettings/useEmbeddedPython", defaultValue="0")
        if use_embedded_python == "2":
            # Prepare a command list (FIFO queue) with two commands for Python Console
            # 1st cmd: Change current work directory
            # 2nd cmd: Run script with given args
            # Cast args in list to strings and combine them to a single string
            args = " ".join([repr(x) for x in self.tool_specification.get_cmdline_args()])
            cd_work_dir_cmd = "%cd -q {0} ".format(work_dir)  # -q: quiet
            run_script_cmd = "%run \"{0}\" {1}".format(self.tool_specification.main_prgm, args)
            # Populate FIFO command queue
            self.ipython_command_list.append(cd_work_dir_cmd)
            self.ipython_command_list.append(run_script_cmd)
        else:
            # Prepare command "python script.py"
            python_path = self._toolbox.qsettings().value("appSettings/pythonPath", defaultValue="")
            if python_path != "":
                python_cmd = python_path
            else:
                python_cmd = PYTHON_EXECUTABLE
            script_path = os.path.join(work_dir, self.tool_specification.main_prgm)
            self.program = python_cmd
            self.args.append(script_path)  # TODO: Why are we doing this?
            self.append_cmdline_args()

    def execute(self, **kwargs):
        """Executes a prepared instance."""
        if self._toolbox.qsettings().value("appSettings/useEmbeddedPython", defaultValue="0") == "2":
            self.exec_mngr = ConsoleExecutionManager(
                self._toolbox, self._toolbox.python_repl, self.ipython_command_list
            )
            self.exec_mngr.execution_finished.connect(self.handle_console_execution_finished)
            self.exec_mngr.start_execution()
        else:
            self.exec_mngr = QProcessExecutionManager(self._toolbox, self.program, self.args, **kwargs)
            self.exec_mngr.execution_finished.connect(self.handle_execution_finished)
            self.exec_mngr.start_execution(workdir=self.basedir)

    @Slot(int)
    def handle_console_execution_finished(self, ret):
        """Handles console-execution finished.

        Args:
            ret (int): Tool specification process return value
        """
        self.exec_mngr.deleteLater()
        if ret != 0:
            try:
                return_msg = self.tool_specification.return_codes[ret]
                self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code: {1}]".format(return_msg, ret))
            except KeyError:
                self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:
            self._toolbox.msg.emit("\tTool specification execution finished")
        self.exec_mngr = None
        self.instance_finished_signal.emit(ret)

    @Slot(int)
    def handle_execution_finished(self, ret):
        """Handles execution finished.

        Args:
            ret (int): Tool specification process return value
        """
        self.exec_mngr.deleteLater()
        if self.exec_mngr.process_failed:  # process_failed should be True if ret != 0
            if self.exec_mngr.process_failed_to_start:
                self._toolbox.msg_error.emit(
                    "\t<b>{0}</b> failed to start. Make sure that "
                    "Python is installed properly on your computer.".format(self.exec_mngr.program())
                )
            else:
                try:
                    return_msg = self.tool_specification.return_codes[ret]
                    self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self._toolbox.msg.emit("\tTool specification execution finished")
        self.exec_mngr.deleteLater()
        self.exec_mngr = None
        self.instance_finished_signal.emit(ret)


class ExecutableToolInstance(ToolInstance):
    """Class for Executable Tool instances."""

    def prepare(self):
        """Prepares this instance for execution."""
        batch_path = os.path.join(self.basedir, self.tool_specification.main_prgm)
        if sys.platform != "win32":
            self.program = "sh"
            self.args.append(batch_path)
        else:
            self.program = batch_path
        self.append_cmdline_args()  # Append Tool specific cmd line args into args list

    def execute(self, **kwargs):
        """Executes a prepared instance."""
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.program, self.args, **kwargs)
        self.exec_mngr.execution_finished.connect(self.handle_execution_finished)
        self.exec_mngr.start_execution(workdir=self.basedir)

    @Slot(int)
    def handle_execution_finished(self, ret):
        """Handles execution finished.

        Args:
            ret (int): Tool specification process return value
        """
        self.exec_mngr.deleteLater()
        if self.exec_mngr.process_failed:  # process_failed should be True if ret != 0
            if self.exec_mngr.process_failed_to_start:
                self._toolbox.msg_error.emit("\t<b>{0}</b> failed to start.".format(self.exec_mngr.program()))
            else:
                try:
                    return_msg = self.tool_specification.return_codes[ret]
                    self._toolbox.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self._toolbox.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self._toolbox.msg.emit("\tTool specification execution finished")
        self.exec_mngr.deleteLater()
        self.exec_mngr = None
        self.instance_finished_signal.emit(ret)
