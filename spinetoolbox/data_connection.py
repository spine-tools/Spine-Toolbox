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
Module for data connection class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.12.2017
"""

import os
import shutil
from PySide2.QtCore import Slot, QUrl
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QFileDialog
from metaobject import MetaObject
from widgets.sw_data_connection_widget import DataConnectionWidget
from helpers import create_dir
from config import APPLICATION_PATH


class DataConnection(MetaObject):
    """Data Connection class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        references (list): List of file references
    """
    def __init__(self, parent, name, description, project, references):
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Data Connection"
        self.item_category = "Data Connections"
        self._project = project
        self._widget = DataConnectionWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_references()
        self._widget.make_header_for_data()
        # Make directory for Data Connection
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        self.references = references
        try:
            create_dir(self.data_dir)
        except OSError:
            self._parent.msg_error.emit("[OSError] Creating directory {0} failed."
                                        " Check permissions.".format(self.data_dir))
        # Populate references model
        self._widget.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = os.listdir(self.data_dir)
        self._widget.populate_data_list(data_files)
        self.connect_signals()

    def connect_signals(self):
        """Connect this data connection's signals to slots."""
        self._widget.ui.pushButton_open.clicked.connect(self.open_directory)
        self._widget.ui.toolButton_plus.clicked.connect(self.add_references)
        self._widget.ui.toolButton_minus.clicked.connect(self.remove_references)
        self._widget.ui.toolButton_add.clicked.connect(self.copy_to_project)
        self._widget.ui.pushButton_connections.clicked.connect(self.show_connections)

    @Slot(name="open_directory")
    def open_directory(self):
        """Open file explorer in Data Connection data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._parent.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(name="add_references")
    def add_references(self):
        """Let user select references to files for this data connection."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileNames(self._widget, "Add file references", APPLICATION_PATH, "*.*")
        file_paths = answer[0]
        if not file_paths:  # Cancel button clicked
            return
        for path in file_paths:
            if path in self.references:
                self._parent.msg_warning.emit("Reference to file <b>{0}</b> already available".format(path))
                continue
            self.references.append(os.path.abspath(path))
        self._widget.populate_reference_list(self.references)

    @Slot(name="remove_references")
    def remove_references(self):
        """Remove selected references from reference list.
        Removes all references if nothing is selected.
        """
        indexes = self._widget.ui.treeView_references.selectedIndexes()
        if not indexes:  # Nothing selected
            self.references.clear()
            self._parent.msg.emit("All references removed")
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.references.pop(row)
            self._parent.msg.emit("Selected references removed")
        self._widget.populate_reference_list(self.references)

    @Slot(name="copy_to_project")
    def copy_to_project(self):
        """Copy files in the file reference list to project and update Data QTreeView."""
        if not self.references:
            self._parent.msg_warning.emit("No files to copy")
            return
        self._parent.msg.emit("Copying files to {0}".format(self.data_dir))
        for file_path in self.references:
            if not os.path.exists(file_path):
                self._parent.msg_error.emit("File <b>{0}</b> does not exist".format(file_path))
                continue
            src_dir, filename = os.path.split(file_path)
            self._parent.msg.emit("Copying file <b>{0}</b>".format(filename))
            try:
                shutil.copy(file_path, self.data_dir)
            except OSError:
                self._parent.msg_error.emit("[OSError] Copying failed")
                continue
        data_files = os.listdir(self.data_dir)
        self._widget.populate_data_list(data_files)

    @Slot(name="show_connections")
    def show_connections(self):
        """Show connections of this item."""
        inputs = self._parent.connection_model.input_items(self.name)
        outputs = self._parent.connection_model.output_items(self.name)
        self._parent.msg.emit("<br/><b>{0}</b>".format(self.name))
        self._parent.msg.emit("Input items")
        if not inputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in inputs:
                self._parent.msg_warning.emit("{0}".format(item))
        self._parent.msg.emit("Output items")
        if not outputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in outputs:
                self._parent.msg_warning.emit("{0}".format(item))

    def file_references(self):
        """Return a list of paths to files that are in this item as references (self.references)."""
        return self.references

    def data_files(self):
        """Return a list of files that are in the data directory."""
        return os.listdir(self.data_dir)

    def refresh(self):
        """Refresh data files QTreeView.
        NOTE: Might lead to performance issues."""
        d = os.listdir(self.data_dir)
        self._widget.populate_data_list(d)

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget
