######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

import itertools
import os
import sys
import glob
import json
import logging
import datetime
import shutil
import matplotlib
from PySide2.QtGui import QCursor
from PySide2.QtCore import Qt, Slot, QFile, QIODevice, QSize, QRect, QPoint, QUrl, QObject, QEvent
from PySide2.QtCore import __version__ as qt_version
from PySide2.QtCore import __version_info__ as qt_version_info
from PySide2.QtWidgets import QApplication, QMessageBox, QFileIconProvider, QStyle, QFileDialog
from PySide2.QtGui import (
    QImageReader,
    QPixmap,
    QPainter,
    QIcon,
    QIconEngine,
    QFont,
    QStandardItemModel,
    QStandardItem,
    QDesktopServices,
    QKeySequence,
    QTextCursor,
    QPalette,
    QColor,
)
import spine_engine
from .config import DEFAULT_WORK_DIR, REQUIRED_SPINE_ENGINE_VERSION


if os.name == "nt":
    import ctypes

matplotlib.use('Qt5Agg')
matplotlib.rcParams.update({"font.size": 8})
logging.getLogger("matplotlib").setLevel(logging.WARNING)
_matplotlib_version = [int(x) for x in matplotlib.__version__.split(".") if x.isdigit()]
if _matplotlib_version[0] == 3 and _matplotlib_version[1] == 0:
    from pandas.plotting import register_matplotlib_converters

    register_matplotlib_converters()


def format_log_message(msg_type, message, show_datetime=True):
    color = {"msg": "white", "msg_success": "#00ff00", "msg_error": "#ff3333", "msg_warning": "yellow"}[msg_type]
    open_tag = f"<span style='color:{color};white-space: pre-wrap;'>"
    date_str = get_datetime(show=show_datetime)
    return open_tag + date_str + message + "</span>"


def add_message_to_document(document, message):
    """Adds a message to a document and return the cursor.

    Args:
        document (QTextDocument)
        message (str)

    Returns:
        QTextCursor
    """
    cursor = QTextCursor(document)
    cursor.movePosition(QTextCursor.End)
    cursor.insertBlock()
    cursor.insertHtml(message)
    return cursor


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
        finally:
            # noinspection PyArgumentList
            QApplication.restoreOverrideCursor()

    return new_function


def create_dir(base_path, folder="", verbosity=False):
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
    if os.path.exists(directory) and verbosity:
        logging.debug("Directory found: %s", directory)
    else:
        os.makedirs(directory, exist_ok=True)
        if verbosity:
            logging.debug("Directory created: %s", directory)
    return True


def rename_dir(old_dir, new_dir, toolbox, box_title):
    """Renames directory. Called by ``ProjectItemModel.set_item_name()``

    Args:
        old_dir (str): Absolute path to directory that will be renamed
        new_dir (str): Absolute path to new directory
        toolbox (ToolboxUI): A toolbox to log messages and ask questions.
        box_title (str): The title of the message boxes, (e.g. "Undoing 'rename DC1 to DC2'")
    """
    if os.path.exists(new_dir):
        msg = "Directory <b>{0}</b> already exists.<br/><br/>Would you like to overwrite its contents?".format(new_dir)
        box = QMessageBox(
            QMessageBox.Question, box_title, msg, buttons=QMessageBox.Ok | QMessageBox.Cancel, parent=toolbox
        )
        box.button(QMessageBox.Ok).setText("Overwrite")
        answer = box.exec_()
        if answer != QMessageBox.Ok:
            return False
        shutil.rmtree(new_dir)
    try:
        shutil.move(old_dir, new_dir)
    except FileExistsError:
        # This is unlikely because of the above `if`, but still possible since another concurrent process
        # might have done things in between
        msg = "Directory<br/><b>{0}</b><br/>already exists".format(new_dir)
        toolbox.information_box.emit(box_title, msg)
        return False
    except PermissionError as pe_e:
        logging.error(pe_e)
        msg = (
            "Access to directory <br/><b>{0}</b><br/>denied."
            "<br/><br/>Possible reasons:"
            "<br/>1. You don't have a permission to edit the directory"
            "<br/>2. Windows Explorer is open in the directory"
            "<br/><br/>Check these and try again.".format(old_dir)
        )
        toolbox.information_box.emit(box_title, msg)
        return False
    except OSError as os_e:
        logging.error(os_e)
        msg = (
            "Renaming directory "
            "<br/><b>{0}</b> "
            "<br/>to "
            "<br/><b>{1}</b> "
            "<br/>failed."
            "<br/><br/>Possibly reasons:"
            "<br/>1. Windows Explorer is open in the directory."
            "<br/>2. A file in the directory is open in another program. "
            "<br/><br/>Check these and try again.".format(old_dir, new_dir)
        )
        toolbox.information_box.emit(box_title, msg)
        return False
    return True


def open_url(url):
    """Opens the given url in the appropriate Web browser for the user's desktop environment,
    and returns true if successful; otherwise returns false.

    If the URL is a reference to a local file (i.e., the URL scheme is "file") then it will
    be opened with a suitable application instead of a Web browser.

    Handle return value on caller side.

    Args:
        url(str): URL to open

    Returns:
        bool: True if successful, False otherwise
    """
    return QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))


def set_taskbar_icon():
    """Set application icon to Windows taskbar."""
    if os.name == "nt":
        myappid = "{6E794A8A-E508-47C4-9319-1113852224D3}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


@Slot()
def supported_img_formats():
    """Function to check if reading .ico files is supported."""
    img_formats = QImageReader().supportedImageFormats()
    img_formats_str = '\n'.join(str(x) for x in img_formats)
    logging.debug("Supported Image formats:\n%s", img_formats_str)


def pyside2_version_check():
    """Check that PySide2 version is 5.14 or 5.15.
    Version 5.15 is allowed but it is not promoted yet
    because user's may need to update their VC++ runtime
    libraries on Windows.

    qt_version is the Qt version used to compile PySide2 as string. E.g. "5.14.2"
    qt_version_info is a tuple with each version component of Qt used to compile PySide2. E.g. (5, 14, 2)
    """
    # print("Your QT version info is:{0} version string:{1}".format(qt_version_info, qt_version))
    if not (qt_version_info[0] == 5 and qt_version_info[1] == 14) and not (
        qt_version_info[0] == 5 and qt_version_info[1] == 15
    ):
        print(
            """Sorry for the inconvenience but,

            Spine Toolbox does not support PySide2 version {0}.
            At the moment, supported PySide2 versions are 5.14 & 5.15.

            To upgrade PySide2 to latest supported version, run

                pip install -r requirements.txt --upgrade

            And start the application again.
            """.format(
                qt_version
            )
        )
        return False
    return True


def spine_engine_version_check():
    """Check if spine engine package is the correct version and explain how to upgrade if it is not."""
    try:
        current_version = spine_engine.__version__
        current_split = [int(x) for x in current_version.split(".")]
        required_split = [int(x) for x in REQUIRED_SPINE_ENGINE_VERSION.split(".")]
        if current_split >= required_split:
            return True
    except AttributeError:
        current_version = "not reported"
    script = "upgrade_spine_engine.bat" if sys.platform == "win32" else "upgrade_spine_engine.py"
    print(
        """SPINE ENGINE OUTDATED.

        Spine Toolbox failed to start because spine_engine is outdated.
        (Required version is {0}, whereas current is {1})
        Please upgrade spine_engine to v{0} and start Spine Toolbox again.

        To upgrade, run script '{2}' in the '/bin' folder.

        Or upgrade it manually by running,

            pip install --upgrade git+https://github.com/Spine-project/spine-engine.git#egg=spine_engine

        """.format(
            REQUIRED_SPINE_ENGINE_VERSION, current_version, script
        )
    )
    return False


def get_datetime(show, date=True):
    """Returns date and time string for appending into Event Log messages.

    Args:
        show (bool): True returns date and time string. False returns empty string.
        date (bool): Whether or not the date should be included in the result
    """
    if show:
        t = datetime.datetime.now()
        time_str = "{:02d}:{:02d}:{:02d}".format(t.hour, t.minute, t.second)
        if not date:
            return "[{}] ".format(time_str)
        date_str = "{}-{:02d}-{:02d}".format(t.day, t.month, t.year)
        return "[{} {}] ".format(date_str, time_str)
    return ""


@busy_effect
def copy_files(src_dir, dst_dir, includes=None, excludes=None):
    """Function for copying files. Does not copy folders.

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
    """Deletes a directory and all its contents without prompt.

    Args:
        path (str): Path to directory
        verbosity (bool): Print logging messages or not
    """
    if not os.path.exists(path):
        if verbosity:
            logging.debug("Path does not exist: %s", path)
        return False
    if verbosity:
        logging.debug("Deleting directory %s", path)
    shutil.rmtree(path)
    return True


@busy_effect
def copy_dir(widget, src_dir, dst_dir):
    """Makes a copy of a directory. All files and folders are copied.
    Destination directory must not exist. Does not overwrite files.

    Args:
        widget (QWidget): Parent widget for QMessageBoxes
        src_dir (str): Absolute path to directory that will be copied
        dst_dir (str): Absolute path to new directory
    """
    try:
        shutil.copytree(src_dir, dst_dir)
    except FileExistsError:
        msg = "Directory<br/><b>{0}</b><br/>already exists".format(dst_dir)
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, "Copying directory failed", msg)
        return False
    except PermissionError as pe_e:
        logging.error(pe_e)
        msg = (
            "Access to directory <br/><b>{0}</b><br/>denied."
            "<br/><br/>Possible reasons:"
            "<br/>1. Permission error"
            "<br/>2. Windows Explorer is open in the directory"
            "<br/><br/>Check these and try again.".format(dst_dir)
        )
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, "Permission Error", msg)
        return False
    except OSError as os_e:
        logging.error(os_e)
        msg = (
            "Copying directory "
            "<br/><b>{0}</b> "
            "<br/>to "
            "<br/><b>{1}</b> "
            "<br/>failed."
            "<br/><br/>Possibly reasons:"
            "<br/>1. Windows Explorer is open in the source or destination directory."
            "<br/>2. A file in these directories is open in another program. "
            "<br/><br/>Check these and try again.".format(src_dir, dst_dir)
        )
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QMessageBox.information(widget, "OS Error", msg)
        return False
    return True


@busy_effect
def recursive_overwrite(widget, src, dst, ignore=None, silent=True):
    """Copies everything from source directory to destination directory recursively.
    Overwrites existing files.

    Args:
        widget (QWidget): Enables e.g. printing to Event Log
        src (str): Source directory
        dst (str): Destination directory
        ignore: Ignore function
        silent (bool): If False, messages are sent to Event Log, If True, copying is done in silence
    """
    if os.path.isdir(src):
        if not os.path.isdir(dst):
            if not silent:
                widget.msg.emit("Creating directory <b>{0}</b>".format(dst))
            os.makedirs(dst)
        files = os.listdir(src)
        for file_name in list(files):
            # Avoid ending up in 'dst' as this would result in infinite recursion.
            file_path = os.path.join(src, file_name)
            if os.path.samefile(os.path.commonpath((file_path, dst)), file_path):
                files.remove(file_name)
                break
        if ignore is not None:
            ignored = ignore(src, files)
        else:
            ignored = set()
        for f in files:
            if f not in ignored:
                recursive_overwrite(widget, os.path.join(src, f), os.path.join(dst, f), ignore, silent)
    else:
        if not silent:
            _, src_filename = os.path.split(src)
            dst_dir, _ = os.path.split(dst)
            widget.msg.emit("Copying <b>{0}</b> -> <b>{1}</b>".format(src_filename, dst_dir))
        shutil.copyfile(src, dst)


def tuple_itemgetter(itemgetter_func, num_indexes):
    """Change output of itemgetter to always be a tuple even for a single index.

    Args:
        itemgetter_func (Callable): item getter function
        num_indexes (int): number of indexes

    Returns:
        Callable: getter function that works with a single index
    """
    return (lambda item: (itemgetter_func(item),)) if num_indexes == 1 else itemgetter_func


def format_string_list(str_list):
    """Returns a html unordered list from the given list of strings.
    Intended to print error logs as returned by spinedb_api.

    Args:
        str_list (list(str))
    """
    return "<ul>" + "".join(["<li>" + str(x) + "</li>" for x in str_list]) + "</ul>"


def rows_to_row_count_tuples(rows):
    """Breaks a list of rows into a list of (row, count) tuples corresponding
    to chunks of successive rows.
    """
    if not rows:
        return []
    sorted_rows = sorted(set(rows))
    break_points = [k + 1 for k in range(len(sorted_rows) - 1) if sorted_rows[k] + 1 != sorted_rows[k + 1]]
    break_points = [0] + break_points + [len(sorted_rows)]
    ranges = [(break_points[l], break_points[l + 1]) for l in range(len(break_points) - 1)]
    return [(sorted_rows[start], stop - start) for start, stop in ranges]


def inverted(input_):
    """Inverts a dictionary that maps keys to a list of values.
    The output maps values to a list of keys that include the value in the input.
    """
    output = dict()
    for key, value_list in input_.items():
        for value in value_list:
            output.setdefault(value, list()).append(key)
    return output


class Singleton(type):
    """A singleton class from SO."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class IconListManager:
    """A class to manage icons for icon list widgets."""

    def __init__(self, icon_size):
        self._icon_size = icon_size
        self.searchterms = {}
        self.model = QStandardItemModel()
        self.model.data = self._model_data

    @busy_effect
    def init_model(self):
        """Init model that can be used to display all icons in a list."""
        if self.searchterms:
            return
        qfile = QFile(":/fonts/fontawesome5-searchterms.json")
        qfile.open(QIODevice.ReadOnly | QIODevice.Text)
        data = str(qfile.readAll().data(), "utf-8")
        qfile.close()
        self.searchterms = json.loads(data)
        items = []
        for codepoint, searchterms in self.searchterms.items():
            item = QStandardItem()
            display_icon = int(codepoint, 16)
            item.setData(display_icon, Qt.UserRole)
            item.setData(searchterms, Qt.UserRole + 1)
            items.append(item)
        self.model.invisibleRootItem().appendRows(items)

    def _model_data(self, index, role):
        """Replacement method for model.data().
        Create pixmaps as they're requested by the data() method, to reduce loading time.
        """
        if role == Qt.DisplayRole:
            return None
        if role != Qt.DecorationRole:
            return QStandardItemModel.data(self.model, index, role)
        display_icon = index.data(Qt.UserRole)
        return object_icon(display_icon)


def object_icon(display_icon):
    """Create and return a QIcon corresponding to display_icon."""
    icon_code, color_code = interpret_icon_id(display_icon)
    engine = CharIconEngine(chr(icon_code), color_code)
    return QIcon(engine)


class TransparentIconEngine(QIconEngine):
    """Specialization of QIconEngine with transparent background."""

    def pixmap(self, size=QSize(512, 512), mode=None, state=None):
        pm = QPixmap(size)
        pm.fill(Qt.transparent)
        self.paint(QPainter(pm), QRect(QPoint(0, 0), size), mode, state)
        return pm


class CharIconEngine(TransparentIconEngine):
    """Specialization of QIconEngine used to draw font-based icons."""

    def __init__(self, char, color=None):
        super().__init__()
        self.char = char
        self.color = color
        self.font = QFont('Font Awesome 5 Free Solid')

    def paint(self, painter, rect, mode=None, state=None):
        painter.save()
        size = 0.875 * round(min(rect.width(), rect.height()))
        self.font.setPixelSize(size)
        painter.setFont(self.font)
        if self.color:
            color = self.color
        else:
            palette = QPalette(QApplication.palette())
            if mode == QIcon.Disabled:
                palette.setCurrentColorGroup(QPalette.Disabled)
            elif mode == QIcon.Active:
                palette.setCurrentColorGroup(QPalette.Active)
            color = palette.buttonText().color()
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignCenter | Qt.AlignVCenter, self.char)
        painter.restore()


def make_icon_id(icon_code, color_code):
    """Takes icon and color codes, and return equivalent integer.

    Args:
        icon_code (int):icon's code
        color_code (int): color code

    Returns:
        int: icon id
    """
    return icon_code + (color_code << 16)


def interpret_icon_id(display_icon):
    """Takes a display icon id and returns an equivalent tuple of icon and color code.

    Args:
        display_icon (int): icon id

    Returns:
        tuple: icon's code, color code
    """
    if not isinstance(display_icon, int) or display_icon < 0:
        return 0xF1B2, 0
    icon_code = display_icon & 65535
    try:
        color_code = display_icon >> 16
    except OverflowError:
        color_code = 0
    return icon_code, color_code


def default_icon_id():
    """Creates a default icon id.

    Returns:
        int: default icon's id
    """
    return make_icon_id(*interpret_icon_id(None))


class ProjectDirectoryIconProvider(QFileIconProvider):
    """QFileIconProvider that provides a Spine icon to the
    Open Project Dialog when a Spine Toolbox project
    directory is encountered."""

    def __init__(self):
        super().__init__()
        self.spine_icon = QIcon(":/symbols/Spine_symbol.png")

    def icon(self, info):
        """Returns an icon for the file described by info.

        Args:
            info (QFileInfo): File (or directory) info

        Returns:
            QIcon: Icon for a file system resource with the given info
        """
        if isinstance(info, QFileIconProvider.IconType):
            return super().icon(info)  # Because there are two icon() methods
        if not info.isDir():
            return super().icon(info)
        p = info.filePath()
        # logging.debug("In dir:{0}".format(p))
        if os.path.exists(os.path.join(p, ".spinetoolbox")):
            # logging.debug("found project dir:{0}".format(p))
            return self.spine_icon
        return super().icon(info)


def ensure_window_is_on_screen(window, size):
    """
    Checks if window is on screen and if not, moves and resizes it to make it visible on the primary screen.

    Args:
        window (QWidget): a window to check
        size (QSize): desired window size if the window is moved
    """
    window_geometry = window.frameGeometry()
    widget_center = window_geometry.center()
    screens = QApplication.screens()
    widget_inside_screen = False
    for screen in screens:
        screen_geometry = screen.geometry()
        if screen_geometry.contains(widget_center):
            widget_inside_screen = True
            break
    if not widget_inside_screen:
        primary_screen = QApplication.primaryScreen()
        screen_geometry = primary_screen.availableGeometry()
        window.setGeometry(QStyle.alignedRect(Qt.LeftToRight, Qt.AlignCenter, size, screen_geometry))


def first_non_null(s):
    """Returns the first element in Iterable s that is not None."""
    try:
        return next(itertools.dropwhile(lambda x: x is None, s))
    except StopIteration:
        return None


def get_save_file_name_in_last_dir(qsettings, key, parent, caption, given_dir, filter_=""):
    """Calls QFileDialog.getSaveFileName in the directory that was selected last time the dialog was accepted.

    Args:
        qsettings (QSettings): A QSettings object where the last directory is stored
        key (string): The name of the entry in the above QSettings
        parent, caption, given_dir, filter_: Args passed to QFileDialog.getSaveFileName

    Returns:
        str: filename
        str: selected filter
    """
    dir_ = qsettings.value(key, defaultValue=given_dir)
    filename, selected_filter = QFileDialog.getSaveFileName(parent, caption, dir_, filter_)
    if filename:
        qsettings.setValue(key, os.path.dirname(filename))
    return filename, selected_filter


def get_open_file_name_in_last_dir(qsettings, key, parent, caption, given_dir, filter_=""):
    dir_ = qsettings.value(key, defaultValue=given_dir)
    filename, selected_filter = QFileDialog.getOpenFileName(parent, caption, dir_, filter_)
    if filename:
        qsettings.setValue(key, os.path.dirname(filename))
    return filename, selected_filter


def try_number_from_string(text):
    """
    Returns an integer or a float from the given text if possible.
    """
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text
    except TypeError:
        return None


def focused_widget_has_callable(parent, callable_name):
    """Returns True if the currently focused widget or one of its ancestors has the given callable."""
    focus_widget = parent.focusWidget()
    while focus_widget is not None and focus_widget is not parent:
        if hasattr(focus_widget, callable_name):
            method = getattr(focus_widget, callable_name)
            if callable(method):
                return True
        focus_widget = focus_widget.parentWidget()
    return False


def call_on_focused_widget(parent, callable_name):
    """Calls the given callable on the currently focused widget or one of its ancestors."""
    focus_widget = parent.focusWidget()
    while focus_widget is not None and focus_widget is not parent:
        if hasattr(focus_widget, callable_name):
            method = getattr(focus_widget, callable_name)
            if callable(method):
                return method()
        focus_widget = focus_widget.parentWidget()


class ChildCyclingKeyPressFilter(QObject):
    """Event filter class for catching next and previous child key presses.
    Used in filtering the Ctrl+Tab and Ctrl+Shift+Tab key presses in the
    Item Properties tab widget."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.matches(QKeySequence.NextChild) or event.matches(QKeySequence.PreviousChild):
                return True
        return QObject.eventFilter(self, obj, event)  # Pass event further


def select_julia_executable(parent, line_edit):
    """Opens file browser where user can select a Julia executable (i.e. julia.exe on Windows).
    Used in SettingsWidget and KernelEditor.

    Args:
        parent (QWidget): Parent widget for the file dialog and message boxes
        line_edit (QLineEdit): Line edit where the selected path will be inserted
    """
    # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
    answer = QFileDialog.getOpenFileName(
        parent, "Select Julia Executable (e.g. julia.exe on Windows)", os.path.abspath('C:\\')
    )
    if answer[0] == "":  # Canceled (american-english), cancelled (british-english)
        return
    # Check that it's not a directory
    if os.path.isdir(answer[0]):
        msg = "Please select a valid Julia Executable (file) and not a directory"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid Julia Executable", msg)
        return
    # Check that it's a file that actually exists
    if not os.path.exists(answer[0]):
        msg = "File {0} does not exist".format(answer[0])
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid Julia Executable", msg)
        return
    # Check that selected file at least starts with string 'julia'
    _, selected_file = os.path.split(answer[0])
    if not selected_file.lower().startswith("julia"):
        msg = "Selected file <b>{0}</b> is not a valid Julia Executable".format(selected_file)
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid Julia Executable", msg)
        return
    line_edit.setText(answer[0])
    return


def select_julia_project(parent, line_edit):
    """Shows file browser and inserts selected julia project dir to give line_edit.
    Used in SettingsWidget and KernelEditor.

    Args:
        parent (QWidget): Parent of QFileDialog
        line_edit (QLineEdit): Line edit where the selected path will be inserted
    """
    answer = QFileDialog.getExistingDirectory(parent, "Select Julia project directory", os.path.abspath("C:\\"))
    if not answer:  # Canceled (american-english), cancelled (british-english)
        return
    line_edit.setText(answer)


def select_python_interpreter(parent, line_edit):
    """Opens file browser where user can select a python interpreter (i.e. python.exe on Windows).
    Used in SettingsWidget and KernelEditor.

    Args:
        parent (QWidget): Parent widget for the file dialog and message boxes
        line_edit (QLineEdit): Line edit where the selected path will be inserted
    """
    # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
    answer = QFileDialog.getOpenFileName(
        parent, "Select Python Interpreter (e.g. python.exe on Windows)", os.path.abspath("C:\\")
    )
    if answer[0] == "":  # Canceled
        return
    # Check that it's not a directory
    if os.path.isdir(answer[0]):
        msg = "Please select a valid Python interpreter (file) and not a directory"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid Python Interpreter", msg)
        return
    # Check that selected file at least starts with string 'python'
    _, selected_file = os.path.split(answer[0])
    if not selected_file.lower().startswith("python"):
        msg = "Selected file <b>{0}</b> is not a valid Python interpreter".format(selected_file)
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid Python Interpreter", msg)
        return
    line_edit.setText(answer[0])
    return


def file_is_valid(parent, file_path, msgbox_title, extra_check=None):
    """Checks that given path is not a directory and it's a file that actually exists.
    In addition, can be used to check if the file name in given file path starts with
    the given extra_check string. Needed in SettingsWidget and KernelEditor because
    the QLineEdits are editable. Returns True when file_path is an empty string so that
    we can use default values (e.g. from line edit place holder text)

    Args:
        parent (QWidget): Parent widget for the message boxes
        file_path (str): Path to check
        msgbox_title (str): Title for message boxes
        extra_check (str): Optional, string that must match the file name of the given file_path (without extension)

    Returns:
        bool: True if given path is an empty string or if path is valid, False otherwise
    """
    if file_path == "":
        return True
    if os.path.isdir(file_path):
        msg = "Please select a file and not a directory"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, msgbox_title, msg)
        return False
    if not os.path.exists(file_path):
        msg = f"File {file_path} does not exist"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, msgbox_title, msg)
        return False
    if extra_check is not None:
        # Check that file name in given file path starts with the extra_check string (e.g. 'python' or 'julia')
        _, file_name = os.path.split(file_path)
        if not file_name.lower().startswith(extra_check):
            msg = f"Selected file <b>{file_name}</b> is not a valid {extra_check} file"
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(parent, msgbox_title, msg)
            return False
    return True


def dir_is_valid(parent, dir_path, msgbox_title):
    """Checks that given path is a directory. Needed in
    SettingsWdiget and KernelEditor because the QLineEdits
    are editable. Returns True when dir_path is an empty string so that
    we can use default values (e.g. from line edit place holder text)

    Args:
        parent (QWidget): Parent widget for the message box
        dir_path (str): Directory path to check
        msgbox_title (str): Message box title

    Returns:
        bool: True if given path is an empty string or if path is an existing directory, False otherwise
    """
    if dir_path == "":
        return True
    if not os.path.isdir(dir_path):
        msg = "Please select a valid directory"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, msgbox_title, msg)
        return False
    return True


class QuietLogger:
    def __getattr__(self, _):
        return self

    def __call__(self, *args, **kwargs):
        pass


def make_settings_dict_for_engine(app_settings):
    """Converts Toolbox settings to a dictionary acceptable by Engine.

    Args:
        app_settings (QSettings): Toolbox settings

    Returns:
        dict: Engine-compatible settings
    """
    # XXX: We may want to introduce a new group "executionSettings", for more clarity
    settings = {}
    app_settings.beginGroup("appSettings")
    for key in app_settings.childKeys():
        value = app_settings.value(key)
        try:
            json.dumps(value)
        except (TypeError, json.decoder.JSONDecodeError):
            continue
        settings[f"appSettings/{key}"] = value
    app_settings.endGroup()
    if "appSettings/workDir" not in settings:
        # Headless mode may execute on a system where we don't have any Toolbox settings available.
        # Make sure we set a sane work directory for Tools, at least.
        settings["appSettings/workDir"] = DEFAULT_WORK_DIR
    return settings


def make_icon_background(color):
    color0 = color.name()
    color1 = color.lighter(140).name()
    return f"qlineargradient(x1: 1, y1: 1, x2: 0, y2: 0, stop: 0 {color0}, stop: 1 {color1});"


def make_icon_toolbar_ss(color):
    icon_background = make_icon_background(color)
    # NOTE: border-style property needs to be set for QToolBar so the lineargradient works on GNOME desktop environment
    return f"QToolBar{{spacing: 6px; background: {icon_background}; padding: 3px; border-style: solid;}}"


def color_from_index(i, count, base_hue=0.0, saturation=1.0):
    golden_ratio = 0.618033988749895
    h = golden_ratio * (360 / count) * i
    h = ((base_hue + h) % 360) / 360
    # return QColor.fromHsvF(217 / 360, 0.60, 1.0, 1.0)
    return QColor.fromHsvF(h, saturation, 1.0, 1.0)
