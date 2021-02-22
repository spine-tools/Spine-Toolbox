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
from ..helpers import make_icon_background


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


class ProjectItemButtonBase(ProjectItemDragMixin, QToolButton):
    def __init__(self, toolbox, icon, item_type, parent=None):
        super().__init__(parent=parent)
        self.item_type = item_type
        self.setIcon(icon)
        self.setMouseTracking(True)
        self.drag_about_to_start.connect(self._handle_drag_about_to_start)

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
            self.mime_data = QMimeData()
            self.mime_data.setText(self._make_mime_data_text())

    def _make_mime_data_text(self):
        raise NotImplementedError()


class PluginProjectItemSpecButton(ProjectItemButtonBase):
    def __init__(self, toolbox, icon, item_type, spec_name, parent=None):
        super().__init__(toolbox, icon, item_type, parent=parent)
        self._spec_name = spec_name
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
        self.setText(spec_name)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setToolTip(
            f"<p>Drag-and-drop this onto the Design View to create a new <b>{self._spec_name}</b> item.</p>"
        )

    def _make_mime_data_text(self):
        return ",".join([self.item_type, self._spec_name])


class ProjectItemButton(ProjectItemButtonBase):
    def __init__(self, toolbox, icon, item_type, parent=None):
        super().__init__(toolbox, icon, item_type, parent=parent)
        self.setToolTip(f"<p>Drag-and-drop this onto the Design View to create a new <b>{item_type}</b> item.</p>")
        if not toolbox.supports_specification(item_type):
            self._list_view = None
            self._menu = None
            return
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._list_view = ProjectItemDragListView()
        self._list_view.doubleClicked.connect(toolbox.edit_specification)
        self._list_view.context_menu_requested.connect(toolbox.show_specification_context_menu)
        self._list_widget = _CreateNewSpecListWidget(item_type)
        self._list_widget.itemClicked.connect(lambda _, item_type=item_type: toolbox.show_specification_form(item_type))
        self._menu = QMenu(self)  # Drop-down menu
        widget_action = CustomWidgetAction(self._menu)
        widget_action.setDefaultWidget(self._list_view)
        self._menu.addAction(widget_action)
        widget_action = CustomWidgetAction(self._menu)
        widget_action.setDefaultWidget(self._list_widget)
        self._menu.addAction(widget_action)
        self.setMenu(self._menu)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self._resize()
        model = toolbox.filtered_spec_factory_models.get(self.item_type)
        self._list_view.setModel(model)
        model.rowsInserted.connect(lambda *args: self._resize())
        model.rowsRemoved.connect(lambda *args: self._resize())
        model.modelReset.connect(lambda *args: self._resize())
        self._list_view.drag_about_to_start.connect(self._menu.hide)

    def set_menu_color(self, color):
        if self._menu:
            self._menu.setStyleSheet(f"QMenu{{background: {make_icon_background(color)};}}")

    def setIconSize(self, size):
        super().setIconSize(size)
        if self._list_view:
            self._list_view.setIconSize(size)

    def _resize(self):
        self._list_view._set_preferred_height()
        self._list_widget._set_preferred_height()
        width = max(self._list_view._get_preferred_width(), self._list_widget._get_preferred_width())
        self._list_view.setFixedWidth(width)
        self._list_widget.setFixedWidth(width)
        event = QResizeEvent(QSize(), self.menu().size())
        QApplication.sendEvent(self.menu(), event)

    def _make_mime_data_text(self):
        return ",".join([self.item_type, ""])


_VIEW_STYLE_SHEET = "QListView{background: transparent; border: 1px solid gray;} QListView::item{padding: 5px;}"
_VIEW_HOVER_STYLE_SHEET_ADDENDUM = (
    "QListView::item:hover{background: white; padding-left: -1px; border: 1px solid lightGray; border-radius: 1px}"
)


class _CreateNewSpecListWidget(QListWidget):
    """A list widget with only one item, to create a new spec.
    Used as widget action for the last entry in ProjectItemButton's menu
    """

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

    def _set_preferred_height(self):
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

    def _set_preferred_height(self):
        model = self.model()
        if not model:
            self.setFixedHeight(0)
            return
        height = self.visualRect(model.index(0, 0)).height() * model.rowCount() + 2 * self.frameWidth()
        self.setFixedHeight(height)

    def _get_preferred_width(self):
        return self.sizeHintForColumn(0) + 2 * self.frameWidth()
