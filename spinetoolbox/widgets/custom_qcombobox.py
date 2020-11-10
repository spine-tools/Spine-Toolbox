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
Class for a custom QComboBox.

:author: P. Savolainen (VTT)
:date:   16.10.2020
"""

from PySide2.QtWidgets import QComboBox


class CustomQComboBox(QComboBox):
    """A custom QComboBox for showing kernels in Settings->Tools."""

    def mouseMoveEvent(self, e):
        """Catch mouseMoveEvent and accept it because the comboBox
        popup (QListView) has mouse tracking on as default.
        This makes sure the comboBox popup appears in correct
        position and clicking on the combobox repeatedly does
        not move the Settings window."""
        e.accept()
