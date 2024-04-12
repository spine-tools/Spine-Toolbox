######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Classes for custom QTreeView."""
import os
from PySide6.QtWidgets import QTreeView, QApplication
from PySide6.QtCore import Signal, Qt


class CopyPasteTreeView(QTreeView):
    """Custom QTreeView class with copy and paste support."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent=parent)

    def can_copy(self):
        """Returns True if tree view has a selection to copy from.

        Returns:
            bool: True if there is something to copy
        """
        return not self.selectionModel().selection().isEmpty()

    def can_paste(self):
        """Returns whether it is possible to paste into this view.

        Returns:
            bool: True if pasting is possible, False otherwise
        """
        return False

    def copy(self):
        """Copy current selection to clipboard.

        The default implementation copies the data as linefeed separated list.

        Returns:
            bool: True if data was successfully copied, False otherwise
        """
        selection = self.selectionModel().selection()
        if not selection:
            return False
        indexes = selection.indexes()
        values = [index.data(Qt.ItemDataRole.EditRole) for index in indexes]
        content = "\n".join(values)
        QApplication.clipboard().setText(content)
        return True

    def paste(self):
        """Pastes data to the view."""


class SourcesTreeView(QTreeView):
    """Custom QTreeView class for 'Sources' in Tool specification editor widget."""

    files_dropped = Signal(list)
    del_key_pressed = Signal()

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
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
    """Custom QTreeView class for Tool specification editor form to enable keyPressEvent."""

    del_key_pressed = Signal()

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): The parent of this view
        """
        super().__init__(parent=parent)

    def keyPressEvent(self, event):
        """Overridden method to make the view support deleting items with a delete key."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.del_key_pressed.emit()
