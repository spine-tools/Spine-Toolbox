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
Contains the SettingsPack class.

:author: A. Soininen (VTT)
:date:   6.5.2020
"""
import dateutil.parser
from PySide2.QtCore import QObject, Signal, Slot
from spinedb_api import SpineDBAPIError
from spinetoolbox.spine_io.exporters import gdx
from .db_utils import scenario_filtered_database_map
from .notifications import Notifications
from .settings_state import SettingsState


class SettingsPack(QObject):
    """
    Keeper of all settings and stuff needed for exporting a database.

    Attributes:
        output_file_name (str): name of the export file
        settings (gdx.SetSettings): export settings
        indexing_settings (dict): parameter indexing settings
        merging_settings (dict): parameter merging settings
        none_fallback (NoneFallback): fallback for None parameter values
        none_export (NoneExport): how to handle None values while exporting
        scenario (str): name of the scenario to export; None for 'Base' alternative
        last_database_commit (datetime): latest database commit time stamp
        settings_window (GdxExportSettings): settings editor window
    """

    state_changed = Signal(object)
    """Emitted when the pack's state changes."""

    def __init__(self, output_file_name):
        """
        Args:
            output_file_name (str): name of the export file
        """
        super().__init__()
        self.output_file_name = output_file_name
        self.settings = None
        self.indexing_settings = None
        self.merging_settings = dict()
        self.none_fallback = gdx.NoneFallback.USE_IT
        self.none_export = gdx.NoneExport.DO_NOT_EXPORT
        self.scenario = None
        self.last_database_commit = None
        self.settings_window = None
        self._state = SettingsState.FETCHING
        self.notifications = Notifications()
        self.state_changed.connect(self.notifications.update_settings_state)

    @property
    def state(self):
        """State of the pack."""
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        self.state_changed.emit(state)

    def to_dict(self):
        """Stores the settings pack into a JSON compatible dictionary."""
        d = dict()
        d["output_file_name"] = self.output_file_name
        # Override ERROR by FETCHING so we'll retry reading the database when reopening the project.
        d["state"] = self.state.value
        if self.state not in (SettingsState.OK, SettingsState.INDEXING_PROBLEM):
            return d
        d["settings"] = self.settings.to_dict()
        d["indexing_settings"] = gdx.indexing_settings_to_dict(self.indexing_settings)
        d["merging_settings"] = {
            parameter_name: setting.to_dict() for parameter_name, setting in self.merging_settings.items()
        }
        d["none_fallback"] = self.none_fallback.value
        d["none_export"] = self.none_export.value
        d["scenario"] = self.scenario
        d["latest_database_commit"] = (
            self.last_database_commit.isoformat() if self.last_database_commit is not None else None
        )
        return d

    @staticmethod
    def from_dict(pack_dict, database_url, logger):
        """Restores the settings pack from a dictionary."""
        pack = SettingsPack(pack_dict["output_file_name"])
        pack.state = SettingsState(pack_dict["state"])
        if pack.state not in (SettingsState.OK, SettingsState.INDEXING_PROBLEM):
            return pack
        value = pack_dict.get("none_fallback")
        if value is not None:
            pack.none_fallback = gdx.NoneFallback(value)
        value = pack_dict.get("none_export")
        if value is not None:
            pack.none_export = gdx.NoneExport(value)
        try:
            pack.settings = gdx.SetSettings.from_dict(pack_dict["settings"])
        except gdx.GdxExportException as error:
            logger.msg_error.emit(f"Failed to fully restore Exporter settings: {error}")
            return pack
        pack.scenario = pack_dict.get("scenario")
        try:
            db_map = scenario_filtered_database_map(database_url, pack.scenario)
            value_type_logger = _UnsupportedValueTypeLogger(
                f"Exporter settings ignoring some parameters from database '{database_url}':", logger
            )
            pack.indexing_settings = gdx.indexing_settings_from_dict(
                pack_dict["indexing_settings"], db_map, pack.none_fallback, value_type_logger
            )
        except SpineDBAPIError as error:
            logger.msg_error.emit(
                f"Failed to fully restore Exporter settings. Error while reading database '{database_url}': {error}"
            )
            pack.state = SettingsState.ERROR
            return pack
        else:
            db_map.connection.close()
        pack.merging_settings = {
            parameter_name: gdx.MergingSetting.from_dict(setting_dict)
            for parameter_name, setting_dict in pack_dict["merging_settings"].items()
        }
        latest_commit = pack_dict.get("latest_database_commit")
        if latest_commit is not None:
            try:
                pack.last_database_commit = dateutil.parser.parse(latest_commit)
            except ValueError as error:
                logger.msg_error.emit(f"Failed to read latest database commit: {error}")
        return pack


class _UnsupportedValueTypeLogger(QObject):
    msg = Signal(str)
    msg_warning = Signal(str)
    msg_error = Signal(str)

    def __init__(self, preample, real_logger):
        super().__init__()
        self._preample = preample
        self._logger = real_logger
        self.msg.connect(self.relay_message)
        self.msg_warning.connect(self.relay_warning)
        self.msg_error.connect(self.relay_error)

    @Slot(str)
    def relay_message(self, text):
        self._logger.msg.emit(self._preample + " " + text)

    @Slot(str)
    def relay_warning(self, text):
        self._logger.msg_warning.emit(self._preample + " " + text)

    @Slot(str)
    def relay_error(self, text):
        self._logger.msg_error.emit(self._preample + " " + text)
