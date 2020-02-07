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
Provides the main() function.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

from argparse import ArgumentParser
import sys
import logging
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QApplication

# Importing resources_icons_rc initializes resources and Font Awesome gets added to the application
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from .ui_main import ToolboxUI
from .helpers import spinedb_api_version_check, pyside2_version_check, spine_engine_version_check
from .version import __version__


def main():
    """Creates main window GUI and starts main event loop."""
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    if not pyside2_version_check():
        return 1
    if not spinedb_api_version_check():
        return 1
    if not spine_engine_version_check():
        return 1
    parser = _make_argument_parser()
    args = parser.parse_args()
    app = QApplication(sys.argv)
    status = QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
    if status < 0:
        logging.warning("Could not load fonts from resources file. Some icons may not render properly.")
    window = ToolboxUI()
    window.show()
    window.init_project(args.project)
    # Enter main event loop and wait until exit() is called
    return_code = app.exec_()
    return return_code


def _make_argument_parser():
    """Returns a command line argument parser configured for Toolbox use."""
    parser = ArgumentParser()
    version = f"Spine Toolbox {__version__}"
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("project", help="project to open at startup", nargs="?", default="")
    return parser
