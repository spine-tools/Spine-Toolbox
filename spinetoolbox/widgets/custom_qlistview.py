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
Classes for custom QListView.

:author: M. Marin (KTH)
:date:   14.11.2018
"""

from PySide2.QtWidgets import QListView, QApplication
from PySide2.QtGui import QIcon, QPixmap, QDrag
from PySide2.QtCore import Qt, QMimeData


class ObjectClassListView(QListView):
    """Custom QListView class for object class list in GraphViewForm.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self.drag_start_pos = None
        self.pixmap = None
        self.object_class_id = None

    def mousePressEvent(self, event):
        """Register drag start position"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            index = self.indexAt(event.pos())
            self.pixmap = index.data(Qt.DecorationRole).pixmap(self.iconSize())
            self.object_class_id = index.data(Qt.UserRole)

    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        drag.setPixmap(self.pixmap)
        mimeData = QMimeData()
        mimeData.setText(str(self.object_class_id))
        drag.setMimeData(mimeData)
        drag.setHotSpot(self.pixmap.rect().center())
        dropAction = drag.exec_()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        super().mouseReleaseEvent(event)
        self.drag_start_pos = None
