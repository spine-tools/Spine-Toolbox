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
The ToolFactory class.

:author: M. Marin (KTH)
:date:   15.4.2020
"""

from spinetoolbox.project_item import ProjectItemFactory
from .tool import Tool
from .tool_icon import ToolIcon
from .widgets.tool_properties_widget import ToolPropertiesWidget
from .widgets.tool_specification_widget import ToolSpecificationWidget
from .widgets.add_tool_widget import AddToolWidget
from .widgets.custom_menus import ToolSpecificationMenu


class ToolFactory(ProjectItemFactory):
    @staticmethod
    def item_class():
        return Tool

    @staticmethod
    def icon():
        return ":/icons/project_item_icons/hammer.svg"

    @staticmethod
    def supports_specifications():
        return True

    @staticmethod
    def make_add_item_widget(toolbox, x, y, specification):
        return AddToolWidget(toolbox, x, y, specification)

    @staticmethod
    def make_icon(toolbox, x, y, project_item):
        return ToolIcon(toolbox, x, y, project_item, ToolFactory.icon())

    @staticmethod
    def make_item(name, item_dict, toolbox, project, logger):
        return Tool.from_dict(name, item_dict, toolbox, project, logger)

    @staticmethod
    def make_properties_widget(toolbox):
        return ToolPropertiesWidget(toolbox)

    @staticmethod
    def make_specification_menu(parent, index):
        return ToolSpecificationMenu(parent, index)

    @staticmethod
    def make_specification_widget(toolbox, specification=None):
        """See base class."""
        return ToolSpecificationWidget(toolbox, specification)
