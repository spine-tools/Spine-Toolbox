######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains a class for storing Tool specifications."""
import bisect
from PySide6.QtCore import Qt, QModelIndex, QAbstractListModel, QSortFilterProxyModel, Slot, Signal


class ProjectItemSpecificationModel(QAbstractListModel):
    """Class to store specs that are available in a project e.g. GAMS or Julia models."""

    specification_replaced = Signal(str, str)

    def __init__(self, icons):
        super().__init__()
        self._spec_names = list()
        self._icons = icons
        self._project = None

    @Slot(str)
    def add_specification(self, name):
        """Adds a specification to the model.

        Args:
            name (str): specification's name
        """
        pos = bisect.bisect_left([x.lower() for x in self._spec_names], name.lower())
        self.insertRow(name, pos)

    @Slot(str)
    def remove_specification(self, name):
        """Removes a specification from the model

        Args:
            name (str): specification's name
        """
        for i, spec_name in enumerate(self._spec_names):
            if spec_name == name:
                self.removeRow(i)
                break

    @Slot(str, str)
    def replace_specification(self, old_name, new_name):
        """Replaces a specification.

        Args:
            old_name (str): previous name
            new_name (str): new name
        """
        self.remove_specification(old_name)
        self.add_specification(new_name)
        self.specification_replaced.emit(old_name, new_name)

    def connect_to_project(self, project):
        """Connects the model to a project.

        Args:
            project (SpineToolboxProject): project to connect to
        """
        self.clear()
        self._project = project
        for spec in self._project.specifications():
            self.insertRow(spec.name)
        self._project.specification_added.connect(self.add_specification)
        self._project.specification_about_to_be_removed.connect(self.remove_specification)
        self._project.specification_replaced.connect(self.replace_specification)

    def clear(self):
        self.beginResetModel()
        self._spec_names = list()
        self.endResetModel()

    def rowCount(self, parent=None):
        """Returns the number of specs in the model.

        Args:
            parent (QModelIndex): Not used (because this is a list)

        Returns:
            Number of rows (available specs) in the model
        """
        return len(self._spec_names)

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
        if role == Qt.ItemDataRole.DisplayRole:
            return self._spec_names[row]
        if role == Qt.ItemDataRole.DecorationRole:
            spec = self.specification(row)
            return self._icons[spec.item_type]

    def flags(self, index):
        """Returns enabled flags for the given index.

        Args:
            index (QModelIndex): Index of spec
        """
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def insertRow(self, spec_name, row=None, parent=QModelIndex()):
        """Insert row (specification) into model.

        Args:
            spec_name (str): name of spec added to the model
            row (int, optional): Row to insert spec to
            parent (QModelIndex): Parent of child (not used)

        Returns:
            Void
        """
        if row is None:
            row = self.rowCount()
        self.beginInsertRows(parent, row, row)
        self._spec_names.insert(row, spec_name)
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
        self._spec_names.pop(row)
        self.endRemoveRows()
        return True

    def specification(self, row):
        """Returns spec on given row.

        Args:
            row (int): Row of spec specification

        Returns:
            ProjectItemSpecification from specification list or None if given row is zero
        """
        if row < 0 or row >= self.rowCount():
            return None
        return self._project.get_specification(self._spec_names[row])

    def specification_row(self, name):
        """Returns the row on which the given specification is located or -1 if it is not found."""
        for i, spec_name in enumerate(self._spec_names):
            if name.lower() == spec_name.lower():
                return i
        return -1

    def specification_index(self, name):
        """Returns the QModelIndex on which a specification with
        the given name is located or invalid index if it is not found."""
        row = self.specification_row(name)
        if row == -1:
            return QModelIndex()
        return self.createIndex(row, 0)


class FilteredSpecificationModel(QSortFilterProxyModel):
    def __init__(self, item_type):
        super().__init__()
        self.item_type = item_type

    def filterAcceptsRow(self, source_row, source_parent):
        spec = self.sourceModel().specification(source_row)
        return spec.item_type == self.item_type

    def get_mime_data_text(self, index):
        row = self.mapToSource(index).row()
        return ",".join([self.item_type, self.sourceModel().specification(row).name])

    def specifications(self):
        """Yields all specs."""
        for row in range(self.rowCount()):
            source_row = self.mapToSource(self.index(row, 0)).row()
            yield self.sourceModel().specification(source_row)

    def specification(self, row):
        if row < 0 or row >= self.rowCount():
            return None
        index = self.index(row, 0)
        source_index = self.mapToSource(index)
        source_row = source_index.row()
        return self.sourceModel().specification(source_row)
