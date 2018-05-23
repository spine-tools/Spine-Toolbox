#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Class for a custom RichJupyterWidget to use as julia REPL.

:author: Manuel Marin <manuelma@kth.se>
:date:   22.5.2018
"""

from PySide2.QtCore import Slot, Signal
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from config import JULIA_KERNEL
import logging
import signal

class JuliaREPLWidget(RichJupyterWidget):
    """
    Attributes:
        ui (ToolboxUI): QMainWindow instance
    """

    execution_finished_signal = Signal(int, name="execution_finished_signal")


    def __init__(self, ui):
        """Start a julia kernel, connect to it, and create a RichJupyterWidget to use it
        """
        super().__init__()
        self.ui = ui
        self.kernel_manager = None
        self.kernel_client = None

    def start_jupyter_kernel(self):
        if self.kernel_manager is None:
            kernel_manager = QtKernelManager(kernel_name=JULIA_KERNEL)
            kernel_manager.start_kernel()
            kernel_client = kernel_manager.client()
            kernel_client.start_channels()
            self.kernel_manager = kernel_manager
            self.kernel_client = kernel_client
            self.kernel_client.iopub_channel.message_received.connect(self.message_received)

    def execute_command(self, command):
        # TODO: if kernel busy, dismiss command
        if self.kernel_client is None:
            self.ui.msg_error.emit("Kernel client not initialized.")
            return
        self.kernel_client.execute(command)

    def connect_signal_message_received(self, slot):
        if self.kernel_client is None:
            self.ui.msg_error.emit("Kernel client not initialized.")
            return


    @Slot("dict", name="message_received")
    def message_received(self, msg):
        """Run when a message is received from kernel.

        Args:
            msg (int): Message sent by Julia ekernel
        """
        logging.debug("message received")
        logging.debug(msg)
        if msg['header']['msg_type'] == 'execute_result':
            if msg['content']['data']['text/plain'] == '101':
                self.execution_finished_signal.emit(0)
        elif msg['header']['msg_type'] == 'error':
            self.execution_finished_signal.emit(-9999)

    def shutdown_jupyter_kernel(self):
        logging.debug('Shutting down kernel...')
        self.ui.msg_proc.emit("Shutting down Julia REPL...")
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel(now=True)
