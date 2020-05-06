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
The DataStoreFactory class.

:author: M. Marin (KTH)
:date:   15.4.2020
"""

from spinetoolbox.project_item import ProjectItemFactory
from .data_store import DataStore
from .data_store_icon import DataStoreIcon
from .widgets.data_store_properties_widget import DataStorePropertiesWidget
from .widgets.add_data_store_widget import AddDataStoreWidget


class DataStoreFactory(ProjectItemFactory):
    @staticmethod
    def icon():
        return ":/icons/project_item_icons/database.svg"

    @property
    def item_maker(self):
        return DataStore

    @property
    def icon_maker(self):
        return DataStoreIcon

    @property
    def add_form_maker(self):
        return AddDataStoreWidget

    @property
    def specification_form_maker(self):
        raise NotImplementedError()

    @property
    def specification_menu_maker(self):
        raise NotImplementedError()

    @staticmethod
    def _make_properties_widget(toolbox):
        """See base class"""
        return DataStorePropertiesWidget(toolbox)
