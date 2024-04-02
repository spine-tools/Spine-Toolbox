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

"""Classes for custom context menus and pop-up menus."""
import os
from PySide6.QtWidgets import QMenu, QWidgetAction
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Slot, QPersistentModelIndex
from spinetoolbox.widgets.custom_qwidgets import FilterWidget


class CustomContextMenu(QMenu):
    """Context menu master class for several context menus."""

    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.position = position
        self.option = "None"

    def add_action(self, text, icon=QIcon(), enabled=True):
        """Adds an action to the context menu.

        Args:
            text (str): Text description of the action
            icon (QIcon): Icon for menu item
            enabled (bool): Is action enabled?
        """
        action = self.addAction(icon, text)
        action.setEnabled(enabled)
        action.triggered.connect(lambda: self.set_action(text))

    def set_action(self, option):
        """Sets the action which was clicked.

        Args:
            option (str): string with the text description of the action
        """
        self.option = option

    def get_action(self):
        """Returns the clicked action, a string with a description."""
        self.exec(self.position)
        return self.option


class OpenProjectDialogComboBoxContextMenu(CustomContextMenu):
    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.add_action("Clear history")


class CustomPopupMenu(QMenu):
    """Popup menu master class for several popup menus."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget of this pop-up menu
        """
        super().__init__(parent=parent)
        self._parent = parent

    def add_action(self, text, slot, enabled=True, tooltip=None, icon=None):
        """Adds an action to the popup menu.

        Args:
            text (str): Text description of the action
            slot (method): Method to connect to action's triggered signal
            enabled (bool): Is action enabled?
            tooltip (str): Tool tip for the action
            icon (QIcon): Action icon
        """
        if icon is not None:
            action = self.addAction(icon, text, slot)
        else:
            action = self.addAction(text, slot)
        action.setEnabled(enabled)
        if tooltip is not None:
            action.setToolTip(tooltip)


class ItemSpecificationMenu(CustomPopupMenu):
    """Context menu class for item specifications."""

    def __init__(self, toolbox, index, item=None):
        """
        Args:
            toolbox (ToolboxUI): Toolbox that requests this menu, used as parent.
            index (QModelIndex): the index
            item (ProjectItem, optional): passed to show_specification_form
        """
        super().__init__(toolbox)
        self._toolbox = toolbox
        self.index = QPersistentModelIndex(index)
        self.add_action("Edit specification", lambda item=item: toolbox.edit_specification(self.index, item))
        self.add_action("Remove specification", lambda: toolbox.remove_specification(self.index))
        self.add_action("Open specification file...", lambda: toolbox.open_specification_file(self.index))


class RecentProjectsPopupMenu(CustomPopupMenu):
    """Recent projects menu embedded to 'File-Open recent' QAction."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget of this menu (ToolboxUI)
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.setToolTipsVisible(True)
        self.add_recent_projects()
        self.addSeparator()
        self.add_action(
            "Clear",
            lambda checked=False: self.call_clear_recents(checked),
            enabled=self.has_recents(),
            icon=QIcon(":icons/trash-alt.svg"),
        )

    def has_recents(self):
        """Returns True if recent projects available, False otherwise."""
        return bool(self._parent.qsettings().value("appSettings/recentProjects", defaultValue=None))

    def add_recent_projects(self):
        """Reads the previous project names and paths from QSettings. Adds them to the QMenu as QActions."""
        recents = self._parent.qsettings().value("appSettings/recentProjects", defaultValue=None)
        if recents:
            recents = str(recents)
            recents_list = recents.split("\n")
            for entry in recents_list:
                name, filepath = entry.split("<>")
                self.add_action(
                    name,
                    lambda checked=False, filepath=filepath: self.call_open_project(checked, filepath),
                    tooltip=filepath,
                )

    @Slot(bool)
    def call_clear_recents(self, checked):
        """Slot for Clear recents menu item.

        Args:
            checked (bool): Argument sent by triggered signal
        """

        self._parent.clear_recent_projects()

    @Slot(bool, str)
    def call_open_project(self, checked, p):
        """Slot for catching the user selected action from the recent projects menu.

        Args:
            checked (bool): Argument sent by triggered signal
            p (str): Full path to a project file
        """
        if not os.path.exists(p):
            # Project has been removed, remove it from recent projects list
            self._parent.remove_path_from_recent_projects(p)
            self._parent.msg_error.emit(
                "Opening selected project failed. Project file <b>{0}</b> may have been removed.".format(p)
            )
            return
        # Check if the same project is already open
        if self._parent.project():
            if p == self._parent.project().project_dir:
                self._parent.msg.emit("Project already open")
                return
        if not self._parent.open_project(p):
            return


class KernelsPopupMenu(CustomPopupMenu):
    """Menu embedded into 'Consoles->Start Jupyter Console' QMenu."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget of this menu (ToolboxUI)
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.setToolTipsVisible(True)

    @Slot(str, str, bool, QIcon, dict)
    def add_kernel(self, kernel_name, resource_dir, cond, ico, deats):
        """Adds a kernel entry as an action to this menu."""
        self.add_action(
            kernel_name,
            lambda checked=False, kname=kernel_name, icon=ico, conda=cond: self.call_open_console(
                checked, kname, icon, conda
            ),
            tooltip=resource_dir,
            icon=ico,
        )

    @Slot(bool, str, QIcon, bool)
    def call_open_console(self, checked, kernel_name, icon, conda):
        """Slot for catching the user selected action from the kernel's menu.

        Args:
            checked (bool): Argument sent by triggered signal
            kernel_name (str): Kernel name to launch
            icon (QIcon): Icon representing the kernel language
            conda (bool): Is this a Conda kernel spec?
        """
        self._parent.start_detached_jupyter_console(kernel_name, icon, conda)


class FilterMenuBase(QMenu):
    """Filter menu."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): a parent widget
        """
        super().__init__(parent)
        self._filter = None
        self._remove_filter = QAction("Remove filters", None)
        self._filter_action = QWidgetAction(self)
        self.addAction(self._remove_filter)

    def _set_up(self, make_filter_model, *args, **kwargs):
        self._filter = FilterWidget(self, make_filter_model, *args, **kwargs)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.connect_signals()

    def connect_signals(self):
        self.aboutToShow.connect(self._check_filter)
        self._remove_filter.triggered.connect(self._clear_filter)
        self._filter.okPressed.connect(self._change_filter)
        self._filter.cancelPressed.connect(self.hide)

    def add_items_to_filter_list(self, items):
        self._filter._filter_model.add_items(items)
        self._filter.save_state()

    def remove_items_from_filter_list(self, items):
        self._filter._filter_model.remove_items(items)
        self._filter.save_state()

    def _clear_filter(self):
        self._filter.clear_filter()
        self._change_filter()

    def _check_filter(self):
        self._remove_filter.setEnabled(self._filter.has_filter())

    def _change_filter(self):
        valid_values = set(self._filter._filter_state)
        if self._filter._filter_empty_state:
            valid_values.add(None)
        self.emit_filter_changed(valid_values)
        self.hide()

    def emit_filter_changed(self, valid_values):
        raise NotImplementedError()
