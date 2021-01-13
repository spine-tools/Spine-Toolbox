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
from PySide2.QtWidgets import QApplication, QMessageBox, QGraphicsScene, QFileIconProvider, QStyle, QFileDialog
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
    QPainterPath,
    QPen,
    QKeySequence,
    QTextCursor,
    QPalette,
)
import spine_engine
from spine_engine.config import PYTHON_EXECUTABLE, JULIA_EXECUTABLE
from .config import REQUIRED_SPINE_ENGINE_VERSION


if os.name == "nt":
    import ctypes

matplotlib.use('Qt5Agg')
matplotlib.rcParams.update({"font.size": 8})
logging.getLogger("matplotlib").setLevel(logging.WARNING)
_matplotlib_version = [int(x) for x in matplotlib.__version__.split(".")]
if _matplotlib_version[0] == 3 and _matplotlib_version[1] == 0:
    from pandas.plotting import register_matplotlib_converters

    register_matplotlib_converters()


def format_event_message(msg_type, message, show_datetime=True):
    color = {"msg": "white", "msg_success": "#00ff00", "msg_error": "#ff3333", "msg_warning": "yellow"}[msg_type]
    open_tag = f"<span style='color:{color};white-space: pre-wrap;'>"
    date_str = get_datetime(show=show_datetime)
    return open_tag + date_str + message + "</span>"


def format_process_message(msg_type, message):
    color = {"msg": "white", "msg_error": "#ff3333"}[msg_type]
    open_tag = f"<span style='color:{color};white-space: pre-wrap;'>"
    return open_tag + message + "</span>"


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


def open_url(url, logger=None):
    result = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
    if logger is not None:
        logger.msg_error.emit(f"Unable to open URL <b>{url}</b>")
    return result


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
    """Check that PySide2 version is at least 5.14 but not 5.15, since
     we don't want to support 5.15 yet because user's may need to update
     their VC++ runtime libraries on Windows.

    qt_version is the Qt version used to compile PySide2 as string. E.g. "5.14.2"
    qt_version_info is a tuple with each version component of Qt used to compile PySide2. E.g. (5, 14, 2)
    """
    # print("Your QT version info is:{0} version string:{1}".format(qt_version_info, qt_version))
    if not (qt_version_info[0] == 5 and qt_version_info[1] == 14):
        print(
            """Sorry for the inconvenience but,

            Spine Toolbox does not support PySide2 version {0}.
            At the moment, supported PySide2 version is 5.14.

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
    """Change output of itemgetter to always be a tuple even for one index"""
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
        pixmap = self.create_object_pixmap(display_icon)
        return QIcon(pixmap)

    def create_object_pixmap(self, display_icon):
        """Create and return a pixmap corresponding to display_icon."""
        icon_code, color_code = interpret_icon_id(display_icon)
        engine = CharIconEngine(chr(icon_code), color_code)
        return engine.pixmap(self._icon_size)


class IconManager:
    """A class to manage object_class icons for spine db editors."""

    ICON_SIZE = QSize(512, 512)

    def __init__(self):
        self.obj_cls_icon_code_cache = {}  # A mapping from object_class name to display icon code
        self.icon_pixmap_cache = {}  # A mapping from display icon code to associated pixmap
        self.rel_cls_pixmap_cache = {}  # A mapping from object_class name list to associated pixmap
        self.group_obj_pixmap_cache = {}  # A mapping from class name to associated group pixmap
        self.searchterms = {}

    def create_object_pixmap(self, display_icon):
        """Create a pixmap corresponding to display_icon, cache it, and return it."""
        pixmap = self.icon_pixmap_cache.get(display_icon, None)
        if pixmap is None:
            icon_code, color_code = interpret_icon_id(display_icon)
            engine = CharIconEngine(chr(icon_code), color_code)
            pixmap = engine.pixmap(self.ICON_SIZE)
            self.icon_pixmap_cache[display_icon] = pixmap
        return pixmap

    def setup_object_pixmaps(self, object_classes):
        """Called after adding or updating object classes.
        Create the corresponding object pixmaps and clear obsolete entries
        from the relationship_class and entity groups pixmap caches."""
        for object_class in object_classes:
            self.create_object_pixmap(object_class["display_icon"])
            self.obj_cls_icon_code_cache[object_class["name"]] = object_class["display_icon"]
        object_class_names = [x["name"] for x in object_classes]
        dirty_keys = [k for k in self.rel_cls_pixmap_cache if any(x in object_class_names for x in k)]
        for k in dirty_keys:
            del self.rel_cls_pixmap_cache[k]
        for name in object_class_names:
            self.group_obj_pixmap_cache.pop(name, None)

    def object_pixmap(self, object_class_name):
        """A pixmap for the given object_class."""
        if object_class_name in self.obj_cls_icon_code_cache:
            display_icon = self.obj_cls_icon_code_cache[object_class_name]
            if display_icon in self.icon_pixmap_cache:
                return self.icon_pixmap_cache[display_icon]
        engine = CharIconEngine("\uf1b2", 0)
        return engine.pixmap(self.ICON_SIZE)

    def object_icon(self, object_class_name):
        """An icon for the given object_class."""
        return QIcon(self.object_pixmap(object_class_name))

    def relationship_pixmap(self, str_object_class_name_list):
        """A pixmap for the given object_class name list,
        created by rendering several object pixmaps next to each other."""
        if not str_object_class_name_list:
            engine = CharIconEngine("\uf1b3", 0)
            return engine.pixmap(self.ICON_SIZE)
        object_class_name_list = tuple(str_object_class_name_list.split(","))
        if object_class_name_list in self.rel_cls_pixmap_cache:
            return self.rel_cls_pixmap_cache[object_class_name_list]
        scene = QGraphicsScene()
        x = 0
        for j, object_class_name in enumerate(object_class_name_list):
            pixmap = self.object_pixmap(object_class_name)
            pixmap_item = scene.addPixmap(pixmap)
            if j % 2 == 0:
                y = 0
            else:
                y = -0.875 * 0.75 * pixmap_item.boundingRect().height()
                pixmap_item.setZValue(-1)
            pixmap_item.setPos(x, y)
            x += 0.875 * 0.5 * pixmap_item.boundingRect().width()
        pixmap = QPixmap(scene.itemsBoundingRect().toRect().size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        scene.render(painter)
        painter.end()
        self.rel_cls_pixmap_cache[object_class_name_list] = pixmap
        return pixmap

    def relationship_icon(self, str_object_class_name_list):
        """An icon for the given object_class name list."""
        return QIcon(self.relationship_pixmap(str_object_class_name_list))

    def group_object_pixmap(self, object_class_name):
        if object_class_name in self.group_obj_pixmap_cache:
            return self.group_obj_pixmap_cache[object_class_name]
        object_pixmap = self.object_pixmap(object_class_name)
        size = object_pixmap.size()
        width, height = size.width(), size.height()
        radius = width / 8
        pen_width = width / 32
        margin = width / 16
        pen = QPen(QApplication.palette().shadow().color())
        pen.setWidth(pen_width)
        path = QPainterPath()
        path.addRoundedRect(0, 0, width, height, radius, radius)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillPath(path, QApplication.palette().window())
        painter.setPen(pen)
        painter.drawRoundedRect(pixmap.rect().adjusted(pen_width, pen_width, -pen_width, -pen_width), radius, radius)
        painter.drawPixmap(
            pixmap.rect().adjusted(margin, margin, -width / 2, -height / 2), object_pixmap, object_pixmap.rect()
        )
        painter.drawPixmap(
            pixmap.rect().adjusted(width / 2, margin, -margin, -height / 2), object_pixmap, object_pixmap.rect()
        )
        painter.drawPixmap(
            pixmap.rect().adjusted(width / 2, height / 2, -margin, -margin), object_pixmap, object_pixmap.rect()
        )
        painter.drawPixmap(
            pixmap.rect().adjusted(margin, height / 2, -width / 2, -margin), object_pixmap, object_pixmap.rect()
        )
        painter.end()
        self.group_obj_pixmap_cache[object_class_name] = pixmap
        return pixmap

    def group_object_icon(self, object_class_name):
        return QIcon(self.group_object_pixmap(object_class_name))


class CharIconEngine(QIconEngine):
    """Specialization of QIconEngine used to draw font-based icons."""

    def __init__(self, char, color=None):
        super().__init__()
        self.char = char
        self.color = color
        self.font = QFont('Font Awesome 5 Free Solid')

    def paint(self, painter, rect, mode=None, state=None):
        painter.save()
        size = 0.875 * round(rect.height())
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

    def pixmap(self, size=QSize(512, 512), mode=None, state=None):
        pm = QPixmap(size)
        pm.fill(Qt.transparent)
        self.paint(QPainter(pm), QRect(QPoint(0, 0), size), mode, state)
        return pm


def make_icon_id(icon_code, color_code):
    """Take icon and color codes, and return equivalent integer."""
    return icon_code + (color_code << 16)


def interpret_icon_id(display_icon):
    """Take a display icon integer and return an equivalent tuple of icon and color code."""
    if not isinstance(display_icon, int) or display_icon < 0:
        return 0xF1B2, 0
    icon_code = display_icon & 65535
    try:
        color_code = display_icon >> 16
    except OverflowError:
        color_code = 0
    return icon_code, color_code


def default_icon_id():
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
                method()
                break
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


def python_interpreter(app_settings):
    """Returns the full path to Python interpreter depending on
    user's settings and whether the app is frozen or not.

    Args:
        app_settings (QSettings): Application preferences

    Returns:
        str: Path to python executable
    """
    python_path = app_settings.value("appSettings/pythonPath", defaultValue="")
    return resolve_python_interpreter(python_path)


def resolve_python_interpreter(python_path):
    """Solves the full path to Python interpreter and returns it."""
    if python_path != "":
        path = python_path
    else:
        if not getattr(sys, "frozen", False):
            path = sys.executable  # Use current Python
        else:
            # We are frozen
            p = resolve_python_executable_from_path()
            if p != "":
                path = p  # Use Python from PATH
            else:
                path = PYTHON_EXECUTABLE  # Use embedded <app_install_dir>/Tools/python.exe
    return path


def resolve_python_executable_from_path():
    """[Windows only] Returns full path to Python executable in user's PATH env variable.
    If not found, returns an empty string.

    Note: This looks for python.exe so this is Windows only.
    Update needed to PYTHON_EXECUTABLE to make this os independent.
    """
    p = ""
    executable_paths = os.get_exec_path()
    for path in executable_paths:
        if "python" in path.casefold():
            python_candidate = os.path.join(path, "python.exe")
            if os.path.isfile(python_candidate):
                p = python_candidate
    return p


def resolve_julia_executable_from_path():
    """Returns full path to Julia executable in user's PATH env variable.
    If not found, returns an empty string.

    Note: In the long run, we should decide whether this is something we want to do
    because adding julia-x.x./bin/ dir to the PATH is not recommended because this
    also exposes some .dlls to other programs on user's (windows) system. I.e. it
    may break other programs, and this is why the Julia installer does not
    add (and does not even offer the chance to add) Julia to PATH.
    """
    p = ""
    executable_paths = os.get_exec_path()
    for path in executable_paths:
        if "julia" in path.casefold():
            julia_candidate = os.path.join(path, JULIA_EXECUTABLE)
            if os.path.isfile(julia_candidate):
                p = julia_candidate
    return p


class QuietLogger:
    def __getattr__(self, _):
        return self

    def __call__(self, *args, **kwargs):
        pass
