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
cx-Freeze setup file for building importer_program.py into an application.
It is recommended that this is built with the same Python that is used
in building Spine Toolbox (Python3.6-64bit).

See cx_Freeze_setup.py for full instructions.

Usage:

On Windows:
1. Build the application into build/importer_program directory with command
'python cx_Freeze_importer_program_setup.py build'


:author: P. Savolainen (VTT)
:date:   1.4.2020
"""

import sys
import os
from cx_Freeze import setup, Executable


def main(argv):
    """Main."""
    python_dir = os.path.dirname(sys.executable)
    alembic_version_files = alembic_files(python_dir)
    # Most dependencies are automatically detected but some need to be manually included.
    build_exe_options = {
        "packages": ["os"],
        "excludes": ["tkinter", "matplotlib", "IPython", "ipykernel"],
        "includes": ["pygments.styles.default",
                     "ijson.compat",
                     "ijson.utils",
                     "ijson.backends.__init__",
                     "ijson.backends.python",
                     "ijson.backends.yajl",
                     "ijson.backends.yajl2",
                     "ijson.backends.yajl2_c",
                     "ijson.backends.yajl2_cffi",
                     "sqlalchemy.sql.default_comparator",
                     ],
        "include_files": alembic_version_files,
        "build_exe": "./build/importer_program/"
    }
    # Windows specific options
    if os.name == "nt":  # Windows specific options
        base = "Console"  # set this to "Win32GUI" to not show console, "Console" shows console
    # Other platforms
    else:
        base = None
    executables = [Executable("spinetoolbox/project_items/Importer/importer_program.py", base=base)]
    setup(
        name="Importer Program",
        version="0.0.1",
        description="Program that does the importing when executing the Importer project item.",
        author="Spine project consortium",
        options={"build_exe": build_exe_options},
        executables=executables,
    )


def alembic_files(python_dir):
    """Returns a list of tuples of files in python/Lib/site-packages/spinedb_api/alembic/versions.
    First item in tuple is the source file. Second item is the relative destination path to the install directory.
    """
    dest_dir = os.path.join("lib", "spinedb_api", "alembic", "versions")
    p = os.path.join(python_dir, "Lib", "site-packages", "spinedb_api", "alembic", "versions")
    files = list()
    for f in os.listdir(p):
        if f.endswith(".py"):
            files.append((os.path.abspath(os.path.join(p, f)), os.path.join(dest_dir, f)))
    return files


if __name__ == '__main__':
    sys.exit(main(sys.argv))
