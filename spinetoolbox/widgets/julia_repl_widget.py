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
from qtconsole.manager import QtKernelRestarter
from config import JULIA_EXECUTABLE, JL_REPL_TIME_TO_DEAD, JL_REPL_RESTART_LIMIT
from widgets.toolbars import DraggableWidget
from helpers import busy_effect


class CustomQtKernelManager(QtKernelManager):
    """A QtKernelManager with a custom restarter."""

    kernel_left_dead = Signal(name="kernel_left_dead")

    def start_restarter(self):
        """Start a restarter with custom time to dead and restart limit."""
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = QtKernelRestarter(
                    time_to_dead=JL_REPL_TIME_TO_DEAD,
                    restart_limit=JL_REPL_RESTART_LIMIT,
                    kernel_manager=self,
                    parent=self,
                    log=self.log,
                )
                self._restarter.add_callback(self._handle_kernel_restarted, event='restart')
                self._restarter.add_callback(self._handle_kernel_left_dead, event='dead')
            self._restarter.start()

    def _handle_kernel_left_dead(self):
        self.kernel_left_dead.emit()


# FIXME: if the kernel cannot be started we always assume the execution failed and send the signal,
# but maybe the user wasn't running anything, juts starting or restarting the REPL...
class JuliaREPLWidget(RichJupyterWidget):
    """Class for a custom RichJupyterWidget.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
    """
    execution_finished_signal = Signal(int, name="execution_finished_signal")

    def __init__(self, toolbox):
        super().__init__(parent=toolbox)
        self._toolbox = toolbox
        self.custom_restart = True
        self.kernel_name = None  # The name of the Julia kernel from settings last checked
        self.kernel_manager = None
        self.kernel_client = None
        self.running = False
        self.command = None
        self.kernel_execution_state = None
        self.ijulia_process = None  # IJulia installation/reconfiguration process (QSubProcess)
        self.ijulia_process_succeeded = False  # True if IJulia installation was successful
        self.execution_failed_to_start = False
        self.starting = False
        self.normal_cursor = self._control.viewport().cursor()
        # Set logging level for jupyter module loggers
        traitlets_logger = logging.getLogger("traitlets")
        asyncio_logger = logging.getLogger("asyncio")
        traitlets_logger.setLevel(level=logging.WARNING)
        asyncio_logger.setLevel(level=logging.WARNING)

    @busy_effect
    def julia_kernel_name(self):
        """Return the name of the julia kernel according to julia executable from settings."""
        self._toolbox.msg.emit("\tFinding out Julia version...")
        julia_dir = self._toolbox._config.get("settings", "julia_path")
        if not julia_dir == '':
            julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
        else:
            julia_exe = JULIA_EXECUTABLE
        program = "{0}".format(julia_exe)
        args = list()
        args.append("-e")
        args.append("println(VERSION)")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        if not q_process.wait_for_finished(msecs=3000):
            self._toolbox.msg_error.emit("Subprocess failed. "
                                         "Make sure that Julia is installed properly on your computer "
                                         "and try again.")
            return None
        julia_version = q_process.output
        kernel_name = "julia-" + ".".join(julia_version.split(".")[0:2])
        if self.kernel_name is not None and self.kernel_name != kernel_name:
            self._toolbox.msg.emit("\tJulia version has changed in settings. "
                                   "New kernel is {0}".format(kernel_name))
        return kernel_name

    def start_jupyter_kernel(self):
        """Find the julia kernel name from settings and
        start a new kernel if needed."""
        kernel_name = self.julia_kernel_name()
        if not kernel_name:
            return
        if self.kernel_manager and kernel_name == self.kernel_name:
            self._toolbox.msg.emit("*** Using previously started Julia REPL ***")
            return
        self.kernel_name = kernel_name
        kernel_specs = find_kernel_specs()
        julia_kernel_names = [x for x in kernel_specs if x.startswith('julia')]
        if self.kernel_name not in julia_kernel_names:
            self._toolbox.msg_error.emit("\tCouldn't find a Jupyter kernel "
                                         "specification for {}".format(self.kernel_name))
            self.prompt_to_install_ijulia()
            return
        self.start_new_jupyter_kernel()

    def start_new_jupyter_kernel(self):
        """Start a new Jupyter kernel with the stored kernel name."""
        self.starting = True
        self._toolbox.msg.emit("*** Starting Julia REPL ***")
        kernel_manager = CustomQtKernelManager(kernel_name=self.kernel_name)
        try:
            kernel_manager.start_kernel()
        except FileNotFoundError:
            self._toolbox.msg_error.emit("\tCouldn't find the specified Julia Jupyter kernel.")
            self.prompt_to_reconfigure_ijulia()
            return
        self.kernel_manager = kernel_manager
        self.kernel_manager.kernel_left_dead.connect(self._handle_kernel_left_dead)
        self.setup_client()

    def setup_client(self):
        if not self.kernel_manager:
            return
        kernel_client = self.kernel_manager.client()
        kernel_client.hb_channel.time_to_dead = JL_REPL_TIME_TO_DEAD  # Not crucial, but nicer to keep the same as mngr
        kernel_client.start_channels()
        self.kernel_client = kernel_client

    @Slot(name="_handle_kernel_restarted")
    def _handle_kernel_restarted(self):
        """Called when the kernel is restarted, i.e., when time to dead has elapsed."""
        self._kernel_restarted_message(died=True)
        restart_count = self.kernel_manager._restarter._restart_count
        restart_limit = self.kernel_manager._restarter.restart_limit
        self._toolbox.msg_warning.emit("\tFailed to start Julia Jupyter kernel "
                                       "(attempt {0} of {1})".format(restart_count, restart_limit))

    @Slot(name="_handle_kernel_left_dead")
    def _handle_kernel_left_dead(self):
        """Called when the kernel is finally declared dead, i.e., the restart limit has been reached."""
        restart_limit = self.kernel_manager._restarter.restart_limit
        self._toolbox.msg_error.emit("\tFailed to start Julia Jupyter kernel "
                                     "(attempt {0} of {0})".format(restart_limit))
        self.kernel_manager = None
        self.kernel_client = None  # TODO: needed?
        self.prompt_to_install_ijulia()

    def prompt_to_reconfigure_ijulia(self):
        """Prompt user to reconfigure IJulia via QSubProcess."""
        title = "Unable to start Julia kernel for Jupyter"
        if not self.ijulia_process_succeeded:
            message = "The Julia kernel for Jupyter failed to start. "\
                      "This may be due to a configuration problem in the <b>IJulia</b> package. "\
                      "<p>Do you want to reconfigure it now?</p>"
        else:
            message = "The Julia kernel for Jupyter failed to start. "\
                      "even though IJulia was correctly reconfigured. "\
                      "This may be due to a couple of reasons: <ul>"\
                      "<li> An issue that the automatic reconfiguration process cannot handle. "\
                      "In this case, manual reconfiguration may solve the problem "\
                      "(check out instructions <a href='https://github.com/JuliaLang/IJulia.jl'> here</a>).</li>"\
                      "<li> A change in Julia or IJulia made by another program. "\
                      "This can be solved by running the automatic reconfiguration process again.</li>"\
                      "</ul><p>Do you want to run the automatic reconfiguration process again?</p>"
        answer = QMessageBox.question(self, title, message, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            self.starting = False
            self._control.viewport().setCursor(self.normal_cursor)
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
        args.append("try using Pkg catch; end; ENV[ARGS[1]] = ARGS[2]; Pkg.build(ARGS[3])")
        args.append("JUPYTER")
        args.append("jupyter")
        args.append("IJulia")
        self.ijulia_process = qsubprocess.QSubProcess(self._toolbox, command, args)
        self.ijulia_process.subprocess_finished_signal.connect(self.ijulia_process_finished)
        self.ijulia_process.start_process()

    def prompt_to_install_ijulia(self):
        """Prompt user to install IJulia via QSubProcess."""
        title = "Unable to find Julia kernel for Jupyter"
        if not self.ijulia_process_succeeded:
            message = "There is no Julia kernel for Jupyter available in your system. "\
                      "A Julia kernel is provided by the <b>IJulia</b> package. "\
                      "<p>Do you want to install it now?</p>"
        else:
            message = "The Julia kernel for Jupyter couldn't be found "\
                      "even though IJulia was correctly installed. "\
                      "This may be due to a couple of reasons: <ul>"\
                      "<li> An issue that the automatic installation process cannot handle. "\
                      "In this case, manual installation of IJulia may solve the problem "\
                      "(check out instructions <a href='https://github.com/JuliaLang/IJulia.jl'> here</a>).</li>"\
                      "<li> A change in Julia or IJulia made by another program. "\
                      "This can be solved by running the automatic installation process again.</li>"\
                      "</ul><p>Do you want to run the automatic installation process again?</p>"
        answer = QMessageBox.question(self, title, message, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            self.starting = False
            self._control.viewport().setCursor(self.normal_cursor)
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
        args.append("try using Pkg catch; end; ENV[ARGS[1]] = ARGS[2]; Pkg.add(ARGS[3])")
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
            if self.ijulia_process.process_failed_to_start:
                self._toolbox.msg_error.emit("Process failed to start. Make sure that "
                                             "Julia is installed properly in your system "
                                             "and try again.")
            else:
                self._toolbox.msg_error.emit("Process failed [exit code:{0}]".format(ret))
            self.execution_failed_to_start = True
            self.execution_finished_signal.emit(-9999)
        else:
            self._toolbox.msg.emit("Julia kernel for Jupyter successfully installed.")
            self.ijulia_process_succeeded = True
            # Try to start jupyter kernel again now IJulia is installed/reconfigured
            self.start_new_jupyter_kernel()
        self.ijulia_process.deleteLater()
        self.ijulia_process = None

    @Slot("dict", name="_handle_execute_reply")
    def _handle_execute_reply(self, msg):
        super()._handle_execute_reply(msg)
        if self.running:
            content = msg['content']
            if content['execution_count'] == 0:
                return
            if content['status'] == 'ok':
                self.execution_finished_signal.emit(0)  # success code
            else:
                self.execution_finished_signal.emit(-9999)  # any error code
            self.running = False

    @Slot("dict", name="_handle_status")
    def _handle_status(self, msg):
        """Handle status message"""
        super()._handle_status(msg)
        self.kernel_execution_state = msg['content'].get('execution_state', '')
        if self.kernel_execution_state == 'idle':
            if self.starting:
                self.starting = False
                self._toolbox.msg_success.emit("\tJulia REPL successfully started "
                                               "using {}".format(self.kernel_name))
                self._control.viewport().setCursor(self.normal_cursor)
            if self.command:
                self.running = True
                self.execute(self.command)
                self.command = None

    @Slot("dict", name="_handle_error")
    def _handle_error(self, msg):
        """Handle error messages."""
        super()._handle_error(msg)
        if self.running:
            self.execution_finished_signal.emit(-9999)  # any error code
            self.running = False

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
        kernel_name = self.julia_kernel_name()
        if not kernel_name:
            return
        if kernel_name != self.kernel_name:
            self.kernel_name = kernel_name
            self.start_new_jupyter_kernel()
            return
        self.starting = True
        self._toolbox.msg.emit("*** Restarting Julia REPL ***")
        self.kernel_client.stop_channels()
        self.kernel_manager.restart_kernel(now=True)
        self.setup_client()

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
