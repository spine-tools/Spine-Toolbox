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
Classes for models dealing with Data Packages.

:authors: M. Marin (KTH)
:date:   24.6.2018
"""

import os
from copy import deepcopy
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QUndoCommand
from PySide2.QtGui import QFont
from datapackage.exceptions import DataPackageException
from .minimal_table_model import MinimalTableModel
from .empty_row_model import EmptyRowModel


class DatapackageResourcesModel(MinimalTableModel):

    resource_dirty_changed = Signal(int, bool)

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
        data = [self.datapackage.is_resource_dirty(i) for i in range(len(self.datapackage.resources))]
        self.reset_model(data)

    def data(self, index, role=Qt.DisplayRole):
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return super().data(index, role=role)
        resource = self.datapackage.resources[index.row()]
        if index.column() == 0:
            return resource.name
        dirty = self._main_data[index.row()]
        return os.path.basename(resource.source) + ("*" if dirty else "")

    def update_dirty(self, resource_index):
        dirty = self.datapackage.is_resource_dirty(resource_index)
        if dirty == self._main_data[resource_index]:
            return
        self._main_data[resource_index] = dirty
        index = self.index(resource_index, 1)
        self.dataChanged.emit(index, index, [Qt.DisplayRole])
        self.resource_dirty_changed.emit(resource_index, dirty)

    def setData(self, index, value, role=Qt.EditRole):
        if not value or role != Qt.EditRole:
            return False
        old_value = index.data(Qt.DisplayRole)
        if old_value == value:
            return False
        resource_index = index.row()
        self._parent.undo_stack.push(UpdateResourceNameCommand(self, resource_index, old_value, value))
        return True

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

    resource_data_changed = Signal(int)

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

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        old_value = index.data(Qt.DisplayRole)
        if old_value == value:
            return False
        row, column = index.row(), index.column()
        self._parent.undo_stack.push(
            UpdateResourceDataCommand(self, self.resource_index, row, column, old_value, value)
        )
        return True

    def update_resource_data(self, resource_index, row, column, new_value):
        self.datapackage.set_resource_data(resource_index, row, column, new_value)
        self.resource_data_changed.emit(resource_index)
        if resource_index == self.resource_index:
            index = self.index(row, column)
            self.dataChanged.emit(index, index, [Qt.DisplayRole])


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

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        field_index = index.row()
        if index.column() == 0:
            old_value = index.data(Qt.DisplayRole)
            if not value or value == old_value:
                return False
            self._parent.undo_stack.push(
                UpdateFieldNameCommand(self, self.resource_index, field_index, old_value, value)
            )
        if index.column() == 2:
            self._parent.undo_stack.push(UpdatePrimaryKeyCommand(self, self.resource_index, field_index, value))
        return True

    def update_field_name(self, resource_index, field_index, old_name, new_name):
        self.datapackage.rename_field(resource_index, field_index, old_name, new_name)
        if resource_index == self.resource_index:
            index = self.index(field_index, 0)
            self.dataChanged.emit(index, index, [Qt.DisplayRole])

    def update_primary_key(self, resource_index, field_index, status):
        if status:
            self.datapackage.append_to_primary_key(resource_index, field_index)
        else:
            self.datapackage.remove_from_primary_key(resource_index, field_index)
        if resource_index == self.resource_index:
            index = self.index(field_index, 2)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])


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

    def check_foreign_key(self, foreign_key):
        try:
            self.datapackage.check_foreign_key(self.resource_index, foreign_key)
            return True
        except DataPackageException as e:
            self._parent.msg_error.emit(f"Invalid foreign key: {e}")
            return False

    def setData(self, index, value, role=Qt.EditRole):
        if not super().setData(index, value, role):
            return False
        fk_index = index.row()
        if fk_index >= len(self.foreign_keys):
            self._add_foreign_key(fk_index)
        else:
            self._update_foreign_key(fk_index)
        return True

    def _add_foreign_key(self, fk_index):
        row_data = self._main_data[fk_index]
        if not all(row_data):
            return
        fields_str, reference_resource, reference_fields_str = row_data
        foreign_key = {
            "fields": fields_str.split(","),
            "reference": {"resource": reference_resource, "fields": reference_fields_str.split(",")},
        }
        if not self.check_foreign_key(foreign_key):
            return
        if self.removeRows(fk_index, 1):
            self._parent.undo_stack.push(AddForeignKeyCommandCommand(self, self.resource_index, foreign_key))

    def _update_foreign_key(self, fk_index):
        foreign_key = deepcopy(self.foreign_keys[fk_index])
        fields_str, reference_resource, reference_fields_str = self._main_data[fk_index]
        if fields_str is not None:
            foreign_key['fields'] = fields_str.split(",")
        if reference_resource is not None:
            foreign_key['reference']['resource'] = reference_resource
        if reference_fields_str is not None:
            foreign_key['reference']['fields'] = reference_fields_str.split(",")
        if not self.check_foreign_key(foreign_key):
            return
        if foreign_key == self.foreign_keys[fk_index]:
            return
        self._parent.undo_stack.push(UpdateForeignKeyCommandCommand(self, self.resource_index, fk_index, foreign_key))

    def add_foreign_key(self, resource_index, foreign_key):
        self.datapackage.add_foreign_key(resource_index, foreign_key)
        if resource_index == self.resource_index:
            self.insertRows(len(self.foreign_keys), 1)

    def remove_foreign_key(self, resource_index, fk_index):
        self.datapackage.remove_foreign_key(resource_index, fk_index)
        if resource_index == self.resource_index:
            self.removeRows(fk_index, 1)

    def update_foreign_key(self, resource_index, fk_index, foreign_key):
        self.datapackage.update_foreign_key(resource_index, fk_index, foreign_key)
        if resource_index == self.resource_index:
            self._main_data[fk_index] = [None, None, None]
            top_left = self.index(fk_index, 0)
            bottom_right = self.index(fk_index, 2)
            self.dataChanged.emit(top_left, bottom_right)

    def emit_data_changed(self, roles=None):
        """Emits dataChanged for the entire model."""
        if roles is None:
            roles = [Qt.DisplayRole]
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right, roles)


class UpdateResourceNameCommand(QUndoCommand):
    def __init__(self, model, resource_index, old_name, new_name):
        """Command to update a resource's name.

        Args:

        """
        super().__init__()
        self.model = model
        self.resource_index = resource_index
        self.old_name = old_name
        self.new_name = new_name
        self.setText(f"rename {old_name} to {new_name}")

    def redo(self):
        self.model.update_resource_name(self.resource_index, self.new_name)

    def undo(self):
        self.model.update_resource_name(self.resource_index, self.old_name)


class UpdateResourceDataCommand(QUndoCommand):
    def __init__(self, model, resource_index, row, column, old_value, new_value):
        """Command to update resource data.

        Args:

        """
        super().__init__()
        self.model = model
        self.resource_index = resource_index
        self.row = row
        self.column = column
        self.new_value = new_value
        self.old_value = old_value
        self.setText(f"update {old_value} to {new_value}")

    def redo(self):
        self.model.update_resource_data(self.resource_index, self.row, self.column, self.new_value)

    def undo(self):
        self.model.update_resource_data(self.resource_index, self.row, self.column, self.old_value)


class UpdateFieldNameCommand(QUndoCommand):
    def __init__(self, model, resource_index, field_index, old_name, new_name):
        """Command to update a resource's name.

        Args:

        """
        super().__init__()
        self.model = model
        self.resource_index = resource_index
        self.field_index = field_index
        self.old_name = old_name
        self.new_name = new_name
        self.setText(f"rename {old_name} to {new_name}")

    def redo(self):
        self.model.update_field_name(self.resource_index, self.field_index, self.old_name, self.new_name)

    def undo(self):
        self.model.update_field_name(self.resource_index, self.field_index, self.new_name, self.old_name)


class UpdatePrimaryKeyCommand(QUndoCommand):
    def __init__(self, model, resource_index, field_index, status):
        """Command to update a resource's name.

        Args:

        """
        super().__init__()
        self.model = model
        self.resource_index = resource_index
        self.field_index = field_index
        self.status = status
        field_name = self.model.index(self.field_index, 0).data()
        action = f"add {field_name} to" if self.status else f"remove {field_name} from"
        self.setText(f"{action} primary key")

    def redo(self):
        self.model.update_primary_key(self.resource_index, self.field_index, self.status)

    def undo(self):
        self.model.update_primary_key(self.resource_index, self.field_index, not self.status)


class AddForeignKeyCommandCommand(QUndoCommand):
    def __init__(self, model, resource_index, foreign_key):
        """Command to update a resource's name.

        Args:

        """
        super().__init__()
        self.model = model
        self.resource_index = resource_index
        self.foreign_key = foreign_key
        self.fk_index = len(model.foreign_keys)
        resource_name = self.model.datapackage.resources[self.resource_index].name
        self.setText(f"add foreign key to {resource_name}")

    def redo(self):
        self.model.add_foreign_key(self.resource_index, self.foreign_key)

    def undo(self):
        self.model.remove_foreign_key(self.resource_index, self.fk_index)


class UpdateForeignKeyCommandCommand(QUndoCommand):
    def __init__(self, model, resource_index, fk_index, foreign_key):
        """Command to update a resource's name.

        Args:

        """
        super().__init__()
        self.model = model
        self.resource_index = resource_index
        self.fk_index = fk_index
        self.foreign_key = foreign_key
        self.old_foreign_key = self.model.foreign_keys[fk_index]
        resource_name = self.model.datapackage.resources[self.resource_index].name
        self.setText(f"update foreign key of {resource_name}")

    def redo(self):
        self.model.update_foreign_key(self.resource_index, self.fk_index, self.foreign_key)

    def undo(self):
        self.model.update_foreign_key(self.resource_index, self.fk_index, self.old_foreign_key)
