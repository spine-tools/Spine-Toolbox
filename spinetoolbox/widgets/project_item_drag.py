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

from PySide2.QtCore import Qt, Signal, Slot, QMimeData, QRect
from PySide2.QtGui import QDrag, QIcon, QPainter, QBrush, QColor, QFont, QFontMetrics
from PySide2.QtWidgets import QToolButton, QApplication, QToolBar, QWidgetAction
from ..helpers import CharIconEngine, make_icon_background


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
    double_clicked = Signal()

    def __init__(self, toolbox, icon, item_type, parent=None):
        super().__init__(toolbox, icon, item_type, parent=parent)
        self.setToolTip(f"<p>Drag-and-drop this onto the Design View to create a new <b>{item_type}</b> item.</p>")

    def _make_mime_data_text(self):
        return ",".join([self.item_type, ""])

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()


class ProjectItemSpecButton(ProjectItemButtonBase):
    def __init__(self, toolbox, icon, item_type, spec_name, max_width=None, parent=None):
        super().__init__(toolbox, icon, item_type, parent=parent)
        self._spec_name = spec_name
        self._set_text(max_width)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setToolTip(
            f"<p>Drag-and-drop this onto the Design View to create a new <b>{self._spec_name}</b> item.</p>"
        )
        self._index = self._toolbox.specification_model.specification_index(self._spec_name)

    def _set_text(self, max_width):
        font = self.font()
        if max_width is None:
            font.setPointSize(9)
            self.setFont(font)
            self.setText(self._spec_name)
            return
        row_count = 0
        while True:
            row_count += 1
            chunk_size = len(self._spec_name) // row_count + 1
            chunks = [self._spec_name[i : i + chunk_size] for i in range(0, len(self._spec_name), chunk_size)]
            for point_size in range(9, 7, -1):
                font.setPointSize(point_size)
                fm = QFontMetrics(font)
                if all(fm.horizontalAdvance(chunk) <= max_width for chunk in chunks):
                    text = "\n".join(chunks)
                    self.setFont(font)
                    self.setText(text)
                    return

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
        rect = ev.rect()
        painter.fillRect(rect, brush)
        painter.end()
        super().paintEvent(ev)


class ShadeProjectItemSpecButton(ShadeMixin, ProjectItemSpecButton):
    def menu_button(self):
        return ProjectItemSpecButton(self._toolbox, self.icon(), self.item_type, self._spec_name, max_width=None)


class ShadeButton(ShadeMixin, QToolButton):
    def menu_button(self):
        button = QToolButton()
        button.setFont(self.font())
        button.setText(self.text())
        button.setIcon(self.icon())
        button.clicked.connect(self.clicked)
        return button


class ProjectItemSpecArray(QToolBar):
    """An array of ProjectItemSpecButton that can be expanded/collapsed."""

    def __init__(self, toolbox, model, item_type):
        """
        Args:
            toolbox (ToolboxUI)
            model (FilteredSpecificationModel)
            item_type (str)
        """
        super().__init__()
        self._extension_button = next(iter(self.findChildren(QToolButton)))
        self._margin = self.layout().margin()
        self._maximum_size = self.maximumSize()
        self._model = model
        self._toolbox = toolbox
        self._item_type = item_type
        self._visible = False
        self._button_visible = QToolButton()
        font = QFont("Font Awesome 5 Free Solid")
        self._button_visible.setFont(font)
        self.addWidget(self._button_visible)
        self._button_new = ShadeButton()
        self._button_new.setIcon(QIcon(CharIconEngine("\uf067", color=Qt.darkGreen)))
        self._button_new.setText("New...")
        self._button_new.setToolTip(f"<p>Create new <b>{item_type}</b> specification...</p>")
        font = QFont()
        font.setPointSize(9)
        self._button_new.setFont(font)
        self._button_new.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._action_new = self.addWidget(self._button_new)
        self._action_new.setVisible(self._visible)
        self._actions = {}
        self._model.rowsInserted.connect(self._insert_specs)
        self._model.rowsRemoved.connect(self._remove_specs)
        self._model.modelReset.connect(self._reset_specs)
        self._button_visible.clicked.connect(self.toggle_visibility)
        self._button_new.clicked.connect(self._show_spec_form)
        self.orientationChanged.connect(self._update_button_geom)

    def set_color(self, color):
        bg = make_icon_background(color)
        ss = f"QMenu {{background: {bg};}}"
        self._extension_button.menu().setStyleSheet(ss)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if not self._visible:
            return
        rect = self._get_filling()
        if rect.isEmpty():
            return
        brush = QBrush(QColor(255, 255, 255, a=96))
        brush.setStyle(Qt.Dense3Pattern)
        painter = QPainter(self)
        painter.fillRect(rect, brush)
        painter.end()

    def _get_filling(self):
        ind, actions, toolbar_size = self._get_first_chopped_index()
        if ind is None:
            return QRect()
        if ind > 0:
            w = self.widgetForAction(actions[ind - 1])
        else:
            w = self._button_visible
        geom = w.geometry()
        return QRect(geom.right() + 1, geom.top(), toolbar_size - geom.right(), geom.height())

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._extension_button.setEnabled(True)
        menu = self._extension_button.menu()
        menu.clear()
        ss = (
            "QToolButton {background-color: rgba(255,255,255,0); border: 1px solid transparent; padding: 3px}"
            "QToolButton:hover {background-color: white; border: 1px solid lightGray; padding: 3px}"
        )
        for act in self._get_chopped_actions():
            button = self.widgetForAction(act).menu_button()
            button.setIconSize(self.iconSize())
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.setStyleSheet(ss)
            action = QWidgetAction(menu)
            action.setDefaultWidget(button)
            menu.addAction(action)

    def _get_chopped_actions(self):
        ind, actions, _ = self._get_first_chopped_index()
        return actions[ind:]

    def _get_toolbar_size(self):
        """Returns the relevant toolbar size for filling, depending on the orientation.

        Returns:
            int
        """
        style = self.style()
        extension_extent = style.pixelMetric(style.PM_ToolBarExtensionExtent)
        margin = self.layout().margin()
        if self.orientation() == Qt.Horizontal:
            return self.width() - extension_extent - 2 * margin + 2
        return self.height() - extension_extent - 2 * margin + 2

    def _get_first_chopped_index(self):
        actions = [self._action_new, *self._actions.values()]
        toolbar_size = self._get_toolbar_size()
        if self.orientation() == Qt.Horizontal:
            f = lambda ref_geom, curr_size: ref_geom.right() + curr_size.width()
        else:
            f = lambda ref_geom, curr_size: ref_geom.bottom() + curr_size.height()
        ref_widget = self._button_visible
        ind = None
        for i, act in enumerate(actions):
            widget = self.widgetForAction(act)
            if f(ref_widget.geometry(), widget.sizeHint()) > toolbar_size:
                ind = i
                break
            ref_widget = widget
        return ind, actions, toolbar_size

    def _update_button_geom(self, orientation=None):
        if orientation is None:
            orientation = self.orientation()
        style = self.style()
        extent = style.pixelMetric(style.PM_ToolBarExtensionExtent)
        widgets = [self.widgetForAction(a) for a in self._actions.values()]
        up, down, right, left = "\uf0d8", "\uf0d7", "\uf0da", "\uf0d9"
        if orientation == Qt.Horizontal:
            icon = right if not self._visible else left
            width = extent
            height = max((w.height() for w in widgets), default=self._button_new.height())
            self._button_new.setMaximumHeight(height)
            for w in widgets:
                w.setMaximumHeight(height)
        else:  # orientation == Qt.Vertical
            icon = down if not self._visible else up
            width = max((w.width() for w in widgets), default=self._button_new.width())
            height = extent
            self._button_new.setMaximumWidth(width)
            for w in widgets:
                w.setMaximumWidth(width)
        self._button_visible.setText(icon)
        self._button_visible.setMaximumWidth(width)
        self._button_visible.setMaximumHeight(height)
        if not self._visible:
            self.layout().setMargin(0)
            self.setMaximumSize(2 * self._button_visible.maximumSize())
            self.setStyleSheet("QToolBar {background: transparent}")
        else:
            self.layout().setMargin(self._margin)
            self.setMaximumSize(self._maximum_size)
            self.setStyleSheet("")

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
        self._update_button_geom()

    def _remove_specs(self, parent, first, last):
        for row in range(first, last + 1):
            action = self._actions.pop(row)
            self.removeAction(action)
        self._update_button_geom()

    def _reset_specs(self):
        for action in self._actions.values():
            self.removeAction(action)
        self._actions.clear()
        for row in range(self._model.rowCount()):
            self._add_spec(row)
        self._update_button_geom()

    def _add_spec(self, row):
        index = self._model.index(row, 0)
        source_index = self._model.mapToSource(index)
        spec = self._model.sourceModel().specification(source_index.row())
        if spec.plugin:
            return
        factory = self._toolbox.item_factories[spec.item_type]
        icon = QIcon(factory.icon())
        button = ShadeProjectItemSpecButton(self._toolbox, icon, spec.item_type, spec.name)
        button.setIconSize(self.iconSize())
        action = self.addWidget(button)
        action.setVisible(self._visible)
        self._actions[row] = action
