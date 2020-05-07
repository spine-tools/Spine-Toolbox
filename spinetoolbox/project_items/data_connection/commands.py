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
Undo/redo commands for the DataConnection project item.

:authors: M. Marin (KTH)
:date:   5.5.2020
"""
from spinetoolbox.project_commands import SpineToolboxCommand


class AddDCReferencesCommand(SpineToolboxCommand):
    def __init__(self, dc, paths):
        """Command to add DC references.

        Args:
            dc (DataConnection): the DC
            paths (set(str)): set of paths to add
        """
        super().__init__()
        self.dc = dc
        self.paths = paths
        self.setText(f"add references to {dc.name}")

    def redo(self):
        self.dc.do_add_files_to_references(self.paths)

    def undo(self):
        self.dc.do_remove_references(self.paths)


class RemoveDCReferencesCommand(SpineToolboxCommand):
    def __init__(self, dc, paths):
        """Command to remove DC references.

        Args:
            dc (DataConnection): the DC
            paths (list(str)): list of paths to remove
        """
        super().__init__()
        self.dc = dc
        self.paths = paths
        self.setText(f"remove references from {dc.name}")

    def redo(self):
        self.dc.do_remove_references(self.paths)

    def undo(self):
        self.dc.do_add_files_to_references(self.paths)
