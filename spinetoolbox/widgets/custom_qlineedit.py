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
from pathlib import Path
import os

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
        self.history = None
        self.history_point = None
        self.history_file_handle = None

    def setup_command_line(self, ui, project):
        self.ui = ui
        self._project = project
        self.julia_subprocess = self._project.get_julia_subprocess()
        self.julia_subprocess.start_if_not_running()
        self.history = list()
        self.history_point = 0
        julia_history_file = os.path.join(Path.home(), ".spine_toolbox_julia_history")
        self.history_file_handle = open(julia_history_file, 'a+')
        with open(julia_history_file, 'r') as f:
            for line in f:
                self.history.append(line.strip())

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
            if self.julia_subprocess.write_on_process(command):
                self.history_point = 0
                # save command only if history is empty or command is different from last one 
                if not self.history or self.text() != self.history[-1]:
                    self.history.append(self.text())
                    self.history_file_handle.write(command)
                    self.history_file_handle.flush()
                self.setText("")
        elif e.key() == Qt.Key_Up:
            try:
                self.history[self.history_point-1]
                self.history_point -= 1
                self.update_text_from_history()
            except IndexError:
                pass
        elif e.key() == Qt.Key_Down:
            self.history_point += 1
            if self.history_point > 0:
                self.history_point = 0
            self.update_text_from_history()
        else:
            super().keyPressEvent(e)


    def update_text_from_history(self):
        if self.history_point:
            self.setText(self.history[self.history_point])
        else:
            self.setText("")
