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
from __future__ import annotations
from typing import TYPE_CHECKING, Type
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget
from spine_engine.project_item.project_item_specification import ProjectItemSpecification
from ..project import SpineToolboxProject
from ..project_item_icon import ProjectItemIcon
from ..widgets.add_project_item_widget import AddProjectItemWidget
from ..widgets.custom_menus import ItemSpecificationMenu
from ..widgets.properties_widget import PropertiesWidgetBase
from .project_item import ProjectItem
from .specification_editor_window import SpecificationEditorWindowBase

if TYPE_CHECKING:
    from ..ui_main import ToolboxUI


class ProjectItemFactory:
    """Class for project item factories."""

    @staticmethod
    def item_class() -> Type[ProjectItem]:
        """
        Returns the project item's class.

        Returns:
            item's class
        """
        raise NotImplementedError()

    @staticmethod
    def is_deprecated() -> bool:
        """Queries if item is deprecated.

        Returns:
            True if item is deprecated, False otherwise
        """
        return False

    @staticmethod
    def icon() -> str:
        """Returns the icon resource path."""
        raise NotImplementedError()

    @staticmethod
    def icon_color() -> QColor:
        """
        Returns the icon color.

        Returns:
            QColor: icon's color
        """
        raise NotImplementedError()

    @staticmethod
    def make_add_item_widget(toolbox: ToolboxUI, x: float, y: float, specification: str) -> AddProjectItemWidget:
        """
        Returns an appropriate Add project item widget.

        Args:
            toolbox: the main window
            x: Icon's horizontal coordinate.
            y: Icon's vertical coordinate.
            specification: The name of optionally selected specification.

        Returns:
            Add item widget.
        """
        raise NotImplementedError()

    @staticmethod
    def make_icon(toolbox: ToolboxUI) -> ProjectItemIcon:
        """Returns a ProjectItemIcon to use with given toolbox, for given project item."""
        raise NotImplementedError()

    @staticmethod
    def make_item(name: str, item_dict: dict, toolbox: ToolboxUI, project: SpineToolboxProject) -> ProjectItem:
        """
        Returns a project item constructed from the given ``item_dict``.

        Args:
            name: item's name
            item_dict: serialized project item
            toolbox: Toolbox main window
            project: the project the item belongs to

        Returns:
            Deserialized project item.
        """
        raise NotImplementedError()

    @staticmethod
    def make_properties_widget(toolbox: ToolboxUI) -> PropertiesWidgetBase:
        """
        Creates the item's properties tab widget.

        Returns:
            Item's properties tab widget.
        """
        raise NotImplementedError()

    @staticmethod
    def make_specification_menu(parent: QWidget, index: QModelIndex) -> ItemSpecificationMenu:
        """
        Creates item specification's context menu.

        Subclasses that do not support specifications can still raise :class:`NotImplementedError`.

        Args:
            parent: menu's parent widget
            index: an index from specification model
        Returns:
            specification's context menu
        """
        raise NotImplementedError()

    @staticmethod
    def make_specification_editor(
        toolbox: ToolboxUI,
        specification: ProjectItemSpecification | None = None,
        item: ProjectItem | None = None,
        **kwargs,
    ) -> SpecificationEditorWindowBase:
        """
        Creates the item's specification widget.

        Subclasses that do not support specifications can still raise :class:`NotImplementedError`.

        Args:
            toolbox: Toolbox main window
            specification: a specification to show in the widget or None for a fresh start
            item: a project item. If the specification is accepted, it is also set for this item
            **kwargs: parameters passed to the specification widget
        Returns:
            item's specification widget
        """
        raise NotImplementedError()

    @staticmethod
    def repair_specification(toolbox: ToolboxUI, specification: ProjectItemSpecification) -> None:
        """Called right after a spec is added to the project. Finds if there's something wrong with the spec
        and proposes actions to fix it with help from toolbox.

        Args:
            toolbox: Toolbox main window
            specification: a specification to check
        """
