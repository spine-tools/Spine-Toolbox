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
"""
This is the PyInstaller spec file for Spine Toolbox.

We bundle an embeddable Python interpreter with Toolbox
so all basic functionality should be available without the need to install Python.

Steps to bundle Spine Toolbox:

1. Activate Toolbox Python environment.
2. Install PyInstaller using Pip.
3. Download one of the 64-bit *embeddable* Python packages from https://www.python.org/downloads/windows/
4. Unzip the downloaded package somewhere, e.g. <path-to-embeddable-python>
5. cd to <path-to-embeddable-python> and open file pythonXX._pth, where XX is the version, e.g. 312
6. Add two lines to the end of the file, save & close
    Lib
    Lib/site-packages
7. Run
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
8. Run
    python get-pip.py
9. cd to <path-to-embeddable-python>/Scripts and run 'pip --version' to make sure you are running
    the pip installed for the embeddable python
10. Run
    pip install ipykernel
11. Run
    pip install jill
12. cd to the directory where this file is
13. Finally, run
    python -m PyInstaller spinetoolbox.spec -- --embedded-python=<path-to-embeddable-python>
"""

import argparse
from pathlib import Path
import spinedb_api
import spine_engine
from spine_engine.config import BUNDLE_DIR
import spine_items

parser = argparse.ArgumentParser()
parser.add_argument("--embedded-python", help="path to embedded Python interpreter", required=True)
options = parser.parse_args()
embedded_python_path = Path(options.embedded_python)
spinedb_api_path = Path(spinedb_api.__file__).parent.parent
spine_engine_path = Path(spine_engine.__file__).parent.parent
spine_items_path = Path(spine_items.__file__).parent.parent
data_file_target = Path()
data_files = ("CHANGELOG.md", "README.md", "COPYING", "COPYING.LESSER")
embed_python_files = [(str(path), BUNDLE_DIR) for path in embedded_python_path.iterdir() if path.is_file()]
embed_python_dirs = [(str(path), os.path.join(BUNDLE_DIR, path.name)) for path in embedded_python_path.iterdir() if path.is_dir()]
a = Analysis(
    ['spinetoolbox.py'],
    pathex=list(set(map(str, (spinedb_api_path, spine_engine_path, spine_items_path)))),
    binaries=[],
    datas=[(data_file, str(Path())) for data_file in data_files] + embed_python_files + embed_python_dirs,
    hiddenimports=["scipy._cyutility"],
    hookspath=["PyInstaller hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='spinetoolbox',
    icon=Path("spinetoolbox", "ui", "resources", "app.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Spine Toolbox',
)
