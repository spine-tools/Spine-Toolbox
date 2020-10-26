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
Classes for custom QListView.

:author: M. Marin (KTH)
:date:   14.11.2018
"""

from PySide2.QtWidgets import QListView, QApplication
from PySide2.QtGui import QDrag
from PySide2.QtCore import Qt, QMimeData, QSize, Slot


class DragListView(QListView):
    """Custom QListView class with dragging support.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None

    def mousePressEvent(self, event):
        """Register drag start position"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.pos())
            if not index.isValid() or not index.model().is_index_draggable(index):
                self.drag_start_pos = None
                self.pixmap = None
                self.mime_data = None
                return
            self.drag_start_pos = event.pos()
            self.pixmap = index.data(Qt.DecorationRole).pixmap(self.iconSize())
            mime_data_text = self.model().get_mime_data_text(index)
            self.mime_data = QMimeData()
            self.mime_data.setText(mime_data_text)

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
        drag.setMimeData(self.mime_data)
        drag.setHotSpot(self.pixmap.rect().center())
        drag.exec_()
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        super().mouseReleaseEvent(event)
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None


class ProjectItemDragListView(DragListView):
    def __init__(self):
        super().__init__(None)
        self._toolbar = None
        self._orientation = None
        self._obscured = None
        self._contents_size = QSize()
        self._scroll_sub_line_action = None
        self._scroll_add_line_action = None
        base_size = QSize(24, 24)
        self.setIconSize(base_size)
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
        self.setStyleSheet("QListView {background: transparent;}")
        self.setResizeMode(DragListView.Adjust)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def add_to_toolbar(self, toolbar):
        """
        Adds this view to a toolbar.

        Args:
            toolbar (MainToolBar)
        """
        self._toolbar = toolbar
        self._create_scroll_sub_line_action()
        self._toolbar.addWidget(self)
        self._create_scroll_add_line_action()
        self._toolbar.orientationChanged.connect(self._handle_orientation_changed)
        self._handle_orientation_changed(self._toolbar.orientation())

    def _create_scroll_sub_line_action(self):
        self._scroll_sub_line_action = self._toolbar.addAction("", self._scroll_sub_line)
        button = self._toolbar.widgetForAction(self._scroll_sub_line_action)
        button.setStyleSheet("background-color: rgba(255, 255, 255, 0); border: 0px")

    def _create_scroll_add_line_action(self):
        self._scroll_add_line_action = self._toolbar.addAction("", self._scroll_add_line)
        button = self._toolbar.widgetForAction(self._scroll_add_line_action)
        button.setStyleSheet("background-color: rgba(255, 255, 255, 0); border: 0px")

    @Slot(bool)
    def _scroll_sub_line(self, _checked=False):
        scrollbar = self._get_scroll_bar()
        scrollbar.setValue(scrollbar.value() - scrollbar.singleStep())

    @Slot(bool)
    def _scroll_add_line(self, _checked=False):
        scrollbar = self._get_scroll_bar()
        scrollbar.setValue(scrollbar.value() + scrollbar.singleStep())

    def _get_scroll_bar(self):
        if self._orientation == Qt.Horizontal:
            return self.horizontalScrollBar()
        if self._orientation == Qt.Vertical:
            return self.verticalScrollBar()

    @Slot("Qt::Orientation")
    def _handle_orientation_changed(self, orientation):
        self._orientation = orientation
        scroll_sub_line_button = self._toolbar.widgetForAction(self._scroll_sub_line_action)
        scroll_add_line_button = self._toolbar.widgetForAction(self._scroll_add_line_action)
        max_width = self.sizeHintForColumn(0)
        max_height = self.sizeHintForRow(0)
        row_count = self.model().rowCount() if self.model() else 0
        if self._orientation == Qt.Horizontal:
            self.setFlow(QListView.LeftToRight)
            scroll_sub_line_button.setArrowType(Qt.LeftArrow)
            scroll_add_line_button.setArrowType(Qt.RightArrow)
            max_width *= row_count
        elif self._orientation == Qt.Vertical:
            self.setFlow(QListView.TopToBottom)
            scroll_sub_line_button.setArrowType(Qt.UpArrow)
            scroll_add_line_button.setArrowType(Qt.DownArrow)
            max_height *= row_count
        self._contents_size = QSize(max_width, max_height)
        margin = 2 * self.frameWidth()
        max_size = self._contents_size + QSize(margin, margin)
        self.setMaximumSize(max_size)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        viewport_size = self.viewport().size()
        if self._orientation == Qt.Horizontal:
            obscured = self._contents_size.width() > viewport_size.width()
        elif self._orientation == Qt.Vertical:
            obscured = self._contents_size.height() > viewport_size.height()
        self._update_obscured(obscured)

    def _update_obscured(self, obscured):
        if self._obscured == obscured:
            return
        self._obscured = obscured
        self._scroll_sub_line_action.setVisible(obscured)
        self._scroll_add_line_action.setVisible(obscured)
