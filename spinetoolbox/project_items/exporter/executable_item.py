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
Contains Exporter's executable item as well as support utilities.

:authors: A. Soininen (VTT)
:date:   2.4.2020
"""
import os.path
import pathlib
from spinedb_api import SpineDBAPIError
from spinetoolbox.executable_item_base import ExecutableItemBase
from spinetoolbox.helpers import deserialize_path, shorten
from spinetoolbox.project_item_resource import ProjectItemResource
from spinetoolbox.spine_io import gdx_utils
from spinetoolbox.spine_io.exporters import gdx
from .db_utils import scenario_filtered_database_map
from .item_info import ItemInfo
from .settings_pack import SettingsPack
from .settings_state import SettingsState


class ExecutableItem(ExecutableItemBase):
    def __init__(self, name, settings_packs, cancel_on_error, data_dir, gams_path, logger):
        """
        Args:
            name (str): item's name
            settings_packs (dict): mapping from database URLs to SettingsPacks
            cancel_on_error (bool): True if execution should fail on all errors, False if certain errors can be ignored
            data_dir (str): absolute path to exporter's data directory
            gams_path (str): GAMS path from Toolbox settings
            logger (LoggerInterface): a logger
        """
        super().__init__(name, logger)
        self._settings_packs = settings_packs
        self._cancel_on_error = cancel_on_error
        self._data_dir = data_dir
        self._gams_path = gams_path

    @staticmethod
    def item_type():
        """Returns Exporter's type identifier string."""
        return ItemInfo.item_type()

    def _execute_forward(self, resources):
        """See base class."""
        database_urls = [r.url for r in resources if r.type_ == "database"]
        gams_system_directory = self._resolve_gams_system_directory()
        if gams_system_directory is None:
            self._logger.msg_error.emit(f"<b>{self.name}</b>: Cannot proceed. No GAMS installation found.")
            return False
        for url in database_urls:
            settings_pack = self._settings_packs.get(url, None)
            if settings_pack is None:
                self._logger.msg_error.emit(f"<b>{self.name}</b>: No export settings defined for database {url}.")
                return False
            if not settings_pack.output_file_name:
                self._logger.msg_error.emit(f"<b>{self.name}</b>: No file name given to export database {url}.")
                return False
            if settings_pack.state == SettingsState.FETCHING:
                self._logger.msg_error.emit(f"<b>{self.name}</b>: Settings not ready for database {url}.")
                return False
            if settings_pack.state == SettingsState.INDEXING_PROBLEM:
                self._logger.msg_error.emit(
                    f"<b>{self.name}</b>: Parameters missing indexing information for database {url}."
                )
                return False
            if settings_pack.state == SettingsState.ERROR:
                self._logger.msg_error.emit(f"<b>{self.name}</b>: Ill formed database {url}.")
                return False
            out_path = os.path.join(self._data_dir, settings_pack.output_file_name)
            try:
                database_map = scenario_filtered_database_map(url, settings_pack.scenario)
            except SpineDBAPIError as error:
                self._logger.msg_error.emit(f"Failed to export <b>{url}</b> to .gdx: {error}")
                return
            export_logger = self._logger if not self._cancel_on_error else None
            try:
                gdx.to_gdx_file(
                    database_map,
                    out_path,
                    settings_pack.settings,
                    settings_pack.indexing_settings,
                    settings_pack.merging_settings,
                    settings_pack.none_fallback,
                    settings_pack.none_export,
                    gams_system_directory,
                    export_logger,
                )
            except gdx.GdxExportException as error:
                self._logger.msg_error.emit(f"Failed to export <b>{url}</b> to .gdx: {error}")
                return False
            finally:
                database_map.connection.close()
            self._logger.msg_success.emit(f"File <b>{out_path}</b> written")
        return True

    def _output_resources_forward(self):
        """See base class."""
        resources = [
            ProjectItemResource(
                self,
                "transient_file",
                pathlib.Path(self._data_dir, pack.output_file_name).as_uri(),
                {"label": pack.output_file_name},
            )
            for pack in self._settings_packs.values()
        ]
        return resources

    def _resolve_gams_system_directory(self):
        """Returns GAMS system path from Toolbox settings or None if GAMS default is to be used."""
        path = self._gams_path
        if not path:
            path = gdx_utils.find_gams_directory()
        if path is not None and os.path.isfile(path):
            path = os.path.dirname(path)
        return path

    @classmethod
    def from_dict(cls, item_dict, name, project_dir, app_settings, specifications, logger):
        """See base class."""
        settings_packs = dict()
        for pack_dict in item_dict["settings_packs"]:
            serialized_url = pack_dict["database_url"]
            url = deserialize_path(serialized_url, project_dir)
            try:
                settings_pack = SettingsPack.from_dict(pack_dict, url, logger)
            except gdx.GdxExportException as error:
                logger.msg_error.emit(f"Failed to fully restore Exporter settings: {error}")
                settings_pack = SettingsPack("")
            settings_packs[url] = settings_pack
        cancel_on_error = item_dict.get("cancel_on_error")
        if cancel_on_error is None:
            cancel_on_error = True
        data_dir = pathlib.Path(project_dir, ".spinetoolbox", "items", shorten(name))
        gams_path = app_settings.value("appSettings/gamsPath", defaultValue=None)
        return cls(name, settings_packs, cancel_on_error, data_dir, gams_path, logger)
