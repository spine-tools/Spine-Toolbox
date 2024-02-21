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

""" Functions to load project item modules. """
import importlib


def load_project_items(items_package_name):
    """Loads project item modules.

    Args:
        items_package_name (str): name of the package that contains the project items

    Returns:
        tuple of dict: two dictionaries; first maps item type to its category
            while second maps item type to item factory
    """
    items = importlib.import_module(items_package_name)
    return items.item_factories()
