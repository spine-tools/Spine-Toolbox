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
cx-Freeze setup file for Spine Toolbox.

On Windows:

1. Download *embeddable* Python packages from https://www.python.org/downloads/windows/
2. Unzip the downloaded package somewhere.
3. Build application with command 'python cx_Freeze_setup.py build --embedded-python=<path to unzipped Python package>'
4. Check version numbers and CHANGELOG

"""
import argparse
from pathlib import Path
import sys
from cx_Freeze import setup, Executable
from cx_Freeze.cli import prepare_parser
import ijson
import spinedb_api
import spine_engine
from spine_engine.config import BUNDLE_DIR
import spine_items


def main():
    """Main of cx_Freeze_setup.py."""
    parser = argparse.ArgumentParser(parents=[prepare_parser()], add_help=False)
    parser.add_argument("--embedded-python", help="path to embedded Python interpreter", required=True)
    options = parser.parse_args()
    sys.argv = [arg for arg in sys.argv if not arg.startswith("--embedded-python")]
    spinedb_api_package = Path(spinedb_api.__file__).parent
    spinedb_api_root = spinedb_api_package.parent
    spine_engine_root = Path(spine_engine.__file__).parent.parent
    spine_items_root = Path(spine_items.__file__).parent.parent
    root = Path(__file__).parent
    changelog_file = root / "CHANGELOG.md"
    readme_file = root / "README.md"
    copying_file = root / "COPYING"
    copying_lesser_file = root / "COPYING.LESSER"
    # Most dependencies are automatically detected but some need to be manually included.
    build_exe_options = {
        "path": list(set(map(str, (spinedb_api_root, spine_engine_root, spine_items_root)))) + sys.path,
        "packages": ["ijson.compat", "pendulum.locales", "sqlalchemy.sql.default_comparator", "tabulator.loaders", "tabulator.parsers"],
        "excludes": [],
        "includes": [],
        "include_files": [
            changelog_file,
            readme_file,
            copying_file,
            copying_lesser_file,
        ]
        + alembic_files(spinedb_api_package)
        + spine_repl_files()
        + ijson_backends()
        + embedded_python(options),
    }
    # Windows specific options
    if sys.platform == "win32":  # Windows specific options
        base = "Win32GUI"  # set this to "Win32GUI" to not show console, "Console" shows console
    else:  # Other platforms
        base = None
    executables = [Executable("spinetoolbox.py", base=base, icon="spinetoolbox/ui/resources/app.ico")]
    setup(
        options={"build_exe": build_exe_options},
        executables=executables,
    )
    return 0


def embedded_python(options):
    embedded_python_path = Path(options.embedded_python)
    return [(str(path), str(Path(BUNDLE_DIR, path.name))) for path in embedded_python_path.iterdir()]


def alembic_files(spinedb_api_path):
    """Returns a list of tuples of files in python/Lib/site-packages/spinedb_api/alembic/versions.
    First item in tuple is the source file. Second item is the relative destination path to the install directory.
    We are including these .py files into 'include_files' list because adding them to the 'includes' list
    would require us to give the whole explicit file name.
    """
    source_dir = spinedb_api_path / "alembic" / "versions"
    destination_dir = Path("lib", "spinedb_api", "alembic", "versions")
    return [(str(file), str(destination_dir / file.name)) for file in source_dir.iterdir() if file.suffix == ".py"]


def ijson_backends():
    source_dir = Path(ijson.__file__).parent / "backends"
    destination_dir = Path("lib", "ijson", "backends")
    return [(str(file), str(destination_dir / file.name)) for file in source_dir.iterdir() if file.suffix == ".py"]


def spine_repl_files():
    # spine_repl.jl gets copied to the bundle automatically
    py_repl = Path("execution_managers", "spine_repl.py")
    source_file = Path(spine_engine.__file__).parent / py_repl
    destination_file = Path("lib", spine_engine.__name__) / py_repl
    return [(str(source_file), str(destination_file))]


if __name__ == '__main__':
    sys.exit(main())
