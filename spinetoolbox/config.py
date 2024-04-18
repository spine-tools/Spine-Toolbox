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

"""Application constants and style sheets."""
import sys
import os
from pathlib import Path

LATEST_PROJECT_VERSION = 13

# For the Add/Update SpineOpt wizard
REQUIRED_SPINE_OPT_VERSION = "0.6.9"

# Invalid characters for directory names
# NOTE: "." is actually valid in a directory name but this is
# to prevent the user from creating directories like /..../
INVALID_CHARS = ["<", ">", ":", '"', "/", "\\", "|", "?", "*", "."]
# Invalid characters for file names
INVALID_FILENAME_CHARS = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]

# Paths to application, configuration file, default project and work dirs, and documentation index page
_frozen = getattr(sys, "frozen", False)
_path_to_executable = os.path.dirname(sys.executable if _frozen else __file__)
APPLICATION_PATH = os.path.realpath(_path_to_executable)
_program_root = APPLICATION_PATH if _frozen else os.path.join(APPLICATION_PATH, os.path.pardir)
DEFAULT_WORK_DIR = os.path.abspath(os.path.join(str(Path.home()), ".spinetoolbox", "work"))
if _frozen:
    DOCUMENTATION_PATH = os.path.abspath(os.path.join(_program_root, "docs", "html"))
else:
    DOCUMENTATION_PATH = os.path.abspath(os.path.join(_program_root, "docs", "build", "html"))
ONLINE_DOCUMENTATION_URL = "https://spine-toolbox.readthedocs.io/en/master/"

PLUGINS_PATH = os.path.abspath(os.path.join(str(Path.home()), ".spinetoolbox", "plugins"))

PLUGIN_REGISTRY_URL = "https://spine-tools.github.io/PluginRegistry/registry.json"
# Jupyter kernel constants
JUPYTER_KERNEL_TIME_TO_DEAD = 20

# Project constants
PROJECT_FILENAME = "project.json"
PROJECT_LOCAL_DATA_DIR_NAME = "local"
PROJECT_LOCAL_DATA_FILENAME = "project_local_data.json"
SPECIFICATION_LOCAL_DATA_FILENAME = "specification_local_data.json"
PROJECT_ZIP_FILENAME = "project_package"  # ZIP-file name for remote execution

# Stylesheets
STATUSBAR_SS = "QStatusBar{background-color: #EBEBE0; border-width: 1px; border-color: gray; border-style: groove;}"

BG_COLOR = "#19232D"
FG_COLOR = "#F0F0F0"

SETTINGS_SS = (
    "#SettingsForm{background-color: ghostwhite;}"
    "QLabel{color: black;}"
    "QGroupBox{border: 2px solid gray; "
    "background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #80B0FF, stop: 1 #e6efff);"
    "font-size: 14px;"
    "border-radius: 5px;"
    "margin-top: 0.5em;}"
    "QGroupBox:title{border-radius: 2px; "
    "background-color: white;"
    "border-radius: 5px;"
    "subcontrol-origin: margin;"
    "subcontrol-position: top center;"
    "padding-top: 0px;"
    "padding-bottom: 0px;"
    "padding-right: 3px;"
    "padding-left: 3px;}"
    "QCheckBox{outline-style: dashed; outline-width: 1px; outline-color: white;}"
    f"QPushButton{{background-color: #505F69; border: 1px solid #29353d; color: {FG_COLOR}; border-radius: 4px; padding: 3px; outline: none; min-width:80px}}"
    "QPushButton:disabled {background-color: #32414B; border: 1px solid #29353d; color: #787878; border-radius: 4px; padding: 3px;}"
    "QPushButton::menu-indicator {subcontrol-origin: padding; subcontrol-position: bottom right; bottom: 4px;}"
    "QPushButton:focus{background-color: #637683; border: 1px solid #148CD2;}"
    f"QPushButton:hover{{border: 1px solid #148CD2; color: {FG_COLOR};}}"
    f"QPushButton:pressed{{background-color: {BG_COLOR}; border: 1px solid {BG_COLOR};}}"
    "QSlider::groove:horizontal{background: #e1e1e1; border: 1px solid #a4a4a4; height: 5px; margin: 2px 0; border-radius: 2px;}"
    "QSlider::handle:horizontal{background: #fafafa; border: 1px solid #a4a4a4; width: 12px; margin: -5px 0; border-radius: 2px;}"
    "QSlider::add-page:horizontal{background: transparent;}"
    "QSlider::sub-page:horizontal{background: transparent;}"
)

# ICON_BACKGROUND = "qlineargradient(x1: 1, y1: 1, x2: 0, y2: 0, stop: 0 #cce0ff, stop: 1 #66a1ff);"
# ICON_TOOLBAR_SS = f"QToolBar{{spacing: 6px; background: {ICON_BACKGROUND}; padding: 3px; border-style: solid;}}"

TEXTBROWSER_SS = (
    f"QTextBrowser {{background-color: {BG_COLOR}; border: 1px solid #32414B; color: {FG_COLOR}; border-radius: 2px;}}"
    "QTextBrowser:hover,"
    "QTextBrowser:selected,"
    "QTextBrowser:pressed {border: 1px solid #668599;}"
)

# ToolboxUI stylesheet. A lot of widgets inherit this sheet.
MAINWINDOW_SS = (
    "QMainWindow::separator{width: 3px; background-color: lightgray; border: 1px solid white;}"
    f"QPushButton{{background-color: #505F69; border: 1px solid #29353d; color: {FG_COLOR}; border-radius: 4px; padding: 3px; outline: none; min-width: 75px;}}"
    "QPushButton:disabled {background-color: #32414B; border: 1px solid #29353d; color: #787878; border-radius: 4px; padding: 3px;}"
    "QPushButton::menu-indicator {subcontrol-origin: padding; subcontrol-position: bottom right; bottom: 4px;}"
    "QPushButton:focus{background-color: #637683; border: 1px solid #148CD2;}"
    f"QPushButton:hover{{border: 1px solid #148CD2; color: {FG_COLOR};}}"
    f"QPushButton:pressed{{background-color: {BG_COLOR}; border: 1px solid {BG_COLOR};}}"
    "QToolButton:focus{border-color: black; border-width: 1px; border-style: ridge;}"
    "QToolButton:pressed{background-color: #f2f2f2;}"
    "QToolButton::menu-indicator{width: 0px;}"
    "QCheckBox{padding: 2px; spacing: 10px; outline-style: dashed; outline-width: 1px; outline-color: black;}"
    "QComboBox QAbstractItemView{border: 1px solid darkgray; selection-background-color: lightgray;}"
    "QLineEdit:focus{border-color: black; border-width: 1px; border-style: ridge;}"
    "QTextEdit:focus{border-color: black; border-width: 1px; border-style: ridge;}"
    "QTreeView:focus{border-color: darkslategray; border-width: 2px; border-style: ridge;}"
)
