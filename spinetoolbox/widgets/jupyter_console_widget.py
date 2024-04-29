######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Class for a custom RichJupyterWidget that can run Tool instances."""
import logging
import multiprocessing
from queue import Empty
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QAction, QTextCursor
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
        self.sysimage_path = None
        self.owners = {owner}
        if owner is not None:
            self.sysimage_path = owner._options.get("julia_sysimage", None)
        self.kernel_client = None
        self._connection_file = None
        self._execution_manager = None
        exec_remotely = self._toolbox.qsettings().value("engineSettings/remoteExecutionEnabled", "false") == "true"
        self._engine_manager = make_engine_manager(exec_remotely)
        self._q = multiprocessing.Queue()
        self._logger = QueueLogger(self._q, "DetachedPythonConsole", None, dict())
        self.normal_cursor = self._control.viewport().cursor()
        self._copy_input_action = QAction("Copy (Only Input)", self)
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
        self._execution_manager = KernelExecutionManager(
            self._logger,
            self.kernel_name,
            [],
            group_id="DetachedConsoleGroup",
            server_ip="127.0.0.1",
            environment=environment,
            conda_exe=conda_exe,
            extra_switches=self.sysimage_path,
        )
        try:
            msg_type, msg = self._q.get(timeout=20)  # Blocks until msg (tuple(str, dict)  is received, or timeout.
        except Empty:
            msg_type, msg = "No response from Engine", {}
        if msg_type != "kernel_execution_msg":
            self._toolbox.msg_error.emit(f"Starting console failed: {msg_type} [{msg}]")
            retval = None
        else:
            retval = self._handle_kernel_started_msg(msg)
        if not retval:
            self.release_exec_mngr_resources()
        return retval

    def release_exec_mngr_resources(self):
        """Closes _io.TextIOWrapper files."""
        if self._execution_manager is not None:
            self._execution_manager.std_out.close()
            self._execution_manager.std_err.close()
            self._execution_manager = None

    def _handle_kernel_started_msg(self, msg):
        """Handles the response message from KernelExecutionManager.

        Args:
            msg (dict): Message with item_name, type, etc. keys

        Returns:
            str or None: Path to a connection file if engine started the requested kernel
            manager successfully, None otherwise.
        """
        if msg["type"] == "kernel_started":
            self._connection_file = solve_connection_file(
                msg["connection_file"], msg.get("connection_file_dict", dict())
            )
            return self._connection_file
        elif msg["type"] == "kernel_spec_not_found":
            self._toolbox.msg_error.emit(
                f"Kernel failed to start:<br/>"
                f"Unable to find kernel spec <b>{msg['kernel_name']}</b>.<br/>"
                f"For Python Tools, select a kernel spec in the Tool specification editor.<br/>"
                f"For Julia Tools, select a kernel spec from File->Settings->Tools."
            )
        elif msg["type"] == "conda_kernel_spec_not_found":
            msg_text = (
                f"Unable to make Conda kernel spec <b>{msg['kernel_name']}</b>. Make sure <b>ipykernel</b> "
                f"package and the IPython kernel have been installed successfully."
            )
            self._toolbox.msg_error.emit(f"Kernel failed to start:<br/>{msg_text}")
        elif msg["type"] == "conda_not_found":
            self._toolbox.msg_error.emit(
                "Conda not found. Please set a path for <b>Conda executable</b> in <b>File->Settings->Tools</b>."
            )
        elif msg["type"] == "kernel_spec_exe_not_found":
            self._toolbox.msg_error.emit(
                f"Invalid kernel spec ({msg['kernel_name']}). File <b>{msg['kernel_exe_path']}</b> "
                f"does not exist. Please try reinstalling the kernel specs."
            )
        else:
            self._toolbox.msg.emit(f"Unhandled message: {msg}")
        return None

    def _execute(self, source, hidden):
        """Catches exit or similar commands and closes the console immediately if user so chooses."""
        if (
            source.strip() == "exit"
            or source.strip() == "exit()"
            or source.strip() == "quit"
            or source.strip() == "quit()"
        ):
            message_box = QMessageBox(
                QMessageBox.Icon.Question,
                "Close Console?",
                "Are you sure?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                parent=self,
            )
            message_box.button(QMessageBox.StandardButton.Ok).setText("Close")
            answer = message_box.exec()
            if answer == QMessageBox.StandardButton.Cancel:
                super()._execute("", hidden)
                return
            self.insert_text_to_console("\n\nConsole killed (can be restarted from the right-click menu)")
            self.request_shutdown_kernel_manager()
            self.close()
            return
        super()._execute(source, hidden)

    def insert_text_to_console(self, msg):
        """Inserts given message to console.

        Args:
            msg (str): Text to insert
        """
        cursor = self._control.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._insert_plain_text(cursor, msg, flush=True)

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
            # If the kernel manager is not running, we need to start it again
            if not self.request_start_kernel():
                Notification(self, "Restarting kernel manager failed", corner=Qt.Corner.TopLeftCorner).show()
                self.shutdown_kernel_client()
                return
        self.connect_to_kernel()

    def request_shutdown_kernel_manager(self):
        """Sends a shutdown kernel manager request to engine."""
        # TODO: Shutting down Conda or other kernel managers (e.g. Javascript) does not work!
        self._engine_manager.shutdown_kernel(self._connection_file)
        self.release_exec_mngr_resources()

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
            if before_action.text() == "Copy (Raw Text)":
                menu.insertAction(before_action, self._copy_input_action)
                break
        first_action = menu.actions()[0]
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
        text = "\n".join(useful_lines)
        try:
            was_newline = text[-1] == "\n"
        except IndexError:
            was_newline = False
        if was_newline:  # user doesn't need newline
            text = text[:-1]
        QApplication.clipboard().setText(text)

    def _show_interpreter_prompt(self, number=None):
        if self.kernel_client is not None:
            super()._show_interpreter_prompt(number)

    def closeEvent(self, e):
        """Catches close event to shut down the kernel client
        and sends a signal to Toolbox to request Spine Engine
        to shut down the kernel manager."""
        self.shutdown_kernel_client()
        super().closeEvent(e)
        self.console_closed.emit(self._connection_file)
