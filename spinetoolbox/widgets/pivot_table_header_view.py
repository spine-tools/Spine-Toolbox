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
Contains custom QHeaderView for the pivot table.

:author: M. Marin (KTH)
:date:   2.12.2019
"""

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QHeaderView
from .tabular_view_header_widget import TabularViewHeaderWidget


class PivotTableHeaderView(QHeaderView):

    header_dropped = Signal(object, object)

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent=parent)
        self.setAcceptDrops(True)
        if orientation == Qt.Horizontal:
            self._area = "columns"
        elif orientation == Qt.Vertical:
            self._area = "rows"

    @property
    def area(self):
        return self._area

    def dragEnterEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dragMoveEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dropEvent(self, event):
        self.header_dropped.emit(event.source(), self)
