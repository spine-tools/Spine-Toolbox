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

from PySide2.QtCore import QTimeLine, QUrl
from spinetoolbox.widgets.custom_menus import (
    CustomContextMenu,
    CustomPopupMenu,
    ProjectItemContextMenu,
    ItemSpecificationContextMenu,
)
from ..tool_specifications import open_main_program_file


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


class ToolSpecificationOptionsPopupmenu(CustomPopupMenu):
    """Popup menu class for tool specification options button in Tool item."""

    def __init__(self, parent, tool):
        """
        Args:
            parent (QWidget): Parent widget of this menu (ToolboxUI)
            tool (Tool): Tool item that is associated with the pressed button
        """
        super().__init__(parent)
        enabled = bool(tool.specification())
        self.add_action("Edit Tool specification", tool.edit_specification, enabled=enabled)
        self.add_action("Edit main program file...", tool.open_main_program_file, enabled=enabled)
        self.add_action("Open main program directory...", tool.open_main_directory, enabled=enabled)
        self.add_action("Open definition file", tool.open_specification_file, enabled=enabled)
        self.addSeparator()
        # self.add_action("New Tool specification", self._parent.show_tool_specification_form)
        # self.add_action("Add Tool specification...", self._parent.open_tool_specification)


class ToolSpecificationContextMenu(ItemSpecificationContextMenu):
    """Context menu class for Tool specifications."""

    def __init__(self, parent, position, index):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            position (QPoint): Position on screen
            index (QModelIndex): the index
        """
        super().__init__(parent, position, index)
        self.addSeparator()
        self.add_action("Edit main program file...")
        self.add_action("Open main program directory...")

    def apply_action(self, option):
        if super().apply_action(option):
            return True
        if option == "Edit main program file...":
            spec = self.parent().specification_model.specification(self.index.row())
            open_main_program_file(spec, self.parent())
        elif option == "Open main program directory...":
            tool_specification_path = self.parent().specification_model.specification(self.index.row()).path
            path_url = "file:///" + tool_specification_path
            self.parent().open_anchor(QUrl(path_url, QUrl.TolerantMode))
        return True


class AddIncludesPopupMenu(CustomPopupMenu):
    """Popup menu class for add includes button in Tool specification editor widget."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget (ToolSpecificationWidget)
        """
        super().__init__(parent)
        self._parent = parent
        # Open a tool specification file
        self.add_action("New file", self._parent.new_source_file)
        self.addSeparator()
        self.add_action("Open files...", self._parent.show_add_source_files_dialog)


class CreateMainProgramPopupMenu(CustomPopupMenu):
    """Popup menu class for add main program QToolButton in Tool specification editor widget."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent widget (ToolSpecificationWidget)
        """
        super().__init__(parent)
        self._parent = parent
        # Open a tool specification file
        self.add_action("Make new main program", self._parent.new_main_program_file)
        self.add_action("Select existing main program", self._parent.browse_main_program)
