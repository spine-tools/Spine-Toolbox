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
from PySide2.QtCore import QObject, QRunnable, Signal
from spinedb_api import DatabaseMapping, SpineDBAPIError
from spinetoolbox.spine_io.exporters import gdx
from .db_utils import latest_database_commit_time_stamp


class Worker(QRunnable):
    """
    A worker to construct export settings for a database.

    Attributes:
        signals: contains signals that the worker may emit during its execution
    """

    def __init__(self, database_url):
        """
        Args:
            database_url (str): database's URL
        """
        super().__init__()
        self.signals = _Signals()
        self._database_url = str(database_url)
        self._previous_settings = None
        self._previous_indexing_settings = None
        self._previous_indexing_domains = None
        self._previous_merging_settings = None

    def reset_previous_settings(self):
        """Makes worker send new settings instead of updating old ones."""
        self._previous_settings = None
        self._previous_indexing_settings = None
        self._previous_indexing_domains = None
        self._previous_merging_settings = None

    def run(self):
        """Constructs settings and parameter index settings and sends them to interested parties using signals."""
        settings, indexing_settings, time_stamp = self._read_settings()
        if settings is None:
            return
        if self._previous_settings is not None:
            updated_settings = deepcopy(self._previous_settings)
            updated_settings.update(settings)
            updated_indexing_settings, updated_indexing_domains = self._update_indexing_settings(
                updated_settings, indexing_settings
            )
            if updated_indexing_settings is None:
                return
            updated_merging_settings, updated_merging_domains = self._update_merging_settings(updated_settings)
            if updated_merging_settings is None:
                return
            self.signals.time_stamp_read.emit(self._database_url, time_stamp)
            self.signals.settings_read.emit(self._database_url, updated_settings)
            self.signals.indexing_settings_read.emit(self._database_url, updated_indexing_settings)
            self.signals.indexing_domains_read.emit(self._database_url, updated_indexing_domains)
            self.signals.merging_settings_read.emit(self._database_url, updated_merging_settings)
            self.signals.merging_domains_read.emit(self._database_url, updated_merging_domains)
            self.signals.finished.emit(self._database_url)
            return
        self.signals.time_stamp_read.emit(self._database_url, time_stamp)
        self.signals.settings_read.emit(self._database_url, settings)
        self.signals.indexing_settings_read.emit(self._database_url, indexing_settings)
        self.signals.indexing_domains_read.emit(self._database_url, list())
        self.signals.finished.emit(self._database_url)

    def set_previous_settings(
        self, previous_settings, previous_indexing_settings, previous_indexing_domains, previous_merging_settings
    ):
        """
        Makes worker update existing settings instead of just making new ones.

        Args:
            previous_settings (Settings): existing settings
            previous_indexing_settings (dict): existing indexing settings
            previous_indexing_domains (list) existing indexing domains
            previous_merging_settings (dict): existing merging settings
        """
        self._previous_settings = previous_settings
        self._previous_indexing_settings = previous_indexing_settings
        self._previous_indexing_domains = previous_indexing_domains
        self._previous_merging_settings = previous_merging_settings

    def _read_settings(self):
        """Reads fresh gdx settings from the database."""
        try:
            database_map = DatabaseMapping(self._database_url)
        except SpineDBAPIError as error:
            self.signals.errored.emit(self._database_url, error)
            return None, None
        try:
            time_stamp = latest_database_commit_time_stamp(database_map)
            settings = gdx.make_settings(database_map)
            indexing_settings = gdx.make_indexing_settings(database_map)
        except gdx.GdxExportException as error:
            self.signals.errored.emit(self._database_url, error)
            return None, None
        finally:
            database_map.connection.close()
        return settings, indexing_settings, time_stamp

    def _update_indexing_settings(self, updated_settings, new_indexing_settings):
        """Updates the parameter indexing settings according to changes in the database."""
        updated_indexing_settings = gdx.update_indexing_settings(
            self._previous_indexing_settings, new_indexing_settings, updated_settings
        )
        indexing_domain_names = list()
        for indexing_setting in updated_indexing_settings.values():
            if indexing_setting.indexing_domain is not None:
                indexing_domain_names.append(indexing_setting.indexing_domain.name)
        updated_indexing_domains = [
            domain for domain in self._previous_indexing_domains if domain.name in indexing_domain_names
        ]
        for indexing_domain in updated_indexing_domains:
            metadata = gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True)
            updated_settings.add_or_replace_domain(indexing_domain, metadata)
        return updated_indexing_settings, updated_indexing_domains

    def _update_merging_settings(self, updated_settings):
        """Updates the parameter merging settings according to changes in the database"""
        try:
            database_map = DatabaseMapping(self._database_url)
        except SpineDBAPIError as error:
            self.signals.errored.emit(self._database_url, error)
            return None, None
        try:
            updated_merging_settings = gdx.update_merging_settings(
                self._previous_merging_settings, updated_settings, database_map
            )
        except gdx.GdxExportException as error:
            self.signals.errored.emit(self._database_url, error)
            return None, None
        finally:
            database_map.connection.close()
        updated_merging_domains = list(map(gdx.merging_domain, updated_merging_settings.values()))
        for domain in updated_merging_domains:
            metadata = gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True)
            updated_settings.add_or_replace_domain(domain, metadata)
        return updated_merging_settings, updated_merging_domains


class _Signals(QObject):
    """Signals which the Worker emits during its execution."""

    errored = Signal(str, "QVariant")
    """Emitted when an error occurs."""
    finished = Signal(str)
    """Emitted when the worker has finished."""
    indexing_domains_read = Signal(str, "QVariant")
    """Sends new additional domains away."""
    indexing_settings_read = Signal(str, "QVariant")
    """Sends the indexing settings away."""
    merging_settings_read = Signal(str, "QVariant")
    """Sends updated merging settings away."""
    merging_domains_read = Signal(str, "QVariant")
    """Sends updated merging domains away."""
    settings_read = Signal(str, "QVariant")
    """Sends the settings away."""
    time_stamp_read = Signal(str, "QVariant")
    """Emits latest time stamp of database commits."""
