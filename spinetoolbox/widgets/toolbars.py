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

"""
Functions to make and handle QToolBars.
"""

from PySide6.QtCore import Qt, Slot, QModelIndex
from PySide6.QtWidgets import QToolBar, QToolButton, QMenu
from PySide6.QtGui import QIcon, QPainter, QFontMetrics
from ..helpers import make_icon_toolbar_ss, ColoredIcon, CharIconEngine
from .project_item_drag import NiceButton, ProjectItemButton, ProjectItemSpecButton


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
        self._title_font = self.font()
        self._title_font.setItalic(True)
        self._title_font.setBold(True)
        self._title_font.setPointSize(self._title_font.pointSize() - 2)
        self._title_height = QFontMetrics(self._title_font).height()
        self._title_margin = 0.25 * self._title_height

    def name(self):
        return self._name

    def sizeHint(self):
        size = super().sizeHint()
        title_width = QFontMetrics(self._title_font).horizontalAdvance(self.name())
        size.setWidth(max(size.width(), 2 * self._title_margin + title_width))
        size.setHeight(size.height() + self._title_height + self._title_margin)
        return size

    def paintEvent(self, ev):
        layout = self.layout()
        widgets = [w for i in range(layout.count()) if isinstance((w := layout.itemAt(i).widget()), NiceButton)]
        height = self._title_height + 3 * self._title_margin
        if self.orientation() == Qt.Horizontal:
            for w in widgets:
                w.move(w.pos().x(), height)
        elif self.orientation() == Qt.Vertical:
            top_w = min(widgets, key=lambda w: w.pos().y())
            adjustment = height - top_w.pos().y()
            if adjustment > 0:
                for w in widgets:
                    pos = w.pos()
                    w.move(pos.x(), pos.y() + adjustment)
        super().paintEvent(ev)
        painter = QPainter(self)
        painter.setFont(self._title_font)
        painter.drawText(2 * self._title_margin, self._title_height + self._title_margin, self.name())
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

    def _add_tool_button(self, button):
        """Adds a button to the toolbar.

        Args:
            button (QToolButton): button to add
        """
        button.setStyleSheet("QToolButton{padding: 2px}")
        button.set_orientation(self.orientation())
        self.orientationChanged.connect(button.set_orientation)
        self.addWidget(button)

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
                self.addWidget(button)
                self._buttons[spec.name] = button

    @Slot(str, str)
    def _update_spec_button_name(self, old_name, new_name):
        button = self._buttons.pop(old_name, None)
        if button is None:
            return
        self._buttons[new_name] = button
        button.spec_name = new_name


class ProjectToolBar(ToolBar):
    def __init__(self, parent):
        super().__init__("Project specific", parent)  # Inherits stylesheet from ToolboxUI
        self._actions = {}
        self._model = None

    def name(self):
        return self._name + " items"

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
        action = self.insertWidget(self._actions[next_spec.name], button) if next_spec else self.addWidget(button)
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


class BaseToolBar(ToolBar):
    """The base items"""

    _SEPARATOR = ";;"

    def __init__(self, parent):
        """
        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Generic", parent)  # Inherits stylesheet from ToolboxUI
        self._buttons = []
        self._drop_source_action = None
        self._drop_target_action = None
        self.setAcceptDrops(True)

    def name(self):
        return self._name + " items"

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
        if factory.is_deprecated() or self._toolbox.supports_specification(item_type):
            return
        icon = self._icon_from_factory(factory)
        button = ProjectItemButton(self._toolbox, item_type, icon)
        button.set_orientation(self.orientation())
        self.orientationChanged.connect(button.set_orientation)
        self.addWidget(button)
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
        if self._drop_target_action != self._drop_source_action:
            self.insertAction(self._drop_target_action, self._drop_source_action)
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
        source_action = next((a for a in actions if self.widgetForAction(a) == source))
        target_index = next((i for i, a in enumerate(actions) if self.widgetForAction(a) == target))
        if after:
            target_index += 1
        target_action = actions[target_index]
        self._drop_source_action = source_action
        self._drop_target_action = target_action

    def paintEvent(self, ev):
        """Draw a line as drop indicator."""
        super().paintEvent(ev)
        if self._drop_target_action is None:
            return
        painter = QPainter(self)
        painter.drawLine(*self._drop_line())  # Draw line from (x1, y1) to (x2, y2)
        painter.end()

    def _drop_line(self):
        widget = self.widgetForAction(self._drop_target_action)
        geom = widget.geometry()
        margins = self.layout().contentsMargins()
        if self.orientation() == Qt.Orientation.Horizontal:
            x = geom.left() - 1
            return x, margins.left(), x, self.height() - margins.top()
        y = geom.top() - 1
        return margins.top(), y, self.width() - margins.left(), y

    def icon_ordering(self):
        item_types = []
        for a in self.actions():
            w = self.widgetForAction(a)
            if not isinstance(w, ProjectItemButton):
                continue
            item_types.append(w.item_type)
        return self._SEPARATOR.join(item_types)


class ExecuteToolBar(ToolBar):
    def __init__(self, execute_project_action, execute_selection_action, stop_execution_action, parent):
        """
        Args:
            execute_project_action (QAction): action to execute project
            execute_selection_action (QAction): action to execute selected items
            stop_execution_action (QAction): action to stop execution
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Execute", parent)  # Inherits stylesheet from ToolboxUI
        self._execute_project_action = execute_project_action
        self.execute_project_button = None
        self._execute_selection_action = execute_selection_action
        self.execute_selection_button = None
        self._stop_execution_action = stop_execution_action
        self.stop_execution_button = None
        self.setAcceptDrops(False)

    def setup(self):
        self.add_execute_buttons()

    def add_execute_buttons(self):
        """Adds project execution buttons to the toolbar."""
        self.execute_project_button = NiceButton()
        self.execute_project_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.execute_project_button.setDefaultAction(self._execute_project_action)
        self._add_tool_button(self.execute_project_button)
        self.execute_selection_button = NiceButton()
        self.execute_selection_button.setDefaultAction(self._execute_selection_action)
        self._add_tool_button(self.execute_selection_button)
        self.stop_execution_button = NiceButton()
        self.stop_execution_button.setDefaultAction(self._stop_execution_action)
        self._add_tool_button(self.stop_execution_button)
