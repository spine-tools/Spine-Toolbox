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
Classes for custom context menus and pop-up menus.

:author: P. Savolainen (VTT)
:date:   9.1.2018
"""

import os
from PySide2.QtWidgets import QAction, QMenu, QWidgetAction
from PySide2.QtGui import QIcon
from PySide2.QtCore import Signal, Slot
from .custom_qwidgets import SimpleFilterWidget


class CustomContextMenu(QMenu):
    """Context menu master class for several context menus."""

    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.position = position
        self.option = "None"

    def add_action(self, text, icon=QIcon(), enabled=True):
        """Adds an action to the context menu.

        Args:
            text (str): Text description of the action
            icon (QIcon): Icon for menu item
            enabled (bool): Is action enabled?
        """
        action = self.addAction(icon, text)
        action.setEnabled(enabled)
        action.triggered.connect(lambda: self.set_action(text))

    def set_action(self, option):
        """Sets the action which was clicked.

        Args:
            option (str): string with the text description of the action
        """
        self.option = option

    def get_action(self):
        """Returns the clicked action, a string with a description."""
        self.exec_(self.position)
        return self.option


class CategoryProjectItemContextMenu(CustomContextMenu):
    """Context menu for category project items in the QTreeView."""

    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.add_action("Open project directory...")


class ProjectItemModelContextMenu(CustomContextMenu):
    """Context menu for project item model in the QTreeView."""

    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.add_action("Open project directory...")
        self.addSeparator()
        self.add_action("Export project to GraphML")


class ProjectItemContextMenu(CustomContextMenu):
    """Context menu for project items in the Project tree widget and in the Design View."""

    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.add_action("Copy")
        self.add_action("Paste")
        self.add_action("Duplicate")
        self.addSeparator()
        self.add_action("Open directory...")
        self.addSeparator()
        self.add_action("Rename")
        self.add_action("Remove item")


class LinkContextMenu(CustomContextMenu):
    """Context menu class for connection links."""

    def __init__(self, parent, position, link):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
            link (Link(QGraphicsPathItem)): Link that requested the menu
        """
        super().__init__(parent, position)
        self.add_action("Remove connection")
        self.add_action("Take connection")
        if link.has_parallel_link():
            self.add_action("Send to bottom")


class OpenProjectDialogComboBoxContextMenu(CustomContextMenu):
    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.add_action("Clear history")


class CustomPopupMenu(QMenu):
    """Popup menu master class for several popup menus."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget of this pop-up menu
        """
        super().__init__(parent=parent)
        self._parent = parent

    def add_action(self, text, slot, enabled=True, tooltip=None):
        """Adds an action to the popup menu.

        Args:
            text (str): Text description of the action
            slot (method): Method to connect to action's triggered signal
            enabled (bool): Is action enabled?
            tooltip (str): Tool tip for the action
        """
        action = self.addAction(text)
        action.setEnabled(enabled)
        action.triggered.connect(slot)
        if tooltip is not None:
            action.setToolTip(tooltip)


class AddSpecificationPopupMenu(CustomPopupMenu):
    """Popup menu class for add Tool specification button."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget (ToolboxUI)
        """
        super().__init__(parent)
        # Open empty Tool specification Form
        self.add_action("Add Specification from file...", parent.import_specification)
        self.addSeparator()
        for item_type, factory in parent.item_factories.items():
            if not factory.supports_specifications():
                continue
            # Pass item_type as keyword argument so it's not a cell variable
            self.add_action(
                f"Create {item_type} Specification...",
                lambda checked=False, item_type=item_type: parent.show_specification_form(
                    item_type, specification=None
                ),
            )


class ItemSpecificationMenu(CustomPopupMenu):
    """Context menu class for item specifications."""

    def __init__(self, parent, index):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
            index (QModelIndex): the index
        """
        super().__init__(parent)
        self.index = index
        self.add_action("Edit specification", lambda: parent.edit_specification(index))
        self.add_action("Remove specification", lambda: parent.remove_specification(index.row()))
        self.add_action("Open specification file...", lambda: parent.open_specification_file(index))
        self.addSeparator()


class RecentProjectsPopupMenu(CustomPopupMenu):
    """Recent projects menu embedded to 'File-Open recent' QAction."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget of this menu (ToolboxUI)
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.setToolTipsVisible(True)
        self.add_recent_projects()

    def add_recent_projects(self):
        """Reads the previous project names and paths from QSettings. Adds them to the QMenu as QActions."""
        recents = self._parent.qsettings().value("appSettings/recentProjects", defaultValue=None)
        if recents:
            recents = str(recents)
            recents_list = recents.split("\n")
            for entry in recents_list:
                name, filepath = entry.split("<>")
                self.add_action(
                    name,
                    lambda checked=False, filepath=filepath: self.call_open_project(checked, filepath),
                    tooltip=filepath,
                )

    @Slot(bool, str)
    def call_open_project(self, checked, p):
        """Slot for catching the user selected action from the recent projects menu.

        Args:
            checked (bool): Argument sent by triggered signal
            p (str): Full path to a project file
        """
        if not os.path.exists(p):
            # Project has been removed, remove it from recent projects list
            self._parent.remove_path_from_recent_projects(p)
            self._parent.msg_error.emit(
                "Opening selected project failed. Project file <b>{0}</b> may have been removed.".format(p)
            )
            return
        # Check if the same project is already open
        if self._parent.project():
            if p == self._parent.project().project_dir:
                self._parent.msg.emit("Project already open")
                return
        if not self._parent.open_project(p):
            return


class FilterMenuBase(QMenu):
    """Filter menu."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): a parent widget
        """
        super().__init__(parent)
        self._remove_filter = QAction('Remove filters', None)
        self._filter = None
        self._filter_action = None
        self.addAction(self._remove_filter)

    def connect_signals(self):
        self.aboutToShow.connect(self._check_filter)
        self._remove_filter.triggered.connect(self._clear_filter)
        self._filter.okPressed.connect(self._change_filter)
        self._filter.cancelPressed.connect(self.hide)

    def set_filter_list(self, data):
        self._filter.set_filter_list(data)

    def add_items_to_filter_list(self, items):
        self._filter._filter_model.add_items(items)
        self._filter.save_state()

    def remove_items_from_filter_list(self, items):
        self._filter._filter_model.remove_items(items)
        self._filter.save_state()

    def _clear_filter(self):
        self._filter.clear_filter()
        self._change_filter()

    def _check_filter(self):
        self._remove_filter.setEnabled(self._filter.has_filter())

    def _change_filter(self):
        valid_values = set(self._filter._filter_state)
        if self._filter._filter_empty_state:
            valid_values.add(None)
        self.emit_filter_changed(valid_values)
        self.hide()

    def emit_filter_changed(self, valid_values):
        raise NotImplementedError()

    def wipe_out(self):
        self._filter._filter_model.set_list(set())
        self.deleteLater()


class SimpleFilterMenu(FilterMenuBase):

    filterChanged = Signal(set)

    def __init__(self, parent, show_empty=True):
        """
        Args:
            parent (SpineDBEditor)
        """
        super().__init__(parent)
        self._filter = SimpleFilterWidget(self, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.connect_signals()

    def emit_filter_changed(self, valid_values):
        self.filterChanged.emit(valid_values)
