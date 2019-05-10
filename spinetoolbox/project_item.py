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
ProjectItem class.

:authors: P. Savolainen (VTT)
:date:   4.10.2018
"""

import logging
from metaobject import MetaObject


class ProjectItem(MetaObject):
    """Base class for all project items. Create root and category items by
    instantiating objects from this class.

    Attributes:
        name (str): Object name
        description (str): Object description
        is_root (bool): True if new item should be a root item
        is_category (bool): True if new item should be a category item
    """
    def __init__(self, name, description, is_root=False, is_category=False):
        """Class constructor."""
        super().__init__(name, description)
        self._parent = None  # Parent ProjectItem. Set when add_child is called
        self._children = list()  # Child ProjectItems. Appended when new items are inserted into model.
        self.is_root = is_root
        self.is_category = is_category

    def parent(self):
        """Returns parent project item."""
        return self._parent

    def child_count(self):
        """Returns the number of child project items for this object."""
        return len(self._children)

    def children(self):
        """Returns the children of this project item."""
        return self._children

    def child(self, row):
        """Returns child ProjectItem on given row.

        Args:
            row (int): Row of child to return

        Returns:
            ProjectItem on given row or None if it does not exist
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
        """Append child project item as the last item in the children list.
        Set parent of this items parent as this item. This method is called by
        ProjectItemModel when new items are added.

        Args:
            child_item (ProjectItem): Project item to add

        Returns:
            True if operation succeeded, False otherwise
        """
        if self.is_root:
            if child_item.is_category:
                self._children.append(child_item)
                child_item._parent = self
            else:
                logging.error("You can only add category items as a child of root")
                return False
        elif self.is_category:
            self._children.append(child_item)
            child_item._parent = self
        else:
            logging.error("Trying to add '%s' as the child of '%s'", child_item.name, self.name)
            return False
        return True

    def remove_child(self, row):
        """Remove the child of this ProjectItem from given row. Do not call this method directly.
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
