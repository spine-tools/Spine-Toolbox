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

from .tool import Tool as item_maker
from .tool_icon import ToolIcon as icon_maker
from .widgets.tool_properties_widget import ToolPropertiesWidget as properties_widget_maker
from .widgets.add_tool_widget import AddToolWidget as add_form_maker
from .widgets.tool_specification_widget import ToolSpecificationWidget as specification_form_maker
from .widgets.custom_menus import ToolSpecificationMenu as specification_menu_maker
from .tool_specifications import load_tool_specification as specification_loader

item_rank = 2
item_category = item_maker.category()
item_type = item_maker.item_type()
item_icon = ":/icons/project_item_icons/hammer.svg"
