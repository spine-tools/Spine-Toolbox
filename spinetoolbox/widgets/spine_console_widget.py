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
Class for a custom RichJupyterWidget that can run Tool instances.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   22.10.2019
"""

import logging
import os
from PySide2.QtCore import Slot, Qt
from PySide2.QtWidgets import QAction, QApplication
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager
from jupyter_client.kernelspec import NoSuchKernel
from spinetoolbox.widgets.project_item_drag import ProjectItemDragMixin
from spinetoolbox.config import JUPYTER_KERNEL_TIME_TO_DEAD
from spinetoolbox.widgets.kernel_editor import find_python_kernels, find_julia_kernels


class SpineConsoleWidget(RichJupyterWidget):
    """Base class for all embedded console widgets that can run tool instances."""

    def __init__(self, toolbox, name, owner=""):
        """
        Args:
            toolbox (ToolboxUI): QMainWindow instance
            name (str): Console name, e.g. 'Python Console'
            owner (str): The name of the project item that 'owns' the console, empty if it's the toolbox 'main' console
        """
        super().__init__(parent=toolbox)
        self._toolbox = toolbox
        self._name = name
        self.owner = owner
        self._kernel_starting = False  # Warning: Do not use self._starting (protected class variable in JupyterWidget)
        self.kernel_name = None
        self.kernel_manager = None
        self.kernel_client = None
        self.normal_cursor = self._control.viewport().cursor()
        self._copy_input_action = QAction('Copy (Only Input)', self)
        self._copy_input_action.triggered.connect(lambda checked: self.copy_input())
        self._copy_input_action.setEnabled(False)
        self.copy_available.connect(self._copy_input_action.setEnabled)
        self.start_console_action = QAction("Start", self)
        self.start_console_action.triggered.connect(self.start_console)
        self.restart_console_action = QAction("Restart", self)
        self.restart_console_action.triggered.connect(self.restart_console)
        # Set logging level for jupyter loggers
        traitlets_logger = logging.getLogger("traitlets")
        asyncio_logger = logging.getLogger("asyncio")
        traitlets_logger.setLevel(level=logging.WARNING)
        asyncio_logger.setLevel(level=logging.WARNING)

    def name(self):
        """Returns console name."""
        return self._name

    @Slot(bool)
    def start_console(self, checked=False):
        """Starts chosen Python/Julia kernel if available and not already running.
        Context menu start action handler."""
        if self._name == "Python Console":
            k_name = self._toolbox.qsettings().value("appSettings/pythonKernel", defaultValue="")
        elif self._name == "Julia Console":
            k_name = self._toolbox.qsettings().value("appSettings/juliaKernel", defaultValue="")
        if k_name == "":
            self._toolbox.msg_error.emit(
                f"No kernel selected. Go to Settings->Tools to select a kernel for {self._name}"
            )
            return
        if self.kernel_manager and self.kernel_name == k_name:
            self._toolbox.msg_warning.emit(f"Kernel {k_name} already running in {self._name}")
            return
        self.call_start_kernel(k_name)

    @Slot(bool)
    def restart_console(self, checked=False):
        """Restarts chosen Python/Julia kernel. Starts a new kernel if it
        is not running or if chosen kernel has been changed in Settings.
        Context menu restart action handler."""
        if self._name == "Python Console":
            k_name = self._toolbox.qsettings().value("appSettings/pythonKernel", defaultValue="")
        else:
            k_name = self._toolbox.qsettings().value("appSettings/juliaKernel", defaultValue="")
        if k_name == "":
            self._toolbox.msg_error.emit(
                f"No kernel selected. Go to Settings->Tools to select a kernel for {self._name}"
            )
            return
        if self.kernel_manager and self.kernel_name == k_name:
            # Restart current kernel
            self._kernel_starting = True  # This flag is unset when a correct msg is received from iopub_channel
            self._toolbox.msg.emit(f"*** Restarting {self._name} ***")
            # self.shutdown_kernel()
            if self.kernel_client:
                self.kernel_client.stop_channels()
            # Restart kernel manager
            blackhole = open(os.devnull, 'w')
            self.kernel_manager.restart_kernel(now=True, stdout=blackhole, stderr=blackhole)
            # Start kernel client and attach it to kernel manager
            kc = self.kernel_manager.client()
            kc.hb_channel.time_to_dead = JUPYTER_KERNEL_TIME_TO_DEAD
            kc.start_channels()
            self.kernel_client = kc
        else:
            # No kernel running in Python Console or Python kernel has been changed in Settings->Tools. Start kernel
            self.call_start_kernel(k_name)

    def call_start_kernel(self, k_name=None):
        """Finds a valid kernel and calls ``start_kernel()`` with it."""
        d = {
            "Python Console": ("Python", "pythonKernel", find_python_kernels),
            "Julia Console": ("Julia", "juliaKernel", find_julia_kernels),
        }
        if self._name not in d:
            self._toolbox.msg_error.emit("Unknown Console")
            return
        language, settings_entry, find_kernels = d[self._name]
        if not k_name:
            k_name = self._toolbox.qsettings().value(f"appSettings/{settings_entry}", defaultValue="")
            if not k_name:
                self._toolbox.msg_error.emit(
                    f"No kernel selected. Go to Settings->Tools to select a {language} kernel."
                )
                return
        kernels = find_kernels()
        try:
            kernel_path = kernels[k_name]
        except KeyError:
            self._toolbox.msg_error.emit(
                f"Kernel {k_name} not found. Go to Settings->Tools and select another {language} kernel."
            )
            return
        # Check if this kernel is already running
        if self.kernel_manager and self.kernel_name == k_name:
            return
        self.start_kernel(k_name, kernel_path)

    def start_kernel(self, k_name, k_path):
        """Starts a kernel manager and kernel client and attaches the client to Julia or Python Console.

        Args:
            k_name (str): Kernel name
            k_path (str): Directory where the the kernel specs are located
        """
        if self.kernel_manager and self.kernel_name != k_name:
            old_k_name_anchor = "<a style='color:#99CCFF;' title='{0}' href='#'>{1}</a>".format(
                k_path, self.kernel_name
            )
            self._toolbox.msg.emit(f"Kernel changed in Settings. Shutting down current kernel {old_k_name_anchor}.")
            self.shutdown_kernel()
        self.kernel_name = k_name
        new_k_name_anchor = "<a style='color:#99CCFF;' title='{0}' href='#'>{1}</a>".format(k_path, self.kernel_name)
        self._toolbox.msg.emit(f"*** Starting {self._name} (kernel {new_k_name_anchor}) ***")
        self._kernel_starting = True  # This flag is unset when a correct msg is received from iopub_channel
        km = QtKernelManager(kernel_name=self.kernel_name)
        try:
            blackhole = open(os.devnull, 'w')
            km.start_kernel(stdout=blackhole, stderr=blackhole)
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

    def shutdown_kernel(self):
        """Shut down Julia/Python kernel."""
        if not self.kernel_manager or not self.kernel_manager.is_alive():
            return
        self._toolbox.msg.emit(f"Shutting down {self._name}...")
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
            # This msg does not show up when starting the Python Console but on Restart it does (strange)
            self._kernel_starting = True
            return
        if kernel_execution_state == "idle" and self._kernel_starting:
            self._kernel_starting = False
            self._toolbox.msg_success.emit(f"{self._name} ready for action")
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
        if not self.kernel_manager:
            menu.insertAction(first_action, self.start_console_action)
        else:
            menu.insertAction(first_action, self.restart_console_action)
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

    def _setup_client(self):
        """Sets up client."""
        if self.kernel_manager is None:
            return
        new_kernel_client = self.kernel_manager.client()
        new_kernel_client.hb_channel.time_to_dead = (
            JUPYTER_KERNEL_TIME_TO_DEAD  # Not crucial, but nicer to keep the same as mngr
        )
        new_kernel_client.start_channels()
        if self.kernel_client is not None:
            self.kernel_client.stop_channels()
        self.kernel_client = new_kernel_client

    def connect_to_kernel(self, kernel_name, connection_file):
        """Connects to an existing kernel. Used when Spine Engine is managing the kernel
        for project execution.

        Args:
            connection_file (str): Path to the connection file of the kernel
        """
        self.kernel_manager = QtKernelManager(connection_file=connection_file)
        self.kernel_manager.load_connection_file()
        self.kernel_name = kernel_name
        self._setup_client()
        self.include_other_output = True
        self.other_output_prefix = ""

    def interrupt(self):
        """[TODO: Remove?] Sends interrupt signal to kernel."""
        if not self.kernel_manager:
            return
        self.kernel_manager.interrupt_kernel()
