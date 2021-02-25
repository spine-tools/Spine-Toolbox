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
Contains PluginManager class.

:author: M. Marin (KTH)
:date:   21.2.2021
"""
import os
import json
import urllib.request
from urllib.parse import urljoin
import shutil
from PySide2.QtCore import Qt, Slot, Signal, QSortFilterProxyModel, QTimer, QSize
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListView, QDialogButtonBox
from PySide2.QtGui import QStandardItemModel, QStandardItem
from spine_engine.utils.serialization import serialize_path, deserialize_path, deserialize_remote_path
from .config import PLUGINS_PATH, PLUGIN_REGISTRY_URL
from .widgets.toolbars import PluginToolBar
from .widgets.custom_qwidgets import MenuToolBarWidget


def _download_file(remote, local):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    urllib.request.urlretrieve(remote, local)


class PluginManager:
    """Class for managing plugins."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI)
        """
        self._toolbox = toolbox
        self._plugin_toolbars = {}
        self.plugin_specs = []
        self._registry = {}
        self._registry_plugins = {}
        self._installed_plugins = {}

    @property
    def plugin_toolbars(self):
        return self._plugin_toolbars

    def load_plugins(self):
        search_paths = {PLUGINS_PATH}
        search_paths |= set(
            self._toolbox.qsettings().value("appSettings/pluginSearchPaths", defaultValue="").split(";")
        )
        # Plugind dirs are top-level dirs in all search paths
        plugin_dirs = []
        for path in search_paths:
            try:
                top_level_items = [os.path.join(path, item) for item in os.listdir(path)]
            except FileNotFoundError:
                continue
            plugin_dirs += [item for item in top_level_items if os.path.isdir(item)]
        for plugin_dir in plugin_dirs:
            self.load_individual_plugin(plugin_dir)
        self._toolbox.refresh_toolbars()

    def load_individual_plugin(self, plugin_dir):
        """Loads plugin from directory and returns all the specs in a list.

        Args:
            plugin_dir (str): path of plugin dir with "plugin.json" in it.

        Returns:
            list(ProjectItemSpecification)
        """
        plugin_file = os.path.join(plugin_dir, "plugin.json")
        if not os.path.isfile(plugin_file):
            return
        with open(plugin_file, "r") as fh:
            try:
                plugin_dict = json.load(fh)
            except json.decoder.JSONDecodeError:
                self.msg_error.emit(f"Error in plugin file <b>{plugin_file}</b>. Invalid JSON.")
                return
        try:
            name = plugin_dict["name"]
            plugin_dict["plugin_dir"] = plugin_dir
            self._installed_plugins[name] = plugin_dict
            specifications = plugin_dict["specifications"]
        except KeyError as key:
            self.msg_error.emit(f"Error in plugin file <b>{plugin_file}</b>. Key '{key}' not found.")
            return
        deserialized_paths = [deserialize_path(path, plugin_dir) for paths in specifications.values() for path in paths]
        plugin_specs = []
        for path in deserialized_paths:
            spec = self._toolbox.load_specification_from_file(path)
            if not spec:
                continue
            spec.plugin = name
            plugin_specs.append(spec)
        self.plugin_specs += plugin_specs
        toolbar = self._plugin_toolbars[name] = PluginToolBar(name, parent=self._toolbox)
        toolbar.setup(plugin_specs)
        self._toolbox.addToolBar(Qt.TopToolBarArea, toolbar)
        return plugin_specs

    def _load_registry(self):
        self._registry_plugins.clear()
        with urllib.request.urlopen(PLUGIN_REGISTRY_URL) as url:
            self._registry = json.loads(url.read().decode())
        self._registry_plugins = {plugin_dict["name"]: plugin_dict for plugin_dict in self._registry["plugins"]}

    @Slot(bool)
    def show_install_plugin_dialog(self, _=False):
        dialog = _InstallPluginDialog(self._toolbox)
        self._load_registry()
        names = self._registry_plugins.keys() - self._installed_plugins.keys()
        dialog.populate_list(names)
        dialog.item_selected.connect(self._install_plugin)
        dialog.show()

    @Slot(bool)
    def show_manage_plugins_dialog(self, _=False):
        dialog = _ManagePluginsDialog(self._toolbox)
        self._load_registry()
        names = (
            (name, plugin_dict["version"].split(".") < self._registry_plugins[name]["version"].split("."))
            for name, plugin_dict in self._installed_plugins.items()
        )
        dialog.populate_list(names)
        dialog.item_removed.connect(self._remove_installed_plugin)
        dialog.item_updated.connect(self._update_plugin)
        dialog.show()

    @Slot(str)
    def _install_plugin(self, plugin_name):
        """Installs plugin from the registry and loads it.

        Args:
            plugin_name (str): plugin name
        """
        plugin = self._registry_plugins[plugin_name]
        plugin_local_dir = os.path.join(PLUGINS_PATH, plugin_name)
        worker = self._create_worker()
        worker.finished.connect(lambda plugin_local_dir=plugin_local_dir: self._load_installed_plugin(plugin_local_dir))
        worker.start(_download_plugin, plugin, plugin_local_dir)

    def _load_installed_plugin(self, plugin_local_dir):
        self.load_individual_plugin(plugin_local_dir)
        self._toolbox.refresh_toolbars()

    @Slot(bool)
    def show_manage_plugins_dialog(self, _=False):
        self._toolbox.ui.menuPlugins.setEnabled(False)
        worker = self._create_worker()
        worker.finished.connect(self._do_show_manage_plugins_dialog)
        worker.start(self._load_registry)

    @Slot()
    def _do_show_manage_plugins_dialog(self):
        dialog = ManagePluginsDialog(self._toolbox)
        names = (
            (name, plugin_dict["version"].split(".") < self._registry_plugins[name]["version"].split("."))
            for name, plugin_dict in self._installed_plugins.items()
        )
        dialog.populate_list(names)
        dialog.item_removed.connect(self._remove_plugin)
        dialog.item_updated.connect(self._update_plugin)
        dialog.destroyed.connect(lambda obj=None: self._toolbox.ui.menuPlugins.setEnabled(True))
        dialog.show()

    @Slot(str)
    def _remove_plugin(self, plugin_name):
        """Removes installed plugin.

        Args:
            plugin_name (str): plugin name
        """
        plugin_dict = self._installed_plugins.pop(plugin_name)
        plugin_dir = plugin_dict["plugin_dir"]
        # Remove specs from model
        specifications = plugin_dict["specifications"]
        deserialized_paths = [deserialize_path(path, plugin_dir) for paths in specifications.values() for path in paths]
        for path in deserialized_paths:
            spec_dict = self._toolbox.parse_specification_file(path)
            row = self._toolbox.specification_model.specification_row(spec_dict["name"])
            if row >= 0:
                self._toolbox.do_remove_specification(row, ask_verification=False)
        # Remove plugin dir
        shutil.rmtree(plugin_dir)
        self._plugin_toolbars[plugin_name].deleteLater()
        self._toolbox.refresh_toolbars()

    @Slot(str)
    def _update_plugin(self, plugin_name):
        self._remove_installed_plugin(plugin_name)
        self._install_plugin(plugin_name)


class _PluginWorker(QObject):

    finished = Signal()

    def __init__(self):
        super().__init__()
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._function = None
        self._args = None
        self._kwargs = None

    def start(self, function, *args, **kwargs):
        self._thread.started.connect(self._do_work)
        self._function = function
        self._args = args
        self._kwargs = kwargs
        self._thread.start()

    @Slot()
    def _do_work(self):
        self._function(*self._args, **self._kwargs)
        self.finished.emit()

    def clean_up(self):
        self._thread.quit()
        self._thread.wait()
        self.deleteLater()
