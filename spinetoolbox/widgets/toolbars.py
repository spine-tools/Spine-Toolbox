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
Functions to make and handle QToolBars.

:author: P. Savolainen (VTT)
:date:   19.1.2018
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QToolBar, QLabel, QToolButton
from PySide2.QtGui import QIcon
from ..config import ICON_TOOLBAR_SS
from .custom_qlistview import ProjectItemDragListView


class MainToolBar(QToolBar):
    """A toolbar to add items using drag and drop actions."""

    def __init__(self, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Add Item Toolbar", parent=parent)  # Inherits stylesheet from ToolboxUI
        self._toolbox = parent
        self.project_item_list_view = ProjectItemDragListView()
        self.project_item_spec_list_view = ProjectItemDragListView()
        self.setStyleSheet(ICON_TOOLBAR_SS)
        self.setObjectName("ItemToolbar")

    def setup(self):
        self.add_project_item_list_view()
        self.add_project_item_spec_list_view()
        self.add_execute_buttons()

    def add_project_item_list_view(self):
        self.addWidget(QLabel("Items"))
        self.project_item_list_view.add_to_toolbar(self)
        self.project_item_list_view.setModel(self._toolbox.project_item_factory_model)

    def add_project_item_spec_list_view(self):
        icon_size = 16
        self.addSeparator()
        self.addWidget(QLabel("Specifications"))
        self.project_item_spec_list_view.add_to_toolbar(self)
        remove_spec = QToolButton(self)
        remove_spec_icon = QIcon(":/icons/wrench_minus.svg").pixmap(icon_size, icon_size)
        remove_spec.setIcon(remove_spec_icon)
        remove_spec.clicked.connect(self._toolbox.remove_selected_specification)
        remove_spec.setToolTip("<html><head/><body><p>Remove selected specific item from the project</p></body></html>")
        self.addWidget(remove_spec)
        add_spec = QToolButton(self)
        add_spec_icon = QIcon(":/icons/wrench_plus.svg").pixmap(icon_size, icon_size)
        add_spec.setIcon(add_spec_icon)
        add_spec.setMenu(self._toolbox.add_specification_popup_menu)
        add_spec.setPopupMode(QToolButton.InstantPopup)
        add_spec.setToolTip("<html><head/><body><p>Add new specific item to the project</p></body></html>")
        self.addWidget(add_spec)

    def add_execute_buttons(self):
        icon_size = 24
        self.addSeparator()
        self.addWidget(QLabel("Execution"))
        execute_project_icon = QIcon(":/icons/menu_icons/play-circle-solid.svg").pixmap(icon_size, icon_size)
        execute_project = QToolButton(self)
        execute_project.setIcon(execute_project_icon)
        execute_project.clicked.connect(self.execute_project)
        execute_project.setToolTip("Execute project")
        execute_project.setFocusPolicy(Qt.StrongFocus)
        self.addWidget(execute_project)
        execute_selected_icon = QIcon(":/icons/menu_icons/play-circle-regular.svg").pixmap(icon_size, icon_size)
        execute_selected = QToolButton(self)
        execute_selected.setIcon(execute_selected_icon)
        execute_selected.clicked.connect(self.execute_selected)
        execute_selected.setToolTip("Execute selection")
        execute_selected.setFocusPolicy(Qt.StrongFocus)
        self.addWidget(execute_selected)
        stop_icon = QIcon(":/icons/menu_icons/stop-circle-regular.svg").pixmap(icon_size, icon_size)
        stop = QToolButton(self)
        stop.setIcon(stop_icon)
        stop.clicked.connect(self.stop_execution)
        stop.setToolTip("Stop execution")
        self.addWidget(stop)

    def add_remove_all_button(self):
        icon_size = 24
        remove_all_icon = QIcon(":/icons/menu_icons/trash-alt.svg").pixmap(icon_size, icon_size)
        remove_all = QToolButton(self)
        remove_all.setIcon(remove_all_icon)
        remove_all.clicked.connect(self.remove_all)
        remove_all.setToolTip("Remove all items from project.")
        self.addSeparator()
        self.addWidget(remove_all)

    @Slot(bool)
    def remove_all(self, checked=False):
        """Slot for handling the remove all tool button clicked signal.
        Calls ToolboxUI remove_all_items() method."""
        self._toolbox.remove_all_items()

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
