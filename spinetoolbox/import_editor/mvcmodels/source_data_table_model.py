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
from PySide2.QtCore import Qt, Signal, Slot
from spinedb_api import (
    EntityClassMapping,
    ParameterValueMapping,
    SingleMappingBase,
    ColumnHeaderMapping,
    ColumnMapping,
    RowMapping,
    ParameterValueFormatError,
    mapping_non_pivoted_columns,
)
from spinetoolbox.mvcmodels.minimal_table_model import MinimalTableModel
from spine_engine.spine_io.type_conversion import ConvertSpec
from ..mapping_colors import ERROR_COLOR


class SourceDataTableModel(MinimalTableModel):
    """A model for import mapping specification.

    Highlights columns, rows, and so on, depending on Mapping specification.
    """

    column_types_updated = Signal()
    row_types_updated = Signal()
    mapping_changed = Signal()
    about_to_undo = Signal(str)
    """Emitted when an undo/redo command is going to be executed."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self._mapping_specification = None
        self._column_types = {}
        self._row_types = {}
        self._column_type_errors = {}
        self._row_type_errors = {}
        self._converted_data = {}

    def mapping_specification(self):
        return self._mapping_specification

    def clear(self):
        self._column_type_errors = {}
        self._row_type_errors = {}
        self._column_types = {}
        self._row_types = {}
        self._converted_data = {}
        super().clear()

    def reset_model(self, main_data=None):
        self._column_type_errors = {}
        self._row_type_errors = {}
        self._column_types = {}
        self._row_types = {}
        self._converted_data = {}
        super().reset_model(main_data)

    def set_mapping(self, mapping):
        """Set mapping to display colors from

        Args:
            mapping (MappingSpecificationModel): mapping model
        """
        if self._mapping_specification is not None:
            self._mapping_specification.dataChanged.disconnect(self._mapping_data_changed)
            self._mapping_specification.mapping_read_start_row_changed.disconnect(self._mapping_data_changed)
            self._mapping_specification.row_or_column_type_recommendation_changed.disconnect(self.set_type)
            self._mapping_specification.multi_column_type_recommendation_changed.disconnect(self.set_all_column_types)
        self._mapping_specification = mapping
        if self._mapping_specification is not None:
            self._mapping_specification.dataChanged.connect(self._mapping_data_changed)
            self._mapping_specification.modelReset.connect(self._mapping_data_changed)
            self._mapping_specification.mapping_read_start_row_changed.connect(self._mapping_data_changed)
            self._mapping_specification.row_or_column_type_recommendation_changed.connect(self.set_type)
            self._mapping_specification.multi_column_type_recommendation_changed.connect(self.set_all_column_types)
        self._mapping_data_changed()

    def validate(self, section, orientation=Qt.Horizontal):
        type_class = self.get_type(section, orientation)
        if type_class is None:
            return
        converter = type_class.convert_function()
        if orientation == Qt.Horizontal:
            for row in range(self.rowCount()):
                self._column_type_errors.pop((row, section), None)
                data = self.index(row, section).data(Qt.EditRole)
                if isinstance(data, str) and not data:
                    data = None
                if data is not None:
                    try:
                        self._converted_data[row, section] = converter(data)
                    except (ValueError, ParameterValueFormatError) as e:
                        self._converted_data.pop((row, section), None)
                        self._column_type_errors[row, section] = e
            top_left = self.index(0, section)
            bottom_right = self.index(self.rowCount() - 1, section)
        else:
            for column in range(self.columnCount()):
                self._row_type_errors.pop((section, column), None)
                data = self.index(section, column).data(Qt.EditRole)
                if isinstance(data, str) and not data:
                    data = None
                if data is not None:
                    try:
                        self._converted_data[section, column] = converter(data)
                    except (ValueError, ParameterValueFormatError) as e:
                        self._converted_data.pop((section, column), None)
                        self._row_type_errors[section, column] = e
            top_left = self.index(section, 0)
            bottom_right = self.index(section, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right)

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
        self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole])
        self.headerDataChanged.emit(Qt.Horizontal, 0, self.columnCount() - 1)

    def data_error(self, error, index, role=Qt.DisplayRole, orientation=Qt.Horizontal):
        if role == Qt.ToolTipRole:
            type_display_name = self.get_type(index.column(), orientation).DISPLAY_NAME
            value = self._main_data[index.row()][index.column()]
            return f'<p>Could not parse value: "{value}" as a {type_display_name}: {error}</p>'
        if role == Qt.BackgroundRole:
            return ERROR_COLOR

    def data(self, index, role=Qt.DisplayRole):
        if self._mapping_specification:
            last_pivoted_row = self._mapping_specification.last_pivot_row
            read_from_row = self._mapping_specification.read_start_row
        else:
            last_pivoted_row = -1
            read_from_row = 0
        if role in (Qt.ToolTipRole, Qt.BackgroundRole):
            if index.row() > max(last_pivoted_row, read_from_row - 1):
                error = self._column_type_errors.get((index.row(), index.column()))
                if error is not None:
                    return self.data_error(error, index, role, orientation=Qt.Horizontal)

            if index.row() <= last_pivoted_row:
                if (
                    index.column()
                    not in mapping_non_pivoted_columns(
                        self._mapping_specification.mapping, self.columnCount(), self.header
                    )
                    and index.column() not in self._mapping_specification.skip_columns
                ):
                    error = self._row_type_errors.get((index.row(), index.column()))
                    if error is not None:
                        return self.data_error(error, index, role, orientation=Qt.Vertical)

        if role == Qt.BackgroundRole and self._mapping_specification:
            return self.data_color(index)
        if role == Qt.DisplayRole:
            converted_data = self._converted_data.get((index.row(), index.column()))
            if converted_data is not None:
                return str(converted_data)
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
        if self.index_below_last_pivot_row(mapping, index):
            return self._mapping_specification.data_color("Parameter values")
        for k, component_mapping in enumerate(self._mapping_specification._component_mappings):
            if self.index_in_mapping(component_mapping, index):
                return self._mapping_specification._colors[k]
        return None

    def index_below_last_pivot_row(self, mapping, index):
        if not isinstance(mapping, EntityClassMapping):
            return False
        if not isinstance(mapping.parameters, ParameterValueMapping):
            return False
        if not mapping.is_pivoted():
            return False
        last_row = max(mapping.last_pivot_row(), mapping.read_start_row - 1)
        return (
            last_row is not None and index.row() > last_row and index.column() not in self.mapping_column_ref_int_list()
        )

    def index_in_mapping(self, mapping, index):
        """
        Checks if index is in mapping

        Args:
            mapping (SingleMappingBase): mapping
            index (QModelIndex): index

        Returns:
            bool: True if mapping is in index
        """
        if not isinstance(mapping, SingleMappingBase):
            return False
        if isinstance(mapping, ColumnHeaderMapping):
            # column header can't be in data
            return False
        if isinstance(mapping, ColumnMapping):
            if index.column() == self._reference_from_header(mapping.reference):
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

    def _reference_from_header(self, ref):
        if isinstance(ref, str) and ref in self.header:
            return self.header.index(ref)
        return ref

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal or role != Qt.BackgroundRole:
            return super().headerData(section, orientation, role)
        if self._mapping_specification is None:
            return super().headerData(section, orientation, role)
        for k, component_mapping in enumerate(self._mapping_specification._component_mappings):
            if self.section_in_mapping(component_mapping, section):
                return self._mapping_specification._colors[k]

    def section_in_mapping(self, mapping, section):
        if isinstance(mapping, ColumnHeaderMapping):
            return section == self._reference_from_header(mapping.reference)
        if isinstance(mapping, RowMapping):
            return mapping.reference == -1
        return False
