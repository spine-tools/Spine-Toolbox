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
Utility functions for .gdx import/export.

:author: A. Soininen (VTT)
:date:   7.1.2020
"""

import os
import sys

if sys.platform == 'win32':
    import winreg


def _python_interpreter_bitness():
    """Returns 64 for 64bit Python interpreter or 32 for 32bit interpreter."""
    # As recommended in Python's docs:
    # https://docs.python.org/3/library/platform.html#cross-platform
    return 64 if sys.maxsize > 2 ** 32 else 32


def _windows_dlls_exist(gams_path):
    """Returns True if requred DLL files exist in given GAMS installation path."""
    bitness = _python_interpreter_bitness()
    # This DLL must exist on Windows installation
    dll_name = "gdxdclib{}.dll".format(bitness)
    dll_path = os.path.join(gams_path, dll_name)
    return os.path.isfile(dll_path)


def find_gams_directory():
    """
    Returns GAMS installation directory or None if not found.

    On Windows systems, this function looks for `gams.location` in registry;
    on other systems the `PATH` environment variable is checked.

    Returns:
        a path to GAMS installation directory or None if not found.
    """
    if sys.platform == "win32":
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "gams.location") as gams_location_key:
                gams_path, _ = winreg.QueryValueEx(gams_location_key, None)
                if not _windows_dlls_exist(gams_path):
                    return None
                return gams_path
        except FileNotFoundError:
            return None
    executable_paths = os.get_exec_path()
    for path in executable_paths:
        if "gams" in path.casefold():
            return path
    return None
