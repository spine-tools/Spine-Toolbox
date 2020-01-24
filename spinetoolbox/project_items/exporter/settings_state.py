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
Provides the SettingsState enum.

:author: A. Soininen (VTT)
:date:   20.12.2019
"""

import enum


class SettingsState(enum.Enum):
    """State of export settings."""

    OK = enum.auto()
    """Settings OK."""
    FETCHING = enum.auto()
    """Settings are still being fetched/constructed."""
    INDEXING_PROBLEM = enum.auto()
    """There is a parameter value indexing issue."""
    ERROR = enum.auto()
    """An error prevents the creation of export settings."""
