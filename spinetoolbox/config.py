#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Spine Toolbox default configurations.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   2.1.2018
"""

import sys
import os
from PySide2.QtGui import QColor

# General
SPINE_TOOLBOX_VERSION = '0.0.3'
ERROR_COLOR = QColor('red')
SUCCESS_COLOR = QColor('green')
NEUTRAL_COLOR = QColor('blue')
BLACK_COLOR = QColor('black')
# SPINE GREEN HTML: #99cc33 RGB: 153, 204, 51, alpha channel: 255
# SPINE BLUE HTML: #004ac2 RGB: 0, 74, 194, alpha channel: 255

# Application path, configuration file path and default project path
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.realpath(os.path.dirname(sys.executable))
    CONFIGURATION_FILE = os.path.abspath(os.path.join(APPLICATION_PATH, 'settings.conf'))
    DEFAULT_PROJECT_DIR = os.path.abspath(os.path.join(APPLICATION_PATH, 'projects'))
else:
    APPLICATION_PATH = os.path.realpath(os.path.dirname(__file__))
    CONFIGURATION_FILE = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, 'conf', 'settings.conf'))
    DEFAULT_PROJECT_DIR = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, 'projects'))

# Default settings
SETTINGS = {"project_directory": "",
            "open_previous_project": "false",
            "previous_project": "",
            "show_exit_prompt": "false",
            "logging_level": "2"}

# Stylesheets
STATUSBAR_SS = "QStatusBar{background-color: #EBEBE0; " \
               "border-width: 1px;\n " \
               "border-color: 'gray';\n " \
               "border-style: groove;\n " \
               "border-radius: 2px;\n}"

SETTINGS_SS = "#SettingsForm{background-color: ghostwhite;}" \
              "QLabel{color: white;}" \
              "QCheckBox{color: white;}" \
              "QGroupBox{border: 2px solid gray; " \
                    "background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #004AC2, stop: 1 #80B0FF);" \
                    "border-radius: 5px;" \
                    "margin-top: 0.5em;}" \
              "QGroupBox:title{border-radius: 2px; " \
                    "background-color: ghostwhite;" \
                    "subcontrol-origin: margin;" \
                    "subcontrol-position: top center;" \
                    "padding-top: 0px;" \
                    "padding-bottom: 0px;" \
                    "padding-right: 3px;" \
                    "padding-left: 3px;}"
