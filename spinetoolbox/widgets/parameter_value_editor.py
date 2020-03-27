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
from numbers import Number
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QDialog, QMessageBox
from spinedb_api import (
    Array,
    DateTime,
    Duration,
    duration_to_relativedelta,
    Map,
    ParameterValueFormatError,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    to_database,
)
from .array_editor import ArrayEditor
from .duration_editor import DurationEditor
from .datetime_editor import DatetimeEditor
from .map_editor import MapEditor
from .plain_parameter_value_editor import PlainParameterValueEditor
from .time_pattern_editor import TimePatternEditor
from .time_series_fixed_resolution_editor import TimeSeriesFixedResolutionEditor
from .time_series_variable_resolution_editor import TimeSeriesVariableResolutionEditor
from ..mvcmodels.shared import PARSED_ROLE


@unique
class _Editor(IntEnum):
    """Indexes for the specialized editors corresponding to the selector combo box and editor stack."""

    PLAIN_VALUE = 0
    MAP = 1
    TIME_SERIES_FIXED_RESOLUTION = 2
    TIME_SERIES_VARIABLE_RESOLUTION = 3
    TIME_PATTERN = 4
    ARRAY = 5
    DATETIME = 6
    DURATION = 7


class ParameterValueEditor(QDialog):
    """
    Dialog for editing (relationship) parameter values.

    The dialog takes an index and shows a specialized editor corresponding to the value type in a stack widget.
    The user can change the value type by changing the specialized editor using a combo box.
    When the dialog is closed the value from the currently shown specialized editor is
    written back to the given index.
    """

    def __init__(self, index, parent=None):
        """
        Args:
            index (QModelIndex): an index to a parameter value in parent_model
            parent (QWidget): a parent widget
        """
        from ..ui.parameter_value_editor import Ui_ParameterValueEditor

        super().__init__(parent)
        model = index.model()
        self._index = index
        self._ui = Ui_ParameterValueEditor()
        self._ui.setupUi(self)
        self.set_data_delayed = model.get_set_data_delayed(index)
        self.setWindowTitle(f"Edit value    -- {model.index_name(index)} --")
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)
        self._ui.button_box.accepted.connect(self.accept)
        self._ui.button_box.rejected.connect(self.reject)
        self._time_pattern_editor = TimePatternEditor()
        self._plain_value_editor = PlainParameterValueEditor()
        self._map_editor = MapEditor()
        self._time_series_fixed_resolution_editor = TimeSeriesFixedResolutionEditor()
        self._time_series_variable_resolution_editor = TimeSeriesVariableResolutionEditor()
        self._array_editor = ArrayEditor()
        self._datetime_editor = DatetimeEditor()
        self._duration_editor = DurationEditor()
        self._ui.editor_stack.addWidget(self._plain_value_editor)
        self._ui.editor_stack.addWidget(self._map_editor)
        self._ui.editor_stack.addWidget(self._time_series_fixed_resolution_editor)
        self._ui.editor_stack.addWidget(self._time_series_variable_resolution_editor)
        self._ui.editor_stack.addWidget(self._time_pattern_editor)
        self._ui.editor_stack.addWidget(self._array_editor)
        self._ui.editor_stack.addWidget(self._datetime_editor)
        self._ui.editor_stack.addWidget(self._duration_editor)
        self._ui.parameter_type_selector.currentIndexChanged.connect(self._change_parameter_type)
        self._select_editor(index.data(PARSED_ROLE))

    @Slot()
    def accept(self):
        """Saves the parameter value shown in the currently selected editor widget to the database manager."""
        editor = self._ui.editor_stack.currentWidget()
        try:
            value = to_database(editor.value())
        except ParameterValueFormatError as error:
            message = "Cannot set value: {}".format(error)
            QMessageBox.warning(self, "Parameter Value error", message)
            return
        self.set_data_delayed(value)
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
            resolution = [duration_to_relativedelta(str(difference))]
            fixed_resolution_value = TimeSeriesFixedResolution(
                start,
                resolution,
                variable_resolution_value.values,
                variable_resolution_value.ignore_year,
                variable_resolution_value.repeat,
            )
            self._time_series_fixed_resolution_editor.set_value(fixed_resolution_value)
        self._ui.editor_stack.setCurrentIndex(selector_index)
        if selector_index == _Editor.PLAIN_VALUE:
            self._plain_value_editor.set_value("")

    def _select_editor(self, value):
        """Shows the editor widget corresponding to the given value type on the editor stack."""
        if isinstance(value, ParameterValueFormatError):
            self._use_default_editor(message=str(value))
        elif value is None or isinstance(value, (Number, bool, str)):
            self._use_editor(value, _Editor.PLAIN_VALUE)
        elif isinstance(value, Map):
            self._use_editor(value, _Editor.MAP)
        elif isinstance(value, TimeSeriesFixedResolution):
            self._use_editor(value, _Editor.TIME_SERIES_FIXED_RESOLUTION)
        elif isinstance(value, TimeSeriesVariableResolution):
            self._use_editor(value, _Editor.TIME_SERIES_VARIABLE_RESOLUTION)
        elif isinstance(value, TimePattern):
            self._use_editor(value, _Editor.TIME_PATTERN)
        elif isinstance(value, Array):
            self._use_editor(value, _Editor.ARRAY)
        elif isinstance(value, DateTime):
            self._use_editor(value, _Editor.DATETIME)
        elif isinstance(value, Duration):
            self._use_editor(value, _Editor.DURATION)
        else:
            self._use_default_editor()

    def _use_default_editor(self, message=None):
        """Opens the default editor widget. Optionally, displays a warning dialog indicating the problem.

        Args:
            message (str, optional)
        """
        if message is not None:
            QMessageBox.warning(self.parent(), "Warning", message)
        self._ui.parameter_type_selector.setCurrentIndex(_Editor.PLAIN_VALUE)
        self._ui.editor_stack.setCurrentIndex(_Editor.PLAIN_VALUE)

    def _use_editor(self, value, editor_index):
        self._ui.parameter_type_selector.setCurrentIndex(editor_index)
        self._ui.editor_stack.setCurrentIndex(editor_index)
        self._editor_for_index(editor_index).set_value(value)

    def _editor_for_index(self, editor_index):
        return {
            _Editor.PLAIN_VALUE: self._plain_value_editor,
            _Editor.MAP: self._map_editor,
            _Editor.TIME_SERIES_FIXED_RESOLUTION: self._time_series_fixed_resolution_editor,
            _Editor.TIME_SERIES_VARIABLE_RESOLUTION: self._time_series_variable_resolution_editor,
            _Editor.TIME_PATTERN: self._time_pattern_editor,
            _Editor.ARRAY: self._array_editor,
            _Editor.DATETIME: self._datetime_editor,
            _Editor.DURATION: self._duration_editor,
        }[editor_index]
