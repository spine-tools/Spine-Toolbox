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
BaseProjectItem and ProjectItem classes.

:authors: P. Savolainen (VTT)
:date:   4.10.2018
"""

import os
import logging
from PySide2.QtCore import Qt, Signal, QUrl
from PySide2.QtWidgets import QInputDialog
from PySide2.QtGui import QDesktopServices
from urllib.parse import urlparse
from widgets.custom_menus import CategoryProjectItemContextMenu, ProjectItemContextMenu
from metaobject import MetaObject
from helpers import create_dir


class BaseProjectItem(MetaObject):
    def __init__(self, name, description):
        """Base class for all project items.

        Args:
            name (str): Object name
            description (str): Object description
        """
        super().__init__(name, description)
        self._parent = None  # Parent BaseProjectItem. Set when add_child is called
        self._children = list()  # Child BaseProjectItems. Appended when new items are inserted into model.

    def flags(self):
        """Returns the item flags."""
        return Qt.NoItemFlags

    def parent(self):
        """Returns parent project item."""
        return self._parent

    def child_count(self):
        """Returns the number of child project items."""
        return len(self._children)

    def children(self):
        """Returns the children of this project item."""
        return self._children

    def child(self, row):
        """Returns child BaseProjectItem on given row.

        Args:
            row (int): Row of child to return

        Returns:
            BaseProjectItem on given row or None if it does not exist
        """
        try:
            item = self._children[row]
        except IndexError:
            logging.error("[%s] has no child on row %s", self.name, row)
            return None
        return item

    def row(self):
        """Returns the row on which this project item is located."""
        if self._parent is not None:
            r = self._parent.children().index(self)
            # logging.debug("{0} is on row:{1}".format(self.name, r))
            return r
        return 0

    def add_child(self, child_item):
        """Base method that shall be overridden in subclasses."""
        return False

    def remove_child(self, row):
        """Remove the child of this BaseProjectItem from given row. Do not call this method directly.
        This method is called by ProjectItemModel when items are removed.

        Args:
            row (int): Row of child to remove

        Returns:
            True if operation succeeded, False otherwise
        """
        if row < 0 or row > len(self._children):
            return False
        child = self._children.pop(row)
        child._parent = None
        return True

    def custom_context_menu(self, parent, pos):
        """Returns the context menu for this item. Implement in subclasses as needed.
        Args:
            parent (QWidget): The widget that is controlling the menu
            pos (QPoint): Position on screen
        """
        return NotImplemented

    def apply_context_menu_action(self, parent, action):
        """Applies given action from context menu. Implement in subclasses as needed.

        Args:
            parent (QWidget): The widget that is controlling the menu
            action (str): The selected action
        """


class RootProjectItem(BaseProjectItem):
    """Class for the root project item."""

    def __init__(self):
        super().__init__("root", "The Root Project Item.")

    def add_child(self, child_item):
        """Adds given category item as the child of this root project item. New item is added as the last item.

        Args:
            child_item (CategoryProjectItem): Item to add

        Returns:
            True for success, False otherwise
        """
        if isinstance(child_item, CategoryProjectItem):
            self._children.append(child_item)
            child_item._parent = self
            return True
        logging.error("You can only add a category item as a child of the root item")
        return False


class CategoryProjectItem(BaseProjectItem):
    """Class for category project items.

    Attributes:
        name (str): Category name
        description (str): Category description
        item_maker (function): A function for creating items in this category
        icon_maker (function): A function for creating icons (QGraphicsItems) for items in this category
        add_form_maker (function): A function for creating the form to add items to this category
        properties_ui (object): An object holding the Item Properties UI
    """

    def __init__(self, name, description, item_maker, icon_maker, add_form_maker, properties_ui):
        """Class constructor."""
        super().__init__(name, description)
        self._item_maker = item_maker
        self._icon_maker = icon_maker
        self._add_form_maker = add_form_maker
        self._properties_ui = properties_ui

    def flags(self):
        """Returns the item flags."""
        return Qt.ItemIsEnabled

    def item_maker(self):
        """Returns the item maker method."""
        return self._item_maker

    def add_child(self, child_item):
        """Adds given project item as the child of this category item. New item is added as the last item.

        Args:
            child_item (ProjectItem): Item to add

        Returns:
            True for success, False otherwise
        """
        if isinstance(child_item, ProjectItem):
            self._children.append(child_item)
            child_item._parent = self
            icon = self._icon_maker(child_item._toolbox, child_item.x - 35, child_item.y - 35, 70, 70, child_item.name)
            child_item.set_icon(icon)
            child_item.set_properties_ui(self._properties_ui)
            return True
        logging.error("You can only add a project item as a child of a category item")
        return False

    def custom_context_menu(self, parent, pos):
        """Returns the context menu for this item.

        Args:
            parent (QWidget): The widget that is controlling the menu
            pos (QPoint): Position on screen
        """
        return CategoryProjectItemContextMenu(parent, pos)

    def apply_context_menu_action(self, parent, action):
        """Applies given action from context menu. Implement in subclasses as needed.

        Args:
            parent (QWidget): The widget that is controlling the menu
            action (str): The selected action
        """
        if action == "Open project directory...":
            file_url = "file:///" + parent._project.project_dir
            parent.open_anchor(QUrl(file_url, QUrl.TolerantMode))
        else:  # No option selected
            pass


class ProjectItem(BaseProjectItem):
    """Class for project items that are not category nor root.
    These items can be executed, refreshed, and so on.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Item name
        description (str): Item description
        x (int): horizontal position in the screen
        y (int): vertical position in the screen
    """

    item_changed = Signal(name="item_changed")

    def __init__(self, toolbox, name, description, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.x = x
        self.y = y
        self._properties_ui = None
        self._icon = None
        self._sigs = None
        # Make project directory for this Item
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed." " Check permissions.".format(self.data_dir)
            )

    def flags(self):
        """Returns the item flags."""
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting.
        Must be implemented in subclasses.
        """
        return dict()

    def connect_signals(self):
        """Connect signals to handlers."""
        # NOTE: item_changed is not shared with other proj. items so there's no need to disconnect it
        self.item_changed.connect(lambda: self._toolbox.project().simulate_item_execution(self.name))
        for signal, handler in self._sigs.items():
            signal.connect(handler)

    def disconnect_signals(self):
        """Disconnect signals from handlers and check for errors."""
        for signal, handler in self._sigs.items():
            try:
                ret = signal.disconnect(handler)
            except RuntimeError:
                self._toolbox.msg_error.emit("RuntimeError in disconnecting <b>{0}</b> signals".format(self.name))
                logging.error("RuntimeError in disconnecting signal %s from handler %s", signal, handler)
                return False
            if not ret:
                self._toolbox.msg_error.emit("Disconnecting signal in {0} failed".format(self.name))
                logging.error("Disconnecting signal %s from handler %s failed", signal, handler)
                return False
        return True

    def set_properties_ui(self, properties_ui):
        self._properties_ui = properties_ui
        self._sigs = self.make_signal_handler_dict()

    def set_icon(self, icon):
        self._icon = icon

    def get_icon(self):
        """Returns the graphics item representing this item in the scene."""
        return self._icon

    def clear_notifications(self):
        """Clear all notifications from the exclamation icon."""
        self.get_icon().exclamation_icon.clear_notifications()

    def add_notification(self, text):
        """Add a notification to the exclamation icon."""
        self.get_icon().exclamation_icon.add_notification(text)

    def set_rank(self, rank):
        """Set rank of this item for displaying in the design view."""
        self.get_icon().rank_icon.set_rank(rank)

    def execute(self):
        """Executes this item."""

    def simulate_execution(self, inst):
        """Simulates executing this item."""
        self.clear_notifications()
        self.set_rank(inst.rank)

    def invalidate_workflow(self, edges):
        """Notifies that this item's workflow is not acyclic.

        Args:
            edges (list): A list of edges that make the graph acyclic after removing them.
        """
        edges = ["{0} -> {1}".format(*edge) for edge in edges]
        self.clear_notifications()
        self.set_rank("x")
        self.add_notification(
            "The workflow defined for this item has loops and thus cannot be executed. "
            "Possible fix: remove link(s) {0}.".format(", ".join(edges))
        )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        return {
            "short name": self.short_name,
            "description": self.description,
            "x": self.get_icon().sceneBoundingRect().center().x(),
            "y": self.get_icon().sceneBoundingRect().center().y(),
        }

    def custom_context_menu(self, parent, pos):
        """Returns the context menu for this item.

        Args:
            parent (QWidget): The widget that is controlling the menu
            pos (QPoint): Position on screen
        """
        return ProjectItemContextMenu(parent, pos)

    def apply_context_menu_action(self, parent, action):
        """Applies given action from context menu. Implement in subclasses as needed.

        Args:
            parent (QWidget): The widget that is controlling the menu
            action (str): The selected action
        """
        if action == "Open directory...":
            self.open_directory()
        elif action == "Rename":
            # noinspection PyCallByClass
            answer = QInputDialog.getText(
                self._toolbox,
                "Rename Item",
                "New name:",
                text=self.name,
                flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
            )
            if not answer[1]:
                pass
            else:
                new_name = answer[0]
                self.rename(new_name)
        elif action == "Remove item":
            delete_int = int(self._toolbox._qsettings.value("appSettings/deleteData", defaultValue="0"))
            delete_bool = delete_int != 0
            ind = self._toolbox.project_item_model.find_item(self.name)
            self._toolbox.remove_item(ind, delete_item=delete_bool, check_dialog=True)

    def rename(self, new_name):
        """Rename this item."""
        ind = self._toolbox.project_item_model.find_item(self.name)
        self._toolbox.project_item_model.setData(ind, new_name)

    def open_directory(self):
        """Open this item's data directory in file explorer."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    def tear_down(self):
        """Tears down this item. Called by toolbox just before closing.
        Implement in subclasses to eg close all QMainWindows opened by this item.
        """

    def update_name_label(self):
        """
        Updates the name label on the properties widget when renaming an item.

        Must be reimplemented by subclasses.
        """
        raise NotImplementedError()


class ProjectItemResource:
    """Class to hold a resource made available by a project item
    and that may be consumed by another project item."""

    def __init__(self, provider, type_, url="", data=None, metadata=None):
        """Init class.

        Args:
            provider (ProjectItem): The item that provides the resource
            type_ (str): The resource type, either "file", "database", or "data" (for now)
            url (str): The url of the resource
            data (object): The data in the resource
            metadata (dict): Some metadata providing extra information about the resource. For now it has two keys:
                - is_output (bool): whether the resource is an output from a process, e.g., a Tool ouput file
                - for_import (bool): whether the resource is data to be imported into a Spine db
        """
        self.provider = provider
        self.type_ = type_
        self.url = url
        self.parsed_url = urlparse(url)
        self.data = data
        if not metadata:
            metadata = dict()
        self.metadata = metadata

    @property
    def path(self):
        """Returns the resource path, as obtained from parsing the url."""
        return self.parsed_url.path

    @property
    def scheme(self):
        """Returns the resource scheme, as obtained from parsing the url."""
        return self.parsed_url.scheme
