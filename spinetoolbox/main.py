######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

import sys
import logging
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QApplication
from .ui_main import ToolboxUI
from .helpers import spinedb_api_version_check, pyside2_version_check


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
    # QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont(":/fonts/fontawesome5-solid-webfont.ttf")
    window = ToolboxUI()
    window.show()
    window.init_project()
    # Enter main event loop and wait until exit() is called
    return_code = app.exec_()
    return return_code
