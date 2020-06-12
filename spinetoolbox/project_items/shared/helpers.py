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
Helper functions and classes.

:authors: M. Marin (KTH)
:date:   12.5.2020
"""

import datetime
import time
from spinetoolbox.helpers import deserialize_path, serialize_path


def create_log_file_timestamp():
    """Creates a new timestamp string that is used as Combiner and Importer error log file.

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


def serialize_checked_states(files, project_path):
    """Serializes file paths and adds a boolean value
    for each, which indicates whether the path is
    selected or not. Used in saving checked file states to
    project.json.

    Args:
        files (list): List of absolute file paths
        project_path (str): Absolute project directory path

    Returns:
        list: List of serialized paths with a boolean value
    """
    return [[serialize_path(item.label, project_path), item.selected] for item in files]


def deserialize_checked_states(serialized, project_path):
    """Reverse operation for serialize_checked_states above.
    Returns absolute file paths with their check state as boolean.

    Args:
        serialized (list): List of serialized paths with a boolean value
        project_path (str): Absolute project directory path

    Returns:
        dict: Dictionary with paths as keys and boolean check states as value
    """
    if not serialized:
        return dict()
    deserialized = dict()
    for serialized_label, checked in serialized:
        label = deserialize_path(serialized_label, project_path)
        deserialized[label] = checked
    return deserialized
