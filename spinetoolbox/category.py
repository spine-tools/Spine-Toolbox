######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
This module defines the project item categories available in the Toolbox.

:author: A.Soininen (VTT)
:date:   6.5.2020
"""
# The categories will appear in the main window in the same order they are declared here.
CATEGORIES = ("Data Stores", "Data Connections", "Tools", "Views", "Importers", "Exporters", "Manipulators")


CATEGORY_DESCRIPTIONS = {
    "Data Connections": "Generic data source",
    "Data Stores": "Data in the Spine generic format",
    "Exporters": "Data conversion from Spine to an external format",
    "Importers": "Data conversion from an external format to Spine",
    "Tools": "Custom data processing",
    "Views": "Data visualization",
    "Manipulators": "Data conversion from Spine to Spine",
}
