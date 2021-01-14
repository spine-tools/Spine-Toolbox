######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for models dealing with Data Packages.

:authors: M. Marin (KTH)
:date:   24.6.2018
"""

import os
from copy import deepcopy
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from .minimal_table_model import MinimalTableModel
from .empty_row_model import EmptyRowModel
from ..data_package_commands import (
    UpdateResourceNameCommand,
    UpdateResourceDataCommand,
    UpdateFieldNamesCommand,
    UpdatePrimaryKeysCommand,
    AppendForeignKeyCommandCommand,
    UpdateForeignKeyCommandCommand,
    RemoveForeignKeyCommandCommand,
)
from ..helpers import format_string_list


class DatapackageResourcesModel(MinimalTableModel):
    def __init__(self, parent, datapackage):
        """A model of datapackage resource data, used by SpineDatapackageWidget.

        Args:
            parent (SpineDatapackageWidget)
        """
        super().__init__(parent)
        self._parent = parent
        self.datapackage = datapackage
        self.set_horizontal_header_labels(["name", "source"])

    def refresh_model(self):
        data = [self._parent.is_resource_dirty(i) for i in range(len(self.datapackage.resources))]
        self.reset_model(data)

    def data(self, index, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return super().data(index, role=role)
        resource = self.datapackage.resources[index.row()]
        if index.column() == 0:
            dirty = self._main_data[index.row()]
            return resource.name + ("*" if dirty else "")
        return os.path.basename(resource.source)

    def update_resource_dirty(self, idx, dirty):
        if dirty == self._main_data[idx]:
            return
        self._main_data[idx] = dirty
        self.dataChanged.emit(self.index(idx, 0), self.index(idx, 0), [Qt.DisplayRole])

    def batch_set_data(self, indexes, data):
        for index, value in zip(indexes, data):
            self.set_data(index, value)
        return True

    def set_data(self, index, value):
        old_value = index.data(Qt.DisplayRole)
        if old_value == value:
            return False
        if not self._check_resource_name(value):
            return False
        resource_index = index.row()
        stack = self._parent.get_undo_stack(resource_index)
        stack.push(UpdateResourceNameCommand(self, resource_index, old_value, value))
        return True

    def _check_resource_name(self, name):
        error = self.datapackage.check_resource_name(name)
        if not error:
            return True
        self._parent.msg_error.emit(f"Unable to rename resource: {error}")
        return False

    def update_resource_name(self, resource_index, new_name):
        self.datapackage.rename_resource(resource_index, new_name)
        index = self.index(resource_index, 0)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            return flags & ~Qt.ItemIsEditable
        return flags


class DatapackageResourceDataModel(MinimalTableModel):
    def __init__(self, parent, datapackage):
        """A model of datapackage field data, used by SpineDatapackageWidget.

        Args:
            parent (SpineDatapackageWidget)
        """
        super().__init__(parent)
        self._parent = parent
        self.datapackage = datapackage
        self.resource_index = None

    def refresh_model(self, resource_index):
        self.resource_index = resource_index
        data = self.datapackage.resource_data(self.resource_index)
        self.reset_model(data)

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        return self.datapackage.resources[self.resource_index].schema.field_names[section]

    def batch_set_data(self, indexes, data):
        rows = []
        columns = []
        new_values = []
        old_values = []
        for index, new_value in zip(indexes, data):
            old_value = index.data(Qt.DisplayRole)
            if old_value == new_value:
                continue
            rows.append(index.row())
            columns.append(index.column())
            new_values.append(new_value)
            old_values.append(old_value)
        if not rows:
            return False
        self._parent.undo_stack.push(
            UpdateResourceDataCommand(self, self.resource_index, rows, columns, old_values, new_values)
        )
        return True

    def update_resource_data(self, resource_index, rows, columns, new_values):
        for row, column, new_value in zip(rows, columns, new_values):
            self.datapackage.set_resource_data(resource_index, row, column, new_value)
        if resource_index == self.resource_index:
            top_left = self.index(min(rows), min(columns))
            bottom_right = self.index(max(rows), max(columns))
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])


class DatapackageFieldsModel(MinimalTableModel):
    def __init__(self, parent, datapackage):
        """A model of datapackage field data, used by SpineDatapackageWidget.

        Args:
            parent (SpineDatapackageWidget)
        """
        super().__init__(parent)
        self._parent = parent
        self.datapackage = datapackage
        self.resource_index = None
        self.set_horizontal_header_labels(["name", "type", "primary key"])

    def refresh_model(self, resource_index):
        self.resource_index = resource_index
        fields = self.datapackage.resources[self.resource_index].schema.fields
        data = [None for _ in fields]
        self.reset_model(data)

    def data(self, index, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return super().data(index, role=role)
        schema = self.datapackage.resources[self.resource_index].schema
        field = schema.fields[index.row()]
        if index.column() == 0:
            return field.name
        if index.column() == 1:
            return field.type
        if index.column() == 2:
            return field.name in schema.primary_key

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 1:
            return flags & ~Qt.ItemIsEditable
        return flags

    def batch_set_data(self, indexes, data):
        name_indexes = []
        new_names = []
        old_names = []
        pk_indexes = []
        pk_statuses = []
        for index, new_value in zip(indexes, data):
            if index.column() == 0:
                old_value = index.data(Qt.DisplayRole)
                if new_value == old_value:
                    continue
                name_indexes.append(index.row())
                new_names.append(new_value)
                old_names.append(old_value)
            elif index.column() == 2:
                pk_indexes.append(index.row())
                pk_statuses.append(new_value)
        valid_names = self._valid_field_names(new_names)
        name_indexes = dict(zip(new_names, name_indexes))
        name_indexes = [name_indexes[name] for name in valid_names]
        old_names = dict(zip(new_names, old_names))
        old_names = [old_names[name] for name in valid_names]
        if not name_indexes and not pk_indexes:
            return False
        if name_indexes:
            self._parent.undo_stack.push(
                UpdateFieldNamesCommand(self, self.resource_index, name_indexes, old_names, valid_names)
            )
        if pk_indexes:
            self._parent.undo_stack.push(UpdatePrimaryKeysCommand(self, self.resource_index, pk_indexes, pk_statuses))
        return True

    def _valid_field_names(self, new_names):
        dups = set()
        seen = set()
        for name in new_names:
            if name in seen:
                dups.add(name)
            seen.add(name)
        valid_names = self.datapackage.valid_field_names(self.resource_index, new_names)
        invalid_names = set(new_names).difference(valid_names).union(dups)
        if invalid_names:
            msg = (
                "Unable to rename fields. "
                f"The following names are invalid or already in use: {format_string_list(invalid_names)}"
            )
            self._parent.msg_error.emit(msg)
        return list(valid_names)

    def update_field_names(self, resource_index, field_indexes, old_names, new_names):
        self.datapackage.rename_fields(resource_index, field_indexes, old_names, new_names)
        if resource_index == self.resource_index:
            top_left = self.index(min(field_indexes), 0)
            bottom_right = self.index(max(field_indexes), 0)
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

    def update_primary_keys(self, resource_index, field_indexes, statuses):
        for field_index, status in zip(field_indexes, statuses):
            if status:
                self.datapackage.append_to_primary_key(resource_index, field_index)
            else:
                self.datapackage.remove_from_primary_key(resource_index, field_index)
        if resource_index == self.resource_index:
            top_left = self.index(min(field_indexes), 2)
            bottom_right = self.index(max(field_indexes), 2)
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])


class DatapackageForeignKeysModel(EmptyRowModel):
    def __init__(self, parent, datapackage):
        """A model of datapackage foreign key data, used by SpineDatapackageWidget.

        Args:
            parent (SpineDatapackageWidget)
        """
        super().__init__(parent)
        self._parent = parent
        self.datapackage = datapackage
        self.resource_index = None
        self.set_horizontal_header_labels(["fields", "reference resource", "reference fields"])

    def refresh_model(self, resource_index):
        self.resource_index = resource_index
        data = [[None, None, None] for _ in self.foreign_keys]
        self.reset_model(data)

    @property
    def foreign_keys(self):
        if self.resource_index is None:
            return []
        return self.datapackage.resources[self.resource_index].schema.foreign_keys

    def data(self, index, role=Qt.DisplayRole):
        display_data = super().data(index, role=Qt.DisplayRole)
        if role in (Qt.DisplayRole, Qt.EditRole):
            if index.row() >= len(self.foreign_keys):
                return display_data
            if display_data is not None:
                return display_data
            return self._true_data(index)
        if role == Qt.FontRole:
            if (
                index.row() < len(self.foreign_keys)
                and display_data is not None
                and display_data != self._true_data(index)
            ):
                font = QFont("")
                font.setItalic(True)
                return font
        return super().data(index, role=role)

    def _true_data(self, index):
        foreign_key = self.foreign_keys[index.row()]
        if index.column() == 0:
            return ",".join(foreign_key['fields'])
        if index.column() == 1:
            return foreign_key['reference']['resource']
        if index.column() == 2:
            return ",".join(foreign_key['reference']['fields'])

    def _check_foreign_key(self, foreign_key):
        error = self.datapackage.check_foreign_key(self.resource_index, foreign_key)
        if not error:
            return True
        self._parent.msg_error.emit(f"Invalid foreign key: {error}")
        return False

    def batch_set_data(self, indexes, data):
        if not indexes or not data:
            return False
        for index, value in zip(indexes, data):
            self.set_data(index, value)
        return True

    def set_data(self, index, value):
        fk_index = index.row()
        column = index.column()
        self._main_data[fk_index][column] = value
        if fk_index >= len(self.foreign_keys):
            self._append_foreign_key(fk_index)
        else:
            self._update_foreign_key(fk_index)

    def _append_foreign_key(self, fk_index):
        row_data = self._main_data[fk_index]
        if not all(row_data):
            return
        fields_str, reference_resource, reference_fields_str = row_data
        foreign_key = {
            "fields": fields_str.split(","),
            "reference": {"resource": reference_resource, "fields": reference_fields_str.split(",")},
        }
        if not self._check_foreign_key(foreign_key):
            return
        self._parent.undo_stack.push(AppendForeignKeyCommandCommand(self, self.resource_index, foreign_key))

    def _update_foreign_key(self, fk_index):
        foreign_key = deepcopy(self.foreign_keys[fk_index])
        fields_str, reference_resource, reference_fields_str = self._main_data[fk_index]
        if fields_str is not None:
            foreign_key['fields'] = fields_str.split(",")
        if reference_resource is not None:
            foreign_key['reference']['resource'] = reference_resource
        if reference_fields_str is not None:
            foreign_key['reference']['fields'] = reference_fields_str.split(",")
        if not self._check_foreign_key(foreign_key):
            return
        if foreign_key == self.foreign_keys[fk_index]:
            return
        self._parent.undo_stack.push(UpdateForeignKeyCommandCommand(self, self.resource_index, fk_index, foreign_key))

    def append_foreign_key(self, resource_index, foreign_key):
        self.datapackage.append_foreign_key(resource_index, foreign_key)
        if resource_index == self.resource_index:
            self.insertRows(len(self.foreign_keys), 1)

    def update_foreign_key(self, resource_index, fk_index, foreign_key):
        self.datapackage.update_foreign_key(resource_index, fk_index, foreign_key)
        if resource_index == self.resource_index:
            self._main_data[fk_index] = [None, None, None]
            top_left = self.index(fk_index, 0)
            bottom_right = self.index(fk_index, 2)
            self.dataChanged.emit(top_left, bottom_right)

    def call_remove_foreign_key(self, fk_index):
        self._parent.undo_stack.push(RemoveForeignKeyCommandCommand(self, self.resource_index, fk_index))

    def remove_foreign_key(self, resource_index, fk_index):
        self.datapackage.remove_foreign_key(resource_index, fk_index)
        if resource_index == self.resource_index:
            self.removeRows(fk_index, 1)

    def insert_foreign_key(self, resource_index, fk_index, foreign_key):
        self.datapackage.insert_foreign_key(resource_index, fk_index, foreign_key)
        if resource_index == self.resource_index:
            self.insertRows(fk_index, 1)

    def emit_data_changed(self, roles=None):
        """Emits dataChanged for the entire model."""
        if roles is None:
            roles = [Qt.DisplayRole]
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right, roles)
