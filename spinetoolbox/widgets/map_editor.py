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

"""An editor widget for editing a map type parameter values."""
from PySide6.QtCore import QModelIndex, QPoint, Qt, Slot
from PySide6.QtWidgets import QWidget
from spinedb_api import Map
from ..helpers import inquire_index_name
from .map_value_editor import MapValueEditor
from .indexed_value_table_context_menu import MapTableContextMenu
from ..mvcmodels.map_model import MapModel
from ..spine_db_editor.widgets.custom_delegates import ParameterValueElementDelegate


class MapEditor(QWidget):
    """
    A widget for editing maps.

    Attributes:
        parent (QWidget):
    """

    def __init__(self, parent=None):
        from ..ui.map_editor import Ui_MapEditor  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self._model = MapModel(Map(["key"], [0.0]), self)
        self._ui = Ui_MapEditor()
        self._ui.setupUi(self)
        self._ui.map_table_view.init_copy_and_paste_actions()
        self._ui.map_table_view.setModel(self._model)
        self._ui.map_table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.map_table_view.customContextMenuRequested.connect(self._show_table_context_menu)
        self._ui.map_table_view.horizontalHeader().sectionDoubleClicked.connect(self._open_header_editor)
        delegate = ParameterValueElementDelegate(self._ui.map_table_view)
        delegate.value_editor_requested.connect(self.open_value_editor)
        self._ui.map_table_view.setItemDelegate(delegate)
        self._ui.convert_leaves_button.clicked.connect(self._convert_leaves)

    @Slot(bool)
    def _convert_leaves(self, _):
        self._model.convert_leaf_maps()

    @Slot(QPoint)
    def _show_table_context_menu(self, position):
        """
        Opens table context menu.

        Args:
            position (QPoint): menu's position
        """
        menu = MapTableContextMenu(self, self._ui.map_table_view, position)
        menu.exec(self._ui.map_table_view.mapToGlobal(position))

    def set_value(self, value):
        """Sets the parameter_value to be edited."""
        self._model.reset(value)
        self._ui.map_table_view.resizeColumnsToContents()

    def value(self):
        """Returns the parameter_value currently being edited."""
        return self._model.value()

    @Slot(QModelIndex)
    def open_value_editor(self, index):
        """
        Opens value editor dialog for given map model index.

        Args:
            index (QModelIndex): index
        """
        editor = MapValueEditor(index, self)
        editor.show()

    @Slot(int)
    def _open_header_editor(self, column):
        if column >= self._model.columnCount() - 2:
            return
        inquire_index_name(self._model, column, "Rename map's index", self)
