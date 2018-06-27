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
import shutil
import glob
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QCursor
from config import DEFAULT_PROJECT_DIR
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.mysql import TINYINT, DOUBLE


# TODO: check if this is the right place for this
@compiles(TINYINT, 'sqlite')
def compile_TINYINT_mysql_sqlite(element, compiler, **kw):
    """ Handles mysql TINYINT datatype as INTEGER in sqlite """
    return compiler.visit_INTEGER(element, **kw)


@compiles(DOUBLE, 'sqlite')
def compile_DOUBLE_mysql_sqlite(element, compiler, **kw):
    """ Handles mysql DOUBLE datatype as REAL in sqlite """
    return compiler.visit_REAL(element, **kw)


def busy_effect(func):
    """ Decorator to change the mouse cursor to 'busy' while a function is processed.

    Args:
        func: Decorated function.
    """
    def new_function(*args, **kwargs):
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception("Error {}".format(e.args[0]))
            raise e
        finally:
            # noinspection PyArgumentList
            QApplication.restoreOverrideCursor()
    return new_function


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


@busy_effect
def copy_files(src_dir, dst_dir, includes=None, excludes=None):
    """Method for copying files. Does not copy folders.

    Args:
        src_dir (str): Source directory
        dst_dir (str): Destination directory
        includes (list): Included files (wildcards accepted)
        excludes (list): Excluded files (wildcards accepted)

    Returns:
        count (int): Number of files copied
    """
    if not includes:
        includes = ['*']
    if not excludes:
        excludes = []
    src_files = []
    for pattern in includes:
        src_files += glob.glob(os.path.join(src_dir, pattern))
    exclude_files = []
    for pattern in excludes:
        exclude_files += glob.glob(os.path.join(src_dir, pattern))
    count = 0
    for filename in src_files:
        if os.path.isdir(filename):
            continue
        if filename not in exclude_files:
            shutil.copy(filename, dst_dir)
            count += 1
    return count


@busy_effect
def erase_dir(path, verbosity=False):
    """Delete directory and all its contents without prompt.

    Args:
        path (str): Path to directory
        verbosity (bool): Print logging messages or not
    """
    if not os.path.exists(path):
        if verbosity:
            logging.debug("Path does not exist: {}".format(path))
        return False
    if verbosity:
        logging.debug("Deleting directory {0}".format(path))
    try:
        shutil.rmtree(path)
    except OSError:
        raise
    return True

# NOTE: no longer needed. The cause for dialogs to freeze was calling setLine()
# within paint() in QLineItems back in the days. All this is fixed now.
# def blocking_updates(view, func):
#     """Wrapper to block updates to a view while calling a function.
#     Fix bug on Linux which causes QFileDialogs to become unresponsive
#     when there is visible items on QGraphicsView.
#     """
#     def new_function(*args, **kwargs):
#         view.setUpdatesEnabled(False)
#         try:
#             return func(*args, **kwargs)
#         except Exception as e:
#             logging.exception("Error {}".format(e.args[0]))
#             raise e
#         finally:
#             view.setUpdatesEnabled(True)
#     return new_function
