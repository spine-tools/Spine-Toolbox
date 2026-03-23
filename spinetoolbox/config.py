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
import os
from pathlib import Path
import sys
from typing import Literal

LATEST_PROJECT_VERSION: Literal[13] = 13

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
SPINE_TOOLBOX_REPO_URL = "https://github.com/spine-tools/Spine-Toolbox"

PLUGINS_PATH = os.path.abspath(os.path.join(str(Path.home()), ".spinetoolbox", "plugins"))

PLUGIN_REGISTRY_URL = "https://spine-tools.github.io/PluginRegistry/registry.json"
# Jupyter kernel constants
JUPYTER_KERNEL_TIME_TO_DEAD = 20

# Project constants
PROJECT_CONFIG_DIR_NAME: Literal[".spinetoolbox"] = ".spinetoolbox"
PROJECT_FILENAME: Literal["project.json"] = "project.json"
PROJECT_LOCAL_DATA_DIR_NAME: Literal["local"] = "local"
PROJECT_LOCAL_DATA_FILENAME: Literal["project_local_data.json"] = "project_local_data.json"
PROJECT_CONSUMER_REPLAY_FILENAME: Literal["consumer_replay.json"] = "consumer_replay.json"
SPECIFICATION_LOCAL_DATA_FILENAME: Literal["specification_local_data.json"] = "specification_local_data.json"
PROJECT_ZIP_FILENAME: Literal["project_package"] = "project_package"  # ZIP-file name for remote execution

FG_COLOR = "#F0F0F0"
