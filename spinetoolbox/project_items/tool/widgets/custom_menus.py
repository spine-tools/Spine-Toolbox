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

from PySide2.QtCore import QTimeLine, QUrl, Slot
from spinetoolbox.widgets.custom_menus import (
    CustomContextMenu,
    ProjectItemContextMenu,
    ItemSpecificationMenu,
    CustomPopupMenu,
)


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


class ToolSpecificationMenu(ItemSpecificationMenu):
    """Context menu class for Tool specifications."""

    def __init__(self, parent, index):
        """
        Args:
            parent (QWidget): Parent for menu widget (ToolboxUI)
            index (QModelIndex): the index from specification model
        """
        super().__init__(parent, index)
        self.add_action("Edit main program file...", self.open_main_program_file)
        self.add_action("Open main program directory...", self.open_main_program_dir)

    @Slot()
    def open_main_program_file(self):
        spec = self.parent().specification_model.specification(self.index.row())
        spec.open_main_program_file()

    @Slot()
    def open_main_program_dir(self):
        tool_specification_path = self.parent().specification_model.specification(self.index.row()).path
        path_url = "file:///" + tool_specification_path
        self.parent().open_anchor(QUrl(path_url, QUrl.TolerantMode))


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
