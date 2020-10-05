######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Items.
# Spine Items is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""
Contains base classes for project items and item factories.

:authors: P. Savolainen (VTT)
:date:   4.10.2018
"""


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
    def icon():
        """
        Returns the icon resource path.

        Returns:
            str
        """
        raise NotImplementedError()

    @staticmethod
    def supports_specifications():
        """
        Returns whether or not this factory supports specs.

        If the subclass implementation returns True, then it must also implement
        ``specification_form_maker``, and ``specification_menu_maker``.

        Returns:
            bool
        """
        return False

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
    def make_item(name, item_dict, toolbox, project, logger):
        """
        Returns a project item constructed from the given ``item_dict``.

        Args:
            name (str): item's name
            item_dict (dict): serialized project item
            toolbox (ToolboxUI): Toolbox main window
            project (SpineToolboxProject): the project the item belongs to
            logger (LoggerInterface): a logger
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
    def make_specification_widget(toolbox, specification=None):
        """
        Creates the item's specification widget.

        Subclasses that do not support specifications can still raise :class:`NotImplementedError`.

        Args:
            toolbox (ToolboxUI): Toolbox main window
            specification (ProjectItemSpecification, optional): a specification to show in the widget or None for
                a fresh start
        Returns:
            QWidget: item's specification widget
        """
        raise NotImplementedError()
