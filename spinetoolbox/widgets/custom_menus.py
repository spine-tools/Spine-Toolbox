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

from collections.abc import Callable, Iterable
import os
from typing import Generic, TypeVar
from PySide6.QtCore import QPersistentModelIndex, Slot, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QWidgetAction, QApplication, QMessageBox, QWidget
from spinetoolbox.kernel_fetcher import KernelFetcher
from spinetoolbox.helpers import restore_override_cursor
from spinetoolbox.config import LATEST_PROJECT_VERSION
from spinetoolbox.helpers import clear_recent_projects, remove_path_from_recent_projects
from spinetoolbox.load_project import ProjectLoadingFailed, load_project_dict
from spinetoolbox.mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel
from spinetoolbox.widgets.custom_qwidgets import FilterWidget
from spine_engine.utils.helpers import resolve_current_python_interpreter, resolve_default_julia_executable


class CustomPopupMenu(QMenu):
    """Popup menu master class for several popup menus."""

    def __init__(self, parent: QWidget):
        """
        Args:
            parent: Parent widget of this pop-up menu
        """
        super().__init__(parent=parent)
        self._parent = parent

    def add_action(
        self,
        text: str,
        slot: Callable[[], None],
        enabled: bool = True,
        tooltip: str | None = None,
        icon: QIcon | None = None,
    ) -> QAction:
        """Adds an action to the popup menu.

        Args:
            text: Text description of the action
            slot: Method to connect to action's triggered signal
            enabled: Is action enabled?
            tooltip: Tool tip for the action
            icon: Action icon

        Returns:
            The added action.
        """
        if icon is not None:
            action = self.addAction(icon, text, slot)
        else:
            action = self.addAction(text, slot)
        action.setEnabled(enabled)
        if tooltip is not None:
            action.setToolTip(tooltip)
        return action


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
        self.add_action("Edit specification", lambda it=item: toolbox.edit_specification(self.index, it))
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
            icon=QIcon(":icons/menu_icons/trash-alt.svg"),
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
                version = None
                if os.path.isdir(filepath):
                    try:
                        project_dict = load_project_dict(filepath)
                    except ProjectLoadingFailed:
                        continue
                    version = project_dict.get("project", {}).get("version")
                if version is None:
                    tt = filepath
                else:
                    version = int(version)
                    if version == LATEST_PROJECT_VERSION:
                        tt = f"{filepath}\nProject version: {version} (current)"
                    elif version < LATEST_PROJECT_VERSION:
                        tt = (
                            f"{filepath}\nProject version: {version} (upgrades "
                            f"to {LATEST_PROJECT_VERSION} when opened)"
                        )
                    else:
                        name = f"[Incompatible] " + name
                        tt = (
                            f"{filepath}\nProject version: {version} "
                            f"(requires newer Spine Toolbox, current support: {LATEST_PROJECT_VERSION})"
                        )
                self.add_action(
                    name,
                    lambda checked=False, filepath=filepath, version=version: self.call_open_project(
                        checked, filepath, version
                    ),
                    tooltip=tt,
                )

    @Slot(bool)
    def call_clear_recents(self, _=True):
        """Slot for Clear recents menu item.

        Args:
            _ (bool): Argument sent by triggered signal
        """
        clear_recent_projects(self._parent, self._parent.qsettings())

    @Slot(bool, str, object)
    def call_open_project(self, _, p, version):
        """Slot for catching the user selected action from the recent projects menu.

        Args:
            _ (bool): Argument sent by triggered signal
            p (str): Full path to a project directory
            version (int | None): Project version
        """
        if not os.path.exists(p):
            # Project has been removed, remove it from recent projects list
            remove_path_from_recent_projects(self._parent.qsettings(), p)
            self._parent.msg_error.emit(f"Opening selected project failed. Project <b>{p}</b> may have been removed.")
            return
        if not version:
            QMessageBox.warning(
                self,
                "Project corrupted",
                f"Project '{p}' may be corrupted because 'version' key is missing from the project.json file.\n",
            )
            return
        if version > LATEST_PROJECT_VERSION:
            QMessageBox.warning(
                self,
                "Incompatible project",
                f"Project '{p}' is version {version} and requires a newer Spine Toolbox.\n"
                f"This version of Spine Toolbox supports projects up to version {LATEST_PROJECT_VERSION}.",
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
        self.kernel_fetcher = None

    @Slot()
    def fetch_kernels(self):
        """Starts a thread for fetching local kernels."""
        if self.kernel_fetcher is not None and self.kernel_fetcher.isRunning():
            return
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self.clear()
        conda_path = self._parent.qsettings().value("appSettings/condaPath", defaultValue="")
        self.kernel_fetcher = KernelFetcher(conda_path)
        self.kernel_fetcher.kernel_found.connect(self.add_kernel)
        self.kernel_fetcher.finished.connect(restore_override_cursor)
        self.kernel_fetcher.start()

    @Slot()
    def stop_fetching_kernels(self):
        """Terminates kernel fetcher thread."""
        if self.kernel_fetcher is not None:
            self.kernel_fetcher.stop_fetcher.emit()

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


class PythonPopupMenu(CustomPopupMenu):
    """Menu for showing Python interpreters in Consoles -> Start Python."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.setToolTipsVisible(True)
        self._model = self._parent.exec_compound_models.python_interpreters_model

    @Slot()
    def populate_menu(self):
        self.clear()
        self._parent.exec_compound_models.refresh_python_interpreters_model()
        for r in range(self._model.rowCount()):
            item_data = self._model.itemFromIndex(self._model.index(r, 0)).data()
            path = item_data["exe"]
            if not item_data["exe"]:
                path = resolve_current_python_interpreter()
            action = self.addAction(QIcon(":/symbols/python-logo.svg"), path)
            action.triggered.connect(lambda checked=False, exe=path: self.open_python_console(checked, exe))

    @Slot(bool, str)
    def open_python_console(self, checked, python_path):
        self._parent.start_detached_python_basic_console(python_path)


class JuliaPopupMenu(CustomPopupMenu):
    """Menu for showing Julia executables and projects in Consoles -> Start Julia."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.setToolTipsVisible(True)
        self._julia_model = self._parent.exec_compound_models.julia_executables_model
        self._project_model = self._parent.exec_compound_models.julia_projects_model

    @Slot()
    def populate_menu(self):
        self.clear()
        self._parent.exec_compound_models.refresh_julia_executables_model()
        self._parent.exec_compound_models.refresh_julia_projects_model()
        for julia_row in range(self._julia_model.rowCount()):
            julia_item_data = self._julia_model.itemFromIndex(self._julia_model.index(julia_row, 0)).data()
            if not julia_item_data:
                action = self.addAction("No Julia's available. Add Julia executable(s) in Settings->Tools")
                return
            julia_exe = julia_item_data.get("exe", "")
            if not julia_exe:
                julia_exe = resolve_default_julia_executable()
            submenu = self.addMenu(QIcon(":/symbols/julia-logo.svg"), julia_exe)
            for project_row in range(self._project_model.rowCount()):
                project_item_data = self._project_model.itemFromIndex(self._project_model.index(project_row, 0)).data()
                project_path = project_item_data["path"]
                if not project_path:
                    text = "Home"
                else:
                    text = project_path
                action = submenu.addAction(QIcon(":/icons/folder.svg"), text)
                action.triggered.connect(
                    lambda checked=False, exe=julia_exe, path=project_path: self.open_julia_console(checked, exe, path)
                )

    @Slot(bool, str, str)
    def open_julia_console(self, checked, julia_exe, julia_project):
        self._parent.start_detached_julia_basic_console(julia_exe, julia_project)


T = TypeVar("T")


class FilterMenuBase(Generic[T], QMenu):
    """Filter menu."""

    def __init__(self, parent: QWidget | None):
        """
        Args:
            parent: a parent widget
        """
        super().__init__(parent)
        self.filter: FilterWidget | None = None
        self._remove_filter = QAction("Remove filters", None)
        self._filter_action = QWidgetAction(self)
        self.addAction(self._remove_filter)

    def _set_up(self, filter_model: SimpleFilterCheckboxListModel[T]) -> None:
        self.filter = FilterWidget(self, filter_model)
        self._filter_action.setDefaultWidget(self.filter)
        self.addAction(self._filter_action)
        self.connect_signals()

    def connect_signals(self) -> None:
        self.aboutToShow.connect(self._check_filter)
        self._remove_filter.triggered.connect(self.clear_filter)
        self.filter.okPressed.connect(self._change_filter)
        self.filter.cancelPressed.connect(self.hide)

    def add_items_to_filter_list(self, items: Iterable[T]) -> None:
        self.filter.model().add_items(items)
        self.filter.save_state()

    def remove_items_from_filter_list(self, items: set[T]) -> None:
        self.filter.model().remove_items(items)
        self.filter.save_state()

    @Slot()
    def clear_filter(self) -> None:
        self.filter.clear_filter()
        self._change_filter()

    @Slot()
    def _check_filter(self) -> None:
        self._remove_filter.setEnabled(self.filter.has_filter())

    @Slot()
    def _change_filter(self) -> None:
        valid_values = set(self.filter.filter_state)
        if self.filter.filter_empty_state:
            valid_values.add(None)
        self.emit_filter_changed(valid_values)
        self.hide()

    def emit_filter_changed(self, valid_values: set[T]) -> None:
        raise NotImplementedError()
