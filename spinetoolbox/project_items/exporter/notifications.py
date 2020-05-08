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
Contains the Notifications class.

:author: A. Soininen (VTT)
:date:   6.5.2020
"""
from PySide2.QtCore import QObject, Signal, Slot
from .settings_state import SettingsState


class Notifications(QObject):
    """
    Holds flags for different error conditions.

    Attributes:
        duplicate_output_file_name (bool): if True there are duplicate output file names
        missing_output_file_name (bool): if True the output file name is missing
        missing_parameter_indexing (bool): if True there are indexed parameters without indexing domains
        erroneous_database (bool): if True the database has issues
    """

    changed_due_to_settings_state = Signal()
    """Emitted when notifications have changed due to changes in settings state."""

    def __init__(self):
        super().__init__()
        self.duplicate_output_file_name = False
        self.missing_output_file_name = False
        self.missing_parameter_indexing = False
        self.erroneous_database = False

    def __ior__(self, other):
        """
        ORs the flags with another notifications.

        Args:
            other (Notifications): a Notifications object
        """
        self.duplicate_output_file_name |= other.duplicate_output_file_name
        self.missing_output_file_name |= other.missing_output_file_name
        self.missing_parameter_indexing |= other.missing_parameter_indexing
        self.erroneous_database |= other.erroneous_database
        return self

    @Slot("QVariant")
    def update_settings_state(self, state):
        """Updates the notifications according to settings state."""
        changed = False
        is_erroneous = state == SettingsState.ERROR
        if self.erroneous_database != is_erroneous:
            self.erroneous_database = is_erroneous
            changed = True
        is_problem = state == state.INDEXING_PROBLEM
        if self.missing_parameter_indexing != is_problem:
            self.missing_parameter_indexing = is_problem
            changed = True
        if changed:
            self.changed_due_to_settings_state.emit()
