#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
ProjectItem class.

:authors: P. Savolainen (VTT)
:date:   4.10.2018
"""

import logging
from metaobject import MetaObject


class ProjectItem(MetaObject):
    """Base class for all project items.

    Attributes:
        name (str): Object name
        description (str): Object description
        category (str): Name of parent category
        is_category (bool): True if the new instance should be a category item
    """
    def __init__(self, name, description, category, is_category=False):
        """Class constructor."""
        super().__init__(name, description)
        self._parent = None  # Parent ProjectItem
        self._children = list()  # List of child ProjectItems
        self.is_root = False
        self.is_category = False
        if category == "root":
            self.is_root = True
        elif is_category is True:
            self.is_category = True

    def parent(self):
        """Returns parent ProjectItem."""
        return self._parent

    def child_count(self):
        """Returns the number of child ProjectItems for this object."""
        return len(self._children)

    def child(self, row):
        """Returns child ProjectItem on given row."""
        try:
            item = self._children[row]
        except IndexError:
            logging.error("[{0}] has no child on row {1}".format(self.name, row))
            return None
        return item

    def add_child(self, child_item):
        """Append child project item as the last item in the children list.
        Set parent of this items parent as this item.

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
            logging.error("Trying to add '{0}' as the child of '{1}'".format(child_item.name, self.name))
            return False
        return True

    def remove_child(self, row):
        pass
