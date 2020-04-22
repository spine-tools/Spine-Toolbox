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
Data connection properties widget.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

import os
from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt, Slot, QUrl
from spinetoolbox.config import TREEVIEW_HEADER_SS
from .custom_menus import DcRefContextMenu, DcDataContextMenu


class DataConnectionPropertiesWidget(QWidget):
    """Widget for the Data Connection Item Properties."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): The toolbox instance where this widget should be embedded
        """
        from ..ui.data_connection_properties import Ui_Form

        super().__init__()
        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.treeView_dc_references.setStyleSheet(TREEVIEW_HEADER_SS)
        self.ui.treeView_dc_data.setStyleSheet(TREEVIEW_HEADER_SS)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Data Connection")
        # Class attributes
        self.dc_ref_context_menu = None
        self.dc_data_context_menu = None
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.treeView_dc_references.customContextMenuRequested.connect(self.show_references_context_menu)
        self.ui.treeView_dc_data.customContextMenuRequested.connect(self.show_data_context_menu)

    @Slot("QPoint", name="show_references_context_menu")
    def show_references_context_menu(self, pos):
        """Create and show a context-menu in data connection properties
        references view.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_dc_references.indexAt(pos)
        global_pos = self.ui.treeView_dc_references.viewport().mapToGlobal(pos)
        self.dc_ref_context_menu = DcRefContextMenu(self, global_pos, ind)
        option = self.dc_ref_context_menu.get_action()
        # Get selected Data Connection from project item model
        curr_index = self._toolbox.ui.treeView_project.currentIndex()
        leaf_item = self._toolbox.project_item_model.item(curr_index)
        if not leaf_item:
            self._toolbox.msg_error.emit("FIXME: Data Connection {0} not found in project item tree".format(curr_index))
            return
        dc = leaf_item.project_item
        if option == "Open containing directory...":
            ref_path = self.ui.treeView_dc_references.model().itemFromIndex(ind).data(Qt.DisplayRole)
            ref_dir = os.path.split(ref_path)[0]
            file_url = "file:///" + ref_dir
            self._toolbox.open_anchor(QUrl(file_url, QUrl.TolerantMode))
        elif option == "Edit...":
            dc.open_reference(ind)
        elif option == "Add reference(s)":
            dc.add_references()
        elif option == "Remove reference(s)":
            dc.remove_references()
        elif option == "Copy reference(s) to project":
            dc.copy_to_project()

    @Slot("QPoint", name="show_data_context_menu")
    def show_data_context_menu(self, pos):
        """Create and show a context-menu in data connection properties
        data view.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_dc_data.indexAt(pos)
        global_pos = self.ui.treeView_dc_data.viewport().mapToGlobal(pos)
        self.dc_data_context_menu = DcDataContextMenu(self, global_pos, ind)
        option = self.dc_data_context_menu.get_action()
        # Get selected Data Connection from project item model
        curr_index = self._toolbox.ui.treeView_project.currentIndex()
        leaf_item = self._toolbox.project_item_model.item(curr_index)
        if not leaf_item:
            self._toolbox.msg_error.emit("FIXME: Data Connection {0} not found in project items".format(curr_index))
            return
        dc = leaf_item.project_item
        if option == "New file...":
            dc.make_new_file()
        elif option == "Edit...":
            dc.open_data_file(ind)
        elif option == "Remove file(s)":
            dc.remove_files()
        elif option == "Open Spine Datapackage Editor":
            dc.show_spine_datapackage_form()
        elif option == "Open directory...":
            dc.open_directory()
        return
