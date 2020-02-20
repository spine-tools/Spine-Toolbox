######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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
from PySide2.QtCore import Slot, Qt, QUrl, QFileInfo, QTimeLine, QFileSystemWatcher, QEventLoop
from PySide2.QtGui import QDesktopServices, QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QFileIconProvider
from spinetoolbox.project_item import ProjectItem, ProjectItemResource
from spinetoolbox.config import TOOL_OUTPUT_DIR
from spinetoolbox.widgets.custom_menus import ToolSpecificationOptionsPopupmenu
from spinetoolbox.project_items.tool.widgets.custom_menus import ToolContextMenu
from spinetoolbox.helpers import create_dir, create_output_dir_timestamp
from spinetoolbox.tool_specifications import ToolSpecification
from spinetoolbox.project_commands import (
    SetToolSpecificationCommand,
    UpdateToolExecuteInWorkCommand,
    UpdateToolCmdLineArgsCommand,
)


class Tool(ProjectItem):
    def __init__(
        self, name, description, x, y, toolbox, project, logger, tool="", execute_in_work=True, cmd_line_args=None
    ):
        """Tool class.

        Args:
            name (str): Object name
            description (str): Object description
            x (float): Initial X coordinate of item icon
            y (float): Initial Y coordinate of item icon
            toolbox (ToolboxUI): QMainWindow instance
            project (SpineToolboxProject): the project this item belongs to
            logger (LoggerInterface): a logger instance
            tool (str): Name of this Tool's Tool specification
            execute_in_work (bool): Execute associated Tool specification in work (True) or source directory (False)
            cmd_line_args (list): Tool command line arguments
        """
        super().__init__(name, description, x, y, project, logger)
        self._toolbox = toolbox
        self._downstream_resources = list()
        self.last_return_code = None
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
        self.cmd_line_args = list() if not cmd_line_args else cmd_line_args
        self._tool_specification = self._toolbox.tool_specification_model.find_tool_specification(tool)
        if tool != "" and not self._tool_specification:
            self._logger.msg_error.emit(
                f"Tool <b>{self.name}</b> should have a Tool specification <b>{tool}</b> but it was not found"
            )
        if self._tool_specification:
            self.execute_in_work = self._tool_specification.execute_in_work
        self.do_set_tool_specification(self._tool_specification)
        self.tool_specification_options_popup_menu = None
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        # Base directory for execution, maybe it should be called `execution_dir`
        self.basedir = None
        # Make directory for results
        self.output_dir = os.path.join(self.data_dir, TOOL_OUTPUT_DIR)
        self.output_files_watcher = QFileSystemWatcher(self)
        self.output_files_watcher.fileChanged.connect(lambda path: self.item_changed.emit())

    @staticmethod
    def item_type():
        """See base class."""
        return "Tool"

    @staticmethod
    def category():
        """See base class."""
        return "Tools"

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = super().make_signal_handler_dict()
        s[self._properties_ui.toolButton_tool_open_dir.clicked] = lambda checked=False: self.open_directory()
        s[self._properties_ui.pushButton_tool_results.clicked] = self.open_results
        s[self._properties_ui.comboBox_tool.currentIndexChanged] = self.update_tool_specification
        s[self._properties_ui.radioButton_execute_in_work.toggled] = self.update_execution_mode
        s[self._properties_ui.lineEdit_tool_args.editingFinished] = self.update_tool_cmd_line_args
        return s

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""
        self._properties_ui.label_tool_name.setText(self.name)
        self._properties_ui.treeView_specification.setModel(self.specification_model)
        self.update_execute_in_work_button()
        self.update_tool_ui()

    @Slot(bool)
    def update_execution_mode(self, checked):
        """Pushed a new UpdateToolExecuteInWorkCommand to the toolbox stack."""
        self._toolbox.undo_stack.push(UpdateToolExecuteInWorkCommand(self, checked))

    def do_update_execution_mode(self, execute_in_work):
        """Updates execute_in_work setting."""
        if self.execute_in_work == execute_in_work:
            return
        self.execute_in_work = execute_in_work
        self.update_execute_in_work_button()

    def update_execute_in_work_button(self):
        if not self._active:
            return
        self._properties_ui.radioButton_execute_in_work.blockSignals(True)
        if self.execute_in_work:
            self._properties_ui.radioButton_execute_in_work.setChecked(True)
        else:
            self._properties_ui.radioButton_execute_in_source.setChecked(True)
        self._properties_ui.radioButton_execute_in_work.blockSignals(False)

    @Slot(int)
    def update_tool_specification(self, row):
        """Update Tool specification according to selection in the specification comboBox.

        Args:
            row (int): Selected row in the comboBox
        """
        if row == -1:
            self.set_tool_specification(None)
        else:
            new_tool = self._toolbox.tool_specification_model.tool_specification(row)
            self.set_tool_specification(new_tool)
            self.do_update_execution_mode(new_tool.execute_in_work)

    @Slot()
    def update_tool_cmd_line_args(self):
        """Updates tool cmd line args list as line edit text is changed."""
        txt = self._properties_ui.lineEdit_tool_args.text()
        cmd_line_args = ToolSpecification.split_cmdline_args(txt)
        if self.cmd_line_args == cmd_line_args:
            return
        self._toolbox.undo_stack.push(UpdateToolCmdLineArgsCommand(self, cmd_line_args))

    def do_update_tool_cmd_line_args(self, cmd_line_args):
        self.cmd_line_args = cmd_line_args
        if not self._active:
            return
        self._properties_ui.lineEdit_tool_args.blockSignals(True)
        self._properties_ui.lineEdit_tool_args.setText(" ".join(self.cmd_line_args))
        self._properties_ui.lineEdit_tool_args.blockSignals(False)

    def set_tool_specification(self, tool_specification):
        """Pushes a new SetToolSpecificationCommand to the toolbox' undo stack.
        """
        if tool_specification == self._tool_specification:
            return
        self._toolbox.undo_stack.push(SetToolSpecificationCommand(self, tool_specification))

    def do_set_tool_specification(self, tool_specification):
        """Sets Tool specification for this Tool. Removes Tool specification if None given as argument.

        Args:
            tool_specification (ToolSpecification): Tool specification of this Tool. None removes the specification.
        """
        self._tool_specification = tool_specification
        self.update_tool_models()
        self.update_tool_ui()
        self.item_changed.emit()

    def update_tool_ui(self):
        """Updates Tool UI to show Tool specification details. Used when Tool specification is changed.
        Overrides execution mode (work or source) with the specification default."""
        if not self._active:
            return
        if not self._properties_ui:
            # This happens when calling self.set_tool_specification() in the __init__ method,
            # because the UI only becomes available *after* adding the item to the project_item_model... problem??
            return
        if not self.tool_specification():
            self._properties_ui.comboBox_tool.setCurrentIndex(-1)
            self._properties_ui.lineEdit_tool_spec_args.setText("")
            self.do_update_execution_mode(True)
        else:
            self._properties_ui.comboBox_tool.setCurrentText(self.tool_specification().name)
            self._properties_ui.lineEdit_tool_spec_args.setText(" ".join(self.tool_specification().cmdline_args))
        self.tool_specification_options_popup_menu = ToolSpecificationOptionsPopupmenu(self._toolbox, self)
        self._properties_ui.toolButton_tool_specification.setMenu(self.tool_specification_options_popup_menu)
        self._properties_ui.treeView_specification.expandAll()
        self._properties_ui.lineEdit_tool_args.setText(" ".join(self.cmd_line_args))

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

    @Slot(bool)
    def open_results(self, checked=False):
        """Open output directory in file browser."""
        if not os.path.exists(self.output_dir):
            self._logger.msg_warning.emit(f"Tool <b>{self.name}</b> has no results. Click Execute to generate them.")
            return
        url = "file:///" + self.output_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._logger.msg_error.emit(f"Failed to open directory: {self.output_dir}")

    @Slot()
    def edit_tool_specification(self):
        """Open Tool specification editor for the Tool specification attached to this Tool."""
        index = self._toolbox.tool_specification_model.tool_specification_index(self.tool_specification().name)
        self._toolbox.edit_tool_specification(index)

    @Slot()
    def open_tool_specification_file(self):
        """Open Tool specification file."""
        index = self._toolbox.tool_specification_model.tool_specification_index(self.tool_specification().name)
        self._toolbox.open_tool_specification_file(index)

    @Slot()
    def open_tool_main_program_file(self):
        """Open Tool specification main program file in an external text edit application."""
        index = self._toolbox.tool_specification_model.tool_specification_index(self.tool_specification().name)
        self._toolbox.open_tool_main_program_file(index)

    @Slot()
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
        self.specification_model.setHorizontalHeaderItem(0, QStandardItem("Tool specification"))  # Add header
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

    def _update_base_directory(self):
        """Updates the path to the base directory, depending on `execute_in_work`.
        """
        if self.execute_in_work:
            work_dir = self._toolbox.work_dir
            self.basedir = tempfile.mkdtemp(
                suffix='__toolbox', prefix=self.tool_specification().short_name + '__', dir=work_dir
            )
        else:
            self.basedir = self.tool_specification().path

    def output_resources_forward(self):
        """See base class."""
        watched_files = self.output_files_watcher.files()
        if watched_files:
            self.output_files_watcher.removePaths(watched_files)
        if not self.basedir:
            output_files = self._find_last_output_files()
            metadata = dict()
        else:
            output_files = [
                os.path.abspath(os.path.join(self.basedir, self.output_file_model.item(i, 0).data(Qt.DisplayRole)))
                for i in range(self.output_file_model.rowCount())
            ]
            metadata = dict(future=True)
        if output_files:
            self.output_files_watcher.addPaths(output_files)
        return [
            ProjectItemResource(self, "file", url=pathlib.Path(output_file).as_uri(), metadata=metadata)
            for output_file in output_files
        ]

    def _find_last_output_files(self):
        """Returns a list of most recent output files from the results directory.

        Returns:
            list
        """
        output_files = []
        filenames = [
            self.output_file_model.item(i, 0).data(Qt.DisplayRole) for i in range(self.output_file_model.rowCount())
        ]
        for root, dirs, files in os.walk(self.output_dir):
            if "failed" in dirs:
                dirs.remove("failed")
            dirs.sort(reverse=True)
            for f in sorted(files, reverse=True):
                if f in filenames:
                    filenames.remove(f)
                    output_files.append(os.path.join(root, f))
                    if not filenames:
                        return output_files
        return output_files

    def execute_backward(self, resources):
        """See base class."""
        self._downstream_resources = resources.copy()
        return True

    def execute_forward(self, resources):
        """See base class."""
        if not self.tool_specification():
            self._logger.msg_warning.emit(f"Tool <b>{self.name}</b> has no Tool specification to execute")
            return False
        self._update_base_directory()
        if self.execute_in_work:
            work_or_source = "work"
            work_dir = self._toolbox.work_dir
            if not work_dir:
                self._toolbox.msg_error.emit("Work directory missing. Please check Settings.")
                return False
            if not self.basedir:
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
                self._logger.msg_error.emit("Copying program files to base directory failed.")
                return False
        else:
            work_or_source = "source"
        # Make source directory anchor with path as tooltip
        anchor = (
            f"<a style='color:#99CCFF;' title='{self.basedir}'"
            f"href='file:///{self.basedir}'>{work_or_source} directory</a>"
        )
        self._logger.msg.emit(
            f"*** Executing Tool specification <b>{self.tool_specification().name}</b> in {anchor} ***"
        )
        # Find required input files for ToolInstance (if any)
        if self.input_file_model.rowCount() > 0:
            self._logger.msg.emit("*** Checking Tool specification requirements ***")
            n_dirs, n_files = self.count_files_and_dirs()
            if n_files > 0:
                self._logger.msg.emit("*** Searching for required input files ***")
                file_paths = self._flatten_file_path_duplicates(self._find_input_files(resources), log_duplicates=True)
                not_found = [k for k, v in file_paths.items() if v is None]
                if not_found:
                    self._logger.msg_error.emit(f"Required file(s) <b>{', '.join(not_found)}</b> not found")
                    return False
                # Required files and dirs should have been found at this point
                self._logger.msg.emit(f"*** Copying input files to {work_or_source} directory ***")
                # Copy input files to ToolInstance work or source directory
                if not self.copy_input_files(file_paths):
                    self._logger.msg_error.emit("Copying input files failed. Tool execution aborted.")
                    return False
            if n_dirs > 0:
                self._logger.msg.emit(f"*** Creating input subdirectories to {work_or_source} directory ***")
                if not self.create_input_dirs():
                    # Creating directories failed -> abort
                    self._logger.msg_error.emit("Creating input subdirectories failed. Tool execution aborted.")
                    return False
        optional_file_copy_paths = dict()
        # Check if there are any optional input files to copy
        if self.opt_input_file_model.rowCount() > 0:
            self._logger.msg.emit("*** Searching for optional input files ***")
            optional_file_paths = self._find_optional_input_files(resources)
            for k, v in optional_file_paths.items():
                self._logger.msg.emit(f"\tFound <b>{len(v)}</b> files matching pattern <b>{k}</b>")
            optional_file_copy_paths = self._optional_output_destination_paths(optional_file_paths)
            self._copy_optional_input_files(optional_file_copy_paths)
        if not self.create_output_dirs():
            self._logger.msg_error.emit("Creating output subdirectories failed. Tool execution aborted.")
            return False
        input_database_urls = self._database_urls(resources)
        output_database_urls = self._database_urls(self._downstream_resources)
        self.instance = self.tool_specification().create_tool_instance(self.basedir)

        try:
            self.instance.prepare(
                list(optional_file_copy_paths.values()), input_database_urls, output_database_urls, self.cmd_line_args
            )
        except RuntimeError as error:
            self._logger.msg_error.emit(f"Failed to prepare tool instance: {error}")
            return False
        self.instance.instance_finished.connect(self.handle_execution_finished)
        self._logger.msg.emit(
            f"*** Starting instance of Tool specification <b>{self.tool_specification().name}</b> ***"
        )
        # Wait for finished right here
        loop = QEventLoop()
        self.instance.instance_finished.connect(loop.quit)
        self.instance.execute()
        if self.instance.is_running():
            loop.exec_()
        return self.last_return_code == 0

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

    def _optional_output_destination_paths(self, paths):
        """
        Returns a dictionary telling where optional output files should be copied to before execution.

        Args:
            paths (dict): key is the optional file name pattern, value is a list of paths to source files
        Returns:
            dict: a map from source path to destination path
        """
        destination_paths = dict()
        for dst, src_paths in paths.items():
            for src_path in src_paths:
                if not os.path.exists(src_path):
                    self._logger.msg_error.emit(f"\tFile <b>{src_path}</b> does not exist")
                    continue
                # Get file name that matched the search pattern
                _, dst_fname = os.path.split(src_path)
                # Check if the search pattern included subdirectories (e.g. 'input/*.csv')
                # This means that /input/ directory should be created to work (or source) directory
                # before copying the files
                dst_subdir, _search_pattern = os.path.split(dst)
                if not dst_subdir:
                    # No subdirectories to create
                    self._logger.msg.emit(f"\tCopying optional file <b>{dst_fname}</b>")
                    dst_path = os.path.abspath(os.path.join(self.basedir, dst_fname))
                else:
                    # Create subdirectory structure to work or source directory
                    work_subdir_path = os.path.abspath(os.path.join(self.basedir, dst_subdir))
                    if not os.path.exists(work_subdir_path):
                        try:
                            create_dir(work_subdir_path)
                        except OSError:
                            self._logger.msg_error.emit(
                                f"[OSError] Creating directory <b>{work_subdir_path}</b> failed."
                            )
                            continue
                    self._logger.msg.emit(
                        f"\tCopying optional file <b>{dst_fname}</b> into subdirectory <b>{os.path.sep}{dst_subdir}</b>"
                    )
                    dst_path = os.path.abspath(os.path.join(work_subdir_path, dst_fname))
                destination_paths[src_path] = dst_path
        return destination_paths

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
                    self._logger.msg_error.emit(
                        f"[OSError] Creating directory {path_to_create} failed. Check permissions."
                    )
                    return False
                self._logger.msg.emit(f"\tDirectory <b>{os.path.sep}{path}</b> created")
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
                self._logger.msg_error.emit(f"\tFile <b>{src_path}</b> does not exist")
                return False
            # Join work directory path to dst (dst is the filename including possible subfolders, e.g. 'input/f.csv')
            dst_path = os.path.abspath(os.path.join(self.basedir, dst))
            # Create subdirectories if necessary
            dst_subdir, _ = os.path.split(dst)
            if not dst_subdir:
                # No subdirectories to create
                self._logger.msg.emit(f"\tCopying <b>{src_path}</b>")
            else:
                # Create subdirectory structure to work or source directory
                work_subdir_path = os.path.abspath(os.path.join(self.basedir, dst_subdir))
                if not os.path.exists(work_subdir_path):
                    try:
                        create_dir(work_subdir_path)
                    except OSError:
                        self._logger.msg_error.emit(f"[OSError] Creating directory <b>{work_subdir_path}</b> failed.")
                        return False
                self._logger.msg.emit(f"\tCopying <b>{src_path}</b> into subdirectory <b>{os.path.sep}{dst_subdir}</b>")
            try:
                shutil.copyfile(src_path, dst_path)
                n_copied_files += 1
            except OSError as e:
                self._logger.msg_error.emit(f"Copying file <b>{src_path}</b> to <b>{dst_path}</b> failed")
                self._logger.msg_error.emit(f"{e}")
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
                    self._logger.msg_warning.emit(msg)
                return False
        self._logger.msg.emit(f"\tCopied <b>{n_copied_files}</b> input file(s)")
        return True

    def _copy_optional_input_files(self, paths):
        """Copy optional input files from given paths to work or source directory, depending on
        where the Tool specification requires them to be.

        Args:
            paths (dict): key is the source path, value is the destination path
        """
        n_copied_files = 0
        for src_path, dst_path in paths.items():
            try:
                shutil.copyfile(src_path, dst_path)
                n_copied_files += 1
            except OSError as e:
                self._logger.msg_error.emit(f"Copying optional file <b>{src_path}</b> to <b>{dst_path}</b> failed")
                self._logger.msg_error.emit(f"{e}")
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
                    self._logger.msg_warning.emit(msg)
        self._logger.msg.emit(f"\tCopied <b>{n_copied_files}</b> optional input file(s)")

    def copy_program_files(self):
        """Copies Tool specification source files to base directory."""
        # Make work directory anchor with path as tooltip
        work_anchor = "<a style='color:#99CCFF;' title='{0}' href='file:///{0}'>work directory</a>".format(self.basedir)
        self._logger.msg.emit(
            f"*** Copying Tool specification <b>{self.tool_specification().name}</b> program files to {work_anchor} ***"
        )
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
                self._logger.msg_error.emit(f"Creating directory <b>{dst_dir}</b> failed")
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
                        self._logger.msg_error.emit(f"\tCopying file <b>{src_file}</b> to <b>{dst_file}</b> failed")
                        return False
        if n_copied_files == 0:
            self._logger.msg_warning.emit("Warning: No files copied")
        else:
            self._logger.msg.emit(f"\tCopied <b>{n_copied_files}</b> file(s)")
        return True

    def _find_input_files(self, resources):
        """Iterates files in required input files model and looks for them in the given resources.

        Args:
            resources (list): resources available

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
            file_paths[req_file_path] = self._find_file(filename, resources)
        return file_paths

    def _find_optional_input_files(self, resources):
        """Tries to find optional input files from previous project items in the DAG. Returns found paths.

        Args:
            resources (list): resources available

        Returns:
            Dictionary of optional input file paths or an empty dictionary if no files found. Key is the
            optional input item and value is a list of paths that matches the item.
        """
        file_paths = dict()
        file_paths_from_resources = self._filepaths_from_resources(resources)
        for i in range(self.opt_input_file_model.rowCount()):
            file_path = self.opt_input_file_model.item(i, 0).data(Qt.DisplayRole)
            # Just get the filename if there is a path attached to the file
            _, pattern = os.path.split(file_path)  # Filename may be a pattern (contains wildcards * or ?)
            if not pattern:
                # It's a directory -> skip
                continue
            found_files = self._find_optional_files(pattern, file_paths_from_resources)
            if not found_files:
                self._logger.msg_warning.emit(f"\tNo files matching pattern <b>{pattern}</b> found")
            else:
                file_paths[file_path] = found_files
        return file_paths

    @staticmethod
    def _filepaths_from_resources(resources):
        """Returns file paths from given resources.

        Args:
            resources (list): resources available

        Returns:
            a list of file paths, possibly including patterns
        """
        filepaths = []
        for resource in resources:
            if resource.type_ == "file" or (resource.type_ == "database" and resource.scheme == "sqlite"):
                filepaths += glob.glob(resource.path)
        return filepaths

    def _find_file(self, filename, resources):
        """Returns all occurrences of full paths to given file name in resources available.

        Args:
            filename (str): Searched file name (no path)
            resources (list): list of resources available from upstream items

        Returns:
            list: Full paths to file if found, None if not found
        """
        found_file_paths = list()
        for filepath in self._filepaths_from_resources(resources):
            _, file_candidate = os.path.split(filepath)
            if file_candidate == filename:
                found_file_paths.append(filepath)
        return found_file_paths if found_file_paths else None

    @staticmethod
    def _find_optional_files(pattern, available_file_paths):
        """Returns a list of found paths to files that match the given pattern in files available
        from the execution instance.

        Args:
            pattern (str): file pattern
            available_file_paths (list): list of available file paths from upstream items
        Returns:
            list: List of (full) paths
        """
        extended_pattern = os.path.join("*", pattern)  # Match all absolute paths.
        return fnmatch.filter(available_file_paths, extended_pattern)

    @Slot(int)
    def handle_execution_finished(self, return_code):
        """Handles Tool specification execution finished.

        Args:
            return_code (int): Process exit code
        """
        self.last_return_code = return_code
        # Disconnect instance finished signal
        self.instance.instance_finished.disconnect(self.handle_execution_finished)
        if return_code == 0:
            self._logger.msg_success.emit(f"Tool <b>{self.name}</b> execution finished")
        else:
            self._logger.msg_error.emit(f"Tool <b>{self.name}</b> execution failed")
        self.handle_output_files(return_code)

    def handle_output_files(self, ret):
        """Copies Tool specification output files from work directory to result directory.

        Args:
            ret (int): Tool specification process return value
        """
        output_dir_timestamp = create_output_dir_timestamp()  # Get timestamp when tool finished
        # Create an output folder with timestamp and copy output directly there
        if ret != 0:
            result_path = os.path.abspath(os.path.join(self.output_dir, 'failed', output_dir_timestamp))
        else:
            result_path = os.path.abspath(os.path.join(self.output_dir, output_dir_timestamp))
        try:
            create_dir(result_path)
        except OSError:
            self._logger.msg_error.emit(
                "\tError creating timestamped output directory. "
                "Tool specification output files not copied. Please check directory permissions."
            )
            return
        # Make link to output folder
        result_anchor = (
            f"<a style='color:#BB99FF;' title='{result_path}'" f"href='file:///{result_path}'>results directory</a>"
        )
        self._logger.msg.emit(f"*** Archiving output files to {result_anchor} ***")
        if self.output_file_model.rowCount() > 0:
            saved_files, failed_files = self.copy_output_files(result_path)
            if not saved_files:
                # If no files were saved
                self._logger.msg_error.emit("\tNo files saved")
            else:
                # If there are saved files
                # Split list into filenames and their paths
                filenames, _ = zip(*saved_files)
                self._logger.msg.emit("\tThe following output files were saved to results directory")
                for filename in filenames:
                    self._logger.msg.emit(f"\t\t<b>{filename}</b>")
            if failed_files:
                # If saving some or all files failed
                self._logger.msg_warning.emit("\tThe following output files were not found")
                for failed_file in failed_files:
                    failed_fname = os.path.split(failed_file)[1]
                    self._logger.msg_warning.emit(f"\t\t<b>{failed_fname}</b>")
        else:
            tip_anchor = (
                "<a style='color:#99CCFF;' title='When you add output files to the Tool specification,\n "
                "they will be archived into results directory. Also, output files are passed to\n "
                "subsequent project items.' href='#'>Tip</a>"
            )
            self._logger.msg_warning.emit(f"\tNo output files defined for this Tool specification. {tip_anchor}")

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
                self._logger.msg_error.emit(f"Creating work output directory '{dst_dir}' failed")
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
        for i in range(self.output_file_model.rowCount()):
            pattern = self.output_file_model.item(i, 0).data(Qt.DisplayRole)
            # Create subdirectories if necessary
            dst_subdir, fname_pattern = os.path.split(pattern)
            target = os.path.abspath(os.path.join(target_dir, dst_subdir))
            if not os.path.exists(target):
                try:
                    create_dir(target)
                except OSError:
                    self._logger.msg_error.emit(f"[OSError] Creating directory <b>{target}</b> failed.")
                    continue
                self._logger.msg.emit(f"\tCreated result subdirectory <b>{os.path.sep}{dst_subdir}</b>")
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
                        self._logger.msg_error.emit(f"[OSError] Copying pattern {fname_path} to {dst} failed")
                        failed_files.append(full_fname)
            else:
                output_file = os.path.abspath(os.path.join(self.basedir, pattern))
                if not os.path.isfile(output_file):
                    failed_files.append(pattern)
                    continue
                dst = os.path.abspath(os.path.join(target, fname_pattern))
                try:
                    shutil.copyfile(output_file, dst)
                    saved_files.append((pattern, dst))
                except OSError:
                    self._logger.msg_error.emit(f"[OSError] Copying output file {output_file} to {dst} failed")
                    failed_files.append(pattern)
        return saved_files, failed_files

    def stop_execution(self):
        """Stops executing this Tool."""
        super().stop_execution()
        if self.instance and self.instance.is_running():
            self.get_icon().stop_animation()
            self.instance.terminate_instance()

    def _do_handle_dag_changed(self, resources):
        """See base class."""
        if not self.tool_specification():
            self.add_notification(
                "This Tool is not connected to a Tool specification. Set it in the Tool Properties Panel."
            )
            return
        file_paths = self._find_input_files(resources)
        duplicates = self._file_path_duplicates(file_paths)
        self._notify_if_duplicate_file_paths(duplicates)
        file_paths = self._flatten_file_path_duplicates(file_paths)
        not_found = [k for k, v in file_paths.items() if v is None]
        if not_found:
            self.add_notification(
                "File(s) {0} needed to execute this Tool are not provided by any input item. "
                "Connect items that provide the required files to this Tool.".format(", ".join(not_found))
            )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        if not self.tool_specification():
            d["tool"] = ""
        else:
            d["tool"] = self.tool_specification().name
        d["execute_in_work"] = self.execute_in_work
        d["cmd_line_args"] = ToolSpecification.split_cmdline_args(" ".join(self.cmd_line_args))
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
                self._logger.msg.emit(f"Tool <b>{self.name}</b> is not running")
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
        if not super().rename(new_name):
            return False
        self.output_dir = os.path.join(self.data_dir, TOOL_OUTPUT_DIR)
        if self.output_files_watcher.files():
            self.output_files_watcher.removePaths(self.output_files_watcher.files())
        self.item_changed.emit()
        return True

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type() == "Data Store":
            self._logger.msg.emit(
                f"Link established. Data Store <b>{source_item.name}</b> url will "
                f"be passed to Tool <b>{self.name}</b> when executing."
            )
        elif source_item.item_type() == "Data Connection":
            self._logger.msg.emit(
                f"Link established. Tool <b>{self.name}</b> will look for input "
                f"files from <b>{source_item.name}</b>'s references and data directory."
            )
        elif source_item.item_type() == "Exporter":
            self._logger.msg.emit(
                f"Link established. The file exported by <b>{source_item.name}</b> will "
                f"be passed to Tool <b>{self.name}</b> when executing."
            )
        elif source_item.item_type() == "Tool":
            self._logger.msg.emit("Link established.")
        else:
            super().notify_destination(source_item)

    @staticmethod
    def default_name_prefix():
        """see base class"""
        return "Tool"

    @staticmethod
    def _file_path_duplicates(file_paths):
        """Returns a list of lists of duplicate items in file_paths."""
        duplicates = list()
        for paths in file_paths.values():
            if paths is not None and len(paths) > 1:
                duplicates.append(paths)
        return duplicates

    def _notify_if_duplicate_file_paths(self, duplicates):
        """Adds a notification if duplicates contains items."""
        if not duplicates:
            return
        for duplicate in duplicates:
            self.add_notification("Duplicate input files from upstream items:<br>{}".format("<br>".join(duplicate)))

    def _flatten_file_path_duplicates(self, file_paths, log_duplicates=False):
        """Flattens the extra duplicate dimension in file_paths."""
        flattened = dict()
        for required_file, paths in file_paths.items():
            if paths is not None:
                pick = paths[0]
                if len(paths) > 1 and log_duplicates:
                    self._logger.msg_warning.emit(f"Multiple input files satisfy {required_file}; using {pick}")
                flattened[required_file] = pick
            else:
                flattened[required_file] = None
        return flattened

    @staticmethod
    def _database_urls(resources):
        """
        Pries database URLs and their providers' names from resources.

        Args:
            resources (list): a list of ProjectItemResource objects
        Returns:
            dict: a mapping from resource provider's name to a database URL.
        """
        urls = dict()
        for resource in resources:
            if resource.type_ == "database":
                urls[resource.provider.name] = resource.url
        return urls
