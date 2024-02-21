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

"""An editor widget for editing duration database (relationship) parameter values."""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget
from spinedb_api import Duration, duration_to_relativedelta, ParameterValueFormatError


class DurationEditor(QWidget):
    """
    An editor widget for Duration type parameter values.

    Attributes:
        parent (QWidget): a parent widget
    """

    def __init__(self, parent=None):
        from ..ui.duration_editor import Ui_DurationEditor  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self._value = Duration(duration_to_relativedelta("1 hour"))
        self._ui = Ui_DurationEditor()
        self._ui.setupUi(self)
        self._ui.duration_edit.editingFinished.connect(self._change_duration)
        self._ui.duration_edit.setText(str(self._value))

    @Slot(name="_change_duration")
    def _change_duration(self):
        """Updates the value being edited."""
        text = self._ui.duration_edit.text()
        try:
            self._value = Duration(text)
        except ParameterValueFormatError:
            self._ui.duration_edit.setText(str(self._value))

    def set_value(self, value):
        """Sets the value for editing."""
        self._value = value
        self._ui.duration_edit.setText(str(self._value))

    def value(self):
        """Returns the current Duration."""
        return self._value
