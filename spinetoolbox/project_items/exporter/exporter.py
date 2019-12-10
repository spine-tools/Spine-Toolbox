######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Exporter project item.

:author: A. Soininen (VTT)
:date:   5.9.2019
"""

from copy import deepcopy
import json
import logging
import pathlib
import os.path
from PySide2.QtCore import Slot
from spinedb_api.database_mapping import DatabaseMapping
from spinedb_api.parameter_value import from_database
from spinetoolbox.project_item import ProjectItem, ProjectItemResource
from spinetoolbox.spine_io import gdx_utils
from spinetoolbox.spine_io.exporters import gdx
from .widgets.gdx_export_settings import GdxExportSettings
from .widgets.export_list_item import ExportListItem


class Exporter(ProjectItem):
    """
    This project item handles all functionality regarding exporting a database to a file.

    Currently, only .gdx format is supported.
    """

    _missing_output_file_notification = (
        "Output file name(s) missing. See the settings in the Exporter Properties panel."
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
        super().__init__(toolbox, name, description, x, y)
        self._settings_windows = dict()
        self._settings = dict()
        self._parameter_indexing_settings = dict()
        self._additional_parameter_indexing_domains = dict()
        self._database_urls = database_urls if database_urls is not None else list()
        self._database_to_file_name_map = database_to_file_name_map if database_to_file_name_map is not None else dict()
        if settings_file_names is not None:
            for file_name in settings_file_names:
                try:
                    with open(file_name) as input_file:
                        try:
                            data = json.load(input_file)
                            settings = data["settings"]
                            database_path = settings["database path"]
                            settings = gdx.Settings.from_dict(settings)
                            self._settings[database_path] = settings
                            parameter_indexing_settings = data.get("indexing settings", None)
                            if parameter_indexing_settings is not None:
                                database_map = DatabaseMapping(database_path)
                                for entity_class_name, entity in parameter_indexing_settings.items():
                                    entity_class = database_map.object_class_list.filter(
                                        database_map.object_class_sq.c.name == entity_class_name
                                    ).all()
                                    is_object = bool(entity_class)
                                    for entity_name, parameter in entity.items():
                                        for parameter_name, data in parameter.items():
                                            if is_object:
                                                data["value"] = from_database(
                                                    database_map.object_parameter_value_list(parameter_name).all()[0]
                                                )
                                            else:
                                                data["value"] = from_database(
                                                    database_map.relationship_parameter_value_list(
                                                        parameter_name
                                                    ).all()[0]
                                                )
                                database_map.connection.close()
                                self._parameter_indexing_settings[database_path] = parameter_indexing_settings
                        except (KeyError, json.JSONDecodeError):
                            self._toolbox.msg_warning.emit(
                                "Couldn't parse Exporter settings file {}. Skipping.".format(file_name)
                            )
                except FileNotFoundError:
                    self._toolbox.msg_error.emit("Exporter settings file {} not found. Skipping.".format(file_name))
        self._activated = False

    @staticmethod
    def item_type():
        """See base class."""
        return "Exporter"

    @staticmethod
    def category():
        """See base class."""
        return "Exporters"

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers."""
        s = {self._properties_ui.open_directory_button.clicked: self.open_directory}
        return s

    def activate(self):
        """Restores selections and connects signals."""
        self._properties_ui.item_name_label.setText(self.name)
        self.update_database_list()
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

    def update_database_list(self):
        """Updates the database list in the properties tab."""
        database_list_storage = self._properties_ui.databases_list_layout
        urls_already_in_items = list()
        for i in range(database_list_storage.count()):
            item_url = database_list_storage.itemAt(i).widget().url_field.text()
            if item_url not in self._database_urls:
                widget_to_remove = database_list_storage.takeAt(i)
                widget_to_remove.widget().file_name_changed.disconnect()
                widget_to_remove.widget().deleteLater()
            else:
                urls_already_in_items.append(item_url)
        for url in self._database_urls:
            if url in urls_already_in_items:
                continue
            file_name = self._database_to_file_name_map.get(url, "")
            item = ExportListItem(url, file_name)
            database_list_storage.insertWidget(0, item)
            # pylint: disable=cell-var-from-loop
            item.refresh_settings_clicked.connect(self._refresh_settings_for_database)
            item.open_settings_clicked.connect(self._show_settings)
            item.file_name_changed.connect(self._update_out_file_name)

    def execute_forward(self, resources):
        """See base class."""
        self._database_urls = [r.url for r in resources if r.type_ == "database"]
        gams_system_directory = self._resolve_gams_system_directory()
        if gams_system_directory is None:
            self._toolbox.msg_error.emit("<b>{}</b>: Cannot proceed. No GAMS installation found.".format(self.name))
            return False
        for url in self._database_urls:
            file_name = self._database_to_file_name_map.get(url, None)
            if file_name is None:
                self._toolbox.msg_error.emit(
                    "<b>{}</b>: No file name given to export database {}.".format(self.name, url)
                )
                return False
            database_map = DatabaseMapping(url)
            settings = self._settings.setdefault(url, gdx.make_settings(database_map))
            out_path = os.path.join(self.data_dir, file_name)
            indexing_settings = self._parameter_indexing_settings.get(url, dict())
            additional_domains = self._additional_parameter_indexing_domains.get(url, dict())
            gdx.to_gdx_file(
                database_map, out_path, additional_domains, settings, indexing_settings, gams_system_directory
            )
            database_map.connection.close()
            self._toolbox.msg_success.emit("File <b>{0}</b> written".format(out_path))
        return True

    def _do_handle_dag_changed(self, resources):
        """See base class."""
        self._database_urls = [r.url for r in resources if r.type_ == "database"]
        for mapped_database in list(self._database_to_file_name_map):
            if mapped_database not in self._database_urls:
                del self._database_to_file_name_map[mapped_database]
        files = self._database_to_file_name_map.values()
        notify_about_missing_output_file = False
        if "" in files:
            notify_about_missing_output_file = True
        else:
            for url in self._database_urls:
                if url not in self._database_to_file_name_map:
                    notify_about_missing_output_file = True
                    break
        if notify_about_missing_output_file:
            self.add_notification(Exporter._missing_output_file_notification)
        if self._activated:
            self.update_database_list()

    @Slot(str)
    def _show_settings(self, database_url):
        """Opens the item's settings window."""
        settings = self._settings.get(database_url, None)
        indexing_settings = self._parameter_indexing_settings.get(database_url, None)
        self._additional_parameter_indexing_domains.setdefault(database_url, list())
        if None in (settings, indexing_settings):
            database_map = DatabaseMapping(database_url)
            if settings is None:
                settings = gdx.make_settings(database_map)
                self._settings[database_url] = settings
            if indexing_settings is None:
                indexing_settings = gdx.make_indexing_settings(database_map)
                self._parameter_indexing_settings[database_url] = indexing_settings
            database_map.connection.close()
        # Give window its own settings and indexing domains so Cancel doesn't change anything here.
        settings = deepcopy(settings)
        indexing_settings = deepcopy(indexing_settings)
        settings_window = self._settings_windows.setdefault(
            database_url, GdxExportSettings(settings, indexing_settings, database_url, self._toolbox)
        )
        settings_window.settings_accepted.connect(self._update_settings_from_settings_window)
        settings_window.show()

    @Slot(str, str)
    def _update_out_file_name(self, file_name, database_path):
        """Updates the output file name for given database"""
        if file_name:
            self.clear_notifications()
        else:
            self.add_notification(Exporter._missing_output_file_notification)
        self._database_to_file_name_map[database_path] = file_name
        self.item_changed.emit()

    @Slot(str)
    def _update_settings_from_settings_window(self, database_path):
        """Updates the export settings for given database from the settings window."""
        settings_window = self._settings_windows[database_path]
        self._settings[database_path] = settings_window.settings
        self._parameter_indexing_settings[database_path] = settings_window.indexing_settings
        self._additional_parameter_indexing_domains[database_path] = settings_window.new_domains
        settings_window.hide()

    def item_dict(self):
        """Returns a dictionary corresponding to this item's configuration."""
        d = super().item_dict()
        d["database_to_file_name_map"] = self._database_to_file_name_map
        settings_file_names = self._save_settings()
        d["settings_file_names"] = settings_file_names
        return d

    def _save_settings(self):
        """Saves all export settings to .json files in the item's data directory."""
        file_names = list()
        for index, (database_path, settings) in enumerate(self._settings.items()):
            setting_set = dict()
            settings_dictionary = settings.to_dict()
            settings_dictionary["database path"] = database_path
            setting_set["settings"] = settings_dictionary
            indexing_domains = self._parameter_indexing_settings.get(database_path, None)
            if indexing_domains is not None:
                indexing_domains_dictionary = dict()
                for entity_class_name, entity in indexing_domains.items():
                    entity_dictionary = dict()
                    for entity_name, parameter in entity.items():
                        parameter_dictionary = dict()
                        for parameter_name, data in parameter.items():
                            parameter_dictionary[parameter_name] = {"indexing domain": data["indexing domain"]}
                        entity_dictionary[entity_class_name] = parameter_dictionary
                    indexing_domains_dictionary[entity_class_name] = entity_dictionary
                setting_set["indexing domains"] = indexing_domains_dictionary
            file_name = os.path.join(self.data_dir, "export_settings_{}.json".format(index + 1))
            with open(file_name, "w") as output_file:
                json.dump(setting_set, output_file, sort_keys=True, indent=4)
                file_names.append(file_name)
        return file_names

    def update_name_label(self):
        """See `ProjectItem.update_name_label()`."""
        self._properties_ui.item_name_label.setText(self.name)

    def _resolve_gams_system_directory(self):
        """Returns GAMS system path from Toolbox settings or None if GAMS default is to be used."""
        path = self._toolbox.qsettings().value("appSettings/gamsPath", defaultValue=None)
        if not path:
            path = gdx_utils.find_gams_directory()
        if path is not None and os.path.isfile(path):
            path = os.path.dirname(path)
        return path

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type() == "Data Store":
            self._toolbox.msg.emit(
                "Link established. Data Store <b>{0}</b> will be "
                "exported to a .gdx file by <b>{1}</b> when executing.".format(source_item.name, self.name)
            )
        else:
            super().notify_destination(source_item)

    @Slot(str)
    def _refresh_settings_for_database(self, url):
        """Refreshes database export settings after changes in database's structure/data."""
        original_settings = self._settings.get(url, None)
        database_map = DatabaseMapping(url)
        new_settings = gdx.make_settings(database_map)
        database_map.connection.close()
        if url in self._parameter_indexing_settings:
            del self._parameter_indexing_settings[url]
        if original_settings is None:
            self._settings[url] = new_settings
            return
        original_settings.update(new_settings)

    @staticmethod
    def default_name_prefix():
        """See base class."""
        return "Exporter"

    def output_resources_forward(self):
        """See base class."""
        files = self._database_to_file_name_map.values()
        paths = [os.path.join(self.data_dir, file_name) for file_name in files]
        resources = [ProjectItemResource(self, "file", url=pathlib.Path(path).as_uri()) for path in paths]
        return resources
