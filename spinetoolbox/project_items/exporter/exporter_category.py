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
Exporter project item plugin.

:author: A. Soininen (VTT)
:date:   25.9.2019
"""

from spinetoolbox.project_tree_item import CategoryProjectTreeItem
from .exporter import Exporter
from .exporter_icon import ExporterIcon
from .widgets.add_exporter_widget import AddExporterWidget
from .widgets.exporter_properties import ExporterProperties


class ExporterCategory(CategoryProjectTreeItem):
    def __init__(self, toolbox):
        super().__init__(toolbox, "Exporters", "Some meaningful description.")

    @staticmethod
    def rank():
        return 5

    @staticmethod
    def icon():
        return ":/icons/project_item_icons/database-export.svg"

    @staticmethod
    def item_type():
        return "Exporter"

    @property
    def properties_widget_maker(self):
        return ExporterProperties

    @property
    def item_maker(self):
        return Exporter

    @property
    def icon_maker(self):
        return ExporterIcon

    @property
    def add_form_maker(self):
        return AddExporterWidget
