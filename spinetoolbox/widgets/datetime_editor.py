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

"""An editor widget for editing datetime database (relationship) parameter values."""
from datetime import datetime
from PySide6.QtCore import QDate, QDateTime, QTime, Slot
from PySide6.QtWidgets import QWidget
from spinedb_api import DateTime


def _QDateTime_to_datetime(dt):
    """Converts a QDateTime object to Python's datetime.datetime type."""
    date = dt.date()
    time = dt.time()
    return datetime(
        year=date.year(),
        month=date.month(),
        day=date.day(),
        hour=time.hour(),
        minute=time.minute(),
        second=time.second(),
    )


def _datetime_to_QDateTime(dt):
    """Converts Python's datetime.datetime object to QDateTime."""
    date = QDate(dt.year, dt.month, dt.day)
    time = QTime(dt.hour, dt.minute, dt.second)
    return QDateTime(date, time)


class DatetimeEditor(QWidget):
    """
    An editor widget for DateTime type parameter values.

    Attributes:
        parent (QWidget): a parent widget
    """

    def __init__(self, parent=None):
        from ..ui.datetime_editor import Ui_DatetimeEditor  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self._value = DateTime("2000-01-01")
        self._ui = Ui_DatetimeEditor()
        self._ui.setupUi(self)
        self._ui.datetime_edit.setMinimumDate(QDate(1, 1, 1))
        self._ui.datetime_edit.setDateTime(_datetime_to_QDateTime(self._value.value))
        self._ui.datetime_edit.dateTimeChanged.connect(self._change_datetime)

    @Slot("QDateTime", name="_change_datetime")
    def _change_datetime(self, new_datetime):
        """Updates the internal DateTime value"""
        new_value = DateTime(_QDateTime_to_datetime(new_datetime))
        self._value = new_value

    def set_value(self, value):
        """Sets the value to be edited."""
        self._value = value
        self._ui.datetime_edit.setDateTime(_datetime_to_QDateTime(value.value))

    def value(self):
        """Returns the editor's current value."""
        return self._value
