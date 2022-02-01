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
Functions to make and handle QStatusBars.
"""
from PySide2.QtWidgets import QStatusBar
from ..config import STATUSBAR_SS


class MainStatusBar(QStatusBar):
    """A status bar for the main toolbox window."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI)
        """
        super().__init__(toolbox)
        self.setStyleSheet(STATUSBAR_SS)  # Initialize QStatusBar
