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

from spinetoolbox.widgets.custom_menus import CustomContextMenu


class DcRefContextMenu(CustomContextMenu):
    """Context menu class for references view in Data Connection properties.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        if not index.isValid():
            # If no item at index
            self.add_action("Add reference(s)")
            self.add_action("Remove reference(s)")
            self.add_action("Copy reference(s) to project")
        else:
            self.add_action("Edit...")
            self.add_action("Open containing directory...")
            self.addSeparator()
            self.add_action("Add reference(s)")
            self.add_action("Remove reference(s)")
            self.add_action("Copy reference(s) to project")


class DcDataContextMenu(CustomContextMenu):
    """Context menu class for data view in Data Connection properties.

    Attributes:
        parent (QWidget): Parent for menu widget (ToolboxUI)
        position (QPoint): Position on screen
        index (QModelIndex): Index of item that requested the context-menu
    """

    def __init__(self, parent, position, index):
        """Class constructor."""
        super().__init__(parent, position)
        if not index.isValid():
            # If no item at index
            self.add_action("New file...")
            self.addSeparator()
            self.add_action("Open Spine Datapackage Editor")
            self.add_action("Open directory...")
        else:
            self.add_action("Edit...")
            self.add_action("New file...")
            self.add_action("Remove file(s)")
            self.addSeparator()
            self.add_action("Open Spine Datapackage Editor")
            self.add_action("Open directory...")
