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
Module for data connection class.

:author: P. Savolainen (VTT)
:date:   19.12.2017
"""

import os
import shutil
import logging
from PySide2.QtCore import Slot, QUrl, QFileSystemWatcher, Qt, QFileInfo
from PySide2.QtGui import QDesktopServices, QStandardItem, QStandardItemModel, QIcon, QPixmap
from PySide2.QtWidgets import QFileDialog, QStyle, QFileIconProvider, QInputDialog, QMessageBox
from project_item import ProjectItem
from widgets.spine_datapackage_widget import SpineDatapackageWidget
from helpers import busy_effect, create_dir
from config import APPLICATION_PATH, INVALID_FILENAME_CHARS


class DataConnection(ProjectItem):
    """Data Connection class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        references (list): List of file references
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """

    def __init__(self, toolbox, name, description, references, x, y):
        """Class constructor."""
        super().__init__(toolbox, name, description, x, y)
        self._project = self._toolbox.project()
        self.item_type = "Data Connection"
        self.reference_model = QStandardItemModel()  # References to files
        self.data_model = QStandardItemModel()  # Paths of project internal files. These are found in DC data directory
        self.datapackage_icon = QIcon(QPixmap(":/icons/datapkg.png"))
        self.data_dir_watcher = QFileSystemWatcher(self)
        # Make project directory for this Data Connection
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
            self.data_dir_watcher.addPath(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed." " Check permissions.".format(self.data_dir)
            )
        # Populate references model
        self.references = references
        self.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = self.data_files()
        self.populate_data_list(data_files)
        self.spine_datapackage_form = None

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._properties_ui.toolButton_dc_open_dir.clicked] = self.open_directory
        s[self._properties_ui.toolButton_plus.clicked] = self.add_references
        s[self._properties_ui.toolButton_minus.clicked] = self.remove_references
        s[self._properties_ui.toolButton_add.clicked] = self.copy_to_project
        s[self._properties_ui.pushButton_datapackage.clicked] = self.show_spine_datapackage_form
        s[self._properties_ui.treeView_dc_references.doubleClicked] = self.open_reference
        s[self._properties_ui.treeView_dc_data.doubleClicked] = self.open_data_file
        s[self.data_dir_watcher.directoryChanged] = self.refresh
        s[self._properties_ui.treeView_dc_references.files_dropped] = self.add_files_to_references
        s[self._properties_ui.treeView_dc_data.files_dropped] = self.add_files_to_data_dir
        s[self.get_icon().scene().files_dropped_on_dc] = self.receive_files_dropped_on_dc
        return s

    def activate(self):
        """Restore selections and connect signals."""
        self.restore_selections()  # Do this before connecting signals or funny things happen
        super().connect_signals()

    def deactivate(self):
        """Save selections and disconnect signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed", self.name)
            return False
        return True

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""
        self._properties_ui.label_dc_name.setText(self.name)
        self._properties_ui.treeView_dc_references.setModel(self.reference_model)
        self._properties_ui.treeView_dc_data.setModel(self.data_model)
        self.refresh()

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""

    @Slot("QVariant", name="add_files_to_references")
    def add_files_to_references(self, paths):
        """Add multiple file paths to reference list.

        Args:
            paths (list): A list of paths to files
        """
        for path in paths:
            if path in self.references:
                self._toolbox.msg_warning.emit("Reference to file <b>{0}</b> already available".format(path))
                return
            self.references.append(os.path.abspath(path))
        self.populate_reference_list(self.references)

    @Slot("QGraphicsItem", "QVariant", name="receive_files_dropped_on_dc")
    def receive_files_dropped_on_dc(self, item, file_paths):
        """Called when files are dropped onto a data connection graphics item.
        If the item is this Data Connection's graphics item, add the files to data."""
        if item == self._graphics_item:
            self.add_files_to_data_dir(file_paths)

    @Slot("QVariant", name="add_files_to_data_dir")
    def add_files_to_data_dir(self, file_paths):
        """Add files to data directory"""
        for file_path in file_paths:
            filename = os.path.split(file_path)[1]
            self._toolbox.msg.emit("Copying file <b>{0}</b> to <b>{1}</b>".format(filename, self.name))
            try:
                shutil.copy(file_path, self.data_dir)
            except OSError:
                self._toolbox.msg_error.emit("[OSError] Copying failed")
                return
        data_files = self.data_files()
        self.populate_data_list(data_files)

    @Slot(bool, name="open_directory")
    def open_directory(self, checked=False):
        """Open file explorer in Data Connection data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(bool, name="add_references")
    def add_references(self, checked=False):
        """Let user select references to files for this data connection."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileNames(self._toolbox, "Add file references", APPLICATION_PATH, "*.*")
        file_paths = answer[0]
        if not file_paths:  # Cancel button clicked
            return
        for path in file_paths:
            if path in self.references:
                self._toolbox.msg_warning.emit("Reference to file <b>{0}</b> already available".format(path))
                continue
            self.references.append(os.path.abspath(path))
        self.populate_reference_list(self.references)

    @Slot(bool, name="remove_references")
    def remove_references(self, checked=False):
        """Remove selected references from reference list.
        Do not remove anything if there are no references selected.
        """
        indexes = self._properties_ui.treeView_dc_references.selectedIndexes()
        if not indexes:  # Nothing selected
            self._toolbox.msg.emit("Please select references to remove")
            return
        rows = [ind.row() for ind in indexes]
        rows.sort(reverse=True)
        for row in rows:
            self.references.pop(row)
        self._toolbox.msg.emit("Selected references removed")
        self.populate_reference_list(self.references)

    @Slot(bool, name="copy_to_project")
    def copy_to_project(self, checked=False):
        """Copy selected file references to this Data Connection's data directory."""
        selected_indexes = self._properties_ui.treeView_dc_references.selectedIndexes()
        if not selected_indexes:
            self._toolbox.msg_warning.emit("No files to copy")
            return
        for index in selected_indexes:
            file_path = self.reference_model.itemFromIndex(index).data(Qt.DisplayRole)
            if not os.path.exists(file_path):
                self._toolbox.msg_error.emit("File <b>{0}</b> does not exist".format(file_path))
                continue
            filename = os.path.split(file_path)[1]
            self._toolbox.msg.emit("Copying file <b>{0}</b> to Data Connection <b>{1}</b>".format(filename, self.name))
            try:
                shutil.copy(file_path, self.data_dir)
            except OSError:
                self._toolbox.msg_error.emit("[OSError] Copying failed")
                continue

    @Slot("QModelIndex", name="open_reference")
    def open_reference(self, index):
        """Open reference in default program."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        reference = self.file_references()[index.row()]
        url = "file:///" + reference
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open reference:<b>{0}</b>".format(reference))

    @Slot("QModelIndex", name="open_data_file")
    def open_data_file(self, index):
        """Open data file in default program."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        data_file = self.data_files()[index.row()]
        url = "file:///" + os.path.join(self.data_dir, data_file)
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Opening file <b>{0}</b> failed".format(data_file))

    @busy_effect
    def show_spine_datapackage_form(self):
        """Show spine_datapackage_form widget."""
        if self.spine_datapackage_form:
            if self.spine_datapackage_form.windowState() & Qt.WindowMinimized:
                # Remove minimized status and restore window with the previous state (maximized/normal state)
                self.spine_datapackage_form.setWindowState(
                    self.spine_datapackage_form.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
                )
                self.spine_datapackage_form.activateWindow()
            else:
                self.spine_datapackage_form.raise_()
            return
        self.spine_datapackage_form = SpineDatapackageWidget(self)
        self.spine_datapackage_form.destroyed.connect(self.datapackage_form_destroyed)
        self.spine_datapackage_form.show()

    @Slot(name="datapackage_form_destroyed")
    def datapackage_form_destroyed(self):
        """Notify a connection that datapackage form has been destroyed."""
        self.spine_datapackage_form = None

    def make_new_file(self):
        """Create a new blank file to this Data Connections data directory."""
        msg = "File name"
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QInputDialog.getText(
            self._toolbox, "Create new file", msg, flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        file_name = answer[0]
        if not file_name:  # Cancel button clicked
            return
        if file_name.strip() == "":
            return
        # Check that file name has no invalid chars
        if any(True for x in file_name if x in INVALID_FILENAME_CHARS):
            msg = "File name <b>{0}</b> contains invalid characters.".format(file_name)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Creating file failed", msg)
            return
        file_path = os.path.join(self.data_dir, file_name)
        if os.path.exists(file_path):
            msg = "File <b>{0}</b> already exists.".format(file_name)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Creating file failed", msg)
            return
        try:
            with open(file_path, "w"):
                self._toolbox.msg.emit(
                    "File <b>{0}</b> created to Data Connection <b>{1}</b>".format(file_name, self.name)
                )
        except OSError:
            msg = "Please check directory permissions."
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Creating file failed", msg)
        return

    def remove_files(self):
        """Remove selected files from data directory."""
        indexes = self._properties_ui.treeView_dc_data.selectedIndexes()
        if not indexes:  # Nothing selected
            self._toolbox.msg.emit("Please select files to remove")
            return
        file_list = list()
        for index in indexes:
            file_at_index = self.data_model.itemFromIndex(index).data(Qt.DisplayRole)
            file_list.append(file_at_index)
        files = "\n".join(file_list)
        msg = (
            "The following files will be removed permanently from the project\n\n"
            "{0}\n\n"
            "Are you sure?".format(files)
        )
        # noinspection PyCallByClass, PyTypeChecker
        answer = QMessageBox.question(
            self._toolbox, "Remove {0} file(s)?".format(len(file_list)), msg, QMessageBox.Yes, QMessageBox.No
        )
        if not answer == QMessageBox.Yes:
            return
        for filename in file_list:
            path_to_remove = os.path.join(self.data_dir, filename)
            try:
                os.remove(path_to_remove)
                self._toolbox.msg.emit("File <b>{0}</b> removed".format(path_to_remove))
            except OSError:
                self._toolbox.msg_error.emit("Removing file {0} failed.\nCheck permissions.".format(path_to_remove))
        return

    def file_references(self):
        """Returns a list of paths to files that are in this item as references."""
        return self.references

    def data_files(self):
        """Returns a list of files that are in the data directory."""
        if not os.path.isdir(self.data_dir):
            return None
        files = list()
        with os.scandir(self.data_dir) as scan_iterator:
            for entry in scan_iterator:
                if entry.is_file():
                    files.append(entry.path)
        return files

    @Slot(name="refresh")
    def refresh(self):
        """Refresh data files in Data Connection Properties.
        NOTE: Might lead to performance issues."""
        d = self.data_files()
        self.populate_data_list(d)

    def populate_reference_list(self, items, emit_item_changed=True):
        """List file references in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.reference_model.clear()
        self.reference_model.setHorizontalHeaderItem(0, QStandardItem("References"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(item, Qt.ToolTipRole)
                qitem.setData(self._toolbox.style().standardIcon(QStyle.SP_FileLinkIcon), Qt.DecorationRole)
                self.reference_model.appendRow(qitem)
        if emit_item_changed:
            self.item_changed.emit()

    def populate_data_list(self, items):
        """List project internal data (files) in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.data_model.clear()
        self.data_model.setHorizontalHeaderItem(0, QStandardItem("Data"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                if item == 'datapackage.json':
                    qitem.setData(self.datapackage_icon, Qt.DecorationRole)
                else:
                    qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                full_path = os.path.join(self.data_dir, item)  # For drag and drop
                qitem.setData(full_path, Qt.UserRole)
                self.data_model.appendRow(qitem)
        self.item_changed.emit()

    def update_name_label(self):
        """Update Data Connection tab name label. Used only when renaming project items."""
        self._properties_ui.label_dc_name.setText(self.name)

    def execute(self):
        """Executes this Data Connection."""
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Data Connection <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        inst = self._toolbox.project().execution_instance
        # Update Data Connection based on project items that are already executed
        # Add previously executed Tool's output file paths to references
        self.references += inst.tool_output_files_at_sight(self.name)
        self.populate_reference_list(self.references, emit_item_changed=False)
        # Update execution instance for project items downstream
        # Add data file references and data files into execution instance
        refs = self.file_references()
        inst.append_dc_refs(self.name, refs)
        f_list = [os.path.join(self.data_dir, f) for f in self.data_files()]
        inst.append_dc_files(self.name, f_list)
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(0)  # 0 success

    def stop_execution(self):
        """Stops executing this Data Connection."""
        self._toolbox.msg.emit("Stopping {0}".format(self.name))
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-2)

    def simulate_execution(self, inst):
        """Simulates executing this Data Connection."""
        super().simulate_execution(inst)
        refs = self.file_references()
        inst.append_dc_refs(self.name, refs)
        f_list = [os.path.join(self.data_dir, f) for f in self.data_files()] if self.data_files() else []
        inst.append_dc_files(self.name, f_list)
        if not refs + f_list:
            self.add_notification(
                "This Data Connection does not have any references or data. "
                "Add some in the Data Connection Properties panel."
            )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        d["references"] = self.file_references()
        return d


def activate(toolbox):
    """Activate the plugin for using with given toolbox.

    Args:
        toolbox (ToolboxUI): activate the pluging for this toolbox
    """
    toolbox.item_categories["Data Connections"] = DataConnection
