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
Tool plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from spinetoolbox.project_tree_item import CategoryProjectTreeItem
from .tool import Tool
from .tool_icon import ToolIcon
from .tool_specifications import ToolSpecification
from .widgets.tool_properties_widget import ToolPropertiesWidget
from .widgets.tool_specification_widget import ToolSpecificationWidget
from .widgets.add_tool_widget import AddToolWidget
from .widgets.custom_menus import ToolSpecificationMenu


class ToolCategory(CategoryProjectTreeItem):
    def __init__(self, toolbox):
        super().__init__(toolbox, "Tools", "Some meaningful description.")

    @staticmethod
    def rank():
        return 2

    @staticmethod
    def icon():
        return ":/icons/project_item_icons/hammer.svg"

    @staticmethod
    def item_type():
        return "Tool"

    @property
    def properties_widget_maker(self):
        return ToolPropertiesWidget

    @property
    def item_maker(self):
        return Tool

    @property
    def icon_maker(self):
        return ToolIcon

    @property
    def add_form_maker(self):
        return AddToolWidget

    @staticmethod
    def supports_specifications():
        return True

    @property
    def specification_form_maker(self):
        return ToolSpecificationWidget

    @property
    def specification_menu_maker(self):
        return ToolSpecificationMenu

    @property
    def specification_loader(self):
        return ToolSpecification.toolbox_load
