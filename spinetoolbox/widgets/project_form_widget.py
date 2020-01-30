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
Widget shown to user when a new project is created.

:authors: P. Savolainen (VTT)
:date:   10.1.2018
"""

import os
from PySide2.QtWidgets import QWidget, QFileDialog, QMessageBox
from PySide2.QtCore import Slot, Qt, QStandardPaths
from ..config import INVALID_CHARS, APPLICATION_PATH


class NewProjectForm(QWidget):
    """Class for a new project widget."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): Parent widget.
        """
        from ..ui import project_form

        super().__init__(parent=toolbox, f=Qt.Window)  # Inherits stylesheet from parent
        self._toolbox = toolbox
        # Set up the user interface from Designer.
        self.ui = project_form.Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self.dir = ""
        self.name = ""  # Project name
        self.description = ""  # Project description
        self.connect_signals()
        self.ui.pushButton_ok.setDefault(True)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.toolButton_select_project_dir.clicked.connect(self.select_project_dir)
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    @Slot(bool, name="select_project_dir")
    def select_project_dir(self, checked=False):
        """Opens a file browser, where user can select a directory for the new project."""
        # noinspection PyCallByClass, PyArgumentList
        start_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if not start_dir:
            start_dir = APPLICATION_PATH
        answer = QFileDialog.getExistingDirectory(self, "Select a project directory", start_dir)
        if not answer:  # Canceled (american-english), cancelled (british-english)
            return
        # Check that it's a directory
        if not os.path.isdir(answer):
            msg = "Selected thing is not a directory, please try again"
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self, "Invalid selection", msg)
            return
        self.ui.lineEdit_project_dir.setText(answer)
        # Set a suggested name for the project
        _, suggested_name = os.path.split(answer)
        self.ui.lineEdit_project_name.setText(suggested_name)
        self.ui.lineEdit_project_name.selectAll()
        self.ui.lineEdit_project_name.setFocus()

    @Slot(name="ok_clicked")
    def ok_clicked(self):
        """Check that project name is valid and create project."""
        self.dir = self.ui.lineEdit_project_dir.text()
        if self.dir == "":
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.information(self, "Note", "Please select a project directory")
            return
        if os.path.isdir(os.path.join(self.dir, ".spinetoolbox")):
            msg = (
                "Directory \n\n{0}\n\nalready contains a Spine Toolbox project."
                "\nWould you like to overwrite the existing project?".format(self.dir)
            )
            message_box = QMessageBox(
                QMessageBox.Question, "Overwrite?", msg, buttons=QMessageBox.Ok | QMessageBox.Cancel, parent=self
            )
            message_box.button(QMessageBox.Ok).setText("Overwrite")
            answer = message_box.exec_()
            if answer != QMessageBox.Ok:
                return
        self.name = self.ui.lineEdit_project_name.text()
        self.description = self.ui.textEdit_description.toPlainText()
        if self.name == "":
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.information(self, "Note", "Please give the project a name")
            return
        # Check for invalid characters for a folder name
        if any((True for x in self.name if x in INVALID_CHARS)):
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(
                self,
                "Invalid name",
                "Project name contains invalid character(s)."
                "\nCharacters {0} are not allowed.".format(" ".join(INVALID_CHARS)),
            )
            return
        # Create new project
        self.call_create_project()
        self.close()

    def call_create_project(self):
        """Call ToolboxUI method create_project()."""
        self._toolbox.create_project(self.name, self.description, self.dir)

    def keyPressEvent(self, e):
        """Close project form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.ok_clicked()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
