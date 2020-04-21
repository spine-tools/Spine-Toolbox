######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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
from PySide2.QtCore import Signal, Slot, Qt, QMimeData, QUrl, QEvent
from PySide2.QtGui import QDrag, QMouseEvent


class CopyTreeView(QTreeView):
    """Custom QTreeView class with copy support.
    """

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)

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


class EntityTreeView(CopyTreeView):
    """Custom QTreeView class for object tree in DataStoreForm.

    Attributes:
        parent (QWidget): The parent of this view
    """

    edit_key_pressed = Signal("QModelIndex")

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)

    @Slot("QModelIndex", "EditTrigger", "QEvent")
    def edit(self, index, trigger, event):
        """Send signal instead of editing item, so
        DataStoreForm can catch this signal and open a custom QDialog
        for edition.
        """
        if trigger == QTreeView.EditKeyPressed:
            self.edit_key_pressed.emit(index)
        return False


class StickySelectionEntityTreeView(EntityTreeView):
    """Custom QTreeView class for object tree in DataStoreForm.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def mousePressEvent(self, event):
        """Overrides selection behaviour if the user has selected sticky
        selection in Settings. If sticky selection is enabled, multi-selection is
        enabled when selecting items in the Object tree. Pressing the Ctrl-button down,
        enables single selection. If sticky selection is disabled, single selection is
        enabled and pressing the Ctrl-button down enables multi-selection.

        Args:
            event (QMouseEvent)
        """
        sticky_selection = self.qsettings.value("appSettings/stickySelection", defaultValue="false")
        if sticky_selection == "false":
            super().mousePressEvent(event)
            return
        local_pos = event.localPos()
        window_pos = event.windowPos()
        screen_pos = event.screenPos()
        button = event.button()
        buttons = event.buttons()
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            modifiers &= ~Qt.ControlModifier
        else:
            modifiers |= Qt.ControlModifier
        source = event.source()
        new_event = QMouseEvent(
            QEvent.MouseButtonPress, local_pos, window_pos, screen_pos, button, buttons, modifiers, source
        )
        super().mousePressEvent(new_event)


class ReferencesTreeView(QTreeView):
    """Custom QTreeView class for 'References' in Data Connection properties.

    Attributes:
        parent (QWidget): The parent of this view
    """

    files_dropped = Signal("QVariant", name="files_dropped")
    del_key_pressed = Signal(name="del_key_pressed")

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

    def keyPressEvent(self, event):
        """Overridden method to make the view support deleting items with a delete key."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.del_key_pressed.emit()


class DataTreeView(QTreeView):
    """Custom QTreeView class for 'Data' in Data Connection properties.

    Attributes:
        parent (QWidget): The parent of this view
    """

    files_dropped = Signal("QVariant", name="files_dropped")
    del_key_pressed = Signal(name="del_key_pressed")

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self.drag_start_pos = None
        self.drag_indexes = list()

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
        """Register drag start position."""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.drag_indexes = self.selectedIndexes()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Start dragging action if needed."""
        if not event.buttons() & Qt.LeftButton:
            return
        if not self.drag_start_pos:
            return
        if not self.drag_indexes:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mimeData = QMimeData()
        urls = list()
        for index in self.drag_indexes:
            file_path = index.data(Qt.UserRole)
            urls.append(QUrl.fromLocalFile(file_path))
        mimeData.setUrls(urls)
        drag.setMimeData(mimeData)
        icon = self.drag_indexes[0].data(Qt.DecorationRole)
        if icon:
            pixmap = icon.pixmap(32, 32)
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())
        drag.exec_()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)  # Fixes bug in extended selection

    def keyPressEvent(self, event):
        """Overridden method to make the view support deleting items with a delete key."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.del_key_pressed.emit()


class SourcesTreeView(QTreeView):
    """Custom QTreeView class for 'Sources' in Tool specification editor widget.

    Attributes:
        parent (QWidget): The parent of this view
    """

    files_dropped = Signal("QVariant", name="files_dropped")
    del_key_pressed = Signal(name="del_key_pressed")

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

    def keyPressEvent(self, event):
        """Overridden method to make the view support deleting items with a delete key."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.del_key_pressed.emit()


class CustomTreeView(QTreeView):
    """Custom QTreeView class for Tool specification editor form to enable keyPressEvent.

    Attributes:
        parent (QWidget): The parent of this view
    """

    del_key_pressed = Signal(name="del_key_pressed")

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)

    def keyPressEvent(self, event):
        """Overridden method to make the view support deleting items with a delete key."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.del_key_pressed.emit()
