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
Classes for custom QTreeView.

:author: Manuel Marin <manuelma@kth.se>
:date:   25.4.2018
"""

import os
import logging
from PySide2.QtWidgets import QTreeView, QAbstractItemView
from PySide2.QtCore import Signal, Slot, Qt


class ObjectTreeView(QTreeView):
    """Custom QTreeView class for object tree in Data Store form.

    Attributes:
        parent (QWidget): The parent of this view
    """

    editKeyPressed = Signal("QModelIndex", name="editKeyPressed")

    def __init__(self, parent):
        """Initialize the QGraphicsView."""
        super().__init__(parent)

    @Slot("QModelIndex", "EditTrigger", "QEvent", name="edit")
    def edit(self, index, trigger, event):
        """Send signal instead of editing item.
        The DataStoreWidget will catch this signal and open a custom QDialog
        for edition.
        """
        if trigger == QTreeView.EditKeyPressed:
            self.editKeyPressed.emit(index)
        return False


class ReferencesTreeView(QTreeView):
    """Custom QTreeView class for 'references' in Data Connection subwindow.

    Attributes:
        parent (QWidget): The parent of this view
    """

    file_dropped = Signal("QString", name="file_dropped")

    def __init__(self, parent):
        """Initialize the QGraphicsView."""
        super().__init__(parent)

    def dragEnterEvent(self, event):
        """Accept file drops from the filesystem."""
        urls = event.mimeData().urls()
        for url in urls:
            if not url.isLocalFile():
                event.ignore()
                return
            if not os.path.isfile(url.toLocalFile()):
                event.ignore()
                return
        event.accept()
        event.setDropAction(Qt.LinkAction)

    def dragMoveEvent(self, event):
        """Accept event."""
        event.accept()

    def dropEvent(self, event):
        """Emit signal for each url dropped."""
        for url in event.mimeData().urls():
            self.file_dropped.emit(url.toLocalFile())


class DataTreeView(QTreeView):
    """Custom QTreeView class for 'data' in Data Connection subwindow.

    Attributes:
        parent (QWidget): The parent of this view
    """

    file_dropped = Signal("QString", name="file_dropped")

    def __init__(self, parent):
        """Initialize the QGraphicsView."""
        super().__init__(parent)

    def dragEnterEvent(self, event):
        """Accept file drops from the filesystem."""
        urls = event.mimeData().urls()
        for url in urls:
            if not url.isLocalFile():
                event.ignore()
                return
            if not os.path.isfile(url.toLocalFile()):
                event.ignore()
                return
        event.accept()
        event.setDropAction(Qt.CopyAction)

    def dragMoveEvent(self, event):
        """Accept event."""
        event.accept()

    def dropEvent(self, event):
        """Emit signal for each url dropped."""
        for url in event.mimeData().urls():
            self.file_dropped.emit(url.toLocalFile())
