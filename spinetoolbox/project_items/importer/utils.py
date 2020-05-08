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
Contains Importer's utility functions.

:authors: A. Soininen (VTT)
:date:    6.5.2020
"""
from spinetoolbox.helpers import deserialize_path


def deserialize_mappings(mappings, project_path):
    """Returns mapping settings as dict with absolute paths as keys.

    Args:
        mappings (list): List where each element contains two dictionaries (path dict and mapping dict)
        project_path (str): Path to project directory

    Returns:
        dict: Dictionary with absolute paths as keys and mapping settings as values
    """
    abs_path_mappings = {}
    for source, mapping in mappings:
        abs_path_mappings[deserialize_path(source, project_path)] = mapping
    return abs_path_mappings
