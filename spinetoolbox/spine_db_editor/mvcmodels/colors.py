######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Color functions for models that read from the active palette at call time."""
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication


def pivot_table_header_color():
    """Returns the header background color from the current palette."""
    return QApplication.palette().color(QPalette.ColorRole.Button)


def fixed_field_color():
    """Returns a slightly different background for fixed fields."""
    return QApplication.palette().color(QPalette.ColorRole.Midlight)


def selected_color():
    """Returns the selection/highlight color from the current palette."""
    return QApplication.palette().color(QPalette.ColorRole.Highlight)
