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
Contains ExporterExecutable, an Exporter's counterpart in execution as well as support utilities.

:authors: A. Soininen (VTT)
:date:   2.4.2020
"""
import os.path
import pathlib
from spinedb_api import DatabaseMapping, SpineDBAPIError
from spinetoolbox.executable_item import ExecutableItem
from spinetoolbox.project_item import ProjectItemResource
from spinetoolbox.spine_io import gdx_utils
from spinetoolbox.spine_io.exporters import gdx
from .settings_state import SettingsState


class ExporterExecutable(ExecutableItem):
    def __init__(self, name, settings_packs, data_dir, gams_path, logger):
        """
        Args:
            name (str): item's name
            settings_packs (dict): mapping from database URLs to SettingsPacks
            data_dir (str): absolute path to exporter's data directory
            gams_path (str): GAMS path from Toolbox settings
            logger (LoggerInterface): a logger
        """
        super().__init__(name, logger)
        self._settings_packs = settings_packs
        self._data_dir = data_dir
        self._gams_path = gams_path

    @staticmethod
    def item_type():
        """Returns Exporter's type identifier string."""
        return "Exporter"

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
                database_map = DatabaseMapping(url)
            except SpineDBAPIError as error:
                self._logger.msg_error.emit(f"Failed to export <b>{url}</b> to .gdx: {error}")
                return False
            try:
                gdx.to_gdx_file(
                    database_map,
                    out_path,
                    settings_pack.indexing_domains + settings_pack.merging_domains,
                    settings_pack.settings,
                    settings_pack.indexing_settings,
                    settings_pack.merging_settings,
                    gams_system_directory,
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
        files = [pack.output_file_name for pack in self._settings_packs.values()]
        paths = [os.path.join(self._data_dir, file_name) for file_name in files]
        resources = [ProjectItemResource(self, "file", url=pathlib.Path(path).as_uri()) for path in paths]
        return resources

    def _resolve_gams_system_directory(self):
        """Returns GAMS system path from Toolbox settings or None if GAMS default is to be used."""
        path = self._gams_path
        if not path:
            path = gdx_utils.find_gams_directory()
        if path is not None and os.path.isfile(path):
            path = os.path.dirname(path)
        return path
