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
QWidget that is used to create or edit Tool Templates.
In the former case it is presented empty, but in the latter it
is filled with all the information from the template being edited.

:author: M. Marin (KTH)
:date:   12.4.2018
"""

import logging
import os
import json
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QWidget, QStatusBar, QInputDialog, QFileDialog, QStyle
from PySide2.QtCore import Slot, Qt, QUrl
from PySide2.QtGui import QDesktopServices
from ui.tool_template_form import Ui_Form
from config import STATUSBAR_SS, TT_TREEVIEW_HEADER_SS,\
    APPLICATION_PATH, TOOL_TYPES, REQUIRED_KEYS
from helpers import busy_effect
from widgets.custom_menus import AddIncludesPopupMenu


class ToolTemplateWidget(QWidget):
    """A widget to query user's preferences for a new tool template.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        tool_template (ToolTemplate): If given, the form is pre-filled with this template
    """
    def __init__(self, toolbox, tool_template=None):
        """ Initialize class."""
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
        self.ui.toolButton_add_main_program.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.ui.toolButton_add_source_files.setIcon(self.style().standardIcon(QStyle.SP_FileLinkIcon))
        self.ui.toolButton_add_source_dirs.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.ui.toolButton_minus_source_files.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.ui.toolButton_plus_inputfiles.setIcon(self.style().standardIcon(QStyle.SP_FileLinkIcon))
        self.ui.toolButton_minus_inputfiles.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.ui.toolButton_plus_inputfiles_opt.setIcon(self.style().standardIcon(QStyle.SP_FileLinkIcon))
        self.ui.toolButton_minus_inputfiles_opt.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.ui.toolButton_plus_outputfiles.setIcon(self.style().standardIcon(QStyle.SP_FileLinkIcon))
        self.ui.toolButton_minus_outputfiles.setIcon(self.style().standardIcon(QStyle.SP_DialogDiscardButton))
        self.ui.treeView_sourcefiles.setModel(self.sourcefiles_model)
        self.ui.treeView_inputfiles.setModel(self.inputfiles_model)
        self.ui.treeView_inputfiles_opt.setModel(self.inputfiles_opt_model)
        self.ui.treeView_outputfiles.setModel(self.outputfiles_model)
        self.ui.treeView_sourcefiles.setStyleSheet(TT_TREEVIEW_HEADER_SS)
        self.ui.treeView_inputfiles.setStyleSheet(TT_TREEVIEW_HEADER_SS)
        self.ui.treeView_inputfiles_opt.setStyleSheet(TT_TREEVIEW_HEADER_SS)
        self.ui.treeView_outputfiles.setStyleSheet(TT_TREEVIEW_HEADER_SS)
        self.ui.comboBox_tooltype.addItem("Select tool type...")
        self.ui.comboBox_tooltype.addItems(TOOL_TYPES)
        # if a template is given, fill the form with data from it
        if tool_template:
            self.ui.lineEdit_name.setText(tool_template.name)
            self.ui.textEdit_description.setPlainText(tool_template.description)
            self.ui.lineEdit_args.setText(tool_template.cmdline_args)
            tool_types = [x.lower() for x in TOOL_TYPES]
            index = tool_types.index(tool_template.tooltype) + 1
            self.ui.comboBox_tooltype.setCurrentIndex(index)
        # Init lists
        self.main_program_file = ""
        self.sourcefiles = list(tool_template.includes) if tool_template else list()
        self.inputfiles = list(tool_template.inputfiles) if tool_template else list()
        self.inputfiles_opt = list(tool_template.inputfiles_opt) if tool_template else list()
        self.outputfiles = list(tool_template.outputfiles) if tool_template else list()
        self.def_file_path = tool_template.def_file_path if tool_template else None
        self.program_path = tool_template.path if tool_template else None
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
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.toolButton_add_main_program.clicked.connect(self.browse_main_program)
        self.ui.toolButton_add_source_files.clicked.connect(self.show_add_source_files_dialog)
        self.ui.toolButton_add_source_dirs.clicked.connect(self.show_add_source_dirs_dialog)
        self.ui.treeView_sourcefiles.files_dropped.connect(self.add_dropped_includes)
        self.ui.treeView_sourcefiles.doubleClicked.connect(self.open_includes_file)
        self.ui.toolButton_minus_source_files.clicked.connect(self.remove_source_files)
        self.ui.toolButton_plus_inputfiles.clicked.connect(self.add_inputfiles)
        self.ui.toolButton_minus_inputfiles.clicked.connect(self.remove_inputfiles)
        self.ui.toolButton_plus_inputfiles_opt.clicked.connect(self.add_inputfiles_opt)
        self.ui.toolButton_minus_inputfiles_opt.clicked.connect(self.remove_inputfiles_opt)
        self.ui.toolButton_plus_outputfiles.clicked.connect(self.add_outputfiles)
        self.ui.toolButton_minus_outputfiles.clicked.connect(self.remove_outputfiles)
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    def make_header_for_includes(self):
        """Add header to includes model. I.e. tool source files and necessary folders."""
        h = QStandardItem("Source files")
        self.sourcefiles_model.setHorizontalHeaderItem(0, h)

    def make_header_for_inputfiles(self):
        """Add header to inputfiles model. I.e. tool input files."""
        h = QStandardItem("Input files")
        self.inputfiles_model.setHorizontalHeaderItem(0, h)

    def make_header_for_inputfiles_opt(self):
        """Add header to inputfiles model. I.e. tool optional input files."""
        h = QStandardItem("Optional input files")
        self.inputfiles_opt_model.setHorizontalHeaderItem(0, h)

    def make_header_for_outputfiles(self):
        """Add header to outputfiles model. I.e. tool output files."""
        h = QStandardItem("Output files")
        self.outputfiles_model.setHorizontalHeaderItem(0, h)

    def populate_sourcefile_list(self, items):
        """List source files in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.sourcefiles_model.clear()
        self.make_header_for_includes()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                self.sourcefiles_model.appendRow(qitem)

    def populate_inputfiles_list(self, items):
        """List input files in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.inputfiles_model.clear()
        self.make_header_for_inputfiles()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                self.inputfiles_model.appendRow(qitem)

    def populate_inputfiles_opt_list(self, items):
        """List optional input files in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.inputfiles_opt_model.clear()
        self.make_header_for_inputfiles_opt()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                self.inputfiles_opt_model.appendRow(qitem)

    def populate_outputfiles_list(self, items):
        """List output files in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.outputfiles_model.clear()
        self.make_header_for_outputfiles()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                self.outputfiles_model.appendRow(qitem)

    @Slot(bool, name="browse_main_program")
    def browse_main_program(self, checked=False):
        """Open file browser where user can select the path of the main program file."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self._toolbox, "Add main program file", APPLICATION_PATH, "*.*")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        folder_path = os.path.split(file_path)[0]
        self.program_path = os.path.abspath(folder_path)
        # Update UI
        self.ui.lineEdit_main_program.setText(file_path)
        self.ui.label_mainpath.setText(self.program_path)

    @Slot(name="new_source_file")
    def new_source_file(self):
        """Let user create a new source file for this tool template."""
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
        """Let user select source files for this tool template."""
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
        """Let user select a source directory for this tool template.
        All files and sub-directories will be added to the source files.
        """
        path = self.program_path if self.program_path else APPLICATION_PATH
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getExistingDirectory(self, "Select a directory to add to source files", path)
        file_paths = list()
        for root, dirs, files in os.walk(answer):
            for file in files:
                file_paths.append(os.path.abspath(os.path.join(root, file)))
        for path in file_paths:
            if not self.add_single_include(path):
                continue

    @Slot("QVariant", name="add_dropped_includes")
    def add_dropped_includes(self, file_paths):
        for path in file_paths:
            if not self.add_single_include(path):
                continue

    def add_single_include(self, path):
        """Add file path to Source files list."""
        dirname, file_pattern = os.path.split(path)
        logging.debug("program path:{0}".format(self.program_path))
        logging.debug("{0}, {1}".format(dirname, file_pattern))
        if not self.program_path:
            self.program_path = dirname
            self.ui.label_mainpath.setText(self.program_path)
            path_to_add = file_pattern
        else:
            # check if path is a descendant of main dir. TODO: Is os.path.abspath() the answer?
            common_prefix = os.path.commonprefix([os.path.abspath(self.program_path), os.path.abspath(path)])
            logging.debug("common_prefix:{0}".format(common_prefix))
            if common_prefix != self.program_path:
                self.statusbar.showMessage("Source file {0}'s location is invalid "
                                           "(should be in main directory)"
                                           .format(file_pattern), 5000)
                return False
            path_to_add = os.path.relpath(path, self.program_path)
        if self.sourcefiles_model.findItems(path_to_add):
            self.statusbar.showMessage("Source file {0} already included".format(path_to_add), 5000)
            return False
        qitem = QStandardItem(path_to_add)
        qitem.setFlags(~Qt.ItemIsEditable)
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
        else:
            includes_file = self.sourcefiles_model.itemFromIndex(index).text()
            fname, ext = os.path.splitext(includes_file)
            if ext in [".bat", ".exe"]:
                self._toolbox.msg_warning.emit("Sorry, opening files with extension <b>{0}</b> not implemented. "
                                               "Please open the file manually.".format(ext))
                return
            url = "file:///" + os.path.join(self.program_path, includes_file)
            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
            if not res:
                self._toolbox.msg_error.emit("Failed to open file: <b>{0}</b>".format(includes_file))

    @Slot(bool, name="remove_source_files")
    def remove_source_files(self, checked=False):
        """Remove selected source files from include list.
        Removes all files if nothing is selected.
        """
        indexes = self.ui.treeView_sourcefiles.selectedIndexes()
        if not indexes:  # Nothing selected
            self.sourcefiles_model.clear()
            self.make_header_for_includes()
            if self.ui.lineEdit_main_program.text().strip() == "":
                self.program_path = None
                self.ui.label_mainpath.clear()
            self.statusbar.showMessage("All source files removed", 3000)
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.sourcefiles_model.removeRow(row)
            if self.sourcefiles_model.rowCount() == 0:
                if self.ui.lineEdit_main_program.text().strip() == "":
                    self.program_path = None
                    self.ui.label_mainpath.clear()
            # elif 0 in rows:  # main program was removed
            #     # new main is the first one still in the list
            #     # TODO: isn't it better to pick the new main as the one with the smallest path?
            #     dirname = os.path.dirname(self.sourcefiles_model.item(0).text())
            #     new_main_path = os.path.join(self.program_path, dirname)
            #     old_main_path = self.program_path
            #     row = 0
            #     while True:
            #         if row == self.sourcefiles_model.rowCount():
            #             break
            #         path = self.sourcefiles_model.item(row).text()
            #         old_path = os.path.join(old_main_path, path)
            #         if os.path.commonprefix([new_main_path, old_path]) == new_main_path:
            #             # path is still valid (update item and increase row counter)
            #             new_path = os.path.relpath(old_path, new_main_path)
            #             index = self.sourcefiles_model.index(row, 0)
            #             self.sourcefiles_model.setData(index, new_path)
            #             row = row + 1
            #             continue
            #         # path is no longer valid (remove item and don't increase row counter)
            #         self.sourcefiles_model.removeRow(row)
            #     self.program_path = new_main_path
            #     self.ui.label_mainpath.setText(self.program_path)
            self.statusbar.showMessage("Selected source files removed", 3000)

    @Slot(bool, name="add_inputfiles")
    def add_inputfiles(self, checked=False):
        """Let user select input files for this tool template."""
        msg = "Add an input file or a directory required by your program.\n" \
              "Examples:\n" \
              "data.csv -> File is copied to the same work directory as the main program.\n" \
              "input/data.csv -> Creates subdirectory input\ to the work directory and copies the file there.\n" \
              "output/ -> Creates an empty directory into the work directory."
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QInputDialog.getText(self, "Add input item", msg)
        file_name = answer[0]
        if not file_name:  # Cancel button clicked
            return
        qitem = QStandardItem(file_name)
        self.inputfiles_model.appendRow(qitem)

    @Slot(bool, name="remove_inputfiles")
    def remove_inputfiles(self, checked=False):
        """Remove selected input files from list.
        Removes all files if nothing is selected.
        """
        indexes = self.ui.treeView_inputfiles.selectedIndexes()
        if not indexes:  # Nothing selected
            self.inputfiles_model.clear()
            self.make_header_for_inputfiles()
            self.statusbar.showMessage("All input files removed", 3000)
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.inputfiles_model.removeRow(row)
            self.statusbar.showMessage("Selected input files removed", 3000)

    @Slot(bool, name="add_inputfiles_opt")
    def add_inputfiles_opt(self, checked=False):
        """Let user select optional input files for this tool template."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QInputDialog.getText(self, "Add optional input item", "Optional input file name (eg. other.csv):")
        file_name = answer[0]
        if not file_name:  # Cancel button clicked
            return
        qitem = QStandardItem(file_name)
        self.inputfiles_opt_model.appendRow(qitem)

    @Slot(bool, name="remove_inputfiles_opt")
    def remove_inputfiles_opt(self, checked=False):
        """Remove selected optional input files from list.
        Removes all files if nothing is selected.
        """
        indexes = self.ui.treeView_inputfiles_opt.selectedIndexes()
        if not indexes:  # Nothing selected
            self.inputfiles_opt_model.clear()
            self.make_header_for_inputfiles_opt()
            self.statusbar.showMessage("All optional input files removed", 3000)
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.inputfiles_opt_model.removeRow(row)
            self.statusbar.showMessage("Selected optional input files removed", 3000)

    @Slot(bool, name="add_outputfiles")
    def add_outputfiles(self, checked=False):
        """Let user select output files for this tool template."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QInputDialog.getText(self, "Add output item", "Output file name (eg. results.csv):")
        file_name = answer[0]
        if not file_name:  # Cancel button clicked
            return
        qitem = QStandardItem(file_name)
        self.outputfiles_model.appendRow(qitem)

    @Slot(bool, name="remove_outputfiles")
    def remove_outputfiles(self, checked=False):
        """Remove selected output files from list.
        Removes all files if nothing is selected.
        """
        indexes = self.ui.treeView_outputfiles.selectedIndexes()
        if not indexes:  # Nothing selected
            self.outputfiles_model.clear()
            self.make_header_for_outputfiles()
            self.statusbar.showMessage("All output files removed", 3000)
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.outputfiles_model.removeRow(row)
            self.statusbar.showMessage("Selected output files removed", 3000)

    @Slot(name="ok_clicked")
    def ok_clicked(self):
        """Check that everything is valid, create definition dictionary and add template to project."""
        # Check that tool type is selected
        if self.ui.comboBox_tooltype.currentIndex() == 0:
            self.statusbar.showMessage("Tool type not selected", 3000)
            return
        self.definition['name'] = self.ui.lineEdit_name.text()
        self.definition['description'] = self.ui.textEdit_description.toPlainText()
        self.definition['tooltype'] = self.ui.comboBox_tooltype.currentText().lower()
        flags = Qt.MatchContains
        # Check that main program file is valid before saving it
        if not os.path.isfile(self.ui.lineEdit_main_program.text().strip()):
            self.statusbar.showMessage("Main program file is not valid", 6000)
            return
        self.definition['includes'] = [os.path.split(self.ui.lineEdit_main_program.text().strip())[1]]
        self.definition['includes'] += [i.text() for i in self.sourcefiles_model.findItems("", flags)]
        self.definition['inputfiles'] = [i.text() for i in self.inputfiles_model.findItems("", flags)]
        self.definition['inputfiles_opt'] = [i.text() for i in self.inputfiles_opt_model.findItems("", flags)]
        self.definition['outputfiles'] = [i.text() for i in self.outputfiles_model.findItems("", flags)]
        self.definition['cmdline_args'] = self.ui.lineEdit_args.text()
        for k in REQUIRED_KEYS:
            if not self.definition[k]:
                self.statusbar.showMessage("{} missing".format(k.capitalize()), 3000)
                return
        # Create new Template
        short_name = self.definition['name'].lower().replace(' ', '_')
        self.def_file_path = os.path.join(self.program_path, short_name + ".json")
        if self.call_add_tool_template():
            self.close()

    def call_add_tool_template(self):
        """Add or update Tool Template according to user's selections.
        If the name is the same as an existing tool template, it is updated and
        auto-saved to the definition file. (The user is editing an existing
        tool template.)
        If the name is not in the tool template model, create a new tool template and
        offer to save the definition file. (The user is creating a new tool template
        from scratch or spawning from an existing one).
        """
        # Load tool template
        path = self.program_path
        tool = self._project.load_tool_template_from_dict(self.definition, path)
        if not tool:
            self.statusbar.showMessage("Adding Tool template failed", 3000)
            return False
        # Check if a tool template with this name already exists
        row = self._toolbox.tool_template_model.tool_template_row(tool.name)
        if row >= 0:  # NOTE: Row 0 at this moment has 'No tool', but in the future it may change. Better be ready.
            old_tool = self._toolbox.tool_template_model.tool_template(row)
            def_file = old_tool.get_def_path()
            tool.set_def_path(def_file)
            if tool.__dict__ == old_tool.__dict__:  # Nothing changed. We're done here.
                return True
            # logging.debug("Updating definition for tool template '{}'".format(tool.name))
            self._toolbox.update_tool_template(row, tool)
        else:
            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            answer = QFileDialog.getSaveFileName(self, 'Save tool template file', self.def_file_path, 'JSON (*.json)')
            if answer[0] == '':  # Cancel button clicked
                return False
            def_file = os.path.abspath(answer[0])
            tool.set_def_path(def_file)
            self._toolbox.add_tool_template(tool)
        # Save path of main program file relative to definition file in case they differ
        def_path = os.path.dirname(def_file)
        if def_path != self.program_path:
            self.definition['includes_main_path'] = os.path.relpath(self.program_path, def_path)
        # Save file descriptor
        with open(def_file, 'w') as fp:
            try:
                json.dump(self.definition, fp, indent=4)
            except ValueError:
                self.statusbar.showMessage("Error saving file", 3000)
                self._toolbox.msg_error.emit("Saving Tool template definition file failed. Path:{0}".format(def_file))
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
