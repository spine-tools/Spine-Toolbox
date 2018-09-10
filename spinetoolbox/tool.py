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
import shutil
from metaobject import MetaObject
from widgets.tool_subwindow_widget import ToolSubWindowWidget
from PySide2.QtCore import Slot, Qt, QUrl
from PySide2.QtGui import QDesktopServices
from tool_instance import ToolInstance
from config import TOOL_OUTPUT_DIR, GAMS_EXECUTABLE, JULIA_EXECUTABLE
from graphics_items import ToolImage
from widgets.custom_menus import ToolTemplateOptionsPopupMenu
from helpers import create_dir


class Tool(MetaObject):
    """Tool class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        tool_template (ToolTemplate): Template for this Tool
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """
    def __init__(self, toolbox, name, description, tool_template, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "Tool"
        self.item_category = "Tools"
        self._widget = ToolSubWindowWidget(self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_input_files()
        self._widget.make_header_for_output_files()
        self._widget.ui.comboBox_tool.setModel(self._toolbox.tool_template_model)
        self._tool_template = None
        self._tool_template_index = None
        self.tool_template_options_popup_menu = None
        self.set_tool_template(tool_template)
        # Set correct row selected in the comboBox
        if not tool_template:
            r = 0
        else:
            r = self._toolbox.tool_template_model.tool_template_row(tool_template.name)
            if r == -1:
                logging.error("error in tool_template_row() method")
                r = 0
        self._widget.ui.comboBox_tool.setCurrentIndex(r)
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        self.extra_cmdline_args = ''  # This may be used for additional Tool specific command line arguments
        # Create Tool project directory
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit("[OSError] Creating directory {0} failed."
                                         " Check permissions.".format(self.data_dir))
        # Make directory for results
        self.output_dir = os.path.join(self.data_dir, TOOL_OUTPUT_DIR)
        self._graphics_item = ToolImage(self._toolbox, x - 35, y - 35, w=70, h=70, name=self.name)
        self._widget.ui.pushButton_stop.setEnabled(False)
        self.connect_signals()

    def connect_signals(self):
        """Connect this tool's signals to slots."""
        self._widget.ui.pushButton_stop.clicked.connect(self.stop_process)
        self._widget.ui.pushButton_open_results.clicked.connect(self.open_results)
        self._widget.ui.pushButton_execute.clicked.connect(self.execute)
        self._widget.ui.comboBox_tool.currentIndexChanged.connect(self.update_tool_template)

    @Slot(name="open_results")
    def open_results(self):
        """Open output directory in file browser."""
        if not os.path.exists(self.output_dir):
            self._toolbox.msg_warning.emit("Tool <b>{0}</b> has no results. "
                                           "Click Execute to generate them.".format(self.name))
            return
        url = "file:///" + self.output_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.output_dir))

    @Slot(name="stop_process")
    def stop_process(self):
        try:
            self.instance.instance_finished_signal.disconnect(self.execution_finished)
        except Exception as e:
            logging.exception("Exception {0} caught in Tool stop_process()".format(e))
        self.instance.terminate_instance()
        self._toolbox.msg_warning.emit("Tool <b>{0}</b> has been stopped".format(self.name))

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this data connection in the scene."""
        return self._graphics_item

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    def get_parent(self):
        """Returns the ToolboxUI instance."""
        return self._toolbox

    @Slot(name="edit_tool_template")
    def edit_tool_template(self):
        self._toolbox.edit_tool_template(self._tool_template_index)

    @Slot(name="open_tool_template_file")
    def open_tool_template_file(self):
        self._toolbox.open_tool_template_file(self._tool_template_index)

    @Slot(name="open_tool_main_program_file")
    def open_tool_main_program_file(self):
        self._toolbox.open_tool_main_program_file(self._tool_template_index)

    def tool_template(self):
        """Returns Tool template."""
        return self._tool_template

    def set_tool_template(self, tool_template):
        """Sets Tool Template for this Tool. Removes Tool Template if None given as argument.

        Args:
            tool_template (ToolTemplate): Template for this Tool. None removes the template.

        Returns:
            ToolTemplate or None if no Tool Template set for this Tool.
        """
        self._tool_template = tool_template
        if tool_template:
            self._tool_template_index = self._toolbox.tool_template_model.tool_template_index(tool_template.name)
        else:
            self._tool_template_index = None
        self.update_tool_ui()
        self.tool_template_options_popup_menu = ToolTemplateOptionsPopupMenu(self._toolbox, self)
        self._widget.ui.toolButton_tool_template.setMenu(self.tool_template_options_popup_menu)

    def update_tool_ui(self):
        """Update Tool UI to show Tool template details."""
        if not self.tool_template():
            self._widget.ui.lineEdit_tool_args.setText("")
            self._widget.populate_input_files_list(None)
            self._widget.populate_output_files_list(None)
        else:
            self._widget.ui.lineEdit_tool_args.setText(self.tool_template().cmdline_args)
            self.update_input_files()
            self.update_output_files()

    def update_input_files(self):
        """Show input files in QListView."""
        if not self.tool_template():
            return
        self._widget.populate_input_files_list(self.tool_template().inputfiles)

    def update_output_files(self):
        """Show output files in QListView."""
        if not self.tool_template():
            return
        self._widget.populate_output_files_list(self.tool_template().outputfiles)

    def read_tool_def(self, tool_def_file):
        """[OBSOLETE?] Return tool template definition file contents or None if operation failed."""
        try:
            with open(tool_def_file, 'r') as fp:
                try:
                    definition = json.load(fp)
                except ValueError:
                    self._toolbox.msg_error.emit("Tool template definition file not valid")
                    logging.exception("Loading JSON data failed")
                    return None
        except FileNotFoundError:
            self._toolbox.msg_error.emit("Tool template definition file <b>{0}</b> not found".format(tool_def_file))
            return None
        return definition

    @Slot(name="execute")
    def execute(self):
        """Execute button clicked."""
        if not self.tool_template():
            self._toolbox.msg_warning.emit("No Tool template attached to Tool <b>{0}</b>".format(self.name))
            return
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("----------------------------")
        self._toolbox.msg.emit("Executing Tool <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("----------------------------")
        self._toolbox.msg.emit("")
        try:
            self.instance = ToolInstance(self.tool_template(), self._toolbox, self.output_dir, self._project)
        except OSError as e:
            self._toolbox.msg_error.emit("Tool instance creation failed. {0}".format(e))
            return
        # Find required input files for ToolInstance (if any)
        if self._widget.input_file_model.rowCount() > 0:
            self._toolbox.msg.emit("*** Checking Tool template requirements ***")
            # Abort if there are no input items connected to this Tool
            inputs = self._toolbox.connection_model.input_items(self.name)
            if not inputs:
                self._toolbox.msg_error.emit("This Tool has no input connections. Cannot find required input files.")
                return
            n_dirs, n_files = self.count_files_and_dirs()
            # logging.debug("Tool requires {0} dirs and {1} files".format(n_dirs, n_files))
            if n_dirs > 0:
                self._toolbox.msg.emit("*** Creating subdirectories to work directory ***")
                if not self.create_dirs_to_work():
                    # Creating directories failed -> abort
                    self._toolbox.msg_error.emit("Creating directories to work failed. Tool execution aborted")
                    return
            else:  # just for testing
                # logging.debug("No directories to create")
                pass
            if n_files > 0:
                self._toolbox.msg.emit("*** Searching for required input files ***")
                file_copy_paths = self.find_input_files()
                if not file_copy_paths:
                    self._toolbox.msg_error.emit("Input files not found. Tool execution aborted.")
                    return
                self._toolbox.msg.emit("*** Copying input files to work directory ***")
                # Copy input files to ToolInstance work directory
                if not self.copy_input_files(file_copy_paths):
                    self._toolbox.msg_error.emit("Unable to copy input files to work directory. "
                                                 "Tool execution aborted.")
                    return
            else:  # just for testing
                # logging.debug("No input files to copy")
                pass
        self._widget.ui.pushButton_stop.setEnabled(True)
        self._widget.ui.pushButton_execute.setEnabled(False)
        self._graphics_item.start_wheel_animation()
        self.update_instance()  # Make command and stuff
        self.instance.instance_finished_signal.connect(self.execution_finished)
        self.instance.execute()

    def count_files_and_dirs(self):
        """Count the number of files and directories in required input files model.
        TODO: Change name of 'required input files' because it can contain dir names too.

        Returns:
            Tuple containing the number of required files and directories.
        """
        n_dir = 0
        n_file = 0
        for i in range(self._widget.input_file_model.rowCount()):
            req_file_path = self._widget.input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Check if this a directory or a file
            path, filename = os.path.split(req_file_path)
            if not filename:
                # It's a directory
                n_dir += 1
            else:
                # It's a file
                n_file += 1
        return n_dir, n_file

    def create_dirs_to_work(self):
        """Iterate items in required input files and check
        if there are any directories to create. Create found
        directories directly to instance work folder.

        Returns:
            Boolean variable depending on success
        """
        for i in range(self._widget.input_file_model.rowCount()):
            req_file_path = self._widget.input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Check if this a directory or a file
            path, filename = os.path.split(req_file_path)
            if not filename:
                # It's a directory
                # logging.debug("path {0} should be created to work folder".format(path))
                path_to_create = os.path.join(self.instance.basedir, path)
                try:
                    create_dir(path_to_create)
                except OSError:
                    self._toolbox.msg_error.emit("[OSError] Creating directory {0} failed."
                                                 " Check permissions.".format(path_to_create))
                    return False
                self._toolbox.msg.emit("\tDirectory <b>{0}</b> created".format(path_to_create))
            else:
                # It's a file -> skip
                pass
        return True

    def find_input_files(self):
        """Iterate files in required input files model and find them from connected items.

        Returns:
            Dictionary of paths where required files are found or None if some file was not found.
        """
        file_paths = dict()
        for i in range(self._widget.input_file_model.rowCount()):
            req_file_path = self._widget.input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Just get the filename if there is a path attached to the file
            path, filename = os.path.split(req_file_path)
            if not filename:
                # It's a directory
                continue
            found_file = self.find_file(filename)
            if not found_file:
                self._toolbox.msg_error.emit("\tRequired file <b>{0}</b> not found".format(filename))
                return None
            else:
                # file_paths.append(found_file)
                file_paths[req_file_path] = found_file
        return file_paths

    def find_file(self, fname):
        """Find required input file for this Tool Instance. Search file from Data
        Connection or Data Store items that are input items for this Tool. These in turn
        will search on their own input items and stop when an infinite recursion is detected.

        Args:
            fname (str): File name (no path)

        Returns:
            Path to file or None if it was not found.
        """
        path = None
        # Find file from immediate parent items
        for input_item in self._toolbox.connection_model.input_items(self.name):
            # self._toolbox.msg.emit("Searching for file <b>{0}</b> from item <b>{1}</b>".format(fname, input_item))
            # Find item from project model
            found_item = self._toolbox.project_item_model.find_item(input_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                return path
            item_data = found_item.data(Qt.UserRole)
            # Find file from parent Data Stores and Data Connections
            if item_data.item_type in ["Data Store", "Data Connection"]:
                visited_items = list()
                path = item_data.find_file(fname, visited_items)
                if path is not None:
                    break
            elif item_data.item_type == "Tool":
                # TODO: Find file from output files of parent Tools
                pass
        return path

    def copy_input_files(self, paths):
        """Copy files from given paths to the directories in work directory, where the Tool requires them to be.

        Args:
            paths (dict): Key is path to required file, value is path to source file.

        Returns:
            Boolean variable depending on operation success
        """
        n_copied_files = 0
        for dst, src_path in paths.items():
            if not os.path.exists(src_path):
                self._toolbox.msg_error.emit("\tFile <b>{0}</b> does not exist".format(src_path))
                return False
            # Join work directory path to dst (dst is the filename including possible subfolders, e.g. 'input/f.csv')
            dst_path = os.path.abspath(os.path.join(self.instance.basedir, dst))
            # Create subdirectories to work if necessary
            dst_subdir, fname = os.path.split(dst)
            if not dst_subdir:
                # No subdirectories to create
                self._toolbox.msg.emit("\tCopying <b>{0}</b> -> work directory".format(fname))
            else:
                # Create subdirectory structure to work (Skip if already done in create_dirs_to_work() method)
                work_subdir_path = os.path.abspath(os.path.join(self.instance.basedir, dst_subdir))
                if not os.path.exists(work_subdir_path):
                    try:
                        create_dir(work_subdir_path)
                    except OSError:
                        self._toolbox.msg_error.emit("[OSError] Creating directory <b>{0}</b> failed."
                                                     .format(work_subdir_path))
                        return False
                    self._toolbox.msg.emit("\tCopying <b>{0}</b> -> work subdirectory <b>{1}</b>"
                                           .format(fname, dst_subdir))
            try:
                shutil.copyfile(src_path, dst_path)
                n_copied_files += 1
            except OSError as e:
                logging.error(e)
                self._toolbox.msg_error.emit("\t[OSError] Copying file <b>{0}</b> to <b>{1}</b> failed"
                                             .format(src_path, dst_path))
                return False
        self._toolbox.msg.emit("\tCopied <b>{0}</b> input file(s)".format(n_copied_files))
        return True

    def find_output_items(self):
        """Find output items of this Tool.

        Returns:
            List of Data Store and Data Connection items.
        """
        item_list = list()
        for output_item in self._toolbox.connection_model.output_items(self.name):
            found_item = self._toolbox.project_item_model.find_item(output_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(output_item))
                continue
            item_data = found_item.data(Qt.UserRole)
            item_list.append(item_data)
        return item_list

    def copy_output_files(self, output_items):
        """Copy all Tool output files to all child Data Connections and Data Stores.

        Args:
            output_items (list): Destination items for output files.
        """
        for item in output_items:
            self._toolbox.msg.emit("*** Copying Tool <b>{0}</b> output files to {1} <b>{2}</b> ***"
                                   .format(self.name, item.item_type, item.name))
            dst_dir = ""
            # Copy to child Data Store
            if item.item_type == "Data Store":
                if os.path.isdir(item.data_dir):
                    dst_dir = item.data_dir
            # Copy to child Data Connection
            elif item.item_type == "Data Connection":
                if os.path.isdir(item.data_dir):
                    dst_dir = item.data_dir
            else:
                self._toolbox.msg_warning.emit("\t<b>Not implemented</b>")
                continue
            n_copied_files = 0
            for output_file in self._tool_template.outputfiles:
                src_path = os.path.join(self.instance.output_dir, output_file)
                if not os.path.exists(src_path):
                    self._toolbox.msg_error.emit("\t Source file <b>{0}</b> does not exist".format(src_path))
                    continue
                # Join filename to dst folder
                dst_path = os.path.join(dst_dir, output_file)
                self._toolbox.msg.emit("\tCopying <b>{0}</b>".format(output_file))
                try:
                    shutil.copyfile(src_path, dst_path)
                    n_copied_files += 1
                except OSError as e:
                    logging.error(e)
                    self._toolbox.msg_error.emit("\t[OSError] Copying file <b>{0}</b> to <b>{1}</b> failed"
                                                 .format(src_path, dst_path))
            self._toolbox.msg.emit("\tCopied <b>{0}</b> file(s)".format(n_copied_files))

    @Slot(int, name="execution_finished")
    def execution_finished(self, return_code):
        """Tool execution finished."""
        self._widget.ui.pushButton_stop.setEnabled(False)
        self._widget.ui.pushButton_execute.setEnabled(True)
        self._graphics_item.stop_wheel_animation()
        # Disconnect instance finished signal
        self.instance.instance_finished_signal.disconnect(self.execution_finished)
        if return_code == 0:
            # copy output files to data directories of connected items
            output_items = self.find_output_items()
            if output_items:
                # self._toolbox.msg.emit("Copying Tool output files to connected items")
                self.copy_output_files(output_items)
            self._toolbox.msg_success.emit("Tool <b>{0}</b> execution finished".format(self.name))
        else:
            self._toolbox.msg_error.emit("Tool <b>{0}</b> execution failed".format(self.name))

    def update_instance(self):
        """Initialize and update instance so that it is ready for processing. Maybe this is where Tool
        type specific initialization should happen (whether instance is GAMS or Julia Model)."""
        if self.tool_template().tooltype == "gams":
            gams_path = self._toolbox._config.get("settings", "gams_path")
            if not gams_path == '':
                gams_exe = os.path.join(gams_path, GAMS_EXECUTABLE)
            else:
                gams_exe = GAMS_EXECUTABLE
            self.instance.program = gams_exe
            self.instance.args.append(self.tool_template().main_prgm)
            self.instance.args.append("curDir=")
            self.instance.args.append("{0}".format(self.instance.basedir))
            self.instance.args.append("logoption=3")  # TODO: This should be an option in Settings
            self.append_instance_args()  # Append Tool specific cmd line args into args list
        elif self.tool_template().tooltype == "julia":
            # Prepare prompt command "julia script.jl"
            julia_dir = self._toolbox._config.get("settings", "julia_path")
            if not julia_dir == '':
                julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
            else:
                julia_exe = JULIA_EXECUTABLE
            work_dir = self.instance.basedir
            script_path = os.path.join(work_dir, self.tool_template().main_prgm)
            self.instance.program = julia_exe
            self.instance.args.append(script_path)
            self.append_instance_args()
            use_repl = self._toolbox._config.getboolean("settings", "use_repl")
            if use_repl:
                # Prepare Julia REPL command
                # TODO: See if this can be simplified
                mod_work_dir = work_dir.__repr__().strip("'")
                self.instance.julia_repl_command = r'cd("{}");'\
                    r'include("{}")'.format(mod_work_dir, self.tool_template().main_prgm)

    def append_instance_args(self):
        """Append Tool template command line args into instance args list."""
        # TODO: Deal with cmdline arguments that have spaces. They should be stored in a list in the definition file
        if (self.tool_template().cmdline_args is not None) and (not self.tool_template().cmdline_args == ''):
            # Tool template cmdline args is a space delimited string. Add them to a list.
            self.instance.args += self.tool_template().cmdline_args.split(" ")

    @Slot(int, name="update_tool_template")
    def update_tool_template(self, row):
        """Update Tool template according to selection.

        Args:
            row (int): Selected row in the comboBox
        """
        if row == 0:
            new_tool = None
        else:
            # Find ToolTemplate from model according to row
            new_tool = self._toolbox.tool_template_model.tool_template(row)
        self.set_tool_template(new_tool)
