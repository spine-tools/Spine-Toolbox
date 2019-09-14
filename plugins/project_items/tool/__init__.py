######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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


from .ui.tool_properties import Ui_Form
from .tool import Tool
from .tool_icon import ToolIcon
from .widgets.tool_properties_widget import ToolPropertiesWidget

item_category = "Tools"
item_type = "Tool"
item_icon = ":/icons/project_item_icons/hammer.svg"
item_maker = Tool
icon_maker = ToolIcon
properties_widget_maker = ToolPropertiesWidget


def init_properties_ui(toolbox):
    properties_ui = Ui_Form()
    properties_widget = QWidget()
    properties_ui.setupUi(properties_widget)
    properties_ui.treeView_template.setStyleSheet(TREEVIEW_HEADER_SS)
    toolbox.tool_template_model_changed.connect(properties_ui.comboBox_tool.setModel)
    toolbox.ui.tabWidget_item_properties.addTab(properties_widget, item_type)
    return properties_ui
