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
from ..helpers import make_icon_toolbar_ss
from .project_item_drag import ProjectItemButton, PluginProjectItemSpecButton


class PluginToolBar(QToolBar):
    """A plugin toolbar."""

    def __init__(self, name, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__(name, parent=parent)  # Inherits stylesheet from ToolboxUI
        self._name = name
        self._toolbox = parent
        self.setObjectName(name.replace(" ", "_"))

    def setup(self, plugin_specs):
        self.addWidget(QLabel(self._name))
        for spec in plugin_specs:
            factory = self._toolbox.item_factories[spec.item_type]
            icon = QIcon(factory.icon())
            button = PluginProjectItemSpecButton(self._toolbox, icon, spec.item_type, spec.name)
            button.setIconSize(self.iconSize())
            self.addWidget(button)

    def set_color(self, color):
        self.setStyleSheet(make_icon_toolbar_ss(color))


class MainToolBar(QToolBar):
    """The main application toolbar: Items | Execute"""

    def __init__(self, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Main Toolbar", parent=parent)  # Inherits stylesheet from ToolboxUI
        self._toolbox = parent
        self.setObjectName("Main_Toolbar")
        self.execute_project_button = None
        self.execute_selection_button = None
        self.stop_execution_button = None
        self._project_item_butoons = []

    def set_color(self, color):
        self.setStyleSheet(make_icon_toolbar_ss(color))
        for button in self._project_item_butoons:
            button.set_menu_color(color)

    def setup(self):
        self.add_project_item_buttons()
        self.add_execute_buttons()

    def add_project_item_buttons(self):
        self._project_item_butoons = []
        self.addWidget(QLabel("Main"))
        for item_type, factory in self._toolbox.item_factories.items():
            icon = QIcon(factory.icon())
            button = ProjectItemButton(self._toolbox, icon, item_type)
            button.setIconSize(self.iconSize())
            self.addWidget(button)
            self._project_item_butoons.append(button)
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
        return button

    def add_execute_buttons(self):
        self.addSeparator()
        self.addWidget(QLabel("Execute"))
        self.execute_project_button = self._add_tool_button(
            QIcon(":/icons/menu_icons/play-circle-solid.svg"), "Execute project", self.execute_project
        )
        self.execute_selection_button = self._add_tool_button(
            QIcon(":/icons/menu_icons/play-circle-regular.svg"), "Execute selection", self.execute_selected
        )
        self.stop_execution_button = self._add_tool_button(
            QIcon(":/icons/menu_icons/stop-circle-regular.svg"), "Stop execution", self.stop_execution
        )
        self.execute_project_button.setEnabled(False)  # Will become enabled when user adds items
        self.execute_selection_button.setEnabled(False)  # Will become enabled when user selects something
        self.stop_execution_button.setEnabled(False)  # Will become enabled when user executes something

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
