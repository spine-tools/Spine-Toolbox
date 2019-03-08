# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QWidget, QApplication, QListWidget, QVBoxLayout, QDialogButtonBox, QMainWindow, QGridLayout, QComboBox, QPushButton, QTableView, QHBoxLayout, QSpacerItem, QSpinBox, QGroupBox, QLabel, QMenu, QListWidgetItem, QListView
from PySide2.QtCore import Qt, QAbstractTableModel, QPoint, Signal, QItemSelectionModel, QAbstractListModel,QModelIndex

from functools import partial

import sys
sys.path.append("c:/data/GIT/spine-data/spinedatabase_api/")


from json_mapping import DataMapping, RelationshipClassMapping, ObjectClassMapping, Mapping, ParameterMapping


class MappingTableModel(QAbstractTableModel):
    def __init__(self, model, parent=None):
        super(MappingTableModel, self).__init__(parent)
        self._display_names = []
        self._mappings = []
        if model is None:
            self._model = None
        else:
            self.set_mapping(model)
        
    def map_type(self):
        if self._model is None:
            return None
        else:
            return type(self._model)
    
    def set_mapping(self, mapping):
        if type(mapping) not in (RelationshipClassMapping, ObjectClassMapping):
            raise TypeError("mapping must be of type: RelationshipClassMapping, ObjectClassMapping")
        self.beginResetModel()
        self._model = mapping
        if type(self._model) == RelationshipClassMapping:
            if self._model.objects is None:
                self._model.objects = [None, None]
                self._model.object_classes = [None, None]
        self.update_display_table()
        self.endResetModel()
    
    def update_model_dimension(self, dim):
        if self._model is None or type(self._model) == ObjectClassMapping:
            return
        self.beginResetModel()
        if len(self._model.objects) >= dim:
            self._model.objects = self._model.objects[:dim]
            self._model.object_classes = self._model.object_classes[:dim]
        else:
            self._model.objects = self._model.objects + [None]
            self._model.object_classes = self._model.object_classes + [None]
        self.update_display_table()
        self.endResetModel()

    def change_model_class(self, new_class):
        """
        Change model between Relationship and Object class
        """
        if new_class == 'Object':
            new_class = ObjectClassMapping
        else:
            new_class = RelationshipClassMapping
        if self._model is None or type(self._model) == new_class:
            return
        self.beginResetModel()
        parameters = self._model.parameters
        if new_class == RelationshipClassMapping:
            # convert object mapping to relationship mapping
            obj = [self._model.object, None]
            object_class = [self._model.name, None]
            self._model = RelationshipClassMapping(name=None,
                                                   object_classes=object_class,
                                                   objects=obj,
                                                   parameters=parameters)
        else:
            # convert relationship mapping to object mapping
            self._model = ObjectClassMapping(name=self._model.object_classes[0],
                                             obj=self._model.objects[0],
                                             parameters=parameters)
        
        self.update_display_table()
        self.endResetModel()

    def change_parameter_type(self, new_type):
        """
        Change parameter between time series, single, and no parameter
        """
        self.beginResetModel()
        if new_type == 'None':
            self._model.parameters = None
        elif new_type == 'Single value':
            if self._model.parameters is not None:
                self._model.parameters.extra_dimensions = None
            else:
                self._model.parameters = ParameterMapping(field='value')
        elif new_type == 'Time series':
            if self._model.parameters is not None:
                if self._model.parameters.extra_dimensions is None:
                    self._model.parameters.extra_dimensions = [None]
                else:
                    self._model.parameters.extra_dimensions = self._model.parameters.extra_dimensions[:1]
                    self._model.parameters.field = 'json'
            else:
                self._model.parameters = ParameterMapping(extra_dimensions=[None], field='json')
        self.update_display_table()
        self.endResetModel()
        
    def update_display_table(self):
        display_name = []
        mappings = []
        mappings.append(self._model.name)
        if type(self._model) == RelationshipClassMapping:
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
            mapping_type = 'None'
        elif type(mapping) == str:
            mapping_type = 'String'
        elif type(mapping) == Mapping:
            if mapping.map_type == 'column':
                mapping_type = 'Row values'
            elif mapping.map_type == 'column_name':
                mapping_type = 'Single column header'
            elif mapping.map_type == 'row':
                if mapping.value_reference == -1:
                    mapping_type = 'Pivoted Headers'
                else:
                    mapping_type = 'Column values'
        return mapping_type
    
    def get_map_value_display(self, mapping, name):
        if name == "Parameter values:" and self._model.is_pivoted():
            mapping_value = "Columns values under pivoted columns"
        elif mapping is None:
            mapping_value = ''
        elif type(mapping) == str:
            mapping_value = mapping
        elif type(mapping) == Mapping:
            if mapping.map_type == 'row':
                if mapping.value_reference == -1:
                    mapping_value = 'Headers'
                else:
                    mapping_value = 'Row: ' +  str(mapping.value_reference)
            else:
                mapping_value = 'Column: ' +  str(mapping.value_reference)
        return mapping_value
    
    def get_map_append_display(self, mapping, name):
        append_str = ''
        if type(mapping) == Mapping:
            append_str = mapping.append_str
        return append_str
            
    def get_map_prepend_display(self, mapping, name):
        prepend_str = ''
        if type(mapping) == Mapping:
            prepend_str = mapping.prepend_str
        return prepend_str
    
    def data(self, index, role):
        if role == Qt.DisplayRole:
            name = self._display_names[index.row()]
            m = self._mappings[index.row()]
            func = [lambda : name,
                    lambda : self.get_map_type_display(m, name),
                    lambda : self.get_map_value_display(m, name),
                    lambda : self.get_map_prepend_display(m, name),
                    lambda : self.get_map_append_display(m, name)]
            f = func[index.column()]
            return f()
        else:
            return

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
                return ['Mapping','Type','Reference','Prepend string','Append string'][section]
    
    def flags(self, index):
        editable = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        non_editable = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0:
            return non_editable
        mapping = self._mappings[index.row()]
        
        if self._model.is_pivoted():
            # special case when we have pivoted data, the values should be
            # columns under pivoted indexes
            if self._display_names[index.row()] == 'Parameter values:':
                return non_editable

        if mapping is None:
            if index.column() <= 1:
                return editable
            else:
                return non_editable

        if type(mapping) == str:
            if index.column() <= 2:
                return editable
            else:
                return non_editable
        elif type(mapping) == Mapping and mapping.map_type == "row" and mapping.value_reference == -1:
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
        if value == 'None' or value == '' or value == None:
            value = None
        elif value == 'String':
            value = ''
        elif value == 'Row values':
            value = Mapping(map_type='column')
        elif value == 'Single column header':
            value = Mapping(map_type='column_name')
        elif value == 'Pivoted Headers':
            value = Mapping(map_type='row', value_reference=-1)
        elif value == 'Column values':
            value = Mapping(map_type='row')
        else:
            return False
        return self.set_mapping_from_name(name, value)
    
    def set_value(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if mapping != None:
            if type(mapping) == str:
                mapping = value
            else:
                if value.isdigit():
                    value = int(value)
                    if mapping.map_type == 'row':
                        value = max(-1, value)
                    else:
                        value = max(0, value)
                elif value == '':
                    value = None
                mapping.value_reference = value
            return self.set_mapping_from_name(name, mapping)
        else:
            return False
    
    def set_append_str(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if mapping:
            if type(mapping) == Mapping:
                if value == '':
                    value = None
                mapping.append_str = value
                return self.set_mapping_from_name(name, mapping)
        return False

    def set_prepend_str(self, name, value):
        mapping = self.get_mapping_from_name(name)
        if mapping:
            if type(mapping) == Mapping:
                if value == '':
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



class MappingWidget(QWidget):
    mappingChanged = Signal(MappingTableModel)
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # state
        self._model = None

        # create widgets
        self._ui_add_mapping = QPushButton("New")
        self._ui_remove_mapping = QPushButton("Remove")
        self._ui_list = QListView()
        self._ui_table = QTableView()
        self._ui_options = MappingOptionWidget()
        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # layout
        self.setLayout(QVBoxLayout())
        bl = QHBoxLayout()
        bl.addWidget(self._ui_add_mapping)
        bl.addWidget(self._ui_remove_mapping)

        self.layout().addLayout(bl)
        self.layout().addWidget(self._ui_list)
        self.layout().addWidget(self._ui_options)
        self.layout().addWidget(self._ui_table)
        
        # connect signals
        self._select_handle = None
        self._ui_add_mapping.clicked.connect(self.new_mapping)
        self._ui_remove_mapping.clicked.connect(self.delete_selected_mapping)
        self.mappingChanged.connect(lambda m: self._ui_table.setModel(m))
        self.mappingChanged.connect(lambda m: self._ui_options.set_model(m))
    
    def set_model(self, model):
        """
        Sets new model
        """
        if self._select_handle and self._ui_list.selectionModel():
            self._ui_list.selectionModel().selectionChanged.disconnect(self.select_mapping)
            self._select_handle = None
        self._model = model
        self._ui_list.setModel(model)
        self._select_handle = self._ui_list.selectionModel().selectionChanged.connect(self.select_mapping)
        if self._model.rowCount() > 0:
            self._ui_list.setCurrentIndex(self._model.index(0,0))
        else:
            self._ui_list.clearSelection()
    
    def new_mapping(self):
        """
        Adds new empty mapping
        """
        if self._model:
            self._model.add_mapping()
            if not self._ui_list.selectedIndexes():
                # if no item is selected, select the first item
                self._ui_list.setCurrentIndex(self._model.index(0,0))
    
    def delete_selected_mapping(self):
        """
        deletes selected mapping
        """
        if self._model:
            # get selected mapping in list
            indexes = self._ui_list.selectedIndexes()
            if indexes:
                self._model.remove_mapping(indexes[0].row())
                if self._model.rowCount() > 0:
                    # select the first item
                    self._ui_list.setCurrentIndex(self._model.index(0,0))
                    self.select_mapping(self._ui_list.selectionModel().selection())
                else:
                    # no items clear selection so select_mapping is called
                    self._ui_list.clearSelection()

    def select_mapping(self, selection):
        """
        gets selected mapping and emits mappingChanged
        """
        if selection.indexes():
            m = self._model.data_mapping(selection.indexes()[0])
        else:
            m = None
        self.mappingChanged.emit(m)
            

class DataMappingListModel(QAbstractListModel):
    def __init__(self, mapping_list, parent=None):
        super(DataMappingListModel, self).__init__(parent)
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
            self._qmappings.append(MappingTableModel(m))
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
        if self._qmappings:
            self.beginInsertRows(self.index(self.rowCount(), 0), self.rowCount(),self.rowCount())
            m = ObjectClassMapping()
            self._qmappings.append(MappingTableModel(m))
            self._names.append("Mapping " + str(self._counter))
            self._counter += 1
            self.endInsertRows()
    
    def remove_mapping(self, row):
        if self._qmappings and row < len(self._qmappings):
            self.beginRemoveRows(self.index(row, 0), row, row)
            self._qmappings.pop(row)
            self._names.pop(row)
            self.endRemoveRows()
            

class MappingOptionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # state
        self._model = None
        
        # ui
        self._ui_class_type = QComboBox()
        self._ui_parameter_type = QComboBox()
        self._ui_dimension = QSpinBox()
        self._ui_ignore_columns = QPushButton()
        self._ui_ignore_columns_label = QLabel("Ignore columns:")
        self._ui_dimension_label = QLabel("Dimension:")
        
        self._ui_class_type.addItems(['Object','Relationship'])
        self._ui_parameter_type.addItems(['Single value','Time series','None'])

        self._ui_dimension.setMinimum(2)

        # layout
        groupbox = QGroupBox("Mapping:")
        self.setLayout(QVBoxLayout())
        layout = QGridLayout()
        layout.addWidget(QLabel("Class type:"), 0, 0)
        layout.addWidget(QLabel("Parameter type:"), 1, 0)
        layout.addWidget(self._ui_ignore_columns_label, 2, 0)
        layout.addWidget(self._ui_dimension_label, 0, 2)
        layout.addWidget(self._ui_class_type, 0, 1)
        layout.addWidget(self._ui_parameter_type, 1, 1)
        layout.addWidget(self._ui_ignore_columns, 2, 1)
        layout.addWidget(self._ui_dimension, 0, 3)
        groupbox.setLayout(layout)
        self.layout().addWidget(groupbox)
        
        # connect signals
        self._ui_dimension.valueChanged.connect(self.change_dimension)
        self._ui_class_type.currentTextChanged.connect(self.change_class)
        self._ui_parameter_type.currentTextChanged.connect(self.change_parameter)
        
        self._model_reset_signal = None
        
        
        self.update_ui()
        
    def set_model(self, model):
        if self._model_reset_signal and self._model:
            self._model.modelReset.disconnect(self.update_ui)
        self._model = model
        if self._model:
            self._model_reset_signal = self._model.modelReset.connect(self.update_ui)
        self.update_ui()
            
    def update_ui(self):
        """
        updates ui to RelationshipClassMapping or ObjectClassMapping model
        """
        if not self._model:
            self.hide()
            return
        
        self.show()
        self.block_signals = True
        if self._model.map_type() == RelationshipClassMapping:
            self._ui_dimension_label.show()
            self._ui_dimension.show()
            self._ui_class_type.setCurrentIndex(1)
            self._ui_dimension.setValue(len(self._model._model.objects))
        else:
            self._ui_dimension_label.hide()
            self._ui_dimension.hide()
            self._ui_class_type.setCurrentIndex(0)
        if self._model._model.parameters is None:
            self._ui_parameter_type.setCurrentIndex(2)
        else:
            if self._model._model.parameters.extra_dimensions:
                self._ui_parameter_type.setCurrentIndex(1)
            else:
                self._ui_parameter_type.setCurrentIndex(0)
        if self._model._model.is_pivoted():
            self._ui_ignore_columns.show()
            self._ui_ignore_columns_label.show()
        else:
            self._ui_ignore_columns.hide()
            self._ui_ignore_columns_label.hide()
            
        self.block_signals = False
    
    def change_class(self, new_class):
        if self._model and not self.block_signals:
            self._model.change_model_class(new_class)
    
    def change_dimension(self, dim):
        if self._model and not self.block_signals:
            self._model.update_model_dimension(dim)
    def change_parameter(self, par):
        if self._model and not self.block_signals:
            self._model.change_parameter_type(par)
        

