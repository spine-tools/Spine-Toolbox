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
SPINE_TOOLBOX_VERSION = "0.0.5"
ERROR_COLOR = QColor('red')
SUCCESS_COLOR = QColor('green')
NEUTRAL_COLOR = QColor('blue')
BLACK_COLOR = QColor('black')
# SPINE GREEN HTML: #99cc33 RGBa: 153, 204, 51, 255
# SPINE BLUE HTML: #004ac2 RGBa: 0, 74, 194, 255
# Selected characters that are not allowed in folder names
INVALID_CHARS = ["<", ">", ":", "\"", "/", "\\", "|", "?", "*", "."]
# "." is actually valid in a folder name but this is
# to prevent the user from creating folders like /..../

# Application path, configuration file path and default project path
if getattr(sys, "frozen", False):
    APPLICATION_PATH = os.path.realpath(os.path.dirname(sys.executable))
    CONFIGURATION_FILE = os.path.abspath(os.path.join(APPLICATION_PATH, "settings.conf"))
    DEFAULT_PROJECT_DIR = os.path.abspath(os.path.join(APPLICATION_PATH, "projects"))
else:
    APPLICATION_PATH = os.path.realpath(os.path.dirname(__file__))
    CONFIGURATION_FILE = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "conf", "settings.conf"))
    DEFAULT_PROJECT_DIR = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "projects"))

# GAMS
if not sys.platform == "win32":
    GAMS_EXECUTABLE = "gams"
    GAMSIDE_EXECUTABLE = "gamside"
else:
    GAMS_EXECUTABLE = "gams.exe"
    GAMSIDE_EXECUTABLE = "gamside.exe"

# Required and optional keywords for Tool candidate definition files
REQUIRED_KEYS = ['name', 'description', 'includes']
OPTIONAL_KEYS = ['short_name', 'inputfiles', 'opt_inputfiles', 'outputfiles', 'cmdline_args']
LIST_REQUIRED_KEYS = ['includes', 'inputfiles', 'opt_inputfiles', 'outputfiles']  # These should be lists

# Default settings
SETTINGS = {"project_directory": "",
            "open_previous_project": "false",
            "previous_project": "",
            "show_exit_prompt": "false",
            "logging_level": "2",
            "datetime": "true",
            "gams_path": ""}

# Stylesheets
# TODO: Check necessity of extra hyphens in 'gray'
STATUSBAR_SS = "QStatusBar{" \
                    "background-color: #EBEBE0;" \
                    "border-width: 1px;" \
                    "border-color: 'gray';" \
                    "border-style: groove;" \
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

ICON_TOOLBAR_SS = "QToolBar{spacing: 6px; " \
                    "background-color: qlineargradient(x1: 1, y1: 1, x2: 0, y2: 0, stop: 0 #cce0ff, stop: 1 #66a1ff);" \
                    "padding: 3px;}" \
                  "QToolButton{background-color: white;" \
                    "border-width: 1px;" \
                    "border-style: inset;" \
                    "border-color: darkslategray;" \
                    "border-radius: 2px;}" \
                  "QLabel{color:black;}"

EVENTLOG_SS = "QTextBrowser{background-color: black;}"
