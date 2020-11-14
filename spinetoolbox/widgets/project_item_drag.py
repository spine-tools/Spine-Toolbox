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

from PySide2.QtWidgets import QListView
from PySide2.QtCore import Qt, QSize, Signal, Slot, QMimeData, QModelIndex
from PySide2.QtGui import QDrag, QResizeEvent, QPainter, QCursor
from PySide2.QtWidgets import QMenu, QToolButton, QApplication
from .custom_qwidgets import CustomWidgetAction
from ..config import ICON_BACKGROUND


class ProjectItemDragMixin:
    """Custom class with dragging support.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None

    def mouseMoveEvent(self, event):
        """Start dragging action if needed"""
        super().mouseMoveEvent(event)
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


class ProjectItemButton(ProjectItemDragMixin, QToolButton):
    def __init__(self, toolbox, icon, item_type, supports_specs, parent=None):
        super().__init__(parent=parent)
        self._toolbox = toolbox
        self.item_type = item_type
        self.setIcon(icon)
        self.setMouseTracking(True)
        self.setToolTip(f"<p>Drag-and-drop this onto the Design View to create a new <b>{item_type}</b> item.</p>")
        if not supports_specs:
            self.list_view = None
            return
        self.list_view = ProjectItemDragListView()
        self.list_view.doubleClicked.connect(self._toolbox.edit_specification)
        self.list_view.context_menu_requested.connect(self._toolbox.show_specification_context_menu)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        menu = QMenu(self)
        widget_action = CustomWidgetAction(menu)
        widget_action.setDefaultWidget(self.list_view)
        menu.addAction(widget_action)
        menu.addSeparator()
        menu.addAction(
            icon,
            f"Create new {item_type} Specification...",
            lambda checked=False, item_type=item_type: self._toolbox.show_specification_form(
                item_type, specification=None
            ),
        )
        self.setMenu(menu)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self._toolbox.specification_model_changed.connect(self._update_spec_model)

    def setIconSize(self, size):
        super().setIconSize(size)
        if self.list_view:
            self.list_view.setIconSize(size)

    @Slot()
    def _update_spec_model(self):
        model = self._toolbox.filtered_spec_factory_models.get(self.item_type)
        self.list_view.setModel(model)
        self._resize_list_view()
        model.rowsInserted.connect(lambda *args: self._resize_list_view())
        model.rowsRemoved.connect(lambda *args: self._resize_list_view())

    def _resize_list_view(self):
        self.list_view._resize_to_contents()
        event = QResizeEvent(QSize(), self.menu().size())
        QApplication.sendEvent(self.menu(), event)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self.isDown():
            self.setDown(False)
            self.update()

    def mousePressEvent(self, event):
        """Register drag start position"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.pixmap = self.icon().pixmap(self.iconSize())
            mime_data_text = ",".join([self.item_type, ""])
            self.mime_data = QMimeData()
            self.mime_data.setText(mime_data_text)


class ProjectItemDragListView(ProjectItemDragMixin, QListView):

    context_menu_requested = Signal("QModelIndex", "QPoint")

    def __init__(self):
        super().__init__(None)
        self.setStyleSheet(
            f"QListView{{background: {ICON_BACKGROUND}; padding: 3px; border: 1px solid gray;}}"
            "QListView::item{padding: 3px;}"
            "QListView::item:hover{background: white; padding-left: -1px; border: 1px solid lightGray; border-radius: 1px}"
        )
        self.setSelectionRectVisible(False)
        self.setResizeMode(QListView.Adjust)
        self.setUniformItemSizes(True)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def paintEvent(self, event):
        self.setCurrentIndex(QModelIndex())
        super().paintEvent(event)

    def contextMenuEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return
        source_index = self.model().mapToSource(index)
        self.context_menu_requested.emit(source_index, event.globalPos())

    def mousePressEvent(self, event):
        """Register drag start position"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            index = self.indexAt(event.pos())
            if not index.isValid():
                self.drag_start_pos = None
                self.pixmap = None
                self.mime_data = None
                return
            self.drag_start_pos = event.pos()
            self.pixmap = index.data(Qt.DecorationRole).pixmap(self.iconSize())
            mime_data_text = self.model().get_mime_data_text(index)
            self.mime_data = QMimeData()
            self.mime_data.setText(mime_data_text)

    @Slot()
    def _resize_to_contents(self):
        model = self.model()
        if not model:
            self.setFixedHeight(0)
            return
        row_height = self.visualRect(model.index(0, 0)).height()
        height = row_height * model.rowCount() + 2 * self.frameWidth()
        self.setFixedHeight(height)
