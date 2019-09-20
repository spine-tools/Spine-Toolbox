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
Data interface properties widget.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from ..ui.data_interface_properties import Ui_Form
from .custom_menus import DiFilesContextMenu
from config import TREEVIEW_HEADER_SS


class DataInterfacePropertiesWidget(QWidget):
    """Widget for the Data Interface Item Properties.

    Args:
        toolbox (ToolboxUI): The toolbox instance where this widget should be embeded
    """

    def __init__(self, toolbox):
        """Init class."""
        super().__init__()
        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.treeView_data_interface_files.setStyleSheet(TREEVIEW_HEADER_SS)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Data Interface")
        # Class attributes
        self.di_files_context_menu = None
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.treeView_data_interface_files.customContextMenuRequested.connect(self.show_di_files_context_menu)

    @Slot("QPoint", name="show_di_files_context_menu")
    def show_di_files_context_menu(self, pos):
        """Create and show a context-menu in Data Interface properties source files view.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_data_interface_files.indexAt(pos)  # Index of selected item in DI references tree view.
        cur_index = self._toolbox.ui.treeView_project.currentIndex()  # Get selected DI
        di = self._toolbox.project_item_model.project_item(cur_index)
        global_pos = self.ui.treeView_data_interface_files.viewport().mapToGlobal(pos)
        self.di_files_context_menu = DiFilesContextMenu(self, global_pos, ind)
        option = self.di_files_context_menu.get_action()
        if option == "Open import editor":
            di.open_import_editor(ind)
        elif option == "Select connector type":
            di.select_connector_type(ind)
        elif option == "Open directory...":
            di.open_directory()
        return
