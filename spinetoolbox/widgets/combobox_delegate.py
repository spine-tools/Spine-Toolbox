#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
A delegate to edit table cells with comboboxes.

:author: Manuel Marin <manuelma@kth.se>
:date:   30.3.2018
"""
from PySide2.QtCore import Qt, Slot, QEvent
from PySide2.QtWidgets import QItemDelegate, QComboBox
from PySide2.QtGui import QStandardItemModel, QStandardItem
import logging


class ComboBoxDelegate(QItemDelegate):
    """A QComboBox delegate."""

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomComboEditor. Combo items are obtained from index's Qt.UserRole."""
        combo = CustomComboEditor(parent)
        combo.index = index
        combo.row = index.row()
        combo.column = index.column()
        combo.previous_data = index.data(Qt.EditRole)
        items = index.data(Qt.UserRole)
        combo.addItems(items)
        combo.setCurrentIndex(-1) # force index change
        combo.currentIndexChanged.connect(self.current_index_changed)
        return combo

    def setEditorData(self, editor, index):
        """Show pop up as soon as editing starts."""
        editor.showPopup()

    def setModelData(self, editor, model, index):
        """Do nothing. Model data is updated by handling the `closeEditor` signal."""
        pass

    @Slot(int, name='current_index_changed')
    def current_index_changed(self):
        """Close combo editor, which causes `closeEditor` signal to be emitted."""
        self.sender().close()

class CheckableComboBoxDelegate(ComboBoxDelegate):
    """A QComboBox delegate with checkboxes."""
    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Return CustomComboEditor. Combo items are obtained from index's Qt.UserRole."""
        print('combo check')
        combo = CustomComboEditor(parent)
        combo.index = index
        items = index.data(Qt.UserRole)
        model = QStandardItemModel()
        for item in items:
            q_item = QStandardItem(item)
            q_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            q_item.setData(Qt.Unchecked, Qt.CheckStateRole)
            model.appendRow(q_item)
        combo.setModel(model)
        # combo.setCurrentIndex(-1) # force index change
        # combo.currentIndexChanged.connect(self.current_index_changed)
        return combo

    def setEditorData(self, editor, index):
        """Show pop up as soon as editing starts."""
        pass


class CustomComboEditor(QComboBox):
    """A custom QComboBox to handle data from the model."""
    def __init__(self, parent):
        super().__init__(parent)
        self.index = None
        self.previous_data = None
        self.row = None
        self.column = None
