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
Contains the ObjectNameListEditor class.


:author: M. Marin (KTH)
:date:   27.11.2019
"""

from PySide2.QtCore import Qt, Slot, Signal, QEvent, QCoreApplication
from PySide2.QtWidgets import QItemDelegate
from PySide2.QtGui import QStandardItemModel, QStandardItem
from .manage_db_items_dialog import ManageItemsDialog
from .custom_editors import SearchBarEditor


class SearchBarDelegate(QItemDelegate):
    """A custom delegate to use with ObjectNameListEditor.
    """

    data_committed = Signal("QModelIndex", "QVariant")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.data())

    def createEditor(self, parent, option, index):
        editor = SearchBarEditor(parent)
        editor.set_data(index.data(), index.data(Qt.UserRole))
        model = index.model()
        editor.data_committed.connect(lambda e=editor, i=index, m=model: self.close_editor(e, i, m))
        return editor

    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor, option, index)
        size = option.rect.size()
        editor.set_base_size(size)
        editor.update_geometry()

    def close_editor(self, editor, index, model):
        self.closeEditor.emit(editor)
        self.setModelData(editor, model, index)

    def eventFilter(self, editor, event):
        if event.type() == QEvent.FocusOut:
            super().eventFilter(editor, event)
            return QCoreApplication.sendEvent(self.parent(), event)
        return super().eventFilter(editor, event)


class ObjectNameListEditor(ManageItemsDialog):
    """A dialog to select the object name list for a relationship using Google-like search bars."""

    def __init__(self, parent, index, object_class_names, object_names_lists, current_object_names):
        """Initializes widget.

        Args:
            parent (DataStoreForm)
            index (QModelIndex)
            object_class_names (list): string object class names
            object_names_lists (list): lists of string object names
            current_object_names (list)
        """
        super().__init__(parent, None)
        self.setWindowTitle("Select objects")
        self._index = index
        self.model = QStandardItemModel(self)
        self.init_model(object_class_names, object_names_lists, current_object_names)
        self.table_view.setModel(self.model)
        self.resize_window_to_columns()
        self.table_view.verticalHeader().hide()
        delegate = SearchBarDelegate(self)
        self.table_view.setItemDelegate(delegate)
        self.connect_signals()

    def init_model(self, object_class_names, object_names_lists, current_object_names):
        self.model.setHorizontalHeaderLabels(object_class_names)
        item_list = []
        for k, object_names_list in enumerate(object_names_lists):
            try:
                obj_name = current_object_names[k]
            except IndexError:
                obj_name = None
            qitem = QStandardItem(obj_name)
            qitem.setData(object_names_list, role=Qt.UserRole)
            item_list.append(qitem)
        self.model.invisibleRootItem().appendRow(item_list)

    @Slot()
    def accept(self):
        self._index.model().setData(
            self._index, ",".join(self.model.index(0, j).data() for j in range(self.model.columnCount()))
        )
        super().accept()
