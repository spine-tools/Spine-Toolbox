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
import multiprocessing
from queue import Empty
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.client import QtKernelClient
from spinetoolbox.widgets.project_item_drag import ProjectItemDragMixin
from spinetoolbox.widgets.notification import Notification
from spinetoolbox.config import JUPYTER_KERNEL_TIME_TO_DEAD
from spinetoolbox.spine_engine_manager import make_engine_manager
from spinetoolbox.helpers import solve_connection_file
from spine_engine.execution_managers.kernel_execution_manager import KernelExecutionManager
from spine_engine.utils.queue_logger import QueueLogger
from spine_engine.utils.helpers import resolve_conda_executable

# Set logging level for jupyter loggers
traitlets_logger = logging.getLogger("traitlets")
asyncio_logger = logging.getLogger("asyncio")
traitlets_logger.setLevel(level=logging.WARNING)
asyncio_logger.setLevel(level=logging.WARNING)


class JupyterConsoleWidget(RichJupyterWidget):
    """Base class for all embedded console widgets that can run tool instances."""

    console_closed = Signal(str)

    def __init__(self, toolbox, kernel_name, owner=None):
        """
        Args:
            toolbox (ToolboxUI): QMainWindow instance
            kernel_name (str): Kernel name to start
            owner (ProjectItem, NoneType): Item that owns the console.
        """
        super().__init__()
        self._toolbox = toolbox
        self.kernel_name = kernel_name
        self.owners = {owner}
        self.kernel_client = None
        self._connection_file = None
        self._execution_manager = None
        exec_remotely = self._toolbox.qsettings().value("engineSettings/remoteExecutionEnabled", "false") == "true"
        self._engine_manager = make_engine_manager(exec_remotely)
        self._q = multiprocessing.Queue()
        self._logger = QueueLogger(self._q, "DetachedPythonConsole", None, dict())
        self.normal_cursor = self._control.viewport().cursor()
        self._copy_input_action = QAction('Copy (Only Input)', self)
        self._copy_input_action.triggered.connect(lambda checked: self.copy_input())
        self._copy_input_action.setEnabled(False)
        self.copy_available.connect(self._copy_input_action.setEnabled)
        self.restart_kernel_action = QAction("Restart", self)
        self.restart_kernel_action.triggered.connect(self.request_restart_kernel_manager)

    def request_start_kernel(self, conda=False):
        """Requests Spine Engine to launch a kernel manager for the given kernel_name.

        Args:
            conda (bool): Conda kernel or not

        Returns:
            str or None: Path to connection file if kernel manager was launched successfully, None otherwise
        """
        environment = ""
        if conda:
            environment = "conda"
        conda_exe = self._toolbox.qsettings().value("appSettings/condaPath", defaultValue="")
        conda_exe = resolve_conda_executable(conda_exe)
        try:
            self._execution_manager = KernelExecutionManager(
                self._logger,
                self.kernel_name,
                [],
                group_id="DetachedConsoleGroup",
                server_ip="127.0.0.1",
                environment=environment,
                conda_exe=conda_exe,
            )
        except RuntimeError:
            pass
        try:
            response = self._q.get(timeout=20)  # Blocks until msg is received, or timeout.
        except Empty:
            self._toolbox.msg_error.emit(f"No response from Engine")
            return None
        msg_type, msg = response  # ([str], [dict])
        if msg_type != "kernel_execution_msg":
            self._toolbox.msg_error.emit(f"Unexpected response received: msg_type:{msg_type} received:{msg}")
            return None
        else:
            return self._handle_kernel_started_msg(msg)

    def _handle_kernel_started_msg(self, msg):
        """Handles the response message from KernelExecutionManager.

        Args:
            msg (dict): Message with item_name, type, etc. keys

        Returns:
            str or None: Path to a connection file if engine started the requested kernel manager successfully, None otherwise.
        """
        item = msg["item_name"]  # DetachedPythonConsole
        if msg["type"] == "kernel_started":
            self._connection_file = solve_connection_file(
                msg["connection_file"], msg.get("connection_file_dict", dict())
            )
            return self._connection_file
        elif msg["type"] == "kernel_spec_not_found":
            msg_text = (
                f"Unable to find kernel spec <b>{msg['kernel_name']}</b> <br/>For Python Tools, "
                f"select a kernel spec in the Tool specification editor. <br/>For Julia Tools, "
                f"select a kernel spec from File->Settings->Tools."
            )
            self._toolbox.msg_error.emit(f"Could not connect to kernel manager on Engine:<br/>{msg_text}")
        elif msg["type"] == "conda_not_found":
            msg_text = (
                f"{msg['error']}<br/>Conda not found. Please set a path for <b>Conda executable</b> "
                f"in <b>File->Settings->Tools</b>."
            )
            self._toolbox.msg_error.emit(f"{msg_text}")
        elif msg["type"] == "execution_failed_to_start":
            msg_text = f"Execution on kernel <b>{msg['kernel_name']}</b> failed to start: {msg['error']}"
            self._toolbox.msg_error.emit(msg_text)
        elif msg["type"] == "kernel_spec_exe_not_found":
            msg_text = (
                f"Invalid kernel spec ({msg['kernel_name']}). File "
                f"<b>{msg['kernel_exe_path']}</b> does not exist. "
                f"Please try reinstalling the kernel specs."
            )
            self._toolbox.msg_error.emit(msg_text)
        elif msg["type"] == "execution_started":
            self._toolbox.msg.emit(f"*** Starting execution on kernel spec <b>{msg['kernel_name']}</b> ***")
        else:
            self._toolbox.msg.emit(f"Unhandled message: {msg}")
        return None

    def set_connection_file(self, connection_file):
        """Sets connection file obtained from engine to this console.

        Args:
            connection_file (str): Path to a connection file obtained from a running kernel manager.
        """
        self._connection_file = connection_file

    def connect_to_kernel(self):
        """Connects a local kernel client to a kernel manager running on Spine Engine."""
        kc = QtKernelClient(connection_file=self._connection_file)
        kc.load_connection_file()
        kc.hb_channel.time_to_dead = JUPYTER_KERNEL_TIME_TO_DEAD  # Not crucial, but nicer to keep the same as mngr
        kc.start_channels()
        self.kernel_client = kc  # property in BaseFrontEndMixin(). Handles closing previous client connections.
        # pylint: disable=attribute-defined-outside-init
        self.include_other_output = True
        self.other_output_prefix = ""

    def request_restart_kernel_manager(self):
        """Restarts kernel manager on engine and connects a new kernel client to it."""
        if not self._engine_manager.restart_kernel(self._connection_file):
            Notification(self, "Restarting kernel manager failed", corner=Qt.Corner.TopLeftCorner).show()
            self.shutdown_kernel_client()
            return
        self.connect_to_kernel()

    def request_shutdown_kernel_manager(self):
        """Sends a shutdown kernel manager request to engine."""
        # TODO: Shutting down Conda kernel managers does not work!
        self._engine_manager.shutdown_kernel(self._connection_file)

    def name(self):
        """Returns console name for display purposes."""
        return f"{self.kernel_name} on Jupyter Console - {self.owner_names}"

    @property
    def owner_names(self):
        return " & ".join(x.name for x in self.owners if x is not None)

    def shutdown_kernel_client(self):
        """Shuts down local kernel client."""
        if self.kernel_client is not None:
            self.kernel_client.stop_channels()
            self.kernel_client.deleteLater()
            self.kernel_client = None

    def dragEnterEvent(self, e):
        """Rejects dropped project items."""
        source = e.source()
        if isinstance(source, ProjectItemDragMixin):
            e.ignore()
        else:
            super().dragEnterEvent(e)

    def _context_menu_make(self, pos):
        """Reimplemented to add actions to console context-menus."""
        menu = super()._context_menu_make(pos)
        for before_action in menu.actions():
            if before_action.text() == 'Copy (Raw Text)':
                menu.insertAction(before_action, self._copy_input_action)
                break
        first_action = menu.actions()[0]
        self.restart_kernel_action.setEnabled(self.kernel_client.is_alive())
        menu.insertAction(first_action, self.restart_kernel_action)
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

    def closeEvent(self, e):
        """Catches close event to shut down the kernel client
        and sends a signal to Toolbox to request Spine Engine
        to shut down the kernel manager."""
        self.shutdown_kernel_client()
        super().closeEvent(e)
        self.console_closed.emit(self._connection_file)
