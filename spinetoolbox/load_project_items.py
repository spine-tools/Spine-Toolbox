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

:author: A.Soininen (VTT)
:date:   29.4.2020
"""
import importlib
import importlib.util
import pathlib


def load_project_items(toolbox):
    """
    Loads the project item modules included in the standard Toolbox package.

    Args:
        toolbox (ToolboxUI): Toolbox main widget

    Returns:
        tuple of dict: two dictionaries; first maps item type to its category
            while second maps item type to item factory
    """
    categories = dict()
    factories = dict()
    item_root = pathlib.Path(__file__).parent / "project_items"
    for child in item_root.iterdir():
        if child.is_dir() and child.joinpath("__init__.py").exists():
            spec = importlib.util.find_spec(f"project_items.{child.stem}")
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            if hasattr(m, "ItemInfo") and hasattr(m, "ItemFactory"):
                info = m.ItemInfo()
                category = info.item_category()
                item_type = info.item_type()
                categories[item_type] = category
                factories[item_type] = m.ItemFactory(toolbox)
    return categories, factories
