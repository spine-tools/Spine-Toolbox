#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Class for a custom QLineEdit for the lineEdit_process_command.

:author: Manuel Marin <manuelma@kth.se>
:date:   20.5.2018
"""

import logging
from PySide2.QtWidgets import QLineEdit
from PySide2.QtCore import Signal, Slot, Qt


class CustomQLineEdit(QLineEdit):
    """Custom QLineEdit class.

    Attributes:
        parent (QWidget): The parent of this widget
    """


    def __init__(self, parent):
        """Initialize the QLineEdit."""
        super().__init__(parent)
        self.julia_subprocess = None
        self.ui = None
        self._project = None

    def setup_command_line(self, ui, project):
        self.ui = ui
        self._project = project
        self.julia_subprocess = self._project.get_julia_subprocess()

    def keyPressEvent(self, e):
        """Hide this widget when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.hide()
        elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.julia_subprocess.start_if_not_running()
            julia_prompt = "<span style='color:green;white-space: pre;'><b>julia> </b></span>"
            self.ui.add_process_message(julia_prompt + self.text())
            command = self.text() + "\n"
            ret = self.julia_subprocess.write_on_process(command)
            if ret:
                self.setText("")
        else:
            super().keyPressEvent(e)
