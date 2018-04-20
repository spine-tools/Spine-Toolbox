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
Module for data store class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   18.12.2017
"""

import os
import shutil
import pyodbc
import logging
from PySide2.QtGui import QStandardItemModel, QStandardItem
from metaobject import MetaObject
from widgets.data_store_subwindow_widget import DataStoreWidget
from helpers import create_dir, custom_getopenfilenames
from PySide2.QtCore import Slot


class DataStore(MetaObject):
    """Data Store class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        references (list): List of references (can be files or database references)
    """
    def __init__(self, parent, name, description, project, references):
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Data Store"
        self.item_category = "Data Stores"
        self._project = project
        self._widget = DataStoreWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_references()
        self._widget.make_header_for_data()
        # Make directory for Data Store
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
        #set connections buttons slot type
        self._widget.ui.toolButton_connector.is_connector = True
        self.connect_signals()

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.ui.pushButton_open.clicked.connect(self.open_directory)
        self._widget.ui.toolButton_plus.clicked.connect(self.add_references)
        #self._widget.ui.toolButton_minus.clicked.connect(self.remove_references)
        #self._widget.ui.toolButton_add.clicked.connect(self.copy_to_project)
        self._widget.ui.pushButton_connections.clicked.connect(self.show_connections)
        self._widget.ui.toolButton_connector.clicked.connect(self.draw_links)

    @Slot(name="draw_links")
    def draw_links(self):
        self._parent.ui.graphicsView.draw_links(self.sender())

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
        answer = custom_getopenfilenames(self._parent.ui.graphicsView, self._parent, "Add file references", APPLICATION_PATH, "*.*")
        file_paths = answer[0]
        if not file_paths:  # Cancel button clicked
            return
        for path in file_paths:
            if path in self.references:
                self._parent.msg_warning.emit("Reference to file <b>{0}</b> already available".format(path))
                continue
            self.references.append(os.path.abspath(path))
        self._widget.populate_reference_list(self.references)

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

    def data_references(self):
        """Return a list of paths to files and databases that are in this item as references (self.references)."""
        return self.references

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget
