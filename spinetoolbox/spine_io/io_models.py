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

:author: P. Vennström (VTT)
:date:   1.6.2019
"""
from collections import namedtuple
from six import unichr

from spinedb_api import (
    ObjectClassMapping,
    RelationshipClassMapping,
    ParameterMapping,
    Mapping,
    DateTime,
    Duration,
    ParameterValueFormatError,
)
from PySide2.QtWidgets import QHeaderView, QMenu, QAction, QTableView, QPushButton, QToolButton
from PySide2.QtCore import QModelIndex, Qt, QAbstractTableModel, QAbstractListModel, QPoint, Signal
from PySide2.QtGui import QColor, QBrush, QRegion, QPixmap, QFont
from ..mvcmodels.minimal_table_model import MinimalTableModel
from .io_api import TYPE_CLASS_TO_STRING, TYPE_STRING_TO_CLASS

Margin = namedtuple("Margin", ("left", "right", "top", "bottom"))

_COLUMN_TYPE_ROLE = Qt.UserRole
_COLUMN_NUMBER_ROLE = Qt.UserRole + 1
_ALLOWED_TYPES = list(sorted(TYPE_STRING_TO_CLASS.keys()))

_TYPE_TO_FONT_AWESOME_ICON = {
    "string": unichr(int('f031', 16)),
    "datetime": unichr(int('f073', 16)),
    "duration": unichr(int('f017', 16)),
    "float": unichr(int('f534', 16)),
}

_DISPLAY_TYPE_TO_TYPE = {
    "Single value": "single value",
    "List": "1d array",
    "Time series": "time series",
    "Time pattern": "time pattern",
    "Definition": "definition",
}

_TYPE_TO_DISPLAY_TYPE = {value: key for key, value in _DISPLAY_TYPE_TO_TYPE.items()}


class MappingPreviewModel(MinimalTableModel):
    """A model for highlighting columns, rows, and so on, depending on Mapping specification.
    Used by ImportPreviewWidget.
    """

    columnTypesUpdated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self._mapping = None
        self._data_changed_signal = None
        self._type_errors = {}

    def clear(self):
        self._type_errors = {}
        super().clear()

    def reset_model(self, main_data=None):
        self._type_errors = {}
        super().reset_model(main_data)

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

    def validate_column_type(self, col):
        type_class = self.get_column_type(col)
        if type_class is None:
            return
        type_class = TYPE_STRING_TO_CLASS[type_class]
        for row in range(self.rowCount()):
            index = self.index(row, col)
            self._type_errors.pop((row, col), None)
            data = self.data(index)
            try:
                if isinstance(data, str) and not data:
                    data = None
                if data is not None:
                    type_class(data)
            except (ValueError, ParameterValueFormatError) as e:
                self._type_errors[(row, col)] = e
        self.dataChanged.emit(self.index(0, col), self.index(self.rowCount(), col))

    def get_column_type(self, col):
        return self.headerData(col, orientation=Qt.Horizontal, role=_COLUMN_TYPE_ROLE)

    def get_column_types(self):
        return {col: self.get_column_type(col) for col in range(self.columnCount())}

    def set_column_type(self, col, col_type):
        if col_type not in _ALLOWED_TYPES:
            raise ValueError(f"col_type must be a value in {_ALLOWED_TYPES}, instead got {col_type}")
        if col < 0 or col > self.columnCount():
            raise ValueError(f"col must be a in column count")
        success = self.setHeaderData(col, Qt.Horizontal, col_type, _COLUMN_TYPE_ROLE)
        if success:
            self.columnTypesUpdated.emit()
            self.validate_column_type(col)

    def update_colors(self):
        self.dataChanged.emit(QModelIndex, QModelIndex, [Qt.BackgroundColorRole])

    def data_error(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return "Error"
        if role == Qt.ToolTipRole:
            return f'Could not parse value: "{self._main_data[index.row()][index.column()]}" as a {self.get_column_type(index.column())}'
        if role == Qt.BackgroundColorRole:
            return QColor(Qt.red)

    def data(self, index, role=Qt.DisplayRole):
        if (index.row(), index.column()) in self._type_errors:
            return self.data_error(index, role)
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
        if mapping.parameters is not None:
            # parameter colors
            if mapping.is_pivoted() and mapping.parameters.parameter_type != "definition":
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
        super().__init__(parent)
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

    @property
    def parameter_type(self):
        if self._model.parameters is None:
            return "None"
        return _TYPE_TO_DISPLAY_TYPE[self._model.parameters.parameter_type]

    @property
    def is_pivoted(self):
        if self._model:
            return self._model.is_pivoted()
        return False

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
        Change parameter type
        """

        self.beginResetModel()
        if new_type == "None":
            self._model.parameters = None
        elif new_type in ("Single value", "List", "Definition"):
            if self._model.parameters is None:
                self._model.parameters = ParameterMapping()
            self._model.parameters.extra_dimensions = None
            if new_type == "Definition":
                self._model.parameters.value = None
            self._model.parameters.parameter_type = _DISPLAY_TYPE_TO_TYPE[new_type]
        elif new_type in ("Time series", "Time pattern"):
            if self._model.parameters is None:
                self._model.parameters = ParameterMapping(extra_dimensions=[None])

            if self._model.parameters.extra_dimensions is None:
                self._model.parameters.extra_dimensions = [None]
            else:
                self._model.parameters.extra_dimensions = self._model.parameters.extra_dimensions[:1]
            self._model.parameters.parameter_type = _DISPLAY_TYPE_TO_TYPE[new_type]

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
                display_name.extend([f"Object class {i+1} names" for i, oc in enumerate(self._model.object_classes)])
                mappings.extend(list(self._model.object_classes))
            if self._model.objects:
                display_name.extend([f"Object {i+1} names" for i, oc in enumerate(self._model.objects)])
                mappings.extend(list(self._model.objects))
        else:
            display_name.append("Object class names")
            display_name.append("Object names")
            mappings.append(self._model.object)
        if self._model.parameters:
            display_name.append("Parameter names")
            mappings.append(self._model.parameters.name)
            if self._model.parameters.parameter_type != "definition":
                display_name.append("Parameter values")
                mappings.append(self._model.parameters.value)
            if self._model.parameters.parameter_type == "time series":
                display_name.append("Parameter time index")
                mappings.append(self._model.parameters.extra_dimensions[0])
            if self._model.parameters.parameter_type == "time pattern":
                display_name.append("Parameter time pattern index")
                mappings.append(self._model.parameters.extra_dimensions[0])
        self._display_names = display_name
        self._mappings = mappings

    def get_map_type_display(self, mapping, name):
        if name == "Parameter values" and self._model.is_pivoted():
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
        if name == "Parameter values" and self._model.is_pivoted():
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

    # pylint: disable=no-self-use
    def get_map_append_display(self, mapping, name):
        append_str = ""
        if isinstance(mapping, Mapping):
            append_str = mapping.append_str
        return append_str

    # pylint: disable=no-self-use
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

        if mapping is None:
            if index.column() <= 2:
                return editable
            return non_editable

        if isinstance(mapping, str):
            if index.column() <= 2:
                return editable
            return non_editable
        if isinstance(mapping, Mapping) and mapping.map_type == "row" and mapping.value_reference == -1:
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
        if name in ("Relationship class names", "Object class names"):
            mapping = self._model.name
        elif name == "Object names":
            mapping = self._model.object
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
        elif name in ("Parameter time index", "Parameter time pattern index"):
            mapping = self._model.parameters.extra_dimensions[0]
        else:
            return None
        return mapping

    def set_mapping_from_name(self, name, mapping):
        if name in ("Relationship class names", "Object class names"):
            self._model.name = mapping
        elif name == "Object names":
            self._model.object = mapping
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
        elif name in ("Parameter time index", "Parameter time pattern index"):
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


class HeaderWithButton(QHeaderView):
    def __init__(self, orientation, parent=None):
        super(HeaderWithButton, self).__init__(orientation, parent)
        self.setHighlightSections(True)
        self.setSectionsClickable(True)
        self.setDefaultAlignment(Qt.AlignLeft)
        self.sectionResized.connect(self._section_resize)
        self.sectionMoved.connect(self._section_move)
        self._font = QFont('Font Awesome 5 Free Solid')

        self._margin = Margin(left=0, right=0, top=0, bottom=0)

        self._menu = self._create_menu()

        self._button = QToolButton(parent=self)
        self._button.setMenu(self._menu)
        self._button.setPopupMode(QToolButton.InstantPopup)
        self._button.setFont(self._font)
        self._button.hide()

        self._render_button = QToolButton(parent=self)
        self._render_button.setFont(self._font)
        self._render_button.hide()

        self._menu.triggered.connect(self._menu_pressed)
        self._button_logical_index = None
        self.setMinimumSectionSize(self.minimumSectionSize() + self.widget_width())

    def _create_menu(self):
        menu = QMenu(self)
        for at in _ALLOWED_TYPES:
            action = QAction(parent=menu)
            action.setText(at)
            menu.addAction(action)
        menu.triggered.connect(self._menu_pressed)
        return menu

    def _menu_pressed(self, action):
        logical_index = self._button_logical_index
        self.model().set_column_type(logical_index, action.text())

    def widget_width(self):
        return self.height()

    def mouseMoveEvent(self, mouse_event):
        log_index = self.logicalIndexAt(mouse_event.x(), mouse_event.y())
        if self._button_logical_index != log_index:
            self._button_logical_index = log_index
            self._set_button_geometry(self._button, log_index)
            self._button.show()
        super().mouseMoveEvent(mouse_event)

    def mousePressEvent(self, mouse_event):
        log_index = self.logicalIndexAt(mouse_event.x(), mouse_event.y())
        if self._button_logical_index != log_index:
            self._button_logical_index = log_index
            self._set_button_geometry(self._button, log_index)
            self._button.show()
        super().mousePressEvent(mouse_event)

    def leaveEvent(self, event):
        self._button_logical_index = None
        self._button.hide()
        super().leaveEvent(event)

    def _set_button_geometry(self, button, index):
        margin = self._margin
        button.setGeometry(
            self.sectionViewportPosition(index) + margin.left,
            margin.top,
            self.widget_width() - self._margin.left - self._margin.right,
            self.height() - margin.top - margin.bottom,
        )

    def _section_resize(self, i):
        self._button.hide()
        if i == self._button_logical_index:
            self._set_button_geometry(self._button, self._button_logical_index)

    def paintSection(self, painter, rect, logical_index):
        """move original rect a bit to the right to make room for the widget"""
        type_str = self.model().headerData(logical_index, self.orientation(), _COLUMN_TYPE_ROLE)
        if type_str is None:
            type_str = "string"
        font_str = _TYPE_TO_FONT_AWESOME_ICON[type_str]

        self._button.setText(font_str)
        self._render_button.setText(font_str)
        self._set_button_geometry(self._render_button, logical_index)

        rw = self._render_button.grab()
        painter.drawPixmap(self.sectionViewportPosition(logical_index), 0, rw)

        rect.adjust(self.widget_width(), 0, 0, 0)
        super().paintSection(painter, rect, logical_index)

    def sectionSizeFromContents(self, logical_index):
        org_size = super().sectionSizeFromContents(logical_index)
        org_size.setWidth(org_size.width() + self.widget_width())
        return org_size

    def _section_move(self, logical, old_visual_index, new_visual_index):
        self._button.hide()
        if self._button_logical_index is not None:
            self._set_button_geometry(self._button, self._button_logical_index)

    def fix_widget_positions(self):
        if self._button_logical_index is not None:
            self._set_button_geometry(self._button, self._button_logical_index)

    def set_margins(self, margins):
        self._margin = margins

    def headerDataChanged(self, orientation, logical_first, logical_last):
        super().headerDataChanged(orientation, logical_first, logical_last)


class TableViewWithButtonHeader(QTableView):
    def __init__(self, parent=None):
        super(TableViewWithButtonHeader, self).__init__(parent)
        self._horizontal_header = HeaderWithButton(Qt.Horizontal, self)
        self.setHorizontalHeader(self._horizontal_header)

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        if dx != 0:
            pass
            self._horizontal_header.fix_widget_positions()
