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

"""Functions to make and handle QToolBars."""
from PySide6.QtCore import Qt, Slot, QModelIndex, QPoint, QSize
from PySide6.QtWidgets import QToolBar, QToolButton, QMenu, QWidget
from PySide6.QtGui import QIcon, QPainter, QFontMetrics, QPainterPath
from ..helpers import make_icon_toolbar_ss, ColoredIcon, CharIconEngine
from .project_item_drag import NiceButton, ProjectItemButton, ProjectItemSpecButton


class _TitleWidget(QWidget):
    def __init__(self, title, toolbar):
        self._toolbar = toolbar
        super().__init__()
        self._title = title
        font = self.font()
        font.setPointSize(8)
        self.setFont(font)
        self.setMaximumSize(1, 1)
        fm = QFontMetrics(self.font())
        height = fm.height()
        self.margin = 0.25 * height
        self.desired_height = height + 2 * self.margin
        self.desired_width = fm.horizontalAdvance(self._title) + 2 * self.margin

    def sizeHint(self):
        if self._toolbar.orientation() == Qt.Horizontal:
            return QSize(1, 1)
        return QSize(self.desired_width, self.desired_height)

    def paintEvent(self, ev):
        self.setFixedSize(self.sizeHint())
        painter = QPainter(self)
        self.do_paint(painter)
        painter.end()

    def do_paint(self, painter, x=None):
        if x is None:
            x = self.margin
        pos = QPoint(x, self.desired_height - self.margin)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font())
        path = QPainterPath()
        path.addText(pos, self.font(), self._title)
        painter.setPen(Qt.white)
        painter.drawPath(path)
        painter.setPen(Qt.black)
        painter.drawText(pos, self._title)
        painter.restore()


class ToolBar(QToolBar):
    """Base class for Toolbox toolbars."""

    def __init__(self, name, toolbox):
        """
        Args:
            name (str): toolbar's name
            toolbox (ToolboxUI): Toolbox main window
        """
        super().__init__(name, parent=toolbox)
        self._name = name
        self.setObjectName(name.replace(" ", "_"))
        self._toolbox = toolbox
        self.addWidget(_TitleWidget(self.name(), self))

    def name(self):
        return self._name

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if self.orientation() == Qt.Vertical:
            return
        layout = self.layout()
        title_pos_x = (
            (w, layout.itemAt(i + 1).widget().pos().x())
            for i in range(layout.count())
            if isinstance((w := layout.itemAt(i).widget()), _TitleWidget)
        )
        painter = QPainter(self)
        for w, x in title_pos_x:
            w.do_paint(painter, x)
        painter.end()

    def set_colored_icons(self, colored):
        for w in self.buttons():
            w.set_colored_icons(colored)
        self.update()

    def set_color(self, color):
        """Sets toolbar's background color.

        Args:
            color (QColor): background color
        """
        self.setStyleSheet(make_icon_toolbar_ss(color))

    def set_project_actions_enabled(self, enabled):
        """Enables or disables project related actions.

        Args:
            enabled (bool): True to enable actions, False to disable
        """
        for button in self.findChildren(NiceButton):
            button.setEnabled(enabled)

    def _process_tool_button(self, button):
        button.set_orientation(self.orientation())
        self.orientationChanged.connect(button.set_orientation)

    def _insert_tool_button(self, before, button):
        """Inserts button into the toolbar.

        Args:
            before (QWidget): insert before this widget
            button (QToolButton): button to add

        Returns:
            QAction
        """
        self._process_tool_button(button)
        return self.insertWidget(before, button)

    def _add_tool_button(self, button):
        """Adds a button to the toolbar.

        Args:
            button (QToolButton): button to add

        Returns:
            QAction
        """
        self._process_tool_button(button)
        return self.addWidget(button)

    def _make_tool_button(self, icon, text, slot=None, tip=None):
        """Makes a new tool button and adds it to the toolbar.

        Args:
            icon (QIcon): button's icon
            text (str): button's text
            slot (Callable): slot where to connect button's clicked signal
            tip (str): button's tooltip

        Returns:
            QToolButton: created button
        """
        button = NiceButton()
        button.setIcon(icon)
        button.setText(text)
        button.setToolTip(f"<p>{tip}</p>")
        if slot is not None:
            button.clicked.connect(slot)
        self._add_tool_button(button)
        return button

    def _icon_from_factory(self, factory):
        colored = self._toolbox.qsettings().value("appSettings/colorToolbarIcons", defaultValue="false") == "true"
        icon_file_name = factory.icon()
        icon_color = factory.icon_color().darker(120)
        return ColoredIcon(icon_file_name, icon_color, self.iconSize(), colored=colored)


class PluginToolBar(ToolBar):
    """A plugin toolbar."""

    def __init__(self, name, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__(name, parent)  # Inherits stylesheet from ToolboxUI
        self._buttons = {}
        self._toolbox.specification_model.specification_replaced.connect(self._update_spec_button_name)

    def name(self):
        return self._name + " plugin"

    def buttons(self):
        return self._buttons.values()

    def setup(self, plugin_specs, disabled_names):
        """Sets up the toolbar.

        Args:
            plugin_specs (dict): mapping from specification name to specification
            disabled_names (Iterable of str): specifications that should be disabled
        """
        for specs in plugin_specs.values():
            for spec in specs:
                factory = self._toolbox.item_factories[spec.item_type]
                icon = self._icon_from_factory(factory)
                button = ProjectItemSpecButton(self._toolbox, spec.item_type, icon, spec.name)
                button.setIconSize(self.iconSize())
                if spec.name in disabled_names:
                    button.setEnabled(False)
                self._add_tool_button(button)
                self._buttons[spec.name] = button

    @Slot(str, str)
    def _update_spec_button_name(self, old_name, new_name):
        button = self._buttons.pop(old_name, None)
        if button is None:
            return
        self._buttons[new_name] = button
        button.spec_name = new_name


class SpecToolBar(ToolBar):
    def __init__(self, parent):
        super().__init__("Specifications", parent)  # Inherits stylesheet from ToolboxUI
        self._actions = {}
        self._model = None

    def buttons(self):
        return (self.widgetForAction(a) for a in self._actions.values())

    @Slot(QModelIndex, int, int)
    def _insert_specs(self, parent, first, last):
        for row in range(first, last + 1):
            self._add_spec(row)

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
        factory = self._toolbox.item_factories[spec.item_type]
        icon = self._icon_from_factory(factory)
        button = ProjectItemSpecButton(self._toolbox, spec.item_type, icon, spec.name)
        button.setIconSize(self.iconSize())
        action = (
            self._insert_tool_button(self._actions[next_spec.name], button)
            if next_spec
            else self._add_tool_button(button)
        )
        self._actions[spec.name] = action

    @Slot(QModelIndex, int, int)
    def _remove_specs(self, parent, first, last):
        for row in range(first, last + 1):
            self._remove_spec(row)

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

    def setup(self):
        self._model = self._toolbox.specification_model
        self._model.rowsInserted.connect(self._insert_specs)
        self._model.rowsAboutToBeRemoved.connect(self._remove_specs)
        self._model.modelReset.connect(self._reset_specs)
        menu = QMenu(self)
        for item_type, factory in self._toolbox.item_factories.items():
            if factory.is_deprecated() or not self._toolbox.supports_specification(item_type):
                continue
            menu.addAction(
                item_type, lambda item_type=item_type: self._toolbox.show_specification_form(item_type)
            ).setIcon(self._icon_from_factory(factory))
        menu.addSeparator()
        menu.addAction("From specification file...", self._toolbox.import_specification).setIcon(
            QIcon(CharIconEngine("\uf067", color=Qt.darkGreen))
        )
        button = self._make_tool_button(QIcon(CharIconEngine("\uf067", color=Qt.darkGreen)), "New...")
        button.setPopupMode(QToolButton.InstantPopup)
        button.setMenu(menu)


class ItemsToolBar(ToolBar):
    """The base items"""

    _SEPARATOR = ";;"

    def __init__(self, parent):
        """
        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Generic items", parent)  # Inherits stylesheet from ToolboxUI
        self._buttons = []
        self._drop_source_action = None
        self._drop_target_action = None
        self.setAcceptDrops(True)

    def buttons(self):
        return self._buttons

    def setup(self):
        self.add_project_item_buttons()

    def add_project_item_buttons(self):
        icon_ordering = self._toolbox.qsettings().value("appSettings/toolbarIconOrdering", defaultValue="")
        ordered_item_types = icon_ordering.split(self._SEPARATOR)
        for item_type in ordered_item_types:
            factory = self._toolbox.item_factories.get(item_type)
            if factory is None:
                continue
            self._add_project_item_button(item_type, factory)
        for item_type, factory in self._toolbox.item_factories.items():
            if item_type in ordered_item_types:
                continue
            self._add_project_item_button(item_type, factory)

    def _add_project_item_button(self, item_type, factory):
        if factory.is_deprecated():
            return
        icon = self._icon_from_factory(factory)
        button = ProjectItemButton(self._toolbox, item_type, icon)
        self._add_tool_button(button)
        self._buttons.append(button)

    def dragLeaveEvent(self, event):
        event.accept()
        self._drop_source_action = None
        self._drop_target_action = None
        self.update()

    def dragEnterEvent(self, event):
        source = event.source()
        event.setAccepted(isinstance(source, ProjectItemButton))

    def dragMoveEvent(self, event):
        self._update_drop_actions(event)
        event.setAccepted(self._drop_source_action is not None)
        self.update()

    def dropEvent(self, event):
        if self._drop_source_action is not None:
            if self._drop_target_action is not None:
                self.insertAction(self._drop_target_action, self._drop_source_action)
            else:
                self.addAction(self._drop_source_action)
        self._drop_source_action = None
        self._drop_target_action = None
        self.update()

    def _update_drop_actions(self, event):
        """Updates source and target actions for drop operation:

        Args:
            event (QDragMoveEvent)
        """
        self._drop_source_action = None
        self._drop_target_action = None
        source = event.source()
        if not isinstance(source, ProjectItemButton):
            return
        target = self.childAt(event.position().toPoint())
        if target is None:
            return
        while target.parent() != self:
            target = target.parent()
        if not isinstance(target, ProjectItemButton):
            return
        while source.parent() != self:
            source = source.parent()
        if self.orientation() == Qt.Orientation.Horizontal:
            after = target.geometry().center().x() < event.position().toPoint().x()
        else:
            after = target.geometry().center().y() < event.position().toPoint().y()
        actions = self.actions()
        self._drop_source_action = next((a for a in actions if self.widgetForAction(a) == source))
        target_index = next((i for i, a in enumerate(actions) if self.widgetForAction(a) == target))
        if after:
            target_index += 1
        try:
            self._drop_target_action = actions[target_index]
        except IndexError:
            self._drop_target_action = None

    def paintEvent(self, ev):
        """Draw a line as drop indicator."""
        super().paintEvent(ev)
        if self._drop_source_action is None:
            return
        painter = QPainter(self)
        painter.drawLine(*self._drop_line())  # Draw line from (x1, y1) to (x2, y2)
        painter.end()

    def _drop_line(self):
        target_widget = self.widgetForAction(self._drop_target_action) if self._drop_target_action is not None else None
        last_widget = self.widgetForAction(self.actions()[-1])
        margins = self.layout().contentsMargins()
        if self.orientation() == Qt.Orientation.Horizontal:
            x = (target_widget.geometry().left() if target_widget is not None else last_widget.geometry().right()) - 1
            widget = target_widget or last_widget
            return (x, widget.geometry().top(), x, self.height() - margins.bottom())
        y = (target_widget.geometry().top() if target_widget is not None else last_widget.geometry().bottom()) - 1
        return margins.left(), y, self.width() - margins.right(), y

    def icon_ordering(self):
        item_types = []
        for a in self.actions():
            w = self.widgetForAction(a)
            if not isinstance(w, ProjectItemButton):
                continue
            item_types.append(w.item_type)
        return self._SEPARATOR.join(item_types)


class ExecuteToolBar(ToolBar):
    def __init__(self, parent):
        """
        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Execute", parent)  # Inherits stylesheet from ToolboxUI

    def setup(self):
        self._add_buttons()

    def _add_button_from_action(self, action):
        button = NiceButton()
        button.setDefaultAction(action)
        self._add_tool_button(button)

    def _add_buttons(self):
        """Adds buttons to the toolbar."""
        self._add_button_from_action(self._toolbox.ui.actionExecute_project)
        self._add_button_from_action(self._toolbox.ui.actionExecute_selection)
        self._add_button_from_action(self._toolbox.ui.actionStop_execution)
