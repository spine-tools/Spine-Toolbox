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
from spinedb_api import DatabaseMapping, SpineDBAPIError
from spinetoolbox.spine_io.exporters import gdx
from .db_utils import latest_database_commit_time_stamp


class Worker(QObject):
    """
    A worker to construct export settings for a database.

    Attributes:
        signals: contains signals that the worker may emit during its execution
    """

    database_unavailable = Signal(str)
    """Emitted when opening the database fails."""
    errored = Signal(str, "QVariant")
    """Emitted when an error occurs."""
    finished = Signal(str, "QVariant")
    """Emitted when the worker has finished."""
    # LoggerInterface signals
    msg = Signal(str, str)
    msg_warning = Signal(str, str)
    msg_error = Signal(str, str)

    def __init__(self, database_url):
        """
        Args:
            database_url (str): database's URL
        """
        super().__init__()
        self.thread = QThread()
        self.moveToThread(self.thread)
        self._database_url = str(database_url)
        self._previous_settings = None
        self._previous_indexing_settings = None
        self._previous_indexing_domains = None
        self._previous_merging_settings = None
        self.thread.started.connect(self.fetch_settings)
        self.thread.finished.connect(self.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    @Slot()
    def fetch_settings(self):
        """Constructs settings and parameter index settings."""
        result = _Result(*self._read_settings())
        if result.set_settings is None:
            return
        if self._previous_settings is not None:
            updated_settings = deepcopy(self._previous_settings)
            updated_settings.update(result.set_settings)
            updated_indexing_settings, updated_indexing_domains = self._update_indexing_settings(
                updated_settings, result.indexing_settings
            )
            if updated_indexing_settings is None:
                return
            updated_merging_settings, updated_merging_domains = self._update_merging_settings(updated_settings)
            if updated_merging_settings is None:
                return
            result.set_settings = updated_settings
            result.indexing_settings = updated_indexing_settings
            result.indexing_domains = updated_indexing_domains
            result.merging_settings = updated_merging_settings
            result.merging_domains = updated_merging_domains
        self.finished.emit(self._database_url, result)
        self.thread.quit()

    def set_previous_settings(
        self, previous_settings, previous_indexing_settings, previous_indexing_domains, previous_merging_settings
    ):
        """
        Makes worker update existing settings instead of just making new ones.

        Args:
            previous_settings (gdx.SetSettings): existing set settings
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
            self.signals.database_unavailable.emit(self._database_url, self._cookie)
            return None, None, None
        try:
            time_stamp = latest_database_commit_time_stamp(database_map)
            settings = gdx.make_set_settings(database_map)
            logger = _Logger(self._database_url, self)
            indexing_settings = gdx.make_indexing_settings(database_map, logger)
        except gdx.GdxExportException as error:
            self.signals.errored.emit(self._database_url, self._cookie, error)
            return None, None, None
        finally:
            database_map.connection.close()
        return time_stamp, settings, indexing_settings

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
            self.signals.errored.emit(self._database_url, self._cookie, error)
            return None, None
        try:
            updated_merging_settings = gdx.update_merging_settings(
                self._previous_merging_settings, updated_settings, database_map
            )
        except gdx.GdxExportException as error:
            self.signals.errored.emit(self._database_url, self._cookie, error)
            return None, None
        finally:
            database_map.connection.close()
        updated_merging_domains = list(map(gdx.merging_domain, updated_merging_settings.values()))
        for domain in updated_merging_domains:
            metadata = gdx.SetMetadata(gdx.ExportFlag.FORCED_EXPORTABLE, True)
            updated_settings.add_or_replace_domain(domain, metadata)
        return updated_merging_settings, updated_merging_domains


class _Result:
    """
    Contains fetched export settings.

    Attributes:
        commit_time_stamp (datetime): time of the database's last commit
        set_settings (gdx.SetSettings): gdx export settings
        indexing_settings (dict): parameter indexing settings
        indexing_domains (list): additional domains needed for parameter indexing
        merging_settings (dict): parameter merging settings
        merging_domains (list): additional domains needed for parameter merging
    """

    def __init__(self, time_stamp, set_settings, indexing_settings):
        """
        Args:
            time_stamp (datetime): time of the database's last commit
            set_settings (gdx.SetSettings): gdx export settings
            indexing_settings (dict): parameter indexing settings
        """
        self.commit_time_stamp = time_stamp
        self.set_settings = set_settings
        self.indexing_settings = indexing_settings
        self.indexing_domains = list()
        self.merging_settings = dict()
        self.merging_domains = list()


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
