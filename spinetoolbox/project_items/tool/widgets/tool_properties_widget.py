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
Tool properties widget.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Slot
from spinetoolbox.config import TREEVIEW_HEADER_SS
from .custom_menus import ToolPropertiesContextMenu


class ToolPropertiesWidget(QWidget):
    """Widget for the Tool Item Properties.

    Args:
        toolbox (ToolboxUI): The toolbox instance where this widget should be embeded
    """

    def __init__(self, toolbox):
        """Init class."""
        from ..ui.tool_properties import Ui_Form

        super().__init__()
        self._toolbox = toolbox
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.treeView_specification.setStyleSheet(TREEVIEW_HEADER_SS)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Tool")
        # Class attributes
        self.tool_prop_context_menu = None
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self._toolbox.tool_specification_model_changed.connect(self.ui.comboBox_tool.setModel)
        self.ui.treeView_specification.customContextMenuRequested.connect(self.show_tool_properties_context_menu)

    @Slot("QPoint", name="show_tool_properties_context_menu")
    def show_tool_properties_context_menu(self, pos):
        """Create and show a context-menu in Tool properties
        if selected Tool has a Tool specification.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_specification.indexAt(
            pos
        )  # Index of selected QStandardItem in Tool properties tree view.
        curr_index = self._toolbox.ui.treeView_project.currentIndex()  # Get selected Tool
        tool = self._toolbox.project_item_model.item(curr_index).project_item
        if not tool.tool_specification():
            return
        # Find index of Tool specification
        name = tool.tool_specification().name
        tool_index = self._toolbox.tool_specification_model.tool_specification_index(name)
        global_pos = self.ui.treeView_specification.viewport().mapToGlobal(pos)
        self.tool_prop_context_menu = ToolPropertiesContextMenu(self, global_pos, ind)
        option = self.tool_prop_context_menu.get_action()
        if option == "Edit Tool specification":
            self._toolbox.edit_tool_specification(tool_index)  # index in tool specification model
        elif option == "Edit main program file...":
            self._toolbox.open_tool_main_program_file(tool_index)  # index in tool specification model
        elif option == "Open main program directory...":
            tool.open_tool_main_directory()
        elif option == "Open Tool specification file...":
            self._toolbox.open_tool_specification_file(tool_index)
        elif option == "Open directory...":
            tool.open_directory()
        return
