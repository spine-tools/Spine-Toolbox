######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
from PySide2.QtCore import Signal, Qt, QMimeData, QUrl
from PySide2.QtGui import QDrag


class CopyTreeView(QTreeView):
    """Custom QTreeView class with copy support."""

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)

    def can_copy(self):
        return not self.selectionModel().selection().isEmpty()

    def copy(self):
        """Copy current selection to clipboard in excel format."""
        selection = self.selectionModel().selection()
        if not selection:
            return False
        indexes = selection.indexes()
        values = [index.data(Qt.EditRole) for index in indexes]
        content = "\n".join(values)
        QApplication.clipboard().setText(content)
        return True


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

    del_key_pressed = Signal()

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)

    def keyPressEvent(self, event):
        """Overridden method to make the view support deleting items with a delete key."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.del_key_pressed.emit()
