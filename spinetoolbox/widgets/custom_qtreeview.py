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
Classes for custom QTreeView.

:author: M. Marin (KTH)
:date:   25.4.2018
"""

import os
from PySide2.QtWidgets import QTreeView, QApplication
from PySide2.QtCore import Signal, Slot, Qt, QMimeData, QUrl
from PySide2.QtGui import QPixmap, QDrag


class ObjectTreeView(QTreeView):
    """Custom QTreeView class for object tree in Data Store form.

    Attributes:
        parent (QWidget): The parent of this view
    """
    
    edit_key_pressed = Signal("QModelIndex", name="edit_key_pressed")
    focus_gained = Signal(name="focus_gained")

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focus_gained.emit()

    @Slot("QModelIndex", "EditTrigger", "QEvent", name="edit")
    def edit(self, index, trigger, event):
        """Send signal instead of editing item.
        The DataStoreWidget will catch this signal and open a custom QDialog
        for edition.
        """
        if trigger == QTreeView.EditKeyPressed:
            self.edit_key_pressed.emit(index)
        return False

    def copy(self):
        """Copy current selection to clipboard in excel format."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        indexes = selection.indexes()
        values = [index.data(Qt.DisplayRole) for index in indexes]
        content = "\n".join(values)
        QApplication.clipboard().setText(content)
        return True


class ReferencesTreeView(QTreeView):
    """Custom QTreeView class for 'references' in Data Connection subwindow.

    Attributes:
        parent (QWidget): The parent of this view
    """
    files_dropped = Signal("QVariant", name="files_dropped")

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)

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
        """Emit files_dropped signal with a list of files for each dropped url."""
        self.files_dropped.emit([url.toLocalFile() for url in event.mimeData().urls()])


class DataTreeView(QTreeView):
    """Custom QTreeView class for 'data' in Data Connection subwindow.

    Attributes:
        parent (QWidget): The parent of this view
    """
    files_dropped = Signal("QVariant", name="files_dropped")

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self.drag_start_pos = None
        self.drag_index = None

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
        """Emit files_dropped signal with a list of files for each dropped url."""
        self.files_dropped.emit([url.toLocalFile() for url in event.mimeData().urls()])

    def mousePressEvent(self, event):
        """Register drag start position"""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.drag_index = self.indexAt(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mimeData = QMimeData()
        data_dir = self.parent().owner().data_dir
        filename = self.drag_index.data(Qt.DisplayRole)
        url = QUrl.fromLocalFile(os.path.join(data_dir, filename))
        mimeData.setUrls([url])
        drag.setMimeData(mimeData)
        icon = self.drag_index.data(Qt.DecorationRole)
        if icon:
            pixmap = icon.pixmap(32, 32)
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())
        dropAction = drag.exec_()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        self.drag_start_pos = None


class SourcesTreeView(QTreeView):
    """Custom QTreeView class for 'Sources' in Tool Template form.

    Attributes:
        parent (QWidget): The parent of this view
    """
    files_dropped = Signal("QVariant", name="files_dropped")

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)

    def dragEnterEvent(self, event):
        """Accept file and folder drops from the filesystem."""
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
        """Emit files_dropped signal with a list of files for each dropped url."""
        self.files_dropped.emit([url.toLocalFile() for url in event.mimeData().urls()])
