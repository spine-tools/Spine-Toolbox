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
QWidget that is shown to user when opening Spine data model from a Data Store.
:author: Manuel Marin <manuelma@kth.se>
:date:   21.4.2018
"""

import os
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView
from PySide2.QtCore import Slot, Qt
from ui.Spine_data_explorer import Ui_Form
from config import STATUSBAR_SS
from models import MinimalTableModel
import logging


class SpineDataExplorerWidget(QWidget):
    """A widget to show and edit Spine objects in a data store."""

    def __init__(self, parent, data_store):
        """ Initialize class.

        Args:
            parent (ToolBoxUI): QMainWindow instance
            data_store (DataStore): A data store instance
        """
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self._parent = parent
        self._data_store = data_store
        self.object_parameters_model = MinimalTableModel()
        self.relationship_parameters_model = MinimalTableModel()
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # init ui
        self.ui.treeView_object.setModel(self._data_store.Spine_data_model)
        self.ui.tableView_object_parameters.setModel(self.object_parameters_model)
        self.ui.tableView_relationship_parameters.setModel(self.relationship_parameters_model)
        self.ui.tableView_object_parameters.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_relationship_parameters.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.treeView_object.expandAll()
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.pushButton_close.clicked.connect(self.close)
        self.ui.treeView_object.clicked.connect(self.reset_parameter_models)

    @Slot("QModelIndex", name="reset_parameter_models")
    def reset_parameter_models(self, index):
        """Populate tableViews whenever an object item is selected on the treeView"""
        # logging.debug("reset_parameter_models")
        # Read parameter data from item's UserRole
        item = self._data_store.Spine_data_model.itemFromIndex(index)
        parameter_data = item.data(Qt.UserRole)
        if parameter_data and item.parent(): # object item selected
            # Discover root item (ie database)
            root = item
            while root.parent():
                root = root.parent()
            # Read parameter names from root's UserRole
            parameter_names = root.data(Qt.UserRole)
            # Set headers
            self.object_parameters_model.header.clear()
            #self.object_parameters_model.header.append("parameter_entity_class_id")
            self.object_parameters_model.header.extend(parameter_names)
            self.relationship_parameters_model.header.clear()
            self.relationship_parameters_model.header.append("relationship_class_name")
            self.relationship_parameters_model.header.append("child_class_name")
            self.relationship_parameters_model.header.append("child_object_name")
            self.relationship_parameters_model.header.extend(parameter_names)
            # Reset models
            self.object_parameters_model.reset_model(parameter_data.object)
            self.relationship_parameters_model.reset_model(parameter_data.relationship)

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
