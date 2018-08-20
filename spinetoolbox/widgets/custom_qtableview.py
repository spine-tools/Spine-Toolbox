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
Class for a custom QTableView that allows copy-paste, and maybe some other feature we may think of.

:author: Manuel Marin <manuelma@kth.se>
:date:   18.5.2018
"""

import logging
from PySide2.QtWidgets import QTableView, QApplication
from PySide2.QtCore import Qt, Slot, QItemSelection, QItemSelectionModel
from PySide2.QtGui import QKeySequence

class CustomQTableView(QTableView):
    """Custom QTableView class.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent):
        """Initialize the QGraphicsView."""
        super().__init__(parent)
        # self.editing = False
        self.clipboard = QApplication.clipboard()
        self.clipboard_text = self.clipboard.text()
        self.clipboard.dataChanged.connect(self.clipboard_data_changed)

    @Slot(name="clipboard_data_changed")
    def clipboard_data_changed(self):
        self.clipboard_text = self.clipboard.text()

    # TODO: This below was intended to improve navigation while setting edit trigger on current changed.
    # But it's too try-hard. Better edit on double click like excel, which is what most people are used to anyways
    # def moveCursor(self, cursor_action, modifiers):
    #     """Don't move to next index if the self.editing flag is set.
    #     """
    #     if self.editing and cursor_action == self.CursorAction.MoveNext:
    #         self.editing = False
    #         return self.currentIndex()
    #     return super().moveCursor(cursor_action, modifiers)

    # def edit(self, index, trigger, event):
    #     self.editing = True
    #     return super().edit(index, trigger, event)

    def keyPressEvent(self, event):
        """Copy and paste to and from clipboard in Excel-like format."""
        if event.matches(QKeySequence.Copy):
            selection = self.selectionModel().selection()
            if not selection:
                super().keyPressEvent(event)
                return
            first = selection.first()
            content = ""
            v_header = self.verticalHeader()
            h_header = self.horizontalHeader()
            for i in range(first.top(), first.bottom()+1):
                if v_header.isSectionHidden(i):
                    continue
                row = list()
                for j in range(first.left(), first.right()+1):
                    if h_header.isSectionHidden(j):
                        continue
                    row.append(str(self.model().index(i, j).data(Qt.DisplayRole)))
                content += "\t".join(row)
                content += "\n"
            self.clipboard.setText(content)
        elif event.matches(QKeySequence.Paste):
            if not self.clipboard_text:
                super().keyPressEvent(event)
                return
            top_left_index = self.currentIndex()
            if not top_left_index.isValid():
                super().keyPressEvent(event)
                return
            data = [line.split('\t') for line in self.clipboard_text.split('\n')[0:-1]]
            self.selectionModel().select(top_left_index, QItemSelectionModel.Select)
            top = top_left_index.row()
            left = top_left_index.column()
            for i, line in enumerate(data):
                for j, value in enumerate(line):
                    sibling = top_left_index.sibling(top + i, left + j)
                    self.model().setData(sibling, value, Qt.EditRole)
                    self.selectionModel().select(sibling, QItemSelectionModel.Select)
        else:
            super().keyPressEvent(event)

# NOTE: Not in use, we should eliminate it
# class DataPackageKeyTableView(QTableView):
#     """Custom QTableView class.
#
#     Attributes:
#         parent (QWidget): The parent of this view
#     """
#
#     def __init__(self, parent):
#         """Initialize the QGraphicsView."""
#         super().__init__(parent)
#         self.setup_combo_items = None
#
#     def edit(self, index, trigger=QTableView.AllEditTriggers, event=None):
#         """Starts editing the item corresponding to the given index if it is editable.
#         """
#         if not index.isValid():
#             return False
#         column = index.column()
#         header = self.model().headerData(column)
#         if header == 'Select': # this column should be editable with only one click
#             return super().edit(index, trigger, event)
#         if not trigger & self.editTriggers():
#             return False
#         self.setup_combo_items(index)
#         return super().edit(index, trigger, event)
