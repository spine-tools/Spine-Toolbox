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

:author: M. Marin (KTH)
:date:   22.5.2018
"""

import os
import logging
import qsubprocess
from PySide2.QtWidgets import QMessageBox, QAction
from PySide2.QtCore import Slot, Signal, Qt
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from jupyter_client.kernelspec import find_kernel_specs
from config import JULIA_EXECUTABLE
from widgets.toolbars import DraggableWidget


class JuliaREPLWidget(RichJupyterWidget):
    """Class for a custom RichJupyterWidget.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
    """
    execution_finished_signal = Signal(int, name="execution_finished_signal")

    def __init__(self, toolbox):
        super().__init__(parent=toolbox)
        self._toolbox = toolbox
        self.kernel_manager = None
        self.kernel_client = None
        self.running = False
        self.command = None
        self.kernel_execution_state = None
        self.custom_restart = True  # Needed to get the `custom_restart_kernel_died` signal
        self.custom_restart_kernel_died.connect(self.kernel_died)
        self.kernel_died_count = None
        self.ijulia_process = None  # IJulia installation/reconfiguration process (QSubProcess)
        self.ijulia_process_succeeded = False  # True if IJulia installation was successful
        self.execution_failed_to_start = False
        self.starting = False
        self.normal_cursor = self._control.viewport().cursor()
        # Set logging level for jupyter module loggers
        traitlets_logger = logging.getLogger("traitlets")
        asyncio_logger = logging.getLogger("asyncio")
        traitlets_logger.setLevel(level=logging.ERROR)
        asyncio_logger.setLevel(level=logging.ERROR)

    def find_julia_kernel(self):
        """Return the name of the most recent julia kernel available
        or None if none available."""
        kernel_specs = find_kernel_specs()
        julia_specs = [x for x in kernel_specs if x.startswith('julia')]
        if not julia_specs:
            return None
        # pick the most recent available julia kernel
        julia_specs.sort(reverse=True)
        return julia_specs[0]

    def start_jupyter_kernel(self):
        """Start a julia kernel, and connect to it."""
        if not self.kernel_manager:
            self.starting = True
            self._toolbox.msg.emit("*** Starting Julia REPL ***")
            self.kernel_died_count = 0
            kernel_name = self.find_julia_kernel()
            if not kernel_name:
                self._toolbox.msg_error.emit("\tCouldn't find a Julia Jupyter kernel specification.")
                if self.ijulia_process_succeeded:  # problem is not due to IJulia
                    self.execution_failed_to_start = True
                    self.execution_finished_signal.emit(-9999)
                    return
                self.prompt_to_install_ijulia()
                return
            # try to start the kernel using the available spec
            kernel_manager = QtKernelManager(kernel_name=kernel_name)
            try:
                kernel_manager.start_kernel()
            except FileNotFoundError:
                self._toolbox.msg_error.emit("\tCouldn't find the specified Julia kernel for Jupyter.")
                if self.ijulia_process_succeeded:  # problem is not due to IJulia
                    self.execution_failed_to_start = True
                    self.execution_finished_signal.emit(-9999)
                    return
                self.prompt_to_reconfigure_ijulia()
                return
            kernel_client = kernel_manager.client()
            kernel_client.start_channels()
            self.kernel_manager = kernel_manager
            self.kernel_client = kernel_client
            # connect client signals
            self.kernel_client.iopub_channel.message_received.connect(self.iopub_message_received)
            self.kernel_client.shell_channel.message_received.connect(self.shell_message_received)
        else:
            self._toolbox.msg.emit("*** Using previously started Julia REPL ***")

    @Slot("float", name="kernel_died")
    def kernel_died(self, since_last_heartbeat):
        """Run when kernel dies after a start attempt.
        After 5 deaths, prompt to (re)install IJulia"""
        self.kernel_died_count += 1
        self._toolbox.msg_warning.emit("Failed to start Julia Jupyter kernel "
                                       "(attempt {} of 5)".format(self.kernel_died_count))
        if self.kernel_died_count == 5:
            self._toolbox.msg_error.emit("\tFailed to start Julia Jupyter kernel in 5 attempts.")
            self.kernel_died_count = None
            self.kernel_manager = None
            self.kernel_client = None
            if self.ijulia_process_succeeded:  # problem is not due to IJulia
                self._toolbox.msg_error.emit("Sub-process failed to start. Make sure that "
                                             "Julia is installed properly on your computer.")
                self.execution_failed_to_start = True
                self.execution_finished_signal.emit(-9999)
                return
            self.prompt_to_install_ijulia()

    def prompt_to_reconfigure_ijulia(self):
        """Prompt user to reconfigure IJulia via QSubProcess."""
        title = "Unable to start Julia kernel for Jupyter"
        message = "The Julia kernel for Jupyter failed to start. "\
                  "This may be due to a configuration problem in the <b>IJulia</b> package. "\
                  "<p>Do you want to reconfigure it now?</p>"
        answer = QMessageBox.question(self, title, message, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            self.execution_failed_to_start = True
            self.execution_finished_signal.emit(-9999)
            return
        self._toolbox.msg.emit("*** Reconfiguring <b>IJulia</b> ***")
        self._toolbox.msg_warning.emit("Depending on your system, this process can take a few minutes...")
        julia_dir = self._toolbox._config.get("settings", "julia_path")
        if not julia_dir == '':
            julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
        else:
            julia_exe = JULIA_EXECUTABLE
        # Follow installation instructions in https://github.com/JuliaLang/IJulia.jl
        command = "{0}".format(julia_exe)
        args = list()
        args.append("-e")
        args.append("ENV[ARGS[1]] = ARGS[2]; Pkg.build(ARGS[3])")
        args.append("JUPYTER")
        args.append("jupyter")
        args.append("IJulia")
        self.ijulia_process = qsubprocess.QSubProcess(self._toolbox, command, args)
        self.ijulia_process.subprocess_finished_signal.connect(self.ijulia_process_finished)
        self.ijulia_process.start_process()

    def prompt_to_install_ijulia(self):
        """Prompt user to install IJulia via QSubProcess."""
        title = "Unable to find Julia kernel for Jupyter"
        message = "There is no Julia kernel for Jupyter available. "\
                  "A Julia kernel is provided by the <b>IJulia</b> package. "\
                  "<p>Do you want to install it now?</p>"
        answer = QMessageBox.question(self, title, message, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            self.execution_failed_to_start = True
            self.execution_finished_signal.emit(-9999)
            return
        self._toolbox.msg.emit("*** Installing <b>IJulia</b> ***")
        self._toolbox.msg_warning.emit("Depending on your system, this process can take a few minutes...")
        julia_dir = self._toolbox._config.get("settings", "julia_path")
        if not julia_dir == '':
            julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
        else:
            julia_exe = JULIA_EXECUTABLE
        # Follow installation instructions in https://github.com/JuliaLang/IJulia.jl
        command = "{0}".format(julia_exe)
        args = list()
        args.append("-e")
        args.append("ENV[ARGS[1]] = ARGS[2]; Pkg.add(ARGS[3])")
        args.append("JUPYTER")
        args.append("jupyter")
        args.append("IJulia")
        self.ijulia_process = qsubprocess.QSubProcess(self._toolbox, command, args)
        self.ijulia_process.subprocess_finished_signal.connect(self.ijulia_process_finished)
        self.ijulia_process.start_process()

    @Slot(int, name="ijulia_process_finished")
    def ijulia_process_finished(self, ret):
        """Run when IJulia installation/reconfiguration process finishes"""
        if self.ijulia_process.process_failed:
            self._toolbox.msg_error.emit("Sub-process failed to start. Make sure that "
                                         "Julia is installed properly on your computer.")
            self.execution_failed_to_start = True
            self.execution_finished_signal.emit(-9999)
        else:
            self._toolbox.msg.emit("Julia kernel for Jupyter successfully installed.")
            self.ijulia_process_succeeded = True
            self.start_jupyter_kernel()
        self.ijulia_process.deleteLater()
        self.ijulia_process = None

    @Slot("dict", name="shell_message_received")
    def shell_message_received(self, msg):
        """Run when a message is received on the shell channel.
        Finish execution if message is 'execute_reply'.

        Args:
            msg (dict): Message sent by Julia kernel.
        """
        # logging.debug("shell message received")
        # logging.debug("id: {}".format(msg['msg_id']))
        # logging.debug("type: {}".format(msg['msg_type']))
        # logging.debug("content: {}".format(msg['content']))
        if self.running and msg['msg_type'] == 'execute_reply':
            if msg['content']['execution_count'] == 0:
                self._toolbox.msg.emit("Julia Jupyter kernel successfully started.")
                return
            if msg['content']['status'] == 'ok':
                self.execution_finished_signal.emit(0)  # success code
            else:
                self.execution_finished_signal.emit(-9999)  # any error code
            self.running = False

    @Slot("dict", name="iopub_message_received")
    def iopub_message_received(self, msg):
        """Run when a message is received on the iopub channel.
        Execute current command if the kernel reports status 'idle'

        Args:
            msg (dict): Message sent by Julia ekernel.
        """
        # logging.debug("iopub message received")
        # logging.debug("id: {}".format(msg['msg_id']))
        # logging.debug("type: {}".format(msg['msg_type']))
        # logging.debug("content: {}".format(msg['content']))
        if msg['msg_type'] == 'status':
            self.kernel_execution_state = msg['content']['execution_state']
            if self.starting and self.kernel_execution_state == 'idle':
                self.starting = False
                self._control.viewport().setCursor(self.normal_cursor)
            if self.command and self.kernel_execution_state == 'idle':
                self.running = True
                self.execute(self.command)
                self.command = None
        # handle interrupt exception caused by pressing Stop button in tool item
        elif self.running and msg['msg_type'] == 'error':
            self.execution_finished_signal.emit(-9999)  # any error code

    def execute_instance(self, command):
        """Execute command immediately if kernel is idle. If not, save it for later
        execution.
        """
        if not command:
            return
        self.start_jupyter_kernel()
        if self.kernel_execution_state == 'idle':
            self.running = True
            self.execute(command)
        else:
            # store command. It will be executed as soon as the kernel is 'idle'
            self.command = command

    def terminate_process(self):
        """Send interrupt signal to kernel."""
        # logging.debug("interrupt exec")
        self.kernel_manager.interrupt_kernel()

    def shutdown_jupyter_kernel(self):
        """Shut down the jupyter kernel."""
        if not self.kernel_client:
            return
        self._toolbox.msg.emit("Shutting down Julia REPL...")
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel(now=True)

    def restart_jupyter_kernel(self):
        """Restart the jupyter kernel."""
        if not self.kernel_manager:
            return
        self.starting = True
        self._toolbox.msg.emit("Restarting Julia REPL...")
        self.kernel_client.stop_channels()
        self.kernel_manager.restart_kernel(now=True)
        kernel_client = self.kernel_manager.client()
        kernel_client.start_channels()
        self.kernel_client = kernel_client
        # connect client signals
        self.kernel_client.iopub_channel.message_received.connect(self.iopub_message_received)
        self.kernel_client.shell_channel.message_received.connect(self.shell_message_received)

    def _custom_context_menu_requested(self, pos):
        """Reimplemented method to add a (re)start REPL action into the default context menu.
        """
        menu = self._context_menu_make(pos)
        first_action = menu.actions()[0]
        menu.insertSeparator(first_action)
        if not self.kernel_manager:
            start_repl_action = QAction("Start REPL", self)
            start_repl_action.triggered.connect(lambda: self.start_jupyter_kernel())
            menu.insertAction(first_action, start_repl_action)
        else:
            restart_repl_action = QAction("Restart REPL", self)
            restart_repl_action.triggered.connect(lambda: self.restart_jupyter_kernel())
            restart_repl_action.setEnabled(not self.command and not self.running)
            menu.insertAction(first_action, restart_repl_action)
        menu.exec_(self._control.mapToGlobal(pos))

    def enterEvent(self, event):
        """Set busy cursor during REPL (re)starts."""
        if self.starting:
            self._control.viewport().setCursor(Qt.BusyCursor)

    def dragEnterEvent(self, event):
        """Don't accept drops from Add Item Toolbar."""
        source = event.source()
        if isinstance(source, DraggableWidget):
            event.ignore()
        else:
            super().dragEnterEvent(event)
