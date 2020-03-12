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
Contains a class for storing Tool specifications.

:authors: P. Savolainen (VTT)
:date:   23.1.2018
"""

from PySide2.QtCore import Qt, QModelIndex, QAbstractListModel


class ToolSpecificationModel(QAbstractListModel):
    """Class to store tools that are available in a project e.g. GAMS or Julia models."""

    def __init__(self):
        super().__init__()
        self._tools = list()

    def rowCount(self, parent=None):
        """Must be reimplemented when subclassing. Returns
        the number of Tools in the model.

        Args:
            parent (QModelIndex): Not used (because this is a list)

        Returns:
            Number of rows (available tools) in the model
        """
        return len(self._tools)

    def data(self, index, role=None):
        """Must be reimplemented when subclassing.

        Args:
            index (QModelIndex): Requested index
            role (int): Data role

        Returns:
            Data according to requested role
        """
        if not index.isValid() or self.rowCount() == 0:
            return None
        row = index.row()
        if role == Qt.DisplayRole:
            toolname = self._tools[row].name
            return toolname
        if role == Qt.ToolTipRole:
            if row >= self.rowCount():
                return ""
            return self._tools[row].def_file_path

    def flags(self, index):
        """Returns enabled flags for the given index.

        Args:
            index (QModelIndex): Index of Tool
        """
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def insertRow(self, tool, row=None, parent=QModelIndex()):
        """Insert row (tool specification) into model.

        Args:
            tool (Tool): Tool added to the model
            row (str): Row to insert tool to
            parent (QModelIndex): Parent of child (not used)

        Returns:
            Void
        """
        if row is None:
            row = self.rowCount()
        self.beginInsertRows(parent, row, row)
        self._tools.insert(row, tool)
        self.endInsertRows()

    def removeRow(self, row, parent=QModelIndex()):
        """Remove row (tool specification) from model.

        Args:
            row (int): Row to remove the tool from
            parent (QModelIndex): Parent of tool on row (not used)

        Returns:
            Boolean variable
        """
        if row < 0 or row > self.rowCount():
            # logging.error("Invalid row number")
            return False
        self.beginRemoveRows(parent, row, row)
        self._tools.pop(row)
        self.endRemoveRows()
        return True

    def update_tool_specification(self, row, tool):
        """Update tool specification.

        Args:
            row (int): Position of the tool to be updated
            tool (ToolSpecification): new tool, to replace the old one

        Returns:
            Boolean value depending on the result of the operation
        """
        try:
            self._tools[row] = tool
            return True
        except IndexError:
            return False

    def tool_specification(self, row):
        """Returns tool specification on given row.

        Args:
            row (int): Row of tool specification

        Returns:
            ToolSpecification from tool specification list or None if given row is zero
        """
        return self._tools[row]

    def find_tool_specification(self, name):
        """Returns tool specification with the given name.

        Args:
            name (str): Name of tool specification to find
        """
        for specification in self._tools:
            if name.lower() == specification.name.lower():
                return specification
        return None

    def tool_specification_row(self, name):
        """Returns the row on which the given specification is located or -1 if it is not found."""
        for i in range(len(self._tools)):
            if name == self._tools[i].name:
                return i
        return -1

    def tool_specification_index(self, name):
        """Returns the QModelIndex on which a tool specification with
        the given name is located or invalid index if it is not found."""
        row = self.tool_specification_row(name)
        if row == -1:
            return QModelIndex()
        return self.createIndex(row, 0)
