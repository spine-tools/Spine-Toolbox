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
import stat
import shutil
from collections.abc import Callable, Iterable
from typing import Generic, TypeVar
from PySide6.QtCore import QPersistentModelIndex, Slot, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QWidgetAction, QApplication, QMessageBox, QWidget
from spinetoolbox.kernel_fetcher import KernelFetcher
from spinetoolbox.helpers import restore_override_cursor
from spinetoolbox.config import LATEST_PROJECT_VERSION
from spinetoolbox.helpers import clear_recent_projects, remove_path_from_recent_projects, open_url
from spinetoolbox.load_project import ProjectLoadingFailed, load_project_dict
from spinetoolbox.mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel
from spinetoolbox.widgets.custom_qwidgets import FilterWidget
from spinetoolbox.widgets.notification import Notification
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
                    text = "Default Julia environment (@v1.x)"
                elif project_path == "@.":
                    text = "Current project environment (@.)"
                else:
                    text = project_path
                action = submenu.addAction(QIcon(":/icons/folder.svg"), text)
                action.triggered.connect(
                    lambda checked=False, exe=julia_exe, path=project_path: self.open_julia_console(checked, exe, path)
                )

    @Slot(bool, str, str)
    def open_julia_console(self, checked, julia_exe, julia_project):
        self._parent.start_detached_julia_basic_console(julia_exe, julia_project)


class SharedContextMenu(QMenu):
    """Superclass for Python and Julia context menus."""

    def __init__(self, menu_parent, owner_widget, models, path, is_conda):
        super().__init__(menu_parent)
        self._owner_widget = owner_widget
        self._models = models
        self._path = path
        self._is_conda = is_conda

    def _open_kernel_resource_dir(self):
        """Opens kernel's resource folder in File Explorer."""
        if not self._path:
            Notification(self._owner_widget, "Please select a Jupyter kernel").show()
        else:
            self._open_resource_dir(self._path)

    def _open_resource_dir(self, path):
        """Opens given path in file browser."""
        if not os.path.exists(path):
            Notification(self._owner_widget, f"Path '{path}' does not exist").show()
            return
        url = "file:///" + path
        res = open_url(url)
        if not res:
            Notification(self._owner_widget, f"Opening directory '{path}' failed").show()
            return

    def _open_kernel_json_file(self):
        """Opens kernel.json file in a text editor from the kernel's resource folder."""
        if not self._path:
            Notification(self._owner_widget, "Please select a Jupyter kernel").show()
        else:
            kernel_json_path = os.path.join(self._path, "kernel.json")
            if not os.path.exists(kernel_json_path):
                Notification(self._owner_widget, f"Could not find kernel.json file in '{self._path}'").show()
                return
            url = "file:///" + kernel_json_path
            res = open_url(url)
            if not res:
                Notification(self._owner_widget, f"Opening file '{kernel_json_path}' failed").show()
                return

    def _remove_kernel_resource_directory(self) -> bool:
        """Asks confirmation and removes a kernel resource dir from the system. Effectively does the same thing as
        'jupyter kernelspec remove -f <kernel-name>'"""
        if not self._path or not os.path.exists(self._path):
            Notification(self._owner_widget, f"Please select a Jupyter kernel").show()
            return False
        if self._is_conda:
            Notification(
                self._owner_widget,
                "This is a dynamically created Conda Jupyter kernel and cannot be removed from Spine Toolbox.",
            ).show()
            return False
        _, kernel_name = os.path.split(self._path)
        message_box = QMessageBox(
            QMessageBox.Icon.Warning,
            f"Remove kernel {kernel_name}?",
            f"Kernel {kernel_name} will be removed. This operation is effectively the same as running "
            f"'jupyter kernelspec remove -f {kernel_name}' in a terminal. Are you sure?",
            parent=self._owner_widget,
        )
        yes_button = message_box.addButton("Remove kernel", QMessageBox.ButtonRole.YesRole)
        cancel_button = message_box.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        message_box.setDefaultButton(cancel_button)
        message_box.exec_()
        if message_box.clickedButton() is yes_button:

            def remove_readonly(func, path, excinfo):
                os.chmod(path, stat.S_IWRITE)
                func(path)

            try:
                shutil.rmtree(self._path, onerror=remove_readonly)  # Julia kernel spec files may be read-only
            except OSError as e:
                Notification(self._owner_widget, f"Removing kernel failed: {e}").show()
                return False
            return True
        return False


class PythonContextMenu(SharedContextMenu):
    """Provides a context menu for the Python interpreters and Python kernels comboBoxes and their list views."""

    def __init__(self, menu_parent, owner_widget, models, path, is_conda, menu_mode):
        super().__init__(menu_parent, owner_widget, models, path, is_conda)
        if menu_mode == 0:
            self._make_interpreter_menu()
        elif menu_mode == 1:
            self._make_kernel_menu()

    def _make_interpreter_menu(self):
        """Adds actions for python interpreter comboBox context menu."""
        self.addAction(
            QIcon(":icons/menu_icons/trash-alt.svg"),
            "Remove from list",
            self._remove_python_system_interpreter,
        )
        self.addAction(
            QIcon(":icons/menu_icons/folder-open-solid.svg"),
            "Open containing folder...",
            self._open_python_interpreter_dir,
        )

    def _make_kernel_menu(self):
        """Adds actions for a Python kernel comboBox context menu."""
        self.addAction(
            QIcon(":icons/menu_icons/folder-open-solid.svg"),
            "Open resource folder...",
            self._open_kernel_resource_dir,
        )
        self.addAction(
            QIcon(":icons/menu_icons/edit.svg"),
            "Open kernel.json...",
            self._open_kernel_json_file,
        )
        self.addAction(
            QIcon(":icons/menu_icons/trash-alt.svg"),
            "Remove kernel...",
            self._delete_python_kernel_resource_dir,
        )
        self.addAction(
            QIcon(":icons/menu_icons/sync.svg"),
            "Reload kernels",
            self._reload_python_kernels,
        )

    def _remove_python_system_interpreter(self):
        """Removes Python interpreter from the list of known Pythons."""
        if not self._path:
            Notification(
                self._owner_widget, "This is the current Spine Toolbox interpreter and cannot be removed"
            ).show()
        else:
            self._models.remove_python_interpreter(self._path)

    def _open_python_interpreter_dir(self):
        """Opens Python interpreter folder in File Explorer."""
        path, _ = os.path.split(resolve_current_python_interpreter()) if self._path == "" else os.path.split(self._path)
        self._open_resource_dir(path)

    def _delete_python_kernel_resource_dir(self):
        if self._remove_kernel_resource_directory():
            self._reload_python_kernels()

    def _reload_python_kernels(self):
        Notification(self._owner_widget, "Reloading Python kernels").show()
        self._owner_widget.reload_python_kernels()


class JuliaContextMenu(SharedContextMenu):
    """Provides a context menu for the Julia executable, Julia Project,
    and Julia kernel comboBoxes and their list views."""

    def __init__(self, menu_parent, owner_widget, models, path, is_conda, menu_mode, current_julia_dir):
        super().__init__(menu_parent, owner_widget, models, path, is_conda)
        self._current_julia_dir = current_julia_dir
        if menu_mode == 0:
            self._make_executable_menu()
        elif menu_mode == 1:
            self._make_projects_menu()
        elif menu_mode == 2:
            self._make_kernels_menu()

    def _make_executable_menu(self):
        self.addAction(QIcon(":icons/menu_icons/trash-alt.svg"), "Remove from list", self._remove_julia_executable)
        self.addAction(
            QIcon(":icons/menu_icons/folder-open-solid.svg"),
            "Open containing folder...",
            self._open_julia_executable_dir,
        )

    def _make_projects_menu(self):
        self.addAction(QIcon(":icons/menu_icons/trash-alt.svg"), "Remove from list", self._remove_julia_project)
        self.addAction(QIcon(":icons/menu_icons/folder-open-solid.svg"), "Open folder...", self._open_julia_project_dir)

    def _make_kernels_menu(self):
        self.addAction(
            QIcon(":icons/menu_icons/folder-open-solid.svg"), "Open resource folder...", self._open_kernel_resource_dir
        )
        self.addAction(QIcon(":icons/menu_icons/edit.svg"), "Open kernel.json...", self._open_kernel_json_file)
        self.addAction(
            QIcon(":icons/menu_icons/trash-alt.svg"), "Remove kernel...", self._delete_julia_kernel_resource_dir
        )
        self.addAction(QIcon(":icons/menu_icons/sync.svg"), "Reload kernels", self._owner_widget.reload_julia_kernels)

    def _remove_julia_executable(self):
        """Removes a Julia from the list of known Julias."""
        if not self._path:
            Notification(self._owner_widget, "This is the Julia in PATH and cannot be removed").show()
            return
        else:
            self._models.remove_julia_executable(self._path)

    def _open_julia_executable_dir(self):
        """Opens Julia executable folder in File Explorer."""
        path, _ = os.path.split(resolve_default_julia_executable()) if self._path == "" else os.path.split(self._path)
        self._open_resource_dir(path)

    def _remove_julia_project(self):
        """Removes a Julia environment/project from known environments."""
        if self._path == "@." or self._path == "":
            Notification(self._owner_widget, "This is a default environment and cannot be removed.").show()
            return
        else:
            self._models.remove_julia_project(self._path)

    def _open_julia_project_dir(self):
        if self._path == "@." or self._path == "":
            path = self._current_julia_dir
        else:
            path = self._path
        self._open_resource_dir(path)

    def _delete_julia_kernel_resource_dir(self):
        if self._remove_kernel_resource_directory():
            self._reload_julia_kernels()

    def _reload_julia_kernels(self):
        Notification(self._owner_widget, "Reloading Julia kernels").show()
        self._owner_widget.reload_julia_kernels()


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
