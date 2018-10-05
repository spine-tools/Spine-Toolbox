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
    """
    def __init__(self, name, description, is_root=False, is_category=False):
        """Class constructor."""
        super().__init__(name, description)
        self.children = list()
        self.parent = None
        self.is_category = is_category
        self.is_root = is_root

    def add_child(self, child_item):
        """Append child project item as the last item in the children list."""
        if self.is_root:
            if child_item.is_category:
                self.children.append(child_item)
            else:
                logging.error("You can only add category items as a child of root")
                return False
        elif self.is_category:
            self.children.append(child_item)
        else:
            logging.error("Trying to add '{0}' as the child of '{1}'".format(child_item.name, self.name))
            return False
        return True

    def remove_child(self, row):
        pass