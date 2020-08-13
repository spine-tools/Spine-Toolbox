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
Combiner properties widget.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   12.9.2019
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from spinetoolbox.config import TREEVIEW_HEADER_SS
from .custom_menus import CombinerPropertiesContextMenu


class CombinerPropertiesWidget(QWidget):
    """Widget for the Combiner Project Item Properties.

    Args:
        toolbox (ToolboxUI): The toolbox instance where this widget should be embedded
    """

    def __init__(self, toolbox):
        """Init class."""
        from ..ui.combiner_properties import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__()
        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.treeView_files.setStyleSheet(TREEVIEW_HEADER_SS)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Combiner")
        # Class attributes
        self.properties_context_menu = None
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.treeView_files.customContextMenuRequested.connect(self.show_combiner_properties_context_menu)

    @Slot("QPoint")
    def show_combiner_properties_context_menu(self, pos):
        """Create and show a context-menu in Combiner properties.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_files.indexAt(pos)  # Index of selected item in Combiner references tree view.
        curr_index = self._toolbox.ui.treeView_project.currentIndex()  # Get selected Combiner
        combiner = self._toolbox.project_item_model.item(curr_index).project_item
        global_pos = self.ui.treeView_files.viewport().mapToGlobal(pos)
        self.properties_context_menu = CombinerPropertiesContextMenu(self, global_pos, ind)
        option = self.properties_context_menu.get_action()
        if option == "Open editor":
            combiner.open_db_editor()
        self.properties_context_menu.deleteLater()
        self.properties_context_menu = None
