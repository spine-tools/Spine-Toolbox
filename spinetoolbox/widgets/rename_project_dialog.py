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
A widget for editing project name and description
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QDialogButtonBox
from ..project_commands import SetProjectNameAndDescriptionCommand


class RenameProjectDialog(QDialog):
    """Rename project dialog."""

    def __init__(self, toolbox, project):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            project (SpineToolboxProject)
        """
        super().__init__(parent=toolbox, f=Qt.Popup)
        self._project = project
        self._toolbox = toolbox
        layout = QFormLayout(self)
        self._name_le = QLineEdit(self)
        self._name_le.setText(self._project.name)
        self._description_le = QPlainTextEdit(self)
        self._description_le.setPlainText(self._project.description)
        button_box = QDialogButtonBox(self)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout.addRow("Project name", self._name_le)
        layout.addRow("Description", self._description_le)
        layout.addRow(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self._ok_button = button_box.button(QDialogButtonBox.Ok)
        self._ok_button.setEnabled(False)
        self._name_le.textChanged.connect(self._set_ok_enabled)
        self._description_le.textChanged.connect(self._set_ok_enabled)
        self.setAttribute(Qt.WA_DeleteOnClose)

    @property
    def name(self):
        return self._name_le.text().strip()

    @property
    def description(self):
        return self._description_le.toPlainText().strip()

    @Slot()
    def _set_ok_enabled(self):
        self._ok_button.setEnabled(
            bool(self.name) and (self.description != self._project.description or self.name != self._project.name)
        )

    def accept(self):
        super().accept()
        self._project.call_set_name_and_description(self.name, self.description)
