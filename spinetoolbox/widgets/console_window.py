######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Window for the 'base' Julia Console and Python Console.

:author: P. Savolainen (VTT)
:date: 5.2.2021
"""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


class ConsoleWindow(QMainWindow):
    """Class for a separate window for the Python or Julia Console."""

    def __init__(self, toolbox, spine_console, language):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            spine_console (JupyterConsoleWidget): Qt Console
            language (str): 'python' or 'julia'
        """
        super().__init__()
        self._toolbox = toolbox
        self._console = spine_console
        self._language = language
        self.setCentralWidget(self._console)
        self.setWindowTitle(self._console.name())
        if language == "python":
            self.setWindowIcon(QIcon(":/icons/python.svg"))
        elif language == "julia":
            self.setWindowIcon(QIcon(":icons/julia-dots.svg"))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.show()

    def start(self):
        """Starts the kernel."""
        self._console.start_console()

    def closeEvent(self, e):
        """Shuts down the running kernel and calls ToolboxUI method to destroy this window.

        Args:
            e (QCloseEvent): Event
        """
        self._console.shutdown_kernel()
        if self._language == "python":
            self._toolbox.destroy_base_python_console()
        elif self._language == "julia":
            self._toolbox.destroy_base_julia_console()
        super().closeEvent(e)
