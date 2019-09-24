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
Data interface plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from project_items.data_interface.ui.data_interface_properties import Ui_Form
from project_items.data_interface.data_interface import DataInterface
from project_items.data_interface.data_interface_icon import DataInterfaceIcon
from project_items.data_interface.widgets.data_interface_properties_widget import DataInterfacePropertiesWidget
from project_items.data_interface.widgets.add_data_interface_widget import AddDataInterfaceWidget

item_rank = 4
item_category = "Data Interfaces"
item_type = "Data Interface"
item_icon = ":/icons/project_item_icons/map-solid.svg"
item_maker = DataInterface
icon_maker = DataInterfaceIcon
properties_widget_maker = DataInterfacePropertiesWidget
add_form_maker = AddDataInterfaceWidget
