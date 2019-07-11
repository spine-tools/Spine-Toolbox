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
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QDialog
from spinedb_api import (
    DateTime,
    Duration,
    duration_to_relativedelta,
    from_database,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    to_database,
)
from ui.parameter_value_editor import Ui_ParameterValueEditor
from widgets.duration_editor import DurationEditor
from widgets.datetime_editor import DatetimeEditor
from widgets.plain_parameter_value_editor import PlainParameterValueEditor
from widgets.time_pattern_editor import TimePatternEditor
from widgets.time_series_fixed_resolution_editor import TimeSeriesFixedResolutionEditor
from widgets.time_series_variable_resolution_editor import TimeSeriesVariableResolutionEditor


class _Editor(Enum):
    """Indexes for the specialized editors corresponding to the selector combo box and editor stack."""

    PLAIN_VALUE = 0
    TIME_SERIES_FIXED_RESOLUTION = 1
    TIME_SERIES_VARIABLE_RESOLUTION = 2
    TIME_PATTERN = 3
    DATETIME = 4
    DURATION = 5


class ParameterValueEditor(QDialog):
    """
    Dialog for editing (relationship) parameter values.

    The dialog takes the editable value from a parent model and shows a specialized editor
    corresponding to the value type in a stack widget. The user can change the value type
    by changing the specialized editor using a combo box.
    When the dialog is closed the value from the currently shown specialized editor is
    written back to the parent model.

    Attributes:
        parent_model (ObjectParameterValueModel, RelationshipParameterValueModel): a parent model
        parent_index (QModelIndex): an index to a parameter value in parent_model
        parent_widget (QWidget): a parent widget
    """

    def __init__(self, parent_model, parent_index, parent_widget=None):
        super().__init__(parent_widget)
        self._parent_model = parent_model
        self._parent_index = parent_index
        self._ui = Ui_ParameterValueEditor()
        self._ui.setupUi(self)
        self._ui.close_button.clicked.connect(self.close)
        self._time_pattern_editor = TimePatternEditor()
        self._plain_value_editor = PlainParameterValueEditor()
        self._time_series_fixed_resolution_editor = TimeSeriesFixedResolutionEditor()
        self._time_series_variable_resolution_editor = TimeSeriesVariableResolutionEditor()
        self._datetime_editor = DatetimeEditor()
        self._duration_editor = DurationEditor()
        self._ui.editor_stack.addWidget(self._plain_value_editor)
        self._ui.editor_stack.addWidget(self._time_series_fixed_resolution_editor)
        self._ui.editor_stack.addWidget(self._time_series_variable_resolution_editor)
        self._ui.editor_stack.addWidget(self._time_pattern_editor)
        self._ui.editor_stack.addWidget(self._datetime_editor)
        self._ui.editor_stack.addWidget(self._duration_editor)
        self._ui.parameter_type_selector.activated.connect(self._change_parameter_type)
        value = from_database(parent_model.data(parent_index, Qt.EditRole))
        if isinstance(value, (int, float, bool)):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.PLAIN_VALUE.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.PLAIN_VALUE.value)
            self._plain_value_editor.set_value(value)
        elif isinstance(value, TimeSeriesFixedResolution):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_SERIES_FIXED_RESOLUTION.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_SERIES_FIXED_RESOLUTION.value)
            self._time_series_fixed_resolution_editor.set_value(value)
        elif isinstance(value, TimeSeriesVariableResolution):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_SERIES_VARIABLE_RESOLUTION.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_SERIES_VARIABLE_RESOLUTION.value)
            self._time_series_variable_resolution_editor.set_value(value)
        elif isinstance(value, TimePattern):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_PATTERN.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_PATTERN.value)
            self._time_pattern_editor.set_value(value)
        elif isinstance(value, DateTime):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.DATETIME.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.DATETIME.value)
            self._datetime_editor.set_value(value)
        elif isinstance(value, Duration):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.DURATION.value)
            self._ui.editor_stack.setCurrentIndex(_Editor.DURATION.value)
            self._duration_editor.set_value(value)
        else:
            raise RuntimeError('Could not open editor for parameter value: unknown value type')

    @Slot(int, name="_change_parameter_type")
    def _change_parameter_type(self, selector_index):
        """
        Handles switching between value types.

        Does a rude conversion between fixed and variable resolution time series.
        In other cases, a default 'empty' value is used.

        Args:
            selector_index (int): an index to the selector combo box
        """
        old_index = self._ui.editor_stack.currentIndex()
        if (
            selector_index == _Editor.TIME_SERIES_VARIABLE_RESOLUTION.value
            and old_index == _Editor.TIME_SERIES_FIXED_RESOLUTION.value
        ):
            fixed_resolution_value = self._time_series_fixed_resolution_editor.value()
            stamps = fixed_resolution_value.indexes
            values = fixed_resolution_value.values
            variable_resolution_value = TimeSeriesVariableResolution(
                stamps, values, fixed_resolution_value.ignore_year, fixed_resolution_value.repeat
            )
            self._time_series_variable_resolution_editor.set_value(variable_resolution_value)
        elif (
            selector_index == _Editor.TIME_SERIES_FIXED_RESOLUTION
            and old_index == _Editor.TIME_SERIES_VARIABLE_RESOLUTION
        ):
            variable_resolution_value = self._time_series_variable_resolution_editor.value()
            stamps = variable_resolution_value.indexes
            start = stamps[0]
            difference = stamps[1] - start
            resolution = [duration_to_relativedelta(difference)]
            fixed_resolution_value = TimeSeriesFixedResolution(
                start,
                resolution,
                variable_resolution_value.values,
                variable_resolution_value.ignore_year,
                variable_resolution_value.repeat,
            )
            self._time_series_fixed_resolution_editor.set_value(fixed_resolution_value)
        self._ui.editor_stack.setCurrentIndex(selector_index)

    def closeEvent(self, event):
        """
        Handles the close event.

        Writes the value from the currently selected specialized editor to the parent model.

        Args:
            event (QCloseEvent): the close event
        """
        editor = self._ui.editor_stack.currentWidget()
        self._parent_model.setData(self._parent_index, to_database(editor.value()))
        event.accept()
