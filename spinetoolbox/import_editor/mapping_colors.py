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
Contains colors used in Import editor's tables.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""
from PySide2.QtCore import Qt
from PySide2.QtGui import QColor


MAPPING_COLORS = {
    "entity_class": QColor(196, 117, 56),
    "entity": QColor(223, 194, 125),
    "group": QColor(120, 150, 220),
    "parameter_value": QColor(128, 205, 193),
    "parameter_extra_dimension": QColor(41, 173, 153),
    "parameter_name": QColor(178, 255, 243),
    "alternative": QColor(196, 117, 56),
    "scenario": QColor(223, 194, 125),
    "active": QColor(128, 205, 193),
    "before_alternative": QColor(120, 150, 220),
}
ERROR_COLOR = QColor(Qt.red)
