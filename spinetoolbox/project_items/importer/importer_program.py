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
Contains Importer project item class.

:authors: P. Savolainen (VTT), P. Vennström (VTT), A. Soininen (VTT)
:date:   10.6.2019
"""

import sys
import os
import json
import spinedb_api
from spinetoolbox.helpers import create_log_file_timestamp
from spinetoolbox.executioner import ExecutionState
from spinetoolbox.spine_io.importers.csv_reader import CSVConnector
from spinetoolbox.spine_io.importers.excel_reader import ExcelConnector


def run(args):
    args = [json.loads(arg) for arg in args[1:]]
    importer_name, checked_files, all_settings, urls_downstream, logs_dir = args
    all_data = []
    all_errors = []
    for source in checked_files:
        settings = all_settings.get(source, None)
        if settings is None or not settings:
            print("<b>{0}:</b> There are no mappings defined for {1}, moving on...".format(importer_name, source))
            continue
        source_type = settings["source_type"]
        connector = eval(source_type)()  # pylint: disable=eval-used
        connector.connect_to_source(source)
        table_mappings = {
            name: mapping for name, mapping in settings.get("table_mappings", {}).items() if name in settings["selected_tables"]
        }
        table_options = {
            name: options for name, options in settings.get("table_options", {}).items() if name in settings["selected_tables"]
        }
        table_types = {
                name: types for name, types in settings.get("table_types", {}).items() if name in settings["selected_tables"]
        }
        table_row_types = {
                name: types
                for name, types in settings.get("table_row_types", {}).items()
                if name in settings["selected_tables"]
        }
        data, errors = connector.get_mapped_data(
                table_mappings, table_options, table_types, table_row_types, max_rows=-1
            )
        print(
            "<b>{0}:</b> Read {1} data from {2} with {3} errors".format(
                importer_name, sum(len(d) for d in data.values()), source, len(errors)
            )
        )
        all_data.append(data)
        all_errors.extend(errors)
    if all_errors:
        # Log errors in a time stamped file into the logs directory
        timestamp = create_log_file_timestamp()
        logfilepath = os.path.abspath(os.path.join(logs_dir, timestamp + "_error.log"))
        with open(logfilepath, 'w') as f:
            for err in all_errors:
                f.write("{}\n".format(err))
        # Make error log file anchor with path as tooltip
        logfile_anchor = (
            "<a style='color:#BB99FF;' title='" + logfilepath + "' href='file:///" + logfilepath + "'>error log</a>"
        )
        print("There where errors while executing <b>{0}</b>. {1}".format(importer_name, logfile_anchor))
        return ExecutionState.ABORT
    if all_data:
        for url in urls_downstream:
            _import(all_data, url, importer_name, logs_dir)
    return ExecutionState.CONTINUE


def _import(all_data, url, importer_name, logs_dir):
    try:
        db_map = spinedb_api.DiffDatabaseMapping(url, upgrade=False, username="Mapper")
    except (spinedb_api.SpineDBAPIError, spinedb_api.SpineDBVersionError) as err:
        print("<b>{0}:</b> Unable to create database mapping, all import operations will be omitted.".format(err))
        return
    all_import_errors = []
    for data in all_data:
        import_num, import_errors = spinedb_api.import_data(db_map, **data)
        if import_errors:
            db_map.rollback_session()
            all_import_errors += import_errors
        elif import_num:
            db_map.commit_session("imported with mapper")
            print(
                "<b>{0}:</b> Inserted {1} data with {2} errors into {3}".format(
                    importer_name, import_num, len(import_errors), db_map.db_url
                )
            )
    db_map.connection.close()
    if all_import_errors:
        # Log errors in a time stamped file into the logs directory
        timestamp = create_log_file_timestamp()
        logfilepath = os.path.abspath(os.path.join(logs_dir, timestamp + "_error.log"))
        with open(logfilepath, 'w') as f:
            for err in all_import_errors:
                f.write("{}\n".format(err.msg))
        # Make error log file anchor with path as tooltip
        logfile_anchor = (
            "<a style='color:#BB99FF;' title='" + logfilepath + "' href='file:///" + logfilepath + "'>error log</a>"
        )
        print(
            "There where import errors while executing <b>{0}</b>, rolling back: "
            "{1}".format(importer_name, logfile_anchor)
        )


if __name__ == "__main__":
    run(sys.argv)
