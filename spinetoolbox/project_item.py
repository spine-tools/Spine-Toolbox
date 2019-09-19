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

import logging
from metaobject import MetaObject
from PySide2.QtCore import Signal, Slot


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

    def __init__(self, name, description, item_maker):
        """Class for category project items.

        Args:
            name (str): Category name
            description (str): Category description
            item_maker (function): A method for creating items of this category
        """
        super().__init__(name, description)
        self._item_maker = item_maker

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
            return True
        logging.error("You can only add a project item as a child of a category item")
        return False


class ProjectItem(BaseProjectItem):

    item_changed = Signal(name="item_changed")
    """This is a class attribute."""

    def __init__(self, toolbox, name, description):
        """Class for project items that are not category nor root.
        These items can be executed, refreshed, and so on.

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            name (str): Item name
            description (str): Item description
        """
        super().__init__(name, description)
        self._toolbox = toolbox
        self._graphics_item = None

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

    def get_icon(self):
        """Returns the graphics item representing this item in the scene."""
        return self._graphics_item

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
