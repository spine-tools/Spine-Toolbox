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
from .tool_specifications import ToolSpecification
from .widgets.tool_properties_widget import ToolPropertiesWidget
from .widgets.tool_specification_widget import ToolSpecificationWidget
from .widgets.add_tool_widget import AddToolWidget
from .widgets.custom_menus import ToolSpecificationMenu


class ToolFactory(ProjectItemFactory):
    @staticmethod
    def icon():
        return ":/icons/project_item_icons/hammer.svg"

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

    @staticmethod
    def _make_properties_widget(toolbox):
        return ToolPropertiesWidget(toolbox)
