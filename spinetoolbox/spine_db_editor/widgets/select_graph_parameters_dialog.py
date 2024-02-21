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

"""Classes for custom QDialogs to add items to databases."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QStyledItemDelegate,
)
from spinetoolbox.spine_db_editor.widgets.custom_editors import SearchBarEditor


class SelectGraphParametersDialog(QDialog):
    selection_made = Signal(list)

    def __init__(self, parent, parameters):
        super().__init__(parent)
        self.setWindowTitle("Select graph parameters")
        button_box = QDialogButtonBox(self)
        button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        layout = QVBoxLayout(self)
        self._table_widget = QTableWidget(len(parameters), 1, self)
        self._table_widget.setVerticalHeaderLabels(list(parameters.keys()))
        for k, p in enumerate(parameters.values()):
            self._table_widget.setItem(k, 0, QTableWidgetItem(p))
        self._table_widget.horizontalHeader().hide()
        self._delegate = ParameterNameDelegate(self, parent.db_mngr, *parent.db_maps)
        self._table_widget.setItemDelegate(self._delegate)
        layout.addWidget(self._table_widget)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.resize_columns()

    def resize_columns(self):
        self._table_widget.resizeColumnsToContents()

    def accept(self):
        super().accept()
        self.selection_made.emit([self._table_widget.item(i, 0).text() for i in range(self._table_widget.rowCount())])


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
        editor.update_geometry(option)

    def _close_editor(self, editor, index):
        """Closes editor. Needed by SearchBarEditor."""
        self.closeEditor.emit(editor)
        self.setModelData(editor, index.model(), index)
        self.parent().resize_columns()

    def createEditor(self, parent, option, index):
        """Returns editor."""
        editor = SearchBarEditor(self.parent(), parent)
        editor.set_data(
            index.data(Qt.ItemDataRole.DisplayRole),
            {x["name"] for db_map in self.db_maps for x in self.db_mngr.get_items(db_map, "parameter_definition")},
        )
        editor.data_committed.connect(lambda editor=editor, index=index: self._close_editor(editor, index))
        return editor
