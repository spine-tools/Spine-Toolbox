######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
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
from PySide2.QtWidgets import QWidget, QStatusBar
from PySide2.QtCore import Slot, Qt
from config import STATUSBAR_SS
import ui.project_form
from helpers import project_dir


class NewProjectForm(QWidget):
    """Class for a new project widget.

    Attributes:
        toolbox (ToolboxUI): Parent widget.
    """

    def __init__(self, toolbox):
        """Initialize class."""
        super().__init__(parent=toolbox, f=Qt.Window)  # Inherits stylesheet from parent
        self._toolbox = toolbox
        # Set up the user interface from Designer.
        self.ui = ui.project_form.Ui_Form()
        self.ui.setupUi(self)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # Class attributes
        self.name = ''  # Project name
        self.description = ''  # Project description
        self.connect_signals()
        self.ui.pushButton_ok.setDefault(True)
        self.ui.lineEdit_project_name.setFocus()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.lineEdit_project_name.textChanged.connect(self.name_changed)
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    @Slot(name='name_changed')
    def name_changed(self):
        """Update label to show a preview of the project directory name."""
        project_name = self.ui.lineEdit_project_name.text()
        default = "Project folder:"
        if project_name == '':
            self.ui.label_folder.setText(default)
        else:
            folder_name = project_name.lower().replace(' ', '_')
            msg = default + " " + folder_name
            self.ui.label_folder.setText(msg)

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Check that project name is valid and create project."""
        self.name = self.ui.lineEdit_project_name.text()
        self.description = self.ui.textEdit_description.toPlainText()
        if self.name == '':
            self.statusbar.showMessage("No project name given", 5000)
            return
        # Check for invalid characters for a folder name
        invalid_chars = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*", "."]
        # "." is actually valid in a folder name but
        # this is to prevent creating folders like "...."
        if any((True for x in self.name if x in invalid_chars)):
            self.statusbar.showMessage("Project name contains invalid character(s) for a folder name", 5000)
            return
        # Check if project with same name already exists
        short_name = self.name.lower().replace(' ', '_')
        project_folder = os.path.join(project_dir(self._toolbox.qsettings()), short_name)
        if os.path.isdir(project_folder):
            self.statusbar.showMessage("Project already exists", 5000)
            return
        # Create new project
        self.call_create_project()
        self.close()

    def call_create_project(self):
        """Call ToolboxUI method create_project()."""
        self._toolbox.create_project(self.name, self.description)

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
