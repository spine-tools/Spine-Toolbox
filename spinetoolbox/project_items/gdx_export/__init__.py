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
Gdx export project item plugin.

:author: A. Soininen (VTT)
:date:   25.9.2019
"""

from project_items.gdx_export.gdx_export import GdxExport
from project_items.gdx_export.gdx_export_icon import GdxExportIcon
from project_items.gdx_export.widgets.add_gdx_export_widget import AddGdxExportWidget
from project_items.gdx_export.widgets.gdx_export_properties import GdxExportProperties

item_rank = 5
item_category = "Exporting"
item_type = "Gdx Export"
item_icon = ":/icons/project_item_icons/file-export-solid.svg"
item_maker = GdxExport
icon_maker = GdxExportIcon
properties_widget_maker = GdxExportProperties
add_form_maker = AddGdxExportWidget
