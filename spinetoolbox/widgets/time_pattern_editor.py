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

"""An editor widget for editing a time pattern type (relationship) parameter values."""
from PySide6.QtCore import QPoint, Qt, Slot
from PySide6.QtWidgets import QHeaderView, QWidget
from spinedb_api import TimePattern
from ..helpers import inquire_index_name
from ..mvcmodels.time_pattern_model import TimePatternModel
from .indexed_value_table_context_menu import IndexedValueTableContextMenu


class TimePatternEditor(QWidget):
    """A widget for editing time patterns."""

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget): parent widget
        """
        from ..ui.time_pattern_editor import Ui_TimePatternEditor  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self._model = TimePatternModel(TimePattern(["D1-7"], [0.0]), self)
        self._ui = Ui_TimePatternEditor()
        self._ui.setupUi(self)
        self._ui.pattern_edit_table.init_copy_and_paste_actions()
        self._ui.pattern_edit_table.setModel(self._model)
        self._ui.pattern_edit_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.pattern_edit_table.customContextMenuRequested.connect(self._show_table_context_menu)
        header = self._ui.pattern_edit_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.sectionDoubleClicked.connect(self._open_header_editor)

    @Slot(QPoint)
    def _show_table_context_menu(self, position):
        """
        Opens the table's context menu.

        Args:
            position (QPoint): menu's position on the table
        """
        menu = IndexedValueTableContextMenu(self._ui.pattern_edit_table, position)
        menu.exec(self._ui.pattern_edit_table.mapToGlobal(position))

    def set_value(self, value):
        """Sets the parameter_value to be edited."""
        self._model.reset(value)

    def value(self):
        """Returns the parameter_value currently being edited."""
        return self._model.value

    @Slot(int)
    def _open_header_editor(self, column):
        if column != 0:
            return
        inquire_index_name(self._model, column, "Rename pattern's index", self)
