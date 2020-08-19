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
Contains Combiner program.

:authors: M. Marin (KTH)
:date:   12.5.2020
"""

import sys
import os
from PySide2.QtCore import QObject, Signal, Slot
from spinedb_api import export_data, import_data, SpineDBAPIError, SpineDBVersionError, DiffDatabaseMapping
from ..shared.helpers import create_log_file_timestamp


class CombinerWorker(QObject):

    finished = Signal()

    def __init__(self, from_urls, to_urls, logs_dir, cancel_on_error, logger):
        """
        Args:
            from_urls (list(str)): list of urls to read data from
            to_urls (list(str)): list of urls to write data into
            logs_dir (str): path to the directory where logs should be written
            cancel_on_error (bool): whether or not to rollback and stop execution if errors
            logger (LoggerInterface): somewhere to log important messages
        """
        super().__init__()
        self._from_urls = from_urls
        self._to_urls = to_urls
        self._logs_dir = logs_dir
        self._cancel_on_error = cancel_on_error
        self._logger = logger

    def _get_db_map(self, url):
        try:
            db_map = DiffDatabaseMapping(url)
        except (SpineDBAPIError, SpineDBVersionError) as err:
            self._logger.msg_error.emit(f"Skipping url <b>{url}</b>: {err}")
            return None
        return db_map

    @Slot()
    def do_work(self):
        """Does the work and emits finished when done."""
        from_db_maps = [db_map for db_map in (self._get_db_map(url) for url in self._from_urls) if db_map]
        to_db_maps = [db_map for db_map in (self._get_db_map(url) for url in self._to_urls) if db_map]
        from_db_map_data = {from_db_map: export_data(from_db_map) for from_db_map in from_db_maps}
        all_errors = []
        for to_db_map in to_db_maps:
            to_db_map_import_count = 0
            to_db_map_error_count = 0
            for from_db_map, data in from_db_map_data.items():
                import_count, import_errors = import_data(to_db_map, **data)
                all_errors += import_errors
                if import_errors and self._cancel_on_error:
                    if to_db_map.has_pending_changes():
                        to_db_map.rollback_session()
                elif import_count:
                    to_db_map.commit_session(
                        f"Import {import_count} items from {from_db_map.db_url} by Spine Toolbox Combiner"
                    )
                to_db_map_import_count += import_count
                to_db_map_error_count += len(import_errors)
            self._logger.msg_success.emit(
                "Merged {0} data with {1} errors into {2}".format(
                    to_db_map_import_count, to_db_map_error_count, to_db_map.db_url
                )
            )
        for db_map in from_db_maps + to_db_maps:
            db_map.connection.close()
        if all_errors:
            # Log errors in a time stamped file into the logs directory
            timestamp = create_log_file_timestamp()
            logfilepath = os.path.abspath(os.path.join(self._logs_dir, timestamp + "_error.log"))
            with open(logfilepath, 'w') as f:
                for err in all_errors:
                    f.write("{0}\n".format(err))
            # Make error log file anchor with path as tooltip
            logfile_anchor = (
                "<a style='color:#BB99FF;' title='" + logfilepath + "' href='file:///" + logfilepath + "'>error log</a>"
            )

            self._logger.msg_error.emit("Import errors. Logfile: {0}".format(logfile_anchor), file=sys.stderr)
        self.finished.emit()
