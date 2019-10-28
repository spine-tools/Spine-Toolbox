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
import pathlib
from PySide2.QtCore import Slot, QUrl, QFileSystemWatcher, Qt, QFileInfo
from PySide2.QtGui import QDesktopServices, QStandardItem, QStandardItemModel, QIcon, QPixmap
from PySide2.QtWidgets import QFileDialog, QStyle, QFileIconProvider, QInputDialog, QMessageBox
from spinetoolbox.project_item import ProjectItem, ProjectItemResource
from spinetoolbox.widgets.spine_datapackage_widget import SpineDatapackageWidget
from spinetoolbox.helpers import busy_effect
from spinetoolbox.config import APPLICATION_PATH, INVALID_FILENAME_CHARS


class DataConnection(ProjectItem):
    def __init__(self, toolbox, name, description, x, y, references=None):
        """Data Connection class.

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            name (str): Object name
            description (str): Object description
            x (float): Initial X coordinate of item icon
            y (float): Initial Y coordinate of item icon
            references (list): List of file references
        """
        super().__init__(toolbox, "Data Connection", name, description, x, y)
        self.reference_model = QStandardItemModel()  # References to files
        self.data_model = QStandardItemModel()  # Paths of project internal files. These are found in DC data directory
        self.datapackage_icon = QIcon(QPixmap(":/icons/datapkg.png"))
        self.data_dir_watcher = QFileSystemWatcher(self)
        if os.path.isdir(self.data_dir):
            self.data_dir_watcher.addPath(self.data_dir)
        # Populate references model
        if references is None:
            references = list()
        self.references = references
        self.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = self.data_files()
        self.populate_data_list(data_files)
        self.spine_datapackage_form = None

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = super().make_signal_handler_dict()
        # pylint: disable=unnecessary-lambda
        s[self._properties_ui.toolButton_dc_open_dir.clicked] = lambda checked=False: self.open_directory()
        s[self._properties_ui.toolButton_plus.clicked] = self.add_references
        s[self._properties_ui.toolButton_minus.clicked] = self.remove_references
        s[self._properties_ui.toolButton_add.clicked] = self.copy_to_project
        s[self._properties_ui.pushButton_datapackage.clicked] = self.show_spine_datapackage_form
        s[self._properties_ui.treeView_dc_references.doubleClicked] = self.open_reference
        s[self._properties_ui.treeView_dc_data.doubleClicked] = self.open_data_file
        s[self.data_dir_watcher.directoryChanged] = self.refresh
        s[self._properties_ui.treeView_dc_references.files_dropped] = self.add_files_to_references
        s[self._properties_ui.treeView_dc_data.files_dropped] = self.add_files_to_data_dir
        s[self.get_icon().files_dropped_on_icon] = self.receive_files_dropped_on_icon
        s[self._properties_ui.treeView_dc_references.del_key_pressed] = lambda: self.remove_references()
        s[self._properties_ui.treeView_dc_data.del_key_pressed] = lambda: self.remove_files()
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

    @Slot("QGraphicsItem", list)
    def receive_files_dropped_on_icon(self, icon, file_paths):
        """Called when files are dropped onto a data connection graphics item.
        If the item is this Data Connection's graphics item, add the files to data."""
        if icon == self.get_icon():
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
        title = "Remove {0} File(s)".format(len(file_list))
        message_box = QMessageBox(
            QMessageBox.Question, title, msg, QMessageBox.Ok | QMessageBox.Cancel, parent=self._toolbox
        )
        message_box.button(QMessageBox.Ok).setText("Remove Files")
        answer = message_box.exec_()
        if answer == QMessageBox.Cancel:
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
            return []
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

    def resources_for_advertising(self):
        """Returns list of references and files to advertise to the execution instance."""
        refs = self.file_references()
        f_list = [os.path.join(self.data_dir, f) for f in self.data_files()]
        resources = [ProjectItemResource(self, "file", url=pathlib.Path(ref).as_uri()) for ref in refs]
        resources += [ProjectItemResource(self, "file", url=pathlib.Path(path).as_uri()) for path in f_list]
        return resources

    def execute(self):
        """Executes this Data Connection."""
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Data Connection <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        inst = self._toolbox.project().execution_instance
        # Update Data Connection based on project items that are already executed
        # Add previously executed Tool's output file paths to references
        tool_output_files = [
            r.path for r in inst.available_resources(self.name) if r.type_ == "file" and r.metadata.get("is_output")
        ]
        self.references += tool_output_files
        self.populate_reference_list(self.references, emit_item_changed=False)
        # Update execution instance for project items downstream
        # Add data file references and data files into execution instance
        resources = self.resources_for_advertising()
        inst.advertise_resources(self.name, *resources)
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(0)  # 0 success

    def stop_execution(self):
        """Stops executing this Data Connection."""
        self._toolbox.msg.emit("Stopping {0}".format(self.name))
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-2)

    def simulate_execution(self, inst):
        """Simulates executing this Data Connection."""
        super().simulate_execution(inst)
        resources = self.resources_for_advertising()
        inst.advertise_resources(self.name, *resources)
        if not resources:
            self.add_notification(
                "This Data Connection does not have any references or data. "
                "Add some in the Data Connection Properties panel."
            )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        d["references"] = self.file_references()
        return d

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
        self.data_dir_watcher.removePaths(self.data_dir_watcher.directories())
        self.data_dir_watcher.addPath(self.data_dir)
        return True

    def tear_down(self):
        """Tears down this item. Called by toolbox just before closing.
        Closes the SpineDatapackageWidget instances opened."""
        if self.spine_datapackage_form:
            self.spine_datapackage_form.close()
        watched_paths = self.data_dir_watcher.directories()
        if watched_paths:
            self.data_dir_watcher.removePaths(watched_paths)
        self.data_dir_watcher.deleteLater()

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type == "Tool":
            self._toolbox.msg.emit(
                "Link established. Tool <b>{0}</b> output files will be "
                "passed as references to item <b>{1}</b> after execution.".format(source_item.name, self.name)
            )
        elif source_item.item_type in ["Data Store", "Data Interface"]:
            # Does this type of link do anything?
            self._toolbox.msg.emit("Link established.")
        else:
            super().notify_destination(source_item)

    @staticmethod
    def default_name_prefix():
        """see base class"""
        return "Data Connection"
