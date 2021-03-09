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
A widget for the 'base' Julia Console and Python Console.

:author: P. Savolainen (VTT)
:date: 5.2.2021
"""

from PySide2.QtWidgets import QWidget, QVBoxLayout, QFrame
from PySide2.QtCore import Qt, QPoint


class ConsoleWindow(QWidget):
    """Class for a separate window for the Python or Julia Console."""

    def __init__(self, toolbox, spine_console):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            spine_console (SpineConsoleWidget): Qt Console
        """
        super().__init__(parent=None, f=Qt.Window)  # Setting the parent inherits the stylesheet
        # Make UI
        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.vertical_layout.setSpacing(0)
        # self.frame = QFrame()
        # self.frame.setFrameShape(QFrame.StyledPanel)
        # self.frame.setFrameShadow(QFrame.Raised)
        # self.frame.setLineWidth(5)
        # self.vertical_layout.addWidget(self.frame)
        self.vertical_layout.addWidget(spine_console)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(spine_console.name())
        self.console = spine_console
        self.show()

    def start(self):
        self.console.start_console()
