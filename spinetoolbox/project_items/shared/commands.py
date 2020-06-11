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
Undo/redo commands that can be used by multiple project items.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   5.5.2020
"""
from spinetoolbox.project_commands import SpineToolboxCommand


class UpdateCancelOnErrorCommand(SpineToolboxCommand):
    def __init__(self, project_item, cancel_on_error):
        """Command to update Importer, Exporter, and Combiner cancel on error setting.

        Args:
            project_item (ProjectItem): Item
            cancel_on_error (bool): New setting
        """
        super().__init__()
        self._project_item = project_item
        self._redo_cancel_on_error = cancel_on_error
        self._undo_cancel_on_error = not cancel_on_error
        self.setText(f"change {project_item.name} cancel on error setting")

    def redo(self):
        self._project_item.set_cancel_on_error(self._redo_cancel_on_error)

    def undo(self):
        self._project_item.set_cancel_on_error(self._undo_cancel_on_error)


class ChangeItemSelectionCommand(SpineToolboxCommand):
    def __init__(self, project_item, selected, label):
        """Command to change file item's selection status.
        Used by Importers and Gimlets.

        Args:
            project_item (ProjectItem): Item
            selected (bool): True if the item is selected, False otherwise
            label (str): File label
        """
        super().__init__()
        self._item = project_item
        self._selected = selected
        self._label = label
        self.setText(f"change {project_item.name} file selection")

    def redo(self):
        self._item.set_file_selected(self._label, self._selected)

    def undo(self):
        self._item.set_file_selected(self._label, not self._selected)
