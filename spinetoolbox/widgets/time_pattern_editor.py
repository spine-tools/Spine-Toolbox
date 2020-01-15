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
An editor widget for editing a time pattern type (relationship) parameter values.

:author: A. Soininen (VTT)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget
from spinedb_api import TimePattern
from ..mvcmodels.time_pattern_model import TimePatternModel
from .custom_qtableview import IndexedValueTableView
from .indexed_value_table_context_menu import handle_table_context_menu


class TimePatternEditor(QWidget):
    """
    A widget for editing time patterns.

    Attributes:
        parent (QWidget):
    """

    def __init__(self, parent=None):
        from ..ui.time_pattern_editor import Ui_TimePatternEditor

        super().__init__(parent)
        self._model = TimePatternModel(TimePattern(["1-7d"], [0.0]))
        self._ui = Ui_TimePatternEditor()
        self._ui.setupUi(self)
        self._pattern_edit_table = IndexedValueTableView(self)
        self.layout().addWidget(self._pattern_edit_table)
        self._pattern_edit_table.setModel(self._model)
        self._pattern_edit_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._pattern_edit_table.customContextMenuRequested.connect(self._show_table_context_menu)

    @Slot("QPoint", name="_show_table_context_menu")
    def _show_table_context_menu(self, pos):
        handle_table_context_menu(pos, self._pattern_edit_table, self._model, self)

    def set_value(self, value):
        """Sets the parameter value to be edited."""
        self._model.reset(value)

    def value(self):
        """Returns the parameter value currently being edited."""
        return self._model.value
