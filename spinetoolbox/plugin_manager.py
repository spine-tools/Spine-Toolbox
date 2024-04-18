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

"""Contains PluginManager class."""
import itertools
import os
import json
import urllib.request
import urllib.error
from urllib.parse import urljoin
import shutil
from PySide6.QtCore import Qt, Signal, Slot, QObject, QThread
from spine_engine.utils.serialization import serialize_path, deserialize_path, deserialize_remote_path
from .config import PLUGINS_PATH, PLUGIN_REGISTRY_URL
from .helpers import (
    load_plugin_dict,
    load_plugin_specifications,
    plugins_dirs,
    load_specification_local_data,
    load_specification_from_file,
)
from .widgets.toolbars import PluginToolBar
from .widgets.plugin_manager_widgets import InstallPluginDialog, ManagePluginsDialog


def _download_file(remote, local):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    try:
        urllib.request.urlretrieve(remote, local)
    except urllib.error.HTTPError as e:
        raise PluginWorkFailed(f"Failed to download {remote}: {str(e)}")


def _download_plugin(plugin, plugin_local_dir):
    # 1. Create paths
    plugin_remote_file = plugin["url"]
    plugin_remote_dir = urljoin(plugin_remote_file, ".")
    plugin_local_file = os.path.join(plugin_local_dir, "plugin.json")
    # 2. Download and parse plugin.json file
    _download_file(plugin_remote_file, plugin_local_file)
    with open(plugin_local_file) as fh:
        plugin_dict = json.load(fh)
    # 3. Download specification .json files
    specifications = plugin_dict["specifications"]
    serialized_paths = (path for paths in specifications.values() for path in paths)
    for serialized in serialized_paths:
        local_file = deserialize_path(serialized, plugin_local_dir)
        remote_file = deserialize_remote_path(serialized, plugin_remote_dir)
        _download_file(remote_file, local_file)
    # 4. Download include files in tool specs
    serialized_includes = []
    for serialized in specifications.get("Tool", ()):
        spec_file = deserialize_path(serialized, plugin_local_dir)
        with open(spec_file) as fh:
            spec_dict = json.load(fh)
        includes = spec_dict["includes"]
        includes_main_path = spec_dict.get("includes_main_path", ".")
        spec_dir = os.path.dirname(spec_file)
        includes_main_path = os.path.join(spec_dir, includes_main_path)
        includes = [os.path.join(includes_main_path, include) for include in includes]
        serialized_includes += [serialize_path(include, plugin_local_dir) for include in includes]
    for serialized in serialized_includes:
        local_file = deserialize_path(serialized, plugin_local_dir)
        remote_file = deserialize_remote_path(serialized, plugin_remote_dir)
        _download_file(remote_file, local_file)


class PluginManager:
    """Class for managing plugins."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): Toolbox instance.
        """
        self._toolbox = toolbox
        self._plugin_toolbars = {}
        self._workers = []
        self._installed_plugins = {}
        self._registry_plugins = {}
        self._plugin_specs = {}

    @property
    def plugin_toolbars(self):
        return self._plugin_toolbars

    @property
    def plugin_specs(self):
        for specs in self._plugin_specs.values():
            yield from specs

    def load_installed_plugins(self):
        """Loads installed plugins and adds their specifications to toolbars."""
        project = self._toolbox.project()
        local_data = load_specification_local_data(project.config_dir) if project else {}
        for plugin_dir in plugins_dirs(self._toolbox.qsettings()):
            self.load_individual_plugin(plugin_dir, local_data)

    def reload_plugins_with_local_data(self):
        """Reloads plugins that have project specific local data."""
        project = self._toolbox.project()
        local_data = load_specification_local_data(project.config_dir) if project else {}
        specification_factories = self._toolbox.item_specification_factories()
        app_settings = self._toolbox.qsettings()
        for plugin_name, specifications in self._plugin_specs.items():
            for specification in specifications:
                if not specification.may_have_local_data():
                    continue
                reloaded = load_specification_from_file(
                    specification.definition_file_path, local_data, specification_factories, app_settings, self._toolbox
                )
                reloaded.plugin = plugin_name
                project.replace_specification(reloaded.name, reloaded, save_to_disk=False)

    def load_individual_plugin(self, plugin_dir, specification_local_data):
        """Loads plugin from directory.

        Args:
            plugin_dir (str): path of plugin dir with "plugin.json" in it.
            specification_local_data (dict): specification local data
        """
        plugin_dict = load_plugin_dict(plugin_dir, self._toolbox)
        if plugin_dict is None:
            return
        plugin_specs = load_plugin_specifications(
            plugin_dict,
            specification_local_data,
            self._toolbox.item_specification_factories(),
            self._toolbox.qsettings(),
            self._toolbox,
        )
        if plugin_specs is None:
            return
        name = plugin_dict["name"]
        self._installed_plugins[name] = plugin_dict
        disabled_plugins = set()
        if self._toolbox.project() is not None:
            for spec in itertools.chain(*plugin_specs.values()):
                spec_id = self._toolbox.project().add_specification(spec, save_to_disk=False)
                if spec_id is None:
                    disabled_plugins.add(spec.name)
        self._plugin_specs.update(plugin_specs)
        toolbar = self._plugin_toolbars[name] = PluginToolBar(name, parent=self._toolbox)
        toolbar.setup(plugin_specs, disabled_plugins)

    def _create_worker(self):
        worker = _PluginWorker()
        self._workers.append(worker)
        worker.finished.connect(lambda worker=worker: self._clean_up_worker(worker))
        return worker

    def _clean_up_worker(self, worker):
        self._workers.remove(worker)
        worker.clean_up()

    def _load_registry(self):
        try:
            with urllib.request.urlopen(PLUGIN_REGISTRY_URL) as url:
                registry = json.loads(url.read().decode())
        except urllib.error.URLError:
            raise PluginWorkFailed("Failed to load plugin registry. Are you connected to a network?")
        self._registry_plugins = {plugin_dict["name"]: plugin_dict for plugin_dict in registry["plugins"]}

    @Slot(bool)
    def show_install_plugin_dialog(self, _=False):
        self._toolbox.ui.menuPlugins.setEnabled(False)
        worker = self._create_worker()
        worker.succeeded.connect(self._do_show_install_plugin_dialog)
        worker.failed.connect(self._toolbox.msg_error)
        worker.failed.connect(lambda: self._toolbox.ui.menuPlugins.setEnabled(True))
        worker.start(self._load_registry)

    @Slot()
    def _do_show_install_plugin_dialog(self):
        dialog = InstallPluginDialog(self._toolbox)
        names = self._registry_plugins.keys() - self._installed_plugins.keys()
        dialog.populate_list(names)
        dialog.item_selected.connect(self._install_plugin)
        dialog.destroyed.connect(lambda obj=None: self._toolbox.ui.menuPlugins.setEnabled(True))
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
        worker.succeeded.connect(
            lambda plugin_local_dir=plugin_local_dir: self._load_installed_plugin(plugin_local_dir)
        )
        worker.failed.connect(self._toolbox.msg_error)
        worker.start(_download_plugin, plugin, plugin_local_dir)

    def _load_installed_plugin(self, plugin_local_dir):
        project = self._toolbox.project()
        local_data = load_specification_local_data(project.config_dir) if project is not None else {}
        self.load_individual_plugin(plugin_local_dir, local_data)
        self._toolbox.refresh_toolbars()

    @Slot(bool)
    def show_manage_plugins_dialog(self, _=False):
        self._toolbox.ui.menuPlugins.setEnabled(False)
        worker = self._create_worker()
        worker.succeeded.connect(self._do_show_manage_plugins_dialog)
        worker.failed.connect(self._toolbox.msg_error)
        worker.failed.connect(lambda: self._toolbox.ui.menuPlugins.setEnabled(True))
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
        self._plugin_specs.pop(plugin_name, None)
        if self._toolbox.project() is not None:
            for spec in list(self._toolbox.project().specifications()):
                if spec.plugin == plugin_name:
                    self._toolbox.project().remove_specification(spec.name)
        # Remove plugin dir
        shutil.rmtree(plugin_dir)
        self._plugin_toolbars.pop(plugin_name).deleteLater()
        self._toolbox.refresh_toolbars()

    @Slot(str)
    def _update_plugin(self, plugin_name):
        self._remove_plugin(plugin_name)
        self._install_plugin(plugin_name)


class PluginWorkFailed(Exception):
    """Exception to signal plugin worker that something failed."""


class _PluginWorker(QObject):
    failed = Signal(str)
    finished = Signal()
    succeeded = Signal()

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
        try:
            self._function(*self._args, **self._kwargs)
        except PluginWorkFailed as e:
            self.failed.emit(str(e))
        else:
            self.succeeded.emit()
        self.finished.emit()

    def clean_up(self):
        self._thread.quit()
        self._thread.wait()
        self.deleteLater()
