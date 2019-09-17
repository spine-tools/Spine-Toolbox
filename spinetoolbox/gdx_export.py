######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Tool class.

:author: A. Soininen (VTT)
:date:   5.9.2019
"""

from copy import deepcopy
import json
import logging
import os.path
from PySide2.QtCore import QUrl, Slot
from PySide2.QtGui import QDesktopServices, QIcon, QPixmap
from data_store import DataStore
from graphics_items import GdxExportIcon
from helpers import create_dir, get_db_map
from project_item import ProjectItem
from spine_io.exporters import gdx
from widgets.gdx_export_settings import GdxExportSettings
from widgets.export_list_item import ExportListItem


class GdxExport(ProjectItem):
    """
    This project item handles all functionality regarding exporting a database to .gdx file.

    Attributes:
        toolbox (ToolboxUI): a ToolboxUI instance
        name (str): item name
        description (str): item description
        database_urls (list): a list of connected database urls
        database_to_file_name_map (dict): mapping from database path (str) to an output file name (str)
        x (int): initial X coordinate of item icon
        y (int): initial Y coordinate of item icon
    """
    def __init__(self, toolbox, name, description, database_urls=None, database_to_file_name_map=None, settings_file_names=None, x=0.0, y=0.0):
        super().__init__(toolbox, name, description)
        self.item_type = "Gdx Export"
        self._settings_windows = dict()
        self._settings = dict()
        self._database_urls = database_urls if database_urls is not None else list()
        self._database_to_file_name_map = database_to_file_name_map if database_to_file_name_map is not None else dict()
        self.spine_ref_icon = QIcon(QPixmap(":/icons/Spine_db_ref_icon.png"))
        # Make project directory for this View
        self.data_dir = os.path.join(self._toolbox.project().project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed." " Check permissions.".format(self.data_dir)
            )
        if settings_file_names is not None:
            for file_name in settings_file_names:
                with open(file_name) as input_file:
                    data = json.load(input_file)
                    database_path = data["database path"]
                    settings = gdx.Settings.from_dict(data)
                    self._settings[database_path] = settings
        self._graphics_item = GdxExportIcon(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self._sigs = self.make_signal_handler_dict()

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers."""
        s = {
            self._toolbox.ui.toolButton_gdx_export_open_dir.clicked: lambda checked: self.open_directory(checked)
        }
        return s

    def activate(self):
        """Restores selections and connects signals."""
        self.restore_selections()
        super().connect_signals()

    def deactivate(self):
        """Saves selections and disconnects signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed.", self.name)
            return False
        return True

    def save_selections(self):
        """Saves selections in shared widgets for this project item into instance variables."""

    def restore_selections(self):
        """Restores selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_gdx_export_name.setText(self.name)
        self.link_changed()
        database_list_storage = self._toolbox.ui.gdx_export_databases_list_layout
        while not database_list_storage.isEmpty():
            widget_to_remove = database_list_storage.takeAt(0)
            widget_to_remove.widget().deleteLater()
        for row, url in enumerate(self._database_urls):
            database_path = url.database
            file_name = self._database_to_file_name_map.get(database_path, '')
            item = ExportListItem(database_path, file_name)
            database_list_storage.insertWidget(0, item)
            item.settings_button.clicked.connect(lambda checked: self.__show_settings(url))
            item.out_file_name_edit.textChanged.connect(lambda text: self.__update_out_file_name(text, database_path))

    def link_changed(self):
        """Updates the list of files that this item is exporting."""
        self._database_urls.clear()
        for input_item in self._toolbox.connection_model.input_items(self.name):
            found_index = self._toolbox.project_item_model.find_item(input_item)
            if not found_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(found_index)
            if not isinstance(item, DataStore):
                continue
            self._database_urls.append(item.make_url())

    def data_files(self):
        """Returns a list of exported file names."""
        return list()

    @Slot(bool, name="open_directory")
    def open_directory(self, checked=False):
        """Open file explorer in data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    def execute(self):
        """Executes this Tool."""
        if not gdx.available():
            self._toolbox.msg_error.emit('No GAMS Python bindings installed. GDX export is disabled.')
            abort = -1
            self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(abort)
            return
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Gdx Export <b>{}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        self.link_changed()
        for url in self._database_urls:
            database_map = get_db_map(url)
            settings = self._settings.get(url.database, None)
            if settings is None:
                settings = gdx.make_settings(database_map)
            _, gams_database = gdx.to_gams_workspace(database_map, settings)
            file_name = self._database_to_file_name_map.get(url.database, None)
            if file_name is None:
                self._toolbox.msg_error.emit('No file name given to export database {}.'.format(url.database))
                abort = -1
                self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(abort)
                return
            out_path = os.path.join(self.data_dir, file_name)
            gdx.export_to_gdx(gams_database, out_path)
        success = 0
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(success)

    def stop_execution(self):
        """Stops executing this Tool."""

    def __show_settings(self, database_url):
        """Opens the item's settings window."""
        database_path = database_url.database
        settings = self._settings.get(database_path, None)
        if settings is None:
            database_map = get_db_map(database_url)
            settings = gdx.make_settings(database_map)
            self._settings[database_path] = settings
        # Give window its own settings so Cancel doesn't change anything here.
        settings = deepcopy(settings)
        settings_window = self._settings_windows.get(database_path, None)
        if settings_window is None:
            settings_window = GdxExportSettings(settings, self._toolbox)
            self._settings_windows[database_path] = settings_window
        settings_window.button_box.accepted.connect(lambda: self.__settings_approved(database_path))
        settings_window.button_box.rejected.connect(lambda: self.__settings_declined(database_path))
        settings_window.show()

    def __update_out_file_name(self, file_name, database_path):
        self._database_to_file_name_map[database_path] = file_name

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        d["database_to_file_name_map"] = self._database_to_file_name_map
        settings_file_names = self.__save_settings()
        d["settings_file_names"] = settings_file_names
        return d

    def __settings_approved(self, database_path):
        settings_window = self._settings_windows[database_path]
        self._settings[database_path] = settings_window.settings
        settings_window.deleteLater()
        del self._settings_windows[database_path]

    def __settings_declined(self, database_path):
        settings_window = self._settings_windows[database_path]
        settings_window.deleteLater()
        del self._settings_windows[database_path]

    def __save_settings(self):
        file_names = list()
        for index, (database_path, settings) in enumerate(self._settings.items()):
            settings_dictionary = settings.to_dict()
            settings_dictionary["database path"] = database_path
            file_name = os.path.join(self.data_dir, "export_settings_{}.json".format(index + 1))
            with open(file_name, "w") as output_file:
                json.dump(settings_dictionary, output_file, sort_keys=True, indent=4)
                file_names.append(file_name)
        return file_names
