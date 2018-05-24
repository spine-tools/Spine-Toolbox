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
ToolInstance class definition.

:authors: Pekka Savolainen <pekka.t.savolainen@vtt.fi>, Erkka Rinne <erkka.rinne@vtt.fi>
:date:   1.2.2018
"""

import os
import shutil
import glob
import logging
import tempfile
from PySide2.QtCore import QObject, Signal, Slot, SIGNAL
import qsubprocess
from helpers import create_output_dir_timestamp, create_dir


class ToolInstance(QObject):
    """Class for Tool instances.

    Attributes:
        tool (ToolTemplate): Tool for which this instance is created
        ui (ToolboxUI): QMainWindow instance
        tool_output_dir (str): Directory where results are saved
        project (SpineToolboxProject): Current project
    """
    instance_finished_signal = Signal(int, name="instance_finished_signal")

    def __init__(self, tool, ui, tool_output_dir, project):
        """Tool instance constructor."""
        super().__init__()
        self.tool = tool
        self.ui = ui
        self._project = project
        self.tool_process = None
        self.tool_output_dir = tool_output_dir
        # Directory where results were saved
        self.output_dir = None
        wrk_dir = self._project.work_dir
        self.basedir = tempfile.mkdtemp(suffix='__toolbox', prefix=self.tool.short_name + '__', dir=wrk_dir)
        self.command = ''  # command is created after ToolInstance is initialized
        self.inputfiles = [os.path.join(self.basedir, f) for f in tool.inputfiles]
        self.inputfiles_opt = [os.path.join(self.basedir, f) for f in tool.inputfiles_opt]
        self.outputfiles = [os.path.join(self.basedir, f) for f in tool.outputfiles]
        # Check that required output directories are created
        self.make_work_output_dirs()
        # Checkout Tool
        if not self._checkout:
            raise OSError("Could not create Tool instance")

    @property
    def _checkout(self):
        """Copy Tool files to work directory."""
        n_copied_files = 0
        # Add anchor to work directory
        work_anchor = "<a style='color:#99CCFF;' href='file:///" + self.basedir + "'>" + self.basedir + "</a>"
        self.ui.msg.emit("Work Directory: {}".format(work_anchor))
        self.ui.msg.emit("*** Copying Tool <b>{0}</b> to work directory ***".format(self.tool.name))
        for filepath in self.tool.includes:
            dirname, file_pattern = os.path.split(filepath)
            src_dir = os.path.join(self.tool.path, dirname)
            dst_dir = os.path.join(self.basedir, dirname)
            # Create the destination directory
            try:
                create_dir(dst_dir)
            except OSError:
                self.ui.msg_error.emit("Creating directory <b>{0}</b> failed".format(dst_dir))
                return False
            # Copy file if necessary
            if file_pattern:
                for src_file in glob.glob(os.path.join(src_dir, file_pattern)):
                    dst_file = os.path.join(dst_dir, os.path.basename(src_file))
                    logging.debug("Copying file {} to {}".format(src_file, dst_file))
                    try:
                        shutil.copyfile(src_file, dst_file)
                        n_copied_files += 1
                    except OSError as e:
                        logging.error(e)
                        self.ui.msg_error.emit("\tCopying file <b>{0}</b> to <b>{1}</b> failed"
                                               .format(src_file, dst_file))
                        return False
        if n_copied_files == 0:
            self.ui.msg_warning.emit("Warning: No files copied")
        else:
            self.ui.msg.emit("\tCopied <b>{0}</b> file(s)".format(n_copied_files))
        return True

    def execute(self):
        """Start executing tool instance in QProcess."""
        self.ui.msg.emit("*** Starting Tool <b>{0}</b> ***".format(self.tool.name))
        self.ui.msg.emit("\t<i>{0}</i>".format(self.command))
        if self.tool.tooltype == "julia":
            if self.ui._config.getboolean("settings", "use_repl"):
                self.tool_process = self.ui.julia_repl
                self.tool_process.start_jupyter_kernel()
                self.tool_process.subprocess_finished_signal.connect(self.julia_repl_tool_finished)
                self.tool_process.start_process(self.command)
            else:
                self.tool_process = qsubprocess.QSubProcess(self.ui, self.command)
                self.tool_process.subprocess_finished_signal.connect(self.julia_tool_finished)
                self.tool_process.start_process(workdir=self.basedir)
        else:
            self.tool_process = qsubprocess.QSubProcess(self.ui, self.command)
            self.tool_process.subprocess_finished_signal.connect(self.gams_tool_finished)
            self.tool_process.start_process(workdir=self.basedir)


    def julia_repl_tool_finished(self, ret):
        """Run when Julia tool using REPL has finished processing.

        Args:
            ret (int): Return code given by tool
        """
        if ret == -9998: # 'give-up' code, there is no usable Julia kernel for Jupyter
            self.ui.msg_error.emit("\tUnable to start Julia REPL.")
            self.instance_finished_signal.emit(ret)
            return
        if ret != 0:
            try:
                return_msg = self.tool.return_codes[ret]
                self.ui.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
            except KeyError:
                self.ui.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:
            self.ui.msg.emit("\tJulia Tool finished successfully. Return code:{0}".format(ret))
        self.tool_process = None
        self.save_output_files(ret)


    @Slot(int, name="julia_tool_finished")
    def julia_tool_finished(self, ret):
        """Run when Julia tool has finished processing.

        Args:
            ret (int): Return code given by tool
        """
        if self.tool_process.process_failed:  # process_failed should be True if ret != 0
            if self.tool_process.process_failed_to_start:
                self.ui.msg_error.emit("Sub-process failed to start. Make sure that "
                                       "Julia is installed properly on your computer.")
            else:
                try:
                    return_msg = self.tool.return_codes[ret]
                    self.ui.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self.ui.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self.ui.msg.emit("\tJulia tool finished successfully. Return code:{0}".format(ret))
        self.tool_process.deleteLater()
        self.tool_process = None
        self.save_output_files(ret)

    @Slot(int, name="gams_tool_finished")
    def gams_tool_finished(self, ret):
        """Run when GAMS tool has finished processing. Copies output of tool
        to project output directory.

        Args:
            ret (int): Return code given by tool
        """
        if self.tool_process.process_failed:  # process_failed should be True if ret != 0
            if self.tool_process.process_failed_to_start:
                self.ui.msg_error.emit("Sub-process failed to start. Make sure that "
                                       "GAMS is installed properly on your computer "
                                       "and GAMS directory is given in Settings (F1).")
            else:
                try:
                    return_msg = self.tool.return_codes[ret]
                    self.ui.msg_error.emit("\t<b>{0}</b> [exit code:{1}]".format(return_msg, ret))
                except KeyError:
                    self.ui.msg_error.emit("\tUnknown return code ({0})".format(ret))
        else:  # Return code 0: success
            self.ui.msg.emit("\tGAMS tool finished successfully. Return code:{0}".format(ret))
        self.tool_process.deleteLater()
        self.tool_process = None
        self.save_output_files(ret)

    def save_output_files(self, ret):
        """Copy output files from work directory to Tool ouput directory"""
        # Get timestamp when tool finished
        output_dir_timestamp = create_output_dir_timestamp()
        # Create an output folder with timestamp and copy output directly there
        if ret != 0:
            result_path = os.path.abspath(os.path.join(self.tool_output_dir, 'failed', output_dir_timestamp))
        else:
            result_path = os.path.abspath(os.path.join(self.tool_output_dir, output_dir_timestamp))
        try:
            create_dir(result_path)
        except OSError:
            self.ui.msg_error.emit("\tError creating timestamped result directory. "
                                   "Tool output files not copied. Check folder permissions")
            self.output_dir = None
            self.instance_finished_signal.emit(ret)
            return
        self.output_dir = result_path
        self.ui.msg.emit("\t*** Saving result files ***")
        saved_files, failed_files = self.copy_output(result_path)
        if len(saved_files) == 0:
            # If no files were saved
            logging.error("No files saved to result directory '{0}'".format(result_path))
            self.ui.msg_error.emit("\tNo files saved to result directory")
            if len(failed_files) == 0:
                # If there were no failed files either
                logging.error("No failed files")
                self.ui.msg_warning.emit("\tWarning: Check 'outputfiles' in tool definition.")
        if len(saved_files) > 0:
            # If there are saved files
            self.ui.msg.emit("\tThe following result files were saved successfully")
            for i in range(len(saved_files)):
                fname = os.path.split(saved_files[i])[1]
                self.ui.msg.emit("\t\t{0}".format(fname))
        if len(failed_files) > 0:
            # If some files failed
            self.ui.msg_warning.emit("\tThe following result files were not found")
            for i in range(len(failed_files)):
                failed_fname = os.path.split(failed_files[i])[1]
                self.ui.msg_warning.emit("\t\t{0}".format(failed_fname))
        self.ui.msg.emit("\tDone")
        # Show result folder
        logging.debug("Result files saved to <{0}>".format(result_path))
        result_anchor = "<a href='file:///" + result_path + "'>" + result_path + "</a>"
        self.ui.msg.emit("\tResult Directory: {}".format(result_anchor))
        self.instance_finished_signal.emit(ret)

    def terminate_instance(self):
        """Terminate tool process execution."""
        if not self.tool_process:
            return
        self.tool_process.terminate_process()

    def remove(self):
        """Remove the tool instance files."""
        shutil.rmtree(self.basedir, ignore_errors=True)

    def copy_output(self, target_dir):
            """Save output of a tool instance

            Args:
                target_dir (str): Copy destination

            Returns:
                ret (bool): Operation success
            """
            failed_files = list()
            saved_files = list()
            logging.debug("Saving result files to <{0}>".format(target_dir))
            for pattern in self.outputfiles:
                # Check for wildcards in pattern
                if ('*' in pattern) or ('?' in pattern):
                    for fname in glob.glob(pattern):
                        logging.debug("Match for pattern <{0}> found. Saving file {1}".format(pattern, fname))
                        shutil.copy(fname, target_dir)
                        saved_files.append(fname)
                else:
                    if not os.path.isfile(pattern):
                        failed_files.append(pattern)
                        continue
                    logging.debug("Saving file {0}".format(pattern))
                    shutil.copy(pattern, target_dir)
                    saved_files.append(pattern)
            return saved_files, failed_files

    def make_work_output_dirs(self):
        """Make sure that work directory has the necessary output directories for Tool output files.
        Checks only "outputfiles" list. Alternatively you can add directories to "inputfiles" list
        in the tool definition file.

        Returns:
            Boolean value depending on operation success.
        """
        # TODO: Remove duplicate directory names from the list of created directories.
        for path in self.tool.outputfiles:
            dirname, file_pattern = os.path.split(path)
            if dirname == '':
                continue
            dst_dir = os.path.join(self.basedir, dirname)
            try:
                create_dir(dst_dir)
            except OSError:
                self.ui.msg_error.emit("Creating work output directory '{}' failed".format(dst_dir))
                return False
        return True
