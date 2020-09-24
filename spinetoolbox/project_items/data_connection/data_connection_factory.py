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
The DataConnectionFactory class.

:author: M. Marin (KTH)
:date:   15.4.2020
"""

from spinetoolbox.project_item import ProjectItemFactory
from .data_connection_icon import DataConnectionIcon
from .data_connection import DataConnection
from .widgets.data_connection_properties_widget import DataConnectionPropertiesWidget
from .widgets.add_data_connection_widget import AddDataConnectionWidget


class DataConnectionFactory(ProjectItemFactory):
    @staticmethod
    def item_class():
        return DataConnection

    @staticmethod
    def icon():
        return ":/icons/project_item_icons/file-alt.svg"

    @staticmethod
    def make_add_item_widget(toolbox, x, y, specification):
        return AddDataConnectionWidget(toolbox, x, y, specification)

    @staticmethod
    def make_icon(toolbox, x, y, project_item):
        return DataConnectionIcon(toolbox, x, y, project_item, DataConnectionFactory.icon())

    @staticmethod
    def make_item(name, item_dict, toolbox, project, logger):
        return DataConnection.from_dict(name, item_dict, toolbox, project, logger)

    @staticmethod
    def make_properties_widget(toolbox):
        """See base class."""
        return DataConnectionPropertiesWidget(toolbox)

    @staticmethod
    def make_specification_menu(parent, index):
        raise NotImplementedError()

    @staticmethod
    def make_specification_widget(toolbox, specification=None):
        """See base class."""
        raise NotImplementedError()
