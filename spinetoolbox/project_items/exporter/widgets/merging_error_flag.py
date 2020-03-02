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
Error condition flags for Parameter merging.

:author: A. Soininen (VTT)
:date:   2.3.2020
"""

from enum import auto, Flag


class MergingErrorFlag(Flag):
    """Error flags for parameter merging."""

    NO_ERRORS = 0
    PARAMETER_NAME_MISSING = auto()
    DOMAIN_NAME_MISSING = auto()
    NO_PARAMETER_SELECTED = auto()
