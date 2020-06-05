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
Undo/redo commands for the Importer project item.

:authors: M. Marin (KTH)
:date:   5.5.2020
"""
import copy
from spinetoolbox.project_commands import SpineToolboxCommand


class UpdateSettingsCommand(SpineToolboxCommand):
    """Command to update Importer settings."""

    def __init__(self, importer, settings, label):
        """
        Args:
            importer (spinetoolbox.project_items.importer.importer.Importer): the Importer
            settings (dict): the new settings
            label (str): settings file label
        """
        super().__init__()
        self._importer = importer
        self._redo_settings = settings
        self._label = label
        self._undo_settings = copy.deepcopy(importer.settings.get(label, {}))
        self.setText(f"change mapping settings of {importer.name}")

    def redo(self):
        self._importer.settings.setdefault(self._label, {}).update(self._redo_settings)

    def undo(self):
        self._importer.settings[self._label] = self._undo_settings
