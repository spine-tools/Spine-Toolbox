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
QWidget that is used to create or edit Tool specifications.
In the former case it is presented empty, but in the latter it
is filled with all the information from the specification being edited.

:author: M. Marin (KTH), P. Savolainen (VTT)
:date:   12.4.2018
"""

import os
import json
from PySide2.QtGui import QDesktopServices, QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QWidget, QStatusBar, QInputDialog, QFileDialog, QFileIconProvider, QMessageBox, QMenu
from PySide2.QtCore import Slot, Qt, QUrl, QFileInfo
from ..config import STATUSBAR_SS, TREEVIEW_HEADER_SS, APPLICATION_PATH, TOOL_TYPES, REQUIRED_KEYS
from ..helpers import busy_effect
from ..tool_specifications import CmdlineTag, CMDLINE_TAG_EDGE, ToolSpecification
from .custom_menus import AddIncludesPopupMenu, CreateMainProgramPopupMenu


class ToolSpecificationWidget(QWidget):
    def __init__(self, toolbox, tool_specification=None):
        """A widget to query user's preferences for a new tool specification.

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            tool_specification (ToolSpecification): If given, the form is pre-filled with this specification
        """
        from ..ui.tool_specification_form import Ui_Form

        super().__init__(parent=toolbox, f=Qt.Window)  # Inherit stylesheet from ToolboxUI
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        # init models
        self.sourcefiles_model = QStandardItemModel()
        self.inputfiles_model = QStandardItemModel()
        self.inputfiles_opt_model = QStandardItemModel()
        self.outputfiles_model = QStandardItemModel()
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # init ui
        self.ui.treeView_sourcefiles.setModel(self.sourcefiles_model)
        self.ui.treeView_inputfiles.setModel(self.inputfiles_model)
        self.ui.treeView_inputfiles_opt.setModel(self.inputfiles_opt_model)
        self.ui.treeView_outputfiles.setModel(self.outputfiles_model)
        self.ui.treeView_sourcefiles.setStyleSheet(TREEVIEW_HEADER_SS)
        self.ui.treeView_inputfiles.setStyleSheet(TREEVIEW_HEADER_SS)
        self.ui.treeView_inputfiles_opt.setStyleSheet(TREEVIEW_HEADER_SS)
        self.ui.treeView_outputfiles.setStyleSheet(TREEVIEW_HEADER_SS)
        self.ui.comboBox_tooltype.addItem("Select type...")
        self.ui.comboBox_tooltype.addItems(TOOL_TYPES)
        # if a specification is given, fill the form with data from it
        if tool_specification:
            self.ui.lineEdit_name.setText(tool_specification.name)
            check_state = Qt.Checked if tool_specification.execute_in_work else Qt.Unchecked
            self.ui.checkBox_execute_in_work.setCheckState(check_state)
            self.ui.textEdit_description.setPlainText(tool_specification.description)
            self.ui.lineEdit_args.setText(" ".join(tool_specification.cmdline_args))
            tool_types = [x.lower() for x in TOOL_TYPES]
            index = tool_types.index(tool_specification.tooltype) + 1
            self.ui.comboBox_tooltype.setCurrentIndex(index)
        # Init lists
        self.main_program_file = ""
        self.sourcefiles = list(tool_specification.includes) if tool_specification else list()
        self.inputfiles = list(tool_specification.inputfiles) if tool_specification else list()
        self.inputfiles_opt = list(tool_specification.inputfiles_opt) if tool_specification else list()
        self.outputfiles = list(tool_specification.outputfiles) if tool_specification else list()
        self.def_file_path = tool_specification.def_file_path if tool_specification else None
        self.program_path = tool_specification.path if tool_specification else None
        self.definition = dict()
        # Get first item from sourcefiles list as the main program file
        try:
            self.main_program_file = self.sourcefiles.pop(0)
            self.ui.lineEdit_main_program.setText(os.path.join(self.program_path, self.main_program_file))
        except IndexError:
            pass  # sourcefiles list is empty
        # Populate lists (this will also create headers)
        self.populate_sourcefile_list(self.sourcefiles)
        self.populate_inputfiles_list(self.inputfiles)
        self.populate_inputfiles_opt_list(self.inputfiles_opt)
        self.populate_outputfiles_list(self.outputfiles)
        self.ui.lineEdit_name.setFocus()
        self.ui.label_mainpath.setText(self.program_path)
        # Add includes popup menu
        self.add_source_files_popup_menu = AddIncludesPopupMenu(self)
        self.ui.toolButton_add_source_files.setMenu(self.add_source_files_popup_menu)
        self.ui.toolButton_add_source_files.setStyleSheet('QToolButton::menu-indicator { image: none; }')
        # Add create new or add existing main program popup menu
        self.add_main_prgm_popup_menu = CreateMainProgramPopupMenu(self)
        self.ui.toolButton_add_main_program.setMenu(self.add_main_prgm_popup_menu)
        self.ui.toolButton_add_source_files.setStyleSheet('QToolButton::menu-indicator { image: none; }')
        self.ui.toolButton_add_cmdline_tag.setMenu(self._make_add_cmdline_tag_menu())
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.toolButton_add_source_files.clicked.connect(self.show_add_source_files_dialog)
        self.ui.toolButton_add_source_dirs.clicked.connect(self.show_add_source_dirs_dialog)
        self.ui.lineEdit_main_program.file_dropped.connect(self.set_main_program_path)
        self.ui.treeView_sourcefiles.files_dropped.connect(self.add_dropped_includes)
        self.ui.treeView_sourcefiles.doubleClicked.connect(self.open_includes_file)
        self.ui.toolButton_minus_source_files.clicked.connect(self.remove_source_files)
        self.ui.toolButton_plus_inputfiles.clicked.connect(self.add_inputfiles)
        self.ui.toolButton_minus_inputfiles.clicked.connect(self.remove_inputfiles)
        self.ui.toolButton_plus_inputfiles_opt.clicked.connect(self.add_inputfiles_opt)
        self.ui.toolButton_minus_inputfiles_opt.clicked.connect(self.remove_inputfiles_opt)
        self.ui.toolButton_plus_outputfiles.clicked.connect(self.add_outputfiles)
        self.ui.toolButton_minus_outputfiles.clicked.connect(self.remove_outputfiles)
        self.ui.pushButton_ok.clicked.connect(self.handle_ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)
        # Enable removing items from QTreeViews by pressing the Delete key
        self.ui.treeView_sourcefiles.del_key_pressed.connect(self.remove_source_files_with_del)
        self.ui.treeView_inputfiles.del_key_pressed.connect(self.remove_inputfiles_with_del)
        self.ui.treeView_inputfiles_opt.del_key_pressed.connect(self.remove_inputfiles_opt_with_del)
        self.ui.treeView_outputfiles.del_key_pressed.connect(self.remove_outputfiles_with_del)

    def populate_sourcefile_list(self, items):
        """List source files in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.sourcefiles_model.clear()
        self.sourcefiles_model.setHorizontalHeaderItem(0, QStandardItem("Additional source files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.sourcefiles_model.appendRow(qitem)

    def populate_inputfiles_list(self, items):
        """List input files in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.inputfiles_model.clear()
        self.inputfiles_model.setHorizontalHeaderItem(0, QStandardItem("Input files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.inputfiles_model.appendRow(qitem)

    def populate_inputfiles_opt_list(self, items):
        """List optional input files in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.inputfiles_opt_model.clear()
        self.inputfiles_opt_model.setHorizontalHeaderItem(0, QStandardItem("Optional input files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.inputfiles_opt_model.appendRow(qitem)

    def populate_outputfiles_list(self, items):
        """List output files in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.outputfiles_model.clear()
        self.outputfiles_model.setHorizontalHeaderItem(0, QStandardItem("Output files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.outputfiles_model.appendRow(qitem)

    @Slot(bool, name="browse_main_program")
    def browse_main_program(self, checked=False):
        """Open file browser where user can select the path of the main program file."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self, "Add existing main program file", APPLICATION_PATH, "*.*")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self.set_main_program_path(file_path)

    @Slot("QString", name="set_main_program_path")
    def set_main_program_path(self, file_path):
        """Set main program file and folder path."""
        folder_path = os.path.split(file_path)[0]
        self.program_path = os.path.abspath(folder_path)
        # Update UI
        self.ui.lineEdit_main_program.setText(file_path)
        self.ui.label_mainpath.setText(self.program_path)

    @Slot()
    def new_main_program_file(self):
        """Creates a new blank main program file. Let's user decide the file name and path.
         Alternative version using only one getSaveFileName dialog.
         """
        # noinspection PyCallByClass
        answer = QFileDialog.getSaveFileName(self, "Create new main program", APPLICATION_PATH)
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        # Remove file if it exists. getSaveFileName has asked confirmation for us.
        try:
            os.remove(file_path)
        except OSError:
            pass
        try:
            with open(file_path, "w"):
                pass
        except OSError:
            msg = "Please check directory permissions."
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self, "Creating file failed", msg)
            return
        main_dir = os.path.dirname(file_path)
        self.program_path = os.path.abspath(main_dir)
        # Update UI
        self.ui.lineEdit_main_program.setText(file_path)
        self.ui.label_mainpath.setText(self.program_path)

    @Slot(name="new_source_file")
    def new_source_file(self):
        """Let user create a new source file for this tool specification."""
        path = self.program_path if self.program_path else APPLICATION_PATH
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        dir_path = QFileDialog.getSaveFileName(self, "Create source file", path, "*.*")
        file_path = dir_path[0]
        if file_path == '':  # Cancel button clicked
            return
        # create file. NOTE: getSaveFileName does the 'check for existence' for us
        open(file_path, 'w').close()
        self.add_single_include(file_path)

    @Slot(bool, name="show_add_source_files_dialog")
    def show_add_source_files_dialog(self, checked=False):
        """Let user select source files for this tool specification."""
        path = self.program_path if self.program_path else APPLICATION_PATH
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileNames(self, "Add source file", path, "*.*")
        file_paths = answer[0]
        if not file_paths:  # Cancel button clicked
            return
        for path in file_paths:
            if not self.add_single_include(path):
                continue

    @Slot(bool, name="show_add_source_dirs_dialog")
    def show_add_source_dirs_dialog(self, checked=False):
        """Let user select a source directory for this tool specification.
        All files and sub-directories will be added to the source files.
        """
        path = self.program_path if self.program_path else APPLICATION_PATH
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getExistingDirectory(self, "Select a directory to add to source files", path)
        file_paths = list()
        for root, _, files in os.walk(answer):
            for file in files:
                file_paths.append(os.path.abspath(os.path.join(root, file)))
        for path in file_paths:
            if not self.add_single_include(path):
                continue

    @Slot("QVariant", name="add_dropped_includes")
    def add_dropped_includes(self, file_paths):
        """Adds dropped file paths to Source files list."""
        for path in file_paths:
            if not self.add_single_include(path):
                continue

    def add_single_include(self, path):
        """Add file path to Source files list."""
        dirname, file_pattern = os.path.split(path)
        # logging.debug("program path:{0}".format(self.program_path))
        # logging.debug("{0}, {1}".format(dirname, file_pattern))
        if not self.program_path:
            self.program_path = dirname
            self.ui.label_mainpath.setText(self.program_path)
            path_to_add = file_pattern
        else:
            # check if path is a descendant of main dir.
            common_prefix = os.path.commonprefix([os.path.abspath(self.program_path), os.path.abspath(path)])
            # logging.debug("common_prefix:{0}".format(common_prefix))
            if common_prefix != self.program_path:
                self.statusbar.showMessage(
                    "Source file {0}'s location is invalid " "(should be in main directory)".format(file_pattern), 5000
                )
                return False
            path_to_add = os.path.relpath(path, self.program_path)
        if self.sourcefiles_model.findItems(path_to_add):
            self.statusbar.showMessage("Source file {0} already included".format(path_to_add), 5000)
            return False
        qitem = QStandardItem(path_to_add)
        qitem.setFlags(~Qt.ItemIsEditable)
        qitem.setData(QFileIconProvider().icon(QFileInfo(path_to_add)), Qt.DecorationRole)
        self.sourcefiles_model.appendRow(qitem)
        return True

    @busy_effect
    @Slot("QModelIndex", name="open_includes_file")
    def open_includes_file(self, index):
        """Open source file in default program."""
        if not index:
            return
        if not index.isValid():
            self._toolbox.msg_error.emit("Selected index not valid")
            return
        includes_file = self.sourcefiles_model.itemFromIndex(index).text()
        _, ext = os.path.splitext(includes_file)
        if ext in [".bat", ".exe"]:
            self._toolbox.msg_warning.emit(
                "Sorry, opening files with extension <b>{0}</b> not implemented. "
                "Please open the file manually.".format(ext)
            )
            return
        url = "file:///" + os.path.join(self.program_path, includes_file)
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open file: <b>{0}</b>".format(includes_file))

    @Slot(name="remove_source_files_with_del")
    def remove_source_files_with_del(self):
        """Support for deleting items with the Delete key."""
        self.remove_source_files()

    @Slot(bool, name="remove_source_files")
    def remove_source_files(self, checked=False):
        """Remove selected source files from include list.
        Do not remove anything if there are no items selected.
        """
        indexes = self.ui.treeView_sourcefiles.selectedIndexes()
        if not indexes:  # Nothing selected
            self.statusbar.showMessage("Please select the source files to remove", 3000)
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.sourcefiles_model.removeRow(row)
            if self.sourcefiles_model.rowCount() == 0:
                if self.ui.lineEdit_main_program.text().strip() == "":
                    self.program_path = None
                    self.ui.label_mainpath.clear()
            self.statusbar.showMessage("Selected source files removed", 3000)

    @Slot(bool, name="add_inputfiles")
    def add_inputfiles(self, checked=False):
        """Let user select input files for this tool specification."""
        msg = (
            "Add an input file or a directory required by your program. Wildcards "
            "<b>are not</b> supported.<br/><br/>"
            "Examples:<br/>"
            "<b>data.csv</b> -> File is copied to the same work directory as the main program.<br/>"
            "<b>input/data.csv</b> -> Creates subdirectory /input to work directory and "
            "copies file data.csv there.<br/>"
            "<b>output/</b> -> Creates an empty directory into the work directory.<br/><br/>"
        )
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QInputDialog.getText(self, "Add input item", msg, flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        file_name = answer[0]
        if not file_name:  # Cancel button clicked
            return
        qitem = QStandardItem(file_name)
        qitem.setData(QFileIconProvider().icon(QFileInfo(file_name)), Qt.DecorationRole)
        self.inputfiles_model.appendRow(qitem)

    @Slot(name="remove_inputfiles_with_del")
    def remove_inputfiles_with_del(self):
        """Support for deleting items with the Delete key."""
        self.remove_inputfiles()

    @Slot(bool, name="remove_inputfiles")
    def remove_inputfiles(self, checked=False):
        """Remove selected input files from list.
        Do not remove anything if there are no items selected.
        """
        indexes = self.ui.treeView_inputfiles.selectedIndexes()
        if not indexes:  # Nothing selected
            self.statusbar.showMessage("Please select the input files to remove", 3000)
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.inputfiles_model.removeRow(row)
            self.statusbar.showMessage("Selected input files removed", 3000)

    @Slot(bool, name="add_inputfiles_opt")
    def add_inputfiles_opt(self, checked=False):
        """Let user select optional input files for this tool specification."""
        msg = (
            "Add optional input files that may be utilized by your program. <br/>"
            "Wildcards are supported.<br/><br/>"
            "Examples:<br/>"
            "<b>data.csv</b> -> If found, file is copied to the same work directory as the main program.<br/>"
            "<b>*.csv</b> -> All found CSV files are copied to the same work directory as the main program.<br/>"
            "<b>input/data_?.dat</b> -> All found files matching the pattern 'data_?.dat' will be copied to <br/>"
            "input/ subdirectory under the same work directory as the main program.<br/><br/>"
        )
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QInputDialog.getText(
            self, "Add optional input item", msg, flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        file_name = answer[0]
        if not file_name:  # Cancel button clicked
            return
        qitem = QStandardItem(file_name)
        qitem.setData(QFileIconProvider().icon(QFileInfo(file_name)), Qt.DecorationRole)
        self.inputfiles_opt_model.appendRow(qitem)

    @Slot(name="remove_inputfiles_opt_with_del")
    def remove_inputfiles_opt_with_del(self):
        """Support for deleting items with the Delete key."""
        self.remove_inputfiles_opt()

    @Slot(bool, name="remove_inputfiles_opt")
    def remove_inputfiles_opt(self, checked=False):
        """Remove selected optional input files from list.
        Do not remove anything if there are no items selected.
        """
        indexes = self.ui.treeView_inputfiles_opt.selectedIndexes()
        if not indexes:  # Nothing selected
            self.statusbar.showMessage("Please select the optional input files to remove", 3000)
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.inputfiles_opt_model.removeRow(row)
            self.statusbar.showMessage("Selected optional input files removed", 3000)

    @Slot(bool, name="add_outputfiles")
    def add_outputfiles(self, checked=False):
        """Let user select output files for this tool specification."""
        msg = (
            "Add output files that will be archived into the Tool results directory after the <br/>"
            "Tool specification has finished execution. Wildcards are supported.<br/><br/>"
            "Examples:<br/>"
            "<b>results.csv</b> -> File is copied from work directory into results.<br/> "
            "<b>*.csv</b> -> All CSV files will copied into results.<br/> "
            "<b>output/*.gdx</b> -> All GDX files from the work subdirectory /output will be copied into <br/>"
            "results /output subdirectory.<br/><br/>"
        )
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QInputDialog.getText(self, "Add output item", msg, flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        file_name = answer[0]
        if not file_name:  # Cancel button clicked
            return
        qitem = QStandardItem(file_name)
        qitem.setData(QFileIconProvider().icon(QFileInfo(file_name)), Qt.DecorationRole)
        self.outputfiles_model.appendRow(qitem)

    @Slot(name="remove_outputfiles_with_del")
    def remove_outputfiles_with_del(self):
        """Support for deleting items with the Delete key."""
        self.remove_outputfiles()

    @Slot(bool, name="remove_outputfiles")
    def remove_outputfiles(self, checked=False):
        """Remove selected output files from list.
        Do not remove anything if there are no items selected.
        """
        indexes = self.ui.treeView_outputfiles.selectedIndexes()
        if not indexes:  # Nothing selected
            self.statusbar.showMessage("Please select the output files to remove", 3000)
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.outputfiles_model.removeRow(row)
            self.statusbar.showMessage("Selected output files removed", 3000)

    @Slot()
    def handle_ok_clicked(self):
        """Checks that everything is valid, creates Tool spec definition dictionary and adds Tool spec to project."""
        # Check that tool type is selected
        if self.ui.comboBox_tooltype.currentIndex() == 0:
            self.statusbar.showMessage("Tool type not selected", 3000)
            return
        self.definition["name"] = self.ui.lineEdit_name.text()
        self.definition["description"] = self.ui.textEdit_description.toPlainText()
        self.definition["tooltype"] = self.ui.comboBox_tooltype.currentText().lower()
        flags = Qt.MatchContains
        # Check that path of main program file is valid before saving it
        main_program = self.ui.lineEdit_main_program.text().strip()
        if not os.path.isfile(main_program):
            self.statusbar.showMessage("Main program file is not valid", 6000)
            return
        # Fix for issue #241
        folder_path, file_path = os.path.split(main_program)
        self.program_path = os.path.abspath(folder_path)
        self.ui.label_mainpath.setText(self.program_path)
        self.definition["execute_in_work"] = self.ui.checkBox_execute_in_work.isChecked()
        self.definition["includes"] = [file_path]
        self.definition["includes"] += [i.text() for i in self.sourcefiles_model.findItems("", flags)]
        self.definition["inputfiles"] = [i.text() for i in self.inputfiles_model.findItems("", flags)]
        self.definition["inputfiles_opt"] = [i.text() for i in self.inputfiles_opt_model.findItems("", flags)]
        self.definition["outputfiles"] = [i.text() for i in self.outputfiles_model.findItems("", flags)]
        # Strip whitespace from args before saving it to JSON
        self.definition["cmdline_args"] = ToolSpecification.split_cmdline_args(self.ui.lineEdit_args.text())
        for k in REQUIRED_KEYS:
            if not self.definition[k]:
                self.statusbar.showMessage("{} missing".format(k), 3000)
                return
        # Create new Tool specification
        short_name = self.definition["name"].lower().replace(" ", "_")
        self.def_file_path = os.path.join(self.program_path, short_name + ".json")
        if self.call_add_tool_specification():
            self.close()

    def call_add_tool_specification(self):
        """Adds or updates Tool specification according to user's selections.
        If the name is the same as an existing tool specification, it is updated and
        auto-saved to the definition file. (User is editing an existing
        tool specification.) If the name is not in the tool specification model, creates
        a new tool specification and offer to save the definition file. (User is
        creating a new tool specification from scratch or spawning from an existing one).
        """
        # Load tool specification
        path = self.program_path
        tool = self._project.load_tool_specification_from_dict(self.definition, path)
        if not tool:
            self.statusbar.showMessage("Adding Tool specification failed", 3000)
            return False
        # Check if a tool specification with this name already exists
        row = self._toolbox.tool_specification_model.tool_specification_row(tool.name)
        if row >= 0:  # NOTE: Row 0 at this moment has 'No tool', but in the future it may change. Better be ready.
            old_tool = self._toolbox.tool_specification_model.tool_specification(row)
            def_file = old_tool.get_def_path()
            tool.set_def_path(def_file)
            if tool.__dict__ == old_tool.__dict__:  # Nothing changed. We're done here.
                return True
            # logging.debug("Updating definition for tool specification '{}'".format(tool.name))
            self._toolbox.update_tool_specification(row, tool)
        else:
            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            answer = QFileDialog.getSaveFileName(
                self, "Save Tool specification file", self.def_file_path, "JSON (*.json)"
            )
            if answer[0] == "":  # Cancel button clicked
                return False
            def_file = os.path.abspath(answer[0])
            tool.set_def_path(def_file)
            self._toolbox.add_tool_specification(tool)
        # Save path of main program file relative to definition file in case they differ
        def_path = os.path.dirname(def_file)
        if def_path != self.program_path:
            self.definition["includes_main_path"] = os.path.relpath(self.program_path, def_path)
        # Save file descriptor
        with open(def_file, "w") as fp:
            try:
                json.dump(self.definition, fp, indent=4)
            except ValueError:
                self.statusbar.showMessage("Error saving file", 3000)
                self._toolbox.msg_error.emit("Saving Tool specification file failed. Path:{0}".format(def_file))
                return False
        return True

    def keyPressEvent(self, e):
        """Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()

    def _make_add_cmdline_tag_menu(self):
        """Constructs a popup menu for the '@@' button."""
        menu = QMenu(self.ui.toolButton_add_cmdline_tag)
        action = menu.addAction(str(CmdlineTag.URL_INPUTS))
        action.triggered.connect(self._add_cmdline_tag_url_inputs)
        action.setToolTip("Insert a tag that is replaced by all input database URLs.")
        action = menu.addAction(str(CmdlineTag.URL_OUTPUTS))
        action.triggered.connect(self._add_cmdline_tag_url_outputs)
        action.setToolTip("Insert a tag that is replaced be all output database URLs.")
        action = menu.addAction(str(CmdlineTag.URL))
        action.triggered.connect(self._add_cmdline_tag_data_store_url)
        action.setToolTip("Insert a tag that is replaced by the URL provided by Data Store '<data-store-name>'.")
        action = menu.addAction(str(CmdlineTag.OPTIONAL_INPUTS))
        action.triggered.connect(self._add_cmdline_tag_optional_inputs)
        action.setToolTip("Insert a tag that is replaced by a list of optional input files.")
        return menu

    def _insert_spaces_around_tag_in_args_edit(self, tag_length, restore_cursor_to_tag_end=False):
        """
        Inserts spaces before/after @@ around cursor position/selection

        Expects cursor to be at the end of the tag.
        """
        args_edit = self.ui.lineEdit_args
        text = args_edit.text()
        cursor_position = args_edit.cursorPosition()
        if cursor_position == len(text) or (cursor_position < len(text) - 1 and not text[cursor_position].isspace()):
            args_edit.insert(" ")
            appended_spaces = 1
            text = args_edit.text()
        else:
            appended_spaces = 0
        tag_start = cursor_position - tag_length
        if tag_start > 1 and text[tag_start - 2 : tag_start] == CMDLINE_TAG_EDGE:
            args_edit.setCursorPosition(tag_start)
            args_edit.insert(" ")
            prepended_spaces = 1
        else:
            prepended_spaces = 0
        if restore_cursor_to_tag_end:
            args_edit.setCursorPosition(cursor_position + prepended_spaces)
        else:
            args_edit.setCursorPosition(cursor_position + appended_spaces + prepended_spaces)

    @Slot("QAction")
    def _add_cmdline_tag_url_inputs(self, _):
        """Inserts @@url_inputs@@ tag to command line arguments."""
        tag = CmdlineTag.URL_INPUTS
        self.ui.lineEdit_args.insert(tag)
        self._insert_spaces_around_tag_in_args_edit(len(tag))

    @Slot("QAction")
    def _add_cmdline_tag_url_outputs(self, _):
        """Inserts @@url_outputs@@ tag to command line arguments."""
        tag = CmdlineTag.URL_OUTPUTS
        self.ui.lineEdit_args.insert(tag)
        self._insert_spaces_around_tag_in_args_edit(len(tag))

    @Slot("QAction")
    def _add_cmdline_tag_data_store_url(self, _):
        """Inserts @@url:<data-store-name>@@ tag to command line arguments and selects '<data-store-name>'."""
        args_edit = self.ui.lineEdit_args
        tag = CmdlineTag.URL
        args_edit.insert(tag)
        self._insert_spaces_around_tag_in_args_edit(len(tag), restore_cursor_to_tag_end=True)
        cursor_position = args_edit.cursorPosition()
        args_edit.setSelection(cursor_position - len(CMDLINE_TAG_EDGE + "<data-store_name>"), len("<data-store_name>"))

    @Slot("QAction")
    def _add_cmdline_tag_optional_inputs(self, _):
        """Inserts @@optional_inputs@@ tag to command line arguments."""
        tag = CmdlineTag.OPTIONAL_INPUTS
        self.ui.lineEdit_args.insert(tag)
        self._insert_spaces_around_tag_in_args_edit(len(tag))
