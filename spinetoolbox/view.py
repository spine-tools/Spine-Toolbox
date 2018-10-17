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
Module for view class.

:authors: P. Savolainen (VTT), M. Marin (KHT), J. Olauson (KTH)
:date:   14.07.2018
"""

import logging
from PySide2.QtCore import Qt, Slot, Signal
from PySide2.QtGui import QStandardItem, QStandardItemModel, QIcon, QPixmap
from project_item import ProjectItem
# from widgets.view_subwindow_widget import ViewWidget
from spinedatabase_api import DatabaseMapping, SpineDBAPIError
from widgets.network_map_widget import NetworkMapForm
from graphics_items import ViewImage
from helpers import busy_effect
from config import HEADER_POINTSIZE


class View(ProjectItem):
    """View class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """
    view_refresh_signal = Signal(name="view_refresh_signal")

    def __init__(self, toolbox, name, description, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "View"
        self._references = list()
        self.reference_model = QStandardItemModel()  # References to databases
        self.spine_ref_icon = QIcon(QPixmap(":/icons/Spine_db_ref_icon.png"))
        # self._widget = ViewWidget(self, self.item_type)
        # self._widget.make_header_for_references()
        self._graphics_item = ViewImage(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        # self.connect_signals()
        self.view_refresh_signal.connect(self.refresh)

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self.restore_selections()
        self._toolbox.ui.treeView_view.doubleClicked.connect(self.open_network_map)
        self._toolbox.ui.pushButton_open_network_map.clicked.connect(self.open_network_map)

    def disconnect_signals(self):
        """Disconnect signals of this item, so that the UI elements can be used again with another item."""
        self.save_selections()
        ret = True
        retvals = list()
        try:
            retvals.append(self._toolbox.ui.treeView_view.doubleClicked.disconnect(self.open_network_map))
            retvals.append(self._toolbox.ui.pushButton_open_network_map.clicked.disconnect(self.open_network_map))
            # retvals.append(self.view_refresh_signal.disconnect(self.refresh))
        except RuntimeError:
            self._toolbox.msg_error.emit("Runtime error in disconnecting <b>{0}</b> signals".format(self.name))
            ret = False
        if not all(retvals):
            self._toolbox.msg_error.emit("A signal in <b>{0}</b> was not disconnected properly<br/>{1}"
                                         .format(self.name, retvals))
            ret = False
        return ret

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""
        self._toolbox.ui.treeView_view.setModel(None)

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_view_name.setText(self.name)
        self._toolbox.ui.treeView_view.setModel(self.reference_model)
        self.refresh()

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this Data Store on the scene."""
        return self._graphics_item

    def references(self):
        """Returns a list of connection strings that are in this item as references."""
        return self._references

    def find_input_items(self):
        """Find input project items (only Data Stores now) that are connected to this View.

        Returns:
            List of Data Store items.
        """
        item_list = list()
        for input_item in self._toolbox.connection_model.input_items(self.name):
            found_index = self._toolbox.project_item_model.find_item(input_item)
            if not found_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(found_index)
            if item.item_type != "Data Store":
                continue
            item_list.append(item)
        return item_list

    def refresh(self):
        """Update the list of references that this item is viewing."""
        input_items = self.find_input_items()
        self._toolbox.msg.emit("Refreshing View {0}".format(self.name))
        self._references = [item.reference() for item in input_items if item.reference()]
        logging.debug("{0}".format(self._references))
        self.populate_reference_list(self._references)

    @busy_effect
    @Slot("QModelIndex", name="open_network_map")
    def open_network_map(self, index=None):
        """Open reference in Network Map form."""
        if not index:
            index = self._toolbox.ui.treeView_view.currentIndex()
        if len(self._references) == 0:
            self._toolbox.msg_warning.emit("No data to plot. Try connecting a Data Store here.")
            return
        if not index.isValid():
            # If only one reference available select it automatically
            if len(self._references) == 1:
                index = self._toolbox.ui.treeView_view.model().index(0, 0)
                self._toolbox.ui.treeView_view.setCurrentIndex(index)
            else:
                self._toolbox.msg_warning.emit("Please select a reference to plot")
                return
        reference = self._references[index.row()]
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

    def add_reference_header(self):
        """Add header to reference model."""
        h = QStandardItem("References")
        # Decrease font size
        font = h.font()
        font.setPointSize(HEADER_POINTSIZE)
        h.setFont(font)
        self.reference_model.setHorizontalHeaderItem(0, h)

    def populate_reference_list(self, items):
        """Add given list of items to the reference model. If None or
        an empty list given, the model is cleared."""
        self.reference_model.clear()
        self.add_reference_header()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item['database'])
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(item['url'], Qt.ToolTipRole)
                qitem.setData(self.spine_ref_icon, Qt.DecorationRole)
                self.reference_model.appendRow(qitem)

    # def update_tab(self):
    #     """Update Data Store tab with this item's information."""
    #     self._toolbox.ui.label_view_name.setText(self.name)
