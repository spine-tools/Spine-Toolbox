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
from urllib.parse import urlparse
from urllib.request import url2pathname
from PySide2.QtCore import Qt, Signal, QUrl
from PySide2.QtWidgets import QInputDialog
from PySide2.QtGui import QDesktopServices
from .executioner import ExecutionState
from .helpers import create_dir
from .metaobject import MetaObject
from .widgets.custom_menus import CategoryProjectItemContextMenu, ProjectItemContextMenu


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

    def flags(self):  # pylint: disable=no-self-use
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

    def add_child(self, child_item):  # pylint: disable=no-self-use
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
        raise NotImplementedError()

    def apply_context_menu_action(self, parent, action):
        """Applies given action from context menu. Implement in subclasses as needed.

        Args:
            parent (QWidget): The widget that is controlling the menu
            action (str): The selected action
        """
        raise NotImplementedError()


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
        x (float): horizontal position in the screen
        y (float): vertical position in the screen
    """

    item_changed = Signal(name="item_changed")

    def __init__(self, toolbox, name, description, x, y):
        """
        Args:
            toolbox (ToolboxUI): QMainWindow instance
            name (str): item name
            description (str): item description
            x (float): horizontal position on the scene
            y (float): vertical position on the scene
        """
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.x = x
        self.y = y
        self._properties_ui = None
        self._icon = None
        self._sigs = None
        self.item_changed.connect(lambda: self._toolbox.project().notify_items_in_same_dag_of_dag_changes(self.name))
        # Make project directory for this Item
        self.data_dir = os.path.join(self._project.project_items_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed." " Check permissions.".format(self.data_dir)
            )

    @staticmethod
    def item_type():
        """Item's type identifier string."""
        raise NotImplementedError()

    @staticmethod
    def category():
        """Item's category identifier string."""
        raise NotImplementedError()

    def flags(self):
        """Returns the item flags."""
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    # pylint: disable=no-self-use
    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting.
        Must be implemented in subclasses.
        """
        return dict()

    def connect_signals(self):
        """Connect signals to handlers."""
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
        if rank is not None:
            self.get_icon().rank_icon.set_rank(rank + 1)
        else:
            self.get_icon().rank_icon.set_rank("X")

    def execute(self, resources_upstream, resources_downstream):
        """
        Executes this item.

        Subclasses should overwrite the _do_execute() method to do actual work here.

        Args:
            resources_upstream (list): a list of ProjectItemResources available from upstream items
            resources_downstream (list): a list of ProjectItemResources available from downstream items
        """
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing {} <b>{}</b>".format(self.item_type(), self.name))
        self._toolbox.msg.emit("***")
        execution_state = self._do_execute(resources_upstream, resources_downstream)
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(execution_state)

    # pylint: disable=no-self-use
    def _do_execute(self, resources_upstream, resources_downstream):
        """
        Does the actual work during execution.

        The default implementation just returns ExecutionState.CONTINUE

        Args:
            resources_upstream (list): a list of ProjectItemResources available from upstream items
            resources_downstream (list): a list of ProjectItemResources available from downstream items
        Returns:
            ExecutionState to indicate the status of the execution
        """
        return ExecutionState.CONTINUE

    def handle_dag_changed(self, rank, resources_upstream):
        """
        Handles changes in the DAG.

        Subclasses should reimplement the _do_handle_dag_changes() method.

        Args:
            rank (int): item's execution order
            resources_upstream (list): resources available from upstream items
        """
        self.clear_notifications()
        self.set_rank(rank)
        self._do_handle_dag_changed(resources_upstream)

    def _do_handle_dag_changed(self, resources_upstream):
        """
        Handles changes in the DAG.

        Usually this entails validating the input resources and populating file references etc.
        The default implementation does nothing.

        Args:
            resources_upstream (list): resources available from upstream items
        """

    def invalidate_workflow(self, edges):
        """Notifies that this item's workflow is not acyclic.

        Args:
            edges (list): A list of edges that make the graph acyclic after removing them.
        """
        edges = ["{0} -> {1}".format(*edge) for edge in edges]
        self.clear_notifications()
        self.set_rank(None)
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
        if action == "Copy":
            self._toolbox.project_item_to_clipboard()
        elif action == "Paste":
            self._toolbox.project_item_from_clipboard()
        elif action == "Duplicate":
            self._toolbox.duplicate_project_item()
        elif action == "Open directory...":
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

    @staticmethod
    def default_name_prefix():
        """prefix for default item name"""
        raise NotImplementedError()

    def rename(self, new_name):
        """Renames this item. This is a common rename method for all Project items.
        If the project item needs any additional steps in renaming, override this
        method in subclass. See e.g. rename() method in DataStore class.

        Args:
            new_name(str): New name

        Returns:
            bool: True if renaming was successful, False if renaming fails
        """
        ind = self._toolbox.project_item_model.find_item(self.name)
        return self._toolbox.project_item_model.setData(ind, new_name)

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

    def notify_destination(self, source_item):
        """
        Informs an item that it has become the destination of a connection between two items.

        The default implementation logs a warning message. Subclasses should reimplement this if they need
        more specific behavior.

        Args:
            source_item (ProjectItem): connection source item
        """
        self._toolbox.msg_warning.emit(
            "Link established. Interaction between a "
            "<b>{0}</b> and a <b>{1}</b> has not been "
            "implemented yet.".format(source_item.item_type(), self.item_type())
        )

    # pylint: disable=no-self-use
    def available_resources_downstream(self, upstream_resources):
        """
        Returns available resources for downstream items.

        Should be reimplemented by subclasses if they want to offer resources
        to downstream items. The default implementation returns an empty list.

        Args:
            upstream_resources (list): a list of resources available from upstream items

        Returns:
            a list of ProjectItemResources
        """
        return list()

    # pylint: disable=no-self-use
    def available_resources_upstream(self):
        """
        Returns available resources for upstream items.

        Should be reimplemented by subclasses if they want to offer resources
        to upstream items. The default implementation returns an empty list.

        Returns:
            a list of ProjectItemResources
        """
        return list()


class ProjectItemResource:
    """Class to hold a resource made available by a project item
    and that may be consumed by another project item."""

    def __init__(self, provider, type_, url="", metadata=None):
        """Init class.

        Args:
            provider (ProjectItem): The item that provides the resource
            type_ (str): The resource type, either "file" or "database" (for now)
            url (str): The url of the resource
            metadata (dict): Some metadata providing extra information about the resource. For now it has two keys:
                - future (bool): whether the resource is from the future, e.g. Tool output files advertised beforehand
        """
        self.provider = provider
        self.type_ = type_
        self.url = url
        self.parsed_url = urlparse(url)
        if not metadata:
            metadata = dict()
        self.metadata = metadata

    def __eq__(self, other):
        if not isinstance(other, ProjectItemResource):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return (
            self.provider == other.provider
            and self.type_ == other.type_
            and self.url == other.url
            and self.metadata == other.metadata
        )

    def __repr__(self):
        result = "ProjectItemResource("
        result += f"provider={self.provider}, "
        result += f"type_={self.type_}, "
        result += f"url={self.url}, "
        result += f"metadata={self.metadata})"
        return result

    @property
    def path(self):
        """Returns the resource path in the local syntax, as obtained from parsing the url."""
        return url2pathname(self.parsed_url.path)

    @property
    def scheme(self):
        """Returns the resource scheme, as obtained from parsing the url."""
        return self.parsed_url.scheme
