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
An editor dialog for editing database (relationship) parameter values.

:author: A. Soininen (VTT)
:date:   28.6.2019
"""

from enum import IntEnum, unique
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QDialog, QMessageBox
from spinedb_api import (
    DateTime,
    Duration,
    duration_to_relativedelta,
    from_database,
    Map,
    ParameterValueFormatError,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    to_database,
)
from ..widgets.duration_editor import DurationEditor
from ..widgets.datetime_editor import DatetimeEditor
from ..widgets.map_editor import MapEditor
from ..widgets.plain_parameter_value_editor import PlainParameterValueEditor
from ..widgets.time_pattern_editor import TimePatternEditor
from ..widgets.time_series_fixed_resolution_editor import TimeSeriesFixedResolutionEditor
from ..widgets.time_series_variable_resolution_editor import TimeSeriesVariableResolutionEditor


@unique
class _Editor(IntEnum):
    """Indexes for the specialized editors corresponding to the selector combo box and editor stack."""

    PLAIN_VALUE = 0
    MAP = 1
    TIME_SERIES_FIXED_RESOLUTION = 2
    TIME_SERIES_VARIABLE_RESOLUTION = 3
    TIME_PATTERN = 4
    DATETIME = 5
    DURATION = 6


class ParameterValueEditor(QDialog):
    """
    Dialog for editing (relationship) parameter values.

    The dialog takes the editable value from a parent model and shows a specialized editor
    corresponding to the value type in a stack widget. The user can change the value type
    by changing the specialized editor using a combo box.
    When the dialog is closed the value from the currently shown specialized editor is
    written back to the parent model.
    """

    def __init__(self, parent_index, value_name="", value=None, parent_widget=None):
        """
        Args:
            parent_index (QModelIndex): an index to a parameter value in parent_model
            value_name (str): name of the value
            value: parameter value or None if it should be loaded from parent_index
            parent_widget (QWidget): a parent widget
        """
        from ..ui.parameter_value_editor import Ui_ParameterValueEditor

        super().__init__(parent_widget)
        self._parent_model = parent_index.model()
        self._parent_index = parent_index
        self._ui = Ui_ParameterValueEditor()
        self._ui.setupUi(self)
        self.setWindowTitle(f"Edit value    -- {value_name} --")
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)
        self._ui.button_box.accepted.connect(self.accept)
        self._ui.button_box.rejected.connect(self.reject)
        self._time_pattern_editor = TimePatternEditor()
        self._plain_value_editor = PlainParameterValueEditor()
        self._map_editor = MapEditor()
        self._time_series_fixed_resolution_editor = TimeSeriesFixedResolutionEditor()
        self._time_series_variable_resolution_editor = TimeSeriesVariableResolutionEditor()
        self._datetime_editor = DatetimeEditor()
        self._duration_editor = DurationEditor()
        self._ui.editor_stack.addWidget(self._plain_value_editor)
        self._ui.editor_stack.addWidget(self._map_editor)
        self._ui.editor_stack.addWidget(self._time_series_fixed_resolution_editor)
        self._ui.editor_stack.addWidget(self._time_series_variable_resolution_editor)
        self._ui.editor_stack.addWidget(self._time_pattern_editor)
        self._ui.editor_stack.addWidget(self._datetime_editor)
        self._ui.editor_stack.addWidget(self._duration_editor)
        self._ui.parameter_type_selector.activated.connect(self._change_parameter_type)
        if value is None:
            try:
                value = from_database(self._parent_model.data(parent_index, Qt.EditRole))
            except ParameterValueFormatError as error:
                self._select_default_view(message="Failed to load value: {}".format(error))
                return
        self._select_editor(value)

    @Slot()
    def accept(self):
        """Saves the parameter value shown in the currently selected editor widget back to the parent model."""
        editor = self._ui.editor_stack.currentWidget()
        try:
            self._parent_model.setData(self._parent_index, to_database(editor.value()))
        except ParameterValueFormatError as error:
            message = "Cannot set value: {}".format(error)
            QMessageBox.warning(self, "Parameter Value error", message)
            return
        self.close()

    @Slot(int)
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
            selector_index == _Editor.TIME_SERIES_VARIABLE_RESOLUTION
            and old_index == _Editor.TIME_SERIES_FIXED_RESOLUTION
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

    def _select_editor(self, value):
        """Shows the editor widget corresponding to the given value type on the editor stack."""
        if isinstance(value, (int, float, bool)):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.PLAIN_VALUE)
            self._ui.editor_stack.setCurrentIndex(_Editor.PLAIN_VALUE)
            self._plain_value_editor.set_value(value)
        elif isinstance(value, Map):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.MAP)
            self._ui.editor_stack.setCurrentIndex(_Editor.MAP)
            self._map_editor.set_value(value)
        elif isinstance(value, TimeSeriesFixedResolution):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_SERIES_FIXED_RESOLUTION)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_SERIES_FIXED_RESOLUTION)
            self._time_series_fixed_resolution_editor.set_value(value)
        elif isinstance(value, TimeSeriesVariableResolution):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_SERIES_VARIABLE_RESOLUTION)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_SERIES_VARIABLE_RESOLUTION)
            self._time_series_variable_resolution_editor.set_value(value)
        elif isinstance(value, TimePattern):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.TIME_PATTERN)
            self._ui.editor_stack.setCurrentIndex(_Editor.TIME_PATTERN)
            self._time_pattern_editor.set_value(value)
        elif isinstance(value, DateTime):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.DATETIME)
            self._ui.editor_stack.setCurrentIndex(_Editor.DATETIME)
            self._datetime_editor.set_value(value)
        elif isinstance(value, Duration):
            self._ui.parameter_type_selector.setCurrentIndex(_Editor.DURATION)
            self._ui.editor_stack.setCurrentIndex(_Editor.DURATION)
            self._duration_editor.set_value(value)
        else:
            self._select_default_view()

    def _select_default_view(self, message=None):
        """Opens the default editor widget. Optionally, displays a warning dialog indicating the problem.

        Args:
            message (str, optional)
        """
        if message is not None:
            QMessageBox.warning(self.parent(), "Warning", message)
        self._ui.parameter_type_selector.setCurrentIndex(_Editor.PLAIN_VALUE)
        self._ui.editor_stack.setCurrentIndex(_Editor.PLAIN_VALUE)
