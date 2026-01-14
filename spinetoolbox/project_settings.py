######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains project-specific settings."""
from __future__ import annotations
import dataclasses
from typing import Literal


@dataclasses.dataclass
class ProjectSettings:
    """Spine Toolbox project settings."""

    enable_execute_all: bool = True
    store_external_paths_as_relative: bool = False
    mode: Literal["author", "consumer"] = "author"

    def to_dict(self) -> dict:
        """Serializes the settings into a dictionary.

        Returns:
            serialized settings
        """
        return dataclasses.asdict(self)

    @staticmethod
    def from_dict(settings_dict: dict) -> ProjectSettings:
        """Deserializes settings from dictionary.

        Args:
            settings_dict: serialized settings

        Returns:
            deserialized settings
        """
        return ProjectSettings(**settings_dict)

    @staticmethod
    def dict_local_entries() -> list[tuple[str, ...]]:
        return [("mode",)]
