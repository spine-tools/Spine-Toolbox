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
Classes for custom context menus and pop-up menus.

:author: P. Savolainen (VTT)
:date:   9.1.2018
"""

from PySide2.QtCore import QTimeLine
from spinetoolbox.widgets.custom_menus import CustomContextMenu, ProjectItemContextMenu


class ToolPropertiesContextMenu(CustomContextMenu):
    """Common context menu class for all Tool QTreeViews in Tool properties.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        self.add_action("Edit Tool specification")
        self.add_action("Edit main program file...")
        self.add_action("Open main program directory...")
        self.add_action("Open Tool specification file...")
        self.addSeparator()
        self.add_action("Open directory...")


class ToolContextMenu(ProjectItemContextMenu):
    """Context menu for Tools in the QTreeView and in the QGraphicsView.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
    """

    def __init__(self, parent, tool, position):
        """Class constructor."""
        super().__init__(parent, position)
        self.addSeparator()
        self.add_action("Results...")
        # TODO: Do we still want to have the stop action here???
        enabled = tool.get_icon().timer.state() == QTimeLine.Running
        self.add_action("Stop", enabled=False)
        self.addSeparator()
        enabled = bool(tool.tool_specification())
        self.add_action("Edit Tool specification", enabled=enabled)
        self.add_action("Edit main program file...", enabled=enabled)
