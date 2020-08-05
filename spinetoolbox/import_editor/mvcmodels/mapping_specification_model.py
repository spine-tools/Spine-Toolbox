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
Contains the mapping specification model.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""
from PySide2.QtCore import QModelIndex, Qt, QAbstractTableModel, Signal, Slot
from spinedb_api import (
    EntityClassMapping,
    ObjectClassMapping,
    RelationshipClassMapping,
    ObjectGroupMapping,
    AlternativeMapping,
    ScenarioMapping,
    ScenarioAlternativeMapping,
    ParameterDefinitionMapping,
    ParameterValueMapping,
    ParameterMapMapping,
    ParameterTimeSeriesMapping,
    ParameterTimePatternMapping,
    ParameterArrayMapping,
    NoneMapping,
    ConstantMapping,
    ColumnHeaderMapping,
    ColumnMapping,
    RowMapping,
    TableNameMapping,
)
from spinetoolbox.spine_io.type_conversion import DateTimeConvertSpec, FloatConvertSpec, StringConvertSpec
from ..commands import SetComponentMappingReference, SetComponentMappingType
from ..mapping_colors import ERROR_COLOR, MAPPING_COLORS

_MAP_TYPE_DISPLAY_NAME = {
    NoneMapping: "None",
    ConstantMapping: "Constant",
    ColumnMapping: "Column",
    ColumnHeaderMapping: "Column Header",
    RowMapping: "Row",
    TableNameMapping: "Table Name",
}


_DISPLAY_TYPE_TO_TYPE = {
    "Single value": ParameterValueMapping,
    "Array": ParameterArrayMapping,
    "Map": ParameterMapMapping,
    "Time series": ParameterTimeSeriesMapping,
    "Time pattern": ParameterTimePatternMapping,
    "Definition": ParameterDefinitionMapping,
    "None": NoneMapping,
}


_TYPE_TO_DISPLAY_TYPE = {value: key for key, value in _DISPLAY_TYPE_TO_TYPE.items()}


class MappingSpecificationModel(QAbstractTableModel):
    """
    A model to hold a Mapping specification.
    """

    mapping_read_start_row_changed = Signal(int)
    """Emitted after mapping's read start row has been changed."""
    row_or_column_type_recommendation_changed = Signal(int, object, object)
    """Emitted when a change in mapping prompts for change in column or row type."""
    multi_column_type_recommendation_changed = Signal(object, object)
    """Emitted when all but given columns should be of given type."""

    def __init__(self, mapping, table_name, undo_stack):
        """
        Args:
            mapping (spinedb_api.ItemMappingBase): the item mapping to model
            table_name (str): source table name
            undo_stack (QUndoStack): undo stack
        """
        super().__init__()
        self._display_names = []
        self._component_mappings = []
        self._item_mapping = None
        if mapping is not None:
            self.set_mapping(mapping)
        self._table_name = table_name
        self._undo_stack = undo_stack

    @property
    def mapping(self):
        return self._item_mapping

    @property
    def skip_columns(self):
        if self._item_mapping.skip_columns is None:
            return []
        return list(self._item_mapping.skip_columns)

    @property
    def map_type(self):
        if self._item_mapping is None:
            return None
        return type(self._item_mapping)

    @property
    def last_pivot_row(self):
        last_row = self._item_mapping.last_pivot_row()
        if last_row is None:
            last_row = 0
        return last_row

    @property
    def dimension(self):
        if self._item_mapping is None:
            return 0
        return self._item_mapping.dimensions

    @property
    def import_objects(self):
        if self._item_mapping is None:
            return False
        return self._item_mapping.import_objects

    @property
    def parameter_type(self):
        return _TYPE_TO_DISPLAY_TYPE[type(self._item_mapping.parameters)]

    @property
    def is_pivoted(self):
        if self._item_mapping:
            return self._item_mapping.is_pivoted()
        return False

    @property
    def read_start_row(self):
        if self._item_mapping:
            return self._item_mapping.read_start_row
        return 0

    def set_read_start_row(self, row):
        if self._item_mapping:
            self._item_mapping.read_start_row = row
            self.mapping_read_start_row_changed.emit(row)

    def set_import_objects(self, flag):
        self._item_mapping.import_objects = bool(flag)

    def set_mapping(self, mapping):
        classes = (
            RelationshipClassMapping,
            ObjectClassMapping,
            ObjectGroupMapping,
            AlternativeMapping,
            ScenarioMapping,
            ScenarioAlternativeMapping,
        )
        if not isinstance(mapping, classes):
            raise TypeError(f"mapping must be of type: {classes} instead got {type(mapping)}")
        if isinstance(mapping, type(self._item_mapping)):
            return
        self.beginResetModel()
        self._item_mapping = mapping
        self.update_display_table()
        self.endResetModel()

    def set_dimension(self, dim):
        if self._item_mapping is None or self._item_mapping.has_fixed_dimensions():
            return
        self.beginResetModel()
        if len(self._item_mapping.objects) >= dim:
            self._item_mapping.object_classes = self._item_mapping.object_classes[:dim]
            self._item_mapping.objects = self._item_mapping.objects[:dim]
        else:
            self._item_mapping.object_classes = self._item_mapping.object_classes + [None]
            self._item_mapping.objects = self._item_mapping.objects + [None]
        self.update_display_table()
        self.endResetModel()

    def change_model_class(self, new_class):
        """
        Change model between Relationship and Object class
        """
        self.beginResetModel()
        new_class = {
            "Object": ObjectClassMapping,
            "Relationship": RelationshipClassMapping,
            "Object group": ObjectGroupMapping,
            "Alternative": AlternativeMapping,
            "Scenario": ScenarioMapping,
            "Scenario Alternative": ScenarioAlternativeMapping,
        }[new_class]
        if self._item_mapping is None:
            self._item_mapping = new_class()
        elif not isinstance(self._item_mapping, new_class):
            self._item_mapping = new_class.from_instance(self._item_mapping)
        self.update_display_table()
        self.endResetModel()

    def change_parameter_type(self, new_type):
        """
        Change parameter type
        """

        self.beginResetModel()
        if new_type == "None":
            self._item_mapping.parameters = None
        elif new_type == "Single value":
            self._item_mapping.parameters = ParameterValueMapping()
        elif new_type == "Array":
            self._item_mapping.parameters = ParameterArrayMapping()
        elif new_type == "Definition":
            self._item_mapping.parameters = ParameterDefinitionMapping()
        elif new_type == "Map":
            self._item_mapping.parameters = ParameterMapMapping()
        elif new_type == "Time series":
            self._item_mapping.parameters = ParameterTimeSeriesMapping()
        elif new_type == "Time pattern":
            self._item_mapping.parameters = ParameterTimePatternMapping()

        self.update_display_table()
        self.endResetModel()

    def update_display_table(self):
        self._display_names = []
        self._component_mappings = []
        if not isinstance(self._item_mapping, ScenarioAlternativeMapping):
            self._component_mappings.append(self._item_mapping.name)
        if isinstance(self._item_mapping, RelationshipClassMapping):
            self._display_names.append("Relationship class names")
            if self._item_mapping.object_classes:
                self._display_names.extend(
                    [f"Object class names {i+1}" for i, oc in enumerate(self._item_mapping.object_classes)]
                )
                self._component_mappings.extend(list(self._item_mapping.object_classes))
            if self._item_mapping.objects:
                self._display_names.extend([f"Object names {i+1}" for i, oc in enumerate(self._item_mapping.objects)])
                self._component_mappings.extend(list(self._item_mapping.objects))
        elif isinstance(self._item_mapping, ObjectClassMapping):
            self._display_names.append("Object class names")
            self._display_names.append("Object names")
            self._component_mappings.append(self._item_mapping.objects)
        elif isinstance(self._item_mapping, ObjectGroupMapping):
            self._display_names.append("Object class names")
            self._display_names.append("Group names")
            self._component_mappings.append(self._item_mapping.groups)
            self._display_names.append("Member names")
            self._component_mappings.append(self._item_mapping.members)
        elif isinstance(self._item_mapping, AlternativeMapping):
            self._display_names.append("Alternative names")
        elif isinstance(self._item_mapping, ScenarioMapping):
            self._display_names.append("Scenario names")
            self._display_names.append("Scenario active flags")
            self._component_mappings.append(self._item_mapping.active)
        elif isinstance(self._item_mapping, ScenarioAlternativeMapping):
            self._display_names.append("Scenario names")
            self._display_names.append("Alternative names")
            self._display_names.append("Before Alternative names")
            self._component_mappings.append(self._item_mapping.scenario_name)
            self._component_mappings.append(self._item_mapping.alternative_name)
            self._component_mappings.append(self._item_mapping.before_alternative_name)
        if not self._item_mapping.has_parameters():
            return
        if isinstance(self._item_mapping.parameters, ParameterDefinitionMapping):
            self._display_names.append("Parameter names")
            self._component_mappings.append(self._item_mapping.parameters.name)
        if isinstance(self._item_mapping.parameters, ParameterValueMapping):
            self._display_names.append("Parameter values")
            self._component_mappings.append(self._item_mapping.parameters.value)
        if isinstance(self._item_mapping.parameters, ParameterMapMapping):
            for i, dimension in enumerate(self._item_mapping.parameters.extra_dimensions):
                self._display_names.append(f"Parameter index {i + 1}")
                self._component_mappings.append(dimension)
        if isinstance(self._item_mapping.parameters, ParameterTimeSeriesMapping):
            self._display_names.append("Parameter time index")
            self._component_mappings.append(self._item_mapping.parameters.extra_dimensions[0])
        if isinstance(self._item_mapping.parameters, ParameterTimePatternMapping):
            self._display_names.append("Parameter time pattern index")
            self._component_mappings.append(self._item_mapping.parameters.extra_dimensions[0])

    def get_map_type_display(self, mapping, name):
        if name == "Parameter values" and self._item_mapping.is_pivoted():
            mapping_type = "Pivoted"
        elif isinstance(mapping, RowMapping):
            if mapping.reference == -1:
                mapping_type = "Headers"
            else:
                mapping_type = "Row"
        else:
            mapping_type = _MAP_TYPE_DISPLAY_NAME[type(mapping)]
        return mapping_type

    def get_map_value_display(self, mapping, name):
        if name == "Parameter values" and self._item_mapping.is_pivoted():
            mapping_value = "Pivoted values"
        elif isinstance(mapping, NoneMapping):
            mapping_value = ""
        elif isinstance(mapping, RowMapping) and mapping.reference == -1:
            mapping_value = "Headers"
        else:
            mapping_value = mapping.reference
            if isinstance(mapping_value, int):
                mapping_value += 1
        return mapping_value

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole):
            name = self._display_names[index.row()]
            if column == 0:
                return name
            m = self._component_mappings[index.row()]
            if column == 1:
                return self.get_map_type_display(m, name)
            if column == 2:
                return self.get_map_value_display(m, name)
            raise RuntimeError("Column out of bounds.")
        if role == Qt.BackgroundColorRole and column == 0:
            return self.data_color(self._display_names[index.row()])
        if column == 2:
            if role == Qt.BackgroundColorRole:
                if self._mapping_issues(index.row()):
                    return ERROR_COLOR
                return None
            if role == Qt.ToolTipRole:
                issue = self._mapping_issues(index.row())
                if issue:
                    return issue
                return None

    @staticmethod
    def data_color(display_name):
        if display_name == "Relationship class names":
            return MAPPING_COLORS["entity_class"]
        if "Object class" in display_name:
            return MAPPING_COLORS["entity_class"]
        if "Object names" in display_name:
            return MAPPING_COLORS["entity"]
        if display_name == "Member names":
            return MAPPING_COLORS["entity"]
        if display_name == "Group names":
            return MAPPING_COLORS["group"]
        if display_name == "Alternative names":
            return MAPPING_COLORS["alternative"]
        if display_name == "Scenario names":
            return MAPPING_COLORS["scenario"]
        if display_name == "Before Alternative names":
            return MAPPING_COLORS["before_alternative"]
        if display_name == "Scenario active flags":
            return MAPPING_COLORS["active"]
        if display_name == "Parameter names":
            return MAPPING_COLORS["parameter_name"]
        if display_name in ("Parameter time index", "Parameter time pattern index") or display_name.startswith(
            "Parameter index"
        ):
            return MAPPING_COLORS["parameter_extra_dimension"]
        if display_name == "Parameter values":
            return MAPPING_COLORS["parameter_value"]

    def _mapping_issues(self, row):
        """Returns a message string if given row contains issues, or an empty string if everything is OK."""
        parameter_name_row = None
        if isinstance(self._item_mapping, EntityClassMapping):
            if row == 0:
                return self._item_mapping.class_names_issues()
        if isinstance(self._item_mapping, ObjectClassMapping):
            if row == 1:
                return self._item_mapping.object_names_issues()
            parameter_name_row = 2
        elif isinstance(self._item_mapping, RelationshipClassMapping):
            dimensions = len(self._item_mapping.object_classes)
            parameter_name_row = 2 * dimensions + 1
            if 1 <= row < parameter_name_row:
                display_name = self._display_names[row]
                mapping_name, _, mapping_number = display_name.rpartition(" ")
                index = int(mapping_number) - 1
                if mapping_name == "Object class names":
                    return self._item_mapping.object_class_names_issues(index)
                return self._item_mapping.object_names_issues(index)
        elif isinstance(self._item_mapping, ObjectGroupMapping):
            if row == 1:
                return self._item_mapping.group_names_issues()
            if row == 2:
                return self._item_mapping.member_names_issues()
            parameter_name_row = 3
        elif isinstance(self._item_mapping, AlternativeMapping):
            if row == 1:
                return self._item_mapping.alternative_names_issues()
        elif isinstance(self._item_mapping, ScenarioMapping):
            if row == 1:
                return self._item_mapping.scenario_names_issues()
        elif isinstance(self._item_mapping, ScenarioAlternativeMapping):
            if row == 1:
                return self._item_mapping.scenario_names_issues()
        if parameter_name_row is None:
            return ""
        if row == parameter_name_row:
            return self._item_mapping.parameters.names_issues()
        if row == parameter_name_row + 1:
            return self._item_mapping.parameters.values_issues(self._item_mapping.is_pivoted())
        if row >= parameter_name_row + 2:
            index = row - (parameter_name_row + 2)
            return self._item_mapping.parameters.indexes_issues(index)
        return ""

    def rowCount(self, index=None):
        if not self._item_mapping:
            return 0
        return len(self._display_names)

    def columnCount(self, index=None):
        if not self._item_mapping:
            return 0
        return 3

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ["Target", "Source type", "Source ref."][section]

    def flags(self, index):
        editable = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        non_editable = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0:
            return non_editable
        mapping = self._component_mappings[index.row()]

        if self._item_mapping.is_pivoted():
            # special case when we have pivoted data, the values should be
            # columns under pivoted indexes
            if self._display_names[index.row()] == "Parameter values":
                return non_editable

        if mapping is None or isinstance(mapping, NoneMapping):
            if index.column() <= 2:
                return editable
            return non_editable

        if isinstance(mapping, str):
            if index.column() <= 2:
                return editable
            return non_editable
        if isinstance(mapping, RowMapping) and mapping.reference == -1:
            if index.column() == 2:
                return non_editable
            return editable
        return editable

    def setData(self, index, value, role=Qt.DisplayRole):
        column = index.column()
        if column not in (1, 2):
            return False
        row = index.row()
        name = self._display_names[row]
        component_mapping = self._component_mappings[row]
        previous_reference = component_mapping.reference
        if isinstance(previous_reference, int):
            previous_reference += 1
        if column == 1:
            previous_type = _MAP_TYPE_DISPLAY_NAME[type(component_mapping)]
            self._undo_stack.push(SetComponentMappingType(name, self, value, previous_type, previous_reference))
        elif column == 2:
            self._undo_stack.push(
                SetComponentMappingReference(
                    name, self, value, previous_reference, isinstance(component_mapping, NoneMapping)
                )
            )
        return False

    def set_type(self, name, value):
        if value in ("None", "", None):
            value = NoneMapping()
        elif value == "Constant":
            value = ConstantMapping()
        elif value == "Column":
            value = ColumnMapping()
        elif value == "Column Header":
            value = ColumnHeaderMapping()
        elif value == "Headers":
            value = RowMapping(reference=-1)
        elif value == "Row":
            value = RowMapping()
        elif value == "Table Name":
            value = TableNameMapping(self._table_name)
        else:
            return False
        return self.set_component_mapping_from_name(name, value)

    def set_value(self, name, value):
        """
        Sets the reference for given mapping.

        Args:
            name (str): name of the mapping
            value (str): a new value

        Returns:
            bool: True if the reference was modified successfully, False otherwise.
        """
        mapping = self.get_component_mapping_from_name(name)
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        if isinstance(value, int):
            value -= 1
        if isinstance(mapping, NoneMapping):
            # create new mapping
            if isinstance(value, int):
                mapping = ColumnMapping(reference=value)
            elif value:
                mapping = ConstantMapping(reference=value)
            else:
                return False
        else:
            try:
                mapping.reference = value
            except ValueError:
                return False
        return self.set_component_mapping_from_name(name, mapping)

    def get_component_mapping_from_name(self, name):
        if not self._item_mapping:
            return None
        if name in ("Relationship class names", "Object class names"):
            return self._item_mapping.name
        if name in ("Alternative names", "Scenario names") and not isinstance(
            self._item_mapping, ScenarioAlternativeMapping
        ):
            return self._item_mapping.name
        if name == "Scenario names":
            return self._item_mapping.scenario_name
        if name == "Alternative names":
            return self._item_mapping.alternative_name
        if name == "Before Alternative names":
            return self._item_mapping.before_alternative_name
        if name == "Scenario active flags":
            return self._item_mapping.active
        if name == "Group names":
            return self._item_mapping.groups
        if name == "Member names":
            return self._item_mapping.members
        if name == "Object names":
            return self._item_mapping.objects
        if name.startswith("Object class"):
            # Not to be confused with name == 'Object class names'.
            return self._item_mapping.object_classes[_name_index(name)]
        if name.startswith("Object"):
            # Not to be confused with name == 'Object class names' or name == 'Object class X'.
            return self._item_mapping.objects[_name_index(name)]
        if name == "Parameter names":
            return self._item_mapping.parameters.name
        if name == "Parameter values":
            return self._item_mapping.parameters.value
        if name in ("Parameter time index", "Parameter time pattern index"):
            return self._item_mapping.parameters.extra_dimensions[0]
        if name.startswith("Parameter index"):
            return self._item_mapping.parameters.extra_dimensions[_name_index(name)]
        return None

    def set_component_mapping_from_name(self, name, mapping):
        if name in ("Relationship class names", "Object class names"):
            self._item_mapping.name = mapping
            self._recommend_string_type(mapping)
        elif name in ("Alternative names", "Scenario names") and not isinstance(
            self._item_mapping, ScenarioAlternativeMapping
        ):
            self._item_mapping.name = mapping
            self._recommend_string_type(mapping)
        elif name == "Scenario names":
            self._item_mapping.scenario_name = mapping
            self._recommend_string_type(mapping)
        elif name == "Alternative names":
            self._item_mapping.alternative_name = mapping
            self._recommend_string_type(mapping)
        elif name == "Before Alternative names":
            self._item_mapping.before_alternative_name = mapping
            self._recommend_string_type(mapping)
        elif name == "Scenario active flags":
            self._item_mapping.active = mapping
            self._recommend_string_type(mapping)
        elif name == "Object names":
            self._item_mapping.objects = mapping
            self._recommend_string_type(mapping)
        elif name == "Group names":
            self._item_mapping.groups = mapping
            self._recommend_string_type(mapping)
        elif name == "Member names":
            self._item_mapping.members = mapping
            self._recommend_string_type(mapping)
        elif "Object class " in name:
            self._item_mapping.object_classes[_name_index(name)] = mapping
            self._recommend_string_type(mapping)
        elif "Object " in name:
            self._item_mapping.objects[_name_index(name)] = mapping
            self._recommend_string_type(mapping)
        elif name == "Parameter names":
            self._item_mapping.parameters.name = mapping
            self._recommend_string_type(mapping)
        elif name == "Parameter values":
            self._item_mapping.parameters.value = mapping
            self._recommend_parameter_value_mapping_reference_type_change(mapping)
        elif name in ("Parameter time index", "Parameter time pattern index"):
            self._item_mapping.parameters.extra_dimensions = [mapping]
            if name == "Parameter time index":
                self._recommend_datetime_type(mapping)
            if (
                isinstance(mapping, RowMapping)
                and self._item_mapping.is_pivoted()
                and isinstance(self._item_mapping.parameters.value, NoneMapping)
            ):
                non_pivoted_columns = self._item_mapping.non_pivoted_columns()
                self.multi_column_type_recommendation_changed.emit(non_pivoted_columns, FloatConvertSpec())
        elif name.startswith("Parameter index"):
            self._item_mapping.parameters.extra_dimensions[_name_index(name)] = mapping
            self._recommend_string_type(mapping)
        else:
            return False
        row = self._row_for_component_name(name)
        self._component_mappings[row] = mapping
        top_left = self.index(row, 1)
        bottom_right = self.index(row, 2)
        self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundColorRole, Qt.DisplayRole, Qt.ToolTipRole])
        return True

    def _row_for_component_name(self, name):
        return self._display_names.index(name)

    def _recommend_string_type(self, mapping):
        self._recommend_mapping_reference_type_change(mapping, StringConvertSpec())

    def _recommend_float_type(self, mapping):
        self._recommend_mapping_reference_type_change(mapping, FloatConvertSpec())

    def _recommend_datetime_type(self, mapping):
        self._recommend_mapping_reference_type_change(mapping, DateTimeConvertSpec())

    def _recommend_mapping_reference_type_change(self, mapping, convert_spec):
        if mapping.reference is None:
            return
        if isinstance(mapping, ColumnMapping):
            self.row_or_column_type_recommendation_changed.emit(mapping.reference, convert_spec, Qt.Horizontal)
        elif isinstance(mapping, RowMapping):
            self.row_or_column_type_recommendation_changed.emit(mapping.reference, convert_spec, Qt.Vertical)

    def _recommend_parameter_value_mapping_reference_type_change(self, mapping):
        if isinstance(mapping, ColumnMapping):
            if mapping.reference is not None:
                self.row_or_column_type_recommendation_changed.emit(
                    mapping.reference, FloatConvertSpec(), Qt.Horizontal
                )
        elif isinstance(mapping, RowMapping):
            if mapping.reference is not None:
                self.row_or_column_type_recommendation_changed.emit(mapping.reference, FloatConvertSpec(), Qt.Vertical)
            else:
                non_pivoted_columns = self._item_mapping.non_pivoted_columns()
                self.multi_column_type_recommendation_changed.emit(non_pivoted_columns, FloatConvertSpec())

    def set_skip_columns(self, columns=None):
        if columns is None:
            columns = []
        self._item_mapping.skip_columns = list(set(columns))

    @Slot(bool)
    def set_time_series_repeat(self, repeat):
        """Toggles the repeat flag in the parameter's options."""
        if self._item_mapping is None or not isinstance(self._item_mapping.parameters, ParameterTimeSeriesMapping):
            return
        self._item_mapping.parameters.options.repeat = repeat

    @Slot(int)
    def set_map_dimensions(self, dimensions):
        if self._item_mapping is None or not isinstance(self._item_mapping.parameters, ParameterMapMapping):
            return
        previous_dimensions = len(self._item_mapping.parameters.extra_dimensions)
        if dimensions == previous_dimensions:
            return
        self._item_mapping.parameters.set_number_of_extra_dimensions(dimensions)
        first_dimension_row = 0
        for name in self._display_names:
            if name.startswith("Parameter index"):
                break
            first_dimension_row += 1
        if previous_dimensions < dimensions:
            first = first_dimension_row + previous_dimensions
            last = first_dimension_row + dimensions - 1
            self.beginInsertRows(QModelIndex(), first, last)
            for index in range(previous_dimensions, dimensions):
                self._display_names.append(f"Parameter index {index + 1}")
            self._component_mappings += self._item_mapping.parameters.extra_dimensions[previous_dimensions:]
            self.endInsertRows()
        else:
            first = first_dimension_row + dimensions
            last = first_dimension_row + previous_dimensions - 1
            self.beginRemoveRows(QModelIndex(), first, last)
            self._display_names = self._display_names[:first]
            self._component_mappings = self._component_mappings[:first]
            self.endRemoveRows()

    def mapping_has_parameters(self):
        """Returns True if the item mapping has parameters."""
        return self._item_mapping.has_parameters()

    def model_parameters(self):
        """Returns the mapping's parameters."""
        if self._item_mapping is None or not self._item_mapping.has_parameters():
            return None
        return self._item_mapping.parameters


def _name_index(name):
    """
    Parses an index from a string which ends with that number.

    Args:
        name (str): a string that ends with a number

    Returns:
        int: the number at the end of the given string minus one
    """
    _, number = name.rsplit(" ", 1)
    return int(number) - 1
