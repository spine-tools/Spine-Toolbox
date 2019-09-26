######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
A tree model for parameter value lists.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

import json
from PySide2.QtCore import Qt, Slot, QModelIndex, QAbstractItemModel
from PySide2.QtGui import QBrush, QFont, QIcon, QGuiApplication
from mvcmodels.parameter_value_formatting import format_for_DisplayRole


class TreeNode:
    """A helper class to use as the internalPointer of indexes in ParameterValueListModel.

    Attributes
        parent (TreeNode): the parent node
        row (int): the row, needed by ParameterValueListModel.parent()
        text (str, NoneType): the text to show
        level (int, NoneType): the level in the tree
        id (int, NoneType): the id from the db table
    """

    def __init__(self, parent, row, text=None, level=None, identifier=None):
        self.parent = parent
        self.row = row
        self.child_nodes = list()
        self.text = text
        self.level = level
        self.id = identifier


class ParameterValueListModel(QAbstractItemModel):
    """A model to display parameter value list data in a tree view."""

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)
        self._parent = parent
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        gray_color = QGuiApplication.palette().text().color()
        gray_color.setAlpha(128)
        self.gray_brush = QBrush(gray_color)
        self.empty_list = "Type new list name here..."
        self.empty_value = "Type new list value here..."
        self._root_nodes = list()
        self.dataChanged.connect(self._handle_data_changed)

    def build_tree(self):
        """Initialize the internal data structure of TreeNode instances."""
        self.beginResetModel()
        self._root_nodes = list()
        k = 0
        for db_map, db_name in self._parent.db_map_to_name.items():
            db_node = TreeNode(None, k, text="root ({})".format(db_name), identifier=db_map, level=0)
            k += 1
            self._root_nodes.append(db_node)
            i = 0
            for wide_value_list in db_map.wide_parameter_value_list_list():
                list_node = TreeNode(db_node, i, text=wide_value_list.name, identifier=wide_value_list.id, level=1)
                i += 1
                db_node.child_nodes.append(list_node)
                j = 0
                for value in wide_value_list.value_list.split(","):
                    child_node = TreeNode(list_node, j, text=value, level=2)
                    j += 1
                    list_node.child_nodes.append(child_node)
                list_node.child_nodes.append(TreeNode(list_node, j, text=self.empty_value, level=2))
            db_node.child_nodes.append(TreeNode(db_node, i, text=self.empty_list, level=1))
        self.endResetModel()

    def index(self, row, column, parent=QModelIndex()):
        """Returns the index of the item in the model specified by the given row, column and parent index.
        Toplevel indexes get their pointer from the `_root_nodes` attribute;
        whereas inner indexes get their pointer from the `child_nodes` attribute of the parent node.
        """
        if not parent.isValid():
            return self.createIndex(row, column, self._root_nodes[row])
        parent_node = parent.internalPointer()
        return self.createIndex(row, column, parent_node.child_nodes[row])

    def parent(self, index):
        """Returns the parent of the model item with the given index.
        Use the internal pointer to retrieve the parent node and use it
        to create the parent index.
        """
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        if node.parent is None:
            return QModelIndex()
        return self.createIndex(node.parent.row, 0, node.parent)

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows under the given parent.
        Get it from the lenght of the appropriate list.
        """
        if not parent.isValid():
            return len(self._root_nodes)
        node = parent.internalPointer()
        return len(node.child_nodes)

    def columnCount(self, parent=QModelIndex()):
        """Returns the number of columns under the given parent. Always 1.
        """
        return 1

    def data(self, index, role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index.
        Bold toplevel items. Get the DisplayRole from the `text` attribute of the internal pointer.
        """
        if not index.isValid():
            return None
        if role == Qt.FontRole and index.internalPointer().level == 1:
            # Bold list items
            return self.bold_font
        if role == Qt.ForegroundRole and index.parent().isValid() and index.row() == self.rowCount(index.parent()) - 1:
            # Paint gray last item in each inner level
            return self.gray_brush
        if role == Qt.DecorationRole:
            if index.internalPointer().level == 0:
                return QIcon(":/symbols/Spine_symbol.png")
        if role in (Qt.DisplayRole, Qt.EditRole):
            text = index.internalPointer().text
            # Deserialize value (so we don't see e.g. quotes around strings)
            if index.internalPointer().level == 2 and index.row() != self.rowCount(index.parent()) - 1:
                text = format_for_DisplayRole(text)
            return text
        return None

    def flags(self, index):
        """Returns the item flags for the given index.
        """
        if index.internalPointer().level == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role=Qt.EditRole):
        """Sets the role data for the item at index to value.
        Returns True if successful; otherwise returns False.
        Basically just update the `text` attribute of the internal pointer.
        """
        if not index.isValid():
            return False
        if role != Qt.EditRole:
            return False
        node = index.internalPointer()
        if node.level == 2:
            # values are stored as json (list *names*, as normal python types)
            value = json.dumps(value)
        if value == node.text:
            return False
        node.text = value
        self.dataChanged.emit(index, index, [role])
        return True

    def appendRows(self, count, parent=QModelIndex()):
        """Append count rows into the model.
        Items in the new row will be children of the item represented by the parent model index.
        """
        row = self.rowCount(parent)
        self.beginInsertRows(parent, row, row + count - 1)
        parent_node = parent.internalPointer()
        if parent_node.level == 0:
            parent_node.child_nodes.append(TreeNode(parent_node, row, text=self.empty_list, level=1))
        elif parent_node.level == 1:
            parent_node.child_nodes.append(TreeNode(parent_node, row, text=self.empty_value, level=2))
        self.endInsertRows()

    @Slot("QModelIndex", "QModelIndex", "QVector", name="_handle_data_changed")
    def _handle_data_changed(self, top_left, bottom_right, roles=None):
        """Called when data in the model changes.
        """
        if roles is None:
            roles = list()
        if Qt.EditRole not in roles:
            return
        parent = self.parent(top_left)
        if parent != self.parent(bottom_right):
            return
        self.append_empty_rows(bottom_right)
        to_add, to_update = self.items_to_add_and_update(top_left.row(), bottom_right.row(), parent)
        self._parent.add_parameter_value_lists(to_add)
        self._parent.update_parameter_value_lists(to_update)

    def append_empty_rows(self, index):
        """Append emtpy rows if index is the last children, so the user can continue editing the model.
        """
        parent = index.parent()
        if not parent.isValid():
            return
        if self.rowCount(parent) == index.row() + 1:
            self.appendRows(1, parent)
            if index.internalPointer().level == 1:
                self.appendRows(1, index)

    def items_to_add_and_update(self, first, last, parent):
        """Return list of items to add and update in the db.
        """
        to_add = dict()
        to_update = dict()
        if parent.internalPointer().level == 0:
            # The changes correspond to list *names*.
            # We need to check them all
            db_map = parent.internalPointer().id
            for row in range(first, last + 1):
                index = self.index(row, 0, parent)
                node = index.internalPointer()
                if node.id:
                    # Update
                    to_update.setdefault(db_map, []).append(dict(id=node.id, name=node.text))
                else:
                    # Add
                    value_list = [
                        self.index(i, 0, index).internalPointer().text for i in range(self.rowCount(index) - 1)
                    ]
                    if value_list:
                        to_add.setdefault(db_map, []).append(dict(parent=index, name=node.text, value_list=value_list))
        elif parent.internalPointer().level == 1:
            # The changes correspond to list *values*, so it's enough to check the parent
            db_map = parent.parent().internalPointer().id
            value_list = [
                str(self.index(i, 0, parent).internalPointer().text) for i in range(self.rowCount(parent) - 1)
            ]
            id_ = parent.internalPointer().id
            if id_:
                # Update
                to_update.setdefault(db_map, []).append(dict(id=id_, value_list=value_list))
            else:
                # Add
                name = parent.internalPointer().text
                to_add.setdefault(db_map, []).append(dict(parent=parent, name=name, value_list=value_list))
        return to_add, to_update

    def batch_set_data(self, indexes, values):
        """Set edit role for indexes to values in batch."""
        # NOTE: Not in use at the moment
        parented_rows = dict()
        for index, value in zip(indexes, values):
            index.internalPointer().text = value
            parent = self.parent(index)
            parented_rows.setdefault(parent, list()).append(index.row())
        # Emit dataChanged parent-wise
        for parent, rows in parented_rows.items():
            top_left = self.index(min(rows), 0, parent)
            bottom_right = self.index(max(rows), 0, parent)
            self.dataChanged.emit(top_left, bottom_right, [Qt.EditRole])

    def removeRow(self, row, parent=QModelIndex()):
        """Remove row under parent, but never the last row (which is the empty one)"""
        if row == self.rowCount(parent) - 1:
            return
        self.beginRemoveRows(parent, row, row)
        if not parent.isValid():
            # Row is at the top level
            self._root_nodes.pop(row)
            # Update row attribute of tail items. This is awful but we need it.
            for r in range(row, len(self._root_nodes)):
                node = self._root_nodes[r]
                node.row = r
        else:
            # Row is at the low level
            parent_node = parent.internalPointer()
            child_nodes = parent_node.child_nodes
            child_nodes.pop(row)
            # We don't need to update the row attribute of the childs, since they're not used.
        self.endRemoveRows()
