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
Importer plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from .importer import Importer
from .importer_icon import ImporterIcon
from .widgets.importer_properties_widget import ImporterPropertiesWidget
from .widgets.add_importer_widget import AddImporterWidget

item_rank = 4
item_category = Importer.category()
item_type = Importer.item_type()
item_icon = ":/icons/project_item_icons/database-import.svg"
item_maker = Importer
icon_maker = ImporterIcon
properties_widget_maker = ImporterPropertiesWidget
add_form_maker = AddImporterWidget
