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
Contains a minimal plugin loader infrastructure.

:author: P. Savolainen (VTT)
:date:   11.6.2019
"""

import importlib
import importlib.util
import os
import sys
from .config import PLUGINS_PATH


def get_plugins(subpath):
    """Returns a list of plugin (module) names found in given subpath,
    relative to plugins main directory.
    Adds the directory to sys.path if any plugins were found.

    Args:
        subpath (src): look for plugins in this subdirectory of the plugins main dir
    """
    searchpath = os.path.join(PLUGINS_PATH, subpath)
    if not os.path.isdir(searchpath):
        return []
    plugins = list()
    for plugin_name in os.listdir(searchpath):
        main_file_location = os.path.join(searchpath, plugin_name, "__init__.py")
        if os.path.isfile(main_file_location):
            plugins.append(plugin_name)
    if plugins and searchpath not in sys.path:
        sys.path.append(searchpath)
    return plugins


def load_plugin(plugin_name):
    """Loads (imports) a plugin given its name.

    Args:
        plugin_name (str): Name of the plugin (module) to load
    """
    plugin = importlib.import_module(plugin_name)
    return plugin
