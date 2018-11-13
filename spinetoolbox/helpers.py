######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
General helper functions and classes.

:authors: P. Savolainen (VTT)
:date:   10.1.2018
"""

import logging
import datetime
import os
import time
import shutil
import glob
import spinedatabase_api
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QMessageBox
from PySide2.QtGui import QCursor
from config import DEFAULT_PROJECT_DIR, REQUIRED_SPINE_DBAPI_VERSION


def spinedatabase_api_version_check():
    """Check if spinedatabase_api is the correct version and explain how to upgrade if it is not."""
    try:
        current_version = spinedatabase_api.__version__
        current_split = [int(x) for x in current_version.split(".")]
        required_split = [int(x) for x in REQUIRED_SPINE_DBAPI_VERSION.split(".")]
        if current_split >= required_split:
            return True
    except AttributeError:
        current_version = "not reported"
    print(
        """ERROR:
        Spine Toolbox failed to start because spinedatabase_api is outdated.
        (Required version is {0}, whereas current is {1})
        Please upgrade spinedatabase_api to v{0} and start Spine Toolbox again.

        To upgrade, run script 'upgrade_spinedatabase_api.bat' in the '/bin' folder.

        Or upgrade it manually by running,

            pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git

        """.format(REQUIRED_SPINE_DBAPI_VERSION, current_version))
    return False


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


@busy_effect
def copy_dir(widget, src_dir, dst_dir):
    """Make a copy of a directory. All files and folders are copied.

    Args:
        widget (QWidget): Parent widget for QMessageBoxes
        src_dir (str): Absolute path to directory that will be copied
        dst_dir (str): Absolute path to new directory
    """
    title_msg = "Copying directory failed"
    try:
        shutil.copytree(src_dir, dst_dir)
    except FileExistsError:
        msg = "Directory<br/><b>{0}</b><br/>already exists".format(dst_dir)
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, title_msg, msg)
        return False
    except PermissionError as e:
        logging.exception(e)
        msg = "Access to directory <br/><b>{0}</b><br/>denied." \
              "<br/><br/>Possible reasons:" \
              "<br/>1. Windows Explorer is open in the directory" \
              "<br/>2. Permission error" \
              "<br/><br/>Check these and try again.".format(dst_dir)
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, title_msg, msg)
        return False
    except OSError:
        msg = "Copying directory failed. OSError in" \
              "<br/><b>{0}</b><br/>Possibly because Windows " \
              "Explorer is open in the directory".format(dst_dir)
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, title_msg, msg)
        return False
    return True


def rename_dir(widget, old_dir, new_dir):
    """Rename directory. Note: This is not used in renaming projects due to unreliability.
    Looks like it works fine in renaming project items though.

    Args:
        widget (QWidget): Parent widget for QMessageBoxes
        old_dir (str): Absolute path to directory that will be renamed
        new_dir (str): Absolute path to new directory
    """
    try:
        shutil.move(old_dir, new_dir)
    except FileExistsError:
        msg = "Directory<br/><b>{0}</b><br/>already exists".format(new_dir)
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, "Renaming directory failed", msg)
        return False
    except PermissionError as e:
        logging.exception(e)
        msg = "Access to directory <br/><b>{0}</b><br/>denied." \
              "<br/><br/>Possible reasons:" \
              "<br/>1. Windows Explorer is open in the directory" \
              "<br/>2. Permission error" \
              "<br/><br/>Check these and try again.".format(old_dir)
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, "Renaming directory failed", msg)
        return False
    except OSError:
        msg = "Renaming input directory failed. OSError in" \
              "<br/><b>{0}</b><br/>Possibly because Windows " \
              "Explorer is open in the directory".format(old_dir)
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, "Renaming directory failed", msg)
        return False
    return True
