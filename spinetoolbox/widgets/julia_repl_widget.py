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
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import Slot, Signal
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from jupyter_client.kernelspec import find_kernel_specs
from config import JULIA_EXECUTABLE
import logging
import qsubprocess

class JuliaREPLWidget(RichJupyterWidget):
    """
    Attributes:
        ui (ToolboxUI): QMainWindow instance
    """

    subprocess_finished_signal = Signal(int, name="subprocess_finished_signal")

    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.kernel_manager = None
        self.kernel_client = None
        self.running = False
        self.command = None
        self.kernel_execution_state = None
        self.custom_restart = True  # Needed to get the custom_restart_kernel_died signal
        self.custom_restart_kernel_died.connect(self.kernel_died)
        self.kernel_died_count = None
        self.IJulia_install = None # IJulia installation process (QSubProcess)
        self.IJulia_installed = False # True if IJulia installation was succesfull

    def find_julia_kernel(self):
        """Return the name of the most recent available julia kernel
        or None if none is available"""
        kernel_specs = find_kernel_specs()
        julia_specs = [x for x in kernel_specs if x.startswith('julia')]
        if not julia_specs:
            return None
        # pick the most recent available julia kernel
        julia_specs.sort(reverse=True)
        return julia_specs[0]

    def start_jupyter_kernel(self):
        """Start a julia kernel, and connect to it.
        """
        if not self.kernel_manager:
            self.kernel_died_count = 0
            kernel_name = self.find_julia_kernel()
            if not kernel_name:
                self.ui.msg_error.emit("Couldn't find Julia kernel for Jupyter.")
                if self.IJulia_installed: # problem is not due to IJulia installation
                    self.execution_finished_signal.emit(-9998) # emit 'give up' signal
                    return
                self.prompt_to_install_IJulia(
                    title="Unable to find Julia kernel for Jupyter",
                    message="There is no Julia kernel for Jupyter available. "
                            "A Julia kernel is provided by the <b>IJulia</b> package. "
                            "Do you want to install it automatically?"
                )
                return
            kernel_manager = QtKernelManager(kernel_name=kernel_name)
            kernel_manager.start_kernel()
            kernel_client = kernel_manager.client()
            kernel_client.start_channels()
            self.kernel_manager = kernel_manager
            self.kernel_client = kernel_client
            # connect client signals
            self.kernel_client.iopub_channel.message_received.connect(self.iopub_message_received)
            self.kernel_client.shell_channel.message_received.connect(self.shell_message_received)

    @Slot("float", name="kernel_died")
    def kernel_died(self, since_last_heartbeat):
        """Run when kernel dies after a start attempt.
        After 5 deaths, prompt to (re)install IJulia"""
        self.kernel_died_count += 1
        logging.debug("Failed to start Julia Jupyter kernel ({}/5)".format(self.kernel_died_count))
        if self.kernel_died_count == 5:
            self.ui.msg_error.emit("Failed to start Julia Jupyter kernel.")
            self.kernel_died_count = None
            self.kernel_manager = None
            self.kernel_client = None
            if self.IJulia_installed: # problem is not due to IJulia installation
                self.execution_finished_signal.emit(-9998) # emit 'give up' signal
                return
            self.prompt_to_install_IJulia(
                title="Unable to start Julia kernel for Jupyter",
                message="The Julia kernel for Jupyter failed to start. "
                        "This may be due to a configuration problem in the <b>IJulia</b> package. "
                        "Do you want to reconfigure it automatically?"
            )

    def prompt_to_install_IJulia(self, title, message):
        """Attempt to install IJulia via QSubProcess."""
        answer = QMessageBox.question(self, title, message, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            self.subprocess_finished_signal.emit(-9998) # emit 'give up' signal
            return
        julia_dir = self.ui._config.get("settings", "julia_path")
        if not julia_dir == '':
            julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
        else:
            julia_exe = JULIA_EXECUTABLE
        # Follow installation instructions in https://github.com/JuliaLang/IJulia.jl
        cmnd = '{0} -e "ENV["""JUPYTER"""]="""jupyter"""; '\
                'Pkg.add("""IJulia"""); Pkg.build("""IJulia""")"'.format(julia_exe)
        self.IJulia_install = qsubprocess.QSubProcess(self.ui, cmnd)
        self.IJulia_install.subprocess_finished_signal.connect(self.IJulia_install_finished)
        self.IJulia_install.start_process()

    @Slot(int, name="IJulia_install_finished")
    def IJulia_install_finished(self, ret):
        """Run when IJulia installation process finishes"""
        if self.IJulia_install.process_failed:
            self.ui.msg_error.emit("\tJulia kernel installation failed.")
            self.subprocess_finished_signal.emit(-9998) # emit 'give up' signal
        else:
            self.ui.msg.emit("\tJulia kernel for Jupyter successfully installed (via <b>IJulia</b>).")
            self.IJulia_installed = True
            self.start_jupyter_kernel()
        self.IJulia_install.deleteLater()
        self.IJulia_install = None

    @Slot("dict", name="shell_message_received")
    def shell_message_received(self, msg):
        """Run when a message is received on the shell channel.
        Finish execution if message is 'execute_reply'
        """
        logging.debug("shell message received")
        logging.debug("id: {}".format(msg['msg_id']))
        logging.debug("type: {}".format(msg['msg_type']))
        logging.debug("content: {}".format(msg['content']))
        try:
            logging.debug("status: {}".format(msg['content']['status']))
        except KeyError:
            logging.debug("key status not found")
        if self.running and msg['msg_type'] == 'execute_reply':
            if msg['content']['status'] == 'ok':
                self.subprocess_finished_signal.emit(0) # success code
            else:
                self.subprocess_finished_signal.emit(-9999) # any error code
            self.running = False

    @Slot("dict", name="iopub_message_received")
    def iopub_message_received(self, msg):
        """Run when a message is received on the iopub channel.
        Execute current command if the kernel reports status 'idle'

        Args:
            msg (int): Message sent by Julia ekernel
        """
        logging.debug("iopub message received")
        logging.debug("id: {}".format(msg['msg_id']))
        logging.debug("type: {}".format(msg['msg_type']))
        logging.debug("content: {}".format(msg['content']))
        if msg['msg_type'] == 'status':
            self.kernel_execution_state = msg['content']['execution_state']
            if self.command and self.kernel_execution_state == 'idle':
                self.running = True
                self.execute(self.command)
                self.command = None

    def start_process(self, command):
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
        """Send interrupt signal to kernel"""
        logging.debug("interrupt exec")
        #self.request_interrupt_kernel()
        self.kernel_manager.interrupt_kernel()
        # TODO: get prompt back afer this!

    def shutdown_jupyter_kernel(self):
        """Shut down the jupyter kernel"""
        logging.debug('Shutting down kernel...')
        self.ui.msg_proc.emit("Shutting down Julia REPL...")
        if self.kernel_client:
            self.kernel_client.stop_channels()
        if self.kernel_manager:
            self.kernel_manager.shutdown_kernel(now=True)
