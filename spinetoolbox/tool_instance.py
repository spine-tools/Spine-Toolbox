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
import tempfile
from PySide2.QtCore import QObject, Signal, Slot
import qsubprocess
from helpers import create_output_dir_timestamp, create_dir


class ToolInstance(QObject):
    """Class for Tool instances.

    Args:
        tool_template (ToolTemplate): Tool for which this instance is created
        toolbox (ToolboxUI): QMainWindow instance
        tool_output_dir (str): Directory where results are saved
        project (SpineToolboxProject): Current project
        execute_in_work (bool): True executes instance in work dir, False executes in Tool template source dir

    Class Variables:
        instance_finished_signal (Signal): Signal to emit when a Tool instance has finished processing
    """

    instance_finished_signal = Signal(int, name="instance_finished_signal")

    def __init__(self, tool_template, toolbox, tool_output_dir, project, execute_in_work):
        """class constructor."""

        super().__init__()  # TODO: Should this be QObject.__init__(self) like in MetaObject class?
        self.tool_template = tool_template
        self._toolbox = toolbox
        self._project = project
        self.execute_in_work = execute_in_work
        self.tool_process = None
        self.tool_output_dir = tool_output_dir
        # Directory where results were saved
        self.output_dir = None
        if self.execute_in_work:  # Execute in work directory
            wrk_dir = self._project.work_dir
            self.basedir = tempfile.mkdtemp(
                suffix='__toolbox', prefix=self.tool_template.short_name + '__', dir=wrk_dir
            )
        else:  # Execute in source directory
            self.basedir = self.tool_template.path
        self.julia_repl_command = None
        self.ipython_command_list = list()
        self.program = None  # Program to start in the subprocess
        self.args = list()  # List of command line arguments for the program
        self.inputfiles = [os.path.join(self.basedir, f) for f in tool_template.inputfiles]
        self.inputfiles_opt = [os.path.join(self.basedir, f) for f in tool_template.inputfiles_opt]
        self.outputfiles = [os.path.join(self.basedir, f) for f in tool_template.outputfiles]
        # Check that required output directories are created
        self.make_work_output_dirs()
        # Checkout Tool template to work directory
        if self.execute_in_work:
            if not self._checkout:
                raise OSError("Could not create Tool instance")
        else:
            # Make source directory anchor with path as tooltip
            src_dir_anchor = (
                "<a style='color:#99CCFF;' title='"
                + self.basedir
                + "' href='file:///"
                + self.basedir
                + "'>source directory</a>"
            )
            self._toolbox.msg.emit(
                "*** Executing Tool template <b>{0}</b> in {1} ***".format(self.tool_template.name, src_dir_anchor)
            )

    @property
    def _checkout(self):
        """Copies Tool template files to work directory."""
        n_copied_files = 0
        # Make work directory anchor with path as tooltip
        work_anchor = (
            "<a style='color:#99CCFF;' title='"
            + self.basedir
            + "' href='file:///"
            + self.basedir
            + "'>work directory</a>"
        )
        self._toolbox.msg.emit(
            "*** Copying Tool template <b>{0}</b> source files to {1} ***".format(self.tool_template.name, work_anchor)
        )
        for filepath in self.tool_template.includes:
            dirname, file_pattern = os.path.split(filepath)
            src_dir = os.path.join(self.tool_template.path, dirname)
            dst_dir = os.path.join(self.basedir, dirname)
            # Create the destination directory
            try:
                create_dir(dst_dir)
            except OSError:
                self._toolbox.msg_error.emit("Creating directory <b>{0}</b> failed".format(dst_dir))
                return False
            # Copy file if necessary
            if file_pattern:
                for src_file in glob.glob(os.path.join(src_dir, file_pattern)):
                    dst_file = os.path.join(dst_dir, os.path.basename(src_file))
                    # logging.debug("Copying file {} to {}".format(src_file, dst_file))
                    try:
                        shutil.copyfile(src_file, dst_file)
                        n_copied_files += 1
                    except OSError as e:
                        logging.error(e)
                        self._toolbox.msg_error.emit(
                            "\tCopying file <b>{0}</b> to <b>{1}</b> failed".format(src_file, dst_file)
                        )
                        return False
        if n_copied_files == 0:
            self._toolbox.msg_warning.emit("Warning: No files copied")
        else:
            self._toolbox.msg.emit("\tCopied <b>{0}</b> file(s)".format(n_copied_files))
        return True

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
        self.handle_output_files(ret)

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
        self.handle_output_files(ret)

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
        self.handle_output_files(ret)

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
        self.handle_output_files(ret)

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
        self.handle_output_files(ret)

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
                self.instance_finished_signal.emit(ret)
                return
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
        self.handle_output_files(ret)

    def handle_output_files(self, ret):
        """Creates a timestamped result directory for Tool template output files. Starts copying Tool
        template output files from work directory to result directory and print messages to Event
        Log depending on how the operation went.

        Args:
            ret (int): Tool template process return value
        """
        output_dir_timestamp = create_output_dir_timestamp()  # Get timestamp when tool finished
        # Create an output folder with timestamp and copy output directly there
        if ret != 0:
            result_path = os.path.abspath(os.path.join(self.tool_output_dir, 'failed', output_dir_timestamp))
        else:
            result_path = os.path.abspath(os.path.join(self.tool_output_dir, output_dir_timestamp))
        try:
            create_dir(result_path)
        except OSError:
            self._toolbox.msg_error.emit(
                "\tError creating timestamped output directory. "
                "Tool template output files not copied. Please check directory permissions."
            )
            self.output_dir = None
            self.instance_finished_signal.emit(ret)
            return
        self.output_dir = result_path
        # Make link to output folder
        result_anchor = (
            "<a style='color:#BB99FF;' title='"
            + result_path
            + "' href='file:///"
            + result_path
            + "'>results directory</a>"
        )
        self._toolbox.msg.emit("*** Archiving output files to {0} ***".format(result_anchor))
        if not self.outputfiles:
            tip_anchor = (
                "<a style='color:#99CCFF;' title='When you add output files to the Tool template,\n "
                "they will be archived into results directory. Also, output files are passed to\n "
                "subsequent project items.' href='#'>Tip</a>"
            )
            self._toolbox.msg_warning.emit("\tNo output files defined for this Tool template. {0}".format(tip_anchor))
        else:
            saved_files, failed_files = self.copy_output(result_path)
            if not saved_files:
                # If no files were saved
                self._toolbox.msg_error.emit("\tNo files saved")
            else:
                # If there are saved files
                self._toolbox.msg.emit("\tThe following output files were saved to results directory")
                for saved_file in saved_files:
                    self._toolbox.msg.emit("\t\t<b>{0}</b>".format(saved_file))
            if failed_files:
                # If saving some or all files failed
                self._toolbox.msg_warning.emit("\tThe following output files were not found")
                for failed_file in failed_files:
                    failed_fname = os.path.split(failed_file)[1]
                    self._toolbox.msg_warning.emit("\t\t<b>{0}</b>".format(failed_fname))
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

    def copy_output(self, target_dir):
        """Copies Tool template output files from work directory to given target directory.

        Args:
            target_dir (str): Destination directory for Tool template output files

        Returns:
            tuple: Contains two lists. The first list contains paths to successfully
            copied files. The second list contains paths (or patterns) of Tool template
            output files that were not found.

        Raises:
            OSError: If creating a directory fails.
        """
        failed_files = list()
        saved_files = list()
        # logging.debug("Saving result files to <{0}>".format(target_dir))
        for pattern in self.tool_template.outputfiles:
            # Create subdirectories if necessary
            dst_subdir, fname_pattern = os.path.split(pattern)
            # logging.debug("pattern:{0} dst_subdir:{1} fname_pattern:{2}".format(pattern,
            #                                                                     dst_subdir, fname_pattern))
            if not dst_subdir:
                # No subdirectories to create
                # self._toolbox.msg.emit("\tCopying file <b>{0}</b>".format(fname))
                target = target_dir
            else:
                # Create subdirectory structure to result directory
                result_subdir_path = os.path.abspath(os.path.join(target_dir, dst_subdir))
                if not os.path.exists(result_subdir_path):
                    try:
                        create_dir(result_subdir_path)
                    except OSError:
                        self._toolbox.msg_error.emit(
                            "[OSError] Creating directory <b>{0}</b> failed.".format(result_subdir_path)
                        )
                        continue
                    self._toolbox.msg.emit(
                        "\tCreated result subdirectory <b>{0}{1}</b>".format(os.path.sep, dst_subdir)
                    )
                target = result_subdir_path
            # Check for wildcards in pattern
            if ('*' in pattern) or ('?' in pattern):
                for fname_path in glob.glob(os.path.join(self.basedir, pattern)):  # fname_path is a full path
                    fname = os.path.split(fname_path)[1]  # File name (no path)
                    dst = os.path.join(target, fname)
                    try:
                        shutil.copy(fname_path, dst)
                    except OSError:
                        self._toolbox.msg_error.emit("[OSError] Copying pattern {0} to {1} failed"
                                                     .format(fname_path, dst))
                    self._toolbox.project().execution_instance.append_tool_output_file(dst)
                    saved_files.append(os.path.join(dst_subdir, fname))
            else:
                output_file = os.path.join(self.basedir, pattern)
                # logging.debug("Looking for {0}".format(output_file))
                if not os.path.isfile(output_file):
                    failed_files.append(pattern)
                    continue
                # logging.debug("Saving file {0}".format(fname_pattern))
                dst = os.path.join(target, fname_pattern)
                # logging.debug("Copying to {0}".format(dst))
                try:
                    shutil.copy(output_file, dst)
                except OSError:
                    self._toolbox.msg_error.emit("[OSError] Copying output file {0} to {1} failed"
                                                 .format(output_file, dst))
                self._toolbox.project().execution_instance.append_tool_output_file(dst)
                saved_files.append(pattern)
        return saved_files, failed_files

    def make_work_output_dirs(self):
        """Makes sure that work directory has the necessary output directories for Tool output files.
        Checks only "outputfiles" list. Alternatively you can add directories to "inputfiles" list
        in the tool definition file.

        Returns:
            bool: True for success, False otherwise.

        Raises:
            OSError: If creating an output directory to work fails.
        """
        # TODO: Remove duplicate directory names from the list of created directories.
        for path in self.tool_template.outputfiles:
            dirname = os.path.split(path)[0]
            if dirname == '':
                continue
            dst_dir = os.path.join(self.basedir, dirname)
            try:
                create_dir(dst_dir)
            except OSError:
                self._toolbox.msg_error.emit("Creating work output directory '{}' failed".format(dst_dir))
                return False
        return True
