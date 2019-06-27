######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains ImportErrorWidget class.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from PySide2.QtWidgets import QWidget, QListWidget, QVBoxLayout, QDialogButtonBox, QLabel
from PySide2.QtCore import Signal


class ImportErrorWidget(QWidget):
    """Widget to display errors while importing and ask user for action."""

    importWithErrors = Signal()
    goBack = Signal()
    rejected = Signal()

    def __init__(self, parent=None):
        super(ImportErrorWidget, self).__init__(parent)

        # state
        self._error_list = []
        self._num_imported = 0

        # create widgets
        self._ui_num_errors = QLabel()
        self._ui_num_imports = QLabel()
        self._ui_error_list = QListWidget()

        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Abort | QDialogButtonBox.Cancel)
        self._dialog_buttons.button(QDialogButtonBox.Abort).setText("Back")

        # layout
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._ui_num_imports)
        self.layout().addWidget(self._ui_num_errors)
        self.layout().addWidget(self._ui_error_list)
        self.layout().addWidget(self._dialog_buttons)

        # ok button
        self._dialog_buttons.button(QDialogButtonBox.Ok).clicked.connect(self.importWithErrors.emit)
        self._dialog_buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.rejected.emit)
        self._dialog_buttons.button(QDialogButtonBox.Abort).clicked.connect(self.goBack.emit)

    def set_import_state(self, num_imported, errors):
        """Sets state of error widget.
        
        Arguments:
            num_imported {int} -- number of successfull imported items
            errors {list} -- list of errors.
        """
        self._ui_num_errors.setText(f"Number of errors: {len(errors)}")
        self._ui_num_imports.setText(f"Number of imports: {num_imported}")
        self._ui_error_list.clear()
        self._ui_error_list.addItems(errors)
