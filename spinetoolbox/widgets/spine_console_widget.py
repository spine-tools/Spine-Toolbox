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
Class for a custom RichJupyterWidget that can run tool instances.

:authors: M. Marin (KTH)
:date:   22.10.2019
"""

from PySide2.QtCore import Signal
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.manager import QtKernelManager, QtKernelRestarter
from ..config import JUPYTER_KERNEL_TIME_TO_DEAD, JUPYTER_KERNEL_RESTART_LIMIT


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
        ind = next((k for k, x in enumerate(self._kernel_spec.argv) if x.startswith("--project")), None)
        if not ind:
            return
        if self.project_path is None:
            return
        self._kernel_spec.argv[ind] = f"--project={self.project_path}"

    def start_restarter(self):
        """Starts a restarter with custom time to dead and restart limit."""
        if self.autorestart and self.has_kernel:
            if self._restarter is None:
                self._restarter = QtKernelRestarter(
                    time_to_dead=JUPYTER_KERNEL_TIME_TO_DEAD,
                    restart_limit=JUPYTER_KERNEL_RESTART_LIMIT,
                    kernel_manager=self,
                    parent=self,
                    log=self.log,
                )
                self._restarter.add_callback(self._handle_kernel_restarted, event='restart')
                self._restarter.add_callback(self._handle_kernel_left_dead, event='dead')
            self._restarter.start()

    def _handle_kernel_left_dead(self):
        self.kernel_left_dead.emit()


class SpineConsoleWidget(RichJupyterWidget):
    """Base class for all console widgets that can run tool instances."""

    ready_to_execute = Signal()
    execution_failed = Signal(int)
    name = "Unnamed console"

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): QMainWindow instance
        """
        super().__init__(parent=toolbox)
        self._toolbox = toolbox
        self.kernel_name = None
        self.kernel_manager = None
        self.kernel_client = None

    def wake_up(self):
        """Wakes up the console in preparation for execution.

        Subclasses need to emit either ready_to_execute or execution_failed as a consequence of calling
        this function.
        """
        raise NotImplementedError()

    def setup_client(self):
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
        """
        Connects to an existing kernel.

        Args:
            connection_file (str): Path to the connection file of the kernel
        """
        self.kernel_manager = CustomQtKernelManager(connection_file=connection_file)
        self.kernel_manager.load_connection_file()
        self.kernel_name = kernel_name
        self.setup_client()
        self.include_other_output = True  # FIXME: We may want to set it back to False somewhere else?
        self.other_output_prefix = ""

    def interrupt(self):
        """Sends interrupt signal to kernel."""
        if not self.kernel_manager:
            return
        self.kernel_manager.interrupt_kernel()
