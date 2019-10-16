######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Filled models for parameter definitions and values (as in 'filled with data').

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtGui import QGuiApplication
from ..mvcmodels.minimal_table_model import MinimalTableModel
from ..mvcmodels.parameter_value_formatting import format_for_DisplayRole, format_for_ToolTipRole


class FilledParameterModel(MinimalTableModel):
    """A parameter model filled with data."""

    json_fields = []
    fixed_fields = []

    def __init__(self, parent, header, db_mngr, db_map, lazy_loading=False):
        """Initialize class.

        Args:
            parent (Object): the parent object, typically a CompoundParameterModel
            header (list): list of field names for the header
        """
        super().__init__(parent, header)
        self.db_mngr = db_mngr
        self.db_map = db_map

    @property
    def item_type(self):
        raise NotImplementedError()

    @property
    def update_method_name(self):
        raise NotImplementedError()

    def insertRows(self, row, count, parent=QModelIndex()):
        """This model doesn't support row insertion."""
        return False

    def flags(self, index):
        """Make fixed indexes non-editable."""
        flags = super().flags(index)
        if self.header[index.column()] in self.fixed_fields:
            return flags & ~Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.DisplayRole):
        """Paint background of fixed indexes gray, apply custom format to JSON fields."""
        field = self.header[index.column()]
        if role == Qt.BackgroundRole and field in self.fixed_fields:
            return QGuiApplication.palette().button()
        id_ = self._main_data[index.row()]
        value = self.db_mngr.get_data(self.db_map, self.item_type, id_).get(field)
        if role in (Qt.DisplayRole, Qt.EditRole):
            if field == "database":
                return self.db_map.codename
            if field in self.json_fields:
                return format_for_DisplayRole(value)
            return value
        if role == Qt.ToolTipRole and field in self.json_fields:
            return format_for_ToolTipRole(value)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Set data directly in database. Let db mngr do the rest.
        """
        if not indexes or not data:
            return False
        row_data = dict()
        for index, value in zip(indexes, data):
            row_data.setdefault(index.row(), {})[self.header[index.column()]] = value
        data = [dict(id=self._main_data[row], **data) for row, data in row_data.items()]
        print(data)
        getattr(self.db_mngr, self.update_method_name)({self.db_map: data})
        return True
