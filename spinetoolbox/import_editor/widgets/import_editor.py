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
Contains ImportEditor widget and MappingTableMenu.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from copy import deepcopy
from PySide2.QtCore import QAbstractListModel, QItemSelectionModel, QModelIndex, QObject, QPoint, Qt, Signal, Slot
from PySide2.QtWidgets import QMenu
from spinedb_api import ObjectClassMapping, dict_to_map, mapping_from_dict
from ..commands import SetTableChecked
from ...widgets.custom_menus import CustomContextMenu
from ..mvcmodels.mapping_list_model import MappingListModel
from ..mvcmodels.source_data_table_model import SourceDataTableModel
from ...spine_io.type_conversion import value_to_convert_spec


class ImportEditor(QObject):
    """
    Provides an interface for defining one or more Mappings associated to a data Source (CSV file, Excel file, etc).
    """

    table_checked = Signal()
    mapped_data_ready = Signal(dict, list)
    mapping_model_changed = Signal(object)
    preview_data_updated = Signal(int)

    def __init__(self, ui, ui_error, undo_stack, connector, mapping_settings):
        """
        Args:
            ui (QWidget): importer window's UI
            ui_error (QErrorMessage): error dialog
            undo_stack (QUndoStack): undo stack
            connector (ConnectionManager): a connector
            mapping_settings (dict): serialized mappings
        """
        super().__init__()
        self._ui = ui
        self._ui_error = ui_error

        # state
        self._connector = connector
        self._selected_table = None
        self._preview_table_model = SourceDataTableModel()
        self._selected_source_tables = set()
        self._table_mappings = {}
        self._table_updating = False
        self._data_updating = False
        self._copied_mapping = None
        self._copied_options = {}
        self._ui_preview_menu = None
        self._undo_stack = undo_stack
        self._source_table_model = _SourceTableListModel(self._undo_stack)
        self._restore_mappings(mapping_settings)
        self._ui.source_list.setModel(self._source_table_model)
        # create ui
        self._ui.source_data_table.setModel(self._preview_table_model)
        self._ui_preview_menu = MappingTableMenu(self._ui.source_data_table)
        self._ui.dockWidget_source_options.setWidget(self._connector.option_widget())
        self._ui.source_data_table.verticalHeader().display_all = False

        # connect signals
        self._ui.source_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.source_list.customContextMenuRequested.connect(self.show_source_table_context_menu)
        self._ui.source_list.selectionModel().currentChanged.connect(self._change_selected_table)
        self._ui.source_data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.source_data_table.customContextMenuRequested.connect(self._ui_preview_menu.request_menu)

        # signals for connector
        self._connector.connectionReady.connect(self.request_new_tables_from_connector)
        self._connector.dataReady.connect(self.update_preview_data)
        self._connector.tablesReady.connect(self.update_tables)
        self._connector.mappedDataReady.connect(self.mapped_data_ready.emit)
        # when data is ready set loading status to False.
        self._connector.connectionReady.connect(lambda: self.set_loading_status(False))
        self._connector.dataReady.connect(lambda: self.set_loading_status(False))
        self._connector.tablesReady.connect(lambda: self.set_loading_status(False))
        self._connector.mappedDataReady.connect(lambda: self.set_loading_status(False))
        # when data is getting fetched set loading status to True
        self._connector.fetchingData.connect(lambda: self.set_loading_status(True))
        # set loading status to False if error.
        self._connector.error.connect(lambda: self.set_loading_status(False))

        # current mapping changed
        self._preview_table_model.mapping_changed.connect(self._update_display_row_types)

        # data preview table
        self._preview_table_model.column_types_updated.connect(self._new_column_types)
        self._preview_table_model.row_types_updated.connect(self._new_row_types)

    @property
    def checked_tables(self):
        return self._source_table_model.checked_table_names()

    @Slot(object)
    def set_model(self, model):
        self._ui_preview_menu.set_model(model)

    @Slot(object)
    def set_mapping(self, model):
        self._preview_table_model.set_mapping(model)

    def set_loading_status(self, status):
        """
        Disables/hides widgets while status is True
        """
        self._ui.table_page.setDisabled(status)
        preview_table = 0
        loading_message = 1
        self._ui.source_preview_widget_stack.setCurrentIndex(loading_message if status else preview_table)
        self._ui.dockWidget_mappings.setDisabled(status)
        self._ui.dockWidget_mapping_options.setDisabled(status)
        self._ui.dockWidget_mapping_spec.setDisabled(status)

    @Slot()
    def request_new_tables_from_connector(self):
        """
        Requests new tables data from connector
        """
        self._connector.request_tables()

    @Slot(QModelIndex, QModelIndex)
    def _change_selected_table(self, selected, deselected):
        if not selected.isValid():
            return
        item = self._source_table_model.table_at(selected.row())
        self._select_table(item.name)

    def _select_table(self, table_name):
        """
        Set selected table and request data from connector
        """
        if table_name not in self._table_mappings:
            self._table_mappings[table_name] = MappingListModel([ObjectClassMapping()], table_name, self._undo_stack)
        self.mapping_model_changed.emit(self._table_mappings[table_name])
        # request new data
        self._connector.set_table(table_name)
        self._connector.request_data(table_name, max_rows=100)
        self._selected_table = table_name

    def request_mapped_data(self):
        tables_mappings = {t: self._table_mappings[t].get_mappings() for t in self.checked_tables}
        self._connector.request_mapped_data(tables_mappings, max_rows=-1)

    @Slot(dict)
    def update_tables(self, tables):
        """
        Update list of tables
        """
        new_tables = list()
        for t_name, t_mapping in tables.items():
            if t_name not in self._table_mappings:
                if t_mapping is None:
                    t_mapping = ObjectClassMapping()
                self._table_mappings[t_name] = MappingListModel([t_mapping], t_name, self._undo_stack)
                new_tables.append(t_name)
        for k in list(self._table_mappings.keys()):
            if k not in tables:
                self._table_mappings.pop(k)

        if not tables:
            self._ui.source_list.clear()
            self._ui.source_list.clearSelection()
            return

        # empty tables list and add new tables
        tables_to_select = set(self.checked_tables + new_tables)
        table_items = [_SourceTableItem(name, name in tables_to_select) for name in tables]
        self._source_table_model.reset(table_items)

        # current selected table
        current_index = self._ui.source_list.selectionModel().currentIndex()
        # reselect table if existing otherwise select first table
        if current_index.isValid():
            table_name = self._source_table_model.table_at(current_index.row()).name
            index = self._source_table_model.index(tables.index(table_name), 0)
            self._ui.source_list.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectCurrent)
        elif tables:
            index = self._source_table_model.index(0, 0)
            self._ui.source_list.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectCurrent)
        self.table_checked.emit()

    @Slot(list, list)
    def update_preview_data(self, data, header):
        if data:
            try:
                data = _sanitize_data(data, header)
            except RuntimeError as error:
                self._ui_error.showMessage(str(error))
                self._preview_table_model.reset_model()
                self._preview_table_model.set_horizontal_header_labels([])
                self.preview_data_updated.emit(self._preview_table_model.columnCount())
                return
            if not header:
                header = list(range(1, len(data[0]) + 1))
            self._preview_table_model.reset_model(main_data=data)
            self._preview_table_model.set_horizontal_header_labels(header)
            types = self._connector.table_types.get(self._connector.current_table)
            row_types = self._connector.table_row_types.get(self._connector.current_table)
            for col in range(len(header)):
                col_type = types.get(col, "string")
                self._preview_table_model.set_type(col, value_to_convert_spec(col_type), orientation=Qt.Horizontal)
            for row, row_type in row_types.items():
                self._preview_table_model.set_type(row, value_to_convert_spec(row_type), orientation=Qt.Vertical)
        else:
            self._preview_table_model.reset_model()
            self._preview_table_model.set_horizontal_header_labels([])
        self.preview_data_updated.emit(self._preview_table_model.columnCount())

    def _restore_mappings(self, settings):
        try:
            self._table_mappings = {
                table: MappingListModel([dict_to_map(m) for m in mappings], table, self._undo_stack)
                for table, mappings in settings.get("table_mappings", {}).items()
            }
        except ValueError as error:
            self._ui_error.showMessage(f"{error}")
            return
        table_types = {
            tn: {int(col): value_to_convert_spec(spec) for col, spec in cols.items()}
            for tn, cols in settings.get("table_types", {}).items()
        }
        table_row_types = {
            tn: {int(col): value_to_convert_spec(spec) for col, spec in cols.items()}
            for tn, cols in settings.get("table_row_types", {}).items()
        }
        self._connector.set_table_options(settings.get("table_options", {}))
        self._connector.set_table_types(table_types)
        self._connector.set_table_row_types(table_row_types)
        selected_tables = settings.get("selected_tables")
        if selected_tables is None:
            selected_tables = set(self._table_mappings.keys())
        table_items = [_SourceTableItem(name, name in selected_tables) for name in self._table_mappings]
        self._source_table_model.reset(table_items)

    def get_settings_dict(self):
        """Returns a dictionary with type of connector, connector options for tables,
        mappings for tables, selected tables.

        Returns:
            [Dict] -- dict with settings
        """
        tables = self._source_table_model.table_names()
        selected_tables = self._source_table_model.checked_table_names()

        table_mappings = {
            t: [m.to_dict() for m in mappings.get_mappings()]
            for t, mappings in self._table_mappings.items()
            if t in tables
        }

        table_types = {
            tn: {col: spec.to_json_value() for col, spec in cols.items()}
            for tn, cols in self._connector.table_types.items()
            if cols
            if tn in tables
        }
        table_row_types = {
            tn: {col: spec.to_json_value() for col, spec in cols.items()}
            for tn, cols in self._connector.table_row_types.items()
            if cols and tn in tables
        }

        table_options = {t: o for t, o in self._connector.table_options.items() if t in tables}

        settings = {
            "table_mappings": table_mappings,
            "table_options": table_options,
            "table_types": table_types,
            "table_row_types": table_row_types,
            "selected_tables": selected_tables,
            "source_type": self._connector.source_type,
        }
        return settings

    @Slot()
    def close_connection(self):
        """Close connector connection."""
        self._connector.close_connection()

    @Slot()
    def _new_column_types(self):
        new_types = self._preview_table_model.get_types(orientation=Qt.Horizontal)
        self._connector.set_table_types({self._connector.current_table: new_types})

    @Slot()
    def _new_row_types(self):
        new_types = self._preview_table_model.get_types(orientation=Qt.Vertical)
        self._connector.set_table_row_types({self._connector.current_table: new_types})

    @Slot()
    def _update_display_row_types(self):
        mapping_specification = self._preview_table_model.mapping_specification()
        if mapping_specification.last_pivot_row == -1:
            pivoted_rows = []
        else:
            pivoted_rows = list(range(mapping_specification.last_pivot_row + 1))
        self._ui.source_data_table.verticalHeader().sections_with_buttons = pivoted_rows

    def show_source_table_context_menu(self, pos):
        """Context menu for connection links.

        Args:
            pos (QPoint): Mouse position
        """
        pPos = self._ui.source_list.mapToGlobal(pos)
        item = self._ui.source_list.itemAt(pos)
        table = item.text()
        source_list_menu = TableMenu(self, pPos, bool(self._copied_options), self._copied_mapping is not None)
        source_list_menu.deleteLater()
        option = source_list_menu.get_action()
        if option == "Copy mappings":
            self.copy_mappings(table)
            return
        if option == "Copy options":
            self.copy_options(table)
            return
        if option == "Copy options and mappings":
            self.copy_options(table)
            self.copy_mappings(table)
            return
        if option == "Paste mappings":
            self.paste_mappings(table)
            return
        if option == "Paste options":
            self.paste_options(table)
            return
        if option == "Paste options and mappings":
            self.paste_mappings(table)
            self.paste_options(table)
            return

    def copy_mappings(self, table):
        if table in self._table_mappings:
            self._copied_mapping = [deepcopy(m) for m in self._table_mappings[table].get_mappings()]

    def copy_options(self, table):
        options = self._connector.table_options
        col_types = self._connector.table_types
        row_types = self._connector.table_row_types
        self._copied_options["options"] = deepcopy(options.get(table, {}))
        self._copied_options["col_types"] = deepcopy(col_types.get(table, {}))
        self._copied_options["row_types"] = deepcopy(row_types.get(table, {}))

    def paste_mappings(self, table):
        self._table_mappings[table] = MappingListModel(
            [deepcopy(m) for m in self._copied_mapping], table, self._undo_stack
        )
        if self._selected_table == table:
            self.mapping_model_changed.emit(self._table_mappings[table])

    def paste_options(self, table):
        self._connector.set_table_options({table: deepcopy(self._copied_options.get("options", {}))})
        self._connector.set_table_types({table: deepcopy(self._copied_options.get("col_types", {}))})
        self._connector.set_table_row_types({table: deepcopy(self._copied_options.get("row_types", {}))})
        if self._selected_table == table:
            self._select_table(self._ui.source_list.selectedItems()[0])


class MappingTableMenu(QMenu):
    """
    A context menu for the source data table, to let users define a Mapping from a data table.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None

    def set_model(self, model):
        self._model = model

    def set_mapping(self, name="", map_type=None, value=None):
        if not self._model:
            return
        mapping = mapping_from_dict({"map_type": map_type, "value_reference": value})
        self._model.set_component_mapping_from_name(name, mapping)

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


class TableMenu(CustomContextMenu):
    """
    Menu for tables in data source
    """

    def __init__(self, parent, position, can_paste_option, can_paste_mapping):

        super().__init__(parent, position)
        self.add_action("Copy options")
        self.add_action("Copy mappings")
        self.add_action("Copy options and mappings")
        self.addSeparator()
        self.add_action("Paste options", enabled=can_paste_option)
        self.add_action("Paste mappings", enabled=can_paste_mapping)
        self.add_action("Paste options and mappings", enabled=can_paste_mapping & can_paste_option)


class _SourceTableItem:
    """A list item for :class:`_SourceTableListModel`"""

    def __init__(self, name, checked):
        self.name = name
        self.checked = checked


class _SourceTableListModel(QAbstractListModel):
    """Model for source table lists which supports undo/redo functionality."""

    def __init__(self, undo_stack):
        """
        Args:
            undo_stack (QUndoStack): undo stack
        """
        super().__init__()
        self._tables = []
        self._undo_stack = undo_stack

    def checked_table_names(self):
        return [table.name for table in self._tables if table.checked]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self._tables[index.row()].name
        if role == Qt.CheckStateRole:
            return Qt.Checked if self._tables[index.row()].checked else Qt.Unchecked
        return None

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return None

    def reset(self, items):
        self.beginResetModel()
        self._tables = items
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._tables)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole:
            row = index.row()
            item = self._tables[row]
            checked = value == Qt.Checked
            self._undo_stack.push(SetTableChecked(item.name, self, row, checked))
        return False

    def set_checked(self, row, checked):
        self._tables[row].checked = checked
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [Qt.CheckStateRole])

    def table_at(self, row):
        return self._tables[row]

    def table_names(self):
        return [table.name for table in self._tables]


def _sanitize_data(data, header):
    """Fills empty data cells with None."""
    expected_columns = len(header) if header else max(len(x) for x in data)
    sanitized_data = list()
    for row in data:
        length_diff = expected_columns - len(row)
        if length_diff > 0:
            row = row + length_diff * [None]
        elif length_diff < 0:
            raise RuntimeError("A row contains too many columns of data.")
        sanitized_data.append(row)
    return sanitized_data
