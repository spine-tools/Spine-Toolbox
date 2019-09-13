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
Contains a minimal plugin loader infrastructure.

:author: P. Savolainen (VTT)
:date:   11.6.2019
"""

import importlib
import importlib.util
import os
import sys
from config import PLUGINS_PATH


def get_plugins(subpath):
    """Sniffs plugins directory, adds all found plugins to a dict and returns it."""
    searchpath = os.path.join(PLUGINS_PATH, subpath)
    plugins = dict()
    for plugin_name in os.listdir(searchpath):
        file_location = os.path.join(searchpath, plugin_name, "__init__.py")
        if not os.path.isfile(file_location):
            continue
        plugin_spec = importlib.util.spec_from_file_location(plugin_name, file_location)
        plugins[plugin_name] = plugin_spec
    return plugins


def load_plugin(plugin_spec):
    """Loads (imports) a plugin by using the given plugin spec.

    Args:
        plugin_spec (ModuleSpec): Spec of the plugin (module) to load
    """
    plugin = importlib.util.module_from_spec(plugin_spec)
    try:
        plugin_spec.loader.exec_module(plugin)
    except ModuleNotFoundError:
        # Add submodule search locations directly to sys path...
        sys.path.extend(plugin_spec.submodule_search_locations)
        plugin_spec.loader.exec_module(plugin)
    return plugin
