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
import os
import pathlib
from PySide2.QtCore import Slot, Qt, QUrl, QFileInfo, QTimeLine
from PySide2.QtGui import QDesktopServices, QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QFileIconProvider
from spinetoolbox.project_item import ProjectItem, ProjectItemResource
from spinetoolbox.config import TOOL_OUTPUT_DIR
from spinetoolbox.project_commands import UpdateToolExecuteInWorkCommand, UpdateToolCmdLineArgsCommand
from .tool_specifications import ToolSpecification  # , open_main_program_file
from .widgets.custom_menus import ToolContextMenu, ToolSpecificationMenu
from .tool_executable import ToolExecutable
from .utils import flatten_file_path_duplicates, find_file, find_last_output_files, is_pattern


class Tool(ProjectItem):
    def __init__(
        self, toolbox, project, logger, name, description, x, y, tool="", execute_in_work=True, cmd_line_args=None
    ):
        """Tool class.

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            project (SpineToolboxProject): the project this item belongs to
            logger (LoggerInterface): a logger instance
            name (str): Object name
            description (str): Object description
            x (float): Initial X coordinate of item icon
            y (float): Initial Y coordinate of item icon
            tool (str): Name of this Tool's Tool specification
            execute_in_work (bool): Execute associated Tool specification in work (True) or source directory (False)
            cmd_line_args (list): Tool command line arguments
        """
        super().__init__(name, description, x, y, project, logger)
        self._toolbox = toolbox
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
        self.execute_in_work = None
        self.undo_execute_in_work = None
        self.source_files = list()
        self.cmd_line_args = list() if not cmd_line_args else cmd_line_args
        self._specification = self._toolbox.specification_model.find_specification(tool)
        if tool and not self._specification:
            self._logger.msg_error.emit(
                f"Tool <b>{self.name}</b> should have a Tool specification <b>{tool}</b> but it was not found"
            )
        self.do_set_specification(self._specification)
        self.do_update_execution_mode(execute_in_work)
        self.specification_options_popup_menu = None
        # Make directory for results
        self.output_dir = os.path.join(self.data_dir, TOOL_OUTPUT_DIR)

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
        s[self._properties_ui.comboBox_tool.currentTextChanged] = self.update_specification
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

    @Slot(str)
    def update_specification(self, text):
        """Update Tool specification according to selection in the specification comboBox.

        Args:
            row (int): Selected row in the comboBox
        """
        spec = self._toolbox.specification_model.find_specification(text)
        if spec is None:
            self.set_specification(None)
        else:
            self.set_specification(spec)

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

    def do_set_specification(self, specification):
        """Sets Tool specification for this Tool. Removes Tool specification if None given as argument.

        Args:
            specification (ToolSpecification): Tool specification of this Tool. None removes the specification.
        """
        super().do_set_specification(specification)
        self.update_tool_models()
        self.update_tool_ui()
        if self.undo_execute_in_work is None:
            self.undo_execute_in_work = self.execute_in_work
        if specification:
            self.do_update_execution_mode(specification.execute_in_work)
        self.item_changed.emit()

    def undo_set_specification(self):
        super().undo_set_specification()
        self.do_update_execution_mode(self.undo_execute_in_work)
        self.undo_execute_in_work = None

    def update_tool_ui(self):
        """Updates Tool UI to show Tool specification details. Used when Tool specification is changed.
        Overrides execution mode (work or source) with the specification default."""
        if not self._active:
            return
        if not self._properties_ui:
            # This happens when calling self.set_specification() in the __init__ method,
            # because the UI only becomes available *after* adding the item to the project_item_model... problem??
            return
        if not self.specification():
            self._properties_ui.comboBox_tool.setCurrentIndex(-1)
            self._properties_ui.lineEdit_tool_spec_args.setText("")
            self.do_update_execution_mode(True)
            spec_model_index = None
        else:
            self._properties_ui.comboBox_tool.setCurrentText(self.specification().name)
            self._properties_ui.lineEdit_tool_spec_args.setText(" ".join(self.specification().cmdline_args))
            spec_model_index = self._toolbox.specification_model.specification_index(self.specification().name)
        self.specification_options_popup_menu = ToolSpecificationMenu(self._toolbox, spec_model_index)
        self._properties_ui.toolButton_tool_specification.setMenu(self.specification_options_popup_menu)
        self._properties_ui.treeView_specification.expandAll()
        self._properties_ui.lineEdit_tool_args.setText(" ".join(self.cmd_line_args))

    def update_tool_models(self):
        """Update Tool models with Tool specification details. Used when Tool specification is changed.
        Overrides execution mode (work or source) with the specification default."""
        if not self.specification():
            self.populate_source_file_model(None)
            self.populate_input_file_model(None)
            self.populate_opt_input_file_model(None)
            self.populate_output_file_model(None)
            self.populate_specification_model(populate=False)
        else:
            self.populate_source_file_model(self.specification().includes)
            self.populate_input_file_model(self.specification().inputfiles)
            self.populate_opt_input_file_model(self.specification().inputfiles_opt)
            self.populate_output_file_model(self.specification().outputfiles)
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
    def edit_specification(self):
        """Open Tool specification editor for the Tool specification attached to this Tool."""
        index = self._toolbox.specification_model.specification_index(self.specification().name)
        self._toolbox.edit_specification(index)

    @Slot()
    def open_specification_file(self):
        """Open Tool specification file."""
        index = self._toolbox.specification_model.specification_index(self.specification().name)
        self._toolbox.open_specification_file(index)

    @Slot()
    def open_main_program_file(self):
        """Open Tool specification main program file in an external text edit application."""
        if not self.specification():
            return
        open_main_program_file(self.specification(), self._toolbox)

    @Slot()
    def open_main_directory(self):
        """Open directory where the Tool specification main program is located in file explorer."""
        if not self.specification():
            return
        dir_url = "file:///" + self.specification().path
        self._toolbox.open_anchor(QUrl(dir_url, QUrl.TolerantMode))

    def specification(self):
        """Returns Tool specification."""
        return self._specification

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

    def resources_for_direct_successors(self):
        """
        Returns a list of resources, i.e. the outputs defined by the tool specification.

        The output files are available only after tool has been executed,
        therefore the resource type is 'transient_file' or 'file_pattern'.
        A 'file_pattern' type resource is returned only if the pattern doesn't match any output file.
        For 'transient_file' resources, the url attribute is set to an empty string if the file doesn't exist yet
        or it points to a file from most recent execution.
        The metadata attribute's label key gives the base name or file pattern of the output file.

        Returns:
            list: a list of Tool's output resources
        """
        if self.specification() is None:
            self._logger.msg_error.emit("Tool specification missing.")
            return []
        resources = list()
        last_output_files = find_last_output_files(self._specification.outputfiles, self.output_dir)
        for i in range(self.output_file_model.rowCount()):
            out_file_label = self.output_file_model.item(i, 0).data(Qt.DisplayRole)
            latest_files = last_output_files.get(out_file_label, list())
            if is_pattern(out_file_label):
                if not latest_files:
                    metadata = {"label": out_file_label}
                    resource = ProjectItemResource(self, "file_pattern", metadata=metadata)
                    resources.append(resource)
                else:
                    for out_file in latest_files:
                        file_url = pathlib.Path(out_file.path).as_uri()
                        metadata = {"label": out_file.label}
                        resource = ProjectItemResource(self, "transient_file", url=file_url, metadata=metadata)
                        resources.append(resource)
            else:
                if not latest_files:
                    metadata = {"label": out_file_label}
                    resource = ProjectItemResource(self, "transient_file", metadata=metadata)
                    resources.append(resource)
                else:
                    latest_file = latest_files[0]  # Not a pattern; there should be only one element in the list.
                    file_url = pathlib.Path(latest_file.path).as_uri()
                    metadata = {"label": latest_file.label}
                    resource = ProjectItemResource(self, "transient_file", url=file_url, metadata=metadata)
                    resources.append(resource)
        return resources

    def execution_item(self):
        """Creates project item's execution counterpart."""
        work_dir = self._toolbox.work_dir if self.execute_in_work else None
        return ToolExecutable(
            self.name, work_dir, self.output_dir, self._specification, self.cmd_line_args, self._logger
        )

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
            file_paths[req_file_path] = find_file(filename, resources)
        return file_paths

    def _do_handle_dag_changed(self, resources):
        """See base class."""
        if not self.specification():
            self.add_notification(
                "This Tool is not connected to a Tool specification. Set it in the Tool Properties Panel."
            )
            return
        file_paths = self._find_input_files(resources)
        duplicates = self._file_path_duplicates(file_paths)
        self._notify_if_duplicate_file_paths(duplicates)
        file_paths = flatten_file_path_duplicates(file_paths, self._logger)
        not_found = [k for k, v in file_paths.items() if v is None]
        if not_found:
            self.add_notification(
                "File(s) {0} needed to execute this Tool are not provided by any input item. "
                "Connect items that provide the required files to this Tool.".format(", ".join(not_found))
            )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        if not self.specification():
            d["tool"] = ""
        else:
            d["tool"] = self.specification().name
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
            self.edit_specification()
        elif action == "Edit main program file...":
            self.open_main_program_file()

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
