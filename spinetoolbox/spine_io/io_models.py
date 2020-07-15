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
Classes for handling models in PySide2's model/view framework.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""
from PySide2.QtCore import QModelIndex, Qt, QAbstractTableModel, QAbstractListModel, Signal, Slot
from PySide2.QtGui import QColor
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
    MappingBase,
    NoneMapping,
    ConstantMapping,
    ColumnHeaderMapping,
    ColumnMapping,
    RowMapping,
    TableNameMapping,
    ParameterValueFormatError,
    mapping_non_pivoted_columns,
)
from ..mvcmodels.minimal_table_model import MinimalTableModel
from .type_conversion import ConvertSpec, DateTimeConvertSpec, FloatConvertSpec, StringConvertSpec


_MAPPING_COLORS = {
    "entity_class": QColor(196, 117, 56),
    "entity": QColor(223, 194, 125),
    "group": QColor(120, 150, 220),
    "parameter_value": QColor(128, 205, 193),
    "parameter_extra_dimension": QColor(41, 173, 153),
    "parameter_name": QColor(178, 255, 243),
    "alternative": QColor(196, 117, 56),
    "scenario": QColor(223, 194, 125),
    "active": QColor(128, 205, 193),
    "before_alternative": QColor(120, 150, 220),
}
_ERROR_COLOR = QColor(Qt.red)


_COLUMN_TYPE_ROLE = Qt.UserRole
_COLUMN_NUMBER_ROLE = Qt.UserRole + 1

_MAPTYPE_DISPLAY_NAME = {
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


class MappingPreviewModel(MinimalTableModel):
    """A model for import mapping specification.

    Highlights columns, rows, and so on, depending on Mapping specification.
    """

    column_types_updated = Signal()
    row_types_updated = Signal()
    mapping_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self._mapping = None
        self._data_changed_signal = None
        self._row_or_column_type_recommendation_changed_signal = None
        self._multi_column_type_recommendation_changed_signal = None
        self._column_types = {}
        self._row_types = {}
        self._column_type_errors = {}
        self._row_type_errors = {}

    def mapping(self):
        return self._mapping

    def clear(self):
        self._column_type_errors = {}
        self._row_type_errors = {}
        self._column_types = {}
        self._row_types = {}
        super().clear()

    def reset_model(self, main_data=None):
        self._column_type_errors = {}
        self._row_type_errors = {}
        self._column_types = {}
        self._row_types = {}
        super().reset_model(main_data)

    def set_mapping(self, mapping):
        """Set mapping to display colors from

        Args:
            mapping (MappingSpecModel): mapping model
        """
        if not mapping:
            return
        if not isinstance(mapping, MappingSpecModel):
            raise TypeError(f"mapping must be instance of 'MappingSpecModel', instead got: '{type(mapping).__name__}'")
        if self._mapping is not None:
            if self._data_changed_signal is not None:
                self._mapping.dataChanged.disconnect(self._mapping_data_changed)
                self._data_changed_signal = None
            if self._row_or_column_type_recommendation_changed_signal is not None:
                self._mapping.row_or_column_type_recommendation_changed.disconnect(self.set_type)
                self._row_or_column_type_recommendation_changed_signal = None
            if self._multi_column_type_recommendation_changed_signal is not None:
                self._mapping.multi_column_type_recommendation_changed.disconnect(self.set_all_column_types)
                self._multi_column_type_recommendation_changed_signal = None
        self._mapping = mapping
        self._data_changed_signal = self._mapping.dataChanged.connect(self._mapping_data_changed)
        self._row_or_column_type_recommendation_changed_signal = self._mapping.row_or_column_type_recommendation_changed.connect(
            self.set_type
        )
        self._multi_column_type_recommendation_changed_signal = self._mapping.multi_column_type_recommendation_changed.connect(
            self.set_all_column_types
        )
        self._mapping_data_changed()

    def validate(self, section, orientation=Qt.Horizontal):
        type_class = self.get_type(section, orientation)
        if type_class is None:
            return
        if orientation == Qt.Horizontal:
            other_orientation_count = self.rowCount()
            correct_index_order = lambda x: (x[1], x[0])
            error_dict = self._column_type_errors
        else:
            other_orientation_count = self.columnCount()
            correct_index_order = lambda x: (x[0], x[1])
            error_dict = self._row_type_errors
        converter = type_class.convert_function()
        for other_index in range(other_orientation_count):
            index_tuple = correct_index_order((section, other_index))
            index = self.index(*index_tuple)
            error_dict.pop(index_tuple, None)
            data = self.data(index)
            try:
                if isinstance(data, str) and not data:
                    data = None
                if data is not None:
                    converter(data)
            except (ValueError, ParameterValueFormatError) as e:
                error_dict[index_tuple] = e
        data_changed_start = correct_index_order((section, 0))
        data_changed_end = correct_index_order((section, other_orientation_count))
        self.dataChanged.emit(self.index(*data_changed_start), self.index(*data_changed_end))

    def get_type(self, section, orientation=Qt.Horizontal):
        if orientation == Qt.Horizontal:
            return self._column_types.get(section, None)
        return self._row_types.get(section, None)

    def get_types(self, orientation=Qt.Horizontal):
        if orientation == Qt.Horizontal:
            return self._column_types
        return self._row_types

    @Slot(int, object, object)
    def set_type(self, section, section_type, orientation=Qt.Horizontal):
        if orientation == Qt.Horizontal:
            count = self.columnCount()
            emit_signal = self.column_types_updated
            type_dict = self._column_types
        else:
            count = self.rowCount()
            emit_signal = self.row_types_updated
            type_dict = self._row_types
        if not isinstance(section_type, ConvertSpec):
            raise TypeError(
                f"section_type must be a instance of ConvertSpec, instead got {type(section_type).__name__}"
            )
        if section < 0 or section >= count:
            return
        type_dict[section] = section_type
        emit_signal.emit()
        self.validate(section, orientation)

    def set_types(self, sections, section_type, orientation):
        type_dict = self._column_types if orientation == Qt.Horizontal else self._row_types
        for section in sections:
            type_dict[section] = section_type
            self.validate(section, orientation)
        if orientation == Qt.Horizontal:
            self.column_types_updated.emit()
        else:
            self.row_types_updated.emit()

    @Slot(object, object)
    def set_all_column_types(self, excluded_columns, column_type):
        for column in range(self.columnCount()):
            if column not in excluded_columns:
                self._column_types[column] = column_type
        self.column_types_updated.emit()

    def _mapping_data_changed(self):
        self.update_colors()
        self.mapping_changed.emit()

    def update_colors(self):
        self.dataChanged.emit(QModelIndex, QModelIndex, [Qt.BackgroundColorRole])

    def data_error(self, index, role=Qt.DisplayRole, orientation=Qt.Horizontal):
        if role == Qt.DisplayRole:
            return "Error"
        if role == Qt.ToolTipRole:
            type_name = self.get_type(index.column(), orientation)
            return f'Could not parse value: "{self._main_data[index.row()][index.column()]}" as a {type_name}'
        if role == Qt.BackgroundColorRole:
            return _ERROR_COLOR

    def data(self, index, role=Qt.DisplayRole):
        if self._mapping:
            last_pivoted_row = self._mapping.last_pivot_row
            read_from_row = self._mapping.read_start_row
        else:
            last_pivoted_row = -1
            read_from_row = 0

        if index.row() > max(last_pivoted_row, read_from_row - 1):
            if (index.row(), index.column()) in self._column_type_errors:
                return self.data_error(index, role)

        if index.row() <= last_pivoted_row:
            if (
                index.column() not in mapping_non_pivoted_columns(self._mapping.model, self.columnCount(), self.header)
                and index.column() not in self._mapping.skip_columns
            ):
                if (index.row(), index.column()) in self._row_type_errors:
                    return self.data_error(index, role, orientation=Qt.Vertical)

        if role == Qt.BackgroundColorRole and self._mapping:
            return self.data_color(index)
        return super().data(index, role)

    def data_color(self, index):
        """
        Returns background color for index depending on mapping.

        Arguments:
            index (PySide2.QtCore.QModelIndex): index

        Returns:
            QColor: color of index
        """
        mapping = self._mapping.model
        if isinstance(mapping, EntityClassMapping):
            if isinstance(mapping.parameters, ParameterValueMapping):
                # parameter values color
                if mapping.is_pivoted():
                    last_row = max(mapping.last_pivot_row(), mapping.read_start_row - 1)
                    if (
                        last_row is not None
                        and index.row() > last_row
                        and index.column() not in self.mapping_column_ref_int_list()
                    ):
                        return _MAPPING_COLORS["parameter_value"]
                elif self.index_in_mapping(mapping.parameters.value, index):
                    return _MAPPING_COLORS["parameter_value"]
            if isinstance(mapping.parameters, ParameterArrayMapping) and mapping.parameters.extra_dimensions:
                # parameter extra dimensions color
                for ed in mapping.parameters.extra_dimensions:
                    if self.index_in_mapping(ed, index):
                        return _MAPPING_COLORS["parameter_extra_dimension"]
            if isinstance(mapping.parameters, ParameterDefinitionMapping) and self.index_in_mapping(
                mapping.parameters.name, index
            ):
                # parameter name colors
                return _MAPPING_COLORS["parameter_name"]
        if not isinstance(
            mapping, (AlternativeMapping, ScenarioMapping, ScenarioAlternativeMapping)
        ) and self.index_in_mapping(mapping.name, index):
            return _MAPPING_COLORS["entity_class"]
        classes = []
        objects = []
        if isinstance(mapping, ObjectClassMapping):
            objects = [mapping.objects]
        elif isinstance(mapping, ObjectGroupMapping):
            if self.index_in_mapping(mapping.groups, index):
                return _MAPPING_COLORS["group"]
            objects = [mapping.members]
        elif isinstance(mapping, RelationshipClassMapping):
            objects = mapping.objects
            classes = mapping.object_classes
        elif isinstance(mapping, AlternativeMapping):
            if self.index_in_mapping(mapping.name, index):
                return _MAPPING_COLORS["alternative"]
        elif isinstance(mapping, ScenarioMapping):
            if self.index_in_mapping(mapping.name, index):
                return _MAPPING_COLORS["scenario"]
            if self.index_in_mapping(mapping.active, index):
                return _MAPPING_COLORS["active"]
        elif isinstance(mapping, ScenarioAlternativeMapping):
            if self.index_in_mapping(mapping.scenario_name, index):
                return _MAPPING_COLORS["scenario"]
            if self.index_in_mapping(mapping.alternative_name, index):
                return _MAPPING_COLORS["alternative"]
            if self.index_in_mapping(mapping.before_alternative_name, index):
                return _MAPPING_COLORS["before_alternative"]
        for o in objects:
            # object colors
            if self.index_in_mapping(o, index):
                return _MAPPING_COLORS["entity"]
        for c in classes:
            # object colors
            if self.index_in_mapping(c, index):
                return _MAPPING_COLORS["entity_class"]

    def index_in_mapping(self, mapping, index):
        """
        Checks if index is in mapping

        Args:
            mapping (MappingBase): mapping
            index (QModelIndex): index

        Returns:
            bool: True if mapping is in index
        """
        if not isinstance(mapping, MappingBase):
            return False
        if isinstance(mapping, ColumnHeaderMapping):
            # column header can't be in data
            return False
        if isinstance(mapping, ColumnMapping):
            ref = mapping.reference
            if isinstance(ref, str):
                # find header reference
                if ref in self.header:
                    ref = self.header.index(ref)
            if index.column() == ref:
                if self._mapping.model.is_pivoted():
                    # only rows below pivoted rows
                    last_row = max(self._mapping.model.last_pivot_row(), self._mapping.read_start_row - 1)
                    if last_row is not None and index.row() > last_row:
                        return True
                elif index.row() >= self._mapping.read_start_row:
                    return True
        if isinstance(mapping, RowMapping):
            if index.row() == mapping.reference:
                if index.column() not in self.mapping_column_ref_int_list():
                    return True
        return False

    def mapping_column_ref_int_list(self):
        """Returns a list of column indexes that are not pivoted

        Returns:
            [List[int]] -- list of ints
        """
        if not self._mapping:
            return []
        non_pivoted_columns = self._mapping.model.non_pivoted_columns()
        skip_cols = self._mapping.model.skip_columns
        if skip_cols is None:
            skip_cols = []
        int_non_piv_cols = []
        for pc in set(non_pivoted_columns + skip_cols):
            if isinstance(pc, str):
                if pc in self.horizontal_header_labels():
                    pc = self.horizontal_header_labels().index(pc)
                else:
                    continue
            int_non_piv_cols.append(pc)

        return int_non_piv_cols


class MappingSpecModel(QAbstractTableModel):
    """
    A model to hold a Mapping specification.
    """

    row_or_column_type_recommendation_changed = Signal(int, object, object)
    """Emitted when a change in mapping prompts for change in column or row type."""
    multi_column_type_recommendation_changed = Signal(object, object)
    """Emitted when all but given columns should be of given type."""

    def __init__(self, model, table_name, parent=None):
        super().__init__(parent)
        self._display_names = []
        self._mappings = []
        self._model = None
        if model is not None:
            self.set_mapping(model)
        self._table_name = table_name

    @property
    def model(self):
        return self._model

    @property
    def skip_columns(self):
        if self._model.skip_columns is None:
            return []
        return list(self._model.skip_columns)

    @property
    def map_type(self):
        if self._model is None:
            return None
        return type(self._model)

    @property
    def last_pivot_row(self):
        last_row = self._model.last_pivot_row()
        if last_row is None:
            last_row = 0
        return last_row

    @property
    def dimension(self):
        if self._model is None:
            return 0
        return self._model.dimensions

    @property
    def import_objects(self):
        if self._model is None:
            return False
        return self._model.import_objects

    @property
    def parameter_type(self):
        return _TYPE_TO_DISPLAY_TYPE[type(self._model.parameters)]

    @property
    def is_pivoted(self):
        if self._model:
            return self._model.is_pivoted()
        return False

    @property
    def read_start_row(self):
        if self._model:
            return self._model.read_start_row
        return 0

    def set_read_start_row(self, row):
        if self._model:
            self._model.read_start_row = row
        self.dataChanged.emit(QModelIndex, QModelIndex, [])

    def set_import_objects(self, flag):
        self._model.import_objects = bool(flag)
        self.dataChanged.emit(QModelIndex, QModelIndex, [])

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
        if isinstance(mapping, type(self._model)):
            return
        self.beginResetModel()
        self._model = mapping
        self.update_display_table()
        self.dataChanged.emit(QModelIndex, QModelIndex, [])
        self.endResetModel()

    def set_dimension(self, dim):
        if self._model is None or self._model.has_fixed_dimensions():
            return
        self.beginResetModel()
        if len(self._model.objects) >= dim:
            self._model.object_classes = self._model.object_classes[:dim]
            self._model.objects = self._model.objects[:dim]
        else:
            self._model.object_classes = self._model.object_classes + [None]
            self._model.objects = self._model.objects + [None]
        self.update_display_table()
        self.dataChanged.emit(QModelIndex, QModelIndex, [])
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
        if self._model is None:
            self._model = new_class()
        elif not isinstance(self._model, new_class):
            self._model = new_class.from_instance(self._model)
        self.update_display_table()
        self.dataChanged.emit(QModelIndex, QModelIndex, [])
        self.endResetModel()

    def change_parameter_type(self, new_type):
        """
        Change parameter type
        """

        self.beginResetModel()
        if new_type == "None":
            self._model.parameters = None
        elif new_type == "Single value":
            self._model.parameters = ParameterValueMapping()
        elif new_type == "Array":
            self._model.parameters = ParameterArrayMapping()
        elif new_type == "Definition":
            self._model.parameters = ParameterDefinitionMapping()
        elif new_type == "Map":
            self._model.parameters = ParameterMapMapping()
        elif new_type == "Time series":
            self._model.parameters = ParameterTimeSeriesMapping()
        elif new_type == "Time pattern":
            self._model.parameters = ParameterTimePatternMapping()

        self.update_display_table()
        self.dataChanged.emit(QModelIndex, QModelIndex, [])
        self.endResetModel()

    def update_display_table(self):
        self._display_names = []
        self._mappings = []
        if not isinstance(self._model, ScenarioAlternativeMapping):
            self._mappings.append(self._model.name)
        if isinstance(self._model, RelationshipClassMapping):
            self._display_names.append("Relationship class names")
            if self._model.object_classes:
                self._display_names.extend(
                    [f"Object class names {i+1}" for i, oc in enumerate(self._model.object_classes)]
                )
                self._mappings.extend(list(self._model.object_classes))
            if self._model.objects:
                self._display_names.extend([f"Object names {i+1}" for i, oc in enumerate(self._model.objects)])
                self._mappings.extend(list(self._model.objects))
        elif isinstance(self._model, ObjectClassMapping):
            self._display_names.append("Object class names")
            self._display_names.append("Object names")
            self._mappings.append(self._model.objects)
        elif isinstance(self._model, ObjectGroupMapping):
            self._display_names.append("Object class names")
            self._display_names.append("Group names")
            self._mappings.append(self._model.groups)
            self._display_names.append("Member names")
            self._mappings.append(self._model.members)
        elif isinstance(self._model, AlternativeMapping):
            self._display_names.append("Alternative names")
        elif isinstance(self._model, ScenarioMapping):
            self._display_names.append("Scenario names")
            self._display_names.append("Scenario active flags")
            self._mappings.append(self._model.active)
        elif isinstance(self._model, ScenarioAlternativeMapping):
            self._display_names.append("Scenario names")
            self._display_names.append("Alternative names")
            self._display_names.append("Before Alternative names")
            self._mappings.append(self._model.scenario_name)
            self._mappings.append(self._model.alternative_name)
            self._mappings.append(self._model.before_alternative_name)
        if not self.mapping_has_parameters():
            return
        if isinstance(self._model.parameters, ParameterDefinitionMapping):
            self._display_names.append("Parameter names")
            self._mappings.append(self._model.parameters.name)
        if isinstance(self._model.parameters, ParameterValueMapping):
            self._display_names.append("Parameter values")
            self._mappings.append(self._model.parameters.value)
        if isinstance(self._model.parameters, ParameterMapMapping):
            for i, dimension in enumerate(self._model.parameters.extra_dimensions):
                self._display_names.append(f"Parameter index {i + 1}")
                self._mappings.append(dimension)
        if isinstance(self._model.parameters, ParameterTimeSeriesMapping):
            self._display_names.append("Parameter time index")
            self._mappings.append(self._model.parameters.extra_dimensions[0])
        if isinstance(self._model.parameters, ParameterTimePatternMapping):
            self._display_names.append("Parameter time pattern index")
            self._mappings.append(self._model.parameters.extra_dimensions[0])

    def get_map_type_display(self, mapping, name):
        if name == "Parameter values" and self._model.is_pivoted():
            mapping_type = "Pivoted"
        elif isinstance(mapping, RowMapping):
            if mapping.reference == -1:
                mapping_type = "Headers"
            else:
                mapping_type = "Row"
        else:
            mapping_type = _MAPTYPE_DISPLAY_NAME[type(mapping)]
        return mapping_type

    def get_map_value_display(self, mapping, name):
        if name == "Parameter values" and self._model.is_pivoted():
            mapping_value = "Pivoted values"
        elif isinstance(mapping, NoneMapping):
            mapping_value = ""
        elif isinstance(mapping, RowMapping) and mapping.reference == -1:
            mapping_value = "Headers"
        else:
            mapping_value = mapping.reference
        return mapping_value

    # pylint: disable=no-self-use
    def get_map_append_display(self, mapping, name):
        append_str = ""
        if isinstance(mapping, MappingBase):
            append_str = mapping.append_str
        return append_str

    # pylint: disable=no-self-use
    def get_map_prepend_display(self, mapping, name):
        prepend_str = ""
        if isinstance(mapping, MappingBase):
            prepend_str = mapping.prepend_str
        return prepend_str

    def data(self, index, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            name = self._display_names[index.row()]
            m = self._mappings[index.row()]
            func = [
                lambda: name,
                lambda: self.get_map_type_display(m, name),
                lambda: self.get_map_value_display(m, name),
                lambda: self.get_map_prepend_display(m, name),
                lambda: self.get_map_append_display(m, name),
            ]
            f = func[index.column()]
            return f()
        column = index.column()
        if role == Qt.BackgroundColorRole and column == 0:
            return self.data_color(self._display_names[index.row()])
        if column == 2:
            if role == Qt.BackgroundColorRole:
                if self._mapping_issues(index.row()):
                    return _ERROR_COLOR
                return None
            if role == Qt.ToolTipRole:
                issue = self._mapping_issues(index.row())
                if issue:
                    return issue
                return None

    @staticmethod
    def data_color(display_name):
        if display_name == "Relationship class names":
            return _MAPPING_COLORS["entity_class"]
        if "Object class" in display_name:
            return _MAPPING_COLORS["entity_class"]
        if "Object names" in display_name:
            return _MAPPING_COLORS["entity"]
        if display_name == "Member names":
            return _MAPPING_COLORS["entity"]
        if display_name == "Group names":
            return _MAPPING_COLORS["group"]
        if display_name == "Alternative names":
            return _MAPPING_COLORS["alternative"]
        if display_name == "Scenario names":
            return _MAPPING_COLORS["scenario"]
        if display_name == "Before Alternative names":
            return _MAPPING_COLORS["before_alternative"]
        if display_name == "Scenario active flags":
            return _MAPPING_COLORS["active"]
        if display_name == "Parameter names":
            return _MAPPING_COLORS["parameter_name"]
        if display_name in ("Parameter time index", "Parameter time pattern index") or display_name.startswith(
            "Parameter index"
        ):
            return _MAPPING_COLORS["parameter_extra_dimension"]
        if display_name == "Parameter values":
            return _MAPPING_COLORS["parameter_value"]

    def _mapping_issues(self, row):
        """Returns a message string if given row contains issues, or an empty string if everything is OK."""
        parameter_name_row = None
        if isinstance(self._model, EntityClassMapping):
            if row == 0:
                return self._model.class_names_issues()
        if isinstance(self._model, ObjectClassMapping):
            if row == 1:
                return self._model.object_names_issues()
            parameter_name_row = 2
        elif isinstance(self._model, RelationshipClassMapping):
            dimensions = len(self._model.object_classes)
            parameter_name_row = 2 * dimensions + 1
            if 1 <= row < parameter_name_row:
                display_name = self._display_names[row]
                mapping_name, _, mapping_number = display_name.rpartition(" ")
                index = int(mapping_number) - 1
                if mapping_name == "Object class names":
                    return self._model.object_class_names_issues(index)
                return self._model.object_names_issues(index)
        elif isinstance(self._model, ObjectGroupMapping):
            if row == 1:
                return self._model.group_names_issues()
            if row == 2:
                return self._model.member_names_issues()
            parameter_name_row = 3
        elif isinstance(self._model, AlternativeMapping):
            if row == 1:
                return self._model.alternative_names_issues()
        elif isinstance(self._model, ScenarioMapping):
            if row == 1:
                return self._model.scenario_names_issues()
        elif isinstance(self._model, ScenarioAlternativeMapping):
            if row == 1:
                return self._model.scenario_names_issues()
        if parameter_name_row is None:
            return ""
        if row == parameter_name_row:
            return self._model.parameters.names_issues()
        if row == parameter_name_row + 1:
            return self._model.parameters.values_issues(self._model.is_pivoted())
        if row >= parameter_name_row + 2:
            index = row - (parameter_name_row + 2)
            return self._model.parameters.indexes_issues(index)
        return ""

    def rowCount(self, index=None):
        if not self._model:
            return 0
        return len(self._display_names)

    def columnCount(self, index=None):
        if not self._model:
            return 0
        return 3

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ["Target", "Source type", "Source ref.", "Prepend string", "Append string"][section]

    def flags(self, index):
        editable = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        non_editable = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0:
            return non_editable
        mapping = self._mappings[index.row()]

        if self._model.is_pivoted():
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
        name = self._display_names[index.row()]
        if index.column() == 1:
            return self.set_type(name, value)
        if index.column() == 2:
            if self.set_value(index.row(), name, value):
                if name in self._display_names:
                    self.dataChanged.emit(index, index)
                return True
            return False
        if index.column() == 3:
            return self.set_prepend_str(name, value)
        if index.column() == 4:
            return self.set_append_str(name, value)
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
        return self.set_mapping_from_name(name, value)

    def set_value(self, row, name, value):
        """
        Sets the reference for given mapping.

        Args:
            row (int): row index
            name (str): name of the mapping
            value (str): a new value

        Returns:
            bool: True if the reference was modified successfully, False otherwise.
        """
        mapping = self.get_mapping_from_name(name)
        if isinstance(mapping, NoneMapping):
            # create new mapping
            if value.isdigit():
                mapping = ColumnMapping(reference=int(value))
            elif value:
                mapping = ConstantMapping(reference=value)
            else:
                return False
            index = self.index(row, 1)
            self.dataChanged.emit(index, index)
        try:
            mapping.reference = value
        except ValueError:
            return False
        return self.set_mapping_from_name(name, mapping)

    def set_append_str(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if mapping:
            if isinstance(mapping, MappingBase):
                if value == "":
                    value = None
                mapping.append_str = value
                return self.set_mapping_from_name(name, mapping)
        return False

    def set_prepend_str(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if mapping:
            if isinstance(mapping, MappingBase):
                if value == "":
                    value = None
                mapping.prepend_str = value
                return self.set_mapping_from_name(name, mapping)
        return False

    def get_mapping_from_name(self, name):
        if not self._model:
            return None
        if name in ("Relationship class names", "Object class names"):
            return self._model.name
        if name in ("Alternative names", "Scenario names") and not isinstance(self._model, ScenarioAlternativeMapping):
            return self._model.name
        if name == "Scenario names":
            return self._model.scenario_name
        if name == "Alternative names":
            return self._model.alternative_name
        if name == "Before Alternative names":
            return self._model.before_alternative_name
        if name == "Scenario active flags":
            return self._model.active
        if name == "Group names":
            return self._model.groups
        if name == "Member names":
            return self._model.members
        if name == "Object names":
            return self._model.objects
        if name.startswith("Object class"):
            # Not to be confused with name == 'Object class names'.
            return self._model.object_classes[_name_index(name)]
        if name.startswith("Object"):
            # Not to be confused with name == 'Object class names' or name == 'Object class X'.
            return self._model.objects[_name_index(name)]
        if name == "Parameter names":
            return self._model.parameters.name
        if name == "Parameter values":
            return self._model.parameters.value
        if name in ("Parameter time index", "Parameter time pattern index"):
            return self._model.parameters.extra_dimensions[0]
        if name.startswith("Parameter index"):
            return self._model.parameters.extra_dimensions[_name_index(name)]
        return None

    def set_mapping_from_name(self, name, mapping):
        if name in ("Relationship class names", "Object class names"):
            self._model.name = mapping
            self._recommend_string_type(mapping)
        elif name in ("Alternative names", "Scenario names") and not isinstance(
            self._model, ScenarioAlternativeMapping
        ):
            self._model.name = mapping
            self._recommend_string_type(mapping)
        elif name == "Scenario names":
            self._model.scenario_name = mapping
            self._recommend_string_type(mapping)
        elif name == "Alternative names":
            self._model.alternative_name = mapping
            self._recommend_string_type(mapping)
        elif name == "Before Alternative names":
            self._model.before_alternative_name = mapping
            self._recommend_string_type(mapping)
        elif name == "Scenario active flags":
            self._model.active = mapping
            self._recommend_string_type(mapping)
        elif name == "Object names":
            self._model.objects = mapping
            self._recommend_string_type(mapping)
        elif name == "Group names":
            self._model.groups = mapping
            self._recommend_string_type(mapping)
        elif name == "Member names":
            self._model.members = mapping
            self._recommend_string_type(mapping)
        elif "Object class " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                self._model.object_classes[index[0]] = mapping
                self._recommend_string_type(mapping)
        elif "Object " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                self._model.objects[index[0]] = mapping
                self._recommend_string_type(mapping)
        elif name == "Parameter names":
            self._model.parameters.name = mapping
            self._recommend_string_type(mapping)
        elif name == "Parameter values":
            self._model.parameters.value = mapping
            self._recommend_parameter_value_mapping_reference_type_change(mapping)
        elif name in ("Parameter time index", "Parameter time pattern index"):
            self._model.parameters.extra_dimensions = [mapping]
            if name == "Parameter time index":
                self._recommend_datetime_type(mapping)
            if (
                isinstance(mapping, RowMapping)
                and self._model.is_pivoted()
                and isinstance(self._model.parameters.value, NoneMapping)
            ):
                non_pivoted_columns = self._model.non_pivoted_columns()
                self.multi_column_type_recommendation_changed.emit(non_pivoted_columns, FloatConvertSpec())
        elif name.startswith("Parameter index"):
            self._model.parameters.extra_dimensions[_name_index(name)] = mapping
            self._recommend_string_type(mapping)
        else:
            return False
        self.update_display_table()
        if name in self._display_names:
            self.dataChanged.emit(QModelIndex(), QModelIndex(), [])
        return True

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
                non_pivoted_columns = self._model.non_pivoted_columns()
                self.multi_column_type_recommendation_changed.emit(non_pivoted_columns, FloatConvertSpec())

    def set_skip_columns(self, columns=None):
        if columns is None:
            columns = []
        self._model.skip_columns = list(set(columns))
        self.dataChanged.emit(0, 0, [])

    @Slot(bool)
    def set_time_series_repeat(self, repeat):
        """Toggles the repeat flag in the parameter's options."""
        if self._model is None or not isinstance(self._model.parameters, ParameterTimeSeriesMapping):
            return
        self._model.parameters.options.repeat = repeat
        self.dataChanged.emit(0, 0, [])

    @Slot(int)
    def set_map_dimensions(self, dimensions):
        if self._model is None or not isinstance(self._model.parameters, ParameterMapMapping):
            return
        previous_dimensions = len(self._model.parameters.extra_dimensions)
        if dimensions == previous_dimensions:
            return
        self._model.parameters.set_number_of_extra_dimensions(dimensions)
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
            self._mappings += self._model.parameters.extra_dimensions[previous_dimensions:]
            self.endInsertRows()
        else:
            first = first_dimension_row + dimensions
            last = first_dimension_row + previous_dimensions - 1
            self.beginRemoveRows(QModelIndex(), first, last)
            self._display_names = self._display_names[:first]
            self._mappings = self._mappings[:first]
            self.endRemoveRows()

    def model_parameters(self):
        """Returns the mapping's parameters."""
        if not isinstance(self._model, EntityClassMapping):
            return None
        return self._model.parameters if self._model is not None else None

    def mapping_has_parameters(self):
        """Returns True if current mapping may have parameters, False otherwise"""
        # This method becomes more useful once we add support for alternatives and scenarios here.
        return not isinstance(self._model, (AlternativeMapping, ScenarioMapping, ScenarioAlternativeMapping))


class MappingListModel(QAbstractListModel):
    """
    A model to hold a list of Mappings.
    """

    def __init__(self, mapping_list, table_name, parent=None):
        super().__init__(parent)
        self._qmappings = []
        self._names = []
        self._counter = 1
        self._table_name = table_name
        self.set_model(mapping_list)

    def set_model(self, model):
        self.beginResetModel()
        self._names = []
        self._qmappings = []
        for m in model:
            self._names.append("Mapping " + str(self._counter))
            self._qmappings.append(MappingSpecModel(m, self._table_name))
            self._counter += 1
        self.endResetModel()

    def get_mappings(self):
        return [m._model for m in self._qmappings]

    def rowCount(self, index=None):
        if not self._qmappings:
            return 0
        return len(self._qmappings)

    def data_mapping(self, index):
        if self._qmappings and index.row() < len(self._qmappings):
            return self._qmappings[index.row()]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return
        if self._qmappings and role == Qt.DisplayRole and index.row() < self.rowCount():
            return self._names[index.row()]

    def add_mapping(self):
        self.beginInsertRows(self.index(self.rowCount(), 0), self.rowCount(), self.rowCount())
        m = ObjectClassMapping()
        self._qmappings.append(MappingSpecModel(m, self._table_name))
        self._names.append("Mapping " + str(self._counter))
        self._counter += 1
        self.endInsertRows()

    def remove_mapping(self, row):
        if self._qmappings and row < len(self._qmappings):
            self.beginRemoveRows(self.index(row, 0), row, row)
            self._qmappings.pop(row)
            self._names.pop(row)
            self.endRemoveRows()

    def check_mapping_validity(self):
        """
        Checks if there are any issues with the mappings.

        Returns:
             dict: a map from mapping name to discovered issue; contains only mappings that have issues
        """
        issues = dict()
        for name, mapping in zip(self._names, self._qmappings):
            issue = mapping.check_mapping_validity()
            if issue:
                issues[name] = issue
        return issues


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
