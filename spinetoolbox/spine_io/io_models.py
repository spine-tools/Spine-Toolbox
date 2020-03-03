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
from collections import namedtuple, Iterable
from six import unichr

from spinedb_api import (
    ObjectClassMapping,
    RelationshipClassMapping,
    ParameterDefinitionMapping,
    ParameterValueMapping,
    ParameterMapMapping,
    ParameterTimeSeriesMapping,
    ParameterTimePatternMapping,
    ParameterListMapping,
    MappingBase,
    NoneMapping,
    ConstantMapping,
    ColumnHeaderMapping,
    ColumnMapping,
    RowMapping,
    ParameterValueFormatError,
    mapping_non_pivoted_columns,
)
from PySide2.QtWidgets import QHeaderView, QMenu, QAction, QTableView, QToolButton
from PySide2.QtCore import QModelIndex, Qt, QAbstractTableModel, QAbstractListModel, Signal, Slot
from PySide2.QtGui import QColor, QFont
from ..mvcmodels.minimal_table_model import MinimalTableModel
from .io_api import TYPE_STRING_TO_CLASS
from .type_conversion import value_to_convert_spec, NewIntegerSequenceDateTimeConvertSpecDialog, ConvertSpec

Margin = namedtuple("Margin", ("left", "right", "top", "bottom"))


_MAPPING_COLORS = {
    "entity": QColor(223, 194, 125),
    "parameter value": QColor(1, 133, 113),
    "parameter extra dimension": QColor(128, 205, 193),
    "parameter name": QColor(128, 205, 193),
    "entity class": QColor(166, 97, 26),
}
_ERROR_COLOR = QColor(Qt.red)


_COLUMN_TYPE_ROLE = Qt.UserRole
_COLUMN_NUMBER_ROLE = Qt.UserRole + 1
_ALLOWED_TYPES = list(sorted(TYPE_STRING_TO_CLASS.keys()))
_ALLOWED_TYPES.append("integer sequence datetime")

_TYPE_TO_FONT_AWESOME_ICON = {
    "integer sequence datetime": unichr(int('f073', 16)),
    "string": unichr(int('f031', 16)),
    "datetime": unichr(int('f073', 16)),
    "duration": unichr(int('f017', 16)),
    "float": unichr(int('f534', 16)),
}

_MAPTYPE_DISPLAY_NAME = {
    NoneMapping: "None",
    ConstantMapping: "Constant",
    ColumnMapping: "Column",
    ColumnHeaderMapping: "Column Header",
    RowMapping: "Row",
}

_DISPLAY_TYPE_TO_TYPE = {
    "Single value": ParameterValueMapping,
    "List": ParameterListMapping,
    "Map": ParameterMapMapping,
    "Time series": ParameterTimeSeriesMapping,
    "Time pattern": ParameterTimePatternMapping,
    "Definition": ParameterDefinitionMapping,
    "None": NoneMapping,
}

_TYPE_TO_DISPLAY_TYPE = {value: key for key, value in _DISPLAY_TYPE_TO_TYPE.items()}


class MappingPreviewModel(MinimalTableModel):
    """A model for highlighting columns, rows, and so on, depending on Mapping specification.
    Used by ImportPreviewWidget.
    """

    columnTypesUpdated = Signal()
    rowTypesUpdated = Signal()
    mappingChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self._mapping = None
        self._data_changed_signal = None
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

        Arguments:
            mapping {MappingSpecModel} -- mapping model
        """
        if not mapping:
            return
        if not isinstance(mapping, MappingSpecModel):
            raise TypeError(f"mapping must be instance of 'MappingSpecModel', instead got: '{type(mapping).__name__}'")
        if self._data_changed_signal is not None and self._mapping:
            self._mapping.dataChanged.disconnect(self._mapping_data_changed)
            self._data_changed_signal = None
        self._mapping = mapping
        if self._mapping:
            self._data_changed_signal = self._mapping.dataChanged.connect(self._mapping_data_changed)
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

    def set_type(self, section, section_type, orientation=Qt.Horizontal):
        if orientation == Qt.Horizontal:
            count = self.columnCount()
            emit_signal = self.columnTypesUpdated
            type_dict = self._column_types
        else:
            count = self.rowCount()
            emit_signal = self.rowTypesUpdated
            type_dict = self._row_types
        if not isinstance(section_type, ConvertSpec):
            raise TypeError(
                f"section_type must be a instance of ConvertSpec, instead got {type(section_type).__name__}"
            )
        if section < 0 or section > count:
            raise ValueError(f"section must be within model data")
        type_dict[section] = section_type
        emit_signal.emit()
        self.validate(section, orientation)

    def _mapping_data_changed(self):
        self.update_colors()
        self.mappingChanged.emit()

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
                index.column() not in mapping_non_pivoted_columns(self._mapping._model, self.columnCount(), self.header)
                and index.column() not in self._mapping.skip_columns
            ):
                if (index.row(), index.column()) in self._row_type_errors:
                    return self.data_error(index, role, orientation=Qt.Vertical)

        if role == Qt.BackgroundColorRole and self._mapping:
            return self.data_color(index)
        return super().data(index, role)

    def data_color(self, index):
        """returns background color for index depending on mapping

        Arguments:
            index {PySide2.QtCore.QModelIndex} -- index

        Returns:
            [QColor] -- QColor of index
        """
        mapping = self._mapping._model
        if isinstance(mapping.parameters, ParameterValueMapping):
            # parameter values color
            if mapping.is_pivoted():
                last_row = max(mapping.last_pivot_row(), mapping.read_start_row - 1)
                if (
                    last_row is not None
                    and index.row() > last_row
                    and index.column() not in self.mapping_column_ref_int_list()
                ):
                    return _MAPPING_COLORS["parameter value"]
            elif self.index_in_mapping(mapping.parameters.value, index):
                return _MAPPING_COLORS["parameter value"]
        if isinstance(mapping.parameters, ParameterListMapping) and mapping.parameters.extra_dimensions:
            # parameter extra dimensions color
            for ed in mapping.parameters.extra_dimensions:
                if self.index_in_mapping(ed, index):
                    return _MAPPING_COLORS["parameter extra dimension"]
        if isinstance(mapping.parameters, ParameterDefinitionMapping) and self.index_in_mapping(
            mapping.parameters.name, index
        ):
            # parameter name colors
            return _MAPPING_COLORS["parameter name"]
        if self.index_in_mapping(mapping.name, index):
            # class name color
            return _MAPPING_COLORS["entity class"]
        objects = []
        classes = []
        if isinstance(mapping, ObjectClassMapping):
            objects = [mapping.objects]
        else:
            if mapping.objects:
                objects = mapping.objects
            if mapping.object_classes:
                classes = mapping.object_classes
        for o in objects:
            # object colors
            if self.index_in_mapping(o, index):
                return _MAPPING_COLORS["entity"]
        for c in classes:
            # object colors
            if self.index_in_mapping(c, index):
                return _MAPPING_COLORS["entity class"]

    def index_in_mapping(self, mapping, index):
        """Checks if index is in mapping

        Arguments:
            mapping {Mapping} -- mapping
            index {QModelIndex} -- index

        Returns:
            [bool] -- returns True if mapping is in index
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
                if self._mapping._model.is_pivoted():
                    # only rows below pivoted rows
                    last_row = max(self._mapping._model.last_pivot_row(), self._mapping.read_start_row - 1)
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
        non_pivoted_columns = self._mapping._model.non_pivoted_columns()
        skip_cols = self._mapping._model.skip_columns
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

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self._display_names = []
        self._mappings = []
        self._model = None
        if model is not None:
            self.set_mapping(model)

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
        if isinstance(self._model, ObjectClassMapping):
            return 1
        return len(self._model.objects)

    @property
    def import_objects(self):
        if self._model is None:
            return False
        if isinstance(self._model, RelationshipClassMapping):
            return self._model.import_objects
        return True

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
        if not isinstance(mapping, (RelationshipClassMapping, ObjectClassMapping)):
            raise TypeError(
                f"mapping must be of type: RelationshipClassMapping, ObjectClassMapping instead got {type(mapping)}"
            )
        if isinstance(mapping, type(self._model)):
            return
        self.beginResetModel()
        self._model = mapping
        if isinstance(self._model, RelationshipClassMapping):
            if self._model.objects is None:
                self._model.objects = [None]
                self._model.object_classes = [None]
        self.update_display_table()
        self.dataChanged.emit(QModelIndex, QModelIndex, [])
        self.endResetModel()

    def set_dimension(self, dim):
        if self._model is None or isinstance(self._model, ObjectClassMapping):
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
        if new_class == "Object":
            new_class = ObjectClassMapping
        else:
            new_class = RelationshipClassMapping
        if self._model is None:
            self._model = new_class()
        elif not isinstance(self._model, new_class):
            parameters = self._model.parameters
            if new_class == RelationshipClassMapping:
                # convert object mapping to relationship mapping
                obj = [self._model.objects]
                object_class = [self._model.name]
                self._model = RelationshipClassMapping(
                    name=None, object_classes=object_class, objects=obj, parameters=parameters
                )
            else:
                # convert relationship mapping to object mapping
                self._model = ObjectClassMapping(
                    name=self._model.object_classes[0], objects=self._model.objects[0], parameters=parameters
                )

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
        elif new_type == "List":
            self._model.parameters = ParameterListMapping()
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
        display_name = []
        mappings = []
        mappings.append(self._model.name)
        if isinstance(self._model, RelationshipClassMapping):
            display_name.append("Relationship class names")
            if self._model.object_classes:
                display_name.extend([f"Object class names {i+1}" for i, oc in enumerate(self._model.object_classes)])
                mappings.extend(list(self._model.object_classes))
            if self._model.objects:
                display_name.extend([f"Object names {i+1}" for i, oc in enumerate(self._model.objects)])
                mappings.extend(list(self._model.objects))
        if isinstance(self._model, ObjectClassMapping):
            display_name.append("Object class names")
            display_name.append("Object names")
            mappings.append(self._model.objects)
        if isinstance(self._model.parameters, ParameterDefinitionMapping):
            display_name.append("Parameter names")
            mappings.append(self._model.parameters.name)
        if isinstance(self._model.parameters, ParameterValueMapping):
            display_name.append("Parameter values")
            mappings.append(self._model.parameters.value)
        if isinstance(self._model.parameters, ParameterMapMapping):
            display_name.append("Parameter map index")
            mappings.append(self._model.parameters.extra_dimensions[0])
        if isinstance(self._model.parameters, ParameterTimeSeriesMapping):
            display_name.append("Parameter time index")
            mappings.append(self._model.parameters.extra_dimensions[0])
        if isinstance(self._model.parameters, ParameterTimePatternMapping):
            display_name.append("Parameter time pattern index")
            mappings.append(self._model.parameters.extra_dimensions[0])
        self._display_names = display_name
        self._mappings = mappings

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

    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
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
        if role == Qt.BackgroundColorRole and index.column() == 0:
            return self.data_color(self._display_names[index.row()])
        if role == Qt.BackgroundColorRole and index.column() == 2:
            # display error color if mapping is None
            m = self._mappings[index.row()]
            if not isinstance(m, NoneMapping) and m.reference is None:
                return _ERROR_COLOR
        if role == Qt.ToolTipRole and index.column() == 2:
            # display error message if reference is None
            m = self._mappings[index.row()]
            if not isinstance(m, NoneMapping) and m.reference is None:
                return "No reference for mapping"

    def data_color(self, display_name):
        if display_name == "Relationship class names":
            return _MAPPING_COLORS["entity class"]
        if "Object class" in display_name:
            return _MAPPING_COLORS["entity class"]
        if "Object names" in display_name:
            return _MAPPING_COLORS["entity"]
        if display_name == "Parameter names":
            return _MAPPING_COLORS["parameter name"]
        if display_name in ["Parameter map index", "Parameter time index", "Parameter time pattern index"]:
            return _MAPPING_COLORS["parameter extra dimension"]
        if display_name == "Parameter values":
            return _MAPPING_COLORS["parameter value"]

    def rowCount(self, index=None):
        if not self._model:
            return 0
        return len(self._display_names)

    def columnCount(self, index=None):
        if not self._model:
            return 0
        return 3

    def headerData(self, section, orientation, role):
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

    def setData(self, index, value, role):
        name = self._display_names[index.row()]
        if index.column() == 1:
            return self.set_type(name, value)
        if index.column() == 2:
            return self.set_value(name, value)
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
        else:
            return False
        return self.set_mapping_from_name(name, value)

    def set_value(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if isinstance(mapping, NoneMapping):
            # create new mapping
            if value.isdigit():
                mapping = ColumnMapping(reference=int(value))
            elif value:
                mapping = ConstantMapping(reference=value)
            else:
                return False
        elif type(mapping) in (ConstantMapping, ColumnHeaderMapping):
            if not value:
                mapping.reference = None
            else:
                mapping.reference = str(value)
        elif isinstance(mapping, RowMapping) and isinstance(value, str) and value.lower() == "header":
            mapping.reference = -1
        elif isinstance(mapping, (RowMapping, ColumnMapping)):
            if not value:
                value = None
            try:
                if value is not None:
                    value = int(value)
                    if isinstance(mapping, RowMapping):
                        value = max(-1, value)
                    else:
                        value = max(0, value)
            except ValueError:
                pass
            mapping.reference = value
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
            mapping = self._model.name
        elif name == "Object names":
            mapping = self._model.objects
        elif "Object class " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                mapping = self._model.object_classes[index[0]]
        elif "Object " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                mapping = self._model.objects[index[0]]
        elif name == "Parameter names":
            mapping = self._model.parameters.name
        elif name == "Parameter values":
            mapping = self._model.parameters.value
        elif name in ("Parameter map index", "Parameter time index", "Parameter time pattern index"):
            mapping = self._model.parameters.extra_dimensions[0]
        else:
            return None
        return mapping

    def set_mapping_from_name(self, name, mapping):
        if name in ("Relationship class names", "Object class names"):
            self._model.name = mapping
        elif name == "Object names":
            self._model.objects = mapping
        elif "Object class " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                self._model.object_classes[index[0]] = mapping
        elif "Object " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                self._model.objects[index[0]] = mapping
        elif name == "Parameter names":
            self._model.parameters.name = mapping
        elif name == "Parameter values":
            self._model.parameters.value = mapping
        elif name in ("Parameter map index", "Parameter time index", "Parameter time pattern index"):
            self._model.parameters.extra_dimensions = [mapping]
        else:
            return False

        self.update_display_table()
        if name in self._display_names:
            self.dataChanged.emit(QModelIndex(), QModelIndex(), [])
        return True

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

    def model_parameters(self):
        """Returns the mapping's parameters."""
        return self._model.parameters if self._model is not None else None


class MappingListModel(QAbstractListModel):
    """
    A model to hold a list of Mappings.
    """

    def __init__(self, mapping_list, parent=None):
        super().__init__(parent)
        self._qmappings = []
        self._names = []
        self._counter = 1
        self.set_model(mapping_list)

    def set_model(self, model):
        self.beginResetModel()
        self._names = []
        self._qmappings = []
        for m in model:
            self._names.append("Mapping " + str(self._counter))
            self._qmappings.append(MappingSpecModel(m))
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
        self._qmappings.append(MappingSpecModel(m))
        self._names.append("Mapping " + str(self._counter))
        self._counter += 1
        self.endInsertRows()

    def remove_mapping(self, row):
        if self._qmappings and row < len(self._qmappings):
            self.beginRemoveRows(self.index(row, 0), row, row)
            self._qmappings.pop(row)
            self._names.pop(row)
            self.endRemoveRows()


def _create_allowed_types_menu(parent, trigger_slot):
    """
    Returns a menu which contains actions for each allowed data type.

    Args:
        parent (QWidget): a parent widget
        trigger_slot (Slot): a slot which is connected to QMenu's 'triggered' signal
    Returns:
        QMenu: a menu
    """
    menu = QMenu(parent)
    for at in _ALLOWED_TYPES:
        menu.addAction(at)
    menu.triggered.connect(trigger_slot)
    return menu


class HeaderWithButton(QHeaderView):
    """Class that reimplements the QHeaderView section paint event to draw a button
    that is used to display and change the type of that column or row.
    """

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setHighlightSections(True)
        self.setSectionsClickable(True)
        self.setDefaultAlignment(Qt.AlignLeft)
        self.sectionResized.connect(self._section_resize)
        self.sectionMoved.connect(self._section_move)
        self._font = QFont('Font Awesome 5 Free Solid')

        self._display_all = True
        self._display_sections = []

        self._margin = Margin(left=0, right=0, top=0, bottom=0)

        self._menu = _create_allowed_types_menu(self, self._menu_pressed)

        self._button = QToolButton(parent=self)
        self._button.setMenu(self._menu)
        self._button.setPopupMode(QToolButton.InstantPopup)
        self._button.setFont(self._font)
        self._button.hide()

        self._render_button = QToolButton(parent=self)
        self._render_button.setFont(self._font)
        self._render_button.hide()

        self._button_logical_index = None
        self.setMinimumSectionSize(self.minimumSectionSize() + self.widget_width())

    @property
    def display_all(self):
        return self._display_all

    @display_all.setter
    def display_all(self, display_all):
        self._display_all = display_all
        self.viewport().update()

    @property
    def sections_with_buttons(self):
        return self._display_sections

    @sections_with_buttons.setter
    def sections_with_buttons(self, sections):
        self._display_sections = set(sections)
        self.viewport().update()

    @Slot("QAction")
    def _menu_pressed(self, action):
        """Sets the data type of a row or column according to menu action."""
        type_str = action.text()
        self.set_data_types(self._button_logical_index, type_str,update_viewport=False)

    def set_data_types(self, sections, type_str, update_viewport=True):
        """
        Sets the data types of given sections (rows, columns).

        Args:
            sections (Iterable or int or NoneType): row/column index
            type_str (str): data type name
            update_viewport (bool): True if the buttons need repaint
        """
        if type_str == "integer sequence datetime":
            dialog = NewIntegerSequenceDateTimeConvertSpecDialog()
            if dialog.exec_():
                convert_spec = dialog.get_spec()
            else:
                return
        else:
            convert_spec = value_to_convert_spec(type_str)
        if not isinstance(sections, Iterable):
            sections = [sections]
        orientation = self.orientation()
        for section in sections:
            self.model().set_type(section, convert_spec, orientation)
        if update_viewport:
            self.viewport().update()

    def widget_width(self):
        """Width of widget

        Returns:
            [int] -- Width of widget
        """
        if self.orientation() == Qt.Horizontal:
            return self.height()
        return self.sectionSize(0)

    def widget_height(self):
        """Height of widget

        Returns:
            [int] -- Height of widget
        """
        if self.orientation() == Qt.Horizontal:
            return self.height()
        return self.sectionSize(0)

    def mouseMoveEvent(self, mouse_event):
        """Moves the button to the correct section so that interacting with the button works.
        """
        log_index = self.logicalIndexAt(mouse_event.x(), mouse_event.y())
        if not self._display_all and log_index not in self._display_sections:
            self._button_logical_index = None
            self._button.hide()
            super().mouseMoveEvent(mouse_event)
            return

        if self._button_logical_index != log_index:
            self._button_logical_index = log_index
            self._set_button_geometry(self._button, log_index)
            self._button.show()
        super().mouseMoveEvent(mouse_event)

    def mousePressEvent(self, mouse_event):
        """Move the button to the pressed location and show or hide it if button should not be shown.
        """
        log_index = self.logicalIndexAt(mouse_event.x(), mouse_event.y())
        if not self._display_all and log_index not in self._display_sections:
            self._button_logical_index = None
            self._button.hide()
            super().mousePressEvent(mouse_event)
            return

        if self._button_logical_index != log_index:
            self._button_logical_index = log_index
            self._set_button_geometry(self._button, log_index)
            self._button.show()
        super().mousePressEvent(mouse_event)

    def leaveEvent(self, event):
        """Hide button
        """
        self._button_logical_index = None
        self._button.hide()
        super().leaveEvent(event)

    def _set_button_geometry(self, button, index):
        """Sets a buttons geometry depending on the index.

        Arguments:
            button {QWidget} -- QWidget that geometry should be set
            index {int} -- logical_index to set position and geometry to.
        """
        margin = self._margin
        if self.orientation() == Qt.Horizontal:
            button.setGeometry(
                self.sectionViewportPosition(index) + margin.left,
                margin.top,
                self.widget_width() - self._margin.left - self._margin.right,
                self.widget_height() - margin.top - margin.bottom,
            )
        else:
            button.setGeometry(
                margin.left,
                self.sectionViewportPosition(index) + margin.top,
                self.widget_width() - self._margin.left - self._margin.right,
                self.widget_height() - margin.top - margin.bottom,
            )

    def _section_resize(self, i):
        """When a section is resized.

        Arguments:
            i {int} -- logical index to section being resized
        """
        self._button.hide()
        if i == self._button_logical_index:
            self._set_button_geometry(self._button, self._button_logical_index)

    def paintSection(self, painter, rect, logical_index):
        """Paints a section of the QHeader view.

        Works by drawing a pixmap of the button to the left of the original paint rectangle.
        Then shifts the original rect to the right so these two doesn't paint over each other.
        """
        if not self._display_all and logical_index not in self._display_sections:
            super().paintSection(painter, rect, logical_index)
            return

        # get the type of the section.
        type_spec = self.model().get_type(logical_index, self.orientation())
        if type_spec is None:
            type_spec = "string"
        else:
            type_spec = type_spec.DISPLAY_NAME
        font_str = _TYPE_TO_FONT_AWESOME_ICON[type_spec]

        # set data for both interaction button and render button.
        self._button.setText(font_str)
        self._render_button.setText(font_str)
        self._set_button_geometry(self._render_button, logical_index)

        # get pixmap from render button and draw into header section.
        rw = self._render_button.grab()
        if self.orientation() == Qt.Horizontal:
            painter.drawPixmap(self.sectionViewportPosition(logical_index), 0, rw)
        else:
            painter.drawPixmap(0, self.sectionViewportPosition(logical_index), rw)

        # shift rect that super class should paint in to the right so it doesn't
        # paint over the button
        rect.adjust(self.widget_width(), 0, 0, 0)
        super().paintSection(painter, rect, logical_index)

    def sectionSizeFromContents(self, logical_index):
        """Add the button width to the section so it displays right.

        Arguments:
            logical_index {int} -- logical index of section

        Returns:
            [QSize] -- Size of section
        """
        org_size = super().sectionSizeFromContents(logical_index)
        org_size.setWidth(org_size.width() + self.widget_width())
        return org_size

    def _section_move(self, logical, old_visual_index, new_visual_index):
        """Section beeing moved.

        Arguments:
            logical {int} -- logical index of section beeing moved.
            old_visual_index {int} -- old visual index of section
            new_visual_index {int} -- new visual index of section
        """
        self._button.hide()
        if self._button_logical_index is not None:
            self._set_button_geometry(self._button, self._button_logical_index)

    def fix_widget_positions(self):
        """Update position of interaction button
        """
        if self._button_logical_index is not None:
            self._set_button_geometry(self._button, self._button_logical_index)

    def set_margins(self, margins):
        """Sets the header margins."""
        self._margin = margins


class TableViewWithButtonHeader(QTableView):
    """Customized table with data type buttons on horizontal and vertical headers"""
    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget): a parent widget
        """
        super().__init__(parent)
        self._horizontal_header = HeaderWithButton(Qt.Horizontal, self)
        self._vertical_header = HeaderWithButton(Qt.Vertical, self)
        self.setHorizontalHeader(self._horizontal_header)
        self._horizontal_header.setContextMenuPolicy(Qt.CustomContextMenu)
        self._horizontal_header.customContextMenuRequested.connect(self._show_horizontal_header_menu)
        self._horizontal_menu = self._create_horizontal_header_menu()
        self.setVerticalHeader(self._vertical_header)
        self._vertical_header.setContextMenuPolicy(Qt.CustomContextMenu)
        self._vertical_header.customContextMenuRequested.connect(self._show_vertical_header_menu)
        self._vertical_menu = self._create_vertical_header_menu()

    def scrollContentsBy(self, dx, dy):
        """Scrolls the table's contents by given delta."""
        super().scrollContentsBy(dx, dy)
        if dx != 0:
            self._horizontal_header.fix_widget_positions()
        if dy != 0:
            self._vertical_header.fix_widget_positions()

    def _create_horizontal_header_menu(self):
        """Returns a new menu for the horizontal header"""
        parent = self._horizontal_header
        menu = QMenu(parent)
        type_menu = _create_allowed_types_menu(parent, self._set_all_column_data_types)
        type_menu.setTitle("Set all data types to...")
        menu.addMenu(type_menu)
        return menu

    def _create_vertical_header_menu(self):
        """Returns a new menu for the vertical header."""
        parent = self._horizontal_header
        menu = QMenu(parent)
        type_menu = _create_allowed_types_menu(parent, self._set_all_row_data_types)
        type_menu.setTitle("Set all data types to...")
        menu.addMenu(type_menu)
        return menu

    @Slot("QPoint")
    def _show_horizontal_header_menu(self, pos):
        """Opens the context menu of the horizontal header."""
        screen_pos = self._horizontal_header.mapToGlobal(pos)
        self._horizontal_menu.exec_(screen_pos)

    @Slot("QPoint")
    def _show_vertical_header_menu(self, pos):
        """Opens the context menu of the vertical header."""
        screen_pos = self._vertical_header.mapToGlobal(pos)
        self._vertical_menu.exec_(screen_pos)

    @Slot("QAction")
    def _set_all_column_data_types(self, action):
        """Sets all columns data types to the type given by action's text."""
        type_str = action.text()
        columns = range(self._horizontal_header.count())
        self._horizontal_header.set_data_types(columns, type_str)

    @Slot("QAction")
    def _set_all_row_data_types(self, action):
        """Sets all rows data types to the type given by action's text."""
        type_str = action.text()
        rows = range(self._vertical_header.count())
        self._vertical_header.set_data_types(rows, type_str)
