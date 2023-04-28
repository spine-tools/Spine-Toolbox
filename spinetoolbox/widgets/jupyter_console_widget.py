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
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from spinetoolbox.widgets.project_item_drag import ProjectItemDragMixin
from spinetoolbox.config import JUPYTER_KERNEL_TIME_TO_DEAD
from spinetoolbox.spine_engine_manager import make_engine_manager
from spinetoolbox.helpers import solve_connection_file
from spine_engine.execution_managers.kernel_execution_manager import KernelExecutionManager
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
        self.owners = {owner}
        self._kernel_starting = False  # Warning: Do not use self._starting (protected class variable in JupyterWidget)
        self.kernel_manager = None
        self.kernel_client = None
        self._engine_connection_file = None
        self._execution_manager = None
        exec_remotely = self._toolbox.qsettings().value("engineSettings/remoteExecutionEnabled", "false") == "true"
        self._engine_manager = make_engine_manager(exec_remotely)
        self._requested_kernel_name = None
        self._q = multiprocessing.Queue()
        self._logger = QueueLogger(self._q, "DetachedPythonConsole", None, dict())
        self.normal_cursor = self._control.viewport().cursor()
        self._copy_input_action = QAction('Copy (Only Input)', self)
        self._copy_input_action.triggered.connect(lambda checked: self.copy_input())
        self._copy_input_action.setEnabled(False)
        self.copy_available.connect(self._copy_input_action.setEnabled)
        self.restart_kernel_action = QAction("Restart", self)
        self.restart_kernel_action.triggered.connect(self.request_restart_kernel)

    def request_start_kernel(self, kernel_name):
        """Requests engine to launch a kernel manager for the given kernel_name.

        Args:
            kernel_name (str): Kernel name

        Returns:
            bool: True if kernel manager was launched successfully, False otherwise
        """
        self._requested_kernel_name = kernel_name  #
        try:
            self._execution_manager = KernelExecutionManager(
                self._logger,
                kernel_name,
                [],
                group_id="DetachedPythonConsoleGroup",
                server_ip="127.0.0.1",
                )
        except RuntimeError:
            pass
        try:
            response = self._q.get(timeout=20)  # Blocks until msg is received, or timeout.
        except Empty:
            self._toolbox.msg_error.emit(f"No response from Engine")
            return False
        msg_type, msg = response  # ([str], [dict])
        if msg_type != "kernel_execution_msg":
            self._toolbox.msg_error.emit(f"Unexpected response received: msg_type:{msg_type} received:{msg}")
            return False
        else:
            return self._handle_kernel_started_msg(msg)

    def _handle_kernel_started_msg(self, msg):
        """Handles the response message from engines KernelExecutionManager.

        Args:
            msg (dict): Message with at least item_name and type keys

        Returns:
            bool: True if engine started the requested kernel manager successfully, False otherwise.
        """
        item = msg["item_name"]  # DetachedPythonConsole
        if msg["type"] == "kernel_started":
            filter_id = msg["filter_id"]
            kernel_name = msg["kernel_name"]
            if self._requested_kernel_name != kernel_name:  # Assert that the launched kernel matches the requested one
                self._toolbox.msg_error.emit(
                    f"Requested {self._requested_kernel_name} but {kernel_name} was launched. Console launch aborted."
                )
                return False
            self._engine_connection_file = solve_connection_file(msg["connection_file"], msg.get("connection_file_dict", dict()))
            return True
        elif msg["type"] == "kernel_spec_not_found":
            msg_text = f"Unable to find kernel spec <b>{msg['kernel_name']}</b> <br/>For Python Tools, " \
                       f"select a kernel spec in the Tool specification editor. <br/>For Julia Tools, " \
                       f"select a kernel spec from File->Settings->Tools."
            self._toolbox.msg_error.emit(f"Could not connect to kernel manager on Engine:<br/>{msg_text}")
        elif msg["type"] == "conda_not_found":
            msg_text = f"{msg['error']}<br/>Conda not found. Please set a path for <b>Conda executable</b> " \
                       f"in <b>File->Settings->Tools</b>."
            self._toolbox.msg_error.emit(f"{msg_text}")
        elif msg["type"] == "execution_failed_to_start":
            msg_text = f"Execution on kernel <b>{msg['kernel_name']}</b> failed to start: {msg['error']}"
            self._toolbox.msg_error.emit(msg_text)
        elif msg["type"] == "kernel_spec_exe_not_found":
            msg_text = f"Invalid kernel spec ({msg['kernel_name']}). File " \
                       f"<b>{msg['kernel_exe_path']}</b> does not exist. " \
                       f"Please try reinstalling the kernel specs."
            self._toolbox.msg_error.emit(msg_text)
        elif msg["type"] == "execution_started":
            print(f"execution_started: {msg}")
            self._toolbox.msg.emit(f"*** Starting execution on kernel spec <b>{msg['kernel_name']}</b> ***")
        else:
            self._toolbox.msg.emit(f"Unhandled message: {msg}")
        return False

    def connect_to_kernel(self, kernel_name, connection_file=None):
        """Connects to an existing kernel manager running on Spine Engine.

        Args:
            kernel_name (str): Kernel name running on Engine
            connection_file (str or None): Path to the connection file of the kernel.
              If None, console is running in detached mode and the connection file is
              already available.
        """
        if connection_file:
            self._engine_connection_file = connection_file
        self._kernel_starting = True
        self.kernel_manager = QtKernelManager(kernel_name=kernel_name, connection_file=self._engine_connection_file)
        self.kernel_manager.load_connection_file()
        self._replace_client()
        # pylint: disable=attribute-defined-outside-init
        self.include_other_output = True
        self.other_output_prefix = ""

    def _replace_client(self):
        """Replaces local kernel client with a new one. Must be
        done when starting or restarting a kernel manager."""
        if self.kernel_manager is None:
            return
        kc = self.kernel_manager.client()
        kc.hb_channel.time_to_dead = JUPYTER_KERNEL_TIME_TO_DEAD  # Not crucial, but nicer to keep the same as mngr
        kc.start_channels()
        if self.kernel_client is not None:
            self.kernel_client.stop_channels()
        self.kernel_client = kc

    def request_restart_kernel(self):
        """Requests the engine to restart the kernel manager."""
        self._engine_manager.restart_kernel(self._engine_connection_file)
        self._replace_client()

    def request_shutdown_kernel_manager(self):
        """Sends a shut down kernel request to engine."""
        self._engine_manager.shutdown_kernel(self._engine_connection_file)

    def name(self):
        """Returns console name for display purposes."""
        return f"{self.kernel_manager.kernel_name} on Jupyter Console - {self.owner_names}"

    @property
    def owner_names(self):
        return " & ".join(x.name for x in self.owners if x is not None)

    def shutdown_local_kernel_manager(self):
        """Shuts down local kernel manager."""
        # TODO: Check if this ever gets past the first line
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
        # TODO: Is this needed?
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
        # TODO: Does this work?
        """Sets busy cursor during console (re)starts."""
        if self._kernel_starting:
            self._control.viewport().setCursor(Qt.BusyCursor)

    def _context_menu_make(self, pos):
        """Reimplemented to add actions to console context-menus."""
        menu = super()._context_menu_make(pos)
        for before_action in menu.actions():
            if before_action.text() == 'Copy (Raw Text)':
                menu.insertAction(before_action, self._copy_input_action)
                break
        first_action = menu.actions()[0]
        self.restart_kernel_action.setEnabled(not self._kernel_starting)
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
