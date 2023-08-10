######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""Contains project-specific settings."""

import dataclasses


@dataclasses.dataclass
class ProjectSettings:
    """Spine Toolbox project settings."""

    enable_execute_all: bool = True

    def to_dict(self):
        """Serializes the settings into a dictionary.

        Returns:
            dict: serialized settings
        """
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(settings_dict):
        """Deserializes settings from dictionary.

        Args:
            settings_dict (dict): serialized settings

        Returns:
            ProjectSettings: deserialized settings
        """
        return ProjectSettings(**settings_dict)
