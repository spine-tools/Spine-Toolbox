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

from PySide2.QtCore import Qt, Signal, Slot, QMimeData
from PySide2.QtGui import QDrag, QIcon, QPainter, QBrush, QColor, QFont
from PySide2.QtWidgets import QToolButton, QApplication
from ..helpers import CharIconEngine


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
        self._toolbox = toolbox
        self.item_type = item_type
        self.setIcon(icon)
        self.setMouseTracking(True)
        self.drag_about_to_start.connect(self._handle_drag_about_to_start)
        self.setStyleSheet("QToolButton{padding: 2px}")

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


class ProjectItemButton(ProjectItemButtonBase):
    def __init__(self, toolbox, icon, item_type, parent=None):
        super().__init__(toolbox, icon, item_type, parent=parent)
        self.spec_array = None
        self.setToolTip(f"<p>Drag-and-drop this onto the Design View to create a new <b>{item_type}</b> item.</p>")

    def _make_mime_data_text(self):
        return ",".join([self.item_type, ""])

    def mouseDoubleClickEvent(self, event):
        if self.spec_array:
            self.spec_array.toggle_visibility()


class ProjectItemSpecButton(ProjectItemButtonBase):
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
        self._index = self._toolbox.specification_model.specification_index(self._spec_name)

    def _make_mime_data_text(self):
        return ",".join([self.item_type, self._spec_name])

    def contextMenuEvent(self, event):
        self._toolbox.show_specification_context_menu(self._index, event.globalPos())

    def mouseDoubleClickEvent(self, event):
        self._toolbox.edit_specification(self._index, None)


class ShadeMixin:
    def paintEvent(self, ev):
        painter = QPainter(self)
        brush = QBrush(QColor(255, 255, 255, a=96))
        painter.fillRect(ev.rect(), brush)
        painter.end()
        super().paintEvent(ev)


class ProjectItemSpecShadeButton(ShadeMixin, ProjectItemSpecButton):
    pass


class QToolShadeButton(ShadeMixin, QToolButton):
    pass


class ProjectItemSpecArray:
    """An array of ProjectItemSpecButton that can be expanded/collapsed."""

    def __init__(self, toolbox, toolbar, model, item_type):
        """
        Args:
            toolbox (ToolboxUI)
            toolbar (MainToolBar)
            model (FilteredSpecificationModel)
            item_type (str)
        """
        self._toolbar = toolbar
        self._model = model
        self._toolbox = toolbox
        self._item_type = item_type
        self._visible = False
        self._separator = self._toolbar.addSeparator()
        self._separator.setVisible(self._visible)
        self._button_visible = QToolButton()
        font = QFont("Font Awesome 5 Free Solid")
        self._button_visible.setFont(font)
        self._toolbar.insertWidget(self._separator, self._button_visible)
        self._button_new = QToolShadeButton()
        self._button_new.setIcon(QIcon(CharIconEngine("\uf067", color=Qt.darkGreen)))
        self._button_new.setText("New...")
        self._button_new.setToolTip(f"<p>Create new <b>{item_type}</b> specification...</p>")
        font = QFont()
        font.setPointSize(9)
        self._button_new.setFont(font)
        self._button_new.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._action_new = self._toolbar.insertWidget(self._separator, self._button_new)
        self._action_new.setVisible(self._visible)
        self._actions = {}
        self._update_button_geom()
        self._model.rowsInserted.connect(self._insert_specs)
        self._model.rowsRemoved.connect(self._remove_specs)
        self._model.modelReset.connect(self._reset_specs)
        self._button_visible.clicked.connect(self.toggle_visibility)
        self._button_new.clicked.connect(self._show_spec_form)
        self._toolbar.orientationChanged.connect(self._update_button_geom)

    def _update_button_geom(self, orientation=None):
        if orientation is None:
            orientation = self._toolbar.orientation()
        style = self._toolbar.style()
        widgets = [self._toolbar.widgetForAction(a) for a in self._actions.values()]
        up, down, right, left = "\uf0d8", "\uf0d7", "\uf0da", "\uf0d9"
        if orientation == Qt.Horizontal:
            icon = right if not self._visible else left
            width = style.pixelMetric(style.PM_ToolBarExtensionExtent)
            height = max((w.height() for w in widgets), default=self._button_new.height())
            self._button_new.setMaximumHeight(height)
            for w in widgets:
                w.setMaximumHeight(height)
        elif orientation == Qt.Vertical:
            icon = down if not self._visible else up
            width = max((w.width() for w in widgets), default=self._button_new.width())
            height = style.pixelMetric(style.PM_ToolBarExtensionExtent)
            self._button_new.setMaximumWidth(width)
            for w in widgets:
                w.setMaximumWidth(width)
        self._button_visible.setText(icon)
        self._button_visible.setMaximumWidth(width)
        self._button_visible.setMaximumHeight(height)

    @Slot(bool)
    def _show_spec_form(self, _checked=False):
        self._toolbox.show_specification_form(self._item_type)

    @Slot(bool)
    def toggle_visibility(self, _checked=False):
        self.set_visible(not self._visible)
        self._update_button_geom()

    def set_visible(self, visible):
        self._visible = visible
        for action in self._actions.values():
            action.setVisible(self._visible)
        self._action_new.setVisible(self._visible)

    def _insert_specs(self, parent, first, last):
        for row in range(first, last + 1):
            self._add_spec(row)

    def _remove_specs(self, parent, first, last):
        for row in range(first, last + 1):
            action = self._actions.pop(row)
            self._toolbar.removeAction(action)

    def _reset_specs(self):
        for action in self._actions.values():
            self._toolbar.removeAction(action)
        self._actions.clear()
        for row in range(self._model.rowCount()):
            self._add_spec(row)

    def _add_spec(self, row):
        index = self._model.index(row, 0)
        source_index = self._model.mapToSource(index)
        spec = self._model.sourceModel().specification(source_index.row())
        if spec.plugin:
            return
        factory = self._toolbox.item_factories[spec.item_type]
        icon = QIcon(factory.icon())
        button = ProjectItemSpecShadeButton(self._toolbox, icon, spec.item_type, spec.name)
        button.setIconSize(self._toolbar.iconSize())
        action = self._toolbar.insertWidget(self._separator, button)
        action.setVisible(self._visible)
        self._actions[row] = action
