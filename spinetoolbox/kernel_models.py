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

"""Contains a class for storing saved Python and Julia executables in a model."""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import QObject, Qt, Slot, QModelIndex
from .kernel_fetcher import KernelFetcher
from .helpers import (
    save_path_to_qsettings,
    remove_path_from_qsettings,
    load_list_of_paths_from_qsettings,
    restore_override_cursor,
)
from widgets.notification import Notification
from spine_engine.utils.helpers import resolve_default_julia_executable, resolve_current_python_interpreter


class ExecutableCompoundModels(QObject):
    """Class for storing Python's and Julia's."""

    def __init__(self, qsettings):
        super().__init__()
        self._qsettings = qsettings
        self._julia_executables_model = QStandardItemModel(self)
        self._julia_projects_model = QStandardItemModel(self)
        self._julia_kernel_model = QStandardItemModel(self)
        self._python_interpreters_model = QStandardItemModel(self)
        self._python_kernel_model = QStandardItemModel(self)
        self.julia_kernel_fetcher = None
        self.python_kernel_fetcher = None

    @property
    def julia_executables_model(self):
        return self._julia_executables_model

    @property
    def julia_projects_model(self):
        return self._julia_projects_model

    @property
    def julia_kernel_model(self):
        return self._julia_kernel_model

    @property
    def python_interpreters_model(self):
        return self._python_interpreters_model

    @property
    def python_kernel_model(self):
        return self._python_kernel_model

    def refresh_julia_executables_model(self, julia_executables=None, show_select_item=False):
        """Clears and populates the Julia executable model with the given list of Julia executable paths."""
        self.julia_executables_model.clear()
        if not julia_executables:
            julia_executables = load_list_of_paths_from_qsettings(self._qsettings, "appSettings/juliaExecutables")
        self.load_julia_executables(julia_executables, show_select_item)

    def refresh_julia_projects_model(self, julia_projects=None, show_select_item=False):
        """Clears and populates the Julia projects model with the given list of Julia project paths."""
        self.julia_projects_model.clear()
        if not julia_projects:
            julia_projects = load_list_of_paths_from_qsettings(self._qsettings, "appSettings/juliaProjects")
        self.load_julia_projects(julia_projects, show_select_item)

    def load_julia_executables(self, julia_executables, show_select_item=False):
        """Adds Julia executables to a model.

        Args:
            julia_executables (list): Julia executable paths in a list
            show_select_item (bool): If True, adds a 'Select Julia executable...' item as the first item
        """
        if show_select_item:
            select_item = QStandardItem("Select Julia executable...")
            self._julia_executables_model.appendRow(select_item)
        current = resolve_default_julia_executable()
        if current:
            first_item = QStandardItem(current)
            first_item.setData({"is_jupyter": False, "is_conda": False, "exe": ""})
            first_item.setIcon(QIcon(":/symbols/julia-logo.svg"))
            first_item.setToolTip(f"This is the Julia from Path ({current})")
            self._julia_executables_model.appendRow(first_item)
        for path in julia_executables:
            item = QStandardItem(path)
            item.setData({"is_jupyter": False, "is_conda": False, "exe": path})
            item.setIcon(QIcon(":/symbols/julia-logo.svg"))
            item.setToolTip(path)
            self._julia_executables_model.appendRow(item)
        if self._julia_executables_model.rowCount() == 0:
            item = QStandardItem("Add path to Julia Executable...")
            item.setToolTip("Add Julia into your Path environment variable or by using the add "
                            "Julia button next to this combo box.")
            self._julia_executables_model.appendRow(item)

    def add_julia_executable(self, path_to_add, notification_parent):
        """Adds given path to the model and returns the index of the new item in the model."""
        key = "appSettings/juliaExecutables"
        updated_julia_executables = save_path_to_qsettings(self._qsettings, key, path_to_add)
        self.refresh_julia_executables_model(updated_julia_executables)
        return self.find_julia_executable_index(path_to_add, notification_parent)

    def remove_julia_executable(self, path_to_remove):
        """Removes given path from the model."""
        key = "appSettings/juliaExecutables"
        updated_julia_exes = remove_path_from_qsettings(self._qsettings, key, path_to_remove)
        self.refresh_julia_executables_model(updated_julia_exes)

    def find_julia_executable_index(self, path, notification_parent=None):
        """Returns the index of the given Julia executable.

        Args:
            path (str): Path to Julia executable
            notification_parent (QWidget): Parent widget for an error notification
        """
        for row in range(self.julia_executables_model.rowCount()):
            item = self.julia_executables_model.item(row, 0)
            if not item.data():  # The model only contains the 'No Julias found' item
                return self.julia_executables_model.index(0, 0)
            if item.data()["exe"] == path:
                return item.index()
        # TODO: Fix when path == "" and model is empty
        if notification_parent is not None:
            Notification(notification_parent, f"Could not find Julia {path}.\nActivating the default Julia.").show()
        return self.julia_executables_model.index(0, 0)

    def load_julia_projects(self, julia_projects, show_select_item=False):
        """Adds Julia projects to a model.

        Args:
            julia_projects (list): Julia project directory paths in a list
            show_select_item (bool): If True, adds a 'Select Julia project...' item as the first item
        """
        if show_select_item:
            select_item = QStandardItem("Select Julia project...")
            self._julia_projects_model.appendRow(select_item)
        first_item = QStandardItem("Home")
        first_item.setData({"is_project": True, "path": ""})
        first_item.setIcon(QIcon(":/icons/folder.svg"))
        first_item.setToolTip(f"This is the Julia Base project")
        second_item = QStandardItem("@.")
        second_item.setData({"is_project": True, "path": "@."})
        second_item.setIcon(QIcon(":/icons/folder.svg"))
        second_item.setToolTip(f"This is the Julia @. project")
        self._julia_projects_model.appendRow(first_item)
        self._julia_projects_model.appendRow(second_item)
        for path in julia_projects:
            item = QStandardItem(path)
            item.setData({"is_project": True, "path": path})
            item.setIcon(QIcon(":/icons/folder.svg"))
            item.setToolTip(path)
            self._julia_projects_model.appendRow(item)

    def add_julia_project(self, path_to_add, notification_parent):
        """Adds given path to the model and returns the index of the new item in the model."""
        key = "appSettings/juliaProjects"
        updated_julia_projects = save_path_to_qsettings(self._qsettings, key, path_to_add)
        self.refresh_julia_projects_model(updated_julia_projects)
        return self.find_julia_project_index(path_to_add, notification_parent)

    def remove_julia_project(self, path_to_remove):
        """Removes given path from the model."""
        key = "appSettings/juliaProjects"
        updated_julia_projects = remove_path_from_qsettings(self._qsettings, key, path_to_remove)
        self.refresh_julia_projects_model(updated_julia_projects)

    def find_julia_project_index(self, path, notification_parent=None):
        """Returns the index of the given Julia project.

        Args:
            path (str): Path to Julia project directory
            notification_parent (QWidget): Parent widget for an error notification
        """
        for row in range(self.julia_projects_model.rowCount()):
            item = self.julia_projects_model.item(row, 0)
            if item.data()["path"] == path:
                return item.index()
        if notification_parent is not None:
            Notification(notification_parent, f"Could not find Julia project {path}.\nActivating the default project.").show()
        return self.julia_projects_model.index(0, 0)

    def start_fetching_julia_kernels(self, finalize_slot=None, conda=""):
        """Starts a thread for fetching Julia kernels."""
        if self.julia_kernel_fetcher is not None and self.julia_kernel_fetcher.isRunning():
            # Trying to start a new thread when the old one is still running
            return
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self.julia_kernel_model.clear()
        first_item = QStandardItem("Select Jupyter kernel...")
        self.julia_kernel_model.appendRow(first_item)
        if not conda:
            conda = self._qsettings.value("appSettings/condaPath", defaultValue="")
        self.julia_kernel_fetcher = KernelFetcher(conda, fetch_mode=4)
        self.julia_kernel_fetcher.kernel_found.connect(self.add_julia_kernel)
        if finalize_slot is not None:
            self.julia_kernel_fetcher.finished.connect(finalize_slot)
        self.julia_kernel_fetcher.finished.connect(restore_override_cursor)
        self.julia_kernel_fetcher.finished.connect(self._delete_julia_kernel_fetcher)
        self.julia_kernel_fetcher.start()

    @Slot()
    def _delete_julia_kernel_fetcher(self):
        """Clears Julia kernel fetcher."""
        self.julia_kernel_fetcher.deleteLater()
        self.julia_kernel_fetcher = None

    @Slot()
    def stop_fetching_julia_kernels(self):
        """Terminates the kernel fetcher thread."""
        if self.julia_kernel_fetcher is not None:
            self.julia_kernel_fetcher.stop_fetcher.emit()

    @Slot(str, str, bool, QIcon, dict)
    def add_julia_kernel(self, kernel_name, resource_dir, conda, icon, deats):
        """Adds a kernel entry as an item to Julia kernels comboBox."""
        if self.julia_kernel_fetcher is not None and not self.julia_kernel_fetcher.keep_going:
            # Settings widget closed while thread still running
            return
        item = QStandardItem(kernel_name)
        item.setIcon(icon)
        item.setToolTip(resource_dir)
        deats["is_jupyter"] = True
        deats["is_conda"] = conda
        item.setData(deats)
        self.julia_kernel_model.appendRow(item)

    def find_julia_kernel_index(self, kname, notification_parent=None):
        """Finds and returns the index of given kernel name item."""
        if not kname:
            return self.julia_kernel_model.index(0, 0)
        items = self.julia_kernel_model.findItems(kname, Qt.MatchFlag.MatchExactly)
        if not items and notification_parent is not None:
            Notification(
                notification_parent,
                f"Could not activate Julia kernel {kname}.\nIt may have been removed."
            ).show()
            return self.julia_kernel_model.index(0, 0)
        return items[0].index()

    def refresh_python_interpreters_model(self, python_interpreters=None, show_select_item=False):
        """Clears and populates the Python interpreters model with the given list of Python interpreter paths."""
        self.python_interpreters_model.clear()
        if not python_interpreters:
            python_interpreters = load_list_of_paths_from_qsettings(self._qsettings, "appSettings/pythonInterpreters")
        self.load_python_system_interpreters(python_interpreters, show_select_item)

    def load_python_system_interpreters(self, python_interpreters, show_select_item=False):
        """Adds Python system interpreters to the Python model.

        Args:
            python_interpreters (list): Python interpreter paths in a list
            show_select_item (bool): If True, adds a 'Select Python interpreter...' item as the first item
        """
        if show_select_item:
            select_item = QStandardItem("Select Python interpreter...")
            self._python_interpreters_model.appendRow(select_item)
        current = resolve_current_python_interpreter()
        first_item = QStandardItem(current)
        first_item.setData({"is_jupyter": False, "is_conda": False, "exe": ""})
        first_item.setIcon(QIcon(":/symbols/app.ico"))
        first_item.setToolTip("This is the current Python Interpreter")
        self._python_interpreters_model.appendRow(first_item)
        for path in python_interpreters:
            item = QStandardItem(path)
            item.setData({"is_jupyter": False, "is_conda": False, "exe": path})
            item.setIcon(QIcon(":/symbols/python-logo.svg"))
            item.setToolTip(path)
            self._python_interpreters_model.appendRow(item)

    def add_python_interpreter(self, path_to_add, notification_parent):
        """Adds given path to the model and returns the index of the new item in the model."""
        key = "appSettings/pythonInterpreters"
        updated_python_interpreters = save_path_to_qsettings(self._qsettings, key, path_to_add)
        self.refresh_python_interpreters_model(updated_python_interpreters)
        return self.find_python_interpreter_index(path_to_add, notification_parent)

    def remove_python_interpreter(self, path_to_remove):
        """Removes given path from the model."""
        key = "appSettings/pythonInterpreters"
        updated_python_interpreters = remove_path_from_qsettings(self._qsettings, key, path_to_remove)
        self.refresh_python_interpreters_model(updated_python_interpreters)

    def find_python_interpreter_index(self, path, notification_parent=None):
        """Returns the index of the given Python interpreter.

        Args:
            path (str): Path to Python interpreter
            notification_parent (QWidget): Parent widget for an error notification
        """
        if not path:
            return self.python_interpreters_model.index(0, 0)
        for row in range(self.python_interpreters_model.rowCount()):
            item = self.python_interpreters_model.item(row, 0)
            if item.data()["exe"] == path:
                return item.index()
        if notification_parent is not None:
            Notification(notification_parent, f"Could not find Python {path}.\nActivating "
                                              f"the current Spine Toolbox Python.").show()
        return self.python_interpreters_model.index(0, 0)

    def find_python_kernel_index(self, kname):
        """Returns the index of the item with the given kernel name
        in Python kernel model or an invalid index if not found."""
        if not kname:
            return self.python_kernel_model.index(0, 0)
        items = self.python_kernel_model.findItems(kname, Qt.MatchFlag.MatchExactly)
        if not items:
            return QModelIndex()
        return items[0].index()

    def start_fetching_python_kernels(self, finalize_slot, conda=""):
        """Starts a thread for fetching Python kernels."""
        if self.python_kernel_fetcher is not None and self.python_kernel_fetcher.isRunning():
            # Trying to start a new thread when the old one is still running
            return
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self.python_kernel_model.clear()
        first_item = QStandardItem("Select Jupyter kernel...")
        self.python_kernel_model.appendRow(first_item)
        if not conda:
            conda = self._qsettings.value("appSettings/condaPath", defaultValue="")
        self.python_kernel_fetcher = KernelFetcher(conda, fetch_mode=2)
        self.python_kernel_fetcher.kernel_found.connect(self._add_python_kernel)
        if finalize_slot is not None:
            self.python_kernel_fetcher.finished.connect(finalize_slot)
        self.python_kernel_fetcher.finished.connect(restore_override_cursor)
        self.python_kernel_fetcher.finished.connect(self._delete_python_kernel_fetcher)
        self.python_kernel_fetcher.start()

    @Slot()
    def _delete_python_kernel_fetcher(self):
        """Clear Julia kernel fetcher."""
        self.python_kernel_fetcher.deleteLater()
        self.python_kernel_fetcher = None

    @Slot()
    def stop_fetching_python_kernels(self):
        """Terminates the kernel fetcher thread."""
        if self.python_kernel_fetcher is not None:
            self.python_kernel_fetcher.stop_fetcher.emit()

    @Slot(str, str, bool, QIcon, dict)
    def _add_python_kernel(self, kernel_name, resource_dir, conda, icon, deats):
        """Adds a kernel entry to a model."""
        if self.python_kernel_fetcher is not None and not self.python_kernel_fetcher.keep_going:
            # Settings widget closed while thread still running
            return
        item = QStandardItem(kernel_name)
        item.setIcon(icon)
        item.setToolTip(resource_dir)
        deats["is_jupyter"] = True
        deats["is_conda"] = conda
        deats["kernel_name"] = kernel_name
        item.setData(deats)
        self._python_kernel_model.appendRow(item)

    @Slot()
    def restore_override_cursor(self):
        """Restores default mouse cursor."""
        while QApplication.overrideCursor() is not None:
            QApplication.restoreOverrideCursor()

    def default_python_execution_settings(self):
        """Returns a dictionary with the Python execution settings stored into QSettings."""
        use_jupyter_cons = bool(int(self._qsettings.value("appSettings/usePythonKernel", defaultValue="0")))
        k_name = self._qsettings.value("appSettings/pythonKernel", defaultValue="")
        env = ""
        if use_jupyter_cons:
            # Find kernel from model and check its data to see if it's a Conda kernel
            index = self.find_python_kernel_index(k_name)
            if index is not None:
                item = self.python_kernel_model.itemFromIndex(index)
                print(f"item.data():{item.data()}")
                if item.data()["is_conda"]:
                    env = "conda"
                print(f"Found Python kernel with env:{env}")
        d = dict()
        d["kernel_spec_name"] = k_name
        d["env"] = env
        d["use_jupyter_console"] = use_jupyter_cons
        d["executable"] = self._qsettings.value("appSettings/pythonPath", defaultValue="")
        return d

    def default_julia_execution_settings(self):
        """Returns a dictionary with the Julia execution settings stored into QSettings."""
        use_jupyter_cons = bool(int(self._qsettings.value("appSettings/useJuliaKernel", defaultValue="0")))
        k_name = self._qsettings.value("appSettings/juliaKernel", defaultValue="")
        env = ""
        if use_jupyter_cons:
            # Find kernel from model and check its data to see if it's a Conda kernel
            item = self.find_julia_kernel_index(k_name)
            if item is not None:
                print(f"item.data():{item.data()}")
                if item.data()["is_conda"]:
                    env = "conda"
                print(f"Found Julia kernel with env:{env}")
        d = dict()
        d["kernel_spec_name"] = k_name
        d["env"] = env
        d["use_jupyter_console"] = use_jupyter_cons
        d["executable"] = self._qsettings.value("appSettings/juliaPath", defaultValue="")
        d["project"] = self._qsettings.value("appSettings/juliaProjectPath", defaultValue="")
        return d

    def load_all(self):
        self.refresh_python_interpreters_model()
        self.refresh_julia_executables_model()
        self.refresh_julia_projects_model()
        self.start_fetching_python_kernels(finalize_slot=None)
        self.start_fetching_julia_kernels(finalize_slot=None)
