#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
CX-FREEZE setup file for Spine Toolbox.

    - Build the application into /build directory with the following command:
        python setup.py build
    - Create a Windows Installer distribution package (.msi) with the following command:
        python setup.py bdist_msi

:author: P. Savolainen (VTT)
:date:   29.5.2018
"""

import os
import sys
from cx_Freeze import setup, Executable
from config import SPINE_TOOLBOX_VERSION, APPLICATION_PATH


def main(argv):
    """Main of cx_Freeze setup.py."""
    python_dir = os.path.dirname(sys.executable)
    os.environ['TCL_LIBRARY'] = os.path.join(python_dir, "tcl", "tcl8.6")
    os.environ['TK_LIBRARY'] = os.path.join(python_dir, "tcl", "tk8.6")
    # tcl86t.dll and tk86t.dll are required by tkinter, which in turn is required by matplotlib
    tcl86t_dll = os.path.join(python_dir, "DLLs", "tcl86t.dll")
    tk86t_dll = os.path.join(python_dir, "DLLs", "tk86t.dll")
    # Path to built documentation (No need for sources)
    doc_path = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "docs", "build"))
    # Change log
    changelog_file = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "CHANGELOG.md"))
    # Readme
    readme_file = os.path.abspath(os.path.join(APPLICATION_PATH, os.path.pardir, "README.md"))
    # Set Windows .msi installer default install path to C:\SpineToolbox-version
    systemdrive = os.environ['SYSTEMDRIVE']
    default_install_dir = os.path.join(systemdrive, os.path.sep, "SpineToolbox-" + SPINE_TOOLBOX_VERSION)
    # Hardcoded path to msvcr120.dll because include_msvcr option does not seem to do anything
    msvcr120_dll = os.path.join(systemdrive, os.path.sep, "Windows", "System32", "msvcr120.dll")
    if not os.path.isfile(msvcr120_dll):
        print("\nmsvcr120.dll not found in path:{0}".format(msvcr120_dll))
        return
    # Most dependencies are automatically detected but some need to be manually included.
    # NOTE: Excluding 'scipy.spatial.cKDTree' and including 'scipy.spatial.ckdtree' is a workaround
    # for a bug in cx_Freeze affecting Windows (https://github.com/anthony-tuininga/cx_Freeze/issues/233)
    build_exe_options = {"packages": [],
                             "excludes": ["scipy.spatial.cKDTree"],
                             "includes": ["atexit", "idna.idnadata", "pygments.lexers.python",
                                          "pygments.lexers.shell", "pygments.lexers.julia",
                                          "qtconsole.client", "sqlalchemy.sql.default_comparator",
                                          "sqlalchemy.ext.baked", "numpy.core._methods",
                                          "matplotlib.backends.backend_tkagg", "scipy.sparse.csgraph._validation",
                                          "scipy.spatial.ckdtree"],
                             "include_files": [(doc_path, "docs/"), msvcr120_dll, tcl86t_dll, tk86t_dll,
                                               changelog_file, readme_file],
                             "include_msvcr": True}
    bdist_msi_options = {"initial_target_dir": default_install_dir}
    # This does not show logging messages
    # base = "Win32GUI" if sys.platform == "win32" else None
    # This opens a console that shows also logging messages
    base = "Console" if sys.platform == "win32" else None
    executables = [Executable("spinetoolbox.py", base=base)]
    setup(name="Spine Toolbox",
          version=SPINE_TOOLBOX_VERSION,
          description="An application to define, manage, and execute various energy system simulation models.",
          author="Spine project",
          options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
          executables=executables)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
