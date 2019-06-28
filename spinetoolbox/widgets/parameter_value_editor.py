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
An editor dialog for editing database (relationship) parameter values.

:author: A. Soininen (VTT)
:date:   28.6.2019
"""

from enum import Enum
from PySide2.QtWidgets import QDialog, QWidget
from spinedb_api import DateTime, Duration, TimePattern, TimeSeriesFixedResolution, TimeSeriesVariableResolution
from ui.parameter_value_editor import Ui_ParameterValueEditor
from widgets.duration_editor import DurationEditor
from widgets.datetime_editor import DatetimeEditor
from widgets.plain_number_editor import PlainNumberEditor
from widgets.time_pattern_editor import TimePatternEditor
from widgets.time_series_fixed_resolution_editor import TimeSeriesFixedResolutionEditor
from widgets.time_series_variable_resolution_editor import TimeSeriesVariableResolutionEditor

class _Editor(Enum):
    NUMBER = 0
    TIME_SERIES_FIXED_RESOLUTION = 1
    TIME_SERIES_VARIABLE_RESOLUTION = 2
    TIME_PATTERN = 3
    DATETIME = 4
    DURATION = 5


class ParameterValueEditor(QDialog):
    def __init__(self, parent_model, parent_index, value, parent=None):
        super().__init__(parent)
        self._ui = Ui_ParameterValueEditor()
        self._ui.setupUi(self)
        self._ui.close_button.clicked.connect(self.close)
        self._time_pattern_editor = TimePatternEditor()
        self._plain_number_editor = PlainNumberEditor()
        self._time_series_fixed_resolution_editor = TimeSeriesFixedResolutionEditor(parent_model, parent_index, value)
        self._time_series_variable_resolution_editor = TimeSeriesVariableResolutionEditor(parent_model, parent_index, value)
        self._datetime_editor = DatetimeEditor()
        self._duration_editor = DurationEditor()
        self._ui.editor_stack.addWidget(self._plain_number_editor)
        self._ui.editor_stack.addWidget(self._time_series_fixed_resolution_editor)
        self._ui.editor_stack.addWidget(self._time_series_variable_resolution_editor)
        self._ui.editor_stack.addWidget(self._time_pattern_editor)
        self._ui.editor_stack.addWidget(self._datetime_editor)
        self._ui.editor_stack.addWidget(self._duration_editor)
        self._ui.parameter_type_selector.activated.connect(self._ui.editor_stack.setCurrentIndex)
        if isinstance(value, (int, float)):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.NUMBER.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.NUMBER.value)
        elif isinstance(value, TimeSeriesFixedResolution):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_SERIES_FIXED_RESOLUTION.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_SERIES_FIXED_RESOLUTION.value)
        elif isinstance(value, TimeSeriesVariableResolution):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_SERIES_VARIABLE_RESOLUTION.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_SERIES_VARIABLE_RESOLUTION.value)
        elif isinstance(value, TimePattern):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_PATTERN.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_PATTERN.value)
        elif isinstance(value, DateTime):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.DATETIME.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.DATETIME.value)
        elif isinstance(value, Duration):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.DURATION.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.DURATION.value)
        else:
            raise RuntimeError('Could not open editor for parameter value: unknown value type')