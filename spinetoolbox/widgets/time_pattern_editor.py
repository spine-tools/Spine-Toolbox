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

import numpy as np
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import TimePattern
from ui.time_pattern_editor import Ui_TimePatternEditor
from indexed_value_table_model import IndexedValueTableModel


class TimePatternEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        indexes = np.array(["1-7d"])
        values = np.array([0.0])
        self._ui = Ui_TimePatternEditor()
        self._ui.setupUi(self)
        self._set_model(indexes, values)
        self._ui.length_edit.editingFinished.connect(self._change_length)

    @Slot(int, name="_change_length")
    def _change_length(self):
        length = self._ui.length_edit.value()
        old_length = len(self._model.indexes)
        if length < old_length:
            new_indexes = self._model.indexes[:length]
            new_values = self._model.values[:length]
            self._model.reset(new_indexes, new_values)
        elif length > old_length:
            new_indexes = self._model.indexes + (length - old_length) * [""]
            new_values = np.zeros(length)
            new_values[:old_length] = self._model.values
            self._model.reset(new_indexes, new_values)

    def _set_model(self, indexes, values):
        self._model = IndexedValueTableModel(indexes, values, str, float)
        self._model.set_index_header("Patterns")
        self._model.set_value_header("Values")
        self._ui.pattern_edit_table.setModel(self._model)

    def set_value(self, value):
        self._set_model(value.indexes, value.values)
        self._ui.length_edit.setValue(len(value))

    def value(self):
        indexes = self._model.indexes
        values = self._model.values
        return TimePattern(indexes, values)
