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
    def icon():
        return ":/icons/project_item_icons/binoculars.svg"

    @property
    def item_maker(self):
        return View

    @property
    def icon_maker(self):
        return ViewIcon

    @property
    def add_form_maker(self):
        return AddViewWidget

    @property
    def specification_form_maker(self):
        raise NotImplementedError()

    @property
    def specification_menu_maker(self):
        raise NotImplementedError()

    @staticmethod
    def _make_properties_widget(toolbox):
        return ViewPropertiesWidget(toolbox)
