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
Functions to make and handle QToolBars.

:author: P. Savolainen (VTT)
:date:   19.1.2018
"""

from PySide2.QtCore import Slot, Qt
from PySide2.QtWidgets import QToolBar, QLabel, QToolButton
from PySide2.QtGui import QIcon, QPainter
from ..helpers import make_icon_toolbar_ss, ColoredIcon
from .project_item_drag import ProjectItemButton, ProjectItemSpecButton, ProjectItemSpecArray


class PluginToolBar(QToolBar):
    """A plugin toolbar."""

    def __init__(self, name, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__(name, parent=parent)  # Inherits stylesheet from ToolboxUI
        self._name = name
        self._toolbox = parent
        self.setObjectName(name.replace(" ", "_"))

    def setup(self, plugin_specs):
        self.addWidget(PaddingLabel(self._name))
        for spec in plugin_specs:
            factory = self._toolbox.item_factories[spec.item_type]
            icon = QIcon(factory.icon())
            button = ProjectItemSpecButton(self._toolbox, spec.item_type, icon, spec.name)
            button.setIconSize(self.iconSize())
            self.addWidget(button)

    def set_color(self, color):
        self.setStyleSheet(make_icon_toolbar_ss(color))


class MainToolBar(QToolBar):
    """The main application toolbar: Items | Execute"""

    _SEPARATOR = ";;"

    def __init__(self, parent):
        """

        Args:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__("Main Toolbar", parent=parent)  # Inherits stylesheet from ToolboxUI
        self._toolbox = parent
        self.setObjectName("Main_Toolbar")
        self.execute_project_button = None
        self.execute_selection_button = None
        self.stop_execution_button = None
        self._buttons = []
        self._spec_arrays = []
        self._drop_source_action = None
        self._drop_target_action = None
        self.setAcceptDrops(True)

    def set_color(self, color):
        self.setStyleSheet(make_icon_toolbar_ss(color))
        self.layout().setSpacing(1)
        for arr in self._spec_arrays:
            arr.set_color(color)

    def setup(self):
        self.add_project_item_buttons()
        self.add_execute_buttons()

    def add_project_item_buttons(self):
        self.addWidget(PaddingLabel("Main"))
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
        self._add_tool_button(
            QIcon(":/icons/wrench_plus.svg"), "Add specification from file...", self._toolbox.import_specification
        )

    def _add_project_item_button(self, item_type, factory, colored):
        icon_file_type = factory.icon()
        icon_color = factory.icon_color().darker(120)
        icon = ColoredIcon(icon_file_type, icon_color, self.iconSize(), colored=colored)
        if not self._toolbox.supports_specification(item_type):
            button = ProjectItemButton(self._toolbox, item_type, icon)
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

    def _add_tool_button(self, icon, tip, slot):
        button = QToolButton()
        button.setIcon(icon)
        button.setToolTip(f"<p>{tip}</p>")
        button.clicked.connect(slot)
        button.setStyleSheet("QToolButton{padding: 2px}")
        self.addWidget(button)
        return button

    def add_execute_buttons(self):
        self.addSeparator()
        self.addWidget(PaddingLabel("Execute"))
        self.execute_project_button = self._add_tool_button(
            QIcon(":/icons/menu_icons/play-circle-solid.svg"), "Execute project", self.execute_project
        )
        self.execute_selection_button = self._add_tool_button(
            QIcon(":/icons/menu_icons/play-circle-regular.svg"), "Execute selection", self.execute_selected
        )
        self.stop_execution_button = self._add_tool_button(
            QIcon(":/icons/menu_icons/stop-circle-regular.svg"), "Stop execution", self.stop_execution
        )
        self.execute_project_button.setEnabled(False)  # Will become enabled when user adds items
        self.execute_selection_button.setEnabled(False)  # Will become enabled when user selects something
        self.stop_execution_button.setEnabled(False)  # Will become enabled when user executes something

    @Slot(bool)
    def execute_project(self, checked=False):
        """Slot for handling the Execute project tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().execute_project()
        return

    @Slot(bool)
    def execute_selected(self, checked=False):
        """Slot for handling the Execute selected tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().execute_selected()
        return

    @Slot(bool)
    def stop_execution(self, checked=False):
        """Slot for handling the Stop execution tool button clicked signal."""
        if not self._toolbox.project():
            self._toolbox.msg.emit("Please create a new project or open an existing one first")
            return
        self._toolbox.project().stop()

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
        target = self.childAt(event.pos())
        if target is None:
            return
        while target.parent() != self:
            target = target.parent()
        if not isinstance(target, (ProjectItemButton, ProjectItemSpecArray)):
            return
        while source.parent() != self:
            source = source.parent()
        if self.orientation() == Qt.Horizontal:
            after = target.geometry().center().x() < event.pos().x()
        else:
            after = target.geometry().center().y() < event.pos().y()
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
        painter.drawLine(*self._drop_line())
        painter.end()

    def _drop_line(self):
        widget = self.widgetForAction(self._drop_target_action)
        geom = widget.geometry()
        margin = self.layout().margin()
        if self.orientation() == Qt.Horizontal:
            x = geom.left() - 1
            return x, margin, x, self.height() - margin
        y = geom.top() - 1
        return margin, y, self.width() - margin, y

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
        self.setStyleSheet("QLabel{padding: 2px}")
