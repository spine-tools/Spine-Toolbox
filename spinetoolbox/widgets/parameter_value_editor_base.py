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

"""A base for editor windows for editing parameter values."""
from enum import auto, Enum, unique
from numbers import Number
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QMessageBox, QWidget
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
)


@unique
class ValueType(Enum):
    """Enum to identify value types that use different editors."""

    PLAIN_VALUE = auto()
    MAP = auto()
    TIME_SERIES_FIXED_RESOLUTION = auto()
    TIME_SERIES_VARIABLE_RESOLUTION = auto()
    TIME_PATTERN = auto()
    ARRAY = auto()
    DATETIME = auto()
    DURATION = auto()


_SELECTORS = {
    ValueType.PLAIN_VALUE: "Plain value",
    ValueType.MAP: "Map",
    ValueType.TIME_SERIES_FIXED_RESOLUTION: "Time series fixed resolution",
    ValueType.TIME_SERIES_VARIABLE_RESOLUTION: "Time series variable resolution",
    ValueType.TIME_PATTERN: "Time pattern",
    ValueType.ARRAY: "Array",
    ValueType.DATETIME: "Date time",
    ValueType.DURATION: "Duration",
}


class ParameterValueEditorBase(QWidget):
    """
    Dialog for editing parameter values.

    The dialog takes an index and shows a specialized editor corresponding to the value type in a stack widget.
    The user can change the value type by changing the specialized editor using a combo box.
    When the dialog is closed the value from the currently shown specialized editor is
    written back to the given index.
    """

    def __init__(self, index, editor_widgets, parent=None):
        """
        Args:
            index (QModelIndex): an index to a parameter_value in parent_model
            editor_widgets (dict): a mapping from :class:`ValueType` to :class:`QWidget`
            parent (QWidget, optional): a parent widget
        """
        from ..ui.parameter_value_editor import Ui_ParameterValueEditor  # pylint: disable=import-outside-toplevel

        super().__init__(parent, f=Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._index = index
        self._editors = editor_widgets
        self._editor_indexes = {value_type: i for i, value_type in enumerate(editor_widgets)}
        self._ui = Ui_ParameterValueEditor()
        self._ui.setupUi(self)
        self._ui.parameter_type_selector.addItems([_SELECTORS[value_type] for value_type in editor_widgets])
        self._ui.parameter_type_selector.currentIndexChanged.connect(self._change_parameter_type)
        self.addAction(self._ui.accept_action)
        self.addAction(self._ui.reject_action)
        self._ui.accept_action.triggered.connect(self.accept)
        self._ui.reject_action.triggered.connect(self.close)
        self._ui.button_box.accepted.connect(self._ui.accept_action.trigger)
        self._ui.button_box.rejected.connect(self._ui.reject_action.trigger)
        for widget in self._editors.values():
            self._ui.editor_stack.addWidget(widget)

    @Slot()
    def accept(self):
        """Saves the parameter_value shown in the currently selected editor widget to the database manager."""
        editor = self._ui.editor_stack.currentWidget()
        try:
            value = editor.value()
        except ParameterValueFormatError as error:
            QMessageBox.warning(self, "Error", str(error))
            return
        success = self._set_data(value)
        if success:
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
            selector_index == self._editor_indexes[ValueType.TIME_SERIES_VARIABLE_RESOLUTION]
            and old_index == self._editor_indexes[ValueType.TIME_SERIES_FIXED_RESOLUTION]
        ):
            fixed_resolution_value = self._editors[ValueType.TIME_SERIES_FIXED_RESOLUTION].value()
            stamps = fixed_resolution_value.indexes
            values = fixed_resolution_value.values
            variable_resolution_value = TimeSeriesVariableResolution(
                stamps, values, fixed_resolution_value.ignore_year, fixed_resolution_value.repeat
            )
            self._editors[ValueType.TIME_SERIES_VARIABLE_RESOLUTION].set_value(variable_resolution_value)
        elif (
            selector_index == self._editor_indexes[ValueType.TIME_SERIES_FIXED_RESOLUTION]
            and old_index == self._editor_indexes[ValueType.TIME_SERIES_VARIABLE_RESOLUTION]
        ):
            variable_resolution_value = self._editors[ValueType.TIME_SERIES_VARIABLE_RESOLUTION].value()
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
            self._editors[ValueType.TIME_SERIES_FIXED_RESOLUTION].set_value(fixed_resolution_value)
        self._ui.editor_stack.setCurrentIndex(selector_index)
        if selector_index == self._editor_indexes[ValueType.PLAIN_VALUE]:
            self._editors[ValueType.PLAIN_VALUE].set_value("")

    def _select_editor(self, value):
        """Shows the editor widget corresponding to the given value type on the editor stack."""
        if isinstance(value, ParameterValueFormatError):
            self._use_default_editor(message=str(value))
        elif value is None or isinstance(value, (Number, bool, str)):
            self._use_editor(value, ValueType.PLAIN_VALUE)
        elif isinstance(value, Map):
            self._use_editor(value, ValueType.MAP)
        elif isinstance(value, TimeSeriesFixedResolution):
            self._use_editor(value, ValueType.TIME_SERIES_FIXED_RESOLUTION)
        elif isinstance(value, TimeSeriesVariableResolution):
            self._use_editor(value, ValueType.TIME_SERIES_VARIABLE_RESOLUTION)
        elif isinstance(value, TimePattern):
            self._use_editor(value, ValueType.TIME_PATTERN)
        elif isinstance(value, Array):
            self._use_editor(value, ValueType.ARRAY)
        elif isinstance(value, DateTime):
            self._use_editor(value, ValueType.DATETIME)
        elif isinstance(value, Duration):
            self._use_editor(value, ValueType.DURATION)
        else:
            self._use_default_editor()

    def _use_default_editor(self, message=None):
        """Opens the default editor widget. Optionally, displays a warning dialog indicating the problem.

        Args:
            message (str, optional)
        """
        if message is not None:
            QMessageBox.warning(self.parent(), "Warning", message)
        self._ui.parameter_type_selector.setCurrentIndex(self._editor_indexes[ValueType.PLAIN_VALUE])
        self._ui.editor_stack.setCurrentIndex(self._editor_indexes[ValueType.PLAIN_VALUE])

    def _use_editor(self, value, value_type):
        """
        Sets a value to edit on an editor widget.

        Args:
            value (object): value to edit
            value_type (ValueType): type of value
        """
        self._ui.parameter_type_selector.setCurrentIndex(self._editor_indexes[value_type])
        self._ui.editor_stack.setCurrentIndex(self._editor_indexes[value_type])
        self._editors[value_type].set_value(value)

    def _set_data(self, value):
        """
        Writes parameter value back to the model.

        Args:
            value (object): value to write

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        raise NotImplementedError()
