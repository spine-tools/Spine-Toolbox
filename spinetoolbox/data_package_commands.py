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

from PySide2.QtWidgets import QUndoCommand


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
