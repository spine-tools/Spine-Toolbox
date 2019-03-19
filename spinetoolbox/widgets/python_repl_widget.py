######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Class for a custom RichJupyterWidget to use as Python REPL.

:author: P. Savolainen (VTT)
:date:   14.3.2019
"""

import sys
import logging
from PySide2.QtWidgets import QAction
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from jupyter_client.kernelspec import find_kernel_specs, NoSuchKernel


class PythonReplWidget(RichJupyterWidget):
    """Python Repl Widget class.

    Attributes:
        toolbox (ToolboxUI): App main window (QMainWindow) instance
    """
    def __init__(self, toolbox):
        """Class constructor."""
        super().__init__()
        self._toolbox = toolbox
        self.kernel_name = "python3"
        self.kernel_manager = None
        self.kernel_client = None
        self.starting = False
        # QActions
        self.start_repl_action = QAction("Start", self)
        self.start_repl_action.triggered.connect(lambda checked: self.setup_python_kernel())

    def setup_python_kernel(self):
        self._toolbox.msg.emit("Setting up Python kernel")
        kernel_specs = find_kernel_specs()
        # logging.debug("kernel_specs:{0}".format(kernel_specs))
        # python_kernels = [x for x in kernel_specs if x.startswith('python')]
        # if self.kernel_name in python_kernels:
        return self.start_python_kernel()
        # else:
        #     self._toolbox.msg_error.emit("\tCouldn't find the {0} kernel specification".format(self.kernel_name))

    def start_python_kernel(self):
        self.starting = True
        self._toolbox.msg.emit("*** Starting Python Console ***")
        kernel_manager = QtKernelManager(kernel_name=self.kernel_name)
        try:
            kernel_manager.start_kernel()
            self.kernel_manager = kernel_manager
            self.setup_client()
            return True
        except FileNotFoundError:
            self._toolbox.msg_error.emit("\tCouldn't find the Python executable specified by the Jupyter kernel.")
            return self.handle_repl_failed_to_start()
        except NoSuchKernel:  # TODO: In which case does this exactly happens?
            self._toolbox.msg_error.emit("\t[NoSuchKernel] Couldn't find the specified Julia Jupyter kernel.")
            return self.handle_repl_failed_to_start()

    def setup_client(self):
        if not self.kernel_manager:
            return
        kernel_client = self.kernel_manager.client()
        kernel_client.start_channels()
        self.kernel_client = kernel_client

    def handle_failed_to_start(self):
        """In case a FileNotFoundError or NoSuchKernel exception"""
        self.starting = False
        self._toolbox.msg.emit("Handling failed to start")
        return False

    def shutdown_kernel(self):
        """Shut down Python kernel."""
        if not self.kernel_client:
            return
        self._toolbox.msg.emit("Shutting down Python Console...")
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()

    def _context_menu_make(self, pos):
        """Reimplemented to add custom actions."""
        menu = super()._context_menu_make(pos)
        first_action = menu.actions()[0]
        menu.insertAction(first_action, self.start_repl_action)
        menu.insertSeparator(first_action)
        return menu