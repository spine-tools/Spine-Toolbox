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
An editor widget for editing datetime database (relationship) parameter values.

:author: A. Soininen (VTT)
:date:   28.6.2019
"""

from datetime import datetime
import dateutil.parser
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import DateTime
from ui.datetime_editor import Ui_DatetimeEditor


class _DatetimeModel:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = DateTime(dateutil.parser.parse(value))


class DatetimeEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = _DatetimeModel(DateTime(datetime(year=1, month=1,day=1)))
        self._ui = Ui_DatetimeEditor()
        self._ui.setupUi(self)
        self._ui.datetime_edit.editingFinished.connect(self._change_datetime)
        self._ui.datetime_edit.setText(str(self._model.value.value))

    @Slot(name="_change_datetime")
    def _change_datetime(self):
        new_value = self._ui.datetime_edit.text()
        try:
            self._model.value = new_value
        except ValueError:
            self._ui.datetime_edit.setText(str(self._model.value))
            return

    def set_value(self, value):
        self._model = _DatetimeModel(value)
        self._ui.datetime_edit.setText(str(value.value))

    def value(self):
        return self._model.value
