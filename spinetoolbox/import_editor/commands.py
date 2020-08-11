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
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QUndoCommand
from spinedb_api import parameter_mapping_from_dict


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


class SetItemMappingType(QUndoCommand):
    """Command to change item mapping's type."""

    def __init__(self, source_table_name, mapping_specification_name, options_widget, new_type, previous_mapping):
        """
        Args:
            source_table_name (src): name of the source table
            mapping_specification_name (str): name of the mapping
            options_widget (ImportMappingOptions): options widget
            new_type (str): name of the new mapping type
            previous_mapping (ItemMappingBase): the previous mapping
        """
        text = "mapping type change"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._mapping_specification_name = mapping_specification_name
        self._options_widget = options_widget
        self._new_type = new_type
        self._previous_mapping = previous_mapping

    def redo(self):
        """Sets the mapping type to its new value."""
        self._options_widget.set_item_mapping_type(
            self._source_table_name, self._mapping_specification_name, self._new_type
        )

    def undo(self):
        """Resets the mapping type to its former value."""
        self._options_widget.set_item_mapping(
            self._source_table_name, self._mapping_specification_name, self._previous_mapping
        )


class SetImportObjectsFlag(QUndoCommand):
    """Command to set item mapping's import objects flag."""

    def __init__(self, source_table_name, mapping_specification_name, options_widget, import_objects):
        """
        Args:
            source_table_name (str): name of the source table
            mapping_specification_name (str): name of the mapping specification
            options_widget (ImportMappingOptions): options widget
            import_objects (bool): new flag value
        """
        text = "import objects flag change"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._mapping_specification_name = mapping_specification_name
        self._options_widget = options_widget
        self._import_objects = import_objects

    def redo(self):
        self._options_widget.set_import_objects_flag(
            self._source_table_name, self._mapping_specification_name, self._import_objects
        )

    def undo(self):
        self._options_widget.set_import_objects_flag(
            self._source_table_name, self._mapping_specification_name, not self._import_objects
        )


class SetParameterType(QUndoCommand):
    """Command to change the parameter type of an item mapping."""

    def __init__(self, source_table_name, mapping_specification_name, options_widget, new_type, previous_parameter):
        """
        Args:
            source_table_name (str): name of the source table
            mapping_specification_name (str): name of the mapping specification
            options_widget (ImportMappingOptions): options widget
            new_type (str): name of the new parameter type
            previous_parameter (ParameterDefinitionMapping): previous parameter mapping
        """
        text = "parameter type change"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._mapping_specification_name = mapping_specification_name
        self._options_widget = options_widget
        self._new_type = new_type
        self._previous_parameter = previous_parameter.to_dict()

    def redo(self):
        self._options_widget.set_parameter_type(
            self._source_table_name, self._mapping_specification_name, self._new_type
        )

    def undo(self):
        mapping = parameter_mapping_from_dict(self._previous_parameter)
        self._options_widget.set_parameter_mapping(self._source_table_name, self._mapping_specification_name, mapping)


class SetReadStartRow(QUndoCommand):
    """Command to change item mapping's read start row option."""

    def __init__(self, source_table_name, mapping_specification_name, options_widget, start_row, previous_start_row):
        """
        Args:
            source_table_name (str): name of the source table
            mapping_specification_name (str): name of the mapping specification
            options_widget (ImportMappingOptions): options widget
            start_row (int): new read start row
            previous_start_row (int): previous read start row value
        """
        text = "mapping read start row change"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._mapping_specification_name = mapping_specification_name
        self._options_widget = options_widget
        self._start_row = start_row
        self._previous_start_row = previous_start_row

    def redo(self):
        """Changes item mapping's read start row to a new value."""
        self._options_widget.set_read_start_row(
            self._source_table_name, self._mapping_specification_name, self._start_row
        )

    def undo(self):
        """Restores item mapping's read start row to its previous value."""
        self._options_widget.set_read_start_row(
            self._source_table_name, self._mapping_specification_name, self._previous_start_row
        )


class SetItemMappingDimension(QUndoCommand):
    """Command to change item mapping's dimension option."""

    def __init__(self, source_table_name, mapping_specification_name, options_widget, dimension, previous_dimension):
        """
        Args:
            source_table_name (str): name of the source table
            mapping_specification_name (str): name of the mapping specification
            options_widget (ImportMappingOptions): options widget
            dimension (int): new dimension
            previous_dimension (int): previous dimension
        """
        text = "mapping dimension change"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._mapping_specification_name = mapping_specification_name
        self._options_widget = options_widget
        self._dimension = dimension
        self._previous_dimension = previous_dimension

    def redo(self):
        """Changes the item mapping's dimension to the new value."""
        self._options_widget.set_dimension(self._source_table_name, self._mapping_specification_name, self._dimension)

    def undo(self):
        """Changes the item mapping's dimension to its previous value."""
        self._options_widget.set_dimension(
            self._source_table_name, self._mapping_specification_name, self._previous_dimension
        )


class SetTimeSeriesRepeatFlag(QUndoCommand):
    """Command to change the repeat flag for time series."""

    def __init__(self, source_table_name, mapping_specification_name, options_widget, repeat):
        """
        Args:
            source_table_name (str): name of the source table
            mapping_specification_name (str): name of the mapping specification
            options_widget (ImportMappingOptions): options widget
            repeat (bool): new repeat flag value
        """
        text = "change time series repeat flag"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._mapping_specification_name = mapping_specification_name
        self._options_widget = options_widget
        self._repeat = repeat

    def redo(self):
        """Sets the repeat flag to given value."""
        self._options_widget.set_time_series_repeat_flag(
            self._source_table_name, self._mapping_specification_name, self._repeat
        )

    def undo(self):
        """Restores the repeat flag to its previous value."""
        self._options_widget.set_time_series_repeat_flag(
            self._source_table_name, self._mapping_specification_name, not self._repeat
        )


class SetMapDimensions(QUndoCommand):
    """Command to change the dimensions of a Map parameter value type."""

    def __init__(self, source_table_name, mapping_specification_name, options_widget, dimensions, previous_dimensions):
        text = "map dimensions change"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._mapping_specification_name = mapping_specification_name
        self._options_widget = options_widget
        self._dimensions = dimensions
        self._previous_dimensions = previous_dimensions

    def redo(self):
        """Sets the Map dimensions to the new value."""
        self._options_widget.set_map_dimensions(
            self._source_table_name, self._mapping_specification_name, self._dimensions
        )

    def undo(self):
        """Restores the previous Map dimensions value."""
        self._options_widget.set_map_dimensions(
            self._source_table_name, self._mapping_specification_name, self._previous_dimensions
        )


class SetColumnOrRowType(QUndoCommand):
    """Command to change the type of columns or rows."""

    def __init__(self, source_table_name, header_widget, sections, new_type, previous_type):
        """
        Args:
            source_table_name (src): name of the source table
            header_widget (HeaderWithButton): widget of origin
            sections (Iterable of int): row or column indexes
            new_type (ConvertSpec): conversion specification for the rows/columns
            previous_type (ConvertSpec): previous conversion specification for the rows/columns
        """
        text = ("row" if header_widget.orientation() == Qt.Vertical else "column") + " type change"
        super().__init__(text)
        self._source_table_name = source_table_name
        self._header_widget = header_widget
        self._sections = sections
        self._new_type = new_type
        self._previous_type = previous_type

    def redo(self):
        """Sets column/row type."""
        self._header_widget.set_data_types(self._source_table_name, self._sections, self._new_type)

    def undo(self):
        """Restores column/row type to its previous value."""
        self._header_widget.set_data_types(self._source_table_name, self._sections, self._previous_type)
