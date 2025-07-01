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

"""Contains the ElementNameListEditor class."""
from PySide6.QtCore import QCoreApplication, QEvent, QModelIndex, Qt, Signal, Slot
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QItemDelegate
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from spinetoolbox.spine_db_editor.widgets.custom_editors import SearchBarEditor
from .manage_items_dialogs import ManageItemsDialog

CURRENT_BYNAME_ROLE: int = Qt.ItemDataRole.UserRole + 1
AVAILABLE_BYNAMES_ROLE: int = Qt.ItemDataRole.UserRole + 2


class SearchBarDelegate(QItemDelegate):
    """A custom delegate to use with ElementNameListEditor."""

    data_committed = Signal(QModelIndex, object)

    def setModelData(self, editor, model, index):
        display_byname = editor.data()
        byname = display_byname.split(DB_ITEM_SEPARATOR) if display_byname is not None else None
        model.setData(index, display_byname)
        model.setData(index, byname, CURRENT_BYNAME_ROLE)

    def createEditor(self, parent, option, index):
        editor = SearchBarEditor(parent)
        editor.set_data(index.data(), [DB_ITEM_SEPARATOR.join(names) for names in index.data(AVAILABLE_BYNAMES_ROLE)])
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

    def __init__(self, parent, index, entity_class_names, entity_byname_lists, current_element_byname_list):
        """
        Args:
            parent (SpineDBEditor)
            index (QModelIndex)
            entity_class_names (list): string entity_class names
            entity_byname_lists (list): lists of string entity names
            current_element_byname_list (list)
        """
        super().__init__(parent, None)
        self.setWindowTitle("Select elements")
        self._index = index
        self.model = QStandardItemModel(self)
        self.init_model(entity_class_names, entity_byname_lists, current_element_byname_list)
        self.table_view.setModel(self.model)
        self.table_view.verticalHeader().hide()
        delegate = SearchBarDelegate(self)
        self.table_view.setItemDelegate(delegate)
        self.connect_signals()

    def init_model(self, entity_class_names, entity_byname_lists, current_element_byname_list):
        self.model.setHorizontalHeaderLabels(entity_class_names)
        item_list = []
        for k, entity_byname_list in enumerate(entity_byname_lists):
            try:
                current_byname = current_element_byname_list[k]
            except IndexError:
                current_byname = None
            display_byname = DB_ITEM_SEPARATOR.join(current_byname) if current_byname is not None else None
            qitem = QStandardItem(display_byname)
            qitem.setData(current_byname, role=CURRENT_BYNAME_ROLE)
            qitem.setData(entity_byname_list, role=AVAILABLE_BYNAMES_ROLE)
            item_list.append(qitem)
        self.model.invisibleRootItem().appendRow(item_list)

    @Slot()
    def accept(self):
        entire_byname = ()
        for j in range(self.model.columnCount()):
            byname = self.model.index(0, j).data(CURRENT_BYNAME_ROLE)
            if byname is None:
                entire_byname = None
                break
            entire_byname = entire_byname + tuple(byname)
        self._index.model().setData(self._index, entire_byname)
        super().accept()
