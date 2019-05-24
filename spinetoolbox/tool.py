######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Tool class.

:author: P. Savolainen (VTT)
:date:   19.12.2017
"""

import logging
import os
import shutil
import getpass
import sys
from project_item import ProjectItem
from PySide2.QtCore import Slot, Qt, QUrl, QFileInfo
from PySide2.QtGui import QDesktopServices, QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QFileIconProvider
from tool_instance import ToolInstance
from config import TOOL_OUTPUT_DIR, GAMS_EXECUTABLE, JULIA_EXECUTABLE, PYTHON_EXECUTABLE
from graphics_items import ToolIcon
from widgets.custom_menus import ToolTemplateOptionsPopupMenu
from helpers import create_dir


class Tool(ProjectItem):
    """Tool class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        tool_template (ToolTemplate): Template for this Tool
        use_work (bool): Execute associated Tool template in work (True) or source directory (False)
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """

    def __init__(self, toolbox, name, description, tool_template, use_work, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "Tool"
        self.source_file_model = QStandardItemModel()
        self.populate_source_file_model(None)
        self.input_file_model = QStandardItemModel()
        self.populate_input_file_model(None)
        self.opt_input_file_model = QStandardItemModel()
        self.populate_opt_input_file_model(None)
        self.output_file_model = QStandardItemModel()
        self.populate_output_file_model(None)
        self.template_model = QStandardItemModel()
        self.populate_template_model(False)
        self.source_files = list()
        self._tool_template = None
        self.set_tool_template(tool_template)
        if not self._tool_template:
            self._tool_template_name = ""
        else:
            self._tool_template_name = self.tool_template().name
        self.tool_template_options_popup_menu = None
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        self.extra_cmdline_args = ''  # This may be used for additional Tool specific command line arguments
        self.execute_in_work = use_work  # Enables overriding the template default setting
        # Make project directory for this Tool
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed." " Check permissions.".format(self.data_dir)
            )
        # Make directory for results
        self.output_dir = os.path.join(self.data_dir, TOOL_OUTPUT_DIR)
        self._graphics_item = ToolIcon(self._toolbox, x - 35, y - 35, w=70, h=70, name=self.name)
        self._sigs = self.make_signal_handler_dict()

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._toolbox.ui.toolButton_tool_open_dir.clicked] = self.open_directory
        s[self._toolbox.ui.pushButton_tool_stop.clicked] = self.stop_process
        s[self._toolbox.ui.pushButton_tool_results.clicked] = self.open_results
        s[self._toolbox.ui.pushButton_tool_execute.clicked] = self.execute
        s[self._toolbox.ui.comboBox_tool.currentIndexChanged] = self.update_tool_template
        s[self._toolbox.ui.radioButton_execute_in_work.toggled] = self.update_execution_mode
        return s

    def activate(self):
        """Restore selections and connect signals."""
        self.restore_selections()
        super().connect_signals()

    def deactivate(self):
        """Save selections and disconnect signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed.", self.name)
            return False
        return True

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_tool_name.setText(self.name)
        self._toolbox.ui.treeView_template.setModel(self.template_model)
        if self._tool_template_name == "":
            self._toolbox.ui.comboBox_tool.setCurrentIndex(-1)
            self.set_tool_template(None)
        else:
            tool_template = self._toolbox.tool_template_model.find_tool_template(self._tool_template_name)
            row = self._toolbox.tool_template_model.tool_template_row(self._tool_template_name)
            self._toolbox.ui.comboBox_tool.setCurrentIndex(row)  # Row in tool temp model
            self.restore_tool_template(tool_template)

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""
        if not self._tool_template:
            self._tool_template_name = ""
        else:
            self._tool_template_name = self.tool_template().name
        self.execute_in_work = self._toolbox.ui.radioButton_execute_in_work.isChecked()

    @Slot(bool, name="update_execution_mode")
    def update_execution_mode(self, checked):
        """Slot for execute in work radio button toggled signal."""
        self.execute_in_work = checked

    @Slot(int, name="update_tool_template")
    def update_tool_template(self, row):
        """Update Tool template according to selection in the template comboBox.

        Args:
            row (int): Selected row in the comboBox
        """
        if row == -1:
            self._toolbox.ui.comboBox_tool.setCurrentIndex(-1)
            self.set_tool_template(None)
        else:
            new_tool = self._toolbox.tool_template_model.tool_template(row)
            self.set_tool_template(new_tool)

    def set_tool_template(self, tool_template):
        """Sets Tool Template for this Tool. Removes Tool Template if None given as argument.

        Args:
            tool_template (ToolTemplate): Template for this Tool. None removes the template.
        """
        self._tool_template = tool_template
        self.update_tool_ui()

    def update_tool_ui(self):
        """Update Tool UI to show Tool template details. Used when Tool template is changed.
        Overrides execution mode (work or source) with the template default."""
        if not self.tool_template():
            self._toolbox.ui.lineEdit_tool_args.setText("")
            self.populate_source_file_model(None)
            self.populate_input_file_model(None)
            self.populate_opt_input_file_model(None)
            self.populate_output_file_model(None)
            self.populate_template_model(populate=False)
            self._toolbox.ui.radioButton_execute_in_work.setChecked(True)
        else:
            self._toolbox.ui.lineEdit_tool_args.setText(self.tool_template().cmdline_args)
            self.populate_source_file_model(self.tool_template().includes)
            self.populate_input_file_model(self.tool_template().inputfiles)
            self.populate_opt_input_file_model(self.tool_template().inputfiles_opt)
            self.populate_output_file_model(self.tool_template().outputfiles)
            self.populate_template_model(populate=True)
            self.execute_in_work = self.tool_template().execute_in_work
            if self.execute_in_work:
                self._toolbox.ui.radioButton_execute_in_work.setChecked(True)
            else:
                self._toolbox.ui.radioButton_execute_in_source.setChecked(True)
        self.tool_template_options_popup_menu = ToolTemplateOptionsPopupMenu(self._toolbox, self)
        self._toolbox.ui.toolButton_tool_template.setMenu(self.tool_template_options_popup_menu)
        self._toolbox.ui.treeView_template.expandAll()

    def restore_tool_template(self, tool_template):
        """Restores the Tool Template of this Tool. Removes Tool Template if None given as argument.
        Needed in order to override tool template default execution mode (work or source).

        Args:
            tool_template (ToolTemplate): Template for this Tool. None removes the template.
        """
        self._tool_template = tool_template
        if not tool_template:
            self._toolbox.ui.lineEdit_tool_args.setText("")
            self.populate_source_file_model(None)
            self.populate_input_file_model(None)
            self.populate_opt_input_file_model(None)
            self.populate_output_file_model(None)
            self.populate_template_model(populate=False)
            self._toolbox.ui.radioButton_execute_in_work.setChecked(True)
        else:
            self._toolbox.ui.lineEdit_tool_args.setText(self.tool_template().cmdline_args)
            self.populate_source_file_model(self.tool_template().includes)
            self.populate_input_file_model(self.tool_template().inputfiles)
            self.populate_opt_input_file_model(self.tool_template().inputfiles_opt)
            self.populate_output_file_model(self.tool_template().outputfiles)
            self.populate_template_model(populate=True)
            if self.execute_in_work:
                self._toolbox.ui.radioButton_execute_in_work.setChecked(True)
            else:
                self._toolbox.ui.radioButton_execute_in_source.setChecked(True)
        self.tool_template_options_popup_menu = ToolTemplateOptionsPopupMenu(self._toolbox, self)
        self._toolbox.ui.toolButton_tool_template.setMenu(self.tool_template_options_popup_menu)
        self._toolbox.ui.treeView_template.expandAll()

    @Slot(bool, name="open_results")
    def open_results(self, checked=False):
        """Open output directory in file browser."""
        if not os.path.exists(self.output_dir):
            self._toolbox.msg_warning.emit(
                "Tool <b>{0}</b> has no results. " "Click Execute to generate them.".format(self.name)
            )
            return
        url = "file:///" + self.output_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.output_dir))

    @Slot(bool, name="stop_process")
    def stop_process(self, checked=False):
        """Terminate Tool template execution."""
        self.instance.terminate_instance()
        self._toolbox.msg_warning.emit("Tool <b>{0}</b> has been stopped".format(self.name))

    def set_icon(self, icon):
        """Icon setter method."""
        self._graphics_item = icon

    def get_icon(self):
        """Returns the graphics item representing this tool in the scene."""
        return self._graphics_item

    @Slot(name="edit_tool_template")
    def edit_tool_template(self):
        """Open Tool template editor for the Tool template attached to this Tool."""
        index = self._toolbox.tool_template_model.tool_template_index(self.tool_template().name)
        self._toolbox.edit_tool_template(index)

    @Slot(name="open_tool_template_file")
    def open_tool_template_file(self):
        """Open Tool template definition file."""
        index = self._toolbox.tool_template_model.tool_template_index(self.tool_template().name)
        self._toolbox.open_tool_template_file(index)

    @Slot(name="open_tool_main_program_file")
    def open_tool_main_program_file(self):
        """Open Tool template main program file in an external text edit application."""
        index = self._toolbox.tool_template_model.tool_template_index(self.tool_template().name)
        self._toolbox.open_tool_main_program_file(index)

    @Slot(name="open_tool_main_directory")
    def open_tool_main_directory(self):
        """Open directory where the Tool template main program is located in file explorer."""
        if not self.tool_template():
            return
        dir_url = "file:///" + self.tool_template().path
        self._toolbox.open_anchor(QUrl(dir_url, QUrl.TolerantMode))

    def tool_template(self):
        """Returns Tool template."""
        return self._tool_template

    @Slot(bool, name="execute")
    def execute(self, checked=False):
        """Execute button clicked."""
        self._toolbox.ui.textBrowser_eventlog.verticalScrollBar().setValue(
            self._toolbox.ui.textBrowser_eventlog.verticalScrollBar().maximum()
        )
        if not self.tool_template():
            self._toolbox.msg_warning.emit("Tool <b>{0}</b> has no Tool template to execute".format(self.name))
            return
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("----------------------------")
        self._toolbox.msg.emit("Executing Tool <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("----------------------------")
        self._toolbox.msg.emit("")
        if self.execute_in_work:
            self._toolbox.msg.emit("*** Executing in <b>work</b> directory mode ***")
        else:
            self._toolbox.msg.emit("*** Executing in <b>source</b> directory mode ***")
        # Find required input files for ToolInstance (if any)
        if self.input_file_model.rowCount() > 0:
            self._toolbox.msg.emit("*** Checking Tool template requirements ***")
            # Abort if there are no input items connected to this Tool
            inputs = self._toolbox.connection_model.input_items(self.name)
            if not inputs:
                self._toolbox.msg_error.emit("This Tool has no input connections. Cannot find required input files.")
                return
            n_dirs, n_files = self.count_files_and_dirs()
            # logging.debug("Tool requires {0} dirs and {1} files".format(n_dirs, n_files))
            if n_files > 0:
                self._toolbox.msg.emit("*** Searching for required input files ***")
                file_paths = self.find_input_files()
                if not file_paths:
                    self._toolbox.msg_error.emit("Tool execution aborted")
                    return
                # Required files and dirs should have been found at this point, so create instance
                try:
                    self.instance = ToolInstance(
                        self.tool_template(), self._toolbox, self.output_dir, self._project, self.execute_in_work
                    )
                except OSError as e:
                    self._toolbox.msg_error.emit("Creating Tool instance failed. {0}".format(e))
                    return
                if self.execute_in_work:
                    self._toolbox.msg.emit("*** Copying input files to work directory ***")
                else:
                    self._toolbox.msg.emit("*** Copying input files to source directory ***")
                # Copy input files to ToolInstance work or source directory
                if not self.copy_input_files(file_paths):
                    self._toolbox.msg_error.emit("Copying input files failed. Tool execution aborted.")
                    return
            else:  # just for testing
                # logging.debug("No input files to copy")
                pass
            if n_dirs > 0:
                if self.execute_in_work:
                    self._toolbox.msg.emit("*** Creating subdirectories to work directory ***")
                else:
                    self._toolbox.msg.emit("*** Creating subdirectories to source directory ***")
                if not self.create_subdirectories():
                    # Creating directories failed -> abort
                    self._toolbox.msg_error.emit("Creating subdirectories failed. Tool execution aborted.")
                    return
            else:  # just for testing
                # logging.debug("No directories to create")
                pass
        else:  # Tool template does not have requirements
            try:
                self.instance = ToolInstance(
                    self.tool_template(), self._toolbox, self.output_dir, self._project, self.execute_in_work
                )
            except OSError as e:
                self._toolbox.msg_error.emit("Tool instance creation failed. {0}".format(e))
                return
        # Check if there are any optional input files to copy
        if self.opt_input_file_model.rowCount() > 0:
            self._toolbox.msg.emit("*** Searching for optional input files ***")
            optional_file_paths = self.find_optional_input_files()
            for k, v in optional_file_paths.items():
                self._toolbox.msg.emit("\tFound <b>{0}</b> files matching pattern <b>{1}</b>".format(len(v), k))
            if not self.copy_optional_input_files(optional_file_paths):
                self._toolbox.msg_warning.emit("Copying optional input files failed")
        self._toolbox.ui.pushButton_tool_stop.setEnabled(True)
        self._toolbox.ui.pushButton_tool_execute.setEnabled(False)
        self._graphics_item.start_animation()
        self.update_instance()  # Make command and stuff
        self.instance.instance_finished_signal.connect(self.execution_finished)
        self.instance.execute()

    def count_files_and_dirs(self):
        """Count the number of files and directories in required input files model.

        Returns:
            Tuple containing the number of required files and directories.
        """
        n_dir = 0
        n_file = 0
        for i in range(self.input_file_model.rowCount()):
            req_file_path = self.input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Check if this a directory or a file
            path, filename = os.path.split(req_file_path)
            if not filename:
                # It's a directory
                n_dir += 1
            else:
                # It's a file
                n_file += 1
        return n_dir, n_file

    def create_subdirectories(self):
        """Iterate items in required input files and check
        if there are any directories to create. Create found
        directories directly to ToolInstance base directory.

        Returns:
            Boolean variable depending on success
        """
        for i in range(self.input_file_model.rowCount()):
            req_file_path = self.input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Check if this a directory or a file
            path, filename = os.path.split(req_file_path)
            if not filename:
                # It's a directory
                # logging.debug("path {0} should be created to work folder".format(path))
                path_to_create = os.path.join(self.instance.basedir, path)
                try:
                    create_dir(path_to_create)
                except OSError:
                    self._toolbox.msg_error.emit(
                        "[OSError] Creating directory {0} failed." " Check permissions.".format(path_to_create)
                    )
                    return False
                self._toolbox.msg.emit("\tDirectory <b>{0}{1}</b> created".format(os.path.sep, path))
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
        for i in range(self.input_file_model.rowCount()):
            req_file_path = self.input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Just get the filename if there is a path attached to the file
            path, filename = os.path.split(req_file_path)
            if not filename:
                # It's a directory
                continue
            found_file = self.find_file(filename)
            if not found_file:
                self._toolbox.msg_error.emit("Required file <b>{0}</b> not found".format(filename))
                return None
            else:
                file_paths[req_file_path] = found_file
        return file_paths

    def find_optional_input_files(self):
        """Find optional input files from connected items.

        Returns:
            Dictionary of optional input file paths or None if no files found. Key is the
            optional input item and value is a list of paths that matches the item.
        """
        file_paths = dict()
        for i in range(self.opt_input_file_model.rowCount()):
            file_path = self.opt_input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Just get the filename if there is a path attached to the file
            path, filename = os.path.split(file_path)
            if not filename:
                # It's a directory
                continue
            found_files = self.find_files(filename)
            if not found_files:
                self._toolbox.msg_warning.emit("\tNo files matching pattern <b>{0}</b> found".format(filename))
            else:
                file_paths[file_path] = found_files
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
            found_item_index = self._toolbox.project_item_model.find_item(input_item)
            found_item = self._toolbox.project_item_model.project_item(found_item_index)
            if not found_item:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                return path
            item_data = found_item
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

    def find_files(self, pattern):
        """Finds optional input files that match the given search word. Searches files from Data
        Connection or Data Store items that are input items for this Tool. These in turn
        will search on their own input items and stop when an infinite recursion is detected.

        Args:
            pattern (str): File name (may have wildcards)

        Returns:
            List of paths to files that match the pattern or an empty list if no matches.
        """
        paths = list()
        # Find file from immediate parent items
        for input_item in self._toolbox.connection_model.input_items(self.name):
            # self._toolbox.msg.emit("Searching for optional file <b>{0}</b> from item <b>{1}</b>"
            #                        .format(pattern, input_item))
            # Find item from project model
            found_item_index = self._toolbox.project_item_model.find_item(input_item)
            found_item = self._toolbox.project_item_model.project_item(found_item_index)
            if not found_item:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                return paths
            # Find file from parent Data Stores and Data Connections
            if found_item.item_type in ["Data Store", "Data Connection"]:
                visited_items = list()
                matching_paths = found_item.find_files(pattern, visited_items)
                if matching_paths is not None:
                    paths = paths + matching_paths
        return paths

    def copy_input_files(self, paths):
        """Copy input files from given paths to work or source directory, depending on
        where the Tool template requires them to be.

        Args:
            paths (dict): Key is path to destination file, value is path to source file.

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
            # Create subdirectories if necessary
            dst_subdir, fname = os.path.split(dst)
            if not dst_subdir:
                # No subdirectories to create
                self._toolbox.msg.emit("\tCopying file <b>{0}</b>".format(fname))
            else:
                # Create subdirectory structure to work or source directory
                work_subdir_path = os.path.abspath(os.path.join(self.instance.basedir, dst_subdir))
                if not os.path.exists(work_subdir_path):
                    try:
                        create_dir(work_subdir_path)
                    except OSError:
                        self._toolbox.msg_error.emit(
                            "[OSError] Creating directory <b>{0}</b> failed.".format(work_subdir_path)
                        )
                        return False
                self._toolbox.msg.emit(
                    "\tCopying file <b>{0}</b> into subdirectory <b>{2}{1}</b>".format(fname, dst_subdir, os.path.sep)
                )
            try:
                shutil.copyfile(src_path, dst_path)
                n_copied_files += 1
            except OSError as e:
                self._toolbox.msg_error.emit("Copying file <b>{0}</b> to <b>{1}</b> failed".format(src_path, dst_path))
                self._toolbox.msg_error.emit("{0}".format(e))
                if e.errno == 22:
                    msg = (
                        "The reason might be:\n"
                        "[1] The destination file already exists and it cannot be "
                        "overwritten because it is locked by Julia or some other application.\n"
                        "[2] You don't have the necessary permissions to overwrite the file.\n"
                        "To solve the problem, you can try the following:\n[1] Execute the Tool in work "
                        "directory.\n[2] If you are executing a Julia Tool with Julia 0.6.x, upgrade to "
                        "Julia 0.7 or newer.\n"
                        "[3] Close any other background application(s) that may have locked the file.\n"
                        "And try again.\n"
                    )
                    self._toolbox.msg_warning.emit(msg)
                return False
        self._toolbox.msg.emit("\tCopied <b>{0}</b> input file(s)".format(n_copied_files))
        return True

    def copy_optional_input_files(self, paths):
        """Copy optional input files from given paths to work or source directory, depending on
        where the Tool template requires them to be.

        Args:
            paths (dict): Key is the optional file name pattern, value is a list of paths to source files.

        Returns:
            Boolean variable depending on operation success
        """
        n_copied_files = 0
        for dst, src_paths in paths.items():
            if not isinstance(src_paths, list):
                self._toolbox.msg_error.emit("Copying optional input files failed. src_paths should be a list.")
                return False
            for src_path in src_paths:
                if not os.path.exists(src_path):
                    self._toolbox.msg_error.emit("\tFile <b>{0}</b> does not exist".format(src_path))
                    continue
                # Get file name that matched the search pattern
                src_dir, dst_fname = os.path.split(src_path)
                # Check if the search pattern included subdirectories (e.g. 'input/*.csv')
                # This means that /input/ directory should be created to work (or source) directory
                # before copying the files
                dst_subdir, _search_pattern = os.path.split(dst)
                if not dst_subdir:
                    # No subdirectories to create
                    self._toolbox.msg.emit("\tCopying optional file <b>{0}</b>".format(dst_fname))
                    dst_path = os.path.abspath(os.path.join(self.instance.basedir, dst_fname))
                else:
                    # Create subdirectory structure to work or source directory
                    work_subdir_path = os.path.abspath(os.path.join(self.instance.basedir, dst_subdir))
                    if not os.path.exists(work_subdir_path):
                        try:
                            create_dir(work_subdir_path)
                        except OSError:
                            self._toolbox.msg_error.emit(
                                "[OSError] Creating directory <b>{0}</b> failed.".format(work_subdir_path)
                            )
                            continue
                    self._toolbox.msg.emit(
                        "\tCopying optional file <b>{0}</b> into subdirectory <b>{2}{1}</b>".format(
                            dst_fname, dst_subdir, os.path.sep
                        )
                    )
                    dst_path = os.path.abspath(os.path.join(work_subdir_path, dst_fname))
                try:
                    shutil.copyfile(src_path, dst_path)
                    n_copied_files += 1
                except OSError as e:
                    self._toolbox.msg_error.emit(
                        "Copying optional file <b>{0}</b> to <b>{1}</b> failed".format(src_path, dst_path)
                    )
                    self._toolbox.msg_error.emit("{0}".format(e))
                    if e.errno == 22:
                        msg = (
                            "The reason might be:\n"
                            "[1] The destination file already exists and it cannot be "
                            "overwritten because it is locked by Julia or some other application.\n"
                            "[2] You don't have the necessary permissions to overwrite the file.\n"
                            "To solve the problem, you can try the following:\n[1] Execute the Tool in work "
                            "directory.\n[2] If you are executing a Julia Tool with Julia 0.6.x, upgrade to "
                            "Julia 0.7 or newer.\n"
                            "[3] Close any other background application(s) that may have locked the file.\n"
                            "And try again.\n"
                        )
                        self._toolbox.msg_warning.emit(msg)
        self._toolbox.msg.emit("\tCopied <b>{0}</b> optional input file(s)".format(n_copied_files))
        return True

    def find_output_items(self):
        """Find output items of this Tool.

        Returns:
            List of Data Store and Data Connection items.
        """
        item_list = list()
        for output_item in self._toolbox.connection_model.output_items(self.name):
            found_index = self._toolbox.project_item_model.find_item(output_item)
            if not found_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(output_item))
                continue
            item_data = self._toolbox.project_item_model.project_item(found_index)
            item_list.append(item_data)
        return item_list

    def create_refs_to_output_files(self, output_items):
        """Create refs to Tool output files in all child Data Connections and Data Stores.
        In case of Data Store only one reference is created (to the first file in the list)

        Args:
            output_items (list): Destination items for output files.
        """
        for item in output_items:
            n_created_refs = 0
            # NOTE: We need to take the basename here since the tool instance saves
            # the output files *without* the 'subfolder' part in the output folder
            for output_file in [os.path.basename(x) for x in self._tool_template.outputfiles]:
                self._toolbox.msg.emit(
                    "*** Creating reference to Tool <b>{0}</b>'s output file {1} "
                    "in {2} <b>{3}</b> ***".format(self.name, output_file, item.item_type, item.name)
                )
                # NOTE: output files are saved
                src_path = os.path.join(self.instance.output_dir, output_file)
                if not os.path.exists(src_path):
                    self._toolbox.msg_error.emit("\t Output file <b>{0}</b> does not exist".format(src_path))
                    continue
                if item.item_type == "Data Connection":
                    item.add_files_to_references([src_path])  # Give path in a list
                    n_created_refs += 1
                elif item.item_type == "Data Store":
                    reference = {
                        'url': 'sqlite:///{0}'.format(src_path),
                        'database': output_file,
                        'username': getpass.getuser(),
                    }
                    item.set_reference(reference)
                    item.load_reference_into_selections()
                    self._toolbox.msg.emit("\tCreated <b>1</b> reference")
                    break
                else:
                    self._toolbox.msg_warning.emit("\t<b>Not implemented</b>")
                    break
            if item.item_type == "Data Connection":
                self._toolbox.msg.emit("\tCreated <b>{0}</b> reference(s)".format(n_created_refs))

    @Slot(int, name="execution_finished")
    def execution_finished(self, return_code):
        """Tool execution finished."""
        self._toolbox.ui.pushButton_tool_stop.setEnabled(False)
        self._toolbox.ui.pushButton_tool_execute.setEnabled(True)
        self._graphics_item.stop_animation()
        # Disconnect instance finished signal
        self.instance.instance_finished_signal.disconnect(self.execution_finished)
        if return_code == 0:
            # copy output files to data directories of connected items
            output_items = self.find_output_items()
            if output_items:
                # self._toolbox.msg.emit("Creating references to Tool output files in connected items")
                self.create_refs_to_output_files(output_items)
            self._toolbox.msg_success.emit("Tool <b>{0}</b> execution finished".format(self.name))
        else:
            self._toolbox.msg_error.emit("Tool <b>{0}</b> execution failed".format(self.name))

    def update_instance(self):
        """Initialize and update instance so that it is ready for processing. This is where Tool
        type specific initialization happens (whether the tool is GAMS, Python or Julia script)."""
        if self.tool_template().tooltype == "gams":
            gams_path = self._toolbox.qsettings().value("appSettings/gamsPath", defaultValue="")
            if not gams_path == '':
                gams_exe = gams_path
            else:
                gams_exe = GAMS_EXECUTABLE
            self.instance.program = gams_exe
            self.instance.args.append(self.tool_template().main_prgm)
            self.instance.args.append("curDir=")
            self.instance.args.append("{0}".format(self.instance.basedir))
            self.instance.args.append("logoption=3")  # TODO: This should be an option in Settings
            self.append_instance_args()  # Append Tool specific cmd line args into args list
        elif self.tool_template().tooltype == "julia":
            # Prepare command "julia script.jl"
            julia_path = self._toolbox.qsettings().value("appSettings/juliaPath", defaultValue="")
            if not julia_path == "":
                julia_cmd = julia_path
            else:
                julia_cmd = JULIA_EXECUTABLE
            work_dir = self.instance.basedir
            script_path = os.path.join(work_dir, self.tool_template().main_prgm)
            self.instance.program = julia_cmd
            self.instance.args.append(script_path)
            self.append_instance_args()
            use_embedded_julia = self._toolbox.qsettings().value("appSettings/useEmbeddedJulia", defaultValue="2")
            if use_embedded_julia == "2":
                # Prepare Julia REPL command
                # TODO: See if this can be simplified
                mod_work_dir = work_dir.__repr__().strip("'")
                args = r'["' + r'", "'.join(self.instance.args[1:]) + r'"]'
                self.instance.julia_repl_command = (
                    r'cd("{}");'
                    r'empty!(ARGS);'
                    r'append!(ARGS, {});'
                    r'include("{}")'.format(mod_work_dir, args, self.tool_template().main_prgm)
                )
        elif self.tool_template().tooltype == "python":
            # Prepare command "python script.py"
            python_path = self._toolbox.qsettings().value("appSettings/pythonPath", defaultValue="")
            if not python_path == "":
                python_cmd = python_path
            else:
                python_cmd = PYTHON_EXECUTABLE
            work_dir = self.instance.basedir
            script_path = os.path.join(work_dir, self.tool_template().main_prgm)
            self.instance.program = python_cmd
            self.instance.args.append(script_path)  # TODO: Why are we doing this?
            self.append_instance_args()
            use_embedded_python = self._toolbox.qsettings().value("appSettings/useEmbeddedPython", defaultValue="0")
            if use_embedded_python == "2":
                # Prepare a command list (FIFO queue) with two commands for Python Console
                # 1st cmd: Change current work directory
                # 2nd cmd: Run script with given args
                # Cast args in list to strings and combine them to a single string
                # Skip first arg since it's the script path (see above)
                args = " ".join([str(x) for x in self.instance.args[1:]])
                cd_work_dir_cmd = "%cd -q {0} ".format(work_dir)  # -q: quiet
                run_script_cmd = "%run \"{0}\" {1}".format(self.tool_template().main_prgm, args)
                # Populate FIFO command queue
                self.instance.ipython_command_list.append(cd_work_dir_cmd)
                self.instance.ipython_command_list.append(run_script_cmd)
        elif self.tool_template().tooltype == "executable":
            batch_path = os.path.join(self.instance.basedir, self.tool_template().main_prgm)
            if sys.platform != "win32":
                self.instance.program = "sh"
                self.instance.args.append(batch_path)
            else:
                self.instance.program = batch_path
            self.append_instance_args()  # Append Tool specific cmd line args into args list

    def append_instance_args(self):
        """Append Tool template command line args into instance args list."""
        # TODO: Deal with cmdline arguments that have spaces. They should be stored in a list in the definition file
        if (self.tool_template().cmdline_args is not None) and (not self.tool_template().cmdline_args == ''):
            # Tool template cmdline args is a space delimited string. Add them to a list.
            self.instance.args += self.tool_template().cmdline_args.split(" ")

    def populate_source_file_model(self, items):
        """Add required source files (includes) into a model.
        If items is None or an empty list, model is cleared."""
        self.source_file_model.clear()
        # self.source_file_model.setHorizontalHeaderItem(0, QStandardItem("Source files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.source_file_model.appendRow(qitem)

    def populate_input_file_model(self, items):
        """Add required Tool input files into a model.
        If items is None or an empty list, model is cleared."""
        self.input_file_model.clear()
        # self.input_file_model.setHorizontalHeaderItem(0, QStandardItem("Input files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.input_file_model.appendRow(qitem)

    def populate_opt_input_file_model(self, items):
        """Add optional Tool template files into a model.
        If items is None or an empty list, model is cleared."""
        self.opt_input_file_model.clear()
        # self.opt_input_file_model.setHorizontalHeaderItem(0, QStandardItem("Optional input files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.opt_input_file_model.appendRow(qitem)

    def populate_output_file_model(self, items):
        """Add Tool output files into a model.
         If items is None or an empty list, model is cleared."""
        self.output_file_model.clear()
        # self.output_file_model.setHorizontalHeaderItem(0, QStandardItem("Output files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.output_file_model.appendRow(qitem)

    def populate_template_model(self, populate):
        """Add all tool template specs to a single QTreeView.
        If items is None or an empty list, model is cleared.

        Args:
            populate (bool): False to clear model, True to populate.
        """
        self.template_model.clear()
        self.template_model.setHorizontalHeaderItem(0, QStandardItem("Template specification"))  # Add header
        # Add category items
        source_file_category_item = QStandardItem("Source files")
        input_category_item = QStandardItem("Input files")
        opt_input_category_item = QStandardItem("Optional input files")
        output_category_item = QStandardItem("Output files")
        self.template_model.appendRow(source_file_category_item)
        self.template_model.appendRow(input_category_item)
        self.template_model.appendRow(opt_input_category_item)
        self.template_model.appendRow(output_category_item)
        if populate:
            if self.source_file_model.rowCount() > 0:
                for row in range(self.source_file_model.rowCount()):
                    text = self.source_file_model.item(row).data(Qt.DisplayRole)
                    qitem = QStandardItem(text)
                    qitem.setFlags(~Qt.ItemIsEditable)
                    qitem.setData(QFileIconProvider().icon(QFileInfo(text)), Qt.DecorationRole)
                    source_file_category_item.appendRow(qitem)
            if self.input_file_model.rowCount() > 0:
                for row in range(self.input_file_model.rowCount()):
                    text = self.input_file_model.item(row).data(Qt.DisplayRole)
                    qitem = QStandardItem(text)
                    qitem.setFlags(~Qt.ItemIsEditable)
                    qitem.setData(QFileIconProvider().icon(QFileInfo(text)), Qt.DecorationRole)
                    input_category_item.appendRow(qitem)
            if self.opt_input_file_model.rowCount() > 0:
                for row in range(self.opt_input_file_model.rowCount()):
                    text = self.opt_input_file_model.item(row).data(Qt.DisplayRole)
                    qitem = QStandardItem(text)
                    qitem.setFlags(~Qt.ItemIsEditable)
                    qitem.setData(QFileIconProvider().icon(QFileInfo(text)), Qt.DecorationRole)
                    opt_input_category_item.appendRow(qitem)
            if self.output_file_model.rowCount() > 0:
                for row in range(self.output_file_model.rowCount()):
                    text = self.output_file_model.item(row).data(Qt.DisplayRole)
                    qitem = QStandardItem(text)
                    qitem.setFlags(~Qt.ItemIsEditable)
                    qitem.setData(QFileIconProvider().icon(QFileInfo(text)), Qt.DecorationRole)
                    output_category_item.appendRow(qitem)

    def update_name_label(self):
        """Update Tool tab name label. Used only when renaming project items."""
        self._toolbox.ui.label_tool_name.setText(self.name)

    @Slot(bool, name="open_directory")
    def open_directory(self, checked=False):
        """Open file explorer in Tool data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))
