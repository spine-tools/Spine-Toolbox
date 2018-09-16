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
Module for view class.

:authors: P. Savolainen (VTT), M. Marin (KHT), J. Olauson (KTH)
:date:   14.07.2018
"""

import os
import shutil
import getpass
import logging
from PySide2.QtCore import Qt, Slot
from metaobject import MetaObject
from widgets.view_subwindow_widget import ViewWidget
from spinedatabase_api import DatabaseMapping, SpineDBAPIError
from widgets.network_map_widget import NetworkMapForm
from graphics_items import ViewImage
from helpers import busy_effect


class View(MetaObject):
    """View class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """
    def __init__(self, toolbox, name, description, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "View"
        self.item_category = "Views"
        self.references = list()
        self._widget = ViewWidget(self, self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_references()
        # Populate data (files) model
        self._graphics_item = ViewImage(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self.connect_signals()

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.ui.treeView_references.doubleClicked.connect(self.open_network_map)
        self._widget.ui.pushButton_open_network_map.clicked.connect(self.open_network_map)

    def project(self):
        """Returns current project or None if no project open."""
        return self._project

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this Data Store on the scene."""
        return self._graphics_item

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    def find_input_items(self):
        """Find input items of this View.

        Returns:
            List of Data Store items.
        """
        item_list = list()
        for input_item in self._toolbox.connection_model.input_items(self.name):
            found_item = self._toolbox.project_item_model.find_item(input_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item_data = found_item.data(Qt.UserRole)
            if item_data.item_type != "Data Store":
                continue
            item_list.append(item_data)
        return item_list

    def refresh(self):
        """Update list of references that this item is viewing."""
        input_items = self.find_input_items()
        self.references = [item.reference() for item in input_items if item.reference()]
        if not self.references:
            return
        self._widget.populate_reference_list(self.references)

    @busy_effect
    @Slot("QModelIndex", name="open_network_map")
    def open_network_map(self, index=None):
        """Open reference in Network Map form."""
        if not index:
            index = self._widget.ui.treeView_references.currentIndex()
        if not index.isValid():
            logging.error("Index not valid")
            return
        reference = self.references[index.row()]
        db_url = reference['url']
        database = reference['database']
        username = reference['username']
        try:
            mapping = DatabaseMapping(db_url, username)
        except SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            return
        network_map_form = NetworkMapForm(self._toolbox, self, mapping)
        network_map_form.show()

    def data_references(self):
        """Returns a list of connection strings that are in this item as references (self.references)."""
        return self.references
