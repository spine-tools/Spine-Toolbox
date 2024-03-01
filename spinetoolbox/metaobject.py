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

"""MetaObject class."""
from PySide6.QtCore import QObject
from spine_engine.utils.helpers import shorten


class MetaObject(QObject):
    """Class for an object which has a name, type, and some description."""

    def __init__(self, name, description):
        """
        Args:
            name (str): Object name
            description (str): Object description
        """
        super().__init__()
        self.name = name
        self.short_name = shorten(name)
        self.description = description

    def set_name(self, name):
        """Set object name and short name.
        Note: Check conflicts (e.g. name already exists)
        before calling this method.

        Args:
            name (str): New (long) name for this object
        """
        self.name = name
        self.short_name = shorten(name)

    def set_description(self, description):
        """Set object description.

        Args:
            description (str): Object description
        """
        self.description = description
