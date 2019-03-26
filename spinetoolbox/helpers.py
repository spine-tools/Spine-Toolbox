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

import sys
import logging
import datetime
import os
import time
import shutil
import glob
import spinedb_api
from PySide2.QtCore import Qt, Slot
from PySide2.QtCore import __version__ as qt_version
from PySide2.QtCore import __version_info__ as qt_version_info
from PySide2.QtWidgets import QApplication, QMessageBox
from PySide2.QtGui import QCursor, QPainter, QPixmap, QImageReader
from config import DEFAULT_PROJECT_DIR, REQUIRED_SPINE_DBAPI_VERSION


def set_taskbar_icon():
    """Set application icon to Windows taskbar."""
    if os.name == "nt":
        import ctypes
        myappid = "{6E794A8A-E508-47C4-9319-1113852224D3}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


@Slot(name="supported_img_formats")
def supported_img_formats():
    """Function to check if reading .ico files is supported."""
    img_formats = QImageReader().supportedImageFormats()
    img_formats_str = '\n'.join(str(x) for x in img_formats)
    logging.debug("Supported Image formats:\n{0}".format(img_formats_str))


def pyside2_version_check():
    """Check that PySide2 version is older than 5.12, since this is not supported yet.
    Issue #238 in GitLab.

    qt_version is the Qt version used to compile PySide2 as string. E.g. "5.11.2"
    qt_version_info is a tuple with each version component of Qt used to compile PySide2. E.g. (5, 11, 2)
    """
    # print("Your QT version info is:{0} version string:{1}".format(qt_version_info, qt_version))
    if qt_version_info[0] == 5 and qt_version_info[1] >= 12:
        print(
            """Sorry for the inconvenience but,

            Spine Toolbox does not support PySide2 version {0} yet.
            Please downgrade PySide2 to version 5.11.x and try to start the application again.

            To downgrade PySide2 to a compatible version, run

                pip install "pyside2<5.12"

            """.format(qt_version))
        return False
    return True


def spinedb_api_version_check():
    """Check if spinedb_api is the correct version and explain how to upgrade if it is not."""
    try:
        current_version = spinedb_api.__version__
        current_split = [int(x) for x in current_version.split(".")]
        required_split = [int(x) for x in REQUIRED_SPINE_DBAPI_VERSION.split(".")]
        if current_split >= required_split:
            return True
    except AttributeError:
        current_version = "not reported"
    script = "upgrade_spinedb_api.bat" if sys.platform == "win32" else "upgrade_spinedb_api.sh"
    print(
        """ERROR:
        Spine Toolbox failed to start because spinedb_api is outdated.
        (Required version is {0}, whereas current is {1})
        Please upgrade spinedb_api to v{0} and start Spine Toolbox again.

        To upgrade, run script '{2}' in the '/bin' folder.

        Or upgrade it manually by running,

            pip install --upgrade git+https://github.com/Spine-project/Spine-Database-API.git

        """.format(REQUIRED_SPINE_DBAPI_VERSION, current_version, script))
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


def object_pixmap(object_class_name):
    """An object pixmap defined for `object_class_name` if any, or a generic one if none."""
    pixmap = QPixmap(":/object_class_icons/{0}.png".format(object_class_name))
    if pixmap.isNull():
        pixmap = QPixmap(":/icons/object_icon.png")
    return pixmap


def relationship_pixmap(object_class_name_list):
    """A pixmap rendered by painting several object pixmaps together."""
    extent = 64
    x_step = extent - 8
    y_offset = extent - 16 + 2
    pixmap_list = list()
    for object_class_name in object_class_name_list:
        pixmap = object_pixmap(object_class_name)
        pixmap_list.append(pixmap.scaled(extent, extent))
    pixmap_matrix = [pixmap_list[i:i + 2] for i in range(0, len(pixmap_list), 2)] # Two pixmaps per row...
    combo_width = extent + (len(pixmap_list) - 1) * x_step / 2
    combo_height = extent + y_offset
    combo_extent = max(combo_width, combo_height)
    x_padding = (combo_extent - combo_width) / 2 if combo_extent > combo_width else 0
    y_padding = (combo_extent - combo_height) / 2 if combo_extent > combo_height else 0
    # Add extra vertical padding in case the list contains only one element, so this one's centered
    if len(object_class_name_list) == 1:
        y_padding += y_offset / 2
    relationship_pixmap = QPixmap(combo_extent, combo_extent)
    relationship_pixmap.fill(Qt.transparent)
    painter = QPainter(relationship_pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    x_offset = 0
    for pixmap_row in pixmap_matrix:
        for j, pixmap in enumerate(pixmap_row):
            if j % 2 == 1:
                x = x_offset + x_step / 2 + x_padding
                y = y_offset + y_padding
            else:
                x = x_offset + x_padding
                y = y_padding
            painter.drawPixmap(x, y, pixmap)
        x_offset += x_step
    painter.end()
    return relationship_pixmap


def fix_name_ambiguity(name_list, offset=0):
    """Modify repeated entries in name list by appending an increasing integer."""
    ref_name_list = name_list.copy()
    ocurrences = {}
    for i, name in enumerate(name_list):
        n_ocurrences = ref_name_list.count(name)
        if n_ocurrences == 1:
            continue
        ocurrence = ocurrences.setdefault(name, 1)
        name_list[i] = name + str(offset + ocurrence)
        ocurrences[name] = ocurrence + 1


def tuple_itemgetter(itemgetter_func, num_indexes):
    """Change output of itemgetter to always be a tuple even for one index"""
    if num_indexes == 1:
        def g(item):
            return (itemgetter_func(item),)
        return g
    else:
        return itemgetter_func


def format_string_list(str_list):
    """
    Return an unordered html list with all elements in str_list.
    Intended to print error logs as returned by spinedb_api.

    Args:
        str_list (list(str))
    """
    return "<ul>" + "".join(["<li>" + str(x) + "</li>" for x in str_list]) + "</ul>"
