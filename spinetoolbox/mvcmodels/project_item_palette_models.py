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

from PySide2.QtCore import Qt, QModelIndex, QAbstractListModel, QSortFilterProxyModel
from PySide2.QtGui import QStandardItem, QStandardItemModel


class ProjectItemPaletteModel(QStandardItemModel):
    """A model for listing project items in the Item Palette view."""

    def add_item(self, item_type, category, icon):
        """Add item to model."""
        new_item = QStandardItem("")
        new_item.setData(icon, Qt.DecorationRole)
        new_item.setData(category, Qt.UserRole + 1)
        new_item.setToolTip(
            f"<p>Drag-and-drop this icon into the Design View to create a new <b>{item_type}</b> item.</p>"
        )
        self.appendRow(new_item)

    def flags(self, index):
        return super().flags(index) & ~Qt.ItemIsSelectable

    @staticmethod
    def is_index_draggable(index):
        return True

    def get_mime_data_text(self, index):
        return ",".join([self.data(index, Qt.UserRole + 1), ""])


class ProjectItemSpecPaletteModel(QAbstractListModel):
    """Class to store specs that are available in a project e.g. GAMS or Julia models."""

    def __init__(self, icons):
        super().__init__()
        self._specs = list()
        self._icons = icons

    def rowCount(self, parent=None):
        """Must be reimplemented when subclassing. Returns
        the number of specs in the model.

        Args:
            parent (QModelIndex): Not used (because this is a list)

        Returns:
            Number of rows (available specs) in the model
        """
        return len(self._specs)

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
            specname = self._specs[row].name
            return specname
        if role == Qt.ToolTipRole:
            if row >= self.rowCount():
                return ""
            return self._specs[row].def_file_path
        if role == Qt.DecorationRole:
            return self._icons[self._specs[row].category]

    def flags(self, index):
        """Returns enabled flags for the given index.

        Args:
            index (QModelIndex): Index of spec
        """
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def insertRow(self, spec, row=None, parent=QModelIndex()):
        """Insert row (specification) into model.

        Args:
            spec (ProjectItemSpecification): spec added to the model
            row (str): Row to insert spec to
            parent (QModelIndex): Parent of child (not used)

        Returns:
            Void
        """
        if row is None:
            row = self.rowCount()
        self.beginInsertRows(parent, row, row)
        self._specs.insert(row, spec)
        self.endInsertRows()

    def removeRow(self, row, parent=QModelIndex()):
        """Remove row (spec) from model.

        Args:
            row (int): Row to remove the spec from
            parent (QModelIndex): Parent of spec on row (not used)

        Returns:
            Boolean variable
        """
        if row < 0 or row > self.rowCount():
            # logging.error("Invalid row number")
            return False
        self.beginRemoveRows(parent, row, row)
        self._specs.pop(row)
        self.endRemoveRows()
        return True

    def update_specification(self, row, spec):
        """Update specification.

        Args:
            row (int): Position of the spec to be updated
            spec (ProjectItemSpecification): new spec, to replace the old one

        Returns:
            Boolean value depending on the result of the operation
        """
        try:
            self._specs[row] = spec
            return True
        except IndexError:
            return False

    def specification(self, row):
        """Returns spec specification on given row.

        Args:
            row (int): Row of spec specification

        Returns:
            ProjectItemSpecification from specification list or None if given row is zero
        """
        return self._specs[row]

    def find_specification(self, name):
        """Returns specification with the given name.

        Args:
            name (str): Name of specification to find
        """
        for specification in self._specs:
            if name.lower() == specification.name.lower():
                return specification
        return None

    def specification_row(self, name):
        """Returns the row on which the given specification is located or -1 if it is not found."""
        for i in range(len(self._specs)):
            if name == self._specs[i].name:
                return i
        return -1

    def specification_index(self, name):
        """Returns the QModelIndex on which a specification with
        the given name is located or invalid index if it is not found."""
        row = self.specification_row(name)
        if row == -1:
            return QModelIndex()
        return self.createIndex(row, 0)

    @staticmethod
    def is_index_draggable(index):
        return True

    def get_mime_data_text(self, index):
        i = index.row()
        return ",".join([self._specs[i].category, self._specs[i].name])


class CategoryFilteredSpecPaletteModel(QSortFilterProxyModel):
    def __init__(self, category):
        super().__init__()
        self._category = category

    def filterAcceptsRow(self, source_row, source_parent):
        spec = self.sourceModel().specification(source_row)
        return spec.category == self._category
