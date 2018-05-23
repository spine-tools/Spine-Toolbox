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
        super().__init__()
        self.ui = ui
        self.kernel_manager = None
        self.kernel_client = None
        self.is_julia_repl = True
        self.running = False
        self.command = None
        self.kernel_execution_state = None

    def start_jupyter_kernel(self):
        """Start a julia kernel, and connect to it.
        """
        if self.kernel_manager is None:
            kernel_manager = QtKernelManager(kernel_name=JULIA_KERNEL)
            kernel_manager.start_kernel()
            kernel_client = kernel_manager.client()
            kernel_client.start_channels()
            self.kernel_manager = kernel_manager
            self.kernel_client = kernel_client
            self.kernel_client.iopub_channel.message_received.connect(self.iopub_message_received)
            self.kernel_client.shell_channel.message_received.connect(self.shell_message_received)


    @Slot("dict", name="shell_message_received")
    def shell_message_received(self, msg):
        """Run when a message is received on the shell channel.
        Send execution finished signal if message is 'execute_reply'
        """
        #logging.debug("shell message received")
        #logging.debug("id: {}".format(msg['msg_id']))
        #logging.debug("type: {}".format(msg['msg_type']))
        #logging.debug("content: {}".format(msg['content']))
        try:
            logging.debug("status: {}".format(msg['content']['status']))
        except KeyError:
            logging.debug("status key not found")
        if self.running and msg['msg_type'] == 'execute_reply':
            if msg['content']['status'] == 'ok':
                self.execution_finished_signal.emit(0)
            else:
                self.execution_finished_signal.emit(-9999)
            self.running = False


    @Slot("dict", name="iopub_message_received")
    def iopub_message_received(self, msg):
        """Run when a message is received on the iopub channel.
        Execute current command if the kernel reports status 'idle'

        Args:
            msg (int): Message sent by Julia ekernel
        """
        #logging.debug("iopub message received")
        #logging.debug("id: {}".format(msg['msg_id']))
        #logging.debug("type: {}".format(msg['msg_type']))
        #logging.debug("content: {}".format(msg['content']))
        if msg['msg_type'] == 'status':
            self.kernel_execution_state = msg['content']['execution_state']
            if self.command and self.kernel_execution_state == 'idle':
                self.running = True
                self.execute(self.command)
                self.command = None

    def execute_command(self, command):
        """Execute command immediately if kernel is idle. If not, save it for later
        execution
        """
        if not command:
            return
        if self.kernel_execution_state == 'idle':
            self.running = True
            self.execute(command)
        else:
            # store command. It will be executed as soon as the kernel is 'idle'
            self.command = command


    def interrupt_execution(self):
        """Send interrupt signal to kernel"""
        logging.debug("interrupt exec")
        #self.request_interrupt_kernel()
        self.kernel_manager.interrupt_kernel()
        # TODO: get prompt back afer this!

    def shutdown_jupyter_kernel(self):
        """Shut down the jupyter kernel"""
        logging.debug('Shutting down kernel...')
        self.ui.msg_proc.emit("Shutting down Julia REPL...")
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel(now=True)
