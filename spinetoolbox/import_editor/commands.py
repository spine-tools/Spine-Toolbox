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
Contains undo and redo commands for Import editor.

:author: A. Soininen (VTT)
:date:   4.8.2020
"""
from enum import auto, IntEnum, unique
from PySide2.QtWidgets import QUndoCommand


@unique
class _Id(IntEnum):
    SET_OPTION = auto()


class SetTableChecked(QUndoCommand):
    def __init__(self, table_name, table_list_model, row, checked):
        text = ("select" if checked else "deselect") + f" '{table_name}'"
        super().__init__(text)
        self._model = table_list_model
        self._row = row
        self._checked = checked

    def redo(self):
        self._model.set_checked(self._row, self._checked)

    def undo(self):
        self._model.set_checked(self._row, not self._checked)


class SetComponentMappingType(QUndoCommand):
    def __init__(
        self, component_display_name, mapping_specification_model, mapping_type, previous_type, previous_reference
    ):
        text = "change source mapping"
        super().__init__(text)
        self._model = mapping_specification_model
        self._component_display_name = component_display_name
        self._new_type = mapping_type
        self._previous_type = previous_type
        self._previous_reference = previous_reference

    def redo(self):
        self._model.set_type(self._component_display_name, self._new_type)

    def undo(self):
        self._model.set_type(self._component_display_name, self._previous_type)
        self._model.set_value(self._component_display_name, self._previous_reference)


class SetComponentMappingReference(QUndoCommand):
    def __init__(
        self,
        component_display_name,
        mapping_specification_model,
        reference,
        previous_reference,
        previous_mapping_type_was_none,
    ):
        text = "change source mapping reference"
        super().__init__(text)
        self._model = mapping_specification_model
        self._component_display_name = component_display_name
        self._reference = reference
        self._previous_reference = previous_reference
        self._previous_mapping_type_was_none = previous_mapping_type_was_none

    def redo(self):
        self._model.set_value(self._component_display_name, self._reference)

    def undo(self):
        if self._previous_mapping_type_was_none:
            self._model.set_type(self._component_display_name, "None")
        else:
            self._model.set_value(self._component_display_name, self._previous_reference)


class SetConnectorOption(QUndoCommand):
    def __init__(self, source_table, option_key, options_widget, value, previous_value):
        text = f"change {option_key}"
        super().__init__(text)
        self._source_table = source_table
        self._option_key = option_key
        self._options_widget = options_widget
        self._value = value
        self._previous_value = previous_value

    def id(self):
        return _Id.SET_OPTION

    def mergeWith(self, command):
        if not isinstance(command, SetConnectorOption):
            return False
        return command._option_key == self._option_key and command._value == self._value

    def redo(self):
        self._options_widget.set_option_without_undo(self._source_table, self._option_key, self._value)

    def undo(self):
        self._options_widget.set_option_without_undo(self._source_table, self._option_key, self._previous_value)


class CreateMapping(QUndoCommand):
    def __init__(self, source_table_name, import_mappings, row):
        text = "new mapping"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._import_mappings = import_mappings
        self._mapping_name = None
        self._row = row
        self._stored_mapping_specification = None

    def redo(self):
        if self._mapping_name is None:
            self._mapping_name = self._import_mappings.create_mapping()
        else:
            self._import_mappings.insert_mapping_specification(
                self._source_table_name, self._mapping_name, self._row, self._stored_mapping_specification
            )

    def undo(self):
        self._stored_mapping_specification = self._import_mappings.delete_mapping(
            self._source_table_name, self._mapping_name
        )


class DeleteMapping(QUndoCommand):
    def __init__(self, source_table_name, import_mappings, mapping_name, row):
        text = "delete mapping"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._import_mappings = import_mappings
        self._mapping_name = mapping_name
        self._row = row
        self._stored_mapping_specification = None

    def redo(self):
        self._stored_mapping_specification = self._import_mappings.delete_mapping(
            self._source_table_name, self._mapping_name
        )

    def undo(self):
        self._import_mappings.insert_mapping_specification(
            self._source_table_name, self._mapping_name, self._row, self._stored_mapping_specification
        )
