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
cx-Freeze setup file for Spine Toolbox.

Usage:
- Build the application into build/ directory with command 'python cx_Freeze_setup.py build'
- Package the built application into an installer file for distribution:
1. On Windows, compile setup.iss file with Inno Setup. This will create a single-file (.exe) installer.
2. On other platforms, use setup.py (this file) and Cx_Freeze (see Cx_Freeze documentation for help)

:author: P. Savolainen (VTT)
:date:   29.5.2018
"""

import os
import sys
from cx_Freeze import setup, Executable
from spinetoolbox.config import APPLICATION_PATH

version = {}
with open("spinetoolbox/version.py") as fp:
    exec(fp.read(), version)


def main(argv):
    """Main of cx_Freeze_setup.py."""
    python_dir = os.path.dirname(sys.executable)
    os.environ['TCL_LIBRARY'] = os.path.join(python_dir, "tcl", "tcl8.6")
    os.environ['TK_LIBRARY'] = os.path.join(python_dir, "tcl", "tk8.6")
    # tcl86t.dll and tk86t.dll are required by tkinter, which in turn is required by matplotlib
    tcl86t_dll = os.path.join(python_dir, "DLLs", "tcl86t.dll")
    tk86t_dll = os.path.join(python_dir, "DLLs", "tk86t.dll")
    # Path to built documentation (No need for sources)
    doc_path = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "docs", "build"))
    # Paths to files that should be included (Changelog, readme, licence files)
    changelog_file = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "CHANGELOG.md"))
    readme_file = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "README.md"))
    copying_file = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "COPYING"))
    copying_lesser_file = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "COPYING.LESSER"))
    alembic_version_files = alembic_files(python_dir)
    # Most dependencies are automatically detected but some need to be manually included.
    # NOTE: Excluding 'scipy.spatial.cKDTree' and including 'scipy.spatial.ckdtree' is a workaround
    # for a bug in cx_Freeze affecting Windows (https://github.com/anthony-tuininga/cx_Freeze/issues/233)
    build_exe_options = {
        "packages": ["packaging", "pkg_resources", "spine_engine"],
        "excludes": ["scipy.spatial.cKDTree"],
        "includes": [
            "atexit",
            "asyncio.base_futures",
            "asyncio.base_subprocess",
            "asyncio.base_tasks",
            "asyncio.compat",
            "asyncio.constants",
            "asyncio.proactor_events",
            "asyncio.selector_events",
            "asyncio.windows_utils",
            "idna.idnadata",
            "pygments.lexers.markup",
            "pygments.lexers.python",
            "pygments.lexers.shell",
            "pygments.lexers.julia",
            "pygments.styles.default",
            "qtconsole.client",
            "sqlalchemy.sql.default_comparator",
            "sqlalchemy.ext.baked",
            "numpy.core._methods",
            "matplotlib.backends.backend_tkagg",
            "scipy._distributor_init",
            "scipy.sparse.csgraph._validation",
            "scipy.spatial.ckdtree",
            "pymysql",
            "tabulator.loaders.local",
            "tabulator.parsers.csv",
        ],
        "include_files": [
            (doc_path, "docs/"),
            tcl86t_dll,
            tk86t_dll,
            changelog_file,
            readme_file,
            copying_file,
            copying_lesser_file,
        ]
        + alembic_version_files,
        "include_msvcr": True,
    }
    # Windows specific options
    if os.name == "nt":  # Windows specific options
        base = "Win32GUI"  # set this to "Win32GUI" to not show console, "Console" shows console
        # Set Windows .msi installer default install path to C:\SpineToolbox-version
        systemdrive = os.environ['SYSTEMDRIVE']
        # Hardcoded path to msvcr120.dll because include_msvcr option does not seem to do anything
        msvcr120_dll = os.path.join(systemdrive, os.path.sep, "Windows", "System32", "msvcr120.dll")
        if not os.path.isfile(msvcr120_dll):
            print("\nmsvcr120.dll not found in path:{0}".format(msvcr120_dll))
            return
        # Append msvcr120.dll for Windows 7/8 support
        build_exe_options["include_files"].append(msvcr120_dll)
    # Other platforms (TODO: needs testing)
    else:
        base = None
    executables = [Executable("spinetoolbox.py", base=base, icon="spinetoolbox/ui/resources/app.ico")]
    setup(
        name="Spine Toolbox",
        version=version["__version__"],
        description="An application to define, manage, and execute various energy system simulation models.",
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
