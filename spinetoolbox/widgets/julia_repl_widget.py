######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Class for a custom SpineConsoleWidget to use as julia REPL.

:author: M. Marin (KTH)
:date:   22.5.2018
"""

import os
import logging
from PySide2.QtWidgets import QMessageBox, QAction, QApplication
from PySide2.QtCore import Slot, Signal, Qt
from qtconsole.manager import QtKernelManager, QtKernelRestarter
from jupyter_client.kernelspec import find_kernel_specs, NoSuchKernel
from ..execution_managers import QProcessExecutionManager
from ..config import JULIA_EXECUTABLE, JL_REPL_TIME_TO_DEAD, JL_REPL_RESTART_LIMIT
from .toolbars import DraggableWidget
from ..helpers import busy_effect
from .spine_console_widget import SpineConsoleWidget


class CustomQtKernelManager(QtKernelManager):
    """A QtKernelManager with a custom restarter, and a means to override the --project argument."""

    kernel_left_dead = Signal()

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


class JuliaREPLWidget(SpineConsoleWidget):
    """Class for a custom SpineConsoleWidget.
    """

    name = "Julia Console"

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): QMainWindow instance
        """
        super().__init__(toolbox)
        self.custom_restart = True
        self.kernel_name = None  # The name of the Julia kernel from settings last checked
        self.kernel_manager = None
        self.kernel_client = None
        self.kernel_execution_state = None
        self.ijulia_proc_exec_mngr = None  # IJulia installation/reconfiguration process exec manager
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
        exec_mngr = QProcessExecutionManager(self._toolbox, program, args, silent=True)
        exec_mngr.start_execution()
        if not exec_mngr.wait_for_process_finished(msecs=5000):
            self._toolbox.msg_error.emit(
                "\tCouldn't find out Julia version. Make sure that Julia is correctly installed and try again."
            )
            return None
        julia_version = exec_mngr.process_output
        self._toolbox.msg.emit("\tJulia version is {0}".format(julia_version))
        kernel_name = "julia-" + ".".join(julia_version.split(".")[0:2])
        if self.kernel_name is not None and self.kernel_name != kernel_name:
            self._toolbox.msg_warning.emit(
                "\tJulia version has changed in settings. New kernel specification is {0}".format(kernel_name)
            )
        return kernel_name

    def start_jupyter_kernel(self):
        """Starts a Julia Jupyter kernel if available."""
        kernel_name = self.julia_kernel_name()
        if not kernel_name:
            self.execution_failed.emit(-1)
            return
        julia_project_path = self._toolbox.qsettings().value("appSettings/juliaProjectPath", defaultValue="")
        if julia_project_path == "":
            julia_project_path = "@."
        if self.kernel_manager and kernel_name == self.kernel_name and julia_project_path == self.julia_project_path:
            self._toolbox.msg.emit("*** Using previously started Julia Console ***")
            self.ready_to_execute.emit()
            return
        self.julia_project_path = julia_project_path
        self.kernel_execution_state = None
        kernel_specs = find_kernel_specs()
        # logging.debug("kernel_specs:{0}".format(kernel_specs))
        julia_kernel_names = [x for x in kernel_specs if x.startswith('julia')]
        if kernel_name in julia_kernel_names:
            self._do_start_jupyter_kernel(kernel_name)
            return
        self._toolbox.msg_error.emit("\tCouldn't find kernel specification {0}".format(kernel_name))
        self.handle_repl_failed_to_start()

    def _do_start_jupyter_kernel(self, kernel_name=None):
        """Starts a Jupyter kernel with the specified name.

        Args:
            kernel_name (str, optional)
        """
        if kernel_name:
            self.kernel_name = kernel_name
        self.starting = True
        self._toolbox.msg.emit("*** Starting Julia Console ***")
        kernel_manager = CustomQtKernelManager(kernel_name=self.kernel_name, project_path=self.julia_project_path)
        try:
            blackhole = open(os.devnull, 'w')
            kernel_manager.start_kernel(stdout=blackhole, stderr=blackhole)
            self.kernel_manager = kernel_manager
            self.kernel_manager.kernel_left_dead.connect(self._handle_kernel_left_dead)
            self.setup_client()
        except FileNotFoundError:
            self._toolbox.msg_error.emit("\tCouldn't find Julia executable specified by Jupyter kernel.")
            self.handle_repl_failed_to_start()
        except NoSuchKernel:  # TODO: in which case this exactly happens?
            self._toolbox.msg_error.emit("\t[NoSuchKernel] Couldn't find Julia Jupyter kernel.")
            self.handle_repl_failed_to_start()

    def handle_repl_failed_to_start(self):
        """Tries using IJulia.

        Returns:
            (bool, NoneType): True, False, or None if unable to determine."""
        self._toolbox.msg.emit("\tChecking whether IJulia is installed or not...")
        program = "{0}".format(self.julia_exe)
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; try using IJulia; println(ARGS[1]) catch; println(ARGS[2]) end")
        args.append("True")
        args.append("False")
        exec_mngr = QProcessExecutionManager(self._toolbox, program, args, silent=True)
        exec_mngr.start_execution()
        if not exec_mngr.wait_for_process_finished(msecs=5000):
            self._toolbox.msg_error.emit(
                "\tCouldn't start Julia to check IJulia status. "
                "Please make sure that Julia is correctly installed and try again."
            )
            self.execution_failed.emit(-1)
            return
        if exec_mngr.process_output == "True":
            self._toolbox.msg.emit("\tIJulia is installed")
            self._try_rebuilding_ijulia()
            return
        self._toolbox.msg.emit("\tIJulia is not installed")
        self._try_installing_ijulia()

    def _try_installing_ijulia(self):
        """Prompts user to install IJulia."""
        # First find out active project to ask user's permission to change it
        program = "{0}".format(self.julia_exe)
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("println(Base.active_project())")
        exec_mngr = QProcessExecutionManager(self._toolbox, program, args, silent=True)
        exec_mngr.start_execution()
        if not exec_mngr.wait_for_process_finished(msecs=5000):
            self._toolbox.msg_error.emit(
                "\tCouldn't find out Julia active project. "
                "Make sure that Julia is correctly installed and try again."
            )
            self.execution_failed.emit(-1)
            return
        julia_active_project = exec_mngr.process_output
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
            self.execution_failed.emit(-1)
            return
        self._do_try_installing_ijulia()

    def _do_try_installing_ijulia(self):
        command = "{0}".format(self.julia_exe)
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("try using Pkg catch; end; Pkg.add(ARGS[1])")
        args.append("IJulia")
        self.ijulia_proc_exec_mngr = QProcessExecutionManager(self._toolbox, command, args)
        self.ijulia_proc_exec_mngr.execution_finished.connect(self.handle_ijulia_installation_finished)
        self.ijulia_proc_exec_mngr.start_execution()
        self._toolbox.msg.emit("*** Installing <b>IJulia</b> ***")
        self._toolbox.msg_warning.emit("<b>Depending on your system, this process can take a few minutes...</b>")

    def _try_rebuilding_ijulia(self):
        # TODO: what happens if this doesn't solve the problem? Is this some sort of infinite loop?
        command = "{0}".format(self.julia_exe)
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; Pkg.build(ARGS[1])")
        args.append("IJulia")
        self.ijulia_proc_exec_mngr = QProcessExecutionManager(self._toolbox, command, args)
        self.ijulia_proc_exec_mngr.execution_finished.connect(self.handle_ijulia_rebuild_finished)
        self.ijulia_proc_exec_mngr.start_execution()
        self._toolbox.msg.emit("*** Re-building <b>IJulia</b> ***")
        self._toolbox.msg_warning.emit("<b>Depending on your system, this process can take a few minutes...</b>")

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
            blackhole = open(os.devnull, 'w')
            self.kernel_manager.restart_kernel(now=True, stdout=blackhole, stderr=blackhole)
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

    @Slot(int)
    def handle_ijulia_installation_finished(self, ret):
        """Runs when IJulia installation process finishes"""
        self.handle_ijulia_process_finished(ret, "installation")

    @Slot(int)
    def handle_ijulia_rebuild_finished(self, ret):
        """Runs when IJulia rebuild process finishes"""
        self.handle_ijulia_process_finished(ret, "reconfiguration")

    def handle_ijulia_process_finished(self, ret, process):
        """Checks whether or not the IJulia process finished successfully."""
        if self.ijulia_proc_exec_mngr.process_failed:
            if self.ijulia_proc_exec_mngr.process_failed_to_start:
                self._toolbox.msg_error.emit(
                    "Julia failed to start. Please make sure that Julia is properly installed and try again."
                )
            else:
                self._toolbox.msg_error.emit("Julia failed [exit code:{0}]".format(ret))
            self.execution_failed.emit(-1)
        else:
            self._toolbox.msg.emit(f"IJulia {process} successful.")
            self._do_start_jupyter_kernel()
        self.ijulia_proc_exec_mngr.deleteLater()
        self.ijulia_proc_exec_mngr = None

    @Slot("dict", name="_handle_execute_reply")
    def _handle_execute_reply(self, msg):
        super()._handle_execute_reply(msg)
        content = msg['content']
        if content['execution_count'] == 0:
            return  # This is not in response to commands, this is just the kernel saying hello
        if content['status'] != 'ok':
            self.execution_failed.emit(-1)
        else:
            self.ready_to_execute.emit()

    @Slot(dict)
    def _handle_status(self, msg):
        """Handles status message.
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
                self.ready_to_execute.emit()

    @Slot("dict", name="_handle_error")
    def _handle_error(self, msg):
        """Handle error messages."""
        super()._handle_error(msg)
        self.execution_failed.emit(-1)

    def wake_up(self):
        """See base class."""
        if self.kernel_execution_state == 'idle':
            self.ready_to_execute.emit()
            return
        self.start_jupyter_kernel()

    def shutdown_jupyter_kernel(self):
        """Shut down the jupyter kernel."""
        if not self.kernel_client:
            return
        self._toolbox.msg.emit("Shutting down Julia Console...")
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel(now=True)

    def _context_menu_make(self, pos):
        """Reimplemented to add an action for (re)start REPL action."""
        menu = super()._context_menu_make(pos)
        for before_action in menu.actions():
            if before_action.text() == 'Copy (Raw Text)':
                menu.insertAction(before_action, self._copy_input_action)
                break
        first_action = menu.actions()[0]
        if not self.kernel_manager:
            menu.insertAction(first_action, self.start_repl_action)
        else:
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

    def _is_complete(self, source, interactive):
        """See base class."""
        raise NotImplementedError()
