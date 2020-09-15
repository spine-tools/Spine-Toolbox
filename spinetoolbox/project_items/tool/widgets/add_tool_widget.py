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
Widget shown to user when a new Tool is created.

:author: P. Savolainen (VTT)
:date:   19.1.2017
"""

from spinetoolbox.widgets.add_project_item_widget import AddProjectItemWidget
from ..item_info import ItemInfo
from ..tool import Tool


class AddToolWidget(AddProjectItemWidget):
    """A widget that queries user's preferences for a new item.

    Attributes:
        toolbox (ToolboxUI): Parent widget
        x (int): X coordinate of new item
        y (int): Y coordinate of new item
        spec (str): Tool specification
    """

    def __init__(self, toolbox, x, y, spec=""):
        """Initialize class."""
        super().__init__(toolbox, x, y, Tool, spec=spec)

    def call_add_item(self):
        """Creates new Item according to user's selections."""
        spec = self.ui.comboBox_specification.currentText()
        item = {
            self.name: {
                "type": ItemInfo.item_type(),
                "description": self.description,
                "x": self._x,
                "y": self._y,
                "specification": spec,
                "execute_in_work": True,
            }
        }
        self._project.add_project_items(item, set_selected=True)
