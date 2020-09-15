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
Contains :class:`SetListModel`

:author: A. Soininen (VTT)
:date:   25.8.2020
"""
from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt
from PySide2.QtGui import QColor
from spinetoolbox.spine_io.exporters import gdx
from ..list_utils import move_list_elements


class SetListModel(QAbstractListModel):
    """
    A model to configure the domain and set name lists in gdx export settings.

    This model combines domain and set names into a single list.
    The two 'parts' are differentiated by different background colors.
    Items from each part cannot be mixed with the other.
    Both the ordering of the items within each list as well as their exportability flags are handled here.
    """

    def __init__(self, set_settings):
        """
        Args:
            set_settings (gdx.SetSettings): settings whose domain and set name lists should be modelled
        """
        super().__init__()
        self._set_settings = set_settings
        self._sorted_domains = sorted(set_settings.domain_names, key=lambda name: set_settings.domain_tiers[name])
        self._sorted_sets = sorted(set_settings.set_names, key=lambda name: set_settings.set_tiers[name])

    def add_domain(self, domain_name, records, origin):
        """
        Adds a new additional domain.

        Args:
            domain_name (str): domain's name
            records (gdx.Records): domain's sorted records
            origin (gdx.Origin): domain's origin
        """
        metadata = gdx.SetMetadata(gdx.ExportFlag.EXPORTABLE, origin)
        if not self._set_settings.add_or_replace_domain(domain_name, records, metadata):
            first = len(self._set_settings.domain_names)
            last = first
            self.beginInsertRows(QModelIndex(), first, last)
            self._sorted_domains.append(domain_name)
            self.endInsertRows()

    def drop_domain(self, domain_name):
        """
        Removes a domain.

        Args:
            domain_name (str): name of the domain to remove
        """
        row = self._set_settings.domain_tiers[domain_name]
        self.beginRemoveRows(QModelIndex(), row, row)
        self._set_settings.remove_domain(domain_name)
        self._sorted_domains.pop(row)
        self.endRemoveRows()

    def update_domain(self, domain_name, records):
        """
        Updates the records of an existing domain.

        Args:
            domain_name (str): domain's name
            records (gdx.Records): updated records
        """
        self._set_settings.update_records(domain_name, records)
        row = self._set_settings.domain_tiers[domain_name]
        cell = self.index(row, 0)
        self.dataChanged.emit(cell, cell, [Qt.DisplayRole])

    def update_indexing_domains(self, domains):
        """
        Updates additional domains needed for parameter index expansion.

        Args:
            domains (dict): a mapping from domain name to records
        """
        old_indexing_domain_names = {
            name
            for name in self._set_settings.domain_names
            if self._set_settings.metadata(name).origin == gdx.Origin.INDEXING
        }
        domains_to_drop = old_indexing_domain_names - set(domains.keys())
        for name, records in domains.items():
            if name in self._set_settings.domain_names:
                self.update_domain(name, records)
            else:
                self.add_domain(name, records, gdx.Origin.INDEXING)
        for name in domains_to_drop:
            self.drop_domain(name)

    def data(self, index, role=Qt.DisplayRole):
        """
        Returns the value for given role at given index.

        Qt.DisplayRole returns the name of the domain or set
        while Qt.CheckStateRole returns whether the exportable flag has been set or not.
        Qt.BackgroundRole gives the item's background depending whether it is a domain or a set.

        Args:
            index (QModelIndex): an index to the model
            role (int): the query's role

        Returns:
            the requested value or `None`
        """
        if not index.isValid() or index.column() != 0 or index.row() >= self.rowCount():
            return None
        row = index.row()
        domain_count = len(self._sorted_domains)
        if role == Qt.DisplayRole:
            if row < domain_count:
                return self._sorted_domains[row]
            return self._sorted_sets[row - domain_count]
        if role == Qt.BackgroundRole:
            if row < domain_count:
                return QColor(Qt.lightGray)
            return None
        if role == Qt.CheckStateRole:
            if row < domain_count:
                checked = self._set_settings.metadata(self._sorted_domains[row]).is_exportable()
            else:
                checked = self._set_settings.metadata(self._sorted_sets[row - domain_count]).is_exportable()
            return Qt.Checked if checked else Qt.Unchecked
        if role == Qt.ToolTipRole:
            if row < domain_count and self._sorted_domains[row] == self._set_settings.global_parameters_domain_name:
                return "This domain has been set as the global\nparameters domain."
        return None

    def flags(self, index):
        """Returns an item's flags."""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Returns an empty string for horizontal header and row number for vertical header."""
        if orientation == Qt.Horizontal:
            return ""
        return section + 1

    def is_domain(self, index):
        """Returns True if index points to a domain name, otherwise returns False."""
        if not index.isValid():
            return False
        return index.row() < len(self._sorted_domains)

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        """
        Moves the domain and set names around.

        The names cannot be mixed between domains and sets.

        Args:
            sourceParent (QModelIndex): parent from which the rows are moved
            sourceRow (int): index of the first row to be moved
            count (int): number of rows to move
            destinationParent (QModelIndex): parent to which the rows are moved
            destinationChild (int): index where to insert the moved rows

        Returns:
            True if the operation was successful, False otherwise
        """
        row_count = self.rowCount()
        if destinationChild < 0 or destinationChild >= row_count:
            return False
        last_source_row = sourceRow + count - 1
        domain_count = len(self._sorted_domains)
        # Cannot move domains to ordinary sets and vice versa.
        if sourceRow < domain_count <= last_source_row:
            return False
        if sourceRow < domain_count <= destinationChild:
            return False
        if destinationChild < domain_count <= sourceRow:
            return False
        row_after = destinationChild if sourceRow > destinationChild else destinationChild + 1
        self.beginMoveRows(sourceParent, sourceRow, last_source_row, destinationParent, row_after)
        if sourceRow < domain_count:
            names = self._sorted_domains
        else:
            names = self._sorted_sets
            sourceRow -= domain_count
            last_source_row -= domain_count
            destinationChild -= domain_count
        names[:] = move_list_elements(names, sourceRow, last_source_row, destinationChild)
        tiers = self._set_settings.domain_tiers if sourceRow < domain_count else self._set_settings.set_tiers
        begin = min(sourceRow, destinationChild)
        end = max(sourceRow, destinationChild)
        for row, name in enumerate(names[begin : end + count]):
            tiers[name] = row + begin
        self.endMoveRows()
        return True

    def rowCount(self, parent=QModelIndex()):
        """Returns the number of rows."""
        return len(self._sorted_domains) + len(self._sorted_sets)

    def setData(self, index, value, role=Qt.EditRole):
        """Sets the exportable flag status for given row."""
        if not index.isValid() or role != Qt.CheckStateRole:
            return False
        row = index.row()
        domain_count = len(self._sorted_domains)
        if row < domain_count:
            name = self._sorted_domains[row]
            metadata = self._set_settings.metadata(name)
            exportable = gdx.ExportFlag.EXPORTABLE if value == Qt.Checked else gdx.ExportFlag.NON_EXPORTABLE
            metadata.exportable = exportable
        else:
            metadata = self._set_settings.metadata(self._sorted_sets[row - domain_count])
            exportable = gdx.ExportFlag.EXPORTABLE if value == Qt.Checked else gdx.ExportFlag.NON_EXPORTABLE
            metadata.exportable = exportable
            self.dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.ToolTipRole])
        self.dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.ToolTipRole])
        return True

    def update_global_parameters_domain(self, domain_name):
        previous = self._set_settings.global_parameters_domain_name
        if domain_name == previous:
            return
        self._set_settings.global_parameters_domain_name = domain_name
        if previous:
            row = self._set_settings.domain_tiers[previous]
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.ToolTipRole])
        if domain_name:
            row = self._set_settings.domain_tiers[domain_name]
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.ToolTipRole])
