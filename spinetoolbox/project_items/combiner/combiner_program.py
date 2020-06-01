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

import io
import sys
import os
import json
import datetime
import time
from spinedb_api import export_data, import_data, DiffDatabaseMapping, SpineDBAPIError, SpineDBVersionError


def _create_log_file_timestamp():
    """Creates a new timestamp string that is used as Combiner and Data Store error log file.

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


def run(from_urls, to_urls, logs_dir, cancel_on_error):
    print("starting combiner program")
    from_db_maps = [db_map for db_map in (_get_db_map(url) for url in from_urls) if db_map]
    to_db_maps = [db_map for db_map in (_get_db_map(url) for url in to_urls) if db_map]
    from_db_map_data = {from_db_map: export_data(from_db_map) for from_db_map in from_db_maps}
    all_errors = []
    for to_db_map in to_db_maps:
        to_db_map_import_count = 0
        to_db_map_error_count = 0
        for from_db_map, data in from_db_map_data.items():
            import_count, import_errors = import_data(to_db_map, **data)
            all_errors += import_errors
            if import_errors and cancel_on_error:
                if to_db_map.has_pending_changes():
                    to_db_map.rollback_session()
            elif import_count:
                to_db_map.commit_session(
                    f"Import {import_count} items from {from_db_map.db_url} by Spine Toolbox Combiner"
                )
            to_db_map_import_count += import_count
            to_db_map_error_count += len(import_errors)
        print(
            "Merged {0} data with {1} errors into {2}".format(
                to_db_map_import_count, to_db_map_error_count, to_db_map.db_url
            )
        )
    for db_map in from_db_maps + to_db_maps:
        db_map.connection.close()
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


def _get_db_map(url):
    try:
        return DiffDatabaseMapping(url, upgrade=False, username="Combiner")
    except (SpineDBAPIError, SpineDBVersionError) as err:
        print("Unable to create database mapping for {0}, moving on...: {1}".format(url, err))


if __name__ == "__main__":
    # Force std streams to utf-8, since it may not be the default on all terminals (e.g Win cmd prompt)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    run(*json.loads(input()))
