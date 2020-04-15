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
Data store plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

from spinetoolbox.project_tree_item import CategoryProjectTreeItem
from .data_store import DataStore
from .data_store_icon import DataStoreIcon
from .widgets.data_store_properties_widget import DataStorePropertiesWidget
from .widgets.add_data_store_widget import AddDataStoreWidget


class DataStoreCategory(CategoryProjectTreeItem):
    def __init__(self, toolbox):
        super().__init__(toolbox, "Data Stores", "Some meaningful description.")

    @staticmethod
    def rank():
        return 0

    @staticmethod
    def icon():
        return ":/icons/project_item_icons/database.svg"

    @staticmethod
    def item_type():
        return "Data Store"

    @property
    def properties_widget_maker(self):
        return DataStorePropertiesWidget

    @property
    def item_maker(self):
        return DataStore

    @property
    def icon_maker(self):
        return DataStoreIcon

    @property
    def add_form_maker(self):
        return AddDataStoreWidget
