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
Functions for textual display of parameter values in table views.

:authors: A. Soininen (VTT)
:date:   12.7.2019
"""

from spinedb_api import (
    from_database,
    relativedelta_to_duration,
    ParameterValueFormatError,
    DateTime,
    Duration,
    TimePattern,
    TimeSeries,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
)


def format_for_DisplayRole(value_in_database):
    """Returns the value's database representation formatted for Qt.DisplayRole."""
    try:
        value = from_database(value_in_database)
    except ParameterValueFormatError:
        return "Error"
    if isinstance(value, TimeSeries):
        return "Time series"
    if isinstance(value, DateTime):
        return str(value.value)
    if isinstance(value, Duration):
        return relativedelta_to_duration(value.value)
    if isinstance(value, TimePattern):
        return "Time pattern"
    return value


def format_for_EditRole(value_in_database):
    """Returns the value's database representation formatted for Qt.EditRole."""
    # Just return the JSON representation
    return str(value_in_database)


def format_for_ToolTipRole(value_in_database):
    """Returns the value's database representation formatted for Qt.ToolTipRole."""
    try:
        value = from_database(value_in_database)
    except ParameterValueFormatError as error:
        return str(error)
    if isinstance(value, TimeSeriesFixedResolution):
        resolution = [relativedelta_to_duration(r) for r in value.resolution]
        resolution = ', '.join(resolution)
        return "Start: {}, resolution: [{}], length: {}".format(value.start, resolution, len(value))
    if isinstance(value, TimeSeriesVariableResolution):
        return "Start: {}, resolution: variable, length: {}".format(value.indexes[0], len(value))
    return None
