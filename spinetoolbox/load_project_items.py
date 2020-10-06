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
Functions to load project item modules.

:author: A. Soininen (VTT)
:date:   29.4.2020
"""
import pathlib
import importlib
import importlib.util
import subprocess
import sys
from .config import REQUIRED_SPINE_ITEMS_VERSION


def _spine_items_version_check():
    """Check if spine_items is the correct version."""
    try:
        import spine_items
    except ModuleNotFoundError:
        # Module not installed yet
        return False
    try:
        current_version = spine_items.__version__
    except AttributeError:
        # Version not reported (should never happen as spine_items has always reported its version)
        return False
    current_split = [int(x) for x in current_version.split(".")]
    required_split = [int(x) for x in REQUIRED_SPINE_ITEMS_VERSION.split(".")]
    return current_split >= required_split


def upgrade_project_items():
    if not _spine_items_version_check():
        print(
            """
UPGRADING PROJECT ITEMS...

(Depending on your internet connection, this may take a few moments.)
            """
        )
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "git+https://github.com/Spine-project/spine-items.git@master",
            ],
            timeout=30,
        )
    try:
        import spine_items
    except ModuleNotFoundError:
        # Failed to install module
        return False
    return True


def load_project_items(toolbox):
    """
    Loads the standard project item modules included in the Toolbox package.

    Args:
        toolbox (ToolboxUI): Toolbox main widget

    Returns:
        tuple of dict: two dictionaries; first maps item type to its category
            while second maps item type to item factory
    """
    import spine_items

    items_root = pathlib.Path(spine_items.__file__).parent
    categories = dict()
    factories = dict()
    for child in items_root.iterdir():
        if child.is_dir() and child.joinpath("__init__.py").exists():
            spec = importlib.util.find_spec(f"spine_items.{child.stem}")
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            if hasattr(m, "ItemInfo") and hasattr(m, "ItemFactory"):
                info = m.ItemInfo
                category = info.item_category()
                item_type = info.item_type()
                categories[item_type] = category
                factories[item_type] = m.ItemFactory
    return categories, factories


def load_item_specification_factories():
    """
    Loads the project item specification factories in the standard Toolbox package.

    Returns:
        dict: a map from item type to specification factory
    """
    import spine_items

    items_root = pathlib.Path(spine_items.__file__).parent
    factories = dict()
    for child in items_root.iterdir():
        if child.is_dir() and child.joinpath("specification_factory.py").exists():
            spec = importlib.util.find_spec(f"spine_items.{child.stem}.specification_factory")
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            if hasattr(m, "SpecificationFactory"):
                item_type = m.SpecificationFactory.item_type()
                factories[item_type] = m.SpecificationFactory
    return factories


def load_executable_items():
    """
    Loads the project item executable classes included in the standard Toolbox package.

    Returns:
        dict: a map from item type to the executable item class
    """
    import spine_items

    items_root = pathlib.Path(spine_items.__file__).parent
    classes = dict()
    for child in items_root.iterdir():
        if child.is_dir() and child.joinpath("executable_item.py").exists():
            spec = importlib.util.find_spec(f"spine_items.{child.stem}.executable_item")
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            if hasattr(m, "ExecutableItem"):
                item_class = m.ExecutableItem
                item_type = item_class.item_type()
                classes[item_type] = item_class
    return classes
