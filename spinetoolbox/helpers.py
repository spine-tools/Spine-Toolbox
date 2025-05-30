######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""General helper functions and classes."""
from __future__ import annotations
import bisect
import collections
from collections.abc import Callable, Iterable, Mapping
from contextlib import contextmanager
import datetime
from enum import Enum, unique
import functools
import glob
from html.parser import HTMLParser
import itertools
import json
import logging
import os
import pathlib
import re
import shutil
import sys
import tempfile
import time
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union  # pylint: disable=unused-import
from xml.etree import ElementTree
import matplotlib
from PySide6.QtCore import (
    QEvent,
    QFile,
    QIODevice,
    QModelIndex,
    QObject,
    QPoint,
    QRect,
    QSettings,
    QSize,
    Qt,
    QUrl,
    Slot,
)
from PySide6.QtCore import __version__ as qt_version
from PySide6.QtCore import __version_info__ as qt_version_info
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QCursor,
    QDesktopServices,
    QFont,
    QGuiApplication,
    QIcon,
    QIconEngine,
    QImageReader,
    QKeyEvent,
    QKeySequence,
    QPainter,
    QPalette,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
    QSyntaxHighlighter,
    QTextCharFormat,
    QUndoCommand,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFileIconProvider,
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSplitter,
    QStyle,
    QWidget,
)
from spine_engine.utils.serialization import deserialize_path
from spinedb_api import DatabaseMapping
from spinedb_api.db_mapping_base import PublicItem
from spinedb_api.helpers import group_consecutive
from spinedb_api.spine_io.gdx_utils import find_gams_directory
from .config import (
    DEFAULT_WORK_DIR,
    PLUGINS_PATH,
    PROJECT_FILENAME,
    PROJECT_LOCAL_DATA_DIR_NAME,
    PROJECT_LOCAL_DATA_FILENAME,
    SPECIFICATION_LOCAL_DATA_FILENAME,
)
from .font import TOOLBOX_FONT
from .logger_interface import LoggerInterface

if TYPE_CHECKING:
    from .ui_main import ToolboxUI

if sys.platform == "win32":
    import ctypes
    import pywintypes
    import win32con
    import win32gui

matplotlib.use("Qt5Agg")
matplotlib.rcParams.update({"font.size": 8})
logging.getLogger("matplotlib").setLevel(logging.WARNING)
_matplotlib_version = [int(x) for x in matplotlib.__version__.split(".") if x.isdigit()]
if _matplotlib_version[0] == 3 and _matplotlib_version[1] == 0:
    from pandas.plotting import register_matplotlib_converters

    register_matplotlib_converters()

DBMapPublicItems = dict[DatabaseMapping, list[PublicItem]]
DBMapDictItems = dict[DatabaseMapping, list[dict]]
DBMapTypedDictItems = dict[DatabaseMapping, dict[str, list[dict]]]


@unique
class LinkType(Enum):
    """Graphics scene's link types."""

    CONNECTION = "connection"
    JUMP = "jump"


def home_dir() -> str:
    """Returns user's home dir"""
    return str(pathlib.Path.home())


def format_log_message(msg_type: str, message: str, show_datetime: bool = True) -> str:
    """Adds color tags and optional time stamp to message.

    Args:
        msg_type: message's type; accepts only 'msg', 'msg_success', 'msg_warning', or 'msg_error'
        message: message to format
        show_datetime: True to add time stamp, False to omit it

    Returns:
        formatted message
    """
    color = {"msg": "white", "msg_success": "#00ff00", "msg_error": "#ff3333", "msg_warning": "yellow"}[msg_type]
    open_tag = f"<span style='color:{color};white-space: pre-wrap;'>"
    date_str = get_datetime(show=show_datetime)
    return open_tag + date_str + message + "</span>"


def busy_effect(func: Callable) -> Any:
    """Decorator to change the mouse cursor to 'busy' while a function is processed.

    Args:
        func (Callable): Decorated function.
    """

    @functools.wraps(func)
    def new_function(*args, **kwargs):
        # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))
        try:
            return func(*args, **kwargs)
        finally:
            # noinspection PyArgumentList
            QApplication.restoreOverrideCursor()

    return new_function


def create_dir(base_path: str, folder: str = "", verbosity: bool = False) -> None:
    """Create (input/output) directories recursively.

    Args:
        base_path: Absolute path to wanted dir
        folder: (Optional) Folder name. Usually short name of item.
        verbosity: True prints a message that tells if the directory already existed or if it was created.

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


def rename_dir(old_dir: str, new_dir: str, toolbox: ToolboxUI, box_title: str) -> bool:
    """Renames directory.

    Args:
        old_dir: Absolute path to directory that will be renamed
        new_dir: Absolute path to new directory
        toolbox: A toolbox to log messages and ask questions.
        box_title: The title of the message boxes, (e.g. "Undoing 'rename DC1 to DC2'")

    Returns:
        True if operation was successful, False otherwise
    """
    if os.path.exists(new_dir):
        msg = f"Directory <b>{new_dir}</b> already exists.<br/><br/>Would you like to overwrite its contents?"
        box = QMessageBox(
            QMessageBox.Icon.Question,
            box_title,
            msg,
            buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            parent=toolbox,
        )
        box.button(QMessageBox.StandardButton.Ok).setText("Overwrite")
        answer = box.exec()
        if answer != QMessageBox.StandardButton.Ok:
            return False
        shutil.rmtree(new_dir)
    try:
        shutil.move(old_dir, new_dir)
    except FileExistsError:
        # This is unlikely because of the above `if`, but still possible since another concurrent process
        # might have done things in between
        msg = f"Directory<br/><b>{new_dir}</b><br/>already exists"
        toolbox.information_box.emit(box_title, msg)
        return False
    except PermissionError as pe_e:
        logging.error(pe_e)
        msg = (
            f"Access to directory <br/><b>{old_dir}</b><br/>denied."
            f"<br/><br/>Possible reasons:"
            f"<br/>1. You don't have a permission to edit the directory"
            f"<br/>2. Windows Explorer is open in the directory"
            f"<br/><br/>Check these and try again."
        )
        toolbox.information_box.emit(box_title, msg)
        return False
    except OSError as os_e:
        logging.error(os_e)
        msg = (
            f"Renaming directory "
            f"<br/><b>{old_dir}</b> "
            f"<br/>to "
            f"<br/><b>{new_dir}</b> "
            f"<br/>failed."
            f"<br/><br/>Possibly reasons:"
            f"<br/>1. Windows Explorer is open in the directory."
            f"<br/>2. A file in the directory is open in another program. "
            f"<br/><br/>Check these and try again."
        )
        toolbox.information_box.emit(box_title, msg)
        return False
    return True


def open_url(url: str) -> bool:
    """Opens the given url in the appropriate Web browser for the user's desktop environment,
    and returns true if successful; otherwise returns false.

    If the URL is a reference to a local file (i.e., the URL scheme is "file") then it will
    be opened with a suitable application instead of a Web browser.

    Handle return value on caller side.

    Args:
        url: URL to open

    Returns:
        True if successful, False otherwise
    """
    return QDesktopServices.openUrl(QUrl(url, QUrl.ParsingMode.TolerantMode))


def set_taskbar_icon() -> None:
    """Set application icon to Windows taskbar."""
    if sys.platform == "win32":
        myappid = "{6E794A8A-E508-47C4-9319-1113852224D3}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


@Slot()
def supported_img_formats() -> None:
    """Checks if reading .ico files is supported."""
    img_formats = QImageReader().supportedImageFormats()
    img_formats_str = "\n".join(str(x) for x in img_formats)
    logging.debug("Supported Image formats:\n%s", img_formats_str)


def pyside6_version_check() -> bool:
    """Check that PySide6 version is at least 6.4.

    qt_version (str) is the Qt version used to compile PySide6. E.g. "6.4.1"
    qt_version_info (tuple) contains each version component separately e.g. (6, 4, 1)
    """
    if not (qt_version_info[0] == 6 and qt_version_info[1] >= 4):
        print(
            f"""Sorry for the inconvenience but,

            Spine Toolbox does not support PySide6 version {qt_version}.
            At the moment, PySide6 version must be 6.4 or greater.

            To upgrade PySide6 to latest supported version, run

                pip install -r requirements.txt --upgrade

            And start the application again.
            """
        )
        return False
    return True


def get_datetime(show: bool, date: bool = True) -> str:
    """Returns date and time string for appending into Event Log messages.

    Args:
        show: True returns date and time string. False returns empty string.
        date: Whether the date should be included in the result

    Returns:
        : datetime string or empty string if show is False
    """
    if not show:
        return ""
    t = datetime.datetime.now()
    time_str = f"{t.hour:02d}:{t.minute:02d}:{t.second:02d}"
    if not date:
        return f"[{time_str}] "
    date_str = f"{t.day:02d}-{t.month:02d}-{t.year:02d}"
    return f"[{date_str} {time_str}] "


@busy_effect
def copy_files(
    src_dir: str, dst_dir: str, includes: Optional[list[str]] = None, excludes: Optional[list[str]] = None
) -> int:
    """Function for copying files. Does not copy folders.

    Args:
        src_dir: Source directory
        dst_dir: Destination directory
        includes: Included files (wildcards accepted)
        excludes: Excluded files (wildcards accepted)

    Returns:
        Number of files copied
    """
    if includes is None:
        includes = ["*"]
    if excludes is None:
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
def erase_dir(path: str, verbosity: bool = False) -> bool:
    """Deletes a directory and all its contents without prompt.

    Args:
        path: Path to directory
        verbosity: Print logging messages or not

    Returns:
        True if operation was successful, False otherwise
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
def recursive_overwrite(logger: LoggerInterface, src: str, dst: str, silent: bool = True) -> None:
    """Copies everything from source directory to destination directory recursively.
    Overwrites existing files.

    Args:
        logger (LoggerInterface): Enables e.g. printing to Event Log
        src (str): Source directory
        dst (str): Destination directory
        silent (bool): If False, messages are sent to Event Log, If True, copying is done in silence
    """
    if os.path.isdir(src):
        if not os.path.isdir(dst):
            if not silent:
                logger.msg.emit(f"Creating directory <b>{dst}</b>")
            os.makedirs(dst)
        files = os.listdir(src)
        for file_name in list(files):
            # Avoid ending up in 'dst' as this would result in infinite recursion.
            file_path = os.path.join(src, file_name)
            if os.path.samefile(os.path.commonpath((file_path, dst)), file_path):
                files.remove(file_name)
                break
        for f in files:
            recursive_overwrite(logger, os.path.join(src, f), os.path.join(dst, f), silent)
    else:
        if not silent:
            _, src_filename = os.path.split(src)
            dst_dir, _ = os.path.split(dst)
            logger.msg.emit(f"Copying <b>{src_filename}</b> -> <b>{dst_dir}</b>")
        shutil.copyfile(src, dst)


def tuple_itemgetter(
    itemgetter_func: Callable[[Union[Sequence, Mapping]], Any], num_indexes: int
) -> Callable[[Union[Sequence, Mapping]], tuple]:
    """Change output of itemgetter to always be a tuple even for a single index.

    Args:
        itemgetter_func: item getter function
        num_indexes: number of indexes

    Returns:
        getter function that works with a single index
    """
    return (lambda item: (itemgetter_func(item),)) if num_indexes == 1 else itemgetter_func


def format_string_list(str_list: list[str]) -> str:
    """Returns a html unordered list from the given list of strings.
    Intended to print error logs as returned by spinedb_api.

    Args:
        str_list: list of strings to format

    Returns:
        formatted list
    """
    return "<ul>" + "".join(["<li>" + str(x) + "</li>" for x in str_list]) + "</ul>"


def rows_to_row_count_tuples(rows: Iterable[int]) -> list[tuple[int, int]]:
    """Breaks a list of rows into a list of (row, count) tuples corresponding to chunks of successive rows."""
    return [(first, last - first + 1) for first, last in group_consecutive(rows)]


class IconListManager:
    """A class to manage icons for icon list widgets."""

    def __init__(self, icon_size: QSize):
        self._icon_size = icon_size
        self.searchterms = {}
        self.model = QStandardItemModel()
        self.model.data = self._model_data

    @busy_effect
    def init_model(self) -> None:
        """Init model that can be used to display all icons in a list."""
        if self.searchterms:
            return
        qfile = QFile(":/fonts/fontawesome5-searchterms.json")
        qfile.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text)
        data = str(qfile.readAll().data(), "utf-8")
        qfile.close()
        self.searchterms = json.loads(data)
        items = []
        for codepoint, searchterms in self.searchterms.items():
            item = QStandardItem()
            display_icon = int(codepoint, 16)
            item.setData(display_icon, Qt.ItemDataRole.UserRole)
            item.setData(searchterms, Qt.ItemDataRole.UserRole + 1)
            items.append(item)
        self.model.invisibleRootItem().appendRows(items)

    def _model_data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Optional[Any]:
        """Creates icons as they're requested by the data() method, to reduce loading time.

        Args:
            index: index to the model
            role: data role

        Returns:
            role-dependent model data
        """
        if role == Qt.ItemDataRole.DisplayRole:
            return None
        if role != Qt.ItemDataRole.DecorationRole:
            return QStandardItemModel.data(self.model, index, role)
        display_icon = index.data(Qt.ItemDataRole.UserRole)
        return object_icon(display_icon)


def object_icon(display_icon: int) -> QIcon:
    """Creates and returns a QIcon corresponding to display_icon.

    Args:
        display_icon: icon id

    Returns:
        requested icon
    """
    icon_code, color_code = interpret_icon_id(display_icon)
    engine = CharIconEngine(chr(icon_code), color_code)
    return QIcon(engine)


class TransparentIconEngine(QIconEngine):
    """Specialization of QIconEngine with transparent background."""

    def pixmap(self, size=QSize(512, 512), mode=None, state=None):
        pm = QPixmap(size)
        pm.fill(Qt.GlobalColor.transparent)
        self.paint(QPainter(pm), QRect(QPoint(0, 0), size), mode, state)
        return pm


class CharIconEngine(TransparentIconEngine):
    """Specialization of QIconEngine used to draw font-based icons."""

    def __init__(self, char: str, color: Optional[int] = None):
        """
        Args:
            char: character to use as the icon
            color: icon color
        """
        super().__init__()
        self.char = char
        self.color = QColor(color)
        self.font = QFont(TOOLBOX_FONT.family)

    def paint(self, painter, rect, mode=None, state=None):
        painter.save()
        size = int(0.875 * round(min(rect.width(), rect.height())))
        self.font.setPixelSize(max(1, size))
        painter.setFont(self.font)
        if self.color:
            color = self.color
        else:
            palette = QPalette(QApplication.palette())
            if mode == QIcon.Mode.Disabled:
                palette.setCurrentColorGroup(QPalette.ColorGroup.Disabled)
            elif mode == QIcon.Mode.Active:
                palette.setCurrentColorGroup(QPalette.ColorGroup.Active)
            color = palette.buttonText().color()
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, self.char)
        painter.restore()


class ColoredIcon(QIcon):
    def __init__(self, icon_file_name: str, icon_color: QColor, icon_size, colored: bool = False):
        self._engine = ColoredIconEngine(icon_file_name, icon_color, icon_size, colored=colored)
        super().__init__(self._engine)

    def set_colored(self, colored: bool) -> None:
        self._engine.set_colored(colored)

    def color(self, mode=QIcon.Mode.Normal) -> QColor:
        return self._engine.color(mode=mode)


class ColoredIconEngine(QIconEngine):
    def __init__(self, icon_file_name: str, icon_color: QColor, icon_size: QSize, colored: bool = False):
        super().__init__()
        self._icon = QIcon(icon_file_name)
        self._icon_color = icon_color
        self._base_pixmap = self._icon.pixmap(icon_size)
        self._colored = False
        self._pixmaps: dict[tuple[QIcon.Mode, QIcon.State], QPixmap] = {}
        self.set_colored(colored)

    def color(self, mode: QIcon.Mode = QIcon.Mode.Normal) -> QColor:
        color = self._icon_color if self._colored else QColor("black")
        if mode == QIcon.Mode.Disabled:
            r, g, b, a = color.getRgbF()
            tint = 0.37255
            color = QColor.fromRgbF(r + (1.0 - r) * tint, g + (1.0 - g) * tint, b + (1.0 - b) * tint, a)
        return color

    def set_colored(self, colored: bool) -> None:
        if self._colored == colored:
            return
        self._colored = colored
        self._pixmaps.clear()

    def _make_pixmap(self, mode: QIcon.Mode, state: QIcon.State) -> QPixmap:
        if (mode, state) not in self._pixmaps:
            color = self.color(mode)
            self._pixmaps[mode, state] = color_pixmap(self._base_pixmap, color)
        return self._pixmaps[mode, state]

    def pixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State) -> QPixmap:
        return self._make_pixmap(mode, state).scaled(
            self._icon.actualSize(size), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )


def color_pixmap(pixmap: QPixmap, color: QColor) -> QPixmap:
    img = pixmap.toImage()
    for y in range(img.height()):
        for x in range(img.width()):
            color.setAlpha(img.pixelColor(x, y).alpha())
            img.setPixelColor(x, y, color)
    return QPixmap.fromImage(img)


def make_icon_id(icon_code: int, color_code: int) -> int:
    """Takes icon and color codes, and return equivalent integer.

    Args:
        icon_code: icon's code
        color_code: color code

    Returns:
        icon id
    """
    return icon_code + (color_code << 16)


def interpret_icon_id(display_icon: Optional[int]) -> tuple[int, int]:
    """Takes a display icon id and returns an equivalent tuple of icon and color code.

    Args:
        display_icon: icon id

    Returns:
        icon's code, color code
    """
    if not isinstance(display_icon, int) or display_icon < 0:
        return 0xF1B2, 0xFF000000
    icon_code = display_icon & 65535
    try:
        color_code = display_icon >> 16
    except OverflowError:
        color_code = 0
    return icon_code, color_code


def default_icon_id() -> int:
    """Creates a default icon id."""
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


def basic_console_icon(language: str) -> QIcon:
    """Returns an SVG icon for the given language or an empty QIcon if not available."""
    if language == "python":
        return QIcon(":/symbols/python-logo.svg")
    elif language == "julia":
        return QIcon(":/symbols/julia-logo.svg")
    else:
        return QIcon()


def ensure_window_is_on_screen(window: QWidget, size: QSize) -> None:
    """
    Checks if window is on screen and if not, moves and resizes it to make it visible on the primary screen.

    Args:
        window: a window to check
        size: desired window size if the window is moved
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
        window.setGeometry(
            QStyle.alignedRect(Qt.LayoutDirection.LeftToRight, Qt.AlignmentFlag.AlignCenter, size, screen_geometry)
        )


def first_non_null(s: Iterable) -> Optional[Any]:
    """Returns the first element in Iterable s that is not None."""
    try:
        return next(itertools.dropwhile(lambda x: x is None, s))
    except StopIteration:
        return None


def get_save_file_name_in_last_dir(
    qsettings: QSettings, key: str, parent: QWidget, caption: str, given_dir: str, filter_: str = ""
) -> tuple[str, str]:
    """Calls QFileDialog.getSaveFileName in the directory that was selected last time the dialog was accepted.

    Args:
        qsettings: A QSettings object where the last directory is stored
        key: The name of the entry in the above QSettings
        parent: parent widget
        parent, caption, given_dir, filter_: Args passed to QFileDialog.getSaveFileName

    Returns:
        filename and selected filter
    """
    dir_ = qsettings.value(key, defaultValue=given_dir)
    filename, selected_filter = QFileDialog.getSaveFileName(parent, caption, dir_, filter_)
    if filename:
        qsettings.setValue(key, os.path.dirname(filename))
    return filename, selected_filter


def get_open_file_name_in_last_dir(
    qsettings: QSettings, key: str, parent: QWidget, caption: str, given_dir: str, filter_: str = ""
) -> tuple[str, str]:
    dir_ = qsettings.value(key, defaultValue=given_dir)
    filename, selected_filter = QFileDialog.getOpenFileName(parent, caption, dir_, filter_)
    if filename:
        qsettings.setValue(key, os.path.dirname(filename))
    return filename, selected_filter


def try_number_from_string(text: str) -> Union[float, int, str]:
    """Tries to convert a string to integer or float.

    Args:
        text: string to convert

    Returns:
        converted value or text if conversion failed
    """
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text
    except TypeError:
        return text


def focused_widget_has_callable(parent: QWidget, callable_name: str) -> bool:
    """Returns True if the currently focused widget or one of its ancestors has the given callable."""
    focus_widget = parent.focusWidget()
    while focus_widget is not None and focus_widget is not parent:
        if hasattr(focus_widget, callable_name):
            method = getattr(focus_widget, callable_name)
            if callable(method):
                return True
        focus_widget = focus_widget.parentWidget()
    return False


def call_on_focused_widget(parent: QWidget, callable_name: str) -> Any:
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

    def eventFilter(self, obj: QObject, event: QKeyEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            if event.matches(QKeySequence.StandardKey.NextChild) or event.matches(
                QKeySequence.StandardKey.PreviousChild
            ):
                return True
        return QObject.eventFilter(self, obj, event)


def select_work_directory(parent: Optional[QWidget], line_edit: QLineEdit) -> None:
    """Shows file browser and inserts selected directory path to given line_edit.

    Args:
        parent: Parent widget for the file dialog and message boxes
        line_edit: Line edit where the selected path will be inserted
    """
    current_path = get_current_path(line_edit)
    initial_path = current_path if current_path is not None else home_dir()
    # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
    answer = QFileDialog.getExistingDirectory(parent, "Select Work Directory", initial_path)
    if answer == "":  # Cancel button clicked
        return
    selected_path = os.path.abspath(answer)
    line_edit.setText(selected_path)


def select_gams_executable(parent, line_edit):
    """Opens file browser where user can select a Gams executable (i.e. gams.exe on Windows).
    File browser initial dir priority:
        1. current path in line edit (first text, then placeholder text)
        2. Gams path from registry
        3. home_dir()

    Args:
        parent (QWidget, optional): Parent widget for the file dialog and message boxes
        line_edit (QLineEdit): Line edit where the selected path will be inserted
    """
    title = "Select GAMS Program"
    gams_path_from_registry = find_gams_directory()
    current_path = get_current_path(line_edit)
    if sys.platform == "win32":
        answer = get_path_from_native_open_file_dialog(
            parent, current_path, title + " (e.g. gams.exe on Windows)", gams_path_from_registry
        )
    else:
        initial_dir = current_path
        if not initial_dir:
            initial_dir = gams_path_from_registry
            if not initial_dir:
                initial_dir = home_dir()
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(parent, title, initial_dir)
    if answer[0] == "":  # Canceled (american-english), cancelled (british-english)
        return
    # Check that selected file at least starts with string 'gams'
    _, selected_file = os.path.split(answer[0])
    if not selected_file.lower().startswith("gams"):
        msg = f"Selected file <b>{selected_file}</b> may not be a valid GAMS program"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid GAMS Program", msg)
        return
    line_edit.setText(answer[0])


def select_julia_executable(parent, line_edit):
    """Opens file browser where user can select a Julia executable (i.e. julia.exe on Windows).

    Args:
        parent (QWidget, optional): Parent widget for the file dialog and message boxes
        line_edit (QLineEdit): Line edit where the selected path will be inserted
    """
    title = "Select Julia Executable"
    current_path = get_current_path(line_edit)
    if sys.platform == "win32":
        answer = get_path_from_native_open_file_dialog(parent, current_path, title + " (e.g. julia.exe on Windows)")
    else:
        initial_path = current_path if current_path is not None else home_dir()
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(parent, title, initial_path)
    if answer[0] == "":  # Canceled (american-english), cancelled (british-english)
        return
    # Check that the selected file starts with "julia"
    _, selected_file = os.path.split(answer[0])
    if not selected_file.lower().startswith("julia"):
        msg = f"Selected file <b>{selected_file}</b> is not a valid Julia Executable"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid Julia Executable", msg)
        return
    line_edit.setText(answer[0])


def select_julia_project(parent, line_edit):
    """Shows directory browser and inserts selected julia project dir to given line_edit.

    Args:
        parent (QWidget, optional): Parent of QFileDialog
        line_edit (QLineEdit): Line edit where the selected path will be inserted
    """
    current_path = get_current_path(line_edit)
    initial_path = current_path if current_path is not None else home_dir()
    answer = QFileDialog.getExistingDirectory(parent, "Select Julia project directory", initial_path)
    if not answer:  # Canceled (american-english), cancelled (british-english)
        return
    line_edit.setText(answer)


def select_python_interpreter(parent, line_edit):
    """Opens file browser where user can select a python interpreter (i.e. python.exe on Windows).

    Args:
        parent (QWidget): Parent widget for the file dialog and message boxes
        line_edit (QLineEdit): Line edit where the selected path will be inserted
    """
    title = "Select Python Interpreter"
    current_path = get_current_path(line_edit)
    if sys.platform == "win32":
        answer = get_path_from_native_open_file_dialog(parent, current_path, title + " (e.g. python.exe on Windows)")
    else:
        initial_path = current_path if current_path is not None else home_dir()
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(parent, title, initial_path)
    if answer[0] == "":  # Canceled
        return
    # Check that selected file at least starts with string 'python'
    _, selected_file = os.path.split(answer[0])
    if not selected_file.lower().startswith("python"):
        msg = f"Selected file <b>{selected_file}</b> is not a valid Python interpreter"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid Python Interpreter", msg)
        return
    line_edit.setText(answer[0])
    return


def select_conda_executable(parent, line_edit):
    """Opens file browser where user can select a conda executable.

    Args:
        parent (QWidget): Parent widget for the file dialog and message boxes
        line_edit (QLineEdit): Line edit where the selected path will be inserted
    """
    title = "Select Conda Executable"
    current_path = get_current_path(line_edit)
    if sys.platform == "win32":
        answer = get_path_from_native_open_file_dialog(
            parent, current_path, title + " (e.g. conda.exe or conda.bat on Windows)"
        )
    else:
        initial_path = current_path if current_path is not None else home_dir()
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(parent, title, initial_path)
    if answer[0] == "":  # Canceled
        return
    # Check that selected file at least starts with string 'conda'
    if not is_valid_conda_executable(answer[0]):
        _, selected_file = os.path.split(answer[0])
        msg = f"Selected file <b>{selected_file}</b> is not a valid Conda executable"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid Conda selected", msg)
        return
    line_edit.setText(answer[0])


def select_certificate_directory(parent, line_edit):
    """Shows file browser and inserts selected certificate directory to given line edit.

    Args:
        parent (QWidget, optional): Parent of QFileDialog
        line_edit (QLineEdit): Line edit where the selected dir path will be inserted
    """
    current_path = get_current_path(line_edit)
    initial_path = current_path if current_path is not None else home_dir()
    answer = QFileDialog.getExistingDirectory(parent, "Select certificates directory", initial_path)
    if not answer:
        return
    line_edit.setText(answer)


def select_root_directory(parent, line_edit, project_path):
    """Shows file browser and inserts selected root directory to given line edit.
    Used in Tool Properties.

    Args:
        parent (QWidget, optional): Parent of QFileDialog
        line_edit (QLineEdit): Line edit where the selected path will be inserted
        project_path (str): Project path
    """
    current_path = get_current_path(line_edit)
    initial_path = current_path if current_path is not None else project_path
    answer = QFileDialog.getExistingDirectory(parent, "Select root directory", initial_path)
    if not answer:
        return
    line_edit.setText(answer)
    return


def get_current_path(le):
    """Returns the text in the given line edit. If no text, returns the
    placeholder text if it is a valid path. If it's not a valid path,
    Returns None.
    """
    current_path = le.text().strip()
    if not current_path:
        current_path = le.placeholderText().strip()
        if not os.path.exists(current_path):
            return None
    return os.path.abspath(current_path)


def get_path_from_native_open_file_dialog(parent, current_path, title, initial_path=None):
    """Opens the native open file dialog on Windows.

    Args:
        parent (QWidget, optional): Parent widget for the file dialog
        current_path (str): If not None, the open file dialog initial dir is set according to the 'File' keyword.
            If None, initial dir set according to the 'InitialDir' keyword.
        title (str): Dialog title
        initial_path (str): Initial dir if something else than home_dir()

    Returns:
        tuple: [0] is the selected path, [1] is the calling function, [2] is the error message
    """
    init_path = initial_path if initial_path is not None else home_dir()
    # pylint: disable= possibly-used-before-assignment
    hwnd = win32gui.FindWindow(None, parent.windowTitle())
    pyhandle = pywintypes.HANDLE(hwnd)
    try:
        # NOTE: Paths must use Windows path separators (\) !
        # pylint: disable= possibly-used-before-assignment
        r = win32gui.GetOpenFileNameW(
            hwndOwner=pyhandle,
            File=current_path,
            InitialDir=init_path,
            Flags=win32con.OFN_EXPLORER
            | win32con.OFN_NOCHANGEDIR
            | win32con.OFN_PATHMUSTEXIST
            | win32con.OFN_FILEMUSTEXIST
            | win32con.OFN_NOVALIDATE
            | win32con.OFN_DONTADDTORECENT
            | win32con.OFN_HIDEREADONLY,
            Title=title,
        )
    except BaseException:  # GetOpenFileNameW throws pywinerror.error or similar when the user cancels the operation
        r = [""]
    return r


def is_valid_conda_executable(p):
    """Checks that given path points to an existing file and the file name starts with 'conda'.

    Args:
        p (str): Absolute path to a file
    """
    if not os.path.isfile(p):
        return False
    _, filename = os.path.split(p)
    if not filename.lower().startswith("conda"):
        return False
    return True


def file_is_valid(parent, file_path, msgbox_title, extra_check=None):
    """Checks that given path is not a directory and that it's a file and it exists.
    In addition, can be used to check if the file name in given file path starts with
    the given extra_check string. Needed in SettingsWidget and KernelEditor because
    the QLineEdits are editable. Returns True when file_path is an empty string so that
    we can use default values (e.g. from line edit place holder text). Returns also True
    when file_path is just 'python' or 'julia' so that user's can use the python or julia
    in PATH.

    Args:
        parent (QWidget): Parent widget for the message boxes
        file_path (str): Path to check
        msgbox_title (str): Title for message boxes
        extra_check (str, optional): String that must match the file name of the given file_path (without extension)

    Returns:
        bool: True if given path is an empty string or if path is valid, False otherwise
    """
    if file_path == "":
        return True
    if file_path.lower() in ("python", "python3", "julia"):
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


def dir_is_valid(parent, dir_path, msgbox_title, msg=None):
    """Checks that given path is a directory. Needed in
    SettingsWidget and KernelEditor because the QLineEdits
    are editable. Returns True when dir_path is an empty string so that
    we can use default values (e.g. from line edit placeholder text)

    Args:
        parent (QWidget): Parent widget for the message box
        dir_path (str): Directory path to check
        msgbox_title (str): Message box title
        msg (str): Warning message

    Returns:
        bool: True if given path is an empty string or if path is an existing directory, False otherwise
    """
    if not msg:
        msg = "Please select a valid directory"
    if dir_path == "":
        return True
    if not os.path.isdir(dir_path):
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

    def dump_group(group):
        app_settings.beginGroup(group)
        for key in app_settings.childKeys():
            value = app_settings.value(key)
            try:
                json.dumps(value)
            except (TypeError, json.decoder.JSONDecodeError):
                continue
            settings[f"{group}/{key}"] = value
        app_settings.endGroup()

    settings = {}
    dump_group("appSettings")
    dump_group("engineSettings")
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
    return f"QToolBar{{spacing: 0px; background: {icon_background}; padding: 3px; border-style: solid;}}"


def color_from_index(i, count, base_hue=0.0, saturation=1.0, value=1.0):
    golden_ratio = 0.618033988749895
    h = golden_ratio * (360 / count) * i
    h = ((base_hue + h) % 360) / 360
    return QColor.fromHsvF(h, saturation, value, 1.0)


def unique_name(prefix, existing):
    """
    Creates a unique name in the form `prefix (xx)` where xx is a counter value.
    When `prefix` already contains a counter `(xx)`, the value `xx` is updated.

    Args:
        prefix (str): name prefix
        existing (Iterable of str): existing names

    Returns:
        str: unique name
    """
    reserved = set()

    # check if `prefix` is already a duplicate and adjust if needed
    match = re.fullmatch(r"^(.*) \(([0-9]+)\)$", prefix)
    if match:
        prefix = match[1]
        reserved.add(int(match[2]))

    pattern = re.compile(rf"^{prefix} \(([0-9]+)\)$")
    for name in existing:
        match = pattern.fullmatch(name)
        if match:
            reserved.add(int(match[1]))

    free = len(reserved) + 1
    for i in range(1, len(reserved) + 1):
        if i not in reserved:
            free = i
            break
    return f"{prefix} ({free})"


def parse_specification_file(spec_path, logger):
    """Parses specification file.

    Args:
        spec_path (str): path to specification file
        logger (LoggerInterface): a logger

    Returns:
        dict: specification dict or None if the operation failed
    """
    try:
        with open(spec_path, "r") as fp:
            try:
                return json.load(fp)
            except ValueError:
                logger.msg_error.emit("Item specification file not valid")
                return None
    except FileNotFoundError:
        logger.msg_error.emit(f"Specification file <b>{spec_path}</b> does not exist")
        return None
    except OSError:
        logger.msg_error.emit(f"Specification file <b>{spec_path}</b> not found")
        return None


def load_specification_from_file(spec_path, local_data_dict, spec_factories, app_settings, logger):
    """Returns an Item specification from a definition file.

    Args:
        spec_path (str): Path of the specification definition file
        local_data_dict (dict): specifications local data dict
        spec_factories (dict): Dictionary mapping specification type to ProjectItemSpecificationFactory
        app_settings (QSettings): Toolbox settings
        logger (LoggerInterface): a logger

    Returns:
        ProjectItemSpecification: item specification or None if reading the file failed
    """
    spec_dict = parse_specification_file(spec_path, logger)
    if spec_dict is None:
        return None
    spec_dict["definition_file_path"] = spec_path
    try:
        spec = specification_from_dict(spec_dict, local_data_dict, spec_factories, app_settings, logger)
    except KeyError:
        spec = None
    if spec is not None:
        spec.definition_file_path = spec_path
    return spec


def specification_from_dict(spec_dict, local_data_dict, spec_factories, app_settings, logger):
    """Returns item specification from a dictionary.

    Args:
        spec_dict (dict): Dictionary with the specification
        local_data_dict (dict): specifications local data
        spec_factories (dict): Dictionary mapping specification name to ProjectItemSpecificationFactory
        app_settings (QSettings): Toolbox settings
        logger (LoggerInterface): a logger

    Returns:
        ProjectItemSpecification or NoneType: specification or None if factory isn't found.
    """
    # NOTE: If the spec doesn't have the "item_type" key, we can assume it's a tool spec
    item_type = spec_dict.get("item_type", "Tool")
    local_data = local_data_dict.get(item_type, {}).get(spec_dict["name"])
    if local_data is not None:
        merge_dicts(local_data, spec_dict)
    spec_factory = spec_factories.get(item_type)
    if spec_factory is None:
        return None
    return spec_factory.make_specification(spec_dict, app_settings, logger)


def plugins_dirs(app_settings):
    """Loads plugins.

    Args:
        app_settings (QSettings): Toolbox settings

    Returns:
        list of str: plugin directories
    """
    search_paths = {PLUGINS_PATH}
    search_paths |= set(app_settings.value("appSettings/pluginSearchPaths", defaultValue="").split(";"))
    # Plugin dirs are top-level dirs in all search paths
    plugin_dirs = []
    for path in search_paths:
        try:
            top_level_items = [os.path.join(path, item) for item in os.listdir(path)]
        except FileNotFoundError:
            continue
        plugin_dirs += [item for item in top_level_items if os.path.isdir(item)]
    return plugin_dirs


def load_plugin_dict(plugin_dir, logger):
    """Loads plugin dict from plugin directory.

    Args:
        plugin_dir (str): path of plugin dir with "plugin.json" in it
        logger (LoggerInterface): a logger

    Returns:
        dict: plugin dict or None if the operation failed
    """
    plugin_file = os.path.join(plugin_dir, "plugin.json")
    if not os.path.isfile(plugin_file):
        return None
    with open(plugin_file, "r") as fh:
        try:
            plugin_dict = json.load(fh)
        except json.decoder.JSONDecodeError:
            logger.msg_error.emit(f"Error in plugin file <b>{plugin_file}</b>. Invalid JSON.")
            return None
    try:
        plugin_dict["plugin_dir"] = plugin_dir
    except KeyError as key:
        logger.msg_error.emit(f"Error in plugin file <b>{plugin_file}</b>. Key '{key}' not found.")
        return None
    return plugin_dict


def load_plugin_specifications(plugin_dict, local_data_dict, spec_factories, app_settings, logger):
    """Loads plugin's specifications.

    Args:
        plugin_dict (dict): plugin dict
        local_data_dict (dict): specifications local data dictionary
        spec_factories (dict): Dictionary mapping specification name to ProjectItemSpecificationFactory
        app_settings (QSettings): Toolbox settings
        logger (LoggerInterface): a logger

    Returns:
        dict: mapping from plugin name to list of specifications or None if the operation failed
    """
    plugin_dir = plugin_dict["plugin_dir"]
    try:
        name = plugin_dict["name"]
        specifications = plugin_dict["specifications"]
    except KeyError as key:
        logger.msg_error.emit(f"Error in plugin file <b>{plugin_dir}</b>. Key '{key}' not found.")
        return None
    deserialized_paths = [deserialize_path(path, plugin_dir) for paths in specifications.values() for path in paths]
    plugin_specs = []
    for path in deserialized_paths:
        spec = load_specification_from_file(path, local_data_dict, spec_factories, app_settings, logger)
        if not spec:
            continue
        spec.plugin = name
        plugin_specs.append(spec)
    return {name: plugin_specs}


def load_specification_local_data(config_dir):
    """Loads specifications' project-specific data.

    Args:
        config_dir (str or Path): project config dir

    Returns:
        dict: specifications local data
    """
    local_data_path = pathlib.Path(config_dir, PROJECT_LOCAL_DATA_DIR_NAME, SPECIFICATION_LOCAL_DATA_FILENAME)
    if not local_data_path.exists():
        return {}
    with open(local_data_path) as data_file:
        return json.load(data_file)


DB_ITEM_SEPARATOR = " \u01C0 "
"""Display string to separate items such as entity names."""


def parameter_identifier(database, parameter, names, alternative):
    """Concatenates given information into parameter value identifier string.

    Args:
        database (str, optional): database's code name
        parameter (str): parameter's name
        names (list of str): name of the entity or class that holds the value
        alternative (str or NoneType): name of the value's alternative
    """
    parts = [database] if database is not None else []
    parts += [parameter]
    if alternative is not None:
        parts += [alternative]
    parts += [DB_ITEM_SEPARATOR.join(names)]
    return " - ".join(parts)


@contextmanager
def disconnect(signal, *slots):
    """Disconnects signal for the duration of a 'with' block.

    Args:
        signal (Signal): signal to disconnect
        *slots: slots to disconnect from
    """
    for slot in slots:
        signal.disconnect(slot)
    try:
        yield
    finally:
        # PyCharm thinks this code is unreachable; however, unit tests show that it works just fine.
        for slot in slots:
            signal.connect(slot)


class SignalWaiter(QObject):
    """A 'traffic light' that allows waiting for a signal to be emitted in another thread."""

    def __init__(self, condition=None, timeout=None):
        """
        Args:
            condition (function, optional): receiving the self.args and returning whether to stop waiting.
            timeout (float, optional): timeout in seconds; wait will raise after timeout
        """
        super().__init__()
        self._triggered = False
        self.args = ()
        self._condition = condition
        self._timeout = timeout
        self._start = time.monotonic() if self._timeout is not None else None

    @property
    def triggered(self) -> bool:
        return self._triggered

    def trigger(self, *args):
        """Signal receiving slot."""
        if self._triggered:
            return
        self._triggered = True if self._condition is None else self._condition(*args)
        self.args = args

    def wait(self):
        """Wait for signal to be received."""
        while not self._triggered:
            QApplication.processEvents()
            if self._timeout is not None and time.monotonic() - self._start > self._timeout:
                raise RuntimeError("timeout exceeded")


@contextmanager
def signal_waiter(signal, condition=None, timeout=None):
    """Gives a context manager that waits for the emission of given Qt signal.

    Args:
        signal (Any): signal to wait
        condition (Callable, optional): a callable that takes the signal's parameters and returns True to stop waiting
        timeout (float, optional): timeout in seconds; if None, wait indefinitely

    Yields:
        SignalWaiter: waiter instance
    """
    waiter = SignalWaiter(condition=condition, timeout=timeout)
    signal.connect(waiter.trigger)
    try:
        yield waiter
    finally:
        signal.disconnect(waiter.trigger)
        waiter.deleteLater()


class CustomSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.lexer = None
        self._formats = {}

    @property
    def formats(self):
        return self._formats

    def set_style(self, style):
        self._formats.clear()
        for ttype, tstyle in style:
            text_format = self._formats[ttype] = QTextCharFormat()
            if tstyle["color"]:
                brush = QBrush(QColor("#" + tstyle["color"]))
                text_format.setForeground(brush)
            if tstyle["bgcolor"]:
                brush = QBrush(QColor("#" + tstyle["bgcolor"]))
                text_format.setBackground(brush)
            if tstyle["bold"]:
                text_format.setFontWeight(QFont.Bold)
            if tstyle["italic"]:
                text_format.setFontItalic(True)
            if tstyle["underline"]:
                text_format.setFontUnderline(True)

    def yield_formats(self, text):
        if self.lexer is None:
            return
        for start, ttype, subtext in self.lexer.get_tokens_unprocessed(text):
            while True:
                text_format = self._formats.get(ttype)
                if text_format is not None:
                    break
                ttype = ttype.parent
            yield start, len(subtext), text_format

    def highlightBlock(self, text):
        for start, count, text_format in self.yield_formats(text):
            self.setFormat(start, count, text_format)


def inquire_index_name(model, column, title, parent_widget):
    """Asks for indexed parameter's index name and updates model accordingly.

    Args:
        model (IndexedValueTableModel or ArrayModel): a model with header that contains index names
        column (int): column index
        title (str): input dialog's title
        parent_widget (QWidget): dialog's parent widget
    """
    index_name = model.headerData(column, Qt.Orientation.Horizontal)
    dialog_flags = Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
    new_name, ok = QInputDialog.getText(parent_widget, title, "Index name:", text=index_name, flags=dialog_flags)
    if not ok:
        return
    model.setHeaderData(column, Qt.Orientation.Horizontal, new_name)


def preferred_row_height(widget, factor=1.5):
    return factor * widget.fontMetrics().lineSpacing()


def restore_ui(window, app_settings, settings_group):
    """Restores UI state from previous session.

    Args:
        window (QMainWindow)
        app_settings (QSettings)
        settings_group (str)
    """
    app_settings.beginGroup(settings_group)
    window_size = app_settings.value("windowSize")
    window_pos = app_settings.value("windowPosition")
    window_state = app_settings.value("windowState")
    window_maximized = app_settings.value("windowMaximized", defaultValue="false")
    n_screens = app_settings.value("n_screens", defaultValue=1)
    splitter_states = {
        splitter: app_settings.value(splitter.objectName() + "State") for splitter in window.findChildren(QSplitter)
    }
    app_settings.endGroup()
    original_size = window.size()
    if window_size:
        window.resize(window_size)
    if window_pos:
        window.move(window_pos)
    if window_state:
        window.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
    # noinspection PyArgumentList
    if len(QGuiApplication.screens()) < int(n_screens):
        # There are less screens available now than on previous application startup
        window.move(0, 0)  # Move this widget to primary screen position (0,0)
    for splitter, state in splitter_states.items():
        splitter.restoreState(state)
    ensure_window_is_on_screen(window, original_size)
    if window_maximized == "true":
        window.setWindowState(Qt.WindowMaximized)


def save_ui(window, app_settings, settings_group):
    """Saves UI state for next session.

    Args:
        window (QMainWindow)
        app_settings (QSettings)
        settings_group (str)
    """
    app_settings.beginGroup(settings_group)
    app_settings.setValue("windowSize", window.size())
    app_settings.setValue("windowPosition", window.pos())
    app_settings.setValue("windowState", window.saveState(version=1))
    app_settings.setValue("windowMaximized", window.windowState() == Qt.WindowMaximized)
    app_settings.setValue("n_screens", len(QGuiApplication.screens()))
    for splitter in window.findChildren(QSplitter):
        app_settings.setValue(splitter.objectName() + "State", splitter.saveState())
    app_settings.endGroup()


def bisect_chunks(current_data, new_data, key=None):
    """Finds insertion points for chunks of data using binary search.

    Args:
        current_data (list): sorted list where to insert new data
        new_data (list): data to insert
        key (Callable, optional): sort key

    Returns:
        tuple: sorted chunk of new data, insertion position
    """
    if key is not None:
        current_data = [key(x) for x in current_data]
    else:

        def key(x):
            # pylint: disable=function-redefined
            return x

    new_data = sorted(new_data, key=key)
    if not new_data:
        return ()
    item = new_data[0]
    chunk = [item]
    lo = bisect.bisect_left(current_data, key(item))
    for item in new_data[1:]:
        row = bisect.bisect_left(current_data, key(item), lo=lo)
        if row == lo:
            chunk.append(item)
            continue
        yield chunk, lo
        count = len(chunk)
        chunk = [item]
        lo = row + count
    yield chunk, lo


def load_project_dict(project_config_dir, logger):
    """Loads project dictionary from project directory.

    Args:
        project_config_dir (str): project's .spinetoolbox directory
        logger (LoggerInterface): a logger

    Returns:
        dict: project dictionary
    """
    load_path = os.path.abspath(os.path.join(project_config_dir, PROJECT_FILENAME))
    try:
        with open(load_path, "r") as fh:
            try:
                project_dict = json.load(fh)
            except json.decoder.JSONDecodeError:
                logger.msg_error.emit(f"Error in project file <b>{load_path}</b>. Invalid JSON.")
                return None
    except OSError:
        logger.msg_error.emit(f"Project file <b>{load_path}</b> missing")
        return None
    return project_dict


def load_local_project_data(project_config_dir, logger):
    """Loads local project data.

    Args:
        project_config_dir (Path or str): project's .spinetoolbox directory
        logger (LoggerInterface): a logger

    Returns:
        dict: project's local data
    """
    load_path = pathlib.Path(project_config_dir, PROJECT_LOCAL_DATA_DIR_NAME, PROJECT_LOCAL_DATA_FILENAME)
    if not load_path.exists():
        return {}
    with load_path.open() as fh:
        try:
            local_data_dict = json.load(fh)
        except json.decoder.JSONDecodeError:
            logger.msg_error.emit(f"Error in project's local data file <b>{load_path}</b>. Invalid JSON.")
            return {}
    return local_data_dict


def merge_dicts(source, target):
    """Merges two dictionaries that may contain nested dictionaries recursively.

    Args:
        source (dict): dictionary that will be merged to ``target``
        target (dict): target dictionary
    """
    for key, value in source.items():
        target_entry = target.get(key)
        if isinstance(value, dict) and target_entry is not None:
            merge_dicts(value, target_entry)
        else:
            target[key] = value


def fix_lightness_color(color, lightness=240):
    h, s, _, a = color.getHsl()
    return QColor.fromHsl(h, s, lightness, a)


@contextmanager
def scrolling_to_bottom(widget, tolerance=1):
    scrollbar = widget.verticalScrollBar()
    at_bottom = scrollbar.value() >= scrollbar.maximum() - tolerance
    try:
        yield None
    finally:
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())


def _is_metadata_item(item):
    """Identifies a database metadata record.

    Args:
        item (dict): database item

    Returns:
        bool: True if item is metadata item, False otherwise
    """
    return "name" in item and "value" in item


class HTMLTagFilter(HTMLParser):
    """HTML tag filter."""

    def __init__(self):
        super().__init__()
        self._text = ""

    def drain(self):
        text = self._text
        self._text = ""
        return text

    def handle_data(self, data):
        self._text += data

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self._text += "\n"

    def error(self, message):
        """To stop pylint whining"""


def same_path(path1, path2):
    """Checks if two paths are equal.

    This is a lightweight version of os.path.samefile(): it doesn't check if the paths
    point to the same file system object but rather takes into account file system
    case-sensitivity and such.

    Args:
        path1 (str): a path
        path2 (str): a path

    Returns:
        bool: True if paths point to the same
    """
    return os.path.normcase(path1) == os.path.normcase(path2)


def solve_connection_file(connection_file, connection_file_dict):
    """Returns the connection_file path, if it exists on this computer. If the path
    doesn't exist, assume that it points to a path on another computer, in which
    case store the contents of connection_file_dict into a tempfile.

    Args:
        connection_file (str): Path to a connection file
        connection_file_dict (dict) Contents of a connection file

    Returns:
        str: Path to a connection file on this computer.
    """
    if not os.path.exists(connection_file):
        fp = tempfile.TemporaryFile(mode="w+", suffix=".json", delete=False)
        json.dump(connection_file_dict, fp)
        connection_file = fp.name
        fp.close()
        return connection_file
    return connection_file


def remove_first(lst, items):
    for x in items:
        try:
            lst.remove(x)
            break
        except ValueError:
            pass


class SealCommand(QUndoCommand):
    """A 'meta' command that does not store undo data but can be used in mergeWith methods of other commands."""

    def __init__(self, command_id=1):
        """
        Args:
            command_id (int): command id
        """
        super().__init__("")
        self._id = command_id

    def redo(self):
        self.setObsolete(True)

    def id(self):
        return self._id


def plain_to_rich(text):
    """Turns plain strings into rich text.

    Args:
        text (str): string to convert

    Returns:
        str: rich text string
    """
    return "<qt>" + text + "</qt>"


def list_to_rich_text(data):
    """Turns a sequence of strings into rich text list.

    Args:
        data (Sequence of str): iterable to convert

    Returns:
        str: rich text string
    """
    return plain_to_rich("<br>".join(data))


def plain_to_tool_tip(text):
    """Turns plain strings into rich text and empty strings/Nones to None.

    Args:
        text (str, optional): string to convert

    Returns:
        str or NoneType: rich text string or None
    """
    return plain_to_rich(text) if text else None


class CustomPopupMenu(QMenu):
    """Popup menu master class for several popup menus."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget of this pop-up menu
        """
        super().__init__(parent=parent)
        self._parent = parent

    def add_action(self, text, slot, enabled=True, tooltip=None, icon=None):
        """Adds an action to the popup menu.

        Args:
            text (str): Text description of the action
            slot (method): Method to connect to action's triggered signal
            enabled (bool): Is action enabled?
            tooltip (str): Tool tip for the action
            icon (QIcon): Action icon
        """
        if icon is not None:
            action = self.addAction(icon, text, slot)
        else:
            action = self.addAction(text, slot)
        action.setEnabled(enabled)
        if tooltip is not None:
            action.setToolTip(tooltip)


def order_key(name):
    """Splits the given string into a list of its substrings and fills digits with '0'
    to ensure that e.g. 1 and 11 get sorted correctly.

    Example: "David_1946_Gilmour" -> ["David_", "000000001946", "_Gilmour"]
    """
    key_list = [f"{int(text):#012}" if text.isdigit() else text for text in re.split(r"(\d+|__)", name) if text]
    if key_list and key_list[0].isdigit():
        key_list.insert(0, "\U0010FFFF")
    return key_list


def add_keyboard_shortcut_to_tool_tip(action):
    """Adds keyboard shortcut to action's tool tip.

    Args:
        action (QAction): action to modify
    """
    shortcut = action.shortcut()
    if shortcut.isEmpty():
        return
    tool_tip = action.toolTip()
    if "<html>" not in tool_tip or "<p>" not in tool_tip:
        tool_tip = "<p>" + tool_tip + "</p>"
    root = ElementTree.fromstring(tool_tip)
    paragraphs = [paragraph for paragraph in root.iter("p")]
    new_root = ElementTree.Element("qt")
    for paragraph in paragraphs:
        new_root.append(paragraph)
    tool_tip_element = ElementTree.SubElement(new_root, "p")
    ElementTree.SubElement(tool_tip_element, "em").text = shortcut.toString()
    action.setToolTip(ElementTree.tostring(new_root, encoding="utf-8", method="html").decode())


def add_keyboard_shortcuts_to_action_tool_tips(ui):
    """Appends keyboard shortcuts to the tool tip texts of given UI's actions.

    Args:
        ui (object): UI to modify
    """
    for attribute in dir(ui):
        action = getattr(ui, attribute)
        if not isinstance(action, QAction):
            continue
        add_keyboard_shortcut_to_tool_tip(action)


def clear_qsettings(settings):
    """Clears Application Settings.

    Args:
        settings (QSettings): Settings instance that refers to
        'Spine Toolbox' application in a 'SpineProject' organization.
    """
    settings.clear()
    s1 = QSettings("SpineProject", "AddUpSpineOptWizard")
    s1.clear()
