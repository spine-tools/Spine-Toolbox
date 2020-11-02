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
from distutils.util import strtobool
from PySide2.QtCore import QModelIndex, Qt, QAbstractTableModel, Signal
from PySide2.QtGui import QColor
from spinedb_api import (
    NoneMapping,
    ConstantMapping,
    ColumnMapping,
    ColumnHeaderMapping,
    TableNameMapping,
    RowMapping,
    ObjectClassMapping,
    ObjectGroupMapping,
    RelationshipClassMapping,
    AlternativeMapping,
    ScenarioMapping,
    ScenarioAlternativeMapping,
    ParameterValueListMapping,
    FeatureMapping,
    ToolMapping,
    ToolFeatureMapping,
    ToolFeatureMethodMapping,
    item_mapping_from_dict,
    NoParameterMapping,
    ParameterValueMapping,
    ParameterDefinitionMapping,
    SingleValueMapping,
    ArrayValueMapping,
    MapValueMapping,
    TimePatternValueMapping,
    TimeSeriesValueMapping,
)
from spine_engine.spine_io.type_conversion import DateTimeConvertSpec, FloatConvertSpec, StringConvertSpec
from ..commands import SetComponentMappingReference, SetComponentMappingType
from ..mapping_colors import ERROR_COLOR

_MAP_TYPE_DISPLAY_NAME = {
    NoneMapping: "None",
    ConstantMapping: "Constant",
    ColumnMapping: "Column",
    ColumnHeaderMapping: "Column Header",
    RowMapping: "Row",
    TableNameMapping: "Table Name",
}

_PARAMETER_TYPE_DISPLAY_NAME = {
    ParameterValueMapping: "Value",
    ParameterDefinitionMapping: "Definition",
    NoParameterMapping: "None",
}


_VALUE_TYPE_DISPLAY_NAME = {
    SingleValueMapping: "Single value",
    ArrayValueMapping: "Array",
    MapValueMapping: "Map",
    TimeSeriesValueMapping: "Time series",
    TimePatternValueMapping: "Time pattern",
}


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
    about_to_undo = Signal(str, str)
    """Emitted before an undo/redo action."""

    def __init__(self, table_name, mapping_name, mapping, undo_stack):
        """
        Args:
            table_name (str): source table name
            mapping_name (str): mapping name
            mapping (spinedb_api.ItemMappingBase): the item mapping to model
            undo_stack (QUndoStack): undo stack
        """
        super().__init__()
        self._component_names = []
        self._component_mappings = []
        self._colors = []
        self._item_mapping = None
        if mapping is not None:
            self.set_mapping(mapping)
        self._table_name = table_name
        self._mapping_name = mapping_name
        self._undo_stack = undo_stack

    @property
    def mapping(self):
        return self._item_mapping

    @property
    def mapping_name(self):
        return self._mapping_name

    @mapping_name.setter
    def mapping_name(self, name):
        self._mapping_name = name

    @property
    def source_table_name(self):
        return self._table_name

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
        if not self._item_mapping:
            return None
        if not self._item_mapping.has_parameters():
            return None
        return _PARAMETER_TYPE_DISPLAY_NAME[type(self._item_mapping.parameters)]

    def _value_mapping_attribute_name(self):
        if not self._item_mapping:
            return None
        if self._item_mapping.has_parameters():
            if isinstance(self._item_mapping.parameters, ParameterValueMapping):
                return "value"
            if isinstance(self._item_mapping.parameters, ParameterDefinitionMapping):
                return "default_value"
        if isinstance(self._item_mapping, ParameterValueListMapping):
            return "value"
        return None

    @property
    def value_type_label_text(self):
        return {"value": "Value type:", "default_value": "Default value type:"}.get(
            self._value_mapping_attribute_name()
        )

    @property
    def value_mapping(self):
        value_mapping_attribute_name = self._value_mapping_attribute_name()
        if not value_mapping_attribute_name:
            return None
        if self._item_mapping.has_parameters():
            return getattr(self._item_mapping.parameters, value_mapping_attribute_name)
        return getattr(self._item_mapping, value_mapping_attribute_name)

    @value_mapping.setter
    def value_mapping(self, value_mapping):
        value_mapping_attribute_name = self._value_mapping_attribute_name()
        if not value_mapping_attribute_name:
            return
        if self._item_mapping.has_parameters():
            return setattr(self._item_mapping.parameters, value_mapping_attribute_name, value_mapping)
        return setattr(self._item_mapping, value_mapping_attribute_name, value_mapping)

    @property
    def value_type(self):
        if not self.value_mapping:
            return None
        return _VALUE_TYPE_DISPLAY_NAME[type(self.value_mapping)]

    def mapping_has_parameters(self):
        """Returns True if the item mapping has parameters."""
        return self._item_mapping.has_parameters()

    def mapping_has_values(self):
        """Returns True if the parameter mapping has values."""
        return self.value_mapping is not None

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
            ParameterValueListMapping,
            FeatureMapping,
            ToolMapping,
            ToolFeatureMapping,
            ToolFeatureMethodMapping,
        )
        if not isinstance(mapping, classes):
            class_names = [c.__name__ for c in classes]
            raise TypeError(f"mapping must be of type: {class_names} instead got {type(mapping).__name__}")
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

    def change_item_mapping_type(self, new_type):
        """
        Change item mapping's type.

        Args:
            new_type (str): name of the type
        """
        self.beginResetModel()
        new_type = {
            "Object class": ObjectClassMapping,
            "Relationship class": RelationshipClassMapping,
            "Object group": ObjectGroupMapping,
            "Alternative": AlternativeMapping,
            "Scenario": ScenarioMapping,
            "Scenario alternative": ScenarioAlternativeMapping,
            "Parameter value list": ParameterValueListMapping,
            "Feature": FeatureMapping,
            "Tool": ToolMapping,
            "Tool feature": ToolFeatureMapping,
            "Tool feature method": ToolFeatureMethodMapping,
        }[new_type]
        if self._item_mapping is None:
            self._item_mapping = new_type()
        elif not isinstance(self._item_mapping, new_type):
            self._item_mapping = new_type.from_instance(self._item_mapping)
        self.update_display_table()
        self.endResetModel()

    def change_parameter_type(self, new_type):
        """
        Change parameter type
        """
        previous_value_mapping = self.value_mapping
        self.beginResetModel()
        if new_type == "None":
            self._item_mapping.parameters = None
        elif new_type == "Value":
            self._item_mapping.parameters = ParameterValueMapping()
        elif new_type == "Definition":
            self._item_mapping.parameters = ParameterDefinitionMapping()
        self.value_mapping = previous_value_mapping
        self.update_display_table()
        self.endResetModel()

    def change_value_type(self, new_type):
        """
        Change value type
        """

        if not self.mapping_has_values():
            return
        self.beginResetModel()
        if new_type == "None":
            self.value_mapping = None
        elif new_type == "Single value":
            self.value_mapping = SingleValueMapping()
        elif new_type == "Array":
            self.value_mapping = ArrayValueMapping()
        elif new_type == "Map":
            self.value_mapping = MapValueMapping()
        elif new_type == "Time series":
            self.value_mapping = TimeSeriesValueMapping()
        elif new_type == "Time pattern":
            self.value_mapping = TimePatternValueMapping()
        self.update_display_table()
        self.endResetModel()

    def set_parameter_mapping(self, mapping):
        """
        Changes the parameter mapping.

        Args:
            mapping (ParameterDefinitionMapping): new mapping
        """
        self.beginResetModel()
        self._item_mapping.parameters = mapping
        self.update_display_table()
        self.endResetModel()

    def update_display_table(self):
        self._component_names = self._item_mapping.component_names()
        self._component_mappings = self._item_mapping.component_mappings()
        self._colors = self._make_colors()

    def _make_colors(self):
        component_count = len(self._component_mappings)
        return [self._color_from_index(i, component_count).lighter() for i in range(component_count)]

    @staticmethod
    def _color_from_index(i, count):
        golden_ratio = 0.618033988749895
        h = golden_ratio * (360 / count) * i
        return QColor.fromHsv(h, 255, 255, 255)

    def get_map_type_display(self, mapping, name):
        if name == "Parameter values" and self._item_mapping.is_pivoted():
            return "Pivoted"
        if isinstance(mapping, RowMapping):
            if mapping.reference == -1:
                return "Headers"
            return "Row"
        return _MAP_TYPE_DISPLAY_NAME[type(mapping)]

    def get_map_value_display(self, mapping, name):
        if name == "Parameter values" and self._item_mapping.is_pivoted():
            return "Pivoted values"
        if isinstance(mapping, NoneMapping):
            return ""
        if isinstance(mapping, RowMapping) and mapping.reference == -1:
            return "Headers"
        mapping_ref = mapping.reference
        if (
            name in ("Scenario active flags", "Tool feature required flags")
            and isinstance(mapping, ConstantMapping)
            and mapping.is_valid()
        ):
            try:
                return bool(strtobool(mapping_ref))
            except ValueError:
                return mapping_ref
        if isinstance(mapping_ref, int):
            mapping_ref += 1
        return mapping_ref

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole):
            name = self._component_names[index.row()]
            if column == 0:
                return name
            m = self._component_mappings[index.row()]
            if column == 1:
                return self.get_map_type_display(m, name)
            if column == 2:
                return self.get_map_value_display(m, name)
            raise RuntimeError("Column out of bounds.")
        if role == Qt.BackgroundRole and column == 0:
            return self.data_color(self._component_names[index.row()])
        if column == 2:
            if role == Qt.BackgroundRole:
                if self._mapping_issues(index.row()):
                    return ERROR_COLOR
                return None
            if role == Qt.ToolTipRole:
                issue = self._mapping_issues(index.row())
                if issue:
                    return issue
                return None

    def data_color(self, display_name):
        return dict(zip(self._component_names, self._colors)).get(display_name)

    def _mapping_issues(self, row):
        """Returns a message string if given row contains issues, or an empty string if everything is OK."""
        issues = self._item_mapping.component_issues(row)
        if issues:
            return issues
        parameter_row = row - len(self._item_mapping.component_mappings())
        if parameter_row < 0:
            return ""
        return self._item_mapping.parameters.component_issues(parameter_row)

    def rowCount(self, index=None):
        if not self._item_mapping:
            return 0
        return len(self._component_names)

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
            if self._component_names[index.row()] == "Parameter values":
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
        name = self._component_names[row]
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

    def change_component_mapping(self, component_name, type_name, reference):
        """
        Pushes :class:`SetComponentMappingType` to the undo stack.

        Args:
            component_name (str): name of the component whose type to change
            type_name (str): name of the new type
            reference (str or int): component mapping reference
        """
        row = self._component_names.index(component_name)
        component_mapping = self._component_mappings[row]
        previous_reference = component_mapping.reference
        previous_type = _MAP_TYPE_DISPLAY_NAME[type(component_mapping)]
        self._undo_stack.beginMacro("mapping type change")
        self._undo_stack.push(
            SetComponentMappingType(component_name, self, type_name, previous_type, previous_reference)
        )
        self._undo_stack.push(
            SetComponentMappingReference(
                component_name, self, reference, previous_reference, isinstance(component_mapping, NoneMapping)
            )
        )
        self._undo_stack.endMacro()

    def set_type(self, name, value):
        """
        Changes the type of a component mapping.

        Args:
            name (str): component name
            value (str): mapping type name
        """
        self.about_to_undo.emit(self._table_name, self._mapping_name)
        if value in ("None", "", None):
            mapping = NoneMapping()
        elif value == "Constant":
            mapping = ConstantMapping()
        elif value == "Column":
            mapping = ColumnMapping()
        elif value == "Column Header":
            mapping = ColumnHeaderMapping()
        elif value == "Headers":
            mapping = RowMapping(reference=-1)
        elif value == "Row":
            mapping = RowMapping()
        elif value == "Table Name":
            mapping = TableNameMapping(self._table_name)
        else:
            return False
        return self._set_component_mapping_from_name(name, mapping)

    def set_value(self, name, value):
        """
        Sets the reference for given mapping.

        Args:
            name (str): name of the mapping
            value (str): a new value

        Returns:
            bool: True if the reference was modified successfully, False otherwise.
        """
        self.about_to_undo.emit(self._table_name, self._mapping_name)
        mapping = self._get_component_mapping_from_name(name)
        if isinstance(mapping, NoneMapping):
            mapping = ConstantMapping()
        try:
            mapping.reference = value
        except TypeError:
            return False
        if isinstance(mapping.reference, int):
            mapping.reference = mapping.reference - 1
        return self._set_component_mapping_from_name(name, mapping)

    def _get_component_mapping_from_name(self, name):
        if not self._item_mapping:
            return None
        component_names = self._item_mapping.component_names()
        component_mappings = self._item_mapping.component_mappings()
        name_to_component = dict(zip(component_names, component_mappings))
        return name_to_component.get(name)

    def _set_component_mapping_from_name(self, name, mapping):
        if not self._item_mapping:
            return False
        if not self._item_mapping.set_component_by_name(name, mapping):
            return False
        row = self._row_for_component_name(name)
        self._component_mappings[row] = mapping
        top_left = self.index(row, 1)
        bottom_right = self.index(row, 2)
        self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole, Qt.DisplayRole, Qt.ToolTipRole])
        # Recommend data types
        if name == "Parameter values":
            self._recommend_parameter_value_mapping_reference_type_change(mapping)
        elif name == "Parameter time index":
            self._recommend_datetime_type(mapping)
            self._recommend_float_type_for_non_pivoted_columns(mapping)
        elif name == "Parameter time pattern index":
            self._recommend_float_type_for_non_pivoted_columns(mapping)
        else:
            self._recommend_string_type(mapping)
        return True

    def _recommend_float_type_for_non_pivoted_columns(self, mapping):
        if (
            isinstance(mapping, RowMapping)
            and self._item_mapping.is_pivoted()
            and isinstance(self._item_mapping.parameters.value, NoneMapping)
        ):
            non_pivoted_columns = self._item_mapping.non_pivoted_columns()
            self.multi_column_type_recommendation_changed.emit(non_pivoted_columns, FloatConvertSpec())

    def _row_for_component_name(self, name):
        return self._component_names.index(name)

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

    def set_time_series_repeat(self, repeat):
        """Toggles the repeat flag in the parameter's options."""
        if self._item_mapping is None:
            return
        if not isinstance(self.value_mapping, TimeSeriesValueMapping):
            return
        self.value_mapping.options.repeat = repeat

    def set_map_dimensions(self, dimensions):
        if self._item_mapping is None:
            return
        if not isinstance(self.value_mapping, MapValueMapping):
            return
        previous_dimensions = len(self.value_mapping.extra_dimensions)
        if dimensions == previous_dimensions:
            return
        self.value_mapping.set_number_of_extra_dimensions(dimensions)
        first_dimension_row = 0
        for name in self._component_names:
            if name.startswith("Parameter index"):
                break
            first_dimension_row += 1
        if previous_dimensions < dimensions:
            first = first_dimension_row + previous_dimensions
            last = first_dimension_row + dimensions - 1
            self.beginInsertRows(QModelIndex(), first, last)
            self.endInsertRows()
        else:
            first = first_dimension_row + dimensions
            last = first_dimension_row + previous_dimensions - 1
            self.beginRemoveRows(QModelIndex(), first, last)
            self.endRemoveRows()
        self.update_display_table()

    def set_map_compress_flag(self, compress):
        """
        Sets the compress flag for Map type parameters.

        Args:
            compress (bool): flag value
        """
        if self._item_mapping is None or not isinstance(self.value_mapping, MapValueMapping):
            return
        self.value_mapping.compress = compress

    def to_dict(self):
        """
        Serializes the mapping specification into a dict.

        Returns:
            dict: serialized specification
        """
        specification_dict = self._item_mapping.to_dict()
        specification_dict["mapping_name"] = self._mapping_name
        return specification_dict

    @staticmethod
    def from_dict(specification_dict, table_name, undo_stack):
        """
        Restores a serialized mapping specification.

        Args:
            specification_dict (dict): serialized specification model
            table_name (str): source table name
            undo_stack (QUndoStack): undo stack

        Returns:
            MappingSpecificationModel: mapping specification
        """
        mapping_name = specification_dict.pop("mapping_name", "")
        mapping = item_mapping_from_dict(specification_dict)
        return MappingSpecificationModel(table_name, mapping_name, mapping, undo_stack)

    def duplicate(self, table_name, undo_stack):
        return self.from_dict(self.to_dict(), table_name, undo_stack)
