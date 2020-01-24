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

from PySide2.QtCore import Qt, QMimeData, Signal, Slot
from PySide2.QtWidgets import (
    QToolBar,
    QLabel,
    QAction,
    QApplication,
    QButtonGroup,
    QPushButton,
    QWidget,
    QSizePolicy,
    QToolButton,
)
from PySide2.QtGui import QIcon, QDrag
from ..config import ICON_TOOLBAR_SS, PARAMETER_TAG_TOOLBAR_SS


class ItemToolBar(QToolBar):
    """A toolbar to add items using drag and drop actions."""

    # noinspection PyUnresolvedReferences, PyUnusedLocal
    def __init__(self, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Add Item Toolbar", parent=parent)  # Inherits stylesheet from ToolboxUI
        self._toolbox = parent
        label = QLabel("Drag & Drop Icon")
        self.addWidget(label)
        icon_size = 24
        # set remove all action
        remove_all_icon = QIcon(":/icons/menu_icons/trash-alt.svg").pixmap(icon_size, icon_size)
        remove_all = QToolButton(parent)
        remove_all.setIcon(remove_all_icon)
        remove_all.clicked.connect(self.remove_all)
        remove_all.setToolTip("Remove all items from project.")
        self.tool_separator = self.addSeparator()
        self.addWidget(remove_all)
        # Execute label and button
        self.addSeparator()
        ex_label = QLabel("Execute")
        self.addWidget(ex_label)
        execute_project_icon = QIcon(":/icons/project_item_icons/play-circle-solid.svg").pixmap(icon_size, icon_size)
        execute_project = QToolButton(parent)
        execute_project.setIcon(execute_project_icon)
        execute_project.clicked.connect(self.execute_project)
        execute_project.setToolTip("Execute project.")
        self.addWidget(execute_project)
        # ex_selected_label = QLabel("Execute Selected")
        # self.addWidget(ex_selected_label)
        execute_selected_icon = QIcon(":/icons/project_item_icons/play-circle-regular.svg").pixmap(icon_size, icon_size)
        execute_selected = QToolButton(parent)
        execute_selected.setIcon(execute_selected_icon)
        execute_selected.clicked.connect(self.execute_selected)
        execute_selected.setToolTip("Execute selection.")
        self.addWidget(execute_selected)
        self.addSeparator()
        stop_icon = QIcon(":/icons/project_item_icons/stop-circle-regular.svg").pixmap(icon_size, icon_size)
        stop = QToolButton(parent)
        stop.setIcon(stop_icon)
        stop.clicked.connect(self.stop_execution)
        stop.setToolTip("Stop execution.")
        self.addWidget(stop)
        # Set stylesheet
        self.setStyleSheet(ICON_TOOLBAR_SS)
        self.setObjectName("ItemToolbar")

    def add_draggable_widgets(self, category_icon):
        """Adds draggable widgets from the given list.

        Args:
            category_icon (list): List of tuples (item_type (str), item category (str), icon path (str))
        """
        widgets = list()
        for item_type, category, icon in category_icon:
            pixmap = QIcon(icon).pixmap(24, 24)
            widget = DraggableWidget(self, pixmap, item_type, category)
            widgets.append(widget)
        for widget in widgets:
            self.insertWidget(self.tool_separator, widget)

    @Slot(bool, name="remove_all")
    def remove_all(self, checked=False):
        """Slot for handling the remove all tool button clicked signal.
        Calls ToolboxUI remove_all_items() method."""
        self._toolbox.remove_all_items()

    @Slot(bool, name="execute_project")
    def execute_project(self, checked=False):
        """Slot for handling the Execute project tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().execute_project()
        return

    @Slot(bool, name="execute_selected")
    def execute_selected(self, checked=False):
        """Slot for handling the Execute selected tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().execute_selected()
        return

    @Slot(bool, name="stop_execution")
    def stop_execution(self, checked=False):
        """Slot for handling the Stop execution tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().stop()


class DraggableWidget(QLabel):
    """A draggable QLabel."""

    def __init__(self, parent, pixmap, item_type, category):
        """

        Args:
            parent (QWidget): Parent widget
            pixmap (QPixMap): Picture for the label
            item_type (str): Item type (e.g. Data Store, Data Connection, etc...)
            category (str): Item category (e.g. Data Stores, Data Connetions, etc...)
        """
        super().__init__(parent=parent)  # Parent passed to QLabel constructor. Inherits stylesheet from ToolboxUI.
        self.category = category
        self.setPixmap(pixmap)
        self.drag_start_pos = None
        self.setToolTip(
            "<p>Drag-and-drop this icon into the Design View to create a new <b>{}</b> item.</p>".format(item_type)
        )
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
        mime_data.setText(self.category)
        drag.setMimeData(mime_data)
        drag.setPixmap(self.pixmap())
        drag.setHotSpot(self.pixmap().rect().center())
        drag.exec_()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        self.drag_start_pos = None


class ParameterTagToolBar(QToolBar):
    """A toolbar to add items using drag and drop actions."""

    tag_button_toggled = Signal("QVariant", "bool")
    manage_tags_action_triggered = Signal("bool")

    def __init__(self, parent, db_mngr, *db_maps):
        """

        Args:
            parent (DataStoreForm): tree or graph view form
            db_mngr (SpineDBManager): the DB manager for interacting with the db
            db_maps (iter): DiffDatabaseMapping instances
        """
        super().__init__("Parameter Tag Toolbar", parent=parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        label = QLabel("Parameter tag")
        self.addWidget(label)
        self.tag_button_group = QButtonGroup(self)
        self.tag_button_group.setExclusive(False)
        self.actions = []
        self.db_map_ids = []
        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.empty_action = self.addWidget(empty)
        button = QPushButton("Manage tags...")
        self.addWidget(button)
        # noinspection PyUnresolvedReferences
        # pylint: disable=unnecessary-lambda
        button.clicked.connect(lambda checked: self.manage_tags_action_triggered.emit(checked))
        self.setStyleSheet(PARAMETER_TAG_TOOLBAR_SS)
        self.setObjectName("ParameterTagToolbar")

    def init_toolbar(self):
        for button in self.tag_button_group.buttons():
            self.tag_button_group.removeButton(button)
        for action in self.actions:
            self.removeAction(action)
        action = QAction("untagged")
        self.insertAction(self.empty_action, action)
        action.setCheckable(True)
        button = self.widgetForAction(action)
        self.tag_button_group.addButton(button, id=0)
        self.actions = [action]
        self.db_map_ids = [[(db_map, 0) for db_map in self.db_maps]]
        tag_data = {}
        for db_map in self.db_maps:
            for parameter_tag in self.db_mngr.get_parameter_tags(db_map):
                tag_data.setdefault(parameter_tag["tag"], {})[db_map] = parameter_tag["id"]
        for tag, db_map_data in tag_data.items():
            action = QAction(tag)
            self.insertAction(self.empty_action, action)
            action.setCheckable(True)
            button = self.widgetForAction(action)
            self.tag_button_group.addButton(button, id=len(self.db_map_ids))
            self.actions.append(action)
            self.db_map_ids.append(list(db_map_data.items()))
        self.tag_button_group.buttonToggled["int", "bool"].connect(
            lambda i, checked: self.tag_button_toggled.emit(self.db_map_ids[i], checked)
        )

    def receive_parameter_tags_added(self, db_map_data):
        for db_map, parameter_tags in db_map_data.items():
            self._add_db_map_tag_actions(db_map, parameter_tags)

    def _add_db_map_tag_actions(self, db_map, parameter_tags):
        action_texts = [a.text() for a in self.actions]
        for parameter_tag in parameter_tags:
            if parameter_tag["tag"] in action_texts:
                # Already a tag named after that, add db_map id information
                i = action_texts.index(parameter_tag["tag"])
                self.db_map_ids[i].append((db_map, parameter_tag["id"]))
            else:
                action = QAction(parameter_tag["tag"])
                self.insertAction(self.empty_action, action)
                action.setCheckable(True)
                button = self.widgetForAction(action)
                self.tag_button_group.addButton(button, id=len(self.db_map_ids))
                self.actions.append(action)
                self.db_map_ids.append([(db_map, parameter_tag["id"])])
                action_texts.append(action.text())

    def receive_parameter_tags_removed(self, db_map_data):
        for db_map, parameter_tags in db_map_data.items():
            parameter_tag_ids = {x["id"] for x in parameter_tags}
            self._remove_db_map_tag_actions(db_map, parameter_tag_ids)

    def _remove_db_map_tag_actions(self, db_map, parameter_tag_ids):
        for tag_id in parameter_tag_ids:
            i = next(k for k, x in enumerate(self.db_map_ids) if (db_map, tag_id) in x)
            self.db_map_ids[i].remove((db_map, tag_id))
            if not self.db_map_ids[i]:
                self.db_map_ids.pop(i)
                self.removeAction(self.actions.pop(i))

    def receive_parameter_tags_updated(self, db_map_data):
        for db_map, parameter_tags in db_map_data.items():
            self._update_db_map_tag_actions(db_map, parameter_tags)

    def _update_db_map_tag_actions(self, db_map, parameter_tags):
        for parameter_tag in parameter_tags:
            i = next(k for k, x in enumerate(self.db_map_ids) if (db_map, parameter_tag["id"]) in x)
            action = self.actions[i]
            action.setText(parameter_tag["tag"])
