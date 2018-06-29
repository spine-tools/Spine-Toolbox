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
from PySide2.QtCore import Slot, Qt
from tool_instance import ToolInstance
from config import TOOL_OUTPUT_DIR, GAMS_EXECUTABLE, JULIA_EXECUTABLE
from graphics_items import ToolImage
from widgets.custom_menus import ToolTemplateOptionsPopupMenu
from helpers import create_dir


class Tool(MetaObject):
    """Tool class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        tool_template (ToolTemplate): Template for this Tool
    """
    def __init__(self, parent, name, description, project, tool_template, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Tool"
        self.item_category = "Tools"
        self._project = project
        self._widget = ToolSubWindowWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_input_files()
        self._widget.make_header_for_output_files()
        self._widget.ui.comboBox_tool.setModel(self._parent.tool_template_model)
        self._tool_template = None
        self._tool_template_index = None
        self.tool_template_options_popup_menu = None
        self.set_tool_template(tool_template)
        # Set correct row selected in the comboBox
        if not tool_template:
            r = 0
        else:
            r = self._parent.tool_template_model.tool_template_row(tool_template.name)
            if r == -1:
                logging.error("error in tool_template_row() method")
                r = 0
        self._widget.ui.comboBox_tool.setCurrentIndex(r)
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        self.extra_cmdline_args = ''  # This may be used for additional Tool specific command line arguments
        # Directory where results are saved
        self.output_dir = os.path.join(self._project.project_dir, self.short_name, TOOL_OUTPUT_DIR)
        self._graphics_item = ToolImage(self._parent, x - 35, y - 35, w=70, h=70, name=self.name)
        self._widget.ui.pushButton_stop.setEnabled(False)
        self.connect_signals()

    def connect_signals(self):
        """Connect this tool's signals to slots."""
        self._widget.ui.pushButton_stop.clicked.connect(self.stop_process)
        self._widget.ui.pushButton_execute.clicked.connect(self.execute)
        self._widget.ui.comboBox_tool.currentIndexChanged.connect(self.update_tool_template)

    @Slot(name="stop_process")
    def stop_process(self):
        self.instance.terminate_instance()

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this data connection in the scene."""
        return self._graphics_item

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    def get_parent(self):
        """Returns the parent (ToolboxUI instance) of this object."""
        return self._parent

    @Slot(name="edit_tool_template")
    def edit_tool_template(self):
        self._parent.edit_tool_template(self._tool_template_index)

    @Slot(name="open_tool_template_file")
    def open_tool_template_file(self):
        self._parent.open_tool_template_file(self._tool_template_index)

    @Slot(name="open_tool_main_program_file")
    def open_tool_main_program_file(self):
        self._parent.open_tool_main_program_file(self._tool_template_index)

    @Slot(name='show_details')
    def show_details(self):
        """Details button clicked."""
        if not self.tool_template():
            self._parent.msg_warning.emit("No Tool template")
            return
        definition = self.read_tool_def(self.tool_template().get_def_path())
        if not definition:
            return
        self._parent.msg.emit("Tool template file contents:\n{0}"
                              .format(json.dumps(definition, sort_keys=True, indent=4)))

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
            self._tool_template_index = self._parent.tool_template_model.tool_template_index(tool_template.name)
        else:
            self._tool_template_index = None
        self.update_tool_ui()
        self.tool_template_options_popup_menu = ToolTemplateOptionsPopupMenu(self)
        self._widget.ui.toolButton_tool_template_options.setMenu(self.tool_template_options_popup_menu)

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

    @Slot(name="execute")
    def execute(self):
        """Execute button clicked."""
        if not self.tool_template():
            self._parent.msg_warning.emit("No Tool to execute")
            return
        self._parent.msg.emit("")
        self._parent.msg.emit("Executing Tool <b>{0}</b>".format(self.name))
        try:
            self.instance = ToolInstance(self.tool_template(), self._parent, self.output_dir, self._project)
        except OSError as e:
            self._parent.msg_error.emit("Tool instance creation failed. {0}".format(e))
            return
        # Find required input files for ToolInstance (if any)
        if self._widget.input_file_model.rowCount() > 0:
            self._parent.msg.emit("*** Checking Tool requirements ***")
            # Abort if there are no input items connected to this Tool
            inputs = self._parent.connection_model.input_items(self.name)
            if not inputs:
                self._parent.msg_error.emit("This Tool has no input connections. Cannot find required input files.")
                return
            n_dirs, n_files = self.count_files_and_dirs()
            # logging.debug("Tool requires {0} dirs and {1} files".format(n_dirs, n_files))
            if n_dirs > 0:
                self._parent.msg.emit("*** Creating subdirectories to work directory ***")
                if not self.create_dirs_to_work():
                    # Creating directories failed -> abort
                    self._parent.msg_error.emit("Creating directories to work failed. Tool execution aborted")
                    return
            else:  # just for testing
                # logging.debug("No directories to create")
                pass
            if n_files > 0:
                self._parent.msg.emit("*** Searching for required input files ***")
                file_copy_paths = self.find_input_files()
                if not file_copy_paths:
                    self._parent.msg_error.emit("Tool execution aborted1")
                    return
                self._parent.msg.emit("*** Copying input files to work directory ***")
                # Copy input files to ToolInstance work directory
                if not self.copy_input_files(file_copy_paths):
                    self._parent.msg_error.emit("Tool execution aborted2")
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
                    self._parent.msg_error.emit("[OSError] Creating directory {0} failed."
                                                " Check permissions.".format(path_to_create))
                    return False
                self._parent.msg.emit("\tDirectory <b>{0}</b> created".format(path_to_create))
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
                self._parent.msg_error.emit("\tRequired file <b>{0}</b> not found".format(filename))
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
        for input_item in self._parent.connection_model.input_items(self.name):
            # self._parent.msg.emit("Searching for file <b>{0}</b> from item <b>{1}</b>".format(fname, input_item))
            # Find item from project model
            found_item = self._parent.project_item_model.find_item(input_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._parent.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
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
                self._parent.msg_error.emit("\tFile <b>{0}</b> does not exist".format(src_path))
                return False
            # Join work directory path to dst (dst is the filename including possible subfolders, e.g. 'input/f.csv')
            dst_path = os.path.abspath(os.path.join(self.instance.basedir, dst))
            # Create subdirectories to work if necessary
            dst_subdir, fname = os.path.split(dst)
            if not dst_subdir:
                # No subdirectories to create
                self._parent.msg.emit("\tCopying <b>{0}</b> -> work directory".format(fname))
            else:
                # Create subdirectory structure to work (Skip if already done in create_dirs_to_work() method)
                work_subdir_path = os.path.abspath(os.path.join(self.instance.basedir, dst_subdir))
                if not os.path.exists(work_subdir_path):
                    try:
                        create_dir(work_subdir_path)
                    except OSError:
                        self._parent.msg_error.emit("[OSError] Creating directory <b>{0}</b> failed."
                                                    .format(work_subdir_path))
                        return False
                    self._parent.msg.emit("\tCopying <b>{0}</b> -> work subdirectory <b>{1}</b>"
                                          .format(fname, dst_subdir))
            try:
                shutil.copyfile(src_path, dst_path)
                n_copied_files += 1
            except OSError as e:
                logging.error(e)
                self._parent.msg_error.emit("\t[OSError] Copying file <b>{0}</b> to <b>{1}</b> failed"
                                            .format(src_path, dst_path))
                return False
        self._parent.msg.emit("\tCopied <b>{0}</b> input file(s)".format(n_copied_files))
        return True

    def find_output_folders(self):
        """Find output data folders from Data Store and Data Connection items
        that are output items for this Tool.

        Returns:
            List of data folders.
        """
        folder_paths = list()
        for output_item in self._parent.connection_model.output_items(self.name):
            found_item = self._parent.project_item_model.find_item(output_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._parent.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(output_item))
                continue
            item_data = found_item.data(Qt.UserRole)
            # Get data directory from child Data Store
            if item_data.item_type == "Data Store":
                if os.path.isdir(item_data.data_dir):
                    folder_paths.append(item_data.data_dir)
            # Get data directory from child Data Connection
            elif item_data.item_type == "Data Connection":
                if os.path.isdir(item_data.data_dir):
                    folder_paths.append(item_data.data_dir)
        return folder_paths

    def copy_output_files(self, folder_paths):
        """Copy files from work directory to the given paths.

        Args:
            folder_paths (list): Destination folders, where output files need to be copied.
        """
        n_copied_files = 0
        for output_file in self._tool_template.outputfiles:
            src_path = os.path.join(self.instance.output_dir, output_file)
            if not os.path.exists(src_path):
                self._parent.msg_error.emit("\tFile <b>{0}</b> does not exist".format(src_path))
                continue
            for dst_folder in folder_paths:
                # Join filename to dst folder
                dst_path = os.path.join(dst_folder, output_file)
                self._parent.msg.emit("\tCopying <b>{0}</b>".format(output_file))
                try:
                    shutil.copyfile(src_path, dst_path)
                    n_copied_files += 1
                except OSError as e:
                    logging.error(e)
                    self._parent.msg_error.emit("\t[OSError] Copying file <b>{0}</b> to <b>{1}</b> failed"
                                                .format(src_path, dst_path))
        self._parent.msg.emit("\tCopied <b>{0}</b> file(s)".format(n_copied_files))

    @Slot(int, name="execution_finished")
    def execution_finished(self, return_code):
        """Tool execution finished."""
        self._widget.ui.pushButton_stop.setEnabled(False)
        self._widget.ui.pushButton_execute.setEnabled(True)
        self._graphics_item.stop_wheel_animation()
        if return_code == 0:
            self._parent.msg_success.emit("Tool <b>{0}</b> execution finished".format(self.name))
            # copy outputfiles to data directories of connected items
            folder_paths = self.find_output_folders()
            if folder_paths:
                self.copy_output_files(folder_paths)
        else:
            self._parent.msg_error.emit("Tool <b>{0}</b> execution failed".format(self.name))

    def update_instance(self):
        """Initialize and update instance so that it is ready for processing. Maybe this is where Tool
        type specific initialization should happen (whether instance is GAMS or Julia Model)."""
        if self.tool_template().tooltype == "gams":
            gams_path = self._parent._config.get("settings", "gams_path")
            if not gams_path == '':
                gams_exe = os.path.join(gams_path, GAMS_EXECUTABLE)
            else:
                gams_exe = GAMS_EXECUTABLE
            main_dir = self.instance.basedir  # TODO: Is main_dir needed?
            command = '{} "{}" Curdir="{}" logoption=3'\
                .format(gams_exe, self.tool_template().main_prgm, main_dir)
            # Append Tool specific command line arguments to command (if present and implemented)
            self.instance.command = self.append_cmdline_args(command)
        elif self.tool_template().tooltype == "julia":
            # Prepare prompt command "julia script.jl"
            julia_dir = self._parent._config.get("settings", "julia_path")
            if not julia_dir == '':
                julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
            else:
                julia_exe = JULIA_EXECUTABLE
            work_dir = self.instance.basedir
            script_path = os.path.join(work_dir, self.tool_template().main_prgm)
            command = '{0} {1}'.format(julia_exe, script_path)
            # Append Tool specific command line arguments to command
            command = self.append_cmdline_args(command)
            use_repl = self._parent._config.getboolean("settings", "use_repl")
            if use_repl:
                # Prepare Julia REPL command
                main_dir = self.instance.basedir  # TODO: Is main_dir needed?
                mod_main_dir = main_dir.__repr__().strip("'")
                self.instance.command = r'cd("{}");'\
                    r'include("{}")'.format(mod_main_dir, self.tool_template().main_prgm)
                # Attach fallback command (in case REPL doesn't work)
                self.instance.fallback_command = command
            else:
                self.instance.command = command

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
            new_tool = self._parent.tool_template_model.tool_template(row)
        self.set_tool_template(new_tool)
