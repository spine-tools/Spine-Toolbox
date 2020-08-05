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
Contains the source data table model.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""
from PySide2.QtCore import QModelIndex, Qt, Signal, Slot
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
    ParameterArrayMapping,
    MappingBase,
    ColumnHeaderMapping,
    ColumnMapping,
    RowMapping,
    ParameterValueFormatError,
    mapping_non_pivoted_columns,
)
from spinetoolbox.mvcmodels.minimal_table_model import MinimalTableModel
from spinetoolbox.spine_io.type_conversion import ConvertSpec
from .mapping_specification_model import MappingSpecificationModel
from ..mapping_colors import ERROR_COLOR, MAPPING_COLORS


class SourceDataTableModel(MinimalTableModel):
    """A model for import mapping specification.

    Highlights columns, rows, and so on, depending on Mapping specification.
    """

    column_types_updated = Signal()
    row_types_updated = Signal()
    mapping_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self._mapping_specification = None
        self._data_changed_signal = None
        self._read_start_row_changed_signal = None
        self._row_or_column_type_recommendation_changed_signal = None
        self._multi_column_type_recommendation_changed_signal = None
        self._column_types = {}
        self._row_types = {}
        self._column_type_errors = {}
        self._row_type_errors = {}

    def mapping_specification(self):
        return self._mapping_specification

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
            mapping (MappingSpecificationModel): mapping model
        """
        if not mapping:
            return
        if not isinstance(mapping, MappingSpecificationModel):
            raise TypeError(f"mapping must be instance of 'MappingSpecificationModel', instead got: '{type(mapping).__name__}'")
        if self._mapping_specification is not None:
            if self._data_changed_signal is not None:
                self._mapping_specification.dataChanged.disconnect(self._mapping_data_changed)
                self._data_changed_signal = None
            if self._read_start_row_changed_signal is not None:
                self._mapping_specification.mapping_read_start_row_changed.disconnect(self._mapping_data_changed)
                self._read_start_row_changed_signal = None
            if self._row_or_column_type_recommendation_changed_signal is not None:
                self._mapping_specification.row_or_column_type_recommendation_changed.disconnect(self.set_type)
                self._row_or_column_type_recommendation_changed_signal = None
            if self._multi_column_type_recommendation_changed_signal is not None:
                self._mapping_specification.multi_column_type_recommendation_changed.disconnect(
                    self.set_all_column_types
                )
                self._multi_column_type_recommendation_changed_signal = None
        self._mapping_specification = mapping
        self._data_changed_signal = self._mapping_specification.dataChanged.connect(self._mapping_data_changed)
        self._read_start_row_changed_signal = self._mapping_specification.mapping_read_start_row_changed.connect(self._mapping_data_changed)
        self._row_or_column_type_recommendation_changed_signal = self._mapping_specification.row_or_column_type_recommendation_changed.connect(
            self.set_type
        )
        self._multi_column_type_recommendation_changed_signal = self._mapping_specification.multi_column_type_recommendation_changed.connect(
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

    @Slot()
    def _mapping_data_changed(self):
        self.update_colors()
        self.mapping_changed.emit()

    def update_colors(self):
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundColorRole])

    def data_error(self, index, role=Qt.DisplayRole, orientation=Qt.Horizontal):
        if role == Qt.DisplayRole:
            return "Error"
        if role == Qt.ToolTipRole:
            type_name = self.get_type(index.column(), orientation)
            return f'Could not parse value: "{self._main_data[index.row()][index.column()]}" as a {type_name}'
        if role == Qt.BackgroundColorRole:
            return ERROR_COLOR

    def data(self, index, role=Qt.DisplayRole):
        if self._mapping_specification:
            last_pivoted_row = self._mapping_specification.last_pivot_row
            read_from_row = self._mapping_specification.read_start_row
        else:
            last_pivoted_row = -1
            read_from_row = 0

        if index.row() > max(last_pivoted_row, read_from_row - 1):
            if (index.row(), index.column()) in self._column_type_errors:
                return self.data_error(index, role)

        if index.row() <= last_pivoted_row:
            if (
                index.column()
                not in mapping_non_pivoted_columns(self._mapping_specification.mapping, self.columnCount(), self.header)
                and index.column() not in self._mapping_specification.skip_columns
            ):
                if (index.row(), index.column()) in self._row_type_errors:
                    return self.data_error(index, role, orientation=Qt.Vertical)

        if role == Qt.BackgroundColorRole and self._mapping_specification:
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
        mapping = self._mapping_specification.mapping
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
                        return MAPPING_COLORS["parameter_value"]
                elif self.index_in_mapping(mapping.parameters.value, index):
                    return MAPPING_COLORS["parameter_value"]
            if isinstance(mapping.parameters, ParameterArrayMapping) and mapping.parameters.extra_dimensions:
                # parameter extra dimensions color
                for ed in mapping.parameters.extra_dimensions:
                    if self.index_in_mapping(ed, index):
                        return MAPPING_COLORS["parameter_extra_dimension"]
            if isinstance(mapping.parameters, ParameterDefinitionMapping) and self.index_in_mapping(
                mapping.parameters.name, index
            ):
                # parameter name colors
                return MAPPING_COLORS["parameter_name"]
        if not isinstance(
            mapping, (AlternativeMapping, ScenarioMapping, ScenarioAlternativeMapping)
        ) and self.index_in_mapping(mapping.name, index):
            return MAPPING_COLORS["entity_class"]
        classes = []
        objects = []
        if isinstance(mapping, ObjectClassMapping):
            objects = [mapping.objects]
        elif isinstance(mapping, ObjectGroupMapping):
            if self.index_in_mapping(mapping.groups, index):
                return MAPPING_COLORS["group"]
            objects = [mapping.members]
        elif isinstance(mapping, RelationshipClassMapping):
            objects = mapping.objects
            classes = mapping.object_classes
        elif isinstance(mapping, AlternativeMapping):
            if self.index_in_mapping(mapping.name, index):
                return MAPPING_COLORS["alternative"]
        elif isinstance(mapping, ScenarioMapping):
            if self.index_in_mapping(mapping.name, index):
                return MAPPING_COLORS["scenario"]
            if self.index_in_mapping(mapping.active, index):
                return MAPPING_COLORS["active"]
        elif isinstance(mapping, ScenarioAlternativeMapping):
            if self.index_in_mapping(mapping.scenario_name, index):
                return MAPPING_COLORS["scenario"]
            if self.index_in_mapping(mapping.alternative_name, index):
                return MAPPING_COLORS["alternative"]
            if self.index_in_mapping(mapping.before_alternative_name, index):
                return MAPPING_COLORS["before_alternative"]
        for o in objects:
            # object colors
            if self.index_in_mapping(o, index):
                return MAPPING_COLORS["entity"]
        for c in classes:
            # object colors
            if self.index_in_mapping(c, index):
                return MAPPING_COLORS["entity_class"]

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
                if self._mapping_specification.mapping.is_pivoted():
                    # only rows below pivoted rows
                    last_row = max(
                        self._mapping_specification.mapping.last_pivot_row(),
                        self._mapping_specification.read_start_row - 1,
                    )
                    if last_row is not None and index.row() > last_row:
                        return True
                elif index.row() >= self._mapping_specification.read_start_row:
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
        if not self._mapping_specification:
            return []
        non_pivoted_columns = self._mapping_specification.mapping.non_pivoted_columns()
        skip_cols = self._mapping_specification.mapping.skip_columns
        if skip_cols is None:
            skip_cols = []
        int_non_piv_cols = []
        for pc in set(non_pivoted_columns + skip_cols):
            if isinstance(pc, str):
                try:
                    pc = self.horizontal_header_labels().index(pc)
                except ValueError:
                    continue
            int_non_piv_cols.append(pc)

        return int_non_piv_cols
