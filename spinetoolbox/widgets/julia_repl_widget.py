######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

import logging
from PySide2.QtWidgets import QMessageBox, QAction, QApplication
from PySide2.QtCore import Slot, Signal, Qt
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager, QtKernelRestarter
from jupyter_client.kernelspec import find_kernel_specs, NoSuchKernel
from ..config import JULIA_EXECUTABLE, JL_REPL_TIME_TO_DEAD, JL_REPL_RESTART_LIMIT
from ..executioner import ExecutionState
from .toolbars import DraggableWidget
from spinetoolbox import qsubprocess
from ..helpers import busy_effect


class CustomQtKernelManager(QtKernelManager):
    """A QtKernelManager with a custom restarter, and a means to override the --project argument."""

    kernel_left_dead = Signal(name="kernel_left_dead")

    project_path = None

    @property
    def kernel_spec(self):
        if self._kernel_spec is None and self.kernel_name != "":
            self._kernel_spec = self.kernel_spec_manager.get_kernel_spec(self.kernel_name)
            self.override_project_arg()
        return self._kernel_spec

    def override_project_arg(self):
        if self.project_path is None:
            return
        ind = next((k for k, x in enumerate(self._kernel_spec.argv) if x.startswith("--project")), None)
        if not ind:
            return
        self._kernel_spec.argv[ind] = f"--project={self.project_path}"

    def start_restarter(self):
        """Starts a restarter with custom time to dead and restart limit."""
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
        self.julia_exe = None
        self.julia_project_path = None
        self.execution_failed_to_start = False
        self.starting = False
        self.normal_cursor = self._control.viewport().cursor()
        # Actions
        self._copy_input_action = QAction('Copy (Only Input)', self)
        self._copy_input_action.triggered.connect(lambda checked: self.copy_input())
        self._copy_input_action.setEnabled(False)
        self.copy_available.connect(self._copy_input_action.setEnabled)
        self.start_repl_action = QAction("Start", self)
        self.start_repl_action.triggered.connect(lambda checked: self.start_jupyter_kernel())
        self.restart_repl_action = QAction("Restart", self)
        self.restart_repl_action.triggered.connect(lambda checked: self.restart_jupyter_kernel())
        # Set logging level for jupyter module loggers
        traitlets_logger = logging.getLogger("traitlets")
        asyncio_logger = logging.getLogger("asyncio")
        traitlets_logger.setLevel(level=logging.WARNING)
        asyncio_logger.setLevel(level=logging.WARNING)

    @busy_effect
    def julia_kernel_name(self):
        """Returns the name of the julia kernel specification according to the
        julia executable selected in settings. Returns None if julia version
        cannot be determined.

        Returns:
            str, NoneType
        """
        self._toolbox.msg.emit("\tInitializing Julia...")
        julia_path = self._toolbox.qsettings().value("appSettings/juliaPath", defaultValue="")
        if julia_path != "":
            self.julia_exe = julia_path
        else:
            self.julia_exe = JULIA_EXECUTABLE
        program = "{0}".format(self.julia_exe)
        args = list()
        args.append("-e")
        args.append("println(VERSION)")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        if not q_process.wait_for_finished(msecs=5000):
            self._toolbox.msg_error.emit(
                "\tCouldn't find out Julia version. Make sure that Julia is correctly installed and try again."
            )
            return None
        julia_version = q_process.output
        self._toolbox.msg.emit("\tJulia version is {0}".format(julia_version))
        kernel_name = "julia-" + ".".join(julia_version.split(".")[0:2])
        if self.kernel_name is not None and self.kernel_name != kernel_name:
            self._toolbox.msg_warning.emit(
                "\tJulia version has changed in settings. New kernel specification is {0}".format(kernel_name)
            )
        return kernel_name

    def start_jupyter_kernel(self):
        """Starts a Julia Jupyter kernel if available.

        Returns:
            bool: True if the kernel is started, or in process of being started (installing/reconfiguring IJulia)
                False if the kernel cannot be started and the user chooses not to install/reconfigure IJulia
        """
        kernel_name = self.julia_kernel_name()
        if not kernel_name:
            return False
        julia_project_path = self._toolbox.qsettings().value("appSettings/juliaProjectPath", defaultValue="")
        if julia_project_path == "":
            julia_project_path = "@."
        if self.kernel_manager and kernel_name == self.kernel_name and julia_project_path == self.julia_project_path:
            self._toolbox.msg.emit("*** Using previously started Julia Console ***")
            return True
        self.julia_project_path = julia_project_path
        self.kernel_execution_state = None
        kernel_specs = find_kernel_specs()
        # logging.debug("kernel_specs:{0}".format(kernel_specs))
        julia_kernel_names = [x for x in kernel_specs if x.startswith('julia')]
        if kernel_name in julia_kernel_names:
            return self._do_start_jupyter_kernel(kernel_name)
        self._toolbox.msg_error.emit("\tCouldn't find kernel specification {0}".format(kernel_name))
        return self.handle_repl_failed_to_start()

    def _do_start_jupyter_kernel(self, kernel_name=None):
        """Starts a Jupyter kernel with the specified name.

        Args:
            kernel_name (str, optional)

        Returns:
            bool: True if the kernel is started, or in process of being started (reconfiguring IJulia)
                False if the kernel cannot be started and the user chooses not to reconfigure IJulia
        """
        if kernel_name:
            self.kernel_name = kernel_name
        self.starting = True
        self._toolbox.msg.emit("*** Starting Julia Console ***")
        kernel_manager = CustomQtKernelManager(kernel_name=self.kernel_name, project_path=self.julia_project_path)
        try:
            kernel_manager.start_kernel()
            self.kernel_manager = kernel_manager
            self.kernel_manager.kernel_left_dead.connect(self._handle_kernel_left_dead)
            self.setup_client()
            return True
        except FileNotFoundError:
            self._toolbox.msg_error.emit("\tCouldn't find Julia executable specified by Jupyter kernel.")
            return self.handle_repl_failed_to_start()
        except NoSuchKernel:  # TODO: in which case this exactly happens?
            self._toolbox.msg_error.emit("\t[NoSuchKernel] Couldn't find Julia Jupyter kernel.")
            return self.handle_repl_failed_to_start()

    def check_ijulia(self):
        """Checks if IJulia is installed.

        Returns:
            (bool, NoneType): True, False, or None if unable to determine."""
        self._toolbox.msg.emit("\tChecking whether IJulia is installed or not...")
        program = "{0}".format(self.julia_exe)
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; try using IJulia; println(ARGS[1]) catch; println(ARGS[2]) end")
        args.append("True")
        args.append("False")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        if not q_process.wait_for_finished(msecs=5000):
            self._toolbox.msg_error.emit(
                "\tCouldn't start Julia to check IJulia status. "
                "Please make sure that Julia is correctly installed and try again."
            )
            return None
        if q_process.output == "True":
            self._toolbox.msg.emit("\tIJulia is installed")
            return True
        self._toolbox.msg.emit("\tIJulia is not installed")
        return False

    def handle_repl_failed_to_start(self):
        """Prompts user to install IJulia if missing, or to rebuild it otherwise.

        Returns:
            bool: True or False depending on whether or not the problem is being handled.
        """
        check_ijulia = self.check_ijulia()
        if check_ijulia is None:
            # Unable to determine
            return False
        if not check_ijulia:
            # IJulia is not installed, try installing it
            # First find out active project to ask user's permission to change it
            program = "{0}".format(self.julia_exe)
            args = list()
            args.append(f"--project={self.julia_project_path}")
            args.append("-e")
            args.append("println(Base.active_project())")
            q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
            q_process.start_process()
            if not q_process.wait_for_finished(msecs=5000):
                self._toolbox.msg_error.emit(
                    "\tCouldn't find out Julia active project. "
                    "Make sure that Julia is correctly installed and try again."
                )
                return False
            julia_active_project = q_process.output
            msg = QMessageBox(parent=self._toolbox)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("IJulia installation needed")
            msg.setText(
                "Spine Toolbox needs to do the following modifications to the Julia project at <b>{0}</b>:"
                "<p>Install the IJulia package.".format(julia_active_project)
            )
            allow_button = msg.addButton("Allow", QMessageBox.YesRole)
            msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec_()  # Show message box
            if msg.clickedButton() != allow_button:
                self.starting = False
                self._control.viewport().setCursor(self.normal_cursor)
                return False
            command = "{0}".format(self.julia_exe)
            args = list()
            args.append(f"--project={self.julia_project_path}")
            args.append("-e")
            args.append("try using Pkg catch; end; Pkg.add(ARGS[1])")
            args.append("IJulia")
            self.ijulia_process = qsubprocess.QSubProcess(self._toolbox, command, args)
            self.ijulia_process.subprocess_finished_signal.connect(self.handle_ijulia_installation_finished)
            self.ijulia_process.start_process()
            self._toolbox.msg.emit("*** Installing <b>IJulia</b> ***")
            self._toolbox.msg_warning.emit("<b>Depending on your system, this process can take a few minutes...</b>")
        else:
            # IJulia is installed but repl still failed to start, try rebuilding IJulia
            # TODO: what happens if this doesn't solve the problem? Is this some sort of infinite loop?
            command = "{0}".format(self.julia_exe)
            args = list()
            args.append("-e")
            args.append("try using Pkg catch; end; Pkg.build(ARGS[1])")
            args.append("IJulia")
            self.ijulia_process = qsubprocess.QSubProcess(self._toolbox, command, args)
            self.ijulia_process.subprocess_finished_signal.connect(self.handle_ijulia_rebuild_finished)
            self.ijulia_process.start_process()
            self._toolbox.msg.emit("*** Re-building <b>IJulia</b> ***")
            self._toolbox.msg_warning.emit("<b>Depending on your system, this process can take a few minutes...</b>")
        return True

    def restart_jupyter_kernel(self):
        """Restarts the julia jupyter kernel if it's already started.
        Starts a new kernel if none started or if the julia version has changed in Settings.
        """
        kernel_name = self.julia_kernel_name()
        if not kernel_name:
            return
        julia_project_path = self._toolbox.qsettings().value("appSettings/juliaProjectPath", defaultValue="")
        if julia_project_path == "":
            julia_project_path = "@."
        if self.kernel_manager and kernel_name == self.kernel_name and julia_project_path == self.julia_project_path:
            # Restart current kernel
            self.starting = True
            self._toolbox.msg.emit("*** Restarting Julia REPL ***")
            self.kernel_client.stop_channels()
            self.kernel_manager.restart_kernel(now=True)
            self.setup_client()
        else:
            # No kernel to restart (!) or julia has changed in settings. Start a new kernel
            self.julia_project_path = julia_project_path
            kernel_specs = find_kernel_specs()
            julia_kernel_names = [x for x in kernel_specs if x.startswith('julia')]
            if kernel_name in julia_kernel_names:
                self._do_start_jupyter_kernel(kernel_name)
            else:
                self._toolbox.msg_error.emit("\tCouldn't find Jupyter kernel specification for {}".format(kernel_name))
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
        self._toolbox.msg_warning.emit(
            "\tFailed to start Julia Jupyter kernel (attempt {0} of {1})".format(restart_count, restart_limit)
        )

    @Slot(name="_handle_kernel_left_dead")
    def _handle_kernel_left_dead(self):
        """Called when the kernel is finally declared dead, i.e., the restart limit has been reached."""
        restart_limit = self.kernel_manager._restarter.restart_limit
        self._toolbox.msg_error.emit(
            "\tFailed to start Julia Jupyter kernel (attempt {0} of {0})".format(restart_limit)
        )
        self.kernel_manager = None
        self.kernel_client = None  # TODO: needed?
        self.handle_repl_failed_to_start()

    @Slot(int, name="handle_ijulia_installation_finished")
    def handle_ijulia_installation_finished(self, ret):
        """Runs when IJulia installation process finishes"""
        if self.check_ijulia_process(ret):
            self._toolbox.msg.emit("IJulia successfully installed.")
            # Try to start jupyter kernel again now IJulia is installed/reconfigured
            self._do_start_jupyter_kernel()
        self.ijulia_process.deleteLater()
        self.ijulia_process = None

    @Slot(int, name="handle_ijulia_rebuild_finished")
    def handle_ijulia_rebuild_finished(self, ret):
        """Runs when IJulia rebuild process finishes"""
        if self.check_ijulia_process(ret):
            self._toolbox.msg.emit("IJulia successfully rebuild.")
            # Try to start jupyter kernel again now IJulia is installed/reconfigured
            self._do_start_jupyter_kernel()
        self.ijulia_process.deleteLater()
        self.ijulia_process = None

    def check_ijulia_process(self, ret):
        """Checks whether or not the IJulia process finished successfully.

        Returns:
            bool
        """
        if self.ijulia_process.process_failed:
            if self.ijulia_process.process_failed_to_start:
                self._toolbox.msg_error.emit(
                    "Process failed to start. Please make sure that Julia is properly installed and try again."
                )
            else:
                self._toolbox.msg_error.emit("Process failed [exit code:{0}]".format(ret))
            if self.command:
                self.execution_failed_to_start = True
                self.execution_finished_signal.emit(-9999)
                self.command = None
            return False
        return True

    @Slot("dict", name="_handle_execute_reply")
    def _handle_execute_reply(self, msg):
        super()._handle_execute_reply(msg)
        if self.running:
            content = msg['content']
            if content['execution_count'] == 0:
                return  # This is not the instance, this is just the kernel saying hello
            self.running = False
            self.command = None
            if content['status'] == 'ok':
                self.execution_finished_signal.emit(0)  # success code
            else:
                self.execution_finished_signal.emit(-9999)  # any error code

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
                self._toolbox.msg_success.emit(
                    "\tJulia REPL successfully started using kernel specification {}".format(self.kernel_name)
                )
                self._control.viewport().setCursor(self.normal_cursor)
            elif self.command and not self.running:
                self._toolbox.msg_warning.emit("\tExecution in progress. See <b>Julia Console</b> for messages.")
                self.running = True
                self.execute(self.command)

    @Slot("dict", name="_handle_error")
    def _handle_error(self, msg):
        """Handle error messages."""
        super()._handle_error(msg)
        if self.running:
            self.running = False
            self.command = None
            self.execution_finished_signal.emit(-9999)  # any error code

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
            self._toolbox.msg_warning.emit("\tExecution in progress. See <b>Julia Console</b> for messages.")
            self.running = True
            self.execute(self.command)

    def terminate_process(self):
        """Send interrupt signal to kernel."""
        # logging.debug("interrupt exec")
        self.kernel_manager.interrupt_kernel()
        # TODO: Block execution until kernel has been interrupted and then emit the signal
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(
            ExecutionState.STOP_REQUESTED
        )

    def shutdown_jupyter_kernel(self):
        """Shut down the jupyter kernel."""
        if not self.kernel_client:
            return
        self._toolbox.msg.emit("Shutting down Julia Console...")
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

    def dragEnterEvent(self, e):
        """Don't accept drops from Add Item Toolbar."""
        source = e.source()
        if isinstance(source, DraggableWidget):
            e.ignore()
        else:
            super().dragEnterEvent(e)

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
                useful_lines.append(line[len(m.group(0)) :])
                continue
            m = self._highlighter._ipy_prompt_re.match(line)
            if m:
                useful_lines.append(line[len(m.group(0)) :])
                continue
        text = '\n'.join(useful_lines)
        try:
            was_newline = text[-1] == '\n'
        except IndexError:
            was_newline = False
        if was_newline:  # user doesn't need newline
            text = text[:-1]
        QApplication.clipboard().setText(text)
