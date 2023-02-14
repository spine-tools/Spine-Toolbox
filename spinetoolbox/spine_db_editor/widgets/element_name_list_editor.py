######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the ObjectNameListEditor class.

:author: M. Marin (KTH)
:date:   27.11.2019
"""

from PySide6.QtCore import Qt, Slot, Signal, QEvent, QCoreApplication
from PySide6.QtWidgets import QItemDelegate
from PySide6.QtGui import QStandardItemModel, QStandardItem
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from .manage_items_dialogs import ManageItemsDialog
from ...widgets.custom_editors import SearchBarEditor


class SearchBarDelegate(QItemDelegate):
    """A custom delegate to use with ElementNameListEditor."""

    data_committed = Signal("QModelIndex", "QVariant")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.data())

    def createEditor(self, parent, option, index):
        editor = SearchBarEditor(parent)
        editor.set_data(index.data(), index.data(Qt.ItemDataRole.UserRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        editor.update_geometry(option)

    def close_editor(self, editor, index, model):
        self.closeEditor.emit(editor)
        self.setModelData(editor, model, index)

    def eventFilter(self, editor, event):
        if event.type() == QEvent.FocusOut:
            super().eventFilter(editor, event)
            return QCoreApplication.sendEvent(self.parent(), event)
        return super().eventFilter(editor, event)


class ElementNameListEditor(ManageItemsDialog):
    """A dialog to select the element name list for an entity using Google-like search bars."""

    def __init__(self, parent, index, entity_class_names, element_name_lists, current_element_names):
        """Initializes widget.

        Args:
            parent (SpineDBEditor)
            index (QModelIndex)
            entity_class_names (list): string entity_class names
            element_name_lists (list): lists of string element names
            current_element_names (list)
        """
        super().__init__(parent, None)
        self.setWindowTitle("Select elements")
        self._index = index
        self.model = QStandardItemModel(self)
        self.init_model(entity_class_names, element_name_lists, current_element_names)
        self.table_view.setModel(self.model)
        self.resize_window_to_columns()
        self.table_view.verticalHeader().hide()
        delegate = SearchBarDelegate(self)
        self.table_view.setItemDelegate(delegate)
        self.connect_signals()

    def init_model(self, entity_class_names, element_name_lists, current_element_names):
        self.model.setHorizontalHeaderLabels(entity_class_names)
        item_list = []
        for k, element_names_list in enumerate(element_name_lists):
            try:
                el_name = current_element_names[k]
            except IndexError:
                el_name = None
            qitem = QStandardItem(el_name)
            qitem.setData(element_names_list, role=Qt.ItemDataRole.UserRole)
            item_list.append(qitem)
        self.model.invisibleRootItem().appendRow(item_list)

    @Slot()
    def accept(self):
        self._index.model().setData(
            self._index, DB_ITEM_SEPARATOR.join(self.model.index(0, j).data() for j in range(self.model.columnCount()))
        )
        super().accept()
