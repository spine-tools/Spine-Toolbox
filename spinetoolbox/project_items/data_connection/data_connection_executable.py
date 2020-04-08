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
Contains DataConnectionExecutable, DataConnection's executable counterpart as well as support utilities.

:authors: A. Soininen (VTT)
:date:   1.4.2020
"""
import pathlib
from spinetoolbox.executable_item import ExecutableItem
from spinetoolbox.project_item import ProjectItemResource


class DataConnectionExecutable(ExecutableItem):
    def __init__(self, name, file_references, data_files, logger):
        """
        Args:
            name (str): item's name
            file_references (list): a list of absolute paths to connected files
            data_files (list): a list of absolute paths to files in data connection's data directory
        """
        super().__init__(name, logger)
        self._files = file_references + data_files

    @staticmethod
    def item_type():
        """Returns DataConnectionExecutable's type identifier string."""
        return "Data Connection"

    def _output_resources_forward(self):
        """see base class"""
        return [ProjectItemResource(self, "file", url=pathlib.Path(ref).as_uri()) for ref in self._files]
