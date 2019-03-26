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
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import QAction
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from jupyter_client.kernelspec import find_kernel_specs, NoSuchKernel
from widgets.toolbars import DraggableWidget
from helpers import busy_effect


class PythonReplWidget(RichJupyterWidget):
    """Python Repl Widget class.

    Attributes:
        toolbox (ToolboxUI): App main window (QMainWindow) instance
    """

    execution_finished_signal = Signal(int, name="execution_finished_signal")

    def __init__(self, toolbox):
        """Class constructor."""
        super().__init__()
        self._toolbox = toolbox
        self._kernel_starting = False  # Warning: Do not use self._starting (protected class variable in JupyterWidget)
        self._running = False  # Not used
        self._kernel_state = None  # Not used
        self.kernel_name = "python3"
        self.kernel_manager = None
        self.kernel_client = None
        self.commands = list()  # FIFO command queue (buffer)
        self.normal_cursor = self._control.viewport().cursor()
        # QActions
        self.start_console_action = QAction("Start", self)
        self.start_console_action.triggered.connect(lambda checked: self.setup_python_kernel())

    def connect_signals(self):
        """Connect signals."""
        self.executing.connect(self.execution_in_progress)  # Signal defined in FrontEndWidget class
        self.executed.connect(self.execution_done)  # Signal defined in FrontEndWidget class
        self.kernel_client.iopub_channel.message_received.connect(self.iopub_msg_received)

    @Slot(str, name="execution_in_progress")
    def execution_in_progress(self, code):
        """Slot for handling the 'executing' signal. Signal is emitted
        when a user visible 'execute_request' has been submitted to the
        kernel from the FrontendWidget.

        Args:
            code (str): Code to be executed (actually not 'str' but 'object')
        """
        self._control.viewport().setCursor(Qt.BusyCursor)
        self._running = True
        if len(self.commands) == 0:
            self._toolbox.msg.emit("Executing manually typed console command")
            # pass  # Happens when users type commands directly to iPython Console
        else:
            self._toolbox.msg_warning.emit("\tExecution in progress. See <b>Python Console</b> for messages.")

    @Slot(dict, name="execution_done")
    def execution_done(self, msg):
        """Slot for handling the 'executed' signal. Signal is emitted
        when a user-visible 'execute_reply' has been received from the
        kernel and processed by the FrontendWidget.

        Args:
            msg (dict): Response message (actually not 'dict' but 'object')
        """
        self._control.viewport().setCursor(self.normal_cursor)
        self._running = False
        if msg['content']['status'] == 'ok':
            # Run next command or finish up if no more commands to execute
            if len(self.commands) == 0:
                self.execution_finished_signal.emit(0)
            else:
                cmd = self.commands.pop(0)
                self.execute(cmd)
        else:
            # TODO: if status='error' you can get the exception and more info from msg
            # TODO: If there are more commands to execute should we stop or continue to next command
            self.execution_finished_signal.emit(-9999)  # any error code

    def setup_python_kernel(self):
        # self._toolbox.msg.emit("Setting up Python kernel")
        kernel_specs = find_kernel_specs()
        # logging.debug("kernel_specs:{0}".format(kernel_specs))
        # python_kernels = [x for x in kernel_specs if x.startswith('python')]
        # if self.kernel_name in python_kernels:
        return self.start_python_kernel()
        # else:
        #     self._toolbox.msg_error.emit("\tCouldn't find the {0} kernel specification".format(self.kernel_name))

    def start_python_kernel(self):
        """Start IPython kernel and attach it to the Python Console."""
        self._kernel_starting = True
        if self.kernel_manager and self.kernel_name == 'python3':
            self._toolbox.msg.emit("*** Using previously started Python Console ***")
            self._kernel_starting = False
            return True
        self._toolbox.msg.emit("*** Starting Python Console ***")
        km = QtKernelManager(kernel_name=self.kernel_name)
        try:
            km.start_kernel()
            kc = km.client()
            kc.start_channels()
            self.kernel_manager = km
            self.kernel_client = kc
            self.connect_signals()
            return True
        except FileNotFoundError:
            self._toolbox.msg_error.emit("\tCouldn't find the Python executable specified by the Jupyter kernel.")
            self._kernel_starting = False
            return self.handle_failed_to_start()
        except NoSuchKernel:  # TODO: In which case does this exactly happen?
            self._toolbox.msg_error.emit("\t[NoSuchKernel] Couldn't find the specified Python Jupyter kernel.")
            self._kernel_starting = False
            return self.handle_failed_to_start()

    def handle_failed_to_start(self):
        """In case of FileNotFoundError or NoSuchKernel exception"""
        self._toolbox.msg.emit("Handling failed to start")
        return False

    @Slot(dict, "iopub_msg_received")
    def iopub_msg_received(self, msg):
        """Message received from the IOPUB channel.
        Note: We are only monitoring when the kernel has started
        successfully and ready for action here. Alternatively, this
        could be done in the Slot for the 'executed' signal. However,
        this Slot could come in handy at some point. See 'Messaging in
        Jupyter' for details:
        https://jupyter-client.readthedocs.io/en/latest/messaging.html

        Args:
            msg (dict): Received message from IOPUB channel
        """
        parent_msg_type = msg["parent_header"]["msg_type"]  # msg that the received msg is replying to
        msg_type = msg["header"]["msg_type"]
        # When msg_type:'status, content has the kernel execution_state
        # When msg_type:'execute_input', content has the code to be executed
        # When msg_type:'stream', content has the stream name (e.g. stdout) and the text
        if msg_type == "status":
            self._kernel_state = msg['content']['execution_state']
            if parent_msg_type == "kernel_info_request":
                # If kernel_state:'busy', kernel_info_request is being processed
                # If kernel_state:'idle', kernel_info_request is done
                pass
            elif parent_msg_type == "history_request":
                # If kernel_state:'busy', history_request is being processed
                # If kernel_state:'idle', histroy_request is done
                pass
            elif parent_msg_type == "execute_request":
                # If kernel_state:'busy', execute_request is being processed (i.e. execution or start-up in progress)
                # If kernel_state:'idle', execute_request is done
                if self._kernel_state == "busy":
                    # kernel is busy starting up or executing
                    pass
                elif self._kernel_state == "idle":
                    # Kernel is idle after execution
                    if self._kernel_starting:
                        # Kernel is idle after starting up -> execute pending command
                        self._kernel_starting = False
                        # Start executing the first command in command buffer immediately
                        if len(self.commands) == 0:  # Happens if Python console is started from context-menu
                            return
                        else:
                            # Happens if Python console is started by clicking on Tool's Execute button
                            cmd = self.commands.pop(0)
                            self.execute(cmd)
                else:  # Should not happen
                    self._toolbox.msg_error.emit("Unhandled execution_state '{0}' after "
                                                 "execute_request".format(self._kernel_state))

    def execute_instance(self, commands):
        """Start IPython kernel if not running already.
        Execute command if kernel is not executing a previous command."""
        self.commands = commands
        if self.kernel_manager and self.kernel_name == 'python3':
            self._toolbox.msg.emit("*** Using previously started Python Console ***")
            cmd = self.commands.pop(0)
            self.execute(cmd)
        else:
            self.start_python_kernel()  # This will execute the pending command when the kernel has started

    def terminate_process(self):
        """Send interrupt signal to kernel."""
        self.kernel_manager.interrupt_kernel()

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
        menu.insertAction(first_action, self.start_console_action)
        menu.insertSeparator(first_action)
        return menu

    def dragEnterEvent(self, event):
        """Don't accept project item drops."""
        source = event.source()
        if isinstance(source, DraggableWidget):
            event.ignore()
        else:
            super().dragEnterEvent(event)
