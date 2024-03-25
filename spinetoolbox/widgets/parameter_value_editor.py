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

"""An editor dialog for editing database (relationship) parameter values."""
from PySide6.QtWidgets import QMessageBox
from spinedb_api import ParameterValueFormatError, to_database
from spinedb_api.parameter_value import deep_copy_value
from .array_editor import ArrayEditor
from .duration_editor import DurationEditor
from .datetime_editor import DatetimeEditor
from .map_editor import MapEditor
from .parameter_value_editor_base import ParameterValueEditorBase, ValueType
from .plain_parameter_value_editor import PlainParameterValueEditor
from .time_pattern_editor import TimePatternEditor
from .time_series_fixed_resolution_editor import TimeSeriesFixedResolutionEditor
from .time_series_variable_resolution_editor import TimeSeriesVariableResolutionEditor
from ..mvcmodels.shared import PARSED_ROLE


class ParameterValueEditor(ParameterValueEditorBase):
    """Dialog for editing parameter values in Database editor."""

    def __init__(self, index, parent=None, plain=False):
        """
        Args:
            index (QModelIndex): an index to a parameter_value in parent_model
            parent (QWidget, optional): a parent widget
            plain (bool): if True, allow only plain value editing, otherwise allow all parameter types
        """
        editors = {ValueType.PLAIN_VALUE: PlainParameterValueEditor()}
        if not plain:
            editors.update(
                {
                    ValueType.MAP: MapEditor(),
                    ValueType.TIME_SERIES_FIXED_RESOLUTION: TimeSeriesFixedResolutionEditor(),
                    ValueType.TIME_SERIES_VARIABLE_RESOLUTION: TimeSeriesVariableResolutionEditor(),
                    ValueType.TIME_PATTERN: TimePatternEditor(),
                    ValueType.ARRAY: ArrayEditor(),
                    ValueType.DATETIME: DatetimeEditor(),
                    ValueType.DURATION: DurationEditor(),
                }
            )
        super().__init__(index, editors, parent)
        model = index.model()
        self._index = index
        self.set_data_delayed = model.get_set_data_delayed(index)
        self.setWindowTitle(f"Edit value    -- {model.index_name(index)} --")
        value = deep_copy_value(index.data(PARSED_ROLE))
        self._select_editor(value)

    def _set_data(self, value):
        """See base class."""
        try:
            value_type_tup = to_database(value)
        except ParameterValueFormatError as error:
            message = f"Cannot set value: {error}"
            QMessageBox.warning(self, "Parameter Value error", message)
            return False
        self.set_data_delayed(value_type_tup)
        return True
