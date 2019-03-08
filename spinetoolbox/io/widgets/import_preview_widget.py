# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QWidget, QListWidget, QVBoxLayout, QDialogButtonBox, QHBoxLayout, QTableView, QMenu, QListWidgetItem
from PySide2.QtCore import QObject, Signal, QModelIndex, QAbstractItemModel, Qt, QItemSelectionModel, QPoint
from PySide2.QtGui import QColor

from widgets.mapping_widget import MappingWidget, DataMappingListModel
from json_mapping import DataMapping, RelationshipClassMapping, ObjectClassMapping, Mapping, ParameterMapping, read_with_mapping


import sys
sys.path.append("c:/data/GIT/spine-data/spinedatabase_api/")

class ImportPreviewWidget(QWidget):
    def __init__(self, connector, parent=None):
        super().__init__(parent)
        
        # state
        self.connector = connector
        self.selected_table = None
        self.table = MappingPreviewModel()
        self.selected_source_tables = set()
        self.table_mappings = {}
        
        # create widgets
        self._ui_list = QListWidget()
        self._ui_table = QTableView()
        self._ui_table.setModel(self.table)
        self._ui_mapper = MappingWidget()
        self._ui_preview_menu = MappingTableMenu(self._ui_table)

        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # layout
        self.setLayout(QVBoxLayout())
        main_layout = QHBoxLayout()
        self.layout().addLayout(main_layout)

        list_layout = QVBoxLayout()
        preview_layout = QVBoxLayout()
        mapping_layout = QVBoxLayout()
        mapping_layout.addWidget(self._ui_mapper)
        if self.connector.can_have_multiple_tables:
            list_layout.addWidget(self._ui_list)
            main_layout.addLayout(list_layout)
        preview_layout.addWidget(self.connector.option_widget())
        main_layout.addLayout(preview_layout)
        main_layout.addLayout(mapping_layout)
        self.layout().addWidget(self._dialog_buttons)
        preview_layout.addWidget(self._ui_table)
        
        # connect signals
        self._ui_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui_table.customContextMenuRequested.connect(self._ui_preview_menu.request_menu)
        
        self.connector.refreshDataRequest.connect(self.update_preview_data)
        self._ui_list.currentItemChanged.connect(self.select_table)
        self._ui_list.itemChanged.connect(self.check_list_item)
        
        
        self._dialog_buttons.button(QDialogButtonBox.Ok).clicked.connect(self.ok_pressed)

        self._ui_mapper.mappingChanged.connect(self.change_mapper)

        # initiate ui
        self.update_tables()
        self.connector.set_table(self.selected_table)
        self.update_preview_data()
        self.update_ok_state()
        
        if not self.connector.can_have_multiple_tables:
            self.selected_source_tables = set(['default'])
            self.table_mappings['default'] = DataMappingListModel([ObjectClassMapping()])
            self.selected_table = 'default'
        self._ui_mapper.set_model(self.table_mappings[self.selected_table])
    
    def change_mapper(self, mapping):
        self._ui_preview_menu._model = mapping
        self.table.set_mapping(mapping)
        
    def select_table(self, selection):
        self.selected_table = None
        if selection:
            self.selected_table = selection.text()
            self.connector.set_table(self.selected_table)
            self._ui_mapper.set_model(self.table_mappings[self.selected_table])
            self.update_preview_data()
    
    def check_list_item(self, item):
        name = item.text()
        if item.checkState() == Qt.Checked:
            self.selected_source_tables.add(name)
        else:
            self.selected_source_tables.discard(name)
        self.update_ok_state()
            
    def update_ok_state(self):
        if self.selected_source_tables:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(False)
    
    def ok_pressed(self):
        mapped_data = {}
        for t in self.selected_source_tables:
            mapping = self.table_mappings[t].get_mappings()
            data, header = self.connector.read_data(t)
            data = read_with_mapping(iter(data), mapping, len(header), header)
            print(data)
        pass
        

    def update_tables(self):
        if self.connector.can_have_multiple_tables:
            tables = self.connector.tables
            for t in tables:
                if t not in self.table_mappings:
                    self.table_mappings[t] = DataMappingListModel([ObjectClassMapping()])
            for k in list(self.table_mappings.keys()):
                if k not in tables:
                    self.table_mappings.pop(k)
            if not tables:
                self._ui_list.clear()
                return
            if not self.selected_table:
                self.selected_table = tables[0]
            self._ui_list.blockSignals(True)
            self._ui_list.clear()
            for t in tables:
                item = QListWidgetItem()
                item.setText(t)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                if t in self.selected_source_tables:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self._ui_list.addItem(item)
            if self.selected_table in tables:
                self._ui_list.setCurrentRow(tables.index(self.selected_table), QItemSelectionModel.SelectCurrent)
            else:
                self._ui_list.clearSelection()
            self._ui_list.blockSignals(False)
            self.update_ok_state()

    def update_preview_data(self):
        data, header = self.connector.preview_data(self.selected_table)
        if data:
            if not header:
                header = list(range(1,len(data[0])+1))
            self.table.set_data(data, header)
        else:
            self.table.set_data([], [])



class TableModel(QAbstractItemModel):
    def __init__(self, headers = [], data = []):
    # def __init__(self, tasks=[[]]):
        super(TableModel, self).__init__()
        self._data = data
        self._headers = headers

    def parent(self, child = QModelIndex()):
        return QModelIndex()

    def index(self, row, column, parent = QModelIndex()):
        return self.createIndex(row, column, parent)

    def set_data(self, data, headers):
        if data and len(data[0]) != len(headers):
            raise ValueError("'data[0]' must be same length as 'headers'")
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self.endResetModel()
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(top_left, bottom_right)

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            else:
                return section

    def row(self, index):
        if index.isValid():
            return self._data[index.row()]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]


class MappingPreviewModel(TableModel):
    def __init__(self, headers = [], data = []):
        super(MappingPreviewModel, self).__init__(headers, data)
        self._mapping = None
        self._data_changed_signal = None
    
    def set_mapping(self, mapping):
        if not self._data_changed_signal is None and self._model:
            self._model.dataChanged.disconnect(self.update_colors)
            self._data_changed_signal = None
        self._mapping = mapping
        self._mapping.dataChanged.connect(self.update_colors)
        self.update_colors()
    
    def update_colors(self):
        self.dataChanged.emit(QModelIndex,QModelIndex, [Qt.BackgroundColorRole])

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return super(MappingPreviewModel, self).data(index, role)
        elif role == Qt.BackgroundColorRole and self._mapping:
            mapping = self._mapping._model
            if mapping.parameters is not None:
                # parameter colors
                if mapping.is_pivoted():
                    # parameter values color
                    if index.row() > mapping.last_pivot_row() and index.column() not in self.mapping_column_ref_int_list():
                        return QColor(1,133,113)
                elif self.index_in_mapping(mapping.parameters.value, index):
                    return QColor(1,133,113)
                if mapping.parameters.extra_dimensions:
                    # parameter extra dimensions color
                    for ed in mapping.parameters.extra_dimensions:
                        if self.index_in_mapping(ed, index):
                            return  QColor(128,205,193)
                if self.index_in_mapping(mapping.parameters.name, index):
                    # parameter name colors
                    return  QColor(128,205,193)
            if self.index_in_mapping(mapping.name, index):
                # class name color
                return  QColor(166,97,26)
            objects = []
            classes = []
            if type(mapping) == ObjectClassMapping:
                objects = [mapping.object]
            else:
                if mapping.objects:
                    objects = mapping.objects
                if mapping.object_classes:
                    classes = mapping.object_classes
            for o in objects:
                # object colors
                if self.index_in_mapping(o, index):
                            return  QColor(223,194,125)
            for c in classes:
                # object colors
                if self.index_in_mapping(c, index):
                            return  QColor(166,97,26)
            
    
    def index_in_mapping(self, mapping, index):
        if type(mapping) != Mapping:
            return False
        if mapping.map_type == 'column':
            ref = mapping.value_reference
            if type(ref) == str:
                # find header reference
                if ref in self._headers:
                    ref = self._headers.index(ref)
            if index.column() == ref:
                if self._mapping._model.is_pivoted():
                    # only rows below pivoted rows
                    if index.row() > self._mapping._model.last_pivot_row():
                        return True
                else:
                    return True
        if mapping.map_type == 'row':
            if index.row() == mapping.value_reference:
                if index.column() not in self.mapping_column_ref_int_list():
                    return True
        return False
    
    def mapping_column_ref_int_list(self):
        if not self._mapping:
            return []
        non_pivoted_columns = self._mapping._model.non_pivoted_columns()
        int_non_piv_cols = []
        for pc in non_pivoted_columns:
            if type(pc) == str:
                if pc in self._headers:
                    pc = self._headers.index(pc)
            int_non_piv_cols.append(pc)
        return int_non_piv_cols
                


class MappingTableMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None
    
    def set_mapping(self, name='', map_type=None, value=None):
        if not self._model:
            return
        mapping = Mapping(map_type=map_type, value_reference=value)
        self._model.set_mapping_from_name(name, mapping)

    def request_menu(self, QPos=None):
        if not self._model:
            return
        indexes = self.parent().selectedIndexes()
        if not indexes:
            return
        self.clear()
        index = indexes[0]
        row = index.row()
        col = index.column()
        
        mapping_names = [self._model.data(self._model.createIndex(i,0), Qt.DisplayRole) for i in range(self._model.rowCount())]
        for i, n in enumerate(mapping_names):
            m = self.addMenu(n)
            col_map = m.addAction(f'Map to row values for column: {col}')
            col_header_map = m.addAction(f'Map to header value for column: {col}')
            row_map = m.addAction(f'Map to column values for row: {row}')
            header_map = m.addAction(f'Map to column headers')
            
            col_map.triggered.connect(lambda n=n,col=col: self.set_mapping(name=n, map_type='column', value=col))
            col_header_map.triggered.connect(lambda n=n,col=col: self.set_mapping(name=n, map_type='column_name', value=col))
            row_map.triggered.connect(lambda n=n,row=row: self.set_mapping(name=n, map_type='row', value=row))
            header_map.triggered.connect(lambda n=n: self.set_mapping(name=n, map_type='row', value=-1))
        
        pPos=self.parent().mapToGlobal(QPoint(5, 20))
        mPos=pPos+QPos
        self.move(mPos)
        self.show()






