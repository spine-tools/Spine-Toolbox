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

"""A widget for editing project description."""
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QPlainTextEdit, QDialogButtonBox


class SetDescriptionDialog(QDialog):
    """Dialog for setting a description for a project."""

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
        self._name_label = QLabel(self)
        self._name_label.setText(self._project.name)
        self._description_te = QPlainTextEdit(self)
        self._description_te.setPlainText(self._project.description)
        button_box = QDialogButtonBox(self)
        button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        layout.addRow("Project name", self._name_label)
        layout.addRow("Description", self._description_te)
        layout.addRow(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self._ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setEnabled(False)
        self._description_te.textChanged.connect(self._set_ok_enabled)
        self.setAttribute(Qt.WA_DeleteOnClose)

    @property
    def description(self):
        return self._description_te.toPlainText().strip()

    @Slot()
    def _set_ok_enabled(self):
        self._ok_button.setEnabled(self.description != self._project.description)

    def accept(self):
        super().accept()
        self._project.call_set_description(self.description)
