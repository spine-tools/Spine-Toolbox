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
View properties widget.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from spinetoolbox.config import TREEVIEW_HEADER_SS
from .custom_menus import ViewPropertiesContextMenu


class ViewPropertiesWidget(QWidget):
    """Widget for the View Item Properties.

    Args:
        toolbox (ToolboxUI): The toolbox instance where this widget should be embeded
    """

    def __init__(self, toolbox):
        """Init class."""
        from ..ui.view_properties import Ui_Form

        super().__init__()
        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.treeView_view.setStyleSheet(TREEVIEW_HEADER_SS)
        toolbox.ui.tabWidget_item_properties.addTab(self, "View")
        # Class attributes
        self.view_prop_context_menu = None
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.treeView_view.customContextMenuRequested.connect(self.show_view_properties_context_menu)

    @Slot("QPoint", name="show_view_properties_context_menu")
    def show_view_properties_context_menu(self, pos):
        """Create and show a context-menu in View properties.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_view.indexAt(pos)  # Index of selected item in View references tree view.
        curr_index = self._toolbox.ui.treeView_project.currentIndex()  # Get selected View
        view = self._toolbox.project_item_model.item(curr_index).project_item
        global_pos = self.ui.treeView_view.viewport().mapToGlobal(pos)
        self.view_prop_context_menu = ViewPropertiesContextMenu(self, global_pos, ind)
        option = self.view_prop_context_menu.get_action()
        if option == "Open view":
            view.open_view()
        self.view_prop_context_menu.deleteLater()
        self.view_prop_context_menu = None
