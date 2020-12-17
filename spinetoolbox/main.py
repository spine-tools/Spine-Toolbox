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
import os
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QApplication
from .spinedb_api_version_check import spinedb_api_version_check

# pylint: disable=wrong-import-position
# Check for spinedb_api version before we try to import possibly non-existent stuff below.
if not spinedb_api_version_check():
    sys.exit(1)

from .spine_engine_version_check import spine_engine_version_check

# Check for spine_engine version before we try to import possibly non-existent stuff below.
if not spine_engine_version_check():
    sys.exit(1)

# Importing resources_icons_rc initializes resources and Font Awesome gets added to the application
from . import resources_icons_rc  # pylint: disable=unused-import
from .load_project_items import upgrade_project_items

_skip_project_items_upgrade = False
if sys.argv[-1] == "--skip-project-items-upgrade":
    _skip_project_items_upgrade = True
    sys.argv.pop()

if not _skip_project_items_upgrade and upgrade_project_items():
    # Restart, otherwise the newer version is not picked.
    # Not even importlib.reload(site) or importlib.invalidate_caches() are sufficient,
    # because of .pyc files.
    python = sys.executable
    os.execl(python, '"' + python + '"', *sys.argv, "--skip-project-items-upgrade")

from .ui_main import ToolboxUI
from .version import __version__
from .headless import headless_main
from .helpers import pyside2_version_check


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

    parser = _make_argument_parser()
    args = parser.parse_args()
    if args.execute_only:
        return headless_main(args)
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
    parser.add_argument("--execute-only", help="execute given project only, do not open the GUI", action="store_true")
    parser.add_argument("project", help="project to open at startup", nargs="?", default="")
    return parser
