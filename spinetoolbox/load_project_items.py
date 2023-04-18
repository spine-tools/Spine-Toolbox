######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""
import pathlib
import importlib
import importlib.util
import pkgutil
from spine_engine.project_item.project_item_info import ProjectItemInfo
from spine_engine import __version__ as curr_engine_version
from spinedb_api import __version__ as curr_db_api_version
from .version import __version__ as curr_toolbox_version
from .project_item.project_item_factory import ProjectItemFactory


def load_project_items(items_package_name):
    """
    Loads project item modules.

    Args:
        items_package_name (str): name of the package that contains the project items

    Returns:
        tuple of dict: two dictionaries; first maps item type to its category
            while second maps item type to item factory
    """
    items = importlib.import_module(items_package_name)
    items_root = pathlib.Path(items.__file__).parent
    categories = dict()
    factories = dict()
    for child in items_root.iterdir():
        if child.is_dir() and (child.joinpath("__init__.py").exists() or child.joinpath("__init__.pyc").exists()):
            spec = importlib.util.find_spec(f"{items_package_name}.{child.stem}")
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
