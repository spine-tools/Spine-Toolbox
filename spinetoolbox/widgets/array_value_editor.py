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

"""An editor dialog for Array elements."""
from PySide6.QtCore import Qt
from .duration_editor import DurationEditor
from .datetime_editor import DatetimeEditor
from .parameter_value_editor_base import ParameterValueEditorBase, ValueType
from .plain_parameter_value_editor import PlainParameterValueEditor


class ArrayValueEditor(ParameterValueEditorBase):
    """Editor widget for Array elements."""

    def __init__(self, index, value_type, parent=None):
        """
        Args:
            index (QModelIndex): an index to a parameter_value in parent_model
            parent (QWidget, optional): a parent widget
        """
        editors = dict()
        if value_type == ValueType.PLAIN_VALUE:
            editors[ValueType.PLAIN_VALUE] = PlainParameterValueEditor()
        elif value_type == ValueType.DATETIME:
            editors[ValueType.DATETIME] = DatetimeEditor()
        elif value_type == ValueType.DURATION:
            editors[ValueType.DURATION] = DurationEditor()
        else:
            raise RuntimeError("Unsupported value_type.")

        super().__init__(index, editors, parent)
        self._model = index.model()
        self.setWindowTitle("Edit array element")
        self._select_editor(index.data(Qt.ItemDataRole.EditRole))

    def _set_data(self, value):
        """See base class."""
        return self._model.setData(self._index, value)
