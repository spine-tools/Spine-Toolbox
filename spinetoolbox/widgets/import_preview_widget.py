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
Contains ImportPreviewWidget, and MappingTableMenu classes.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from spinedb_api import ObjectClassMapping, Mapping, dict_to_map
from PySide2.QtWidgets import QWidget, QVBoxLayout, QMenu, QListWidgetItem, QErrorMessage
from PySide2.QtCore import Signal, Qt, QItemSelectionModel, QPoint
from .mapping_widget import MappingWidget
from ..spine_io.io_models import MappingPreviewModel, MappingListModel


class ImportPreviewWidget(QWidget):
    """
    A Widget for defining one or more Mappings associated to a data Source (CSV file, Excel file, etc).
    Currently it's being embedded in ImportDialog and ImportPreviewWindow.

    Args:
        connector (ConnectionManager)
    """

    tableChecked = Signal()
    mappedDataReady = Signal(dict, list)
    previewDataUpdated = Signal()

    def __init__(self, connector, parent=None):
        from ..ui.import_preview import Ui_ImportPreview

        super().__init__(parent)

        # state
        self.connector = connector
        self.selected_table = None
        self.table = MappingPreviewModel()
        self.selected_source_tables = set()
        self.table_mappings = {}
        self.table_updating = False
        self.data_updating = False

        # create ui
        self._ui = Ui_ImportPreview()
        self._ui.setupUi(self)
        self._ui.source_data_table.setModel(self.table)
        self._ui_error = QErrorMessage()
        self._ui_preview_menu = MappingTableMenu(self._ui.source_data_table)
        self._ui.top_source_splitter.addWidget(self.connector.option_widget())
        self._ui.mappings_box.setLayout(QVBoxLayout())
        self._ui_mapper = MappingWidget()
        self._ui.mappings_box.layout().addWidget(self._ui_mapper)

        # connect signals
        self._ui.source_data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.source_data_table.customContextMenuRequested.connect(self._ui_preview_menu.request_menu)
        self._ui.source_list.currentItemChanged.connect(self.select_table)
        self._ui.source_list.itemChanged.connect(self.check_list_item)

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
        for i in range(self._ui.source_list.count()):
            item = self._ui.source_list.item(i)
            if item.checkState() == Qt.Checked:
                checked_items.append(item.text())
        return checked_items

    def set_loading_status(self, status):
        """
        Sets widgets enable state
        """
        self._ui.source_list.setDisabled(status)
        self._ui.source_preview_widget_stack.setCurrentIndex(1 if status else 0)
        self._ui_mapper.setDisabled(status)

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
                self.table_mappings[t_name] = MappingListModel([t_mapping])
        for k in list(self.table_mappings.keys()):
            if k not in tables:
                self.table_mappings.pop(k)

        if not tables:
            self._ui.source_list.clear()
            self._ui.source_list.clearSelection()
            return

        # current selected table
        selected = self._ui.source_list.selectedItems()
        self.selected_source_tables = set(tables.keys()).intersection(self.selected_source_tables)

        # empty tables list and add new tables
        self._ui.source_list.blockSignals(True)
        self._ui.source_list.currentItemChanged.disconnect(self.select_table)
        self._ui.source_list.clear()
        self._ui.source_list.clearSelection()
        for t in tables:
            item = QListWidgetItem()
            item.setText(t)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if t in self.selected_source_tables:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self._ui.source_list.addItem(item)
        self._ui.source_list.currentItemChanged.connect(self.select_table)
        self._ui.source_list.blockSignals(False)

        # reselect table if existing otherwise select first table
        if selected and selected[0].text() in tables:
            table = selected[0].text()
            self._ui.source_list.setCurrentRow(tables.index(table), QItemSelectionModel.SelectCurrent)
        elif tables:
            # select first item
            self._ui.source_list.setCurrentRow(0, QItemSelectionModel.SelectCurrent)
        if self._ui.source_list.selectedItems():
            self.select_table(self._ui.source_list.selectedItems()[0])
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
            table: MappingListModel([dict_to_map(m) for m in mappings])
            for table, mappings in settings.get("table_mappings", {}).items()
        }
        self.connector.set_table_options(settings.get("table_options", {}))
        self.selected_source_tables.update(set(settings.get("selected_tables", [])))
        if self._ui.source_list.selectedItems():
            self.select_table(self._ui.source_list.selectedItems()[0])

    def get_settings_dict(self):
        """Returns a dictionary with type of connector, connector options for tables,
        mappings for tables, selected tables.

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
            "source_type": self.connector.source_type,
        }
        return settings

    def close_connection(self):
        """
        close connector connection
        """
        self.connector.close_connection()


class MappingTableMenu(QMenu):
    """
    A menu to let users define a Mapping from a data table.
    Used to generate the context menu for ImportPreviewWidget._ui_table
    """

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

        menus = [
            ("Map column to...", "column", col),
            ("Map header to...", "column_name", col),
            ("Map row to...", "row", row),
            ("Map all headers to...", "row", -1),
        ]

        for title, map_type, value in menus:
            m = self.addMenu(title)
            for name in mapping_names:
                m.addAction(name).triggered.connect(create_callback(name=name, map_type=map_type, value=value))

        pPos = self.parent().mapToGlobal(QPoint(5, 20))
        mPos = pPos + QPos
        self.move(mPos)
        self.show()
