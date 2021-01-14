######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Functions to make and handle QToolBars.

:author: P. Savolainen (VTT)
:date:   19.1.2018
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QToolBar, QLabel, QToolButton
from PySide2.QtGui import QIcon
from ..config import ICON_TOOLBAR_SS
from .project_item_drag import ProjectItemButton


class MainToolBar(QToolBar):
    """A toolbar to add items using drag and drop actions."""

    def __init__(self, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Add Item Toolbar", parent=parent)  # Inherits stylesheet from ToolboxUI
        self._toolbox = parent
        self.setStyleSheet(ICON_TOOLBAR_SS)
        self.setObjectName("ItemToolbar")
        self._project_item_buttons = []

    def setup(self):
        self.add_project_item_buttons()
        self.add_execute_buttons()

    def add_project_item_buttons(self):
        self.addWidget(QLabel("Items"))
        self._project_item_buttons = []
        for item_type, factory in self._toolbox.item_factories.items():
            icon = QIcon(factory.icon())
            button = ProjectItemButton(self._toolbox, icon, item_type, factory.supports_specifications())
            button.setIconSize(self.iconSize())
            self.addWidget(button)
            self._project_item_buttons.append(button)
        self.addSeparator()
        self._add_tool_button(
            QIcon(":/icons/wrench_plus.svg"), "Add specification from file...", self._toolbox.import_specification
        )

    def _add_tool_button(self, icon, tip, slot):
        button = QToolButton()
        button.setIcon(icon)
        button.setToolTip(f"<p>{tip}</p>")
        button.clicked.connect(slot)
        self.addWidget(button)

    def add_execute_buttons(self):
        self.addSeparator()
        self.addWidget(QLabel("Execute"))
        self._add_tool_button(
            QIcon(":/icons/menu_icons/play-circle-solid.svg"), "Execute project", self.execute_project
        )
        self._add_tool_button(
            QIcon(":/icons/menu_icons/play-circle-regular.svg"), "Execute selection", self.execute_selected
        )
        self._add_tool_button(
            QIcon(":/icons/menu_icons/stop-circle-regular.svg"), "Stop execution", self.stop_execution
        )

    @Slot(bool)
    def execute_project(self, checked=False):
        """Slot for handling the Execute project tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().execute_project()
        return

    @Slot(bool)
    def execute_selected(self, checked=False):
        """Slot for handling the Execute selected tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().execute_selected()
        return

    @Slot(bool)
    def stop_execution(self, checked=False):
        """Slot for handling the Stop execution tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().stop()
