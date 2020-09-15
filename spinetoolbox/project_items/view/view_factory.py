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
The ViewFactory class.

:author: M. Marin (KTH)
:date:   15.4.2020
"""

from spinetoolbox.project_item import ProjectItemFactory
from .view import View
from .view_icon import ViewIcon
from .widgets.view_properties_widget import ViewPropertiesWidget
from .widgets.add_view_widget import AddViewWidget


class ViewFactory(ProjectItemFactory):
    @staticmethod
    def item_class():
        return View

    @staticmethod
    def icon():
        return ":/icons/project_item_icons/binoculars.svg"

    @staticmethod
    def make_add_item_widget(toolbox, x, y, specification):
        return AddViewWidget(toolbox, x, y, specification)

    @staticmethod
    def make_icon(toolbox, x, y, project_item):
        return ViewIcon(toolbox, x, y, project_item, ViewFactory.icon())

    @staticmethod
    def make_item(name, item_dict, toolbox, project, logger):
        return View.from_dict(name, item_dict, toolbox, project, logger)

    @staticmethod
    def make_properties_widget(toolbox):
        return ViewPropertiesWidget(toolbox)

    @staticmethod
    def make_specification_menu(parent, index):
        raise NotImplementedError()

    @staticmethod
    def make_specification_widget(toolbox):
        raise NotImplementedError()
