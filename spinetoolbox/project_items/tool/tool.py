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
Tool class.

:author: P. Savolainen (VTT)
:date:   19.12.2017
"""
import fnmatch
import logging
import os
import shutil
import tempfile
import pathlib
import glob
import fnmatch
from PySide2.QtCore import Slot, Qt, QUrl, QFileInfo, QTimeLine
from PySide2.QtGui import QDesktopServices, QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QFileIconProvider
from spinetoolbox.project_item import ProjectItem, ProjectItemResource
from spinetoolbox.config import TOOL_OUTPUT_DIR
from spinetoolbox.widgets.custom_menus import ToolSpecificationOptionsPopupmenu
from spinetoolbox.project_items.tool.widgets.custom_menus import ToolContextMenu
from spinetoolbox.helpers import create_dir, create_output_dir_timestamp


class Tool(ProjectItem):
    def __init__(self, toolbox, name, description, x, y, tool="", execute_in_work=True):
        """Tool class.

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            name (str): Object name
            description (str): Object description
            x (float): Initial X coordinate of item icon
            y (float): Initial Y coordinate of item icon
            tool (str): Name of this Tool's Tool specification
            execute_in_work (bool): Execute associated Tool specification in work (True) or source directory (False)
        """
        super().__init__(toolbox, "Tool", name, description, x, y)
        self.source_file_model = QStandardItemModel()
        self.populate_source_file_model(None)
        self.input_file_model = QStandardItemModel()
        self.populate_input_file_model(None)
        self.opt_input_file_model = QStandardItemModel()
        self.populate_opt_input_file_model(None)
        self.output_file_model = QStandardItemModel()
        self.populate_output_file_model(None)
        self.specification_model = QStandardItemModel()
        self.populate_specification_model(False)
        self.source_files = list()
        self.execute_in_work = execute_in_work
        self._tool_specification = self._toolbox.tool_specification_model.find_tool_specification(tool)
        if tool != "" and not self._tool_specification:
            # Clarifications for user
            self._toolbox.msg_error.emit(
                "Tool <b>{0}</b> should have a Tool "
                "specification <b>{1}</b> but it was not found".format(self.name, tool)
            )
        self.set_tool_specification(self._tool_specification)
        if not self._tool_specification:
            self._tool_specification_name = ""
        else:
            self._tool_specification_name = self.tool_specification().name
        self.tool_specification_options_popup_menu = None
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        self.extra_cmdline_args = ''  # This may be used for additional Tool specific command line arguments
        # Base directory for execution, maybe it should be called `execution_dir`
        self.basedir = None
        # Make directory for results
        self.output_dir = os.path.join(self.data_dir, TOOL_OUTPUT_DIR)

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = super().make_signal_handler_dict()
        s[self._properties_ui.toolButton_tool_open_dir.clicked] = lambda checked=False: self.open_directory()
        s[self._properties_ui.pushButton_tool_results.clicked] = self.open_results
        s[self._properties_ui.comboBox_tool.currentIndexChanged] = self.update_tool_specification
        s[self._properties_ui.radioButton_execute_in_work.toggled] = self.update_execution_mode
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
        self._properties_ui.label_tool_name.setText(self.name)
        self._properties_ui.treeView_specification.setModel(self.specification_model)
        if self._tool_specification_name == "":
            self._properties_ui.comboBox_tool.setCurrentIndex(-1)
            self.set_tool_specification(None)
        else:
            tool_specification = self._toolbox.tool_specification_model.find_tool_specification(
                self._tool_specification_name
            )
            row = self._toolbox.tool_specification_model.tool_specification_row(self._tool_specification_name)
            self._properties_ui.comboBox_tool.setCurrentIndex(row)  # Row in tool temp model
            self.set_tool_specification(tool_specification)

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""
        if not self._tool_specification:
            self._tool_specification_name = ""
        else:
            self._tool_specification_name = self.tool_specification().name
        self.execute_in_work = self._properties_ui.radioButton_execute_in_work.isChecked()

    @Slot(bool, name="update_execution_mode")
    def update_execution_mode(self, checked):
        """Slot for execute in work radio button toggled signal."""
        self.execute_in_work = checked

    @Slot(int, name="update_tool_specification")
    def update_tool_specification(self, row):
        """Update Tool specification according to selection in the specification comboBox.

        Args:
            row (int): Selected row in the comboBox
        """
        if row == -1:
            self._properties_ui.comboBox_tool.setCurrentIndex(-1)
            self.set_tool_specification(None)
        else:
            new_tool = self._toolbox.tool_specification_model.tool_specification(row)
            self.set_tool_specification(new_tool)

    def set_tool_specification(self, tool_specification):
        """Sets Tool specification for this Tool. Removes Tool specification if None given as argument.

        Args:
            tool_specification (ToolSpecification): Tool specification of this Tool. None removes the specification.
        """
        self._tool_specification = tool_specification
        self.update_tool_models()
        self.update_tool_ui()
        self.item_changed.emit()

    def update_tool_ui(self):
        """Update Tool UI to show Tool specification details. Used when Tool specification is changed.
        Overrides execution mode (work or source) with the specification default."""
        if not self._properties_ui:
            # This happens when calling self.set_tool_specification() in the __init__ method,
            # because the UI only becomes available *after* adding the item to the project_item_model... problem??
            return
        if not self.tool_specification():
            self._properties_ui.lineEdit_tool_args.setText("")
            self._properties_ui.radioButton_execute_in_work.setChecked(True)
        else:
            self._properties_ui.lineEdit_tool_args.setText(self.tool_specification().cmdline_args)
            if self.execute_in_work:
                self._properties_ui.radioButton_execute_in_work.setChecked(True)
            else:
                self._properties_ui.radioButton_execute_in_source.setChecked(True)
        self.tool_specification_options_popup_menu = ToolSpecificationOptionsPopupmenu(self._toolbox, self)
        self._properties_ui.toolButton_tool_specification.setMenu(self.tool_specification_options_popup_menu)
        self._properties_ui.treeView_specification.expandAll()

    def update_tool_models(self):
        """Update Tool models with Tool specification details. Used when Tool specification is changed.
        Overrides execution mode (work or source) with the specification default."""
        if not self.tool_specification():
            self.populate_source_file_model(None)
            self.populate_input_file_model(None)
            self.populate_opt_input_file_model(None)
            self.populate_output_file_model(None)
            self.populate_specification_model(populate=False)
        else:
            self.populate_source_file_model(self.tool_specification().includes)
            self.populate_input_file_model(self.tool_specification().inputfiles)
            self.populate_opt_input_file_model(self.tool_specification().inputfiles_opt)
            self.populate_output_file_model(self.tool_specification().outputfiles)
            self.populate_specification_model(populate=True)
            self.execute_in_work = self.tool_specification().execute_in_work

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

    @Slot(name="edit_tool_specification")
    def edit_tool_specification(self):
        """Open Tool specification editor for the Tool specification attached to this Tool."""
        index = self._toolbox.tool_specification_model.tool_specification_index(self.tool_specification().name)
        self._toolbox.edit_tool_specification(index)

    @Slot(name="open_tool_specification_file")
    def open_tool_specification_file(self):
        """Open Tool specification file."""
        index = self._toolbox.tool_specification_model.tool_specification_index(self.tool_specification().name)
        self._toolbox.open_tool_specification_file(index)

    @Slot(name="open_tool_main_program_file")
    def open_tool_main_program_file(self):
        """Open Tool specification main program file in an external text edit application."""
        index = self._toolbox.tool_specification_model.tool_specification_index(self.tool_specification().name)
        self._toolbox.open_tool_main_program_file(index)

    @Slot(name="open_tool_main_directory")
    def open_tool_main_directory(self):
        """Open directory where the Tool specification main program is located in file explorer."""
        if not self.tool_specification():
            return
        dir_url = "file:///" + self.tool_specification().path
        self._toolbox.open_anchor(QUrl(dir_url, QUrl.TolerantMode))

    def tool_specification(self):
        """Returns Tool specification."""
        return self._tool_specification

    def populate_source_file_model(self, items):
        """Add required source files (includes) into a model.
        If items is None or an empty list, model is cleared."""
        self.source_file_model.clear()
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
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.input_file_model.appendRow(qitem)

    def populate_opt_input_file_model(self, items):
        """Add optional Tool specification files into a model.
        If items is None or an empty list, model is cleared."""
        self.opt_input_file_model.clear()
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
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.output_file_model.appendRow(qitem)

    def populate_specification_model(self, populate):
        """Add all tool specifications to a single QTreeView.

        Args:
            populate (bool): False to clear model, True to populate.
        """
        self.specification_model.clear()
        self.specification_model.setHorizontalHeaderItem(0, QStandardItem("Template specification"))  # Add header
        # Add category items
        source_file_category_item = QStandardItem("Source files")
        input_category_item = QStandardItem("Input files")
        opt_input_category_item = QStandardItem("Optional input files")
        output_category_item = QStandardItem("Output files")
        self.specification_model.appendRow(source_file_category_item)
        self.specification_model.appendRow(input_category_item)
        self.specification_model.appendRow(opt_input_category_item)
        self.specification_model.appendRow(output_category_item)
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
        self._properties_ui.label_tool_name.setText(self.name)

    def execute(self):
        """Executes this Tool."""
        exec_inst = self._project.execution_instance
        if not self.tool_specification():
            self._toolbox.msg_warning.emit("Tool <b>{0}</b> has no Tool specification to execute".format(self.name))
            exec_inst.project_item_execution_finished_signal.emit(0)  # continue
            return
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Tool <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        if self.execute_in_work:
            work_or_source = "work"
            work_dir = self._project.work_dir
            self.basedir = tempfile.mkdtemp(
                suffix='__toolbox', prefix=self.tool_specification().short_name + '__', dir=work_dir
            )
            # Make work directory anchor with path as tooltip
            work_anchor = (
                "<a style='color:#99CCFF;' title='"
                + self.basedir
                + "' href='file:///"
                + self.basedir
                + "'>work directory</a>"
            )
            self._toolbox.msg.emit(
                "*** Copying Tool specification <b>{0}</b> source files to {1} ***".format(
                    self.tool_specification().name, work_anchor
                )
            )
            if not self.copy_program_files():
                self._toolbox.msg_error.emit("Copying program files to base directory failed.")
                exec_inst.project_item_execution_finished_signal.emit(-1)  # abort
                return
        else:
            work_or_source = "source"
            self.basedir = self.tool_specification().path
            # Make source directory anchor with path as tooltip
            src_dir_anchor = (
                "<a style='color:#99CCFF;' title='"
                + self.basedir
                + "' href='file:///"
                + self.basedir
                + "'>source directory</a>"
            )
            self._toolbox.msg.emit(
                "*** Executing Tool specification <b>{0}</b> in {1} ***".format(
                    self.tool_specification().name, src_dir_anchor
                )
            )
        self._toolbox.msg.emit("*** Executing in <b>{0}</b> directory mode ***".format(work_or_source))
        # Find required input files for ToolInstance (if any)
        if self.input_file_model.rowCount() > 0:
            self._toolbox.msg.emit("*** Checking Tool specification requirements ***")
            n_dirs, n_files = self.count_files_and_dirs()
            # logging.debug("Tool requires {0} dirs and {1} files".format(n_dirs, n_files))
            if n_files > 0:
                self._toolbox.msg.emit("*** Searching for required input files ***")
                file_paths = self.find_input_files(exec_inst)
                not_found = [k for k, v in file_paths.items() if v is None]
                if not_found:
                    self._toolbox.msg_error.emit("Required file(s) <b>{0}</b> not found".format(", ".join(not_found)))
                    exec_inst.project_item_execution_finished_signal.emit(-1)  # abort
                    return
                # Required files and dirs should have been found at this point, so create instance
                self._toolbox.msg.emit("*** Copying input files to {0} directory ***".format(work_or_source))
                # Copy input files to ToolInstance work or source directory
                if not self.copy_input_files(file_paths):
                    self._toolbox.msg_error.emit("Copying input files failed. Tool execution aborted.")
                    exec_inst.project_item_execution_finished_signal.emit(-1)  # abort
                    return
            else:  # just for testing
                # logging.debug("No input files to copy")
                pass
            if n_dirs > 0:
                self._toolbox.msg.emit("*** Creating input subdirectories to {0} directory ***".format(work_or_source))
                if not self.create_input_dirs():
                    # Creating directories failed -> abort
                    self._toolbox.msg_error.emit("Creating input subdirectories failed. Tool execution aborted.")
                    exec_inst.project_item_execution_finished_signal.emit(-1)  # abort
                    return
            else:  # just for testing
                # logging.debug("No directories to create")
                pass
        # Check if there are any optional input files to copy
        if self.opt_input_file_model.rowCount() > 0:
            self._toolbox.msg.emit("*** Searching for optional input files ***")
            optional_file_paths = self.find_optional_input_files(exec_inst)
            for k, v in optional_file_paths.items():
                self._toolbox.msg.emit("\tFound <b>{0}</b> files matching pattern <b>{1}</b>".format(len(v), k))
            if not self.copy_optional_input_files(optional_file_paths):
                self._toolbox.msg_warning.emit("Copying optional input files failed")
        if not self.create_output_dirs():
            self._toolbox.msg_error.emit("Creating output subdirectories failed. Tool execution aborted.")
            exec_inst.project_item_execution_finished_signal.emit(-1)  # abort
            return
        self.get_icon().start_animation()
        self.instance = self.tool_specification().create_tool_instance(self.basedir)
        self.instance.prepare()  # Make command and stuff
        self.instance.instance_finished_signal.connect(self.handle_execution_finished)
        self._toolbox.msg.emit(
            "*** Starting instance of Tool specification <b>{0}</b> ***".format(self.tool_specification().name)
        )
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
            _, filename = os.path.split(req_file_path)
            if not filename:
                # It's a directory
                n_dir += 1
            else:
                # It's a file
                n_file += 1
        return n_dir, n_file

    def create_input_dirs(self):
        """Iterate items in required input files and check
        if there are any directories to create. Create found
        directories directly to work or source directory.

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
                path_to_create = os.path.join(self.basedir, path)
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

    def copy_input_files(self, paths):
        """Copy input files from given paths to work or source directory, depending on
        where the Tool specification requires them to be.

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
            dst_path = os.path.abspath(os.path.join(self.basedir, dst))
            # Create subdirectories if necessary
            dst_subdir, fname = os.path.split(dst)
            if not dst_subdir:
                # No subdirectories to create
                self._toolbox.msg.emit("\tCopying file <b>{0}</b>".format(fname))
            else:
                # Create subdirectory structure to work or source directory
                work_subdir_path = os.path.abspath(os.path.join(self.basedir, dst_subdir))
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
        where the Tool specification requires them to be.

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
                _, dst_fname = os.path.split(src_path)
                # Check if the search pattern included subdirectories (e.g. 'input/*.csv')
                # This means that /input/ directory should be created to work (or source) directory
                # before copying the files
                dst_subdir, _search_pattern = os.path.split(dst)
                if not dst_subdir:
                    # No subdirectories to create
                    self._toolbox.msg.emit("\tCopying optional file <b>{0}</b>".format(dst_fname))
                    dst_path = os.path.abspath(os.path.join(self.basedir, dst_fname))
                else:
                    # Create subdirectory structure to work or source directory
                    work_subdir_path = os.path.abspath(os.path.join(self.basedir, dst_subdir))
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

    def copy_program_files(self):
        """Copies Tool specification include files to base directory."""
        n_copied_files = 0
        for i in range(self.source_file_model.rowCount()):
            filepath = self.source_file_model.item(i, 0).data(Qt.DisplayRole)
            dirname, file_pattern = os.path.split(filepath)
            src_dir = os.path.join(self.tool_specification().path, dirname)
            dst_dir = os.path.join(self.basedir, dirname)
            # Create the destination directory
            try:
                create_dir(dst_dir)
            except OSError:
                self._toolbox.msg_error.emit("Creating directory <b>{0}</b> failed".format(dst_dir))
                return False
            # Copy file if necessary
            if file_pattern:
                for src_file in glob.glob(os.path.abspath(os.path.join(src_dir, file_pattern))):
                    dst_file = os.path.abspath(os.path.join(dst_dir, os.path.basename(src_file)))
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

    def find_input_files(self, exec_inst):
        """Iterates files in required input files model and looks for them from execution instance.

        Args:
            exec_inst (ExecutionInstance): Look for files in this execution instance.

        Returns:
            Dictionary mapping required files to path where they are found, or to None if not found
        """
        file_paths = dict()
        for i in range(self.input_file_model.rowCount()):
            req_file_path = self.input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Just get the filename if there is a path attached to the file
            _, filename = os.path.split(req_file_path)
            if not filename:
                # It's a directory
                continue
            file_paths[req_file_path] = self.find_file(filename, exec_inst)
        return file_paths

    def find_optional_input_files(self, exec_inst):
        """Tries to find optional input files from previous project items in the DAG. Returns found paths.

        Args:
            exec_inst (ExecutionInstance): Look for files in this execution instance.

        Returns:
            Dictionary of optional input file paths or an empty dictionary if no files found. Key is the
            optional input item and value is a list of paths that matches the item.
        """
        file_paths = dict()
        for i in range(self.opt_input_file_model.rowCount()):
            file_path = self.opt_input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Just get the filename if there is a path attached to the file
            _, pattern = os.path.split(file_path)  # Filename may be a pattern (contains wildcards * or ?)
            if not pattern:
                # It's a directory -> skip
                continue
            found_files = self.find_optional_files(pattern, exec_inst)
            if not found_files:
                self._toolbox.msg_warning.emit("\tNo files matching pattern <b>{0}</b> found".format(pattern))
            else:
                file_paths[file_path] = found_files
        return file_paths

    def available_filepath_resources(self, exec_inst):
        """Returns available filepath resources from the given execution instance."""
        filepaths = []
        for resource in exec_inst.available_resources(self.name):
            if resource.type_ == "file" or (resource.type_ == "database" and resource.scheme == "sqlite"):
                filepaths.append(resource.path)
        return filepaths

    def find_file(self, filename, exec_inst):
        """Returns the first occurrence of full path to given file name in files available
        from the execution instance, or None if file was not found.

        Args:
            filename (str): Searched file name (no path) TODO: Change to pattern
            exec_inst (ExecutionInstance): execution instance

        Returns:
            str: Full path to file if found, None if not found
        """
        for filepath in self.available_filepath_resources(exec_inst):
            _, file_candidate = os.path.split(filepath)
            if file_candidate == filename:
                # logging.debug("Found path for {0} from dc refs: {1}".format(filename, dc_ref))
                return filepath
        return None

    def find_optional_files(self, pattern, exec_inst):
        """Returns a list of found paths to files that match the given pattern in files available
        from the execution instance.

        Returns:
            list: List of (full) paths
        """
        filepaths = self.available_filepath_resources(exec_inst)
        # Find matches when pattern includes wildcards
        if ('*' in pattern) or ('?' in pattern):
            return fnmatch.filter(filepaths, pattern)
        # Pattern is an exact filename (no wildcards)
        match = self.find_file(pattern, exec_inst)
        if match is not None:
            return [match]
        return []

    @Slot(int, name="handle_execution_finished")
    def handle_execution_finished(self, return_code):
        """Tool specification execution finished.

        Args:
            return_code (int): Process exit code
        """
        self.get_icon().stop_animation()
        # Disconnect instance finished signal
        self.instance.instance_finished_signal.disconnect(self.handle_execution_finished)
        if return_code == 0:
            self._toolbox.msg_success.emit("Tool <b>{0}</b> execution finished".format(self.name))
        else:
            self._toolbox.msg_error.emit("Tool <b>{0}</b> execution failed".format(self.name))
        self.handle_output_files(return_code)
        if not self._project.execution_instance:
            # Happens sometimes when Stop button is pressed
            return
        self._project.execution_instance.project_item_execution_finished_signal.emit(0)

    def handle_output_files(self, ret):
        """Creates a timestamped result directory for Tool specification output files. Starts copying Tool
        specification output files from work directory to result directory and print messages to Event
        Log depending on how the operation went.

        Args:
            ret (int): Tool specification process return value
        """
        exec_inst = self._project.execution_instance
        output_dir_timestamp = create_output_dir_timestamp()  # Get timestamp when tool finished
        # Create an output folder with timestamp and copy output directly there
        if ret != 0:
            result_path = os.path.abspath(os.path.join(self.output_dir, 'failed', output_dir_timestamp))
        else:
            result_path = os.path.abspath(os.path.join(self.output_dir, output_dir_timestamp))
        try:
            create_dir(result_path)
        except OSError:
            self._toolbox.msg_error.emit(
                "\tError creating timestamped output directory. "
                "Tool specification output files not copied. Please check directory permissions."
            )
            return
        # Make link to output folder
        result_anchor = (
            "<a style='color:#BB99FF;' title='"
            + result_path
            + "' href='file:///"
            + result_path
            + "'>results directory</a>"
        )
        self._toolbox.msg.emit("*** Archiving output files to {0} ***".format(result_anchor))
        if self.opt_input_file_model.rowCount() > 0:
            saved_files, failed_files = self.copy_output_files(result_path)
            if not saved_files:
                # If no files were saved
                self._toolbox.msg_error.emit("\tNo files saved")
            else:
                # If there are saved files
                # Split list into filenames and their paths
                filenames, paths = zip(*saved_files)
                self._toolbox.msg.emit("\tThe following output files were saved to results directory")
                for filename in filenames:
                    self._toolbox.msg.emit("\t\t<b>{0}</b>".format(filename))
                if ret == 0:
                    # Advertise paths
                    for path in paths:
                        resource = ProjectItemResource(
                            self, "file", url=pathlib.Path(path).as_uri(), metadata=dict(is_output=True)
                        )
                        exec_inst.advertise_resources(self.name, resource)
            if failed_files:
                # If saving some or all files failed
                self._toolbox.msg_warning.emit("\tThe following output files were not found")
                for failed_file in failed_files:
                    failed_fname = os.path.split(failed_file)[1]
                    self._toolbox.msg_warning.emit("\t\t<b>{0}</b>".format(failed_fname))
        else:
            tip_anchor = (
                "<a style='color:#99CCFF;' title='When you add output files to the Tool specification,\n "
                "they will be archived into results directory. Also, output files are passed to\n "
                "subsequent project items.' href='#'>Tip</a>"
            )
            self._toolbox.msg_warning.emit(
                "\tNo output files defined for this Tool specification. {0}".format(tip_anchor)
            )

    def create_output_dirs(self):
        """Makes sure that work directory has the necessary output directories for Tool output files.
        Checks only "outputfiles" list. Alternatively you can add directories to "inputfiles" list
        in the tool definition file.

        Returns:
            bool: True for success, False otherwise.

        Raises:
            OSError: If creating an output directory to work fails.
        """
        # TODO: Remove duplicate directory names from the list of created directories.
        for i in range(self.output_file_model.rowCount()):
            out_file_path = self.output_file_model.item(i, 0).data(Qt.DisplayRole)
            dirname = os.path.split(out_file_path)[0]
            if dirname == '':
                continue
            dst_dir = os.path.join(self.basedir, dirname)
            try:
                create_dir(dst_dir)
            except OSError:
                self._toolbox.msg_error.emit("Creating work output directory '{}' failed".format(dst_dir))
                return False
        return True

    def copy_output_files(self, target_dir):
        """Copies Tool specification output files from work directory to given target directory.

        Args:
            target_dir (str): Destination directory for Tool specification output files

        Returns:
            tuple: Contains two lists. The first list contains paths to successfully
            copied files. The second list contains paths (or patterns) of Tool specification
            output files that were not found.

        Raises:
            OSError: If creating a directory fails.
        """
        failed_files = list()
        saved_files = list()
        # logging.debug("Saving result files to <{0}>".format(target_dir))
        for i in range(self.output_file_model.rowCount()):
            pattern = self.output_file_model.item(i, 0).data(Qt.DisplayRole)
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
                for fname_path in glob.glob(os.path.abspath(os.path.join(self.basedir, pattern))):
                    # fname_path is a full path
                    fname = os.path.split(fname_path)[1]  # File name (no path)
                    dst = os.path.abspath(os.path.join(target, fname))
                    full_fname = os.path.join(dst_subdir, fname)
                    try:
                        shutil.copyfile(fname_path, dst)
                        saved_files.append((full_fname, dst))
                    except OSError:
                        self._toolbox.msg_error.emit(
                            "[OSError] Copying pattern {0} to {1} failed".format(fname_path, dst)
                        )
                        failed_files.append(full_fname)
            else:
                output_file = os.path.abspath(os.path.join(self.basedir, pattern))
                # logging.debug("Looking for {0}".format(output_file))
                if not os.path.isfile(output_file):
                    failed_files.append(pattern)
                    continue
                # logging.debug("Saving file {0}".format(fname_pattern))
                dst = os.path.abspath(os.path.join(target, fname_pattern))
                # logging.debug("Copying to {0}".format(dst))
                try:
                    shutil.copyfile(output_file, dst)
                    saved_files.append((pattern, dst))
                except OSError:
                    self._toolbox.msg_error.emit(
                        "[OSError] Copying output file {0} to {1} failed".format(output_file, dst)
                    )
                    failed_files.append(pattern)
        return saved_files, failed_files

    def stop_execution(self):
        """Stops executing this Tool."""
        self.get_icon().stop_animation()
        self.instance.instance_finished_signal.disconnect(self.handle_execution_finished)
        self._toolbox.msg_warning.emit("Stopping Tool <b>{0}</b>".format(self.name))
        self.instance.terminate_instance()
        # Note: QSubProcess, PythonReplWidget, and JuliaREPLWidget emit project_item_execution_finished_signal

    def simulate_execution(self, inst):
        """Simulates executing this Tool."""
        super().simulate_execution(inst)
        if not self.tool_specification():
            self.add_notification(
                "This Tool is not connected to a Tool specification. Set it in the Tool Properties Panel."
            )
            return
        file_paths = self.find_input_files(inst)
        not_found = [k for k, v in file_paths.items() if v is None]
        if not_found:
            self.add_notification(
                "File(s) {0} needed to execute this Tool are not provided by any input item. "
                "Connect items that provide the required files to this Tool.".format(", ".join(not_found))
            )
            return
        for i in range(self.output_file_model.rowCount()):
            out_file_name = self.output_file_model.item(i, 0).data(Qt.DisplayRole)
            out_file_path = os.path.abspath(os.path.join(self.output_dir, out_file_name))
            resource = ProjectItemResource(
                self, "file", url=pathlib.Path(out_file_path).as_uri(), metadata=dict(is_output=True)
            )
            inst.advertise_resources(self.name, resource)

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        if not self.tool_specification():
            d["tool"] = ""
        else:
            d["tool"] = self.tool_specification().name
        d["execute_in_work"] = self.execute_in_work
        return d

    def custom_context_menu(self, parent, pos):
        """Returns the context menu for this item.

        Args:
            parent (QWidget): The widget that is controlling the menu
            pos (QPoint): Position on screen
        """
        return ToolContextMenu(parent, self, pos)

    def apply_context_menu_action(self, parent, action):
        """Applies given action from context menu. Implement in subclasses as needed.

        Args:
            parent (QWidget): The widget that is controlling the menu
            action (str): The selected action
        """
        super().apply_context_menu_action(parent, action)
        if action == "Results...":
            self.open_results()
        elif action == "Stop":
            # Check that the wheel is still visible, because execution may have stopped before the user clicks Stop
            if self.get_icon().timer.state() != QTimeLine.Running:
                self._toolbox.msg.emit("Tool <b>{0}</b> is not running".format(self.name))
            else:
                self.stop_execution()  # Proceed with stopping
        elif action == "Edit Tool specification":
            self.edit_tool_specification()
        elif action == "Edit main program file...":
            self.open_tool_main_program_file()

    def rename(self, new_name):
        """Rename this item.

        Args:
            new_name (str): New name

        Returns:
            bool: Boolean value depending on success
        """
        ret = super().rename(new_name)
        if not ret:
            return False
        self.output_dir = os.path.join(self.data_dir, TOOL_OUTPUT_DIR)
        return True

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type == "Data Store":
            self._toolbox.msg.emit(
                "Link established. Data Store <b>{0}</b> url will "
                "be passed to Tool <b>{1}</b> when executing.".format(source_item.name, self.name)
            )
        elif source_item.item_type == "Data Connection":
            self._toolbox.msg.emit(
                "Link established. Tool <b>{0}</b> will look for input "
                "files from <b>{1}</b>'s references and data directory.".format(self.name, source_item.name)
            )
        elif source_item.item_type == "Gdx Export":
            self._toolbox.msg.emit(
                "Link established. Gdx Export <b>{0}</b> exported file will "
                "be passed to Tool <b>{1}</b> when executing.".format(source_item.name, self.name)
            )
        elif source_item.item_type == "Tool":
            self._toolbox.msg.emit("Link established.")
        else:
            super().notify_destination(source_item)

    @staticmethod
    def default_name_prefix():
        """see base class"""
        return "Tool"
