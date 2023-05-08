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

"""Window for the Detached Jupyter Console."""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon


class ConsoleWindow(QMainWindow):
    """Class for a separate window for the Python or Julia Console."""

    closed = Signal(str)

    def __init__(self, toolbox, jcw, icon):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            jcw (JupyterConsoleWidget): QtConsole
            icon (QIcon): Icon representing the kernel language
        """
        super().__init__()
        self._toolbox = toolbox
        self._console = jcw
        self.setCentralWidget(self._console)
        self.setWindowIcon(icon)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.show()

    def console(self):
        """Returns the JupyterConsoleWidget attached to this main window."""
        return self._console

    def set_window_title(self, kernel_name):
        """Sets a window title for this main window.

        Args:
            kernel_name (str): Kernel name
        """
        self.setWindowTitle(f"{kernel_name} on Jupyter Console [Detached]")

    def closeEvent(self, e):
        """Shuts down the running kernel closes the window.

        Args:
            e (QCloseEvent): Event
        """
        kernel_name = self._console.kernel_name
        self._console.request_shutdown_kernel_manager()
        self._console.shutdown_kernel_client()
        self.closed.emit(kernel_name)
        super().closeEvent(e)
