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

"""An editor dialog for map indexes and values."""
from PySide6.QtCore import Qt
from .array_editor import ArrayEditor
from .duration_editor import DurationEditor
from .datetime_editor import DatetimeEditor
from .parameter_value_editor_base import ParameterValueEditorBase, ValueType
from .plain_parameter_value_editor import PlainParameterValueEditor
from .time_pattern_editor import TimePatternEditor
from .time_series_fixed_resolution_editor import TimeSeriesFixedResolutionEditor
from .time_series_variable_resolution_editor import TimeSeriesVariableResolutionEditor


class MapValueEditor(ParameterValueEditorBase):
    """Dialog for editing parameter values in Map value editor."""

    def __init__(self, index, parent=None):
        """
        Args:
            index (QModelIndex): an index to a parameter_value in parent_model
            parent (QWidget, optional): a parent widget
        """
        editors = {
            ValueType.PLAIN_VALUE: PlainParameterValueEditor(),
            ValueType.TIME_SERIES_FIXED_RESOLUTION: TimeSeriesFixedResolutionEditor(),
            ValueType.TIME_SERIES_VARIABLE_RESOLUTION: TimeSeriesVariableResolutionEditor(),
            ValueType.TIME_PATTERN: TimePatternEditor(),
            ValueType.ARRAY: ArrayEditor(),
            ValueType.DATETIME: DatetimeEditor(),
            ValueType.DURATION: DurationEditor(),
        }

        super().__init__(index, editors, parent)
        self._model = index.model()
        self.setWindowTitle("Edit map value")
        self._select_editor(index.data(Qt.ItemDataRole.EditRole))

    def _set_data(self, value):
        """See base class."""
        return self._model.setData(self._index, value)
