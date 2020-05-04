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
Undo/redo commands for the Exporter project item.

:authors: A. Soininen (VTT)
:date:   30.4.2020
"""
from spinetoolbox.project_commands import SpineToolboxCommand


class UpdateCancelOnErrorCommand(SpineToolboxCommand):
    """Command to update Exporter cancel on error option."""

    def __init__(self, exporter, cancel_on_error):
        """
        Args:
            exporter (spinetoolbox.project_items.exporter.exporter.Exporter): the Exporter issuing the command
            cancel_on_error (bool): the new option
        """
        super().__init__()
        self._exporter = exporter
        self._redo_cancel_on_error = cancel_on_error
        self._undo_cancel_on_error = not cancel_on_error
        self.setText(f"change cancel on error setting of {exporter.name}")

    def redo(self):
        self._exporter.set_cancel_on_error(self._redo_cancel_on_error)

    def undo(self):
        self._exporter.set_cancel_on_error(self._undo_cancel_on_error)
