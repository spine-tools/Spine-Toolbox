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
Contains Data Connection's executable item as well as support utilities.

:authors: A. Soininen (VTT)
:date:   1.4.2020
"""
import os
import pathlib
from spinetoolbox.executable_item_base import ExecutableItemBase
from spinetoolbox.helpers import deserialize_path, shorten
from spinetoolbox.project_item_resource import ProjectItemResource
from .item_info import ItemInfo


class ExecutableItem(ExecutableItemBase):
    """The executable parts of Data Connection."""

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
        return ItemInfo.item_type()

    def _output_resources_forward(self):
        """See base class."""
        return [ProjectItemResource(self, "file", url=pathlib.Path(ref).as_uri()) for ref in self._files]

    @classmethod
    def from_dict(cls, item_dict, name, project_dir, app_settings, specifications, logger):
        """See base class."""
        references = item_dict["references"]
        file_references = [deserialize_path(r, project_dir) for r in references]
        data_dir = pathlib.Path(project_dir, ".spinetoolbox", "items", shorten(name))
        data_files = list()
        with os.scandir(data_dir) as scan_iterator:
            for entry in scan_iterator:
                if entry.is_file():
                    data_files.append(entry.path)
        return cls(name, file_references, data_files, logger)
