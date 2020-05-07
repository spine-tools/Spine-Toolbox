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
Undo/redo commands for the DataStore project item.

:authors: M. Marin (KTH)
:date:   5.5.2020
"""
from spinetoolbox.project_commands import SpineToolboxCommand


class UpdateDSURLCommand(SpineToolboxCommand):
    def __init__(self, ds, **kwargs):
        """Command to update DS url.

        Args:
            ds (DataStore): the DS
            kwargs: url keys and their values
        """
        super().__init__()
        self.ds = ds
        self.redo_kwargs = kwargs
        self.undo_kwargs = {k: self.ds._url[k] for k in kwargs}
        if len(kwargs) == 1:
            self.setText(f"change {list(kwargs.keys())[0]} of {ds.name}")
        else:
            self.setText(f"change url of {ds.name}")

    def redo(self):
        self.ds.do_update_url(**self.redo_kwargs)

    def undo(self):
        self.ds.do_update_url(**self.undo_kwargs)
