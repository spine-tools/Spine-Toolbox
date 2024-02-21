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

"""Helpers and utilities for Spine Database editor."""


def string_to_display_icon(x):
    """Converts a 'foreign' string (from e.g. Excel) to entity class display icon.

    Args:
        x (str): string to convert

    Returns:
        int: display icon or None if conversion failed
    """
    try:
        return int(x)
    except ValueError:
        return None


TRUE_STRING = "true"
FALSE_STRING = "false"
GENERIC_TRUE = TRUE_STRING.casefold()
GENERIC_FALSE = FALSE_STRING.casefold()


def string_to_bool(x):
    """Converts a 'foreign' string (from e.g. Excel) to boolean.

    Args:
        x (str): string to convert

    Returns:
        bool: boolean value
    """
    return x.casefold() == GENERIC_TRUE
