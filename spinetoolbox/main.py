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
import asyncio
import multiprocessing
import os
import PySide6

dirname = os.path.dirname(PySide6.__file__)
plugin_path = os.path.join(dirname, "plugins", "platforms")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

# pylint: disable=wrong-import-position, wrong-import-order
from argparse import ArgumentParser
import logging
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from .font import TOOLBOX_FONT
from .headless import Status, headless_main
from .helpers import pyside6_version_check
from .ui_main import ToolboxUI
from .version import __version__

# MacOS complains about missing item icons without the following line.
from spine_items import resources_icons_rc  # pylint: disable=unused-import  # isort: skip


def main():
    """Creates main window GUI and starts main event loop."""
    multiprocessing.freeze_support()
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if not pyside6_version_check():
        return 1
    parser = _make_argument_parser()
    args = parser.parse_args()
    if args.execute_only or args.list_items or args.execute_remotely:
        return_code = headless_main(args)
        if return_code == Status.ARGUMENT_ERROR:
            parser.print_usage()
        return return_code
    app = QApplication(sys.argv)
    app.setApplicationName("Spine Toolbox")
    TOOLBOX_FONT.get_family_from_font_database()
    window = ToolboxUI()
    window.show()
    QTimer.singleShot(0, lambda: window.init_tasks(args.project))
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
