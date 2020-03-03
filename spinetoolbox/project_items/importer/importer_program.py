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
Contains Importer project item class.

:authors: P. Savolainen (VTT), P. Vennström (VTT), A. Soininen (VTT)
:date:   10.6.2019
"""

import io
import sys
import os
import json
import datetime
import time
import spinedb_api
from spinetoolbox.spine_io.importers.csv_reader import CSVConnector
from spinetoolbox.spine_io.importers.excel_reader import ExcelConnector
from spinetoolbox.spine_io.importers.gdx_connector import GdxConnector
from spinetoolbox.spine_io.importers.json_reader import JSONConnector
from spinetoolbox.spine_io.type_conversion import value_to_convert_spec


def _create_log_file_timestamp():
    """Creates a new timestamp string that is used as Importer and Data Store error log file.

    Returns:
        Timestamp string or empty string if failed.
    """
    try:
        # Create timestamp
        stamp = datetime.datetime.fromtimestamp(time.time())
    except OverflowError:
        return ''
    extension = stamp.strftime('%Y%m%dT%H%M%S')
    return extension


def run(checked_files, all_settings, urls_downstream, logs_dir, cancel_on_error):
    all_data = []
    all_errors = []
    for source in checked_files:
        settings = all_settings.get(source, None)
        if settings is None or not settings:
            print("There are no mappings defined for {0}, moving on...".format(source))
            continue
        source_type = settings["source_type"]
        connector = {
            "CSVConnector": CSVConnector,
            "ExcelConnector": ExcelConnector,
            "GdxConnector": GdxConnector,
            "JSONConnector": JSONConnector,
        }[source_type]()
        connector.connect_to_source(source)
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
        data, errors = connector.get_mapped_data(
            table_mappings, table_options, table_types, table_row_types, max_rows=-1
        )
        print("Read {0} data from {1} with {2} errors".format(sum(len(d) for d in data.values()), source, len(errors)))
        all_data.append(data)
        all_errors.extend(errors)
    if all_errors:
        # Log errors in a time stamped file into the logs directory
        timestamp = _create_log_file_timestamp()
        logfilepath = os.path.abspath(os.path.join(logs_dir, timestamp + "_error.log"))
        with open(logfilepath, 'w') as f:
            for err in all_errors:
                f.write("{0}\n".format(err))
        # Make error log file anchor with path as tooltip
        logfile_anchor = (
            "<a style='color:#BB99FF;' title='" + logfilepath + "' href='file:///" + logfilepath + "'>error log</a>"
        )

        print("Import errors. Logfile: {0}".format(logfile_anchor), file=sys.stderr)
        if cancel_on_error:
            sys.exit(-1)
    if all_data:
        for url in urls_downstream:
            _import(all_data, url, logs_dir, cancel_on_error)


def _import(all_data, url, logs_dir, cancel_on_error):
    try:
        db_map = spinedb_api.DiffDatabaseMapping(url, upgrade=False, username="Mapper")
    except (spinedb_api.SpineDBAPIError, spinedb_api.SpineDBVersionError) as err:
        print("Unable to create database mapping, all import operations will be omitted: {0}".format(err))
        return
    all_import_errors = []
    for data in all_data:
        import_num, import_errors = spinedb_api.import_data(db_map, **data)
        all_import_errors += import_errors
        if import_errors and cancel_on_error:
            if db_map.has_pending_changes():
                db_map.rollback_session()
        elif import_num:
            db_map.commit_session("imported with mapper")
            print("Inserted {0} data with {1} errors into {2}".format(import_num, len(import_errors), url))
    db_map.connection.close()
    if all_import_errors:
        # Log errors in a time stamped file into the logs directory
        timestamp = _create_log_file_timestamp()
        logfilepath = os.path.abspath(os.path.join(logs_dir, timestamp + "_error.log"))
        with open(logfilepath, 'w') as f:
            for err in all_import_errors:
                f.write("{0}\n".format(err.msg))
        # Make error log file anchor with path as tooltip
        logfile_anchor = (
            "<a style='color:#BB99FF;' title='" + logfilepath + "' href='file:///" + logfilepath + "'>error log</a>"
        )
        rollback_text = ", rolling back" if cancel_on_error else ""
        print("Import errors{0}. Logfile: {1}".format(rollback_text, logfile_anchor), file=sys.stderr)


if __name__ == "__main__":
    # Force std streams to utf-8, since it may not be the default on all terminals (e.g Win cmd prompt)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    run(*json.loads(input()))
