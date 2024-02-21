######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains base classes for project items and item factories."""


class ProjectItemFactory:
    """Class for project item factories."""

    @staticmethod
    def item_class():
        """
        Returns the project item's class.

        Returns:
            type: item's class
        """
        raise NotImplementedError()

    @staticmethod
    def is_deprecated():
        """Queries if item is deprecated.

        Returns:
            bool: True if item is deprecated, False otherwise
        """
        return False

    @staticmethod
    def icon():
        """
        Returns the icon resource path.

        Returns:
            str
        """
        raise NotImplementedError()

    @staticmethod
    def icon_color():
        """
        Returns the icon color.

        Returns:
            QColor: icon's color
        """
        raise NotImplementedError()

    @staticmethod
    def make_add_item_widget(toolbox, x, y, specification):
        """
        Returns an appropriate Add project item widget.

        Args:
            toolbox (ToolboxUI): the main window
            x, y (int): Icon coordinates
            specification (ProjectItemSpecification): item's specification

        Returns:
            QWidget
        """
        raise NotImplementedError()

    @staticmethod
    def make_icon(toolbox):
        """
        Returns a ProjectItemIcon to use with given toolbox, for given project item.

        Args:
            toolbox (ToolboxUI)

        Returns:
            ProjectItemIcon: item's icon
        """
        raise NotImplementedError()

    @staticmethod
    def make_item(name, item_dict, toolbox, project):
        """
        Returns a project item constructed from the given ``item_dict``.

        Args:
            name (str): item's name
            item_dict (dict): serialized project item
            toolbox (ToolboxUI): Toolbox main window
            project (SpineToolboxProject): the project the item belongs to
        Returns:
            ProjectItem
        """
        raise NotImplementedError()

    @staticmethod
    def make_properties_widget(toolbox):
        """
        Creates the item's properties tab widget.

        Returns:
            QWidget: item's properties tab widget
        """
        raise NotImplementedError()

    @staticmethod
    def make_specification_menu(parent, index):
        """
        Creates item specification's context menu.

        Subclasses that do not support specifications can still raise :class:`NotImplementedError`.

        Args:
            parent (QWidget): menu's parent widget
            index (QModelIndex): an index from specification model
        Returns:
            ItemSpecificationMenu: specification's context menu
        """
        raise NotImplementedError()

    @staticmethod
    def make_specification_editor(toolbox, specification=None, item=None, **kwargs):
        """
        Creates the item's specification widget.

        Subclasses that do not support specifications can still raise :class:`NotImplementedError`.

        Args:
            toolbox (ToolboxUI): Toolbox main window
            specification (ProjectItemSpecification, optional): a specification to show in the widget or None for
                a fresh start
            item (ProjectItem, optional): a project item. If the specification is accepted, it is also set for this item
            **kwargs: parameters passed to the specification widget
        Returns:
            QWidget: item's specification widget
        """
        raise NotImplementedError()

    @staticmethod
    def repair_specification(toolbox, specification):
        """Called right after a spec is added to the project. Finds if there's something wrong with the spec
        and proposes actions to fix it with help from toolbox.

        Args:
            toolbox (ToolboxUI): Toolbox main window
            specification (ProjectItemSpecification): a specification to check
        """
