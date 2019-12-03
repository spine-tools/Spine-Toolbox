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

from PySide2.QtWidgets import QTableView, QAbstractItemView
from PySide2.QtCore import Signal
from ..mvcmodels.table_model import TableModel
from .tabular_view_header_widget import TabularViewHeaderWidget


class FrozenTableView(QTableView):

    header_dropped = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = TableModel()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setModel(self.model)
        self.is_updating = False
        self._headers = []
        self.setAcceptDrops(True)

    @property
    def area(self):
        return "frozen"

    def clear(self):
        self.model.set_data([], [])

    def get_selected_row(self):
        if self.model.columnCount() == 0:
            return ()
        if self.model.rowCount() == 0:
            return tuple(None for _ in range(self.model.columnCount()))
        indexes = self.selectedIndexes()
        if not indexes:
            return tuple(None for _ in range(self.model.columnCount()))
        index = indexes[0]
        return self.model.row(index)

    def set_data(self, values, headers):
        self._headers = list(headers)
        data = [self._headers] + values
        self.selectionModel().blockSignals(True)  # prevent selectionChanged signal when updating
        self.model.set_data(data, ["" for _ in headers])
        self.selectRow(0)
        self.selectionModel().blockSignals(False)

    @property
    def headers(self):
        return self._headers

    def dragEnterEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dragMoveEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dropEvent(self, event):
        self.header_dropped.emit(event.source(), self)
