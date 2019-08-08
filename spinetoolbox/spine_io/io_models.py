######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

:author: M. Marin (KTH)
:date:   8.8.2019
"""
from spinedb_api import ObjectClassMapping, RelationshipClassMapping, ParameterMapping, Mapping
from PySide2.QtCore import QModelIndex, Qt, QAbstractTableModel, QAbstractListModel
from PySide2.QtGui import QColor
from models import MinimalTableModel


class MappingPreviewModel(MinimalTableModel):
    """A model for highlighting columns, rows, and so on, depending on Mapping specification.
    Used by ImportPreviewWidget.
    """

    def __init__(self, parent=None):
        super(MappingPreviewModel, self).__init__(parent)
        self.default_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self._mapping = None
        self._data_changed_signal = None

    def set_mapping(self, mapping):
        """Set mapping to display colors from

        Arguments:
            mapping {MappingSpecModel} -- mapping model
        """
        if self._data_changed_signal is not None and self._mapping:
            self._mapping.dataChanged.disconnect(self.update_colors)
            self._data_changed_signal = None
        self._mapping = mapping
        if self._mapping:
            self._data_changed_signal = self._mapping.dataChanged.connect(self.update_colors)
        self.update_colors()

    def update_colors(self):
        self.dataChanged.emit(QModelIndex, QModelIndex, [Qt.BackgroundColorRole])

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.BackgroundColorRole and self._mapping:
            return self.data_color(index)
        return super(MappingPreviewModel, self).data(index, role)

    def data_color(self, index):
        """returns background color for index depending on mapping

        Arguments:
            index {PySide2.QtCore.QModelIndex} -- index

        Returns:
            [QColor] -- QColor of index
        """
        mapping = self._mapping._model
        if mapping.parameters is not None:
            # parameter colors
            if mapping.is_pivoted():
                # parameter values color
                last_row = mapping.last_pivot_row()
                if (
                    last_row is not None
                    and index.row() > last_row
                    and index.column() not in self.mapping_column_ref_int_list()
                ):
                    return QColor(1, 133, 113)
            elif self.index_in_mapping(mapping.parameters.value, index):
                return QColor(1, 133, 113)
            if mapping.parameters.extra_dimensions:
                # parameter extra dimensions color
                for ed in mapping.parameters.extra_dimensions:
                    if self.index_in_mapping(ed, index):
                        return QColor(128, 205, 193)
            if self.index_in_mapping(mapping.parameters.name, index):
                # parameter name colors
                return QColor(128, 205, 193)
        if self.index_in_mapping(mapping.name, index):
            # class name color
            return QColor(166, 97, 26)
        objects = []
        classes = []
        if isinstance(mapping, ObjectClassMapping):
            objects = [mapping.object]
        else:
            if mapping.objects:
                objects = mapping.objects
            if mapping.object_classes:
                classes = mapping.object_classes
        for o in objects:
            # object colors
            if self.index_in_mapping(o, index):
                return QColor(223, 194, 125)
        for c in classes:
            # object colors
            if self.index_in_mapping(c, index):
                return QColor(166, 97, 26)

    def index_in_mapping(self, mapping, index):
        """Checks if index is in mapping

        Arguments:
            mapping {Mapping} -- mapping
            index {QModelIndex} -- index

        Returns:
            [bool] -- returns True if mapping is in index
        """
        if not isinstance(mapping, Mapping):
            return False
        if mapping.map_type == "column":
            ref = mapping.value_reference
            if isinstance(ref, str):
                # find header reference
                if ref in self._headers:
                    ref = self._headers.index(ref)
            if index.column() == ref:
                if self._mapping._model.is_pivoted():
                    # only rows below pivoted rows
                    last_row = self._mapping._model.last_pivot_row()
                    if last_row is not None and index.row() > last_row:
                        return True
                else:
                    return True
        if mapping.map_type == "row":
            if index.row() == mapping.value_reference:
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
        super(MappingSpecModel, self).__init__(parent)
        self._display_names = []
        self._mappings = []
        self._model = None
        if model is not None:
            self.set_mapping(model)

    @property
    def map_type(self):
        if self._model is None:
            return None
        return type(self._model)

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
            self._model.objects = self._model.objects[:dim]
            self._model.object_classes = self._model.object_classes[:dim]
        else:
            self._model.objects = self._model.objects + [None]
            self._model.object_classes = self._model.object_classes + [None]
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
                obj = [self._model.object]
                object_class = [self._model.name]
                self._model = RelationshipClassMapping(
                    name=None, object_classes=object_class, objects=obj, parameters=parameters
                )
            else:
                # convert relationship mapping to object mapping
                self._model = ObjectClassMapping(
                    name=self._model.object_classes[0], obj=self._model.objects[0], parameters=parameters
                )

        self.update_display_table()
        self.dataChanged.emit(QModelIndex, QModelIndex, [])
        self.endResetModel()

    def change_parameter_type(self, new_type):
        """
        Change parameter between time series, single, and no parameter
        """
        self.beginResetModel()
        if new_type == "None":
            self._model.parameters = None
        elif new_type == "Single value":
            if self._model.parameters is not None:
                self._model.parameters.extra_dimensions = None
            else:
                self._model.parameters = ParameterMapping()
        elif new_type == "Time series":
            if self._model.parameters is not None:
                if self._model.parameters.extra_dimensions is None:
                    self._model.parameters.extra_dimensions = [None]
                else:
                    self._model.parameters.extra_dimensions = self._model.parameters.extra_dimensions[:1]
            else:
                self._model.parameters = ParameterMapping(extra_dimensions=[None])
        self.update_display_table()
        self.dataChanged.emit(QModelIndex, QModelIndex, [])
        self.endResetModel()

    def update_display_table(self):
        display_name = []
        mappings = []
        mappings.append(self._model.name)
        if isinstance(self._model, RelationshipClassMapping):
            display_name.append("Relationship class names:")
            if self._model.object_classes:
                display_name.extend([f"Object class {i+1} names:" for i, oc in enumerate(self._model.object_classes)])
                mappings.extend([oc for oc in self._model.object_classes])
            if self._model.objects:
                display_name.extend([f"Object {i+1} names:" for i, oc in enumerate(self._model.objects)])
                mappings.extend([o for o in self._model.objects])
        else:
            display_name.append("Object class names:")
            display_name.append("Object names:")
            mappings.append(self._model.object)
        if self._model.parameters:
            display_name.append("Parameter names:")
            mappings.append(self._model.parameters.name)
            display_name.append("Parameter values:")
            mappings.append(self._model.parameters.value)
            if self._model.parameters.extra_dimensions:
                display_name.append("Parameter time index:")
                mappings.append(self._model.parameters.extra_dimensions[0])
        self._display_names = display_name
        self._mappings = mappings

    def get_map_type_display(self, mapping, name):
        if name == "Parameter values:" and self._model.is_pivoted():
            mapping_type = "Pivoted"
        elif mapping is None:
            mapping_type = "None"
        elif isinstance(mapping, str):
            mapping_type = "Constant"
        elif isinstance(mapping, Mapping):
            if mapping.map_type == "column":
                mapping_type = "Column"
            elif mapping.map_type == "column_name":
                mapping_type = "Header"
            elif mapping.map_type == "row":
                mapping_type = "Row"
        return mapping_type

    def get_map_value_display(self, mapping, name):
        if name == "Parameter values:" and self._model.is_pivoted():
            mapping_value = "Pivoted values"
        elif mapping is None:
            mapping_value = ""
        elif isinstance(mapping, str):
            mapping_value = mapping
        elif isinstance(mapping, Mapping):
            if mapping.map_type == "row":
                if mapping.value_reference == -1:
                    mapping_value = "Headers"
                else:
                    mapping_value = str(mapping.value_reference)
            elif mapping.map_type == "column":
                mapping_value = str(mapping.value_reference)
            else:
                mapping_value = str(mapping.value_reference)
        return mapping_value

    def get_map_append_display(self, mapping, name):
        append_str = ""
        if isinstance(mapping, Mapping):
            append_str = mapping.append_str
        return append_str

    def get_map_prepend_display(self, mapping, name):
        prepend_str = ""
        if isinstance(mapping, Mapping):
            prepend_str = mapping.prepend_str
        return prepend_str

    def data(self, index, role):
        if role == Qt.DisplayRole:
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

    def rowCount(self, index=None):
        if not self._model:
            return 0
        return len(self._display_names)

    def columnCount(self, index=None):
        if not self._model:
            return 0
        return 5

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ["Mapping", "Type", "Reference", "Prepend string", "Append string"][section]

    def flags(self, index):
        editable = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        non_editable = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0:
            return non_editable
        mapping = self._mappings[index.row()]

        if self._model.is_pivoted():
            # special case when we have pivoted data, the values should be
            # columns under pivoted indexes
            if self._display_names[index.row()] == "Parameter values:":
                return non_editable

        if mapping is None:
            if index.column() <= 2:
                return editable
            else:
                return non_editable

        if isinstance(mapping, str):
            if index.column() <= 2:
                return editable
            else:
                return non_editable
        elif isinstance(mapping, Mapping) and mapping.map_type == "row" and mapping.value_reference == -1:
            if index.column() == 2:
                return non_editable
            else:
                return editable
        else:
            return editable

    def setData(self, index, value, role):
        name = self._display_names[index.row()]
        if index.column() == 1:
            return self.set_type(name, value)
        elif index.column() == 2:
            return self.set_value(name, value)
        elif index.column() == 3:
            return self.set_prepend_str(name, value)
        elif index.column() == 4:
            return self.set_append_str(name, value)
        return False

    def set_type(self, name, value):
        if value in ("None", "", None):
            value = None
        elif value == "Constant":
            value = ""
        elif value == "Column":
            value = Mapping(map_type="column")
        elif value == "Header":
            value = Mapping(map_type="column_name")
        elif value == "Pivoted Headers":
            value = Mapping(map_type="row", value_reference=-1)
        elif value == "Row":
            value = Mapping(map_type="row")
        else:
            return False
        return self.set_mapping_from_name(name, value)

    def set_value(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if mapping is None and value.isdigit():
            # create new mapping
            mapping = Mapping(map_type="column", value_reference=int(value))
        elif mapping is None:
            # string mapping
            if value == "":
                return False
            mapping = value
        else:
            # update mapping value
            if isinstance(mapping, str):
                if value == "":
                    mapping = None
                else:
                    mapping = value
            else:
                if mapping.map_type == "row" and value.lower() == "header":
                    value = -1
                if value == "":
                    value = None
                try:
                    if value is not None:
                        value = int(value)
                        if mapping.map_type == "row":
                            value = max(-1, value)
                        else:
                            value = max(0, value)
                except ValueError:
                    return False

                mapping.value_reference = value
        return self.set_mapping_from_name(name, mapping)

    def set_append_str(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if mapping:
            if isinstance(mapping, Mapping):
                if value == "":
                    value = None
                mapping.append_str = value
                return self.set_mapping_from_name(name, mapping)
        return False

    def set_prepend_str(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if mapping:
            if isinstance(mapping, Mapping):
                if value == "":
                    value = None
                mapping.prepend_str = value
                return self.set_mapping_from_name(name, mapping)
        return False

    def get_mapping_from_name(self, name):
        if not self._model:
            return None
        if name in ("Relationship class names:", "Object class names:"):
            mapping = self._model.name
        elif name == "Object names:":
            mapping = self._model.object
        elif "Object class " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                mapping = self._model.object_classes[index[0]]
        elif "Object " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                mapping = self._model.objects[index[0]]
        elif name == "Parameter names:":
            mapping = self._model.parameters.name
        elif name == "Parameter values:":
            mapping = self._model.parameters.value
        elif name == "Parameter time index:":
            mapping = self._model.parameters.extra_dimensions[0]
        else:
            return None
        return mapping

    def set_mapping_from_name(self, name, mapping):
        if name in ("Relationship class names:", "Object class names:"):
            self._model.name = mapping
        elif name == "Object names:":
            self._model.object = mapping
        elif "Object class " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                self._model.object_classes[index[0]] = mapping
        elif "Object " in name:
            index = [int(s) - 1 for s in name.split() if s.isdigit()]
            if index:
                self._model.objects[index[0]] = mapping
        elif name == "Parameter names:":
            self._model.parameters.name = mapping
        elif name == "Parameter values:":
            self._model.parameters.value = mapping
        elif name == "Parameter time index:":
            self._model.parameters.extra_dimensions = [mapping]
        else:
            return False

        self.update_display_table()
        if name in self._display_names:
            self.dataChanged.emit(QModelIndex, QModelIndex, [])
        return True

    def set_skip_columns(self, columns=None):
        if columns is None:
            columns = []
        self._model.skip_columns = list(set(columns))
        self.dataChanged.emit(0, 0, [])


class MappingListModel(QAbstractListModel):
    """
    A model to hold a list of Mappings.
    """

    def __init__(self, mapping_list, parent=None):
        super(MappingListModel, self).__init__(parent)
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
