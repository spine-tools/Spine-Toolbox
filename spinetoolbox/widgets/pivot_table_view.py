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
Custom QTableView classes that support copy-paste and the like.

:author: M. Marin (KTH)
:date:   18.5.2018
"""

from PySide2.QtWidgets import QTableView, QApplication
from PySide2.QtCore import Qt, Slot, QItemSelectionModel
from PySide2.QtGui import QKeySequence
from spinedb_api import from_database, DateTime, Duration, ParameterValueFormatError, TimePattern, TimeSeries
from .parameter_value_editor import ParameterValueEditor
from ..helpers import busy_effect


class PivotTableView(QTableView):
    """Custom QTableView class with pivot capabilities.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent=None):
        """Initialize the class."""
        super().__init__(parent)
        # self.editing = False
        self.clipboard = QApplication.clipboard()
        self.clipboard_text = self.clipboard.text()
        self.clipboard.dataChanged.connect(self.clipboard_data_changed)

    @Slot(name="clipboard_data_changed")
    def clipboard_data_changed(self):
        self.clipboard_text = self.clipboard.text()

    def keyPressEvent(self, event):
        """Copy and paste to and from clipboard in Excel-like format."""
        if event.matches(QKeySequence.Copy):
            selection = self.selectionModel().selection()
            if not selection:
                super().keyPressEvent(event)
                return
            # Take only the first selection in case of multiple selection.
            first = selection.first()
            content = ""
            v_header = self.verticalHeader()
            h_header = self.horizontalHeader()
            for i in range(first.top(), first.bottom() + 1):
                if v_header.isSectionHidden(i):
                    continue
                row = list()
                for j in range(first.left(), first.right() + 1):
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
            self.model().paste_data(top_left_index, data)
        else:
            super().keyPressEvent(event)

    @busy_effect
    def edit(self, index, trigger, event):
        """Starts editing the item at index from pivot_table.
        If the index contains some 'complex' parameter value,
        we open the parameter value editor window instead.
        """
        # pylint: disable=bad-super-call
        if not super().edit(index, trigger, event):
            return False
        if self.model().sourceModel().index_in_data(index):
            try:
                value = from_database(index.data(role=Qt.EditRole))
            except ParameterValueFormatError:
                value = None
            if isinstance(value, (DateTime, Duration, TimePattern, TimeSeries)) or value is None:
                # Close the normal editor and show the `ParameterValueEditor` instead
                self.closePersistentEditor(index)
                editor = ParameterValueEditor(index, value=value, parent_widget=self)
                editor.show()
        return True
