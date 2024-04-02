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

"""Provides the main() function."""
import os
import multiprocessing
import PySide6

dirname = os.path.dirname(PySide6.__file__)
plugin_path = os.path.join(dirname, "plugins", "platforms")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

# pylint: disable=wrong-import-position, wrong-import-order
from argparse import ArgumentParser
import sys
import logging
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

# Importing resources_icons_rc initializes resources and Font Awesome gets added to the application
from . import resources_icons_rc  # pylint: disable=unused-import
from spine_items import resources_icons_rc  # pylint: disable=unused-import

from .ui_main import ToolboxUI
from .version import __version__
from .headless import headless_main, Status
from .helpers import pyside6_version_check


def main():
    """Creates main window GUI and starts main event loop."""
    multiprocessing.freeze_support()
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if not pyside6_version_check():
        return 1
    _add_pywin32_system32_to_path()
    parser = _make_argument_parser()
    args = parser.parse_args()
    if args.execute_only or args.list_items or args.execute_remotely:
        return_code = headless_main(args)
        if return_code == Status.ARGUMENT_ERROR:
            parser.print_usage()
        return return_code
    app = QApplication(sys.argv)
    app.setApplicationName("Spine Toolbox")
    status = QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
    if status < 0:
        logging.warning("Could not load fonts from resources file. Some icons may not render properly.")
    window = ToolboxUI()
    window.show()
    QTimer.singleShot(0, lambda: window.init_project(args.project))
    # Enter main event loop and wait until exit() is called
    return_code = app.exec()
    return return_code


def _make_argument_parser():
    """Returns a command line argument parser configured for Toolbox use.

    Returns:
        ArgumentParser: Toolbox' command line argument parser
    """
    parser = ArgumentParser()
    version = f"Spine Toolbox {__version__}"
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("--list-items", help="list project items' names, do not open the GUI", action="store_true")
    parser.add_argument(
        "--mod-script", help="a Python script to augment the opened project (headless mode only)", metavar="SCRIPT"
    )
    parser.add_argument(
        "--execute-only", help="headless mode: execute given project, do not open the GUI", action="store_true"
    )
    parser.add_argument("project", help="project to open at startup", nargs="?", default="")
    parser.add_argument(
        "-s", "--select", action="append", help="select project item ITEM for execution", nargs="*", metavar="ITEM"
    )
    parser.add_argument(
        "-d",
        "--deselect",
        action="append",
        help="deselect project item ITEM for execution (takes precedence over --select)",
        nargs="*",
        metavar="ITEM",
    )
    parser.add_argument("--execute-remotely", help="execute remotely", action="append", metavar="SERVER CONFIG FILE")
    return parser


def _add_pywin32_system32_to_path():
    """Adds a directory to PATH on Windows that is required to make pywin32 work
    on (Conda) Python 3.8. See https://github.com/spine-tools/Spine-Toolbox/issues/1230."""
    if not sys.platform == "win32":
        return
    if sys.version_info[0:2] == (3, 8):
        p = os.path.join(sys.exec_prefix, "Lib", "site-packages", "pywin32_system32")
        if os.path.exists(p):
            os.environ["PATH"] = p + ";" + os.environ["PATH"]
