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
An editor widget for editing plain number database (relationship) parameter values.

:author: A. Soininen (VTT)
:date:   28.6.2019
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget


class _ValueModel:
    def __init__(self, value):
        """A model to handle the parameter value in the editor.
        Mostly useful because of the handy conversion of strings to floats or booleans.

        Args:
            value (float, bool): a parameter value
        """
        self._value = value

    @property
    def value(self):
        """Returns the value held by the model."""
        return self._value

    @value.setter
    def value(self, value):
        """Converts a value string to float or boolean."""
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
    """
    A widget to edit float or boolean type parameter values.

    Attributes:
        parent_widget (QWidget): a parent widget
    """

    def __init__(self, parent_widget=None):
        from ..ui.plain_parameter_value_editor import Ui_PlainParameterValueEditor

        super().__init__(parent_widget)
        self._ui = Ui_PlainParameterValueEditor()
        self._ui.setupUi(self)
        self._ui.value_edit.editingFinished.connect(self._value_changed)
        self._model = _ValueModel(0.0)
        self._ui.value_edit.setText(str(self._model.value))

    def set_value(self, value):
        """Sets the value to be edited in this widget."""
        if not isinstance(value, (int, float, bool)):
            value = 0.0
        self._model = _ValueModel(value)
        self._ui.value_edit.setText(str(value))

    @Slot(name="_value_changed")
    def _value_changed(self):
        """Updates the model."""
        new_value = self._ui.value_edit.text()
        if new_value:
            try:
                self._model.value = new_value
            except ValueError:
                self._ui.value_edit.setText(str(self._model.value))
                return

    def value(self):
        """Returns the value currently being edited."""
        return self._model.value
