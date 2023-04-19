######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""

from textwrap import fill
from PySide6.QtCore import QModelIndex, Qt, Signal, Slot, QMimeData, QMargins
from PySide6.QtGui import QDrag, QIcon, QPainter, QBrush, QColor, QFont, QIconEngine
from PySide6.QtWidgets import QToolButton, QApplication, QToolBar, QWidgetAction, QStyle
from ..helpers import CharIconEngine, make_icon_background


class ProjectItemDragMixin:
    """Custom class with dragging support."""

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
        if (event.position().toPoint() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        drag.setPixmap(self.pixmap)
        drag.setMimeData(self.mime_data)
        drag.setHotSpot(self.pixmap.rect().center())
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None
        self.drag_about_to_start.emit()
        drag.exec()

    def mouseReleaseEvent(self, event):
        """Forget drag start position"""
        super().mouseReleaseEvent(event)
        self.drag_start_pos = None
        self.pixmap = None
        self.mime_data = None


class NiceButton(QToolButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

    def setText(self, text):
        super().setText(fill(text, width=12, break_long_words=False))

    def set_orientation(self, orientation):
        if orientation == Qt.Orientation.Horizontal:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        else:
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)


class ProjectItemButtonBase(ProjectItemDragMixin, NiceButton):
    def __init__(self, toolbox, item_type, icon, parent=None):
        super().__init__(parent=parent)
        self._toolbox = toolbox
        self.item_type = item_type
        self._icon = icon
        self.setIcon(icon)
        self.setMouseTracking(True)
        self.drag_about_to_start.connect(self._handle_drag_about_to_start)
        self.setStyleSheet("QToolButton{padding: 2px}")

    def set_colored_icons(self, colored):
        self._icon.set_colored(colored)

    @Slot()
    def _handle_drag_about_to_start(self):
        self.setDown(False)
        self.update()

    def mousePressEvent(self, event):
        """Register drag start position"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.position().toPoint()
            self.pixmap = self.icon().pixmap(self.iconSize())
            self.mime_data = QMimeData()
            self.mime_data.setText(self._make_mime_data_text())

    def _make_mime_data_text(self):
        raise NotImplementedError()


class ProjectItemButton(ProjectItemButtonBase):
    double_clicked = Signal()

    def __init__(self, toolbox, item_type, icon, parent=None):
        super().__init__(toolbox, item_type, icon, parent=parent)
        self.setToolTip(f"<p>Drag-and-drop this onto the Design View to create a new <b>{item_type}</b> item.</p>")
        self.setText(item_type)

    def _make_mime_data_text(self):
        return ",".join([self.item_type, ""])

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()


class ProjectItemSpecButton(ProjectItemButtonBase):
    def __init__(self, toolbox, item_type, icon, spec_name="", parent=None):
        super().__init__(toolbox, item_type, icon, parent=parent)
        self._spec_name = None
        self._index = None
        self.spec_name = spec_name
        self.setText(self.spec_name)

    @property
    def spec_name(self):
        return self._spec_name

    @spec_name.setter
    def spec_name(self, spec_name):
        self._spec_name = spec_name
        self.setText(self._spec_name)
        self.setToolTip(f"<p>Drag-and-drop this onto the Design View to create a new <b>{self.spec_name}</b> item.</p>")

    def _make_mime_data_text(self):
        return ",".join([self.item_type, self.spec_name])

    def contextMenuEvent(self, event):
        index = self._toolbox.specification_model.specification_index(self.spec_name)
        self._toolbox.show_specification_context_menu(index, event.globalPos())

    def mouseDoubleClickEvent(self, event):
        index = self._toolbox.specification_model.specification_index(self.spec_name)
        self._toolbox.edit_specification(index, None)


class ShadeMixin:
    def paintEvent(self, ev):
        painter = QPainter(self)
        brush = QBrush(QColor(255, 255, 255, a=96))
        rect = ev.rect()
        painter.fillRect(rect, brush)
        painter.end()
        super().paintEvent(ev)


class ShadeProjectItemSpecButton(ShadeMixin, ProjectItemSpecButton):
    def clone(self):
        return ShadeProjectItemSpecButton(self._toolbox, self.item_type, self.icon(), self.spec_name)


class ShadeButton(ShadeMixin, NiceButton):
    pass


class _ChoppedIcon(QIcon):
    def __init__(self, icon, size):
        self._engine = _ChoppedIconEngine(icon, size)
        super().__init__(self._engine)

    def update(self):
        self._engine.update()


class _ChoppedIconEngine(QIconEngine):
    def __init__(self, icon, size):
        super().__init__()
        self._pixmap = None
        self._icon = icon
        self._size = size
        self.update()

    def update(self):
        self._pixmap = self._icon.pixmap(self._icon.actualSize(self._size))

    def pixmap(self, size, mode, state):
        return self._pixmap


class ProjectItemSpecArray(QToolBar):
    """An array of ProjectItemSpecButton that can be expanded/collapsed."""

    def __init__(self, toolbox, model, item_type, icon):
        """
        Args:
            toolbox (ToolboxUI)
            model (FilteredSpecificationModel)
            item_type (str)
            icon (ColoredIcon)
        """
        super().__init__()
        self._extension_button = next(iter(self.findChildren(QToolButton)))
        self._margins = QMargins(4, 4, 4, 4)
        self.layout().setContentsMargins(self._margins)
        self._maximum_size = self.maximumSize()
        self._model = model
        self._toolbox = toolbox
        self.item_type = item_type
        self._icon = icon
        self._visible = False
        self._button_base_item = ProjectItemButton(self._toolbox, self.item_type, self._icon)
        self._button_base_item.double_clicked.connect(self.toggle_visibility)
        self.addWidget(self._button_base_item)
        self._button_visible = QToolButton()
        font = QFont("Font Awesome 5 Free Solid")
        font.setPointSize(8)
        self._button_visible.setFont(font)
        self._button_visible.setToolTip(f"<p>Show/hide {self.item_type} specifications</p>")
        self.addWidget(self._button_visible)
        self._button_new = ShadeButton()
        self._button_new.setIcon(QIcon(CharIconEngine("\uf067", color=self._icon.color())))
        self._button_new.setIconSize(self.iconSize())
        self._button_new.setText("New...")
        self._button_new.setToolTip(f"<p>Create new <b>{item_type}</b> specification...</p>")
        self._action_new = self.addWidget(self._button_new)
        self._action_new.setVisible(self._visible)
        self._actions = {}
        self._chopped_icon = _ChoppedIcon(self._icon, self.iconSize())
        self._button_filling = ShadeProjectItemSpecButton(self._toolbox, self.item_type, self._chopped_icon)
        self._button_filling.setParent(self)
        self._button_filling.setVisible(False)
        self._model.rowsInserted.connect(self._insert_specs)
        self._model.rowsAboutToBeRemoved.connect(self._remove_specs)
        self._model.modelReset.connect(self._reset_specs)
        self._button_visible.clicked.connect(self.toggle_visibility)
        self._button_new.clicked.connect(self._show_spec_form)
        self.orientationChanged.connect(self._update_button_geom)

    def set_colored_icons(self, colored):
        self._icon.set_colored(colored)
        self.update()

    def update(self):
        self._chopped_icon.update()
        self._update_button_visible_icon_color()

    def _update_button_visible_icon_color(self):
        mode = QIcon.Active if self._button_base_item.isEnabled() else QIcon.Disabled
        color = self._icon.color(mode=mode)
        self._button_visible.setStyleSheet(f"QToolButton{{ color: {color.name()};}}")

    def set_color(self, color):
        bg = make_icon_background(color)
        ss = f"QMenu {{background: {bg};}}"
        self._extension_button.menu().setStyleSheet(ss)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if not self._visible:
            return
        actions, ind = self._get_first_chopped_index()
        self._add_filling(actions, ind)
        self._populate_extension_menu(actions, ind)

    def _get_first_chopped_index(self):
        """Returns the index of the first chopped action (chopped = not drawn because of space).

        Returns:
            list(QAction)
            int or NoneType
        """
        actions_iter = (self._actions.get(spec.name) for spec in self._model.specifications())
        actions = [act for act in actions_iter if act is not None]
        if self.orientation() == Qt.Orientation.Horizontal:
            get_point = lambda ref_geom: (ref_geom.right() + 1, ref_geom.top())
        else:
            get_point = lambda ref_geom: (ref_geom.left(), ref_geom.bottom() + 1)
        ref_widget = self._button_new
        for i, act in enumerate(actions):
            ref_geom = ref_widget.geometry()
            x, y = get_point(ref_geom)
            if not self.actionAt(x, y):
                return actions, i
            ref_widget = self.widgetForAction(act)
        return actions, None

    def _add_filling(self, actions, ind):
        """Adds a button to fill empty space after the last visible action.

        Args:
            actions (list(QAction)): actions
            ind (int or NoneType): index of the first chopped one or None if all are visible
        """
        if ind is None:
            self._button_filling.setVisible(False)
            return
        if ind > 0:
            previous = self.widgetForAction(actions[ind - 1])
        else:
            previous = self._button_new
        x, y, w, h = self._get_filling(previous)
        if w <= 0 or h <= 0:
            self._button_filling.setVisible(False)
            return
        self._button_filling.move(x, y)
        self._button_filling.setFixedSize(w, h)
        self._button_filling.setVisible(True)
        button = self.widgetForAction(actions[ind])
        self._button_filling.spec_name = button.spec_name

    def _get_filling(self, previous):
        """Returns the position and size of the filling widget.

        Args:
            previous (QWidget): last visible widget

        Returns:
            int: position x
            int: position y
            int: width
            int: height
        """
        geom = previous.geometry()
        style = self.style()
        extension_extent = style.pixelMetric(QStyle.PixelMetric.PM_ToolBarExtensionExtent)
        if self.orientation() == Qt.Orientation.Horizontal:
            toolbar_size = self.width() - extension_extent - 2 * self._margins.left() + 2
            x, y = geom.right() + 1, geom.top()
            w, h = toolbar_size - geom.right(), geom.height()
        else:
            toolbar_size = self.height() - extension_extent - 2 * self._margins.top() + 2
            x, y = geom.left(), geom.bottom() + 1
            w, h = geom.width(), toolbar_size - geom.bottom()
        return x, y, w, h

    def _populate_extension_menu(self, actions, ind):
        """Populates extension menu with chopped actions.

        Args:
            actions (list(QAction)): actions
            ind (int or NoneType): index of the first chopped one or None if all are visible
        """
        self._extension_button.setEnabled(True)
        menu = self._extension_button.menu()
        menu.clear()
        if ind is None:
            return
        ss = (
            "QToolButton {background-color: rgba(255,255,255,0); border: 1px solid transparent; padding: 3px}"
            "QToolButton:hover {background-color: white; border: 1px solid lightGray; padding: 3px}"
        )
        chopped_actions = iter(actions[ind:])
        for act in chopped_actions:
            button = self.widgetForAction(act).clone()
            button.setIconSize(self.iconSize())
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.setStyleSheet(ss)
            action = QWidgetAction(menu)
            action.setDefaultWidget(button)
            menu.addAction(action)

    def showEvent(self, ev):
        super().showEvent(ev)
        self._update_button_geom()

    def _update_button_geom(self, orientation=None):
        """Updates geometry of buttons given the orientation

        Args:
            orientation (Qt.Orientation)
        """
        spacing = 2  # additional space till next toolbar icon when collapsed
        if orientation is None:
            orientation = self.orientation()
        self._button_base_item.set_orientation(orientation)
        self._button_new.set_orientation(orientation)
        widgets = [self.widgetForAction(a) for a in self._actions.values()]
        for w in widgets:
            w.set_orientation(orientation)
        style = self.style()
        extent = style.pixelMetric(QStyle.PixelMetric.PM_ToolBarExtensionExtent)
        down, right = "\uf0d7", "\uf0da"
        if orientation == Qt.Orientation.Horizontal:
            icon = down if not self._visible else right
            width = extent
            min_width = self._button_base_item.sizeHint().width() + extent + self._margins.left() + spacing
            min_visible_width = min_width + self._button_new.sizeHint().width() - spacing
            if widgets:
                min_visible_width += extent
            min_height = self._button_base_item.sizeHint().height()
            min_size = (min_width, min_height)
            min_visible_size = (min_visible_width, min_height)
            height = max((w.sizeHint().height() for w in widgets), default=min_height)
            self._button_new.setMaximumHeight(height)
            for w in widgets:
                w.setMaximumWidth(w.sizeHint().width())
                w.setMaximumHeight(height)
        else:
            icon = right if not self._visible else down
            height = extent
            min_width = self._button_base_item.sizeHint().width()
            min_height = self._button_base_item.sizeHint().height() + extent + self._margins.top() + spacing
            min_visible_height = min_height + self._button_new.sizeHint().height() - spacing
            if widgets:
                min_visible_height += extent
            min_size = (min_width, min_height)
            min_visible_size = (min_width, min_visible_height)
            width = max((w.sizeHint().width() for w in widgets), default=min_width)
            self._button_new.setMaximumWidth(width)
            for w in widgets:
                w.setMaximumWidth(width)
                w.setMaximumHeight(w.sizeHint().height())
        self._button_visible.setText(icon)
        self._button_visible.setMaximumSize(width, height)
        if not self._visible:
            self.setFixedSize(*min_size)
            self.setStyleSheet("QToolBar {background: transparent}")
        else:
            self.setMaximumSize(self._maximum_size)
            self.setMinimumSize(*min_visible_size)
            self.setStyleSheet("")

    @Slot(bool)
    def _show_spec_form(self, _checked=False):
        self._toolbox.show_specification_form(self.item_type)

    @Slot(bool)
    def toggle_visibility(self, _checked=False):
        self.set_visible(not self._visible)
        self._update_button_geom()

    def set_visible(self, visible):
        self._visible = visible
        for action in self._actions.values():
            action.setVisible(self._visible)
        self._action_new.setVisible(self._visible)

    @Slot(QModelIndex, int, int)
    def _insert_specs(self, parent, first, last):
        for row in range(first, last + 1):
            self._add_spec(row)
        self._update_button_geom()

    @Slot(QModelIndex, int, int)
    def _remove_specs(self, parent, first, last):
        for row in range(first, last + 1):
            self._remove_spec(row)
        self._update_button_geom()

    def _remove_spec(self, row):
        spec_name = self._model.index(row, 0).data(Qt.ItemDataRole.DisplayRole)
        try:
            action = self._actions.pop(spec_name)
            self.removeAction(action)
        except KeyError:
            pass  # Happens when Plugins are removed

    @Slot()
    def _reset_specs(self):
        for action in self._actions.values():
            self.removeAction(action)
        self._actions.clear()
        for row in range(self._model.rowCount()):
            self._add_spec(row)
        self._update_button_geom()

    def _add_spec(self, row):
        spec = self._model.specification(row)
        if spec.plugin:
            return
        next_row = row + 1
        while True:
            next_spec = self._model.specification(next_row)
            if next_spec is None or not next_spec.plugin:
                break
            next_row += 1
        button = ShadeProjectItemSpecButton(self._toolbox, spec.item_type, self._icon, spec.name)
        button.setIconSize(self.iconSize())
        button.set_orientation(self.orientation())
        action = self.insertWidget(self._actions[next_spec.name], button) if next_spec else self.addWidget(button)
        action.setVisible(self._visible)
        self._actions[spec.name] = action
