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
import shutil
from PySide2.QtCore import Qt, Slot, Signal, QSortFilterProxyModel, QTimer, QSize
from PySide2.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListView, QDialogButtonBox
from PySide2.QtGui import QStandardItemModel, QStandardItem
from spine_engine.utils.serialization import serialize_path, deserialize_path, deserialize_remote_path
from .config import PLUGINS_PATH, PLUGIN_REGISTRY_URL
from .helpers import color_from_index
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
        self._refresh_toolbars()

    def _refresh_toolbars(self):
        """Set toolbars' color using highest possible contrast."""
        all_toolbars = [self._toolbox.main_toolbar] + list(self._plugin_toolbars.values())
        for k, toolbar in enumerate(all_toolbars):
            color = color_from_index(k, len(all_toolbars), base_hue=217.0, saturation=0.6)
            toolbar.set_color(color)

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
        # Download plugin.json file
        plugin_local_dir = os.path.join(PLUGINS_PATH, plugin_name)
        plugin_local_file = os.path.join(plugin_local_dir, "plugin.json")
        plugin_remote_file = plugin["url"]
        _download_file(plugin_remote_file, plugin_local_file)
        # Parse plugin.json file
        with open(plugin_local_file) as fh:
            plugin_dict = json.load(fh)
        # Download specification .json files
        plugin_remote_dir = plugin_dict["base_path"]
        specifications = plugin_dict["specifications"]
        serialized_paths = (path for paths in specifications.values() for path in paths)
        for serialized in serialized_paths:
            local_file = deserialize_path(serialized, plugin_local_dir)
            remote_file = deserialize_remote_path(serialized, plugin_remote_dir)
            _download_file(remote_file, local_file)
        # Download include files in tool specs
        serialized_includes = []
        for serialized in specifications.get("Tool", ()):
            spec_file = deserialize_path(serialized, plugin_local_dir)
            with open(spec_file) as fh:
                spect_dict = json.load(fh)
            includes = spect_dict["includes"]
            includes_main_path = spect_dict.get("includes_main_path", ".")
            spec_dir = os.path.dirname(spec_file)
            includes_main_path = os.path.join(spec_dir, includes_main_path)
            includes = [os.path.join(includes_main_path, include) for include in includes]
            serialized_includes += [serialize_path(include, plugin_local_dir) for include in includes]
        for serialized in serialized_includes:
            local_file = deserialize_path(serialized, plugin_local_dir)
            remote_file = deserialize_remote_path(serialized, plugin_remote_dir)
            _download_file(remote_file, local_file)
        # Load plugin
        plugin_specs = self.load_individual_plugin(plugin_local_dir)
        for spec in plugin_specs:
            self._toolbox.do_add_specification(spec)
        self._refresh_toolbars()

    @Slot(str)
    def _remove_installed_plugin(self, plugin_name):
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
        self._refresh_toolbars()

    @Slot(str)
    def _update_plugin(self, plugin_name):
        self._remove_installed_plugin(plugin_name)
        self._install_plugin(plugin_name)


class _InstallPluginModel(QStandardItemModel):
    def data(self, index, role=None):
        if role == Qt.SizeHintRole:
            return QSize(0, 40)
        return super().data(index, role)


class _ManagePluginsModel(_InstallPluginModel):
    def flags(self, index):
        return super().flags(index) & ~Qt.ItemIsSelectable


class _InstallPluginDialog(QDialog):

    item_selected = Signal(str)

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)
        self.setWindowTitle('Install plugin')
        QVBoxLayout(self)
        self._line_edit = QLineEdit(self)
        self._line_edit.setPlaceholderText("Search registry...")
        self._list_view = QListView(self)
        self._model = QSortFilterProxyModel(self)
        self._source_model = _InstallPluginModel(self)
        self._model.setSourceModel(self._source_model)
        self._model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._list_view.setModel(self._model)
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._button_box = QDialogButtonBox(self)
        self._button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self._button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.layout().addWidget(self._line_edit)
        self.layout().addWidget(self._list_view)
        self.layout().addWidget(self._button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumWidth(400)
        self._button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self._button_box.button(QDialogButtonBox.Ok).clicked.connect(self._handle_ok_clicked)
        self._list_view.doubleClicked.connect(self._emit_item_selected)
        self._list_view.selectionModel().selectionChanged.connect(self._update_ok_button_enabled)
        self._line_edit.textEdited.connect(self._handle_search_text_changed)
        self._timer.timeout.connect(self._filter_model)

    def populate_list(self, names):
        for name in names:
            self._source_model.appendRow(QStandardItem(name))

    @Slot(str)
    def _handle_search_text_changed(self, _text):
        self._timer.start()

    def _filter_model(self):
        self._model.setFilterRegExp(self._line_edit.text())

    @Slot(bool)
    def _handle_ok_clicked(self, _=False):
        index = self._list_view.currentIndex()
        self._emit_item_selected(index)

    @Slot("QModelIndex")
    def _emit_item_selected(self, index):
        if not index.isValid():
            return
        self.item_selected.emit(index.data(Qt.DisplayRole))
        self.close()

    @Slot("QItemSelection", "QItemSelection")
    def _update_ok_button_enabled(self, _selected, _deselected):
        on = self._list_view.selectionModel().hasSelection()
        self._button_box.button(QDialogButtonBox.Ok).setEnabled(on)


class _ManagePluginsDialog(QDialog):
    item_removed = Signal(str)
    item_updated = Signal(str)

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)
        self.setWindowTitle('Manage plugins')
        QVBoxLayout(self)
        self._list_view = QListView(self)
        self._model = _ManagePluginsModel(self)
        self._list_view.setModel(self._model)
        self._button_box = QDialogButtonBox(self)
        self._button_box.setStandardButtons(QDialogButtonBox.Close)
        self.layout().addWidget(self._list_view)
        self.layout().addWidget(self._button_box)
        self.setMinimumWidth(400)
        self._button_box.button(QDialogButtonBox.Close).clicked.connect(self.close)

    def populate_list(self, names):
        for name, can_update in names:
            item = QStandardItem(name)
            self._model.appendRow(item)
            widget = self._create_plugin_widget(name, can_update)
            index = self._model.indexFromItem(item)
            self._list_view.setIndexWidget(index, widget)

    def _create_plugin_widget(self, plugin_name, can_update):
        widget = MenuToolBarWidget(plugin_name)
        widget.tool_bar.addAction("Remove", lambda _=False, n=plugin_name: self._emit_item_removed(n))
        update = widget.tool_bar.addAction("Update", lambda _=False, n=plugin_name: self._emit_item_updated(n))
        update.setEnabled(can_update)
        update.triggered.connect(lambda _=False: update.setEnabled(False))
        return widget

    def _emit_item_removed(self, plugin_name):
        for row in range(self._model.rowCount()):
            if self._model.index(row, 0).data(Qt.DisplayRole) == plugin_name:
                self._model.removeRow(row)
                break
        self.item_removed.emit(plugin_name)

    def _emit_item_updated(self, plugin_name):
        self.item_updated.emit(plugin_name)
