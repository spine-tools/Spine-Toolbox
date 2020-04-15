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
The DataConnectionCategory class.

:author: M. Marin (KTH)
:date:   15.4.2020
"""

from spinetoolbox.project_tree_item import CategoryProjectTreeItem
from .data_connection_icon import DataConnectionIcon
from .data_connection import DataConnection
from .widgets.data_connection_properties_widget import DataConnectionPropertiesWidget
from .widgets.add_data_connection_widget import AddDataConnectionWidget


class DataConnectionCategory(CategoryProjectTreeItem):
    def __init__(self, toolbox):
        super().__init__(toolbox, "Data Connections", "Generic data source.")

    @staticmethod
    def rank():
        return 1

    @staticmethod
    def icon():
        return ":/icons/project_item_icons/file-alt.svg"

    @staticmethod
    def item_type():
        return "Data Connection"

    @property
    def properties_widget_maker(self):
        return DataConnectionPropertiesWidget

    @property
    def item_maker(self):
        return DataConnection

    @property
    def icon_maker(self):
        return DataConnectionIcon

    @property
    def add_form_maker(self):
        return AddDataConnectionWidget
