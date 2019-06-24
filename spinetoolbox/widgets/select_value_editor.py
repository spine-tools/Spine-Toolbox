######################################################################################################################
# Copyright (C) 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains functions to choose a (relationship) parameter value editor.

:author: A. Soininen (VTT)
:date:   6.6.2019
"""

from PySide2.QtCore import Qt
from spinedb_api import FixedTimeSteps, value_from_database, VariableTimeSteps
from widgets.fixed_step_time_series_editor_widget import FixedStepTimeSeriesEditor
from widgets.time_series_editor_widget import TimeSeriesEditor


def select_value_editor(model, index, parent):
    """Returns a widget to edit a (relationship) parameter value."""
    value = value_from_database(model.data(index, Qt.EditRole))
    if isinstance(value, FixedTimeSteps):
        return FixedStepTimeSeriesEditor(model, index, value, parent)
    if isinstance(value, VariableTimeSteps):
        return TimeSeriesEditor(model, index, value, parent)
    raise NotImplementedError("No editor widget available for value '{}'.".format(value.raw))
