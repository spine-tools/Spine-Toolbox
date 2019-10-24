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
Gdx Export project item.

:author: A. Soininen (VTT)
:date:   5.9.2019
"""

from copy import deepcopy
import json
import logging
import pathlib
import os.path
from PySide2.QtCore import Slot
from spinetoolbox.helpers import get_db_map
from spinetoolbox.project_item import ProjectItem, ProjectItemResource
from spinetoolbox.spine_io.exporters import gdx
from .widgets.gdx_export_settings import GdxExportSettings
from .widgets.export_list_item import ExportListItem


class GdxExport(ProjectItem):
    """
    This project item handles all functionality regarding exporting a database to .gdx file.
    """

    _item_type = "Gdx Export"
    _missing_output_file_notification = (
        "Output file name(s) missing." + " See the settings in the {} Properties panel.".format(_item_type)
    )

    def __init__(
        self,
        toolbox,
        name,
        description,
        database_urls=None,
        database_to_file_name_map=None,
        settings_file_names=None,
        x=0.0,
        y=0.0,
    ):
        """
        Args:
            toolbox (ToolboxUI): a ToolboxUI instance
            name (str): item name
            description (str): item description
            database_urls (list): a list of connected database urls
            database_to_file_name_map (dict): mapping from database path (str) to an output file name (str)
            settings_file_names (dict): mapping from database path (str) to export settings file name (str)
            x (float): initial X coordinate of item icon
            y (float): initial Y coordinate of item icon
        """
        super().__init__(toolbox, GdxExport._item_type, name, description, x, y)
        self._settings_windows = dict()
        self._settings = dict()
        self._database_urls = database_urls if database_urls is not None else list()
        self._database_to_file_name_map = database_to_file_name_map if database_to_file_name_map is not None else dict()
        if settings_file_names is not None:
            for file_name in settings_file_names:
                try:
                    with open(file_name) as input_file:
                        data = json.load(input_file)
                        database_path = data["database path"]
                        settings = gdx.Settings.from_dict(data)
                        self._settings[database_path] = settings
                except FileNotFoundError:
                    self._toolbox.msg_error.emit("{} not found. Skipping.".format(file_name))
        self._activated = False

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers."""
        s = {self._properties_ui.open_directory_button.clicked: self.open_directory}
        return s

    def activate(self):
        """Restores selections and connects signals."""
        self.restore_selections()
        super().connect_signals()
        self._activated = True

    def deactivate(self):
        """Saves selections and disconnects signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed.", self.name)
            return False
        self._activated = False
        return True

    def save_selections(self):
        """Saves selections in shared widgets for this project item into instance variables."""

    def restore_selections(self):
        """Restores selections into shared widgets when this project item is selected."""
        self._properties_ui.item_name_label.setText(self.name)
        database_list_storage = self._properties_ui.databases_list_layout
        while not database_list_storage.isEmpty():
            widget_to_remove = database_list_storage.takeAt(0)
            widget_to_remove.widget().deleteLater()
        for url in self._database_urls:
            file_name = self._database_to_file_name_map.get(url, '')
            item = ExportListItem(url, file_name)
            database_list_storage.insertWidget(0, item)
            # pylint: disable=cell-var-from-loop
            item.refresh_settings_clicked.connect(self._refresh_settings_for_database)
            item.open_settings_clicked.connect(self._show_settings)
            item.file_name_changed.connect(self._update_out_file_name)

    def execute(self):
        """Executes this item."""
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Gdx Export <b>{}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        success = 0
        abort = -1
        gams_system_directory = self._resolve_gams_system_directory()
        for url in self._database_urls:
            file_name = self._database_to_file_name_map.get(url, None)
            if file_name is None:
                self._toolbox.msg_error.emit("No file name given to export database {}.".format(url))
                self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(abort)
                return
            database_map = get_db_map(url)
            settings = self._settings.get(url, None)
            if settings is None:
                settings = gdx.make_settings(database_map)
                self._settings[url] = settings
            out_path = os.path.join(self.data_dir, file_name)
            gdx.to_gdx_file(database_map, out_path, settings, gams_system_directory)
            database_map.connection.close()
            self._toolbox.msg_success.emit("File <b>{0}</b> written".format(out_path))
        execution_instance = self._toolbox.project().execution_instance
        paths = [os.path.join(self.data_dir, file_name) for file_name in self._database_to_file_name_map.values()]
        resources = [ProjectItemResource(self, "file", url=pathlib.Path(path).as_uri()) for path in paths]
        execution_instance.advertise_resources(self.name, *resources)
        execution_instance.project_item_execution_finished_signal.emit(success)

    def stop_execution(self):
        """Stops executing this item."""
        self._toolbox.msg.emit("Stopping {0}".format(self.name))
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-2)

    def simulate_execution(self, inst):
        """Simulates executing this item."""
        super().simulate_execution(inst)
        self._database_urls.clear()
        self._database_urls += [r.url for r in inst.available_resources(self.name) if r.type_ == "database"]
        files = self._database_to_file_name_map.values()
        paths = [os.path.join(self.data_dir, file_name) for file_name in files]
        resources = [ProjectItemResource(self, "file", url=pathlib.Path(path).as_uri()) for path in paths]
        inst.advertise_resources(self.name, *resources)
        notify_about_missing_output_file = False
        if "" in files:
            notify_about_missing_output_file = True
        else:
            for url in self._database_urls:
                if url not in self._database_to_file_name_map:
                    notify_about_missing_output_file = True
                    break
        if notify_about_missing_output_file:
            self.add_notification(GdxExport._missing_output_file_notification)
        if self._activated:
            self.restore_selections()

    @Slot(str)
    def _show_settings(self, database_url):
        """Opens the item's settings window."""
        settings = self._settings.get(database_url, None)
        if settings is None:
            database_map = get_db_map(database_url)
            settings = gdx.make_settings(database_map)
            self._settings[database_url] = settings
            database_map.connection.close()
        # Give window its own settings so Cancel doesn't change anything here.
        settings = deepcopy(settings)
        settings_window = self._settings_windows.get(database_url, None)
        if settings_window is None:
            settings_window = GdxExportSettings(settings, database_url, self._toolbox)
            self._settings_windows[database_url] = settings_window
        settings_window.button_box.accepted.connect(lambda: self._update_settings_from_settings_window(database_url))
        settings_window.window_closing.connect(lambda: self._discard_settings_window(database_url))
        settings_window.show()

    @Slot(str, str)
    def _update_out_file_name(self, file_name, database_path):
        """Updates the output file name for given database"""
        if file_name:
            self.clear_notifications()
        else:
            self.add_notification(GdxExport._missing_output_file_notification)
        self._database_to_file_name_map[database_path] = file_name

    def item_dict(self):
        """Returns a dictionary corresponding to this item's configuration."""
        d = super().item_dict()
        d["database_to_file_name_map"] = self._database_to_file_name_map
        settings_file_names = self._save_settings()
        d["settings_file_names"] = settings_file_names
        return d

    def _update_settings_from_settings_window(self, database_path):
        """Updates the export settings for given database from the settings window."""
        settings_window = self._settings_windows[database_path]
        self._settings[database_path] = settings_window.settings
        settings_window.close()

    def _discard_settings_window(self, database_path):
        """Discards the settings window for given database."""
        del self._settings_windows[database_path]

    def _save_settings(self):
        """Saves all export settings to .json files in the item's data directory."""
        file_names = list()
        for index, (database_path, settings) in enumerate(self._settings.items()):
            settings_dictionary = settings.to_dict()
            settings_dictionary["database path"] = database_path
            file_name = os.path.join(self.data_dir, "export_settings_{}.json".format(index + 1))
            with open(file_name, "w") as output_file:
                json.dump(settings_dictionary, output_file, sort_keys=True, indent=4)
                file_names.append(file_name)
        return file_names

    def update_name_label(self):
        """See `ProjectItem.update_name_label()`."""
        self._properties_ui.item_name_label.setText(self.name)

    def _resolve_gams_system_directory(self):
        """Returns GAMS system path from Toolbox settings or None if GAMS default is to be used."""
        path = self._toolbox.qsettings().value("appSettings/gamsPath", defaultValue=None)
        if not path:
            path = gdx.find_gams_directory()
        if path is not None and os.path.isfile(path):
            path = os.path.dirname(path)
        return path

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type == "Data Store":
            self._toolbox.msg.emit(
                "Link established. Data Store <b>{0}</b> will be "
                "exported to a .gdx file by <b>{1}</b> when executing.".format(source_item.name, self.name)
            )
        else:
            super().notify_destination(source_item)

    @Slot(str)
    def _refresh_settings_for_database(self, url):
        original_settings = self._settings.get(url, None)
        database_map = get_db_map(url)
        new_settings = gdx.make_settings(database_map)
        database_map.connection.close()
        if original_settings is None:
            self._settings[url] = new_settings
            return
        original_settings.update(new_settings)

    @staticmethod
    def default_name_prefix():
        """see base class"""
        return "Gdx Export"
