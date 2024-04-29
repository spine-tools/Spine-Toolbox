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

"""An editor widget for editing plain number database (relationship) parameter values."""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget
from spinetoolbox.helpers import try_number_from_string


class PlainParameterValueEditor(QWidget):
    """A widget to edit float or boolean type parameter values."""

    def __init__(self, parent_widget=None):
        """
        Args:
            parent_widget (QWidget): a parent widget
        """
        # pylint: disable=import-outside-toplevel
        from ..ui.plain_parameter_value_editor import Ui_PlainParameterValueEditor

        super().__init__(parent_widget)
        self._ui = Ui_PlainParameterValueEditor()
        self._ui.setupUi(self)
        self._ui.value_edit.setEnabled(False)
        self._ui.radioButton_number_or_string.toggled.connect(self._set_number_or_string_enabled)
        self._ui.radioButton_string.toggled.connect(self._set_string_enabled)

    @Slot(bool)
    def _set_number_or_string_enabled(self, on):
        self._ui.value_edit.setEnabled(on)
        if on:
            self._ui.value_edit.setFocus()

    @Slot(bool)
    def _set_string_enabled(self, on):
        self._ui.string_value_edit.setEnabled(on)
        if on:
            self._ui.string_value_edit.setFocus()

    def set_value(self, value):
        """Sets the value to be edited in this widget."""
        if value is None:
            self._ui.radioButton_null.setChecked(True)
        elif value is True:
            self._ui.radioButton_true.setChecked(True)
        elif value is False:
            self._ui.radioButton_false.setChecked(True)
        elif isinstance(value, str) and value:
            self._ui.string_value_edit.setText(str(value))
            self._ui.radioButton_string.setChecked(True)
        else:
            self._ui.value_edit.setText(str(value))
            self._ui.radioButton_number_or_string.setChecked(True)

    def value(self):
        """Returns the value currently being edited."""
        if self._ui.radioButton_null.isChecked():
            return None
        if self._ui.radioButton_true.isChecked():
            return True
        if self._ui.radioButton_false.isChecked():
            return False
        if self._ui.radioButton_string.isChecked():
            return self._ui.string_value_edit.text()
        return try_number_from_string(self._ui.value_edit.text())
