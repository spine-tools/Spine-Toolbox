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
Classes for custom QListView.

:author: M. Marin (KTH)
:date:   14.11.2018
"""

from PySide2.QtWidgets import QListView, QListWidget
from PySide2.QtCore import Qt, QSize, Signal, Slot, QMimeData, QModelIndex
from PySide2.QtGui import QDrag, QResizeEvent, QIcon
from PySide2.QtWidgets import QMenu, QToolButton, QApplication
from .custom_qwidgets import CustomWidgetAction
from ..config import ICON_BACKGROUND


class ProjectItemDragMixin:
    """Custom class with dragging support.
    """

    drag_about_to_start = Signal()

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
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None
        self.drag_about_to_start.emit()
        drag.exec_()

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
            self._list_view = None
            return
        self._list_view = ProjectItemDragListView()
        self._list_view.doubleClicked.connect(self._toolbox.edit_specification)
        self._list_view.context_menu_requested.connect(self._toolbox.show_specification_context_menu)
        self._list_widget = CreateNewSpecListWidget(item_type)
        self._list_widget.itemClicked.connect(
            lambda _, item_type=item_type: self._toolbox.show_specification_form(item_type)
        )
        menu = QMenu(self)
        widget_action = CustomWidgetAction(menu)
        widget_action.setDefaultWidget(self._list_view)
        menu.addAction(widget_action)
        widget_action = CustomWidgetAction(menu)
        widget_action.setDefaultWidget(self._list_widget)
        menu.addAction(widget_action)
        menu.setStyleSheet(f"QMenu{{background: {ICON_BACKGROUND};}}")
        self.setMenu(menu)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._resize()
        model = self._toolbox.filtered_spec_factory_models.get(self.item_type)
        self._list_view.setModel(model)
        model.rowsInserted.connect(lambda *args: self._resize())
        model.rowsRemoved.connect(lambda *args: self._resize())
        self.drag_about_to_start.connect(self._handle_drag_about_to_start)
        self._list_view.drag_about_to_start.connect(menu.hide)

    def setIconSize(self, size):
        super().setIconSize(size)
        if self._list_view:
            self._list_view.setIconSize(size)

    def _resize(self):
        self._list_view._set_preferred_heigth()
        self._list_widget._set_preferred_heigth()
        width = max(self._list_view._get_preferred_width(), self._list_widget._get_preferred_width())
        self._list_view.setFixedWidth(width)
        self._list_widget.setFixedWidth(width)
        event = QResizeEvent(QSize(), self.menu().size())
        QApplication.sendEvent(self.menu(), event)

    @Slot()
    def _handle_drag_about_to_start(self):
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


_VIEW_STYLE_SHEET = "QListView{background: transparent; border: 1px solid gray;} QListView::item{padding: 5px;}"
_VIEW_HOVER_STYLE_SHEET_ADDENDUM = (
    "QListView::item:hover{background: white; padding-left: -1px; border: 1px solid lightGray; border-radius: 1px}"
)


class CreateNewSpecListWidget(QListWidget):
    def __init__(self, item_type):
        super().__init__(None)
        self.setStyleSheet(_VIEW_STYLE_SHEET + _VIEW_HOVER_STYLE_SHEET_ADDENDUM)
        self.setResizeMode(QListView.Adjust)
        self.addItem(f"Create new {item_type} Specification...")
        item = self.item(0)
        item.setIcon(QIcon(":/icons/wrench_plus.svg"))
        item.setFlags(Qt.ItemIsEnabled)

    def paintEvent(self, event):
        self.setCurrentIndex(QModelIndex())
        super().paintEvent(event)

    def _set_preferred_heigth(self):
        item = self.item(0)
        rect = self.visualItemRect(item)
        height = rect.height() + 2 * self.frameWidth()
        self.setFixedHeight(height)

    def _get_preferred_width(self):
        return self.sizeHintForColumn(0) + 2 * self.frameWidth()


class ProjectItemDragListView(ProjectItemDragMixin, QListView):

    context_menu_requested = Signal("QModelIndex", "QPoint")

    def __init__(self):
        super().__init__(None)
        self._hover = True
        self._main_style_sheet = _VIEW_STYLE_SHEET
        self._hover_addendum = _VIEW_HOVER_STYLE_SHEET_ADDENDUM
        self.setStyleSheet(self._main_style_sheet + self._hover_addendum)
        self.setSelectionRectVisible(False)
        self.setResizeMode(QListView.Adjust)
        self.setUniformItemSizes(True)
        self.setMouseTracking(True)

    def _set_hover(self, hover):
        if hover == self._hover:
            return
        self._hover = hover
        style_sheet = self._main_style_sheet
        if hover:
            style_sheet += self._hover_addendum
        self.setStyleSheet(style_sheet)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._set_hover(False)

    def mouseMoveEvent(self, event):
        if self.indexAt(event.pos()).isValid():
            self._set_hover(True)
        super().mouseMoveEvent(event)

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

    def _set_preferred_heigth(self):
        model = self.model()
        if not model:
            self.setFixedHeight(0)
            return
        height = self.visualRect(model.index(0, 0)).height() * model.rowCount() + 2 * self.frameWidth()
        self.setFixedHeight(height)

    def _get_preferred_width(self):
        return self.sizeHintForColumn(0) + 2 * self.frameWidth()
