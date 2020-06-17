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
Contains importer_program script.

:authors: P. Savolainen (VTT), P. Vennström (VTT), A. Soininen (VTT)
:date:   10.6.2019
"""

import os
from PySide2.QtCore import QObject, Signal, Slot
import spinedb_api
from spinetoolbox.spine_io.importers.csv_reader import CSVConnector
from spinetoolbox.spine_io.importers.excel_reader import ExcelConnector
from spinetoolbox.spine_io.importers.gdx_connector import GdxConnector
from spinetoolbox.spine_io.importers.json_reader import JSONConnector
from spinetoolbox.spine_io.type_conversion import value_to_convert_spec
from ..shared.helpers import create_log_file_timestamp


class ImporterWorker(QObject):

    finished = Signal(int)
    """Emitted when work is finished with 0 if successful, -1 otherwise."""

    def __init__(
        self,
        checked_files,
        all_import_settings,
        all_source_settings,
        urls_downstream,
        logs_dir,
        cancel_on_error,
        logger,
    ):
        """
        Args:
            checked_files (list(str)): List of paths to checked source files
            all_import_settings (dict): Maps source file to setting for that file
            all_source_settings (dict): Maps source type to setting for that type
            urls_downstream (list(str)): List of urls to import data into
            logs_dir (str): path to the directory where logs should be written
            cancel_on_error (bool): whether or not to rollback and stop execution if errors
            logger (LoggerInterface): somewhere to log important messages
        """
        super().__init__()
        self._checked_files = checked_files
        self._all_import_settings = all_import_settings
        self._all_source_settings = all_source_settings
        self._urls_downstream = urls_downstream
        self._logs_dir = logs_dir
        self._cancel_on_error = cancel_on_error
        self._logger = logger

    @Slot()
    def run(self):
        """Does the work and emits finished or failed when done.
        """
        all_data = []
        all_errors = []
        for source in self._checked_files:
            settings = self._all_import_settings.get(source, None)
            if settings == "deselected":
                continue
            if settings is None or not settings:
                self._logger.msg_warning.emit(f"There are no mappings defined for {source}, moving on...")
                continue
            source_type = settings["source_type"]
            source_settings = self._all_source_settings.get(source_type)
            connector = {
                "CSVConnector": CSVConnector,
                "ExcelConnector": ExcelConnector,
                "GdxConnector": GdxConnector,
                "JSONConnector": JSONConnector,
            }[source_type](source_settings)
            try:
                connector.connect_to_source(source)
            except IOError as error:
                self._logger.msg_error.emit(f"Failed to connect to source: {error}")
                self.finished.emit(-1)
            table_mappings = {
                name: mapping
                for name, mapping in settings.get("table_mappings", {}).items()
                if name in settings["selected_tables"]
            }
            table_options = {
                name: options
                for name, options in settings.get("table_options", {}).items()
                if name in settings["selected_tables"]
            }

            table_types = {
                tn: {int(col): value_to_convert_spec(spec) for col, spec in cols.items()}
                for tn, cols in settings.get("table_types", {}).items()
            }
            table_row_types = {
                tn: {int(col): value_to_convert_spec(spec) for col, spec in cols.items()}
                for tn, cols in settings.get("table_row_types", {}).items()
            }
            try:
                data, errors = connector.get_mapped_data(
                    table_mappings, table_options, table_types, table_row_types, max_rows=-1
                )
            except spinedb_api.InvalidMapping as error:
                self._logger.msg_error.emit(f"Failed to import '{source}': {error}")
                if self._cancel_on_error:
                    self.finished.emit(-1)
                else:
                    continue
            self._logger.msg_success.emit(
                f"Read {sum(len(d) for d in data.values())} data from {source} with {len(errors)} errors"
            )
            all_data.append(data)
            all_errors.extend(errors)
        if all_errors:
            # Log errors in a time stamped file into the logs directory
            timestamp = create_log_file_timestamp()
            logfilepath = os.path.abspath(os.path.join(self._logs_dir, timestamp + "_error.log"))
            with open(logfilepath, 'w') as f:
                for err in all_errors:
                    f.write(f"{err}\n")
            # Make error log file anchor with path as tooltip
            logfile_anchor = (
                "<a style='color:#BB99FF;' title='" + logfilepath + "' href='file:///" + logfilepath + "'>error log</a>"
            )

            self._logger.msg_error("Import errors. Logfile: {0}".format(logfile_anchor))
            if self._cancel_on_error:
                self.finished.emit(-1)
        if all_data:
            for url in self._urls_downstream:
                self._import(all_data, url)
        self.finished.emit(0)

    def _import(self, all_data, url):
        try:
            db_map = spinedb_api.DiffDatabaseMapping(url, upgrade=False, username="Mapper")
        except (spinedb_api.SpineDBAPIError, spinedb_api.SpineDBVersionError) as err:
            self._logger.msg_error(
                "Unable to create database mapping, all import operations will be omitted: {0}".format(err)
            )
            return
        all_import_errors = []
        for data in all_data:
            import_num, import_errors = spinedb_api.import_data(db_map, **data)
            all_import_errors += import_errors
            if import_errors and self._cancel_on_error:
                if db_map.has_pending_changes():
                    db_map.rollback_session()
            elif import_num:
                db_map.commit_session("Import data by Spine Toolbox Importer")
                self._logger.msg_success(
                    "Inserted {0} data with {1} errors into {2}".format(import_num, len(import_errors), url)
                )
        db_map.connection.close()
        if all_import_errors:
            # Log errors in a time stamped file into the logs directory
            timestamp = create_log_file_timestamp()
            logfilepath = os.path.abspath(os.path.join(self._logs_dir, timestamp + "_error.log"))
            with open(logfilepath, 'w') as f:
                for err in all_import_errors:
                    f.write("{0}\n".format(err.msg))
            # Make error log file anchor with path as tooltip
            logfile_anchor = (
                "<a style='color:#BB99FF;' title='" + logfilepath + "' href='file:///" + logfilepath + "'>error log</a>"
            )
            rollback_text = ", rolling back" if self._cancel_on_error else ""
            self._logger.msg_error("Import errors{0}. Logfile: {1}".format(rollback_text, logfile_anchor))
