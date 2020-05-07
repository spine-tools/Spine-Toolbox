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


class UpdateImporterSettingsCommand(SpineToolboxCommand):
    def __init__(self, importer, settings, importee):
        """Command to update Importer settings.

        Args:
            importer (spinetoolbox.project_items.importer.importer.Importer): the Importer
            settings (dict): the new settings
            importee (str): the filepath
        """
        super().__init__()
        self.importer = importer
        self.redo_settings = settings
        self.importee = importee
        self.undo_settings = copy.deepcopy(importer.settings.get(importee, {}))
        self.setText(f"change mapping settings of {importer.name}")

    def redo(self):
        self.importer.settings.setdefault(self.importee, {}).update(self.redo_settings)

    def undo(self):
        self.importer.settings[self.importee] = self.undo_settings


class UpdateImporterCancelOnErrorCommand(SpineToolboxCommand):
    def __init__(self, importer, cancel_on_error):
        """Command to update Importer cancel on error setting.

        Args:
            importer (spinetoolbox.project_items.importer.importer.Importer): the Importer
            cancel_on_error (bool): the new setting
        """
        super().__init__()
        self.importer = importer
        self.redo_cancel_on_error = cancel_on_error
        self.undo_cancel_on_error = not cancel_on_error
        self.setText(f"change cancel on error setting of {importer.name}")

    def redo(self):
        self.importer.set_cancel_on_error(self.redo_cancel_on_error)

    def undo(self):
        self.importer.set_cancel_on_error(self.undo_cancel_on_error)
