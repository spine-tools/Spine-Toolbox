# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QWidget, QListWidget, QVBoxLayout, QDialogButtonBox, QHBoxLayout, QTableView, QMenu, QListWidgetItem, QErrorMessage, QSplitter
from PySide2.QtCore import Signal, QModelIndex, QAbstractItemModel, Qt, QItemSelectionModel, QPoint
from PySide2.QtGui import QColor

from spine_io.widgets.mapping_widget import MappingWidget, DataMappingListModel
from spinedatabase_api import ObjectClassMapping, Mapping


import sys
sys.path.append("c:/data/GIT/spine-data/spinedatabase_api/")

class ImportPreviewWidget(QWidget):
    rejected = Signal()
    mappedDataReady = Signal(dict, list)
    previewDataUpdated = Signal()
    def __init__(self, connector, parent=None):
        super().__init__(parent)
        
        # state
        self.connector = connector
        self.selected_table = None
        self.table = MappingPreviewModel()
        self.selected_source_tables = set()
        self.table_mappings = {}
        self.table_updating = False
        self.data_updating = False
        
        # create widgets
        self._ui_error = QErrorMessage()
        self._ui_list = QListWidget()
        self._ui_table = QTableView()
        self._ui_table.setModel(self.table)
        self._ui_mapper = MappingWidget()
        self._ui_preview_menu = MappingTableMenu(self._ui_table)

        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # layout
        self.setLayout(QVBoxLayout())
        main_splitter = QSplitter()
        self.layout().addWidget(main_splitter)

        # splitter for layout
        list_layout = QVBoxLayout()
        preview_layout = QVBoxLayout()
        mapping_layout = QVBoxLayout()
        list_widget = QWidget()
        preview_widget = QWidget()
        mapping_widget = QWidget()
        list_widget.setLayout(list_layout)
        preview_widget.setLayout(preview_layout)
        mapping_widget.setLayout(mapping_layout)
        main_splitter.addWidget(list_widget)
        main_splitter.addWidget(preview_widget)
        main_splitter.addWidget(mapping_widget)
        
        
        mapping_layout.addWidget(self._ui_mapper)
        list_layout.addWidget(self._ui_list)
        preview_layout.addWidget(self.connector.option_widget())
        self.layout().addWidget(self._dialog_buttons)
        preview_layout.addWidget(self._ui_table)
        
        # connect signals
        self._ui_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui_table.customContextMenuRequested.connect(self._ui_preview_menu.request_menu)
        
        self._ui_list.currentItemChanged.connect(self.select_table)
        self._ui_list.itemChanged.connect(self.check_list_item)
        
        # signals for connector
        self.connector.connectionReady.connect(self.connection_ready)
        self.connector.dataReady.connect(self.update_preview_data)
        self.connector.tablesReady.connect(self.update_tables)
        self.connector.mappedDataReady.connect(lambda data, errors: self.mappedDataReady.emit(data, errors))
        self.connector.mappedDataReady.connect(self.close_connection)
        self.connector.error.connect(self.handle_connector_error)
        # when data is ready set loading status to False.
        self.connector.connectionReady.connect(lambda: self.set_loading_status(False))
        self.connector.dataReady.connect(lambda: self.set_loading_status(False))
        self.connector.tablesReady.connect(lambda: self.set_loading_status(False))
        self.connector.mappedDataReady.connect(lambda: self.set_loading_status(False))
        # when data is getting fetched set loading status to True
        self.connector.fetchingData.connect(lambda: self.set_loading_status(True))
        # set loading status to False if error.
        self.connector.error.connect(lambda: self.set_loading_status(False))

        # if widget parent is destroyed, close connection of connector
        self.parent().destroyed.connect(self.close_connection)

        # current mapping changed
        self._ui_mapper.mappingChanged.connect(self._ui_preview_menu.set_model)
        self._ui_mapper.mappingChanged.connect(self.table.set_mapping)
        self._ui_mapper.mappingDataChanged.connect(self.table.set_mapping)
        
        # preview new preview data
        self.previewDataUpdated.connect(lambda: self._ui_mapper.set_data_source_column_num(self.table.columnCount()))
        
        # ok button
        self._dialog_buttons.button(QDialogButtonBox.Ok).clicked.connect(self.ok_pressed)
        self._dialog_buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.close_connection)
        self._dialog_buttons.button(QDialogButtonBox.Cancel).clicked.connect(lambda: self.rejected.emit())

    def set_loading_status(self, status):
        """
        Sets widgets enable state
        """
        self._ui_list.setDisabled(status)
        self._ui_table.setDisabled(status)
        self._ui_mapper.setDisabled(status)
        self.connector.option_widget().setDisabled(status)

    def connection_ready(self):
        """
        Requests new tables data from connector
        """
        self.connector.request_tables()

    def select_table(self, selection):
        """
        Set selected table and request data from connector
        """
        if selection:
            self._ui_mapper.set_model(self.table_mappings[selection.text()])
            # request new data
            self.connector.set_table(selection.text())
            self.connector.request_data(selection.text(), max_rows=100)

    def check_list_item(self, item):
        """
        Set the check state of item
        """
        name = item.text()
        if item.checkState() == Qt.Checked:
            self.selected_source_tables.add(name)
        else:
            self.selected_source_tables.discard(name)
        self.update_ok_state()
    
    def handle_connector_error(self, error_message):
        self._ui_error.showMessage(error_message)

    def update_ok_state(self):
        """
        Set enable state of OK button.
        """
        if self.selected_source_tables:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(False)

    def ok_pressed(self):
        tables_mappings = {t: self.table_mappings[t].get_mappings() for t in self.selected_source_tables}
        self.connector.request_mapped_data(tables_mappings, max_rows=None)

    def update_tables(self, tables):
        """
        Update list of tables
        """
        # create and delete mappings for tables
        for t in tables:
            if t not in self.table_mappings:
                self.table_mappings[t] = DataMappingListModel([ObjectClassMapping()])
        for k in list(self.table_mappings.keys()):
            if k not in tables:
                self.table_mappings.pop(k)
        
        if not tables:
            self._ui_list.clear()
            self._ui_list.clearSelection()
            return
        
        # current selected table
        selected = self._ui_list.selectedItems()

        # empty tables list and add new tables
        self._ui_list.blockSignals(True)
        self._ui_list.currentItemChanged.disconnect(self.select_table)
        self._ui_list.clear()
        self._ui_list.clearSelection()
        for t in tables:
            item = QListWidgetItem()
            item.setText(t)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if t in self.selected_source_tables:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self._ui_list.addItem(item)
        self._ui_list.currentItemChanged.connect(self.select_table)
        self._ui_list.blockSignals(False)

        # reselect table if existing
        if selected and selected[0].text() in tables:
            table = selected[0].text()
            self._ui_list.setCurrentRow(tables.index(table), QItemSelectionModel.SelectCurrent)
        self.update_ok_state()

    def update_preview_data(self, data, header):
        if data:
            if not header:
                header = list(range(1,len(data[0])+1))
            self.table.set_data(data, header)
        else:
            self.table.set_data([], [])
        self.previewDataUpdated.emit()
    
    def close_connection(self):
        """
        close connector connection
        """
        self.connector.close_connection()


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
        self._data_changed_signal = self._mapping.dataChanged.connect(self.update_colors)
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
        skip_cols = self._mapping._model.skip_columns
        if skip_cols is None:
            skip_cols = []
        int_non_piv_cols = []
        for pc in set(non_pivoted_columns + skip_cols):
            if type(pc) == str:
                if pc in self._headers:
                    pc = self._headers.index(pc)
                else:
                    continue
            int_non_piv_cols.append(pc)
        
        return int_non_piv_cols
                


class MappingTableMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None
    
    def set_model(self, model):
        self._model = model
    
    def set_mapping(self, name='', map_type=None, value=None):
        if not self._model:
            return
        mapping = Mapping(map_type=map_type, value_reference=value)
        self._model.set_mapping_from_name(name, mapping)
    
    def ignore_columns(self, columns=[]):
        pass

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
        
        def create_callback(name, map_type, value):
            return lambda : self.set_mapping(name=name, map_type=map_type, value=value)
        
        mapping_names = [self._model.data(self._model.createIndex(i,0), Qt.DisplayRole) for i in range(self._model.rowCount())]
        for i, n in enumerate(mapping_names):
            m = self.addMenu(n)
            col_map = m.addAction(f'Map to row values for column: {col}')
            col_header_map = m.addAction(f'Map to header value for column: {col}')
            row_map = m.addAction(f'Map to column values for row: {row}')
            header_map = m.addAction(f'Map to column headers')

            col_map.triggered.connect(create_callback(name=n, map_type='column', value=col))
            col_header_map.triggered.connect(create_callback(name=n, map_type='column_name', value=col))
            row_map.triggered.connect(create_callback(name=n, map_type='row', value=row))
            header_map.triggered.connect(create_callback(name=n, map_type='row', value=-1))
        
        pPos=self.parent().mapToGlobal(QPoint(5, 20))
        mPos=pPos+QPos
        self.move(mPos)
        self.show()






