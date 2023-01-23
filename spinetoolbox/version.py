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

"""Version info for Spine Toolbox package. Inspired by python sys.version and sys.version_info.

:author: P. Savolainen (VTT)
:date: 8.1.2020
"""

from typing import NamedTuple


class VersionInfo(NamedTuple):
    """A class for a named tuple containing the five components of the version number: major, minor,
    micro, releaselevel, and serial. All values except releaselevel are integers; the release level is
    'dev', 'alpha', 'beta', 'candidate', or 'final'."""

    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

    def __str__(self) -> str:
        """Create a version string following PEP 440"""
        version = f"{self.major}.{self.minor}.{self.micro}"
        if self.releaselevel == 'final':  # pylint: disable=no-else-return
            return version
        elif self.releaselevel.startswith('dev'):
            return version + f".dev{self.serial}"
        else:
            return version + f"-{self.releaselevel}.{self.serial}"


major = 0
minor = 6
micro = 17
releaselevel = "dev"
serial = 0
__version_info__ = VersionInfo(major, minor, micro, releaselevel, serial)
__version__ = str(__version_info__)
