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
Contains ImporterSpecificationToolbar class.

:authors: M. Marin (KTH)
:date:    25.10.2020
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QToolBar, QLabel, QLineEdit, QHBoxLayout, QWidget


class ImporterSpecificationToolbar(QToolBar):
    """A QToolBar to let users set name and description for an Importer Spec."""

    def __init__(self, parent):
        """

        Args:
            parent (ImportEditorWindow): QMainWindow instance
        """
        super().__init__(parent=parent)
        self._line_edit_name = QLineEdit()
        self._line_edit_description = QLineEdit()
        self._line_edit_name.setPlaceholderText("Enter specification name here...")
        self._line_edit_description.setPlaceholderText("Enter specification description here...")
        self.setAllowedAreas(Qt.TopToolBarArea)
        self.setFloatable(False)
        self.setMovable(False)
        self.addWidget(QLabel("Specification"))
        self.addSeparator()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self._line_edit_name)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self._line_edit_description)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setStretchFactor(self._line_edit_name, 1)
        layout.setStretchFactor(self._line_edit_description, 3)
        self.addWidget(widget)
        self.setObjectName("ImporterSpecificationToolbar")
        spec = parent._specification
        if spec:
            self.set_name(spec.name)
            self.set_description(spec.description)

    def set_name(self, name):
        self._line_edit_name.setText(name)

    def set_description(self, description):
        self._line_edit_description.setText(description)

    def name(self):
        return self._line_edit_name.text()

    def description(self):
        return self._line_edit_description.text()
