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
import pkgutil
from .project_item.project_item_info import ProjectItemInfo
from .project_item.project_item_factory import ProjectItemFactory
from .config import PREFERRED_SPINE_ITEMS_VERSION


def _spine_items_version_check():
    """Check if spine_items is the preferred version."""
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
    preferred_split = [int(x) for x in PREFERRED_SPINE_ITEMS_VERSION.split(".")]
    return current_split >= preferred_split


def upgrade_project_items():
    if not _spine_items_version_check():
        print(
            """
UPGRADING PROJECT ITEMS...

(Depending on your internet connection, this may take a few moments.)
            """
        )
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "git+https://github.com/Spine-project/spine-items.git@master",
                ],
                timeout=30,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as err:
            fail_color = "\033[91m"
            end_color = "\033[0m"
            print(fail_color + err.stderr.decode("utf-8") + end_color)
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
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module_material = _find_module_material(module)
            if module_material is not None:
                item_type, category, factory = module_material
                categories[item_type] = category
                factories[item_type] = factory
    return categories, factories


def _find_module_material(module):
    item_type = None
    category = None
    factory = None
    prefix = module.__name__ + "."
    for _, modname, _ in pkgutil.iter_modules(module.__path__, prefix):
        submodule = __import__(modname, fromlist="dummy")
        for name in dir(submodule):
            attr = getattr(submodule, name)
            if not isinstance(attr, type):
                continue
            if attr is not ProjectItemInfo and issubclass(attr, ProjectItemInfo):
                item_type = attr.item_type()
                category = attr.item_category()
            if attr is not ProjectItemFactory and issubclass(attr, ProjectItemFactory):
                factory = attr
            if item_type is not None and factory is not None:
                return item_type, category, factory
    return None


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
