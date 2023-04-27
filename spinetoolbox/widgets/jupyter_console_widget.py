######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Class for a custom RichJupyterWidget that can run Tool instances.
"""

import logging
import os
import sys
import subprocess
import multiprocessing
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from jupyter_client.kernelspec import NoSuchKernel
from spinetoolbox.widgets.project_item_drag import ProjectItemDragMixin
from spinetoolbox.config import JUPYTER_KERNEL_TIME_TO_DEAD
from spinetoolbox.widgets.kernel_editor import find_kernels
from spinetoolbox.spine_engine_manager import make_engine_manager
from spine_engine.execution_managers.kernel_execution_manager import KernelExecutionManager, shutdown_kernel_manager, n_kernel_managers
from spine_engine.utils.queue_logger import QueueLogger

# Set logging level for jupyter loggers
traitlets_logger = logging.getLogger("traitlets")
asyncio_logger = logging.getLogger("asyncio")
traitlets_logger.setLevel(level=logging.WARNING)
asyncio_logger.setLevel(level=logging.WARNING)


class JupyterConsoleWidget(RichJupyterWidget):
    """Base class for all embedded console widgets that can run tool instances."""

    def __init__(self, toolbox, owner=None):
        """
        Args:
            toolbox (ToolboxUI): QMainWindow instance
            owner (ProjectItem, NoneType): Item that owns the console.
        """
        super().__init__(parent=toolbox)
        self._toolbox = toolbox
        # self._target_kernel_name = target_kernel_name
        self.owners = {owner}
        self._kernel_starting = False  # Warning: Do not use self._starting (protected class variable in JupyterWidget)
        self.kernel_name = None
        self.kernel_manager = None
        self.kernel_client = None
        self._engine_connection_file = None  # To restart kernels controlled by Spine Engine
        self._exec_mngr = None
        self._engine_mngr = None
        self._logger = None
        self._q = multiprocessing.Queue()
        self.normal_cursor = self._control.viewport().cursor()
        self._copy_input_action = QAction('Copy (Only Input)', self)
        self._copy_input_action.triggered.connect(lambda checked: self.copy_input())
        self._copy_input_action.setEnabled(False)
        self.copy_available.connect(self._copy_input_action.setEnabled)
        self.start_console_action = QAction("Start", self)
        self.start_console_action.triggered.connect(self.start_console)
        self.restart_console_action = QAction("Restart", self)
        self.restart_console_action.triggered.connect(self.restart_console)

    def start_kernel_manager_in_engine(self, kernel_name):
        # exec_remotely = self.qsettings().value("engineSettings/remoteExecutionEnabled", "false") == "true"
        # self._engine_mngr = make_engine_manager(exec_remotely)
        self._logger = QueueLogger(self._q, "BasePythonConsole", None, dict())
        self._exec_mngr = KernelExecutionManager(
            self._logger,
            kernel_name,
            [],
            group_id="BasePython",
            server_ip="127.0.0.1",
        )
        msg = self._q.get(timeout=20)  # tuple (msg type str, msg dict)
        if msg[0] == "kernel_execution_msg":
            self._handle_kernel_execution_msg(msg[1])
        else:
            print(f"Unhandled msg received:{msg}")

    def _handle_kernel_execution_msg(self, msg):
        item = msg["item_name"]  # BasePythonConsole
        if msg["type"] == "kernel_started":
            filter_id = msg["filter_id"]
            kernel_name = msg["kernel_name"]
            self._engine_connection_file = msg["connection_file"]
            connection_file_dict = msg.get("connection_file_dict", dict())  # For kms running on SpineEngineServer
            self._toolbox.msg.emit(f"Kernel '{kernel_name}' is now running on Engine. Connecting...")
            # Set console window title (Needs editing when multiple consoles are allowed)
            self._toolbox.base_python_consoles[kernel_name].setWindowTitle(f"{kernel_name} on Jupyter Console")
            self.connect_to_kernel(kernel_name, msg["connection_file"])
        elif msg["type"] == "kernel_spec_not_found":
            msg_text = f"Unable to find kernel spec <b>{msg['kernel_name']}</b> <br/>For Python Tools, " \
                       f"select a kernel spec in the Tool specification editor. <br/>For Julia Tools, " \
                       f"select a kernel spec from File->Settings->Tools."
            self._toolbox.msg_error.emit(f"Could not connect to kernel manager on Engine:<br/>{msg_text}")
        elif msg["type"] == "conda_not_found":
            msg_text = f"{msg['error']}<br/>Couldn't call Conda. Set up <b>Conda executable</b> " \
                       f"in <b>File->Settings->Tools</b>."
            self._toolbox.msg_error.emit(f"{msg_text}")
        elif msg["type"] == "execution_failed_to_start":
            msg_text = f"Execution on kernel <b>{msg['kernel_name']}</b> failed to start: {msg['error']}"
            self._toolbox.msg_error.emit(msg_text)
        elif msg["type"] == "kernel_spec_exe_not_found":
            msg_text = f"Invalid kernel spec ({msg['kernel_name']}). File " \
                       f"<b>{msg['kernel_exe_path']}</b> does not exist."
            self._toolbox.msg_error.emit(item, msg["filter_id"], "msg_error", msg_text)
        elif msg["type"] == "execution_started":
            print(f"execution_started: {msg}")
            self._toolbox.msg.emit(f"*** Starting execution on kernel spec <b>{msg['kernel_name']}</b> ***")

    def name(self):
        """Returns console name for display purposes."""
        return f"{self._target_kernel_name} on Jupyter Console - {self.owner_names}"

    @property
    def owner_names(self):
        return " & ".join(x.name for x in self.owners if x is not None)

    @Slot(bool)
    def start_console(self, _=False):
        """Starts chosen Python/Julia kernel if available and not already running.
        Context menu start action handler."""
        if self.kernel_manager and self.kernel_name == self._target_kernel_name:
            self._toolbox.msg_warning.emit(f"Kernel {self._target_kernel_name} already running")
            return
        self.call_start_kernel()

    @Slot(bool)
    def restart_console(self, _=False):
        """Restarts current Python/Julia kernel. Starts a new kernel if it
        is not running or if chosen kernel has been changed in Settings.
        Context menu restart action handler."""
        if self._engine_connection_file:
            self._kernel_starting = True  # This flag is unset when a correct msg is received from iopub_channel
            exec_remotely = self._toolbox.qsettings().value("engineSettings/remoteExecutionEnabled", "false") == "true"
            engine_mngr = make_engine_manager(exec_remotely)
            engine_mngr.restart_kernel(self._engine_connection_file)
            self._replace_client()
            return
        if self.kernel_manager and self.kernel_name == self._target_kernel_name:
            # Restart current kernel
            self._kernel_starting = True  # This flag is unset when a correct msg is received from iopub_channel
            self._toolbox.msg.emit(f"*** Restarting {self._target_kernel_name} ***")
            # Restart kernel manager
            blackhole = open(os.devnull, 'w')
            self.kernel_manager.restart_kernel(now=True, stdout=blackhole, stderr=blackhole)
            # Start kernel client and attach it to kernel manager
            self._replace_client()
        else:
            # No kernel running in Console or kernel has been changed in Settings->Tools. Start kernel
            self.call_start_kernel()

    def call_start_kernel(self):
        """Finds a valid kernel and calls ``start_kernel()`` with it."""
        kernels = find_kernels()
        try:
            kernel_path = kernels[self._target_kernel_name]
        except KeyError:
            self._toolbox.msg_error.emit(
                f"Kernel {self._target_kernel_name} not found. Go to Settings->Tools and select another kernel."
            )
            return
        # Check if this kernel is already running
        if self.kernel_manager and self.kernel_name == self._target_kernel_name:
            return
        self.start_kernel(kernel_path)

    def start_kernel(self, k_path):
        """Starts a kernel manager and kernel client and attaches the client to this Console.

        Args:
            k_path (str): Directory where the the kernel specs are located
        """
        if self.kernel_manager and self.kernel_name != self._target_kernel_name:
            old_k_name_anchor = "<a style='color:#99CCFF;' title='{0}' href='#'>{1}</a>".format(
                k_path, self.kernel_name
            )
            self._toolbox.msg.emit(f"Kernel changed in Settings. Shutting down current kernel {old_k_name_anchor}.")
            self.shutdown_kernel()
        self.kernel_name = self._target_kernel_name
        new_k_name_anchor = "<a style='color:#99CCFF;' title='{0}' href='#'>{1}</a>".format(k_path, self.kernel_name)
        self._toolbox.msg.emit(f"*** Starting {self.name()} (kernel {new_k_name_anchor}) ***")
        self._kernel_starting = True  # This flag is unset when a correct msg is received from iopub_channel
        km = QtKernelManager(kernel_name=self.kernel_name)
        try:
            blackhole = open(os.devnull, 'w')
            cf = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0  # Don't show console when frozen
            km.start_kernel(stdout=blackhole, stderr=blackhole, creationflags=cf)
            kc = km.client()
            kc.hb_channel.time_to_dead = JUPYTER_KERNEL_TIME_TO_DEAD
            kc.start_channels()
            self.kernel_manager = km
            self.kernel_client = kc
            return
        except FileNotFoundError:
            self._toolbox.msg_error.emit(f"Couldn't find the executable specified by kernel {self.kernel_name}")
            self._kernel_starting = False
            return
        except NoSuchKernel:  # kernelspecs missing (probably happens when kernel.json file does not exist
            self._toolbox.msg_error.emit(f"Couldn't find kernel specs for kernel {self.kernel_name}")
            self._kernel_starting = False
            return

    def shutdown_kernel_manager_on_engine(self):
        shutdown_kernel_manager(self._engine_connection_file)
        self._engine_connection_file = ""

    def shutdown_kernel(self):
        """Shut down Julia/Python kernel."""
        if not self.kernel_manager or not self.kernel_manager.is_alive():
            return
        if self.kernel_client is not None:
            self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel(now=True)
        self.kernel_manager.deleteLater()
        self.kernel_manager = None
        self.kernel_client.deleteLater()
        self.kernel_client = None

    def dragEnterEvent(self, e):
        """Don't accept project item drops."""
        source = e.source()
        if isinstance(source, ProjectItemDragMixin):
            e.ignore()
        else:
            super().dragEnterEvent(e)

    @Slot(dict)
    def _handle_status(self, msg):
        """Handles status message."""
        super()._handle_status(msg)
        kernel_execution_state = msg["content"].get("execution_state", "")
        if kernel_execution_state == "starting":
            # This msg does not show up when starting the Console but on Restart it does (strange)
            self._kernel_starting = True
            return
        if kernel_execution_state == "idle" and self._kernel_starting:
            self._kernel_starting = False
            self._control.viewport().setCursor(self.normal_cursor)

    def enterEvent(self, event):
        """Sets busy cursor during console (re)starts."""
        if self._kernel_starting:
            self._control.viewport().setCursor(Qt.BusyCursor)

    def _is_complete(self, source, interactive):
        """See base class."""
        raise NotImplementedError()

    def _context_menu_make(self, pos):
        """Reimplemented to add actions to console context-menus."""
        menu = super()._context_menu_make(pos)
        for before_action in menu.actions():
            if before_action.text() == 'Copy (Raw Text)':
                menu.insertAction(before_action, self._copy_input_action)
                break
        first_action = menu.actions()[0]
        if self.kernel_manager or self._engine_connection_file:
            self.restart_console_action.setEnabled(not self._kernel_starting)
            menu.insertAction(first_action, self.restart_console_action)
        else:
            self.start_console_action.setEnabled(not self._kernel_starting)
            menu.insertAction(first_action, self.start_console_action)
        menu.insertSeparator(first_action)
        return menu

    def copy_input(self):
        """Copies only input."""
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

    def _replace_client(self):
        if self.kernel_manager is None:
            return
        kc = self.kernel_manager.client()
        kc.hb_channel.time_to_dead = JUPYTER_KERNEL_TIME_TO_DEAD  # Not crucial, but nicer to keep the same as mngr
        kc.start_channels()
        if self.kernel_client is not None:
            self.kernel_client.stop_channels()
        self.kernel_client = kc

    def connect_to_kernel(self, kernel_name, connection_file):
        """Connects to an existing kernel. Used when Spine Engine is managing the kernel
        for project execution.

        Args:
            kernel_name (str)
            connection_file (str): Path to the connection file of the kernel
        """
        self.kernel_name = kernel_name
        self._engine_connection_file = connection_file
        self._kernel_starting = True
        self.kernel_manager = QtKernelManager(connection_file=connection_file)
        self.kernel_manager.load_connection_file()
        self._replace_client()
        # pylint: disable=attribute-defined-outside-init
        self.include_other_output = True
        self.other_output_prefix = ""

    def interrupt(self):
        """[TODO: Remove?] Sends interrupt signal to kernel."""
        if not self.kernel_manager:
            return
        self.kernel_manager.interrupt_kernel()
