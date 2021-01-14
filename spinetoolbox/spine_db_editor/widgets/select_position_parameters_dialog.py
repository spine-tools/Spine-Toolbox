######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for custom QDialogs to add items to databases.

:author: M. Marin (KTH)
:date:   13.5.2018
"""
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QStyledItemDelegate,
)
from ...widgets.custom_editors import SearchBarEditor


class SelectPositionParametersDialog(QDialog):

    selection_made = Signal(str, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Select position parameters")
        button_box = QDialogButtonBox(self)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout = QVBoxLayout(self)
        self._table_widget = QTableWidget(1, 2, self)
        self._table_widget.setHorizontalHeaderLabels(["Position x", "Position y"])
        self._table_widget.setItem(0, 0, QTableWidgetItem(parent._pos_x_parameter))
        self._table_widget.setItem(0, 1, QTableWidgetItem(parent._pos_y_parameter))
        self._table_widget.horizontalHeader().setStretchLastSection(True)
        self._table_widget.verticalHeader().hide()
        self._table_widget.verticalHeader().setDefaultSectionSize(parent.default_row_height)
        self._delegate = ParameterNameDelegate(self, parent.db_mngr, *parent.db_maps)
        self._table_widget.setItemDelegate(self._delegate)
        layout.addWidget(self._table_widget)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def accept(self):
        super().accept()
        self.selection_made.emit(self._parameter_position_x(), self._parameter_position_y())

    def _parameter_position_x(self):
        return self._table_widget.item(0, 0).text()

    def _parameter_position_y(self):
        return self._table_widget.item(0, 1).text()


class ParameterNameDelegate(QStyledItemDelegate):
    """A delegate for the database name."""

    def __init__(self, parent, db_mngr, *db_maps):
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps

    def setModelData(self, editor, model, index):
        """Send signal."""
        model.setData(index, editor.data())

    def setEditorData(self, editor, index):
        """Do nothing. We're setting editor data right away in createEditor."""

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        size = option.rect.size()
        editor.set_base_size(size)
        editor.update_geometry()

    def _close_editor(self, editor, index):
        """Closes editor. Needed by SearchBarEditor."""
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)

    def createEditor(self, parent, option, index):
        """Returns editor."""
        editor = SearchBarEditor(self.parent(), parent)
        editor.set_data(
            index.data(Qt.DisplayRole),
            {
                x["parameter_name"]
                for db_map in self.db_maps
                for x in self.db_mngr.get_items(db_map, "parameter_definition")
            },
        )
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor
