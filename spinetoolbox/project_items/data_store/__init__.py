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
Data store plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from .data_store import DataStore as item_maker
from .data_store_icon import DataStoreIcon
from .widgets.data_store_properties_widget import DataStorePropertiesWidget
from .widgets.add_data_store_widget import AddDataStoreWidget

item_rank = 0
item_category = item_maker.category()
item_type = item_maker.item_type()
item_icon = ":/icons/project_item_icons/database.svg"
icon_maker = DataStoreIcon
properties_widget_maker = DataStorePropertiesWidget
add_form_maker = AddDataStoreWidget
