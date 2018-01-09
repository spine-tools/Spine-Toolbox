#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
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
Classes for custom context menus.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   9.1.2018
"""

from PySide2.QtWidgets import QMenu


class ProjectItemContextMenu(QMenu):
    """Context menu class for project items."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if not index.isValid():
            # If no item at index
            pass
        elif not index.parent().isValid():
            # If index is at a category item
            pass
        else:
            self.add_action("Remove")
            self.exec_(position)

    def add_action(self, text):
        """Adds an action to the context menu.

        Args:
            text (str): Text description of the action
        """
        action = self.addAction(text)
        action.triggered.connect(lambda: self.set_action(text))

    def set_action(self, option):
        """Sets the action which was clicked.

        Args:
            option (str): string with the text description of the action
        """
        self.option = option

    def get_action(self):
        """Returns the clicked action, a string with a description."""
        return self.option
