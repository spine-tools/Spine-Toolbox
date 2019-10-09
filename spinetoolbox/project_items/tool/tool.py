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

import logging
import os
import shutil
import sys
from PySide2.QtCore import Slot, Qt, QUrl, QFileInfo, QTimeLine
from PySide2.QtGui import QDesktopServices, QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QFileIconProvider
from spinetoolbox.project_item import ProjectItem
from spinetoolbox.tool_instance import ToolInstance
from spinetoolbox.config import TOOL_OUTPUT_DIR, GAMS_EXECUTABLE, JULIA_EXECUTABLE, PYTHON_EXECUTABLE
from spinetoolbox.widgets.custom_menus import ToolSpecificationOptionsPopupmenu
from spinetoolbox.project_items.tool.widgets.custom_menus import ToolContextMenu
from spinetoolbox.helpers import create_dir


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
        self._tool_specification = self._toolbox.tool_specification_model.find_tool_specification(tool)
        if tool != "" and not self._tool_specification:
            # Clarifications for user
            self._toolbox.msg_error.emit("Tool <b>{0}</b> should have a Tool "
                                         "specification <b>{1}</b> but it was not found"
                                         .format(self.name, tool))
        self.set_tool_specification(self._tool_specification)
        if not self._tool_specification:
            self._tool_specification_name = ""
        else:
            self._tool_specification_name = self.tool_specification().name
        self.tool_specification_options_popup_menu = None
        self.instance = None  # Instance of this Tool that can be sent to a subprocess for processing
        self.extra_cmdline_args = ''  # This may be used for additional Tool specific command line arguments
        self.execute_in_work = execute_in_work  # Enables overriding the specification default setting
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
            tool_specification = self._toolbox.tool_specification_model.find_tool_specification(self._tool_specification_name)
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

    def update_instance(self):
        """Initialize and update instance so that it is ready for processing. This is where Tool
        type specific initialization happens (whether the tool is GAMS, Python or Julia script)."""
        if self.tool_specification().tooltype == "gams":
            gams_path = self._toolbox.qsettings().value("appSettings/gamsPath", defaultValue="")
            if not gams_path == '':
                gams_exe = gams_path
            else:
                gams_exe = GAMS_EXECUTABLE
            self.instance.program = gams_exe
            self.instance.args.append(self.tool_specification().main_prgm)
            self.instance.args.append("curDir=")
            self.instance.args.append("{0}".format(self.instance.basedir))
            self.instance.args.append("logoption=3")  # TODO: This should be an option in Settings
            self.append_instance_args()  # Append Tool specific cmd line args into args list
        elif self.tool_specification().tooltype == "julia":
            # Prepare command "julia --project={PROJECT_DIR} script.jl"
            # Do this regardless of the `useEmbeddedJulia` setting since we may need to fallback
            # to `julia --project={PROJECT_DIR} script.jl`
            julia_path = self._toolbox.qsettings().value("appSettings/juliaPath", defaultValue="")
            if julia_path != "":
                julia_exe = julia_path
            else:
                julia_exe = JULIA_EXECUTABLE
            julia_project_path = self._toolbox.qsettings().value("appSettings/juliaProjectPath", defaultValue="")
            if julia_project_path == "":
                julia_project_path = "@."
            work_dir = self.instance.basedir
            script_path = os.path.join(work_dir, self.tool_specification().main_prgm)
            self.instance.program = julia_exe
            self.instance.args.append(f"--project={julia_project_path}")
            self.instance.args.append(script_path)
            self.append_instance_args()
            use_embedded_julia = self._toolbox.qsettings().value("appSettings/useEmbeddedJulia", defaultValue="2")
            if use_embedded_julia == "2":
                # Prepare Julia REPL command
                # TODO: See if this can be simplified
                mod_work_dir = work_dir.__repr__().strip("'")
                args = r'["' + r'", "'.join(self.get_instance_args()) + r'"]'
                self.instance.julia_repl_command = (
                    r'cd("{}");'
                    r'empty!(ARGS);'
                    r'append!(ARGS, {});'
                    r'include("{}")'.format(mod_work_dir, args, self.tool_specification().main_prgm)
                )
        elif self.tool_specification().tooltype == "python":
            # Prepare command "python script.py"
            python_path = self._toolbox.qsettings().value("appSettings/pythonPath", defaultValue="")
            if not python_path == "":
                python_cmd = python_path
            else:
                python_cmd = PYTHON_EXECUTABLE
            work_dir = self.instance.basedir
            script_path = os.path.join(work_dir, self.tool_specification().main_prgm)
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
                run_script_cmd = "%run \"{0}\" {1}".format(self.tool_specification().main_prgm, args)
                # Populate FIFO command queue
                self.instance.ipython_command_list.append(cd_work_dir_cmd)
                self.instance.ipython_command_list.append(run_script_cmd)
        elif self.tool_specification().tooltype == "executable":
            batch_path = os.path.join(self.instance.basedir, self.tool_specification().main_prgm)
            if sys.platform != "win32":
                self.instance.program = "sh"
                self.instance.args.append(batch_path)
            else:
                self.instance.program = batch_path
            self.append_instance_args()  # Append Tool specific cmd line args into args list

    def append_instance_args(self):
        """Append Tool specification command line args into instance args list."""
        self.instance.args += self.get_instance_args()

    def get_instance_args(self):
        """Return instance args as list."""
        # TODO: Deal with cmdline arguments that have spaces. They should be stored in a list in the definition file
        if (self.tool_specification().cmdline_args is not None) and (self.tool_specification().cmdline_args != ''):
            # Tool specification cmdline args is a space delimited string. Return them as a list.
            return self.tool_specification().cmdline_args.split(" ")
        return []

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

    def execute(self):
        """Executes this Tool."""
        if not self.tool_specification():
            self._toolbox.msg_warning.emit("Tool <b>{0}</b> has no Tool specification to execute".format(self.name))
            self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(0)  # continue
            return
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Tool <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        exec_inst = self._toolbox.project().execution_instance
        work_or_source = "work" if self.execute_in_work else "source"
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
                    self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-1)  # abort
                    return
                # Required files and dirs should have been found at this point, so create instance
                try:
                    self.instance = ToolInstance(self)
                except OSError as e:
                    self._toolbox.msg_error.emit("Creating Tool instance failed. {0}".format(e))
                    self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-1)  # abort
                    return
                self._toolbox.msg.emit("*** Copying input files to {0} directory ***".format(work_or_source))
                # Copy input files to ToolInstance work or source directory
                if not self.copy_input_files(file_paths):
                    self._toolbox.msg_error.emit("Copying input files failed. Tool execution aborted.")
                    self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-1)  # abort
                    return
            else:  # just for testing
                # logging.debug("No input files to copy")
                pass
            if n_dirs > 0:
                self._toolbox.msg.emit("*** Creating subdirectories to {0} directory ***".format(work_or_source))
                if not self.create_subdirectories():
                    # Creating directories failed -> abort
                    self._toolbox.msg_error.emit("Creating subdirectories failed. Tool execution aborted.")
                    self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-1)  # abort
                    return
            else:  # just for testing
                # logging.debug("No directories to create")
                pass
        else:  # Tool specification does not have requirements
            try:
                self.instance = ToolInstance(self)
            except OSError as e:
                self._toolbox.msg_error.emit("Tool instance creation failed. {0}".format(e))
                self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-1)  # abort
                return
        # Check if there are any optional input files to copy
        if self.opt_input_file_model.rowCount() > 0:
            self._toolbox.msg.emit("*** Searching for optional input files ***")
            optional_file_paths = self.find_optional_input_files(exec_inst)
            for k, v in optional_file_paths.items():
                self._toolbox.msg.emit("\tFound <b>{0}</b> files matching pattern <b>{1}</b>".format(len(v), k))
            if not self.copy_optional_input_files(optional_file_paths):
                self._toolbox.msg_warning.emit("Copying optional input files failed")
        self.get_icon().start_animation()
        self.update_instance()  # Make command and stuff
        self.instance.instance_finished_signal.connect(self.execute_finished)
        self.instance.execute()

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
            file_paths[req_file_path] = exec_inst.find_file(filename, self.name)
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
            found_files = exec_inst.find_optional_files(pattern, self.name)
            if not found_files:
                self._toolbox.msg_warning.emit("\tNo files matching pattern <b>{0}</b> found".format(pattern))
            else:
                file_paths[file_path] = found_files
        return file_paths

    @Slot(int, name="execute_finished")
    def execute_finished(self, return_code):
        """Tool specification execution finished.

        Args:
            return_code (int): Process exit code
        """
        self.get_icon().stop_animation()
        # Disconnect instance finished signal
        self.instance.instance_finished_signal.disconnect(self.execute_finished)
        if return_code == 0:
            self._toolbox.msg_success.emit("Tool <b>{0}</b> execution finished".format(self.name))
        else:
            self._toolbox.msg_error.emit("Tool <b>{0}</b> execution failed".format(self.name))
        if not self._toolbox.project().execution_instance:
            # Happens sometimes when Stop button is pressed
            return
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(0)

    def stop_execution(self):
        """Stops executing this Tool."""
        self.get_icon().stop_animation()
        self.instance.instance_finished_signal.disconnect(self.execute_finished)
        self._toolbox.msg_warning.emit("Stopping Tool <b>{0}</b>".format(self.name))
        self.instance.terminate_instance()
        # Note: QSubProcess, PythonReplWidget, and JuliaREPLWidget emit project_item_execution_finished_signal

    def simulate_execution(self, inst):
        """Simulates executing this Tool."""
        super().simulate_execution(inst)
        if not self.tool_specification():
            self.add_notification("This Tool is not connected to a Tool specification. Set it in the Tool Properties Panel.")
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
            out_file_path = self.output_file_model.item(i, 0).data(Qt.DisplayRole)
            inst.append_tool_output_file(self.name, out_file_path)

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

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type == "Data Store":
            self._toolbox.msg.emit(
                "Link established. Data Store <b>{0}</b> reference will "
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
