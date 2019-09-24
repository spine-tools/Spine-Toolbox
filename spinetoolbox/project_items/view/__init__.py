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
View plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from project_items.view.ui.view_properties import Ui_Form
from project_items.view.view import View
from project_items.view.view_icon import ViewIcon
from project_items.view.widgets.view_properties_widget import ViewPropertiesWidget
from project_items.view.widgets.add_view_widget import AddViewWidget

item_rank = 3
item_category = "Views"
item_type = "View"
item_icon = ":/icons/project_item_icons/binoculars.svg"
item_maker = View
icon_maker = ViewIcon
properties_widget_maker = ViewPropertiesWidget
add_form_maker = AddViewWidget
