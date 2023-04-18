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
Functions to make and handle QToolBars.
"""

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QToolBar, QLabel
from PySide6.QtGui import QIcon, QPainter
from ..helpers import make_icon_toolbar_ss, ColoredIcon, CharIconEngine
from .project_item_drag import NiceButton, ProjectItemButton, ProjectItemSpecButton, ProjectItemSpecArray


class ToolBar(QToolBar):
    """Base class for Toolbox toolbars."""

    def __init__(self, name, toolbox):
        """
        Args:
            name (str): toolbar's name
            toolbox (ToolboxUI): Toolbox main window
        """
        super().__init__(name, parent=toolbox)
        self.setObjectName(name.replace(" ", "_"))
        self._toolbox = toolbox

    def set_color(self, color):
        """Sets toolbar's background color.

        Args:
            color (QColor): background color
        """
        raise NotImplementedError()

    def set_project_actions_enabled(self, enabled):
        """Enables or disables project related actions.

        Args:
            enabled (bool): True to enable actions, False to disable
        """
        for child_type in (ProjectItemButton, ProjectItemSpecButton):
            for button in self.findChildren(child_type):
                button.setEnabled(enabled)


class PluginToolBar(ToolBar):
    """A plugin toolbar."""

    def __init__(self, name, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__(name, parent)  # Inherits stylesheet from ToolboxUI
        self._name = name
        self._buttons = {}
        self._toolbox.specification_model.specification_replaced.connect(self._update_spec_button_name)

    def setup(self, plugin_specs, disabled_names):
        """Sets up the toolbar.

        Args:
            plugin_specs (dict): mapping from specification name to specification
            disabled_names (Iterable of str): specifications that should be disabled
        """
        self.addWidget(PaddingLabel(self._name))
        for specs in plugin_specs.values():
            for spec in specs:
                factory = self._toolbox.item_factories[spec.item_type]
                icon = QIcon(factory.icon())
                button = ProjectItemSpecButton(self._toolbox, spec.item_type, icon, spec.name)
                button.setIconSize(self.iconSize())
                if spec.name in disabled_names:
                    button.setEnabled(False)
                self.addWidget(button)
                self._buttons[spec.name] = button

    def set_color(self, color):
        self.setStyleSheet(make_icon_toolbar_ss(color))

    @Slot(str, str)
    def _update_spec_button_name(self, old_name, new_name):
        button = self._buttons.pop(old_name, None)
        if button is None:
            return
        self._buttons[new_name] = button
        button.spec_name = new_name


class MainToolBar(ToolBar):
    """The main application toolbar: Items | Execute"""

    _SEPARATOR = ";;"

    def __init__(self, execute_project_action, execute_selection_action, stop_execution_action, parent):
        """
        Args:
            execute_project_action (QAction): action to execute project
            execute_selection_action (QAction): action to execute selected items
            stop_execution_action (QAction): action to stop execution
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Main Toolbar", parent)  # Inherits stylesheet from ToolboxUI
        self._execute_project_action = execute_project_action
        self.execute_project_button = None
        self._execute_selection_action = execute_selection_action
        self.execute_selection_button = None
        self._stop_execution_action = stop_execution_action
        self.stop_execution_button = None
        self._buttons = []
        self._spec_arrays = []
        self._drop_source_action = None
        self._drop_target_action = None
        self.setAcceptDrops(True)

    def set_project_actions_enabled(self, enabled):
        super().set_project_actions_enabled(enabled)
        for arr in self._spec_arrays:
            arr.update()

    def set_color(self, color):
        self.setStyleSheet(make_icon_toolbar_ss(color))
        self.layout().setSpacing(1)
        for arr in self._spec_arrays:
            arr.set_color(color)

    def setup(self):
        self.add_project_item_buttons()
        self.add_execute_buttons()

    def add_project_item_buttons(self):
        self.addWidget(PaddingLabel("Items"))
        colored = self._toolbox.qsettings().value("appSettings/colorToolbarIcons", defaultValue="false") == "true"
        icon_ordering = self._toolbox.qsettings().value("appSettings/toolbarIconOrdering", defaultValue="")
        ordered_item_types = icon_ordering.split(self._SEPARATOR)
        for item_type in ordered_item_types:
            factory = self._toolbox.item_factories.get(item_type)
            if factory is None:
                continue
            self._add_project_item_button(item_type, factory, colored)
        for item_type, factory in self._toolbox.item_factories.items():
            if item_type in ordered_item_types:
                continue
            self._add_project_item_button(item_type, factory, colored)
        self._make_tool_button(
            QIcon(CharIconEngine("\uf067", color=Qt.darkGreen)),
            "From file...",
            self._toolbox.import_specification,
            tip="Add item specification from file...",
        )

    def _add_project_item_button(self, item_type, factory, colored):
        if factory.is_deprecated():
            return
        icon_file_type = factory.icon()
        icon_color = factory.icon_color().darker(120)
        icon = ColoredIcon(icon_file_type, icon_color, self.iconSize(), colored=colored)
        if not self._toolbox.supports_specification(item_type):
            button = ProjectItemButton(self._toolbox, item_type, icon)
            button.set_orientation(self.orientation())
            self.orientationChanged.connect(button.set_orientation)
            self.addWidget(button)
            self._buttons.append(button)
        else:
            model = self._toolbox.filtered_spec_factory_models.get(item_type)
            spec_array = ProjectItemSpecArray(self._toolbox, model, item_type, icon)
            spec_array.setOrientation(self.orientation())
            self._spec_arrays.append(spec_array)
            self.addWidget(spec_array)
            self.orientationChanged.connect(spec_array.setOrientation)

    def set_colored_icons(self, colored):
        for w in self._buttons + self._spec_arrays:
            w.set_colored_icons(colored)
        self.update()

    def _make_tool_button(self, icon, text, slot, tip=None):
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
        button.clicked.connect(slot)
        self._add_tool_button(button)
        return button

    def _add_tool_button(self, button):
        """Adds a button to the toolbar.

        Args:
            button (QToolButton): button to add
        """
        button.setStyleSheet("QToolButton{padding: 2px}")
        button.set_orientation(self.orientation())
        self.orientationChanged.connect(button.set_orientation)
        self.addWidget(button)

    def add_execute_buttons(self):
        """Adds project execution buttons to the toolbar."""
        self.addSeparator()
        self.addWidget(PaddingLabel("Execute"))
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
        if not isinstance(target, (ProjectItemButton, ProjectItemSpecArray)):
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
            if not isinstance(w, (ProjectItemButton, ProjectItemSpecArray)):
                continue
            item_types.append(w.item_type)
        return self._SEPARATOR.join(item_types)


class PaddingLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.font()
        font.setPointSize(8)
        self.setFont(font)
        self.setStyleSheet("QLabel{padding: 2px}")
