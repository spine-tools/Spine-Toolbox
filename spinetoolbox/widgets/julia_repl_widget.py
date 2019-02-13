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
from PySide2.QtWidgets import QMessageBox, QAction, QApplication
from PySide2.QtCore import Slot, Signal, Qt
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from jupyter_client.kernelspec import find_kernel_specs, NoSuchKernel
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
        self.ijulia_fix = None  # Either "Installing" or "Re-building"
        self.julia_exe = None
        self.execution_failed_to_start = False
        self.starting = False
        self.normal_cursor = self._control.viewport().cursor()
        # Actions
        self._copy_input_action = QAction('Copy (Only Input)', self)
        self._copy_input_action.triggered.connect(lambda checked: self.copy_input())
        self._copy_input_action.setEnabled(False)
        self.copy_available.connect(self._copy_input_action.setEnabled)
        self.start_repl_action = QAction("Start REPL", self)
        self.start_repl_action.triggered.connect(lambda checked: self.start_jupyter_kernel())
        self.restart_repl_action = QAction("Restart REPL", self)
        self.restart_repl_action.triggered.connect(lambda checked: self.restart_jupyter_kernel())
        # Set logging level for jupyter module loggers
        traitlets_logger = logging.getLogger("traitlets")
        asyncio_logger = logging.getLogger("asyncio")
        traitlets_logger.setLevel(level=logging.WARNING)
        asyncio_logger.setLevel(level=logging.WARNING)

    @busy_effect
    def julia_kernel_name(self):
        """Return the name of the julia kernel specification, according to julia executable from settings.
        Return None if julia version can't be determined.
        """
        self._toolbox.msg.emit("\tInitializing Julia...")
        julia_dir = self._toolbox._config.get("settings", "julia_path")
        if not julia_dir == '':
            self.julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
        else:
            self.julia_exe = JULIA_EXECUTABLE
        program = "{0}".format(self.julia_exe)
        args = list()
        args.append("-e")
        args.append("println(VERSION)")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        if not q_process.wait_for_finished(msecs=5000):
            self._toolbox.msg_error.emit("\tCouldn't determine Julia version. "
                                         "Make sure that Julia is correctly installed "
                                         "and try again.")
            return None
        julia_version = q_process.output
        self._toolbox.msg.emit("\tJulia version is {0}".format(julia_version))
        kernel_name = "julia-" + ".".join(julia_version.split(".")[0:2])
        if self.kernel_name is not None and self.kernel_name != kernel_name:
            self._toolbox.msg_warning.emit("\tJulia version has changed in settings. "
                                           "New kernel specification is {0}".format(kernel_name))
        return kernel_name

    def start_jupyter_kernel(self):
        """Start a Julia Jupyter kernel if available.

        Returns:
            True if the kernel is started, or in process of being started (installing/reconfiguring IJulia)
            False if the kernel cannot be started and the user chooses not to install/reconfigure IJulia
        """
        kernel_name = self.julia_kernel_name()
        if not kernel_name:
            return False
        if self.kernel_manager and kernel_name == self.kernel_name:
            self._toolbox.msg.emit("*** Using previously started Julia REPL ***")
            return True
        self.kernel_name = kernel_name
        self.kernel_execution_state = None
        kernel_specs = find_kernel_specs()
        julia_kernel_names = [x for x in kernel_specs if x.startswith('julia')]
        if self.kernel_name in julia_kernel_names:
            return self.start_available_jupyter_kernel()
        else:
            self._toolbox.msg_error.emit("\tCouldn't find the {0} kernel specification".format(self.kernel_name))
            return self.handle_repl_failed_to_start()

    def start_available_jupyter_kernel(self):
        """Start a Jupyter kernel which is available (from the attribute `kernel_name`)

        Returns:
            True if the kernel is started, or in process of being started (reconfiguring IJulia)
            False if the kernel cannot be started and the user chooses not to reconfigure IJulia
        """
        self.starting = True
        self._toolbox.msg.emit("*** Starting Julia REPL ***")
        kernel_manager = CustomQtKernelManager(kernel_name=self.kernel_name)
        try:
            kernel_manager.start_kernel()
            self.kernel_manager = kernel_manager
            self.kernel_manager.kernel_left_dead.connect(self._handle_kernel_left_dead)
            self.setup_client()
            return True
        except FileNotFoundError:
            self._toolbox.msg_error.emit("\tCouldn't find the Julia executable specified by the Jupyter kernel.")
            return self.handle_repl_failed_to_start()
        except NoSuchKernel:  # TODO: in which case this exactly happens?
            self._toolbox.msg_error.emit("\t[NoSuchKernel] Couldn't find the specified Julia Jupyter kernel.")
            return self.handle_repl_failed_to_start()

    def is_ijulia_installed(self):
        """Check if IJulia is installed, returns True, False, or None if unable to determine."""
        self._toolbox.msg.emit("\tFinding out whether IJulia is installed or not...")
        program = "{0}".format(self.julia_exe)
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; try using IJulia; println(ARGS[1]) catch; println(ARGS[2]) end")
        args.append("True")
        args.append("False")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        if not q_process.wait_for_finished(msecs=5000):
            self._toolbox.msg_error.emit("\tCouldn't start Julia to check IJulia status. "
                                         "Make sure that Julia is correctly installed "
                                         "and try again.")
            return None
        if q_process.output == "True":
            self._toolbox.msg.emit("\tIJulia is installed")
            return True
        self._toolbox.msg.emit("\tIJulia is not installed")
        return False

    def handle_repl_failed_to_start(self):
        """Prompt user to install IJulia if missing, or rebuild it otherwise.

        Returns:
            Bolean value depending on whether or not the user chooses to proceed.
        """
        is_ijulia_installed = self.is_ijulia_installed()
        if is_ijulia_installed is None:
            return False
        title = "Julia REPL failed to start"
        if not is_ijulia_installed:
            self.ijulia_fix = "Installing"
            message = "The Julia REPL failed to start because "\
                      "the <a href='https://github.com/JuliaLang/IJulia.jl'>IJulia</a> package "\
                      "is missing."\
                      "<p>Do you want to install <b>IJulia</b> now?</p>"\
                      "<p>Note: after installation, "\
                      "the current operation will resume automatically.".\
                      format(self.kernel_name)
        else:
            self.ijulia_fix = "Re-building"
            message = "The Julia REPL failed to start because of a problem "\
                      "with the Julia Jupyter kernel specification ({0})."\
                      "<p>Re-building the <a href='https://github.com/JuliaLang/IJulia.jl'>IJulia</a> "\
                      "package may help to fix this problem."\
                      "<p>Do you want to re-build <b>IJulia</b> now?</p>"\
                      "<p>Note: after re-building, "\
                      "the current operation will resume automatically.".\
                      format(self.kernel_name)
        answer = QMessageBox.question(self, title, message, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            self.starting = False
            self._control.viewport().setCursor(self.normal_cursor)
            return False
        self._toolbox.msg.emit("*** {0} <b>IJulia</b> ***".format(self.ijulia_fix))
        self._toolbox.msg_warning.emit("<b>Depending on your system, this process can take a few minutes...</b>")
        # Follow installation instructions in https://github.com/JuliaLang/IJulia.jl
        command = "{0}".format(self.julia_exe)
        args = list()
        args.append("-e")
        if self.ijulia_fix == "Installing":
            args.append("try using Pkg catch; end; Pkg.add(ARGS[1])")
        else:
            args.append("try using Pkg catch; end; Pkg.build(ARGS[1])")
        args.append("IJulia")
        self.ijulia_process = qsubprocess.QSubProcess(self._toolbox, command, args)
        self.ijulia_process.subprocess_finished_signal.connect(self.ijulia_process_finished)
        self.ijulia_process.start_process()
        return True

    def restart_jupyter_kernel(self):
        """Restart the julia jupyter kernel if it's already started. Otherwise, or if the julia version
        has changed in settings, start a new jupyter kernel.
        """
        kernel_name = self.julia_kernel_name()
        if not kernel_name:
            return
        if self.kernel_manager and kernel_name == self.kernel_name:
            # Restart current kernel
            self.starting = True
            self._toolbox.msg.emit("*** Restarting Julia REPL ***")
            self.kernel_client.stop_channels()
            self.kernel_manager.restart_kernel(now=True)
            self.setup_client()
        else:
            # No kernel to restart (!) or julia has changed in settings. Start a new kernel
            self.kernel_name = kernel_name
            kernel_specs = find_kernel_specs()
            julia_kernel_names = [x for x in kernel_specs if x.startswith('julia')]
            if self.kernel_name in julia_kernel_names:
                self.start_available_jupyter_kernel()
            else:
                self._toolbox.msg_error.emit("\tCouldn't find a Jupyter kernel "
                                             "specification for {}".format(self.kernel_name))
                self.handle_repl_failed_to_start()

    def setup_client(self):
        if not self.kernel_manager:
            return
        kernel_client = self.kernel_manager.client()
        kernel_client.hb_channel.time_to_dead = JL_REPL_TIME_TO_DEAD  # Not crucial, but nicer to keep the same as mngr
        kernel_client.start_channels()
        self.kernel_client = kernel_client

    @Slot(name="_handle_kernel_restarted")
    def _handle_kernel_restarted(self, died=True):
        """Called when the kernel is restarted, i.e., when time to dead has elapsed."""
        super()._handle_kernel_restarted(died=died)
        if not died:
            return
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
        self.handle_repl_failed_to_start()

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
            if self.command:
                self.execution_failed_to_start = True
                self.execution_finished_signal.emit(-9999)
                self.command = None
        else:
            if self.ijulia_fix == "Installing":
                self._toolbox.msg.emit("Julia kernel for Jupyter successfully installed.")
            else:
                self._toolbox.msg.emit("Julia kernel for Jupyter successfully re-built.")
            # Try to start jupyter kernel again now IJulia is installed/reconfigured
            self.start_available_jupyter_kernel()
        self.ijulia_process.deleteLater()
        self.ijulia_process = None

    @Slot("dict", name="_handle_execute_reply")
    def _handle_execute_reply(self, msg):
        super()._handle_execute_reply(msg)
        if self.running:
            content = msg['content']
            if content['execution_count'] == 0:
                return  # This is not the instance, this is just the kernel saying hello
            if content['status'] == 'ok':
                self.execution_finished_signal.emit(0)  # success code
            else:
                self.execution_finished_signal.emit(-9999)  # any error code
            self.running = False
            self.command = None

    @Slot("dict", name="_handle_status")
    def _handle_status(self, msg):
        """Handle status message. If we have a command in line
        and the kernel reports status 'idle', execute that command.
        """
        super()._handle_status(msg)
        self.kernel_execution_state = msg['content'].get('execution_state', '')
        if self.kernel_execution_state == 'idle':
            if self.starting:
                self.starting = False
                self._toolbox.msg_success.emit("\tJulia REPL successfully started using "
                                               "the {} kernel specification".format(self.kernel_name))
                self._control.viewport().setCursor(self.normal_cursor)
            elif self.command and not self.running:
                self._toolbox.msg_warning.emit("\tExecution is in progress. See Julia Console for messages.")
                self.running = True
                self.execute(self.command)

    @Slot("dict", name="_handle_error")
    def _handle_error(self, msg):
        """Handle error messages."""
        super()._handle_error(msg)
        if self.running:
            self.execution_finished_signal.emit(-9999)  # any error code
            self.running = False

    def execute_instance(self, command):
        """Try and start the jupyter kernel.
        Execute command immediately if kernel is idle.
        If not, it will be executed as soon as the kernel
        becomes idle (see `_handle_status` method).
        """
        if not command:
            return
        self.command = command
        if not self.start_jupyter_kernel():
            self.execution_failed_to_start = True
            self.execution_finished_signal.emit(-9999)
            return
        # Kernel is started or in process of being started
        if self.kernel_execution_state == 'idle' and not self.running:
            self._toolbox.msg_warning.emit("\tExecution is in progress. See Julia Console for messages.")
            self.running = True
            self.execute(self.command)

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

    def _context_menu_make(self, pos):
        """ Reimplemented to add an action for (re)start REPL action.
        """
        menu = super()._context_menu_make(pos)
        for before_action in menu.actions():
            if before_action.text() == 'Copy (Raw Text)':
                menu.insertAction(before_action, self._copy_input_action)
                break
        first_action = menu.actions()[0]
        if not self.kernel_manager:
            menu.insertAction(first_action, self.start_repl_action)
        else:
            self.restart_repl_action.setEnabled(not self.command)
            menu.insertAction(first_action, self.restart_repl_action)
        menu.insertSeparator(first_action)
        return menu

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

    def copy_input(self):
        """Copy only input."""
        if not self._control.hasFocus():
            return
        text = self._control.textCursor().selection().toPlainText()
        if not text:
            return
        # Remove prompts.
        lines = text.splitlines()
        useful_lines = []
        for line in lines:
            m = self._highlighter._classic_prompt_re.match(line)
            if m:
                useful_lines.append(line[len(m.group(0)):])
                continue
            m = self._highlighter._ipy_prompt_re.match(line)
            if m:
                useful_lines.append(line[len(m.group(0)):])
                continue
        text = '\n'.join(useful_lines)
        try:
            was_newline = text[-1] == '\n'
        except IndexError:
            was_newline = False
        if was_newline:  # user doesn't need newline
            text = text[:-1]
        QApplication.clipboard().setText(text)
