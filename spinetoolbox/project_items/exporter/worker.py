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
A worker based machinery to construct the settings data structures needed for gdx export outside the UI loop.

:author: A. Soininen (VTT)
:date:   19.12.2019
"""

from copy import deepcopy
from PySide2.QtCore import QObject, QThread, Signal, Slot
from spinedb_api import (
    apply_scenario_filter_to_parameter_value_sq,
    apply_alternative_filter_to_parameter_value_sq,
    DatabaseMapping,
    SpineDBAPIError,
)
from spinetoolbox.spine_io.exporters import gdx
from .db_utils import latest_database_commit_time_stamp


class Worker(QObject):
    """
    A worker to construct export settings for a database.

    Attributes:
        thread (QThread): the thread the worker executes in
    """

    database_unavailable = Signal(str)
    """Emitted when opening the database fails."""
    errored = Signal(str, object)
    """Emitted when an error occurs."""
    finished = Signal(str, object)
    """Emitted when the worker has finished."""
    # LoggerInterface signals
    msg = Signal(str, str)
    msg_warning = Signal(str, str)
    msg_error = Signal(str, str)

    def __init__(self, database_url, scenario, none_fallback):
        """
        Args:
            database_url (str): database's URL
            scenario (str, optional): scenario name or None if 'Base' alternative should be used
            none_fallback (NoneFallback): how to handle None parameter values
        """
        super().__init__()
        self.thread = QThread()
        self.moveToThread(self.thread)
        self._scenario = scenario
        self._none_fallback = none_fallback
        self._database_url = str(database_url)
        self._previous_settings = None
        self._previous_indexing_settings = None
        self._previous_merging_settings = None
        self.thread.started.connect(self._fetch_settings)

    @Slot()
    def _fetch_settings(self):
        """Constructs settings and parameter index settings."""
        result = _Result(*self._read_settings())
        if result.set_settings is None:
            return
        if self._previous_settings is not None:
            updated_settings = deepcopy(self._previous_settings)
            updated_settings.update(result.set_settings)
            updated_indexing_settings = self._update_indexing_settings(updated_settings, result.indexing_settings)
            if updated_indexing_settings is None:
                return
            updated_merging_settings = self._update_merging_settings(updated_settings)
            if updated_merging_settings is None:
                return
            result.set_settings = updated_settings
            result.indexing_settings = updated_indexing_settings
            result.merging_settings = updated_merging_settings
        self.finished.emit(self._database_url, result)
        self.thread.quit()

    def set_previous_settings(self, previous_settings, previous_indexing_settings, previous_merging_settings):
        """
        Makes worker update existing settings instead of just making new ones.

        Args:
            previous_settings (gdx.SetSettings): existing set settings
            previous_indexing_settings (dict): existing indexing settings
            previous_merging_settings (dict): existing merging settings
        """
        self._previous_settings = previous_settings
        self._previous_indexing_settings = previous_indexing_settings
        self._previous_merging_settings = previous_merging_settings

    @staticmethod
    def _read_scenarios(database_map):
        scenario_rows = database_map.query(database_map.scenario_sq).all()
        scenarios = {row.name: row.active for row in scenario_rows}
        return scenarios

    def _read_settings(self):
        """Reads fresh gdx settings from the database."""
        try:
            database_map = DatabaseMapping(self._database_url)
        except SpineDBAPIError:
            self.database_unavailable.emit(self._database_url)
            return None, None, None, None
        try:
            scenarios = self._read_scenarios(database_map)
            if self._scenario is not None and self._scenario not in scenarios:
                self.errored.emit(self._database_url, f"Scenario {self._scenario} not found.")
                return None, None, None, None
            if self._scenario is None:
                apply_alternative_filter_to_parameter_value_sq(database_map, ["Base"])
            else:
                apply_scenario_filter_to_parameter_value_sq(database_map, self._scenario)
        except SpineDBAPIError as error:
            self.errored.emit(self._database_url, error)
            return None, None, None, None
        try:
            time_stamp = latest_database_commit_time_stamp(database_map)
            settings = gdx.make_set_settings(database_map)
            logger = _Logger(self._database_url, self)
            indexing_settings = gdx.make_indexing_settings(database_map, self._none_fallback, logger)
        except gdx.GdxExportException as error:
            self.errored.emit(self._database_url, error)
            return None, None, None, None
        finally:
            database_map.connection.close()
        return time_stamp, settings, indexing_settings, scenarios

    def _update_indexing_settings(self, updated_settings, new_indexing_settings):
        """Updates the parameter indexing settings according to changes in the database."""
        updated_indexing_settings = gdx.update_indexing_settings(
            self._previous_indexing_settings, new_indexing_settings, updated_settings
        )
        return updated_indexing_settings

    def _update_merging_settings(self, updated_settings):
        """Updates the parameter merging settings according to changes in the database"""
        try:
            database_map = DatabaseMapping(self._database_url)
        except SpineDBAPIError as error:
            self.errored.emit(self._database_url, error)
            return None
        try:
            updated_merging_settings = gdx.update_merging_settings(
                self._previous_merging_settings, updated_settings, database_map
            )
        except gdx.GdxExportException as error:
            self.errored.emit(self._database_url, error)
            return None
        finally:
            database_map.connection.close()
        return updated_merging_settings


class _Result:
    """
    Contains fetched export settings.

    Attributes:
        commit_time_stamp (datetime): time of the database's last commit
        set_settings (gdx.SetSettings): gdx export settings
        indexing_settings (dict): parameter indexing settings
        merging_settings (dict): parameter merging settings
        scenarios (dict): map from scenario name to boolean 'active' flag
    """

    def __init__(self, time_stamp, set_settings, indexing_settings, scenarios):
        """
        Args:
            time_stamp (datetime): time of the database's last commit
            set_settings (gdx.SetSettings): gdx export settings
            indexing_settings (dict): parameter indexing settings
            scenarios (dict): map from scenario name to boolean 'active' flag
        """
        self.commit_time_stamp = time_stamp
        self.set_settings = set_settings
        self.indexing_settings = indexing_settings
        self.merging_settings = dict()
        self.scenarios = scenarios


class _Logger(QObject):
    """A ``LoggerInterface`` compliant logger that relays messages to :class:`Worker`'s signals."""

    msg = Signal(str)
    msg_warning = Signal(str)
    msg_error = Signal(str)

    def __init__(self, database_url, worker):
        """
        Args:
            database_url (str): a database url
            worker (Worker): a worker
        """
        super().__init__()
        self._url = database_url
        self._worker = worker
        self.msg.connect(self.relay_message)
        self.msg_warning.connect(self.relay_warning)
        self.msg_error.connect(self.relay_error)

    @Slot(str)
    def relay_message(self, text):
        self._worker.msg.emit(self._url, text)

    @Slot(str)
    def relay_warning(self, text):
        self._worker.msg_warning.emit(self._url, text)

    @Slot(str)
    def relay_error(self, text):
        self._worker.msg_error.emit(self._url, text)
