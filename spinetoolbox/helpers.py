#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
General helper functions and classes.

:authors: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   10.1.2018
"""

import logging
import datetime
import os
import time
from PySide2.QtCore import Qt
from config import DEFAULT_PROJECT_DIR


def project_dir(configs=None):
    """Returns current project directory.

    Args:
        configs (ConfigurationParser): Configuration parser object. Default value is for unit tests.
    """
    if not configs:
        return DEFAULT_PROJECT_DIR
    proj_dir = configs.get('settings', 'project_directory')
    if not proj_dir:
        return DEFAULT_PROJECT_DIR
    else:
        return proj_dir


def short_name_reserved(short_name, project_model):
    """Check if folder name derived from the name of the given item is in use.

    Args:
        short_name (str): Item short name
        project_model (QStandardItemModel): Project model containing items

    Returns:
        True if short name is taken, False if it is available.
    """
    # short_name = name.lower().replace(' ', '_')
    # Traverse all items in project model
    top_level_items = project_model.findItems('*', Qt.MatchWildcard, column=0)
    for top_level_item in top_level_items:
        if top_level_item.hasChildren():
            n_children = top_level_item.rowCount()
            for i in range(n_children):
                child = top_level_item.child(i, 0)
                child_name = child.data(Qt.UserRole).name
                child_short_name = child.data(Qt.UserRole).short_name
                if short_name == child_short_name:
                    logging.error(
                        "Item {0} short name matches new short name {1}".format(child_name, short_name))
                    return True
    return False


def get_datetime(configs):
    """Returns date and time string for appending into Event Log messages."""
    show_date = configs.getboolean("settings", "datetime")
    if show_date:
        t = datetime.datetime.now()
        return "[{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}] ".format(t.day, t.month, t.year, t.hour, t.minute, t.second)
    else:
        return ""


def create_dir(base_path, folder='', verbosity=False):
    """Create (input/output) directories recursively.

    Args:
        base_path (str): Absolute path to wanted dir
        folder (str): (Optional) Folder name. Usually short name of item.
        verbosity (bool): True prints a message that tells if the directory already existed or if it was created.

    Returns:
        True if directory already exists or if it was created successfully.

    Raises:
        OSError if operation failed.
    """
    directory = os.path.join(base_path, folder)
    if os.path.exists(directory):
        if verbosity:
            logging.debug("Directory found: {0}".format(directory))
        return True
    else:
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError:
            raise
        if verbosity:
            logging.debug("Directory created: {0}".format(directory))
        return True


def create_output_dir_timestamp():
    """ Creates a new timestamp string that is used as Tool output
    directory.

    Returns:
        Timestamp string or empty string if failed.
    """
    try:
        # Create timestamp
        stamp = datetime.datetime.fromtimestamp(time.time())
    except OverflowError:
        logging.error('Timestamp out of range.')
        return ''
    extension = stamp.strftime('%Y-%m-%dT%H.%M.%S')
    return extension
