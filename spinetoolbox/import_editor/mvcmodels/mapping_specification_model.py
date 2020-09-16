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
from PySide2.QtCore import QModelIndex, Qt, QAbstractTableModel, Signal
from PySide2.QtGui import QColor
from spinedb_api import (
    AlternativeMapping,
    ColumnHeaderMapping,
    ColumnMapping,
    ConstantMapping,
    dict_to_map,
    FeatureMapping,
    NoneMapping,
    ObjectClassMapping,
    ObjectGroupMapping,
    ParameterArrayMapping,
    ParameterDefinitionMapping,
    ParameterMapMapping,
    ParameterTimePatternMapping,
    ParameterTimeSeriesMapping,
    ParameterValueMapping,
    RelationshipClassMapping,
    RowMapping,
    ScenarioMapping,
    ScenarioAlternativeMapping,
    TableNameMapping,
    ToolMapping,
    ToolFeatureMapping,
    ToolFeatureMethodMapping,
)
from spinetoolbox.spine_io.type_conversion import DateTimeConvertSpec, FloatConvertSpec, StringConvertSpec
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
        self._display_names = []
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
            "Object": ObjectClassMapping,
            "Relationship": RelationshipClassMapping,
            "Object group": ObjectGroupMapping,
            "Alternative": AlternativeMapping,
            "Scenario": ScenarioMapping,
            "Scenario alternative": ScenarioAlternativeMapping,
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
        self._display_names = self._item_mapping.display_names()
        self._component_mappings = self._item_mapping.component_mappings()
        if self._item_mapping.has_parameters():
            self._display_names += self._item_mapping.parameters.display_names()
            self._component_mappings += self._item_mapping.parameters.component_mappings()
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
        if role == Qt.BackgroundRole and column == 0:
            return self.data_color(self._display_names[index.row()])
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
        return dict(zip(self._display_names, self._colors)).get(display_name)

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

    def change_component_mapping(self, component_name, type_name, reference):
        """
        Pushes :class:`SetComponentMappingType` to the undo stack.

        Args:
            component_name (str): name of the component whose type to change
            type_name (str): name of the new type
            reference (str or int): component mapping reference
        """
        row = self._display_names.index(component_name)
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
        return self._set_component_mapping_from_name(name, value)

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
            except TypeError:
                return False
        return self._set_component_mapping_from_name(name, mapping)

    def _get_component_mapping_from_name(self, name):
        if not self._item_mapping:
            return None
        display_names = self._item_mapping.display_names()
        component_mappings = self._item_mapping.component_mappings()
        if self._item_mapping.has_parameters():
            display_names += self._item_mapping.parameters.display_names()
            component_mappings += self._item_mapping.parameters.component_mappings()
        name_to_component = dict(zip(display_names, component_mappings))
        return name_to_component.get(name)

    def _set_component_mapping_from_name(self, name, mapping):
        if not self._item_mapping:
            return False
        if not self._item_mapping.set_component_by_display_name(name, mapping):
            if not self._item_mapping.has_parameters():
                return False
            if not self._item_mapping.parameters.set_component_by_display_name(name, mapping):
                return False
        row = self._row_for_component_name(name)
        self._component_mappings[row] = mapping
        top_left = self.index(row, 1)
        bottom_right = self.index(row, 2)
        self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole, Qt.DisplayRole, Qt.ToolTipRole])
        # FIXME: Try and see if we can do better here below
        if name == "Parameter values":
            self._recommend_parameter_value_mapping_reference_type_change(mapping)
        elif name in ("Parameter time index", "Parameter time pattern index"):
            if name == "Parameter time index":
                self._recommend_datetime_type(mapping)
            if (
                isinstance(mapping, RowMapping)
                and self._item_mapping.is_pivoted()
                and isinstance(self._item_mapping.parameters.value, NoneMapping)
            ):
                non_pivoted_columns = self._item_mapping.non_pivoted_columns()
                self.multi_column_type_recommendation_changed.emit(non_pivoted_columns, FloatConvertSpec())
        else:
            self._recommend_string_type(mapping)
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

    def set_time_series_repeat(self, repeat):
        """Toggles the repeat flag in the parameter's options."""
        if self._item_mapping is None or not isinstance(self._item_mapping.parameters, ParameterTimeSeriesMapping):
            return
        self._item_mapping.parameters.options.repeat = repeat

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

    def set_map_compress_flag(self, compress):
        """
        Sets the compress flag for Map type parameters.

        Args:
            compress (bool): flag value
        """
        if self._item_mapping is None or not isinstance(self._item_mapping.parameters, ParameterMapMapping):
            return
        self._item_mapping.parameters.compress = compress

    def mapping_has_parameters(self):
        """Returns True if the item mapping has parameters."""
        return self._item_mapping.has_parameters()

    def model_parameters(self):
        """Returns the mapping's parameters."""
        if self._item_mapping is None or not self._item_mapping.has_parameters():
            return None
        return self._item_mapping.parameters

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
        mapping = dict_to_map(specification_dict)
        return MappingSpecificationModel(table_name, mapping_name, mapping, undo_stack)


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
