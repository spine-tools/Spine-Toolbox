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
4. Unzip the downloaded package somewhere.
5. Run

python -m PyInstaller spinetoolbox.spec -- --embedded-python=<path to unzipped Python package>
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
embedded_python_datas = [(str(path), BUNDLE_DIR) for path in embedded_python_path.iterdir()]
a = Analysis(
    ['spinetoolbox.py'],
    pathex=list(set(map(str, (spinedb_api_path, spine_engine_path, spine_items_path)))),
    binaries=[],
    datas=[(data_file, str(Path())) for data_file in data_files] + embedded_python_datas,
    hiddenimports=[],
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
