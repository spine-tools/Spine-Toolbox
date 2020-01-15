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
Exporter project item plugin.

:author: A. Soininen (VTT)
:date:   25.9.2019
"""

from .exporter import Exporter as item_maker
from .exporter_icon import ExporterIcon as icon_maker
from .widgets.add_exporter_widget import AddExporterWidget as add_form_maker
from .widgets.exporter_properties import ExporterProperties as properties_widget_maker

item_rank = 5
item_category = item_maker.category()
item_type = item_maker.item_type()
item_icon = ":/icons/project_item_icons/database-export.svg"
