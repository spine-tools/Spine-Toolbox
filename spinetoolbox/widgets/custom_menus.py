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
Classes for custom context menus.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   9.1.2018
"""

from PySide2.QtWidgets import QMenu, QTextBrowser
from PySide2.QtCore import Qt, SLOT
import sys
import logging


class CustomContextMenu(QMenu):
    """Context menu master class for several context menus."""
    def __init__(self):
        super().__init__()

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

class ProjectItemContextMenu(CustomContextMenu):
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
            self.add_action("Remove Item")
        self.exec_(position)

class ItemImageContextMenu(CustomContextMenu):
    """Context menu class for item images."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if index.isValid():
            self.add_action("Remove")
        self.exec_(position)


class LinkContextMenu(CustomContextMenu):
    """Context menu class for connection links."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if index.isValid():
            self.add_action("Remove")
        self.exec_(position)

class ToolTemplateContextMenu(CustomContextMenu):
    """Context menu class for tool templates."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if not index.isValid():
            # If no item at index
            pass
        elif index.row() == 0:
            # Don't show menu when clicking on No tool
            pass
        else:
            self.add_action("Open")
            self.add_action("Open in external editor")
            self.add_action("Open main program")
            self.add_action("Remove")
        self.exec_(position)


class ObjectTreeContextMenu(CustomContextMenu):
    """Context menu class for Data store form, object tree items."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if not index.isValid():
            return
        if not index.parent().isValid(): # root item
            self.add_action("New object class")
        else:
            item = index.model().itemFromIndex(index)
            item_type = item.data(Qt.UserRole)
            if item_type == 'object_class':
                self.add_action("New object class")
                self.add_action("New relationship class")
                self.add_action("New object")
            elif item_type == 'object':
                self.add_action("New parameter")
            elif item_type == 'relationship_class':
                self.add_action("New relationship class")
                self.add_action("New relationship")
            elif item_type == 'meta_relationship_class':
                self.add_action("New relationship")
            elif item_type == 'related_object':
                self.add_action("Expand at top level")
            self.add_action("Rename")
            self.add_action("Remove")
        self.exec_(position)


class ObjectParameterContextMenu(CustomContextMenu):
    """Context menu class for Data store form, object parameter items."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if not index.isValid():
            return
        self.add_action("New parameter")
        self.add_action("Remove")
        disabled = not (index.flags() & Qt.ItemIsEditable)
        self.add_action("Edit field", disabled=disabled)
        self.exec_(position)

    def add_action(self, text, disabled=False):
        """Adds an action to the context menu.

        Args:
            text (str): Text description of the action
        """
        action = self.addAction(text)
        if disabled:
            action.setEnabled(False)
        action.triggered.connect(lambda: self.set_action(text))


class ProcessOutputContextMenu(CustomContextMenu):
    """Popup menu class for add tool template button."""

    def __init__(self, parent, position):
        super().__init__()
        self._parent = parent
        menu = self._parent.ui.textBrowser_process_output.createStandardContextMenu()
        for action in menu.actions():
            self.addAction(action)
        self.addSeparator()
        self.option = "None"
        self.add_action("Clear")
        self.add_action("Issue Julia commands")
        self.exec_(position)


class addToolTemplatePopupMenu(QMenu):
    """Popup menu class for add tool template button."""

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        self.option = "None"
        # Open a tool template file
        action = self.addAction("Open", self._parent, SLOT("open_tool_template()"))
        # Show the Tool Template Form (empty)
        action = self.addAction("Create", self._parent, SLOT("show_tool_template_form()"))
