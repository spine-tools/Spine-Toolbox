######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for custom context menus and pop-up menus.

:author: P. Savolainen (VTT)
:date:   4.11.2018
"""

from PySide2.QtWidgets import QListWidget, QAbstractItemView
from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QDropEvent

# TODO: rename this class to something better
class TestListView(QListWidget):
    afterDrop = Signal(object, QDropEvent)
    allowedDragLists = []
    
    def __init__(self, parent=None):
        super(TestListView, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropOverwriteMode(False)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        if event.source() == self or event.source() in self.allowedDragLists:
            event.accept()

    def dropEvent(self, event):
        if event.source() == self or event.source() in self.allowedDragLists:
            super(TestListView, self).dropEvent(event)
            self.afterDrop.emit(self, event)


