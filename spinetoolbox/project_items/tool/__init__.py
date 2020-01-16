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
from .tool_icon import ToolIcon
from .widgets.tool_properties_widget import ToolPropertiesWidget
from .widgets.add_tool_widget import AddToolWidget

item_rank = 2
item_category = item_maker.category()
item_type = item_maker.item_type()
item_icon = ":/icons/project_item_icons/hammer.svg"
icon_maker = ToolIcon
properties_widget_maker = ToolPropertiesWidget
add_form_maker = AddToolWidget
