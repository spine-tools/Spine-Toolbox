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
            return
        if not index.parent().isValid():
            # If index is at a category item
            return
        self.add_action("Remove Item")
        self.exec_(position)

class ItemImageContextMenu(CustomContextMenu):
    """Context menu class for item images."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if not index.isValid():
            return
        self.add_action("Remove Item")
        self.exec_(position)


class LinkContextMenu(CustomContextMenu):
    """Context menu class for connection links."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if not index.isValid():
            return
        self.add_action("Remove Connection")
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
            return
        if index.row() == 0:
            # Don't show menu when clicking on No tool
            return
        self.add_action("Edit Tool Template")
        self.add_action("Remove Tool Template")
        self.addSeparator()
        self.add_action("Open main program file")
        self.add_action("Open descriptor file")
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
            self.add_action("Add object class")
        else:
            item = index.model().itemFromIndex(index)
            item_type = item.data(Qt.UserRole)
            if item_type == 'object_class':
                self.add_action("Add object class")
                self.add_action("Add relationship class")
                self.add_action("Add object")
                self.addSeparator()
                self.add_action("Add parameter")
                self.addSeparator()
                self.add_action("Rename object class")
                self.addSeparator()
                self.add_action("Remove object class")
            elif item_type == 'object':
                self.add_action("Add parameter value")
                self.addSeparator()
                self.add_action("Rename object")
                self.addSeparator()
                self.add_action("Remove object")
            elif item_type == 'relationship_class':
                self.add_action("Add relationship class")
                self.add_action("Add relationship")
                self.addSeparator()
                self.add_action("Add parameter")
                self.addSeparator()
                self.add_action("Rename relationship class")
                self.addSeparator()
                self.add_action("Remove relationship class")
            elif item_type == 'meta_relationship_class':
                self.add_action("Add relationship")
                self.addSeparator()
                self.add_action("Add parameter")
                self.addSeparator()
                self.add_action("Rename relationship class")
                self.addSeparator()
                self.add_action("Remove relationship class")
            elif item_type == 'related_object':
                self.add_action("Expand at top level")
                self.addSeparator()
                self.add_action("Add parameter value")
                self.addSeparator()
                self.add_action("Rename relationship")
                self.addSeparator()
                self.add_action("Remove relationship")
        self.exec_(position)


class ParameterValueContextMenu(CustomContextMenu):
    """Context menu class for object parameter value items in Data Store."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if not index.isValid():
            return
        #self.add_action("New parameter value")
        self.add_action("Remove parameter value")
        self.add_action("Edit field")
        self.exec_(position)


class ParameterContextMenu(CustomContextMenu):
    """Context menu class for object parameter items in Data Store."""

    def __init__(self, parent, position, index):
        super().__init__()
        self._parent = parent
        self.index = index
        self.option = "None"
        if not index.isValid():
            return
        self.add_action("Remove parameter")
        self.add_action("Edit field")
        self.exec_(position)


class AddToolTemplatePopupMenu(QMenu):
    """Popup menu class for add tool template button."""

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        # Show the Tool Template Form (empty)
        action = self.addAction("New", self._parent, SLOT("show_tool_template_form()"))
        # Open a tool template file
        action = self.addAction("Open...", self._parent, SLOT("open_tool_template()"))



class ToolTemplateOptionsPopupMenu(QMenu):
    """Popup menu class for tool template options button in Tool item."""

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        # Open a tool template file
        action = self.addAction("Edit Tool Template", self._parent, SLOT("edit_tool_template()"))
        self.addSeparator()
        action = self.addAction("Open descriptor file", self._parent, SLOT("open_tool_template_file()"))
        action = self.addAction("Open main program file", self._parent, SLOT("open_tool_main_program_file()"))

class AddDbReferencePopupMenu(QMenu):
    """Popup menu class for add references button in Data Store item."""

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        # Open a tool template file
        action = self.addAction("New Spine SQLite database", self._parent, SLOT("add_new_spine_reference()"))
        self.addSeparator()
        action = self.addAction("Other...", self._parent, SLOT("show_add_db_reference_form()"))
