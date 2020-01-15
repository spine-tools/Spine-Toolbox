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

    def wake_up(self):
        """Wakes up the console in preparation for execution.

        Subclasses need to emit either ready_to_execute or execution_failed as a consequence of calling
        this function.
        """
        raise NotImplementedError()

    def interrupt(self):
        """Sends interrupt signal to kernel."""
        if not self.kernel_manager:
            return
        self.kernel_manager.interrupt_kernel()
