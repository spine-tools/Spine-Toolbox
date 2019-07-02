######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
An editor widget for editing plain number database (relationship) parameter values.

:author: A. Soininen (VTT)
:date:   28.6.2019
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from ui.plain_parameter_value_editor import Ui_PlainParameterValueEditor


class _ValueModel:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        try:
            self._value = float(value)
        except ValueError:
            value = value.strip().lower()
            if value == 'true':
                self._value = True
            elif value == 'false':
                self._value = False
            else:
                raise


class PlainParameterValueEditor(QWidget):
    def __init__(self, parent_widget=None):
        super().__init__(parent_widget)
        self._ui = Ui_PlainParameterValueEditor()
        self._ui.setupUi(self)
        self._ui.value_edit.editingFinished.connect(self._value_changed)
        self._model = _ValueModel(0.0)

    def is_value_valid(self):
        return self._value_valid

    def set_value(self, value):
        if not isinstance(value, (int, float, bool)):
            value = 0.0
        self._model = _ValueModel(value)
        self._ui.value_edit.setText(str(value))

    @Slot(name="_value_changed")
    def _value_changed(self):
        new_value = self._ui.value_edit.text()
        if new_value:
            try:
                self._model.value = new_value
            except ValueError:
                self._ui.value_edit.setText(str(self._model.value))
                return

    def value(self):
        return self._model.value
