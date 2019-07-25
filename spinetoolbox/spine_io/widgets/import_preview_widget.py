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
Contains ImportPreviewWidget class.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from spinedb_api import ObjectClassMapping, Mapping, dict_to_map
from PySide2.QtWidgets import (
    QWidget,
    QListWidget,
    QVBoxLayout,
    QDialogButtonBox,
    QTableView,
    QMenu,
    QListWidgetItem,
    QErrorMessage,
    QSplitter,
)
from PySide2.QtCore import Signal, QModelIndex, Qt, QItemSelectionModel, QPoint
from PySide2.QtGui import QColor
from spine_io.widgets.mapping_widget import MappingWidget, DataMappingListModel
from models import MinimalTableModel


class ImportPreviewWidget(QWidget):
    tableChecked = Signal()
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
        self.connector.mappedDataReady.connect(self.mappedDataReady.emit)
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

    @property
    def checked_tables(self):
        checked_items = []
        for i in range(self._ui_list.count()):
            item = self._ui_list.item(i)
            if item.checkState() == Qt.Checked:
                checked_items.append(item.text())
        return checked_items

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
        self.tableChecked.emit()

    def handle_connector_error(self, error_message):
        self._ui_error.showMessage(error_message)

    def request_mapped_data(self):
        tables_mappings = {t: self.table_mappings[t].get_mappings() for t in self.selected_source_tables}
        self.connector.request_mapped_data(tables_mappings, max_rows=-1)

    def update_tables(self, tables):
        """
        Update list of tables
        """
        # create and delete mappings for tables
        if isinstance(tables, list):
            tables = {t: None for t in tables}
        for t_name, t_mapping in tables.items():
            if t_name not in self.table_mappings:
                if t_mapping is None:
                    t_mapping = ObjectClassMapping()
                else:
                    # add table to selected if connector gave a mapping object
                    # for the table
                    self.selected_source_tables.add(t_name)
                self.table_mappings[t_name] = DataMappingListModel([t_mapping])
        for k in list(self.table_mappings.keys()):
            if k not in tables:
                self.table_mappings.pop(k)

        if not tables:
            self._ui_list.clear()
            self._ui_list.clearSelection()
            return

        # current selected table
        selected = self._ui_list.selectedItems()
        self.selected_source_tables = set(tables.keys()).difference(self.selected_source_tables)

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

        # reselect table if existing otherwise select first table
        if selected and selected[0].text() in tables:
            table = selected[0].text()
            self._ui_list.setCurrentRow(tables.index(table), QItemSelectionModel.SelectCurrent)
        elif tables:
            # select first item
            self._ui_list.setCurrentRow(0, QItemSelectionModel.SelectCurrent)
        if self._ui_list.selectedItems():
            self.select_table(self._ui_list.selectedItems()[0])
        self.tableChecked.emit()

    def update_preview_data(self, data, header):
        if data:
            if not header:
                header = list(range(len(data[0])))
            self.table.reset_model(main_data=data)
            self.table.set_horizontal_header_labels(header)
        else:
            self.table.reset_model()
            self.table.set_horizontal_header_labels([])
        self.previewDataUpdated.emit()

    def use_settings(self, settings):
        self.table_mappings = {
            table: DataMappingListModel([dict_to_map(m) for m in mappings])
            for table, mappings in settings.get("table_mappings", {}).items()
        }
        self.connector.set_table_options(settings.get("table_options", {}))
        self.selected_source_tables.update(set(settings.get("selected_tables", [])))
        if self._ui_list.selectedItems():
            self.select_table(self._ui_list.selectedItems()[0])

    def get_settings_dict(self):
        """Returns a dictionary with type of connector, connector options for tables, mappings for tables, selected tables.
        
        Returns:
            [Dict] -- dict with settings
        """
        table_mappings = {
            t: [m.to_dict() for m in mappings.get_mappings()] for t, mappings in self.table_mappings.items()
        }

        settings = {
            "table_mappings": table_mappings,
            "table_options": self.connector.table_options,
            "selected_tables": list(self.selected_source_tables),
            "source": self.connector.source,
            "source_type": self.connector.source_type,
        }
        return settings

    def close_connection(self):
        """
        close connector connection
        """
        self.connector.close_connection()


class MappingPreviewModel(MinimalTableModel):
    """Table model that shows different backgroundcolor depending on mapping
    """

    def __init__(self, parent=None):
        super(MappingPreviewModel, self).__init__(parent)
        self.default_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        self._mapping = None
        self._data_changed_signal = None

    def set_mapping(self, mapping):
        """Set mapping to display colors from
        
        Arguments:
            mapping {MappingTableModel} -- mapping model
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


class MappingTableMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None

    def set_model(self, model):
        self._model = model

    def set_mapping(self, name="", map_type=None, value=None):
        if not self._model:
            return
        mapping = Mapping(map_type=map_type, value_reference=value)
        self._model.set_mapping_from_name(name, mapping)

    def ignore_columns(self, columns=None):
        # TODO: implement this, add selected columns to ignored columns in current mapping.
        if columns is None:
            columns = []

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
            return lambda: self.set_mapping(name=name, map_type=map_type, value=value)

        mapping_names = [
            self._model.data(self._model.createIndex(i, 0), Qt.DisplayRole) for i in range(self._model.rowCount())
        ]
        for n in mapping_names:
            m = self.addMenu(n)
            col_map = m.addAction(f"Map to column")
            col_header_map = m.addAction(f"Map to header")
            row_map = m.addAction(f"Map to row")
            header_map = m.addAction(f"Map to all headers")

            col_map.triggered.connect(create_callback(name=n, map_type="column", value=col))
            col_header_map.triggered.connect(create_callback(name=n, map_type="column_name", value=col))
            row_map.triggered.connect(create_callback(name=n, map_type="row", value=row))
            header_map.triggered.connect(create_callback(name=n, map_type="row", value=-1))

        pPos = self.parent().mapToGlobal(QPoint(5, 20))
        mPos = pPos + QPos
        self.move(mPos)
        self.show()
