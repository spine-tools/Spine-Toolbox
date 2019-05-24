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
Functions to make and handle QToolBars.

:author: P. Savolainen (VTT)
:date:   19.1.2018
"""

from PySide2.QtCore import Qt, QMimeData, Signal, Slot
from PySide2.QtWidgets import QToolBar, QLabel, QAction, QApplication, QButtonGroup, \
    QPushButton, QWidget, QSizePolicy, QToolButton
from PySide2.QtGui import QIcon, QDrag
from config import ICON_TOOLBAR_SS, PARAMETER_TAG_TOOLBAR_SS


class ItemToolBar(QToolBar):
    """A toolbar to add items using drag and drop actions.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
    """
    # noinspection PyUnresolvedReferences, PyUnusedLocal
    def __init__(self, parent):
        """Init class."""
        super().__init__("Add Item Toolbar", parent=parent)  # Inherits stylesheet from ToolboxUI
        self._toolbox = parent
        label = QLabel("Drag & Drop Icon")
        self.addWidget(label)
        # DS
        data_store_pixmap = QIcon(":/icons/project_item_icons/database.svg").pixmap(24, 24)
        data_store_widget = DraggableWidget(self, data_store_pixmap, "Data Store")
        data_store_action = self.addWidget(data_store_widget)
        # DC
        data_connection_pixmap = QIcon(":/icons/project_item_icons/file-alt.svg").pixmap(24, 24)
        data_connection_widget = DraggableWidget(self, data_connection_pixmap, "Data Connection")
        data_connection_action = self.addWidget(data_connection_widget)
        # Tool
        tool_pixmap = QIcon(":/icons/project_item_icons/hammer.svg").pixmap(24, 24)
        tool_widget = DraggableWidget(self, tool_pixmap, "Tool")
        tool_action = self.addWidget(tool_widget)
        # View
        view_pixmap = QIcon(":/icons/project_item_icons/binoculars.svg").pixmap(24, 24)
        view_widget = DraggableWidget(self, view_pixmap, "View")
        view_action = self.addWidget(view_widget)
        # set remove all action
        remove_all_icon = QIcon(":/icons/menu_icons/trash-alt.svg").pixmap(24, 24)
        remove_all = QToolButton(parent)
        remove_all.setIcon(remove_all_icon)
        remove_all.clicked.connect(self.remove_all_clicked)
        self.addSeparator()
        self.addWidget(remove_all)
        # Execute label and button
        self.addSeparator()
        ex_label = QLabel("Execute Project")
        self.addWidget(ex_label)
        execute_project_icon = QIcon(":/icons/project_item_icons/play-circle-solid.svg").pixmap(24, 24)
        execute_project = QToolButton(parent)
        execute_project.setIcon(execute_project_icon)
        execute_project.clicked.connect(self.execute_project_clicked)
        self.addWidget(execute_project)
        ex_selected_label = QLabel("Execute Selected")
        self.addWidget(ex_selected_label)
        execute_selected_icon = QIcon(":/icons/project_item_icons/play-circle-regular.svg").pixmap(24, 24)
        execute_selected = QToolButton(parent)
        execute_selected.setIcon(execute_selected_icon)
        execute_selected.clicked.connect(self.execute_selected_clicked)
        self.addWidget(execute_selected)
        # Set stylesheet
        self.setStyleSheet(ICON_TOOLBAR_SS)
        self.setObjectName("ItemToolbar")

    @Slot(bool, name="remove_all_clicked")
    def remove_all_clicked(self, checked=False):
        """Slot for handling the remove all tool button clicked signal.
        Calls ToolboxUI remove_all_items() method."""
        self._toolbox.remove_all_items()

    @Slot(bool, name="execute_project_clicked")
    def execute_project_clicked(self, checked=False):
        """Slot for handling the Execute project tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().execute_project()
        return

    @Slot(bool, name="execute_selected_clicked")
    def execute_selected_clicked(self, checked=False):
        """Slot for handling the Execute selected tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().execute_selected()
        return


class DraggableWidget(QLabel):
    """A draggable QLabel.

    Attributes:
        parent (QWidget): Parent widget
        pixmap (QPixMap): Picture for the label
        text (str): Item type
    """
    def __init__(self, parent, pixmap, text):
        super().__init__(parent=parent)  # Parent passed to QFrame constructor. Inherits stylesheet from ToolboxUI.
        self.text = text
        self.setPixmap(pixmap)
        self.drag_start_pos = None
        self.setToolTip("""
            <p>Drag-and-drop this icon into the Design View to create a new <b>{}</b> item.</p>
        """.format(self.text))
        self.setAlignment(Qt.AlignHCenter)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def mousePressEvent(self, event):
        """Register drag start position"""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()

    # noinspection PyArgumentList, PyUnusedLocal
    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.text)
        drag.setMimeData(mime_data)
        drag.setPixmap(self.pixmap())
        drag.setHotSpot(self.pixmap().rect().center())
        drop_action = drag.exec_()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        self.drag_start_pos = None


class ParameterTagToolBar(QToolBar):
    """A toolbar to add items using drag and drop actions.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
    """

    tag_button_toggled = Signal("int", "bool", name="tag_button_toggled")
    manage_tags_action_triggered = Signal("bool", name="manage_tags_action_triggered")

    def __init__(self, parent, db_map):
        """Init class"""
        super().__init__("Parameter Tag Toolbar", parent=parent)
        self.db_map = db_map
        self.action_dict = {}
        self.filter_action_tool_tip = "<html>Check these buttons to filter parameters according to their tags.</html>"
        self.tag_button_group = QButtonGroup(self)
        self.tag_button_group.setExclusive(False)
        label = QLabel("Parameter tag")
        self.addWidget(label)
        action = self.addAction("untagged")
        action.setCheckable(True)
        action.setToolTip(self.filter_action_tool_tip)
        self.action_dict[0] = action
        button = self.widgetForAction(action)
        self.tag_button_group.addButton(button, id=0)
        for tag in self.db_map.parameter_tag_list():
            action = self.addAction(tag.tag)
            action.setCheckable(True)
            action.setToolTip(self.filter_action_tool_tip)
            self.action_dict[tag.id] = action
            button = self.widgetForAction(action)
            self.tag_button_group.addButton(button, id=tag.id)
        self.tag_button_group.buttonToggled["int", "bool"].\
            connect(lambda id, checked: self.tag_button_toggled.emit(id, checked))
        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.empty_action = self.addWidget(empty)
        button = QPushButton("Manage tags...")
        self.addWidget(button)
        # noinspection PyUnresolvedReferences
        button.clicked.connect(lambda checked: self.manage_tags_action_triggered.emit(checked))
        self.setStyleSheet(PARAMETER_TAG_TOOLBAR_SS)
        self.setObjectName("ParameterTagToolbar")

    def add_tag_actions(self, parameter_tags):
        for tag in parameter_tags:
            action = QAction(tag.tag)
            self.insertAction(self.empty_action, action)
            action.setCheckable(True)
            action.setToolTip(self.filter_action_tool_tip)
            self.action_dict[tag.id] = action
            button = self.widgetForAction(action)
            self.tag_button_group.addButton(button, id=tag.id)

    def remove_tag_actions(self, parameter_tag_ids):
        for tag_id in parameter_tag_ids:
            action = self.action_dict[tag_id]
            self.removeAction(action)

    def update_tag_actions(self, parameter_tags):
        for tag in parameter_tags:
            action = self.action_dict[tag.id]
            action.setText(tag.tag)
