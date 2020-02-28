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
Project Tree items.

:authors: A. Soininen (VTT)
:date:   17.1.2020
"""

import logging
from PySide2.QtCore import Qt, QUrl
from PySide2.QtWidgets import QInputDialog
from .metaobject import MetaObject
from .widgets.custom_menus import CategoryProjectItemContextMenu, ProjectItemContextMenu
from .project_commands import RenameProjectItemCommand


class BaseProjectTreeItem(MetaObject):
    """Base class for all project tree items."""

    def __init__(self, name, description):
        """
        Args:
            name (str): Object name
            description (str): Object description
        """
        super().__init__(name, description)
        self._parent = None  # Parent BaseProjectTreeItem. Set when add_child is called
        self._children = list()  # Child BaseProjectTreeItems. Appended when new items are inserted into model.

    def flags(self):  # pylint: disable=no-self-use
        """Returns the item flags."""
        return Qt.NoItemFlags

    def parent(self):
        """Returns parent project tree item."""
        return self._parent

    def child_count(self):
        """Returns the number of child project tree items."""
        return len(self._children)

    def children(self):
        """Returns the children of this project tree item."""
        return self._children

    def child(self, row):
        """Returns child BaseProjectTreeItem on given row.

        Args:
            row (int): Row of child to return

        Returns:
            BaseProjectTreeItem: item on given row or None if it does not exist
        """
        try:
            item = self._children[row]
        except IndexError:
            logging.error("[%s] has no child on row %s", self.name, row)
            return None
        return item

    def row(self):
        """Returns the row on which this item is located."""
        if self._parent is not None:
            r = self._parent.children().index(self)
            # logging.debug("{0} is on row:{1}".format(self.name, r))
            return r
        return 0

    def add_child(self, child_item):
        """Base method that shall be overridden in subclasses."""
        raise NotImplementedError()

    def remove_child(self, row):
        """Remove the child of this BaseProjectTreeItem from given row. Do not call this method directly.
        This method is called by LeafProjectItemTreeModel when items are removed.

        Args:
            row (int): Row of child to remove

        Returns:
            bool: True if operation succeeded, False otherwise
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


class RootProjectTreeItem(BaseProjectTreeItem):
    """Class for the root project tree item."""

    def __init__(self):
        super().__init__("root", "The Root Project Tree Item.")

    def add_child(self, child_item):
        """Adds given category item as the child of this root project tree item. New item is added as the last item.

        Args:
            child_item (CategoryProjectTreeItem): Item to add

        Returns:
            True for success, False otherwise
        """
        if isinstance(child_item, CategoryProjectTreeItem):
            self._children.append(child_item)
            child_item._parent = self
            return True
        logging.error("You can only add a category item as a child of the root item")
        return False

    def custom_context_menu(self, parent, pos):
        """See base class."""
        raise NotImplementedError()

    def apply_context_menu_action(self, parent, action):
        """See base class."""
        raise NotImplementedError()


class CategoryProjectTreeItem(BaseProjectTreeItem):
    """Class for category project tree items."""

    def __init__(self, name, description, item_maker, icon_maker, add_form_maker, properties_ui):
        """
        Args:
            name (str): Category name
            description (str): Category description
            item_maker (function): A function for creating project items in this category
            icon_maker (function): A function for creating icons (QGraphicsItems) for project items in this category
            add_form_maker (function): A function for creating the form to add project items to this category
            properties_ui (object): An object holding the Item Properties UI
        """
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
        """Adds given project tree item as the child of this category item. New item is added as the last item.

        Args:
            child_item (LeafProjectTreeTreeItem): Item to add
            toolbox (ToolboxUI): A toolbox instance
        Returns:
            True for success, False otherwise
        """
        if not isinstance(child_item, LeafProjectTreeItem):
            logging.error("You can only add a leaf item as a child of a category item")
            return False
        self._children.append(child_item)
        child_item._parent = self
        project_item = child_item.project_item
        icon = project_item.get_icon()
        if icon is not None:
            icon.activate()
        else:
            icon = self._icon_maker(child_item.toolbox, project_item.x - 35, project_item.y - 35, 70, 70, project_item)
            project_item.set_icon(icon)
        project_item.set_properties_ui(self._properties_ui)
        project_item.create_data_dir()
        project_item.set_up()
        return True

    def custom_context_menu(self, parent, pos):
        """Returns the context menu for this item.

        Args:
            parent (QWidget): The widget that is controlling the menu
            pos (QPoint): Position on screen
        """
        return CategoryProjectItemContextMenu(parent, pos)

    def apply_context_menu_action(self, parent, action):
        """Applies given action from context menu.

        Args:
            parent (QWidget): The widget that is controlling the menu
            action (str): The selected action
        """
        if action == "Open project directory...":
            file_url = "file:///" + parent._project.project_dir
            parent.open_anchor(QUrl(file_url, QUrl.TolerantMode))
        else:  # No option selected
            pass


class LeafProjectTreeItem(BaseProjectTreeItem):
    """Class for leaf items in the project item tree."""

    def __init__(self, project_item, toolbox):
        """
        Args:
            project_item (ProjectItem): the real project item this item represents
            toolbox (ToobloxUI): a toolbox instance
        """
        super().__init__(project_item.name, project_item.description)
        self._project_item = project_item
        self._toolbox = toolbox

    @property
    def project_item(self):
        """the project item linked to this leaf"""
        return self._project_item

    @property
    def toolbox(self):
        """the toolbox instance"""
        return self._toolbox

    def add_child(self, child_item):
        """See base class."""
        raise NotImplementedError()

    def flags(self):
        """Returns the item flags."""
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def custom_context_menu(self, parent, pos):
        """Returns the context menu for this item.

        Args:
            parent (QWidget): The widget that is controlling the menu
            pos (QPoint): Position on screen
        """
        return ProjectItemContextMenu(parent, pos)

    def apply_context_menu_action(self, parent, action):
        """Applies given action from context menu.

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
            self.project_item.open_directory()
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
            self._project_item._project.remove_item(self.name, check_dialog=True)

    def rename(self, new_name):
        """Renames this item.

        Args:
            new_name(str): New name

        Returns:
            bool: True if renaming was successful, False if renaming failed
        """
        self._toolbox.undo_stack.push(RenameProjectItemCommand(self._toolbox.project_item_model, self, new_name))
