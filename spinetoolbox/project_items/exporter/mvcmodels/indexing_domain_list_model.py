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
Contains :class:`IndexingDomainListModel`.

:author: A. Soininen (VTT)
:date:   25.8.2020
"""
from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt, Signal
from spinetoolbox.spine_io.exporters import gdx


class IndexingDomainListItem:
    """
    Holds additional indexing domain information.

    Attributes:
        name (str): domain's name
        description (str): domain's description
        expression (str or NoneType): record key generator expression, or None
        length (int): length of the domain
        extract_from (str): parameter name if the record keys are to be extracted from a parameter
    """

    def __init__(self, name):
        """
        Args:
            name (str): domain's name
        """
        self.name = name
        self.description = ""
        self.expression = None
        self.length = 0
        self.extract_from = ""

    def records(self, db_map):
        """
        Generates :class:`Records`

        Args:
            db_map (DatabaseMappingBase): a database mapping, needed to extract parameter indexes

        Return:
            Records: domain's records
        """
        if self.expression is not None:
            return gdx.GeneratedRecords(self.expression, self.length)
        if self.extract_from:
            return gdx.ExtractedRecords.extract(self.extract_from, db_map)
        return gdx.LiteralRecords([])


class IndexingDomainListModel(QAbstractListModel):
    """A model to manage additional domains needed for indexed parameter expansion."""

    domain_renamed = Signal(str, str)
    """Emitted after a domain has been renamed."""
    indexes_changed = Signal(str, object)
    """Emitted when a domain's records change."""

    def __init__(self, set_settings):
        """
        Args:
            set_settings (SetSettings): export settings
        """
        super().__init__()
        self._domains = list()
        for name in set_settings.domain_names:
            metadata = set_settings.metadata(name)
            if metadata.origin != gdx.Origin.INDEXING:
                continue
            item = IndexingDomainListItem(name)
            item.description = metadata.description
            records = set_settings.records(name)
            if isinstance(records, gdx.GeneratedRecords):
                item.expression = records.expression
                item.length = len(records)
            elif isinstance(records, gdx.ExtractedRecords):
                item.extract_from = records.parameter_name
            self._domains.append(item)

    def create_new_domain(self):
        """Adds a new domain as the last element in the list."""
        self.insertRows(self.rowCount(), 1)

    def data(self, index, role=Qt.DisplayRole):
        """
        Returns the domain name at given row on ``DisplayRole``.

        Args:
            index (QModelIndex): an index to the list
            role (int): data role
        """
        if role == Qt.DisplayRole:
            return self._domains[index.row()].name
        return None

    def item_at(self, row):
        """
        Returns :class:`IndexingDomainListItem` at the given row.

        Args:
            row (int): a row in the list.

        Returns:
            IndexingDomainListItem: item at the given row
        """
        return self._domains[row]

    def flags(self, index):
        """
        Returns item flags.

        Args:
            index (QModelIndex): list index

        Returns:
            int: item flags
        """
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def gather_domains(self, db_map):
        """
        Returns domain name and records.

        Args:
            db_map (DatabaseMappingBase): a database map

        Returns:
            dict: mapping from domain name to records
        """
        return {item.name: item.records(db_map) for item in self._domains}

    def insertRows(self, row, count, parent=QModelIndex()):
        """
        Inserts new rows to the list.

        Args:
            row (int): first row occupied by the inserted items
            count (int): number of inserted items
            parent (QModelIndex): ignored

        Returns:
            bool: True if the operation was successful
        """
        self.beginInsertRows(parent, row, row + count - 1)
        reserved = {d.name for d in self._domains}
        names = list()
        number = 1
        while len(names) != count:
            name = f"t{number}"
            if name not in reserved:
                reserved.add(name)
                names.append(name)
            number += 1
        new_domains = [IndexingDomainListItem(name) for name in names]
        self._domains = self._domains[:row] + new_domains + self._domains[row:]
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        """
        Removes rows.

        Args:
            row (int): first row to remove
            count (int): number of rows to remove
            parent (QModelIndex): ignored

        Returns:
            bool: True if the operations was successful
        """
        self.beginRemoveRows(parent, row, row + count - 1)
        self._domains = self._domains[:row] + self._domains[row + count :]
        self.endRemoveRows()
        return True

    def remove_rows(self, rows):
        """
        Removes non-contiguous set of rows effectively resetting the model.

        Args:
            rows (list of int): rows to remove
        """
        if len(rows) == 1:
            self.removeRows(rows[0], 1)
            return
        if all(previous_row + 1 == next_row for previous_row, next_row in zip(rows[:-1], rows[1:])):
            self.removeRows(rows[0], len(rows))
            return
        self.beginResetModel()
        self._domains = [d for i, d in enumerate(self._domains) if i not in rows]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """
        Returns the list length.

        Returns:
            int: number of rows in the list
        """
        return len(self._domains)

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets domain name at given index on ``EditRole``.

        Args:
            index (QModelIndex): an index to the list
            value (str): new domain name
            role (int): role

        Returns:
            bool: True if a domain name was changed
        """
        if role != Qt.EditRole:
            return False
        reserved = {d.name for d in self._domains}
        if value in reserved:
            return False
        item = self._domains[index.row()]
        old_name = item.name
        item.name = value
        self.domain_renamed.emit(old_name, value)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])
        return True
