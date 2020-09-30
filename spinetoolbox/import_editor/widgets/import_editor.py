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
from PySide2.QtCore import QItemSelectionModel, QModelIndex, QObject, QPoint, Qt, Signal, Slot
from PySide2.QtWidgets import QMenu
from spinedb_api import ObjectClassMapping
from .options_widget import OptionsWidget
from ..commands import PasteMappings, PasteOptions
from ..mvcmodels.mapping_list_model import MappingListModel
from ..mvcmodels.mapping_specification_model import MappingSpecificationModel
from ..mvcmodels.source_data_table_model import SourceDataTableModel
from ..mvcmodels.source_table_list_model import SourceTableItem, SourceTableListModel
from spine_items.spine_io.type_conversion import value_to_convert_spec
from ...widgets.custom_menus import CustomContextMenu


class ImportEditor(QObject):
    """
    Provides an interface for defining one or more Mappings associated to a data Source (CSV file, Excel file, etc).
    """

    table_checked = Signal()
    mapped_data_ready = Signal(dict, list)
    source_table_selected = Signal(str, object)
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
        self._table_mappings = {}
        self._table_updating = False
        self._data_updating = False
        self._copied_mapping = None
        self._copied_options = {}
        self._ui_preview_menu = None
        self._undo_stack = undo_stack
        self._preview_table_model = SourceDataTableModel()
        self._source_table_model = SourceTableListModel(self._undo_stack)
        self._restore_mappings(mapping_settings)
        self._ui.source_list.setModel(self._source_table_model)
        # create ui
        self._ui.source_data_table.setModel(self._preview_table_model)
        self._ui_preview_menu = MappingTableMenu(self._ui.source_data_table)
        self._ui_options_widget = OptionsWidget(self._connector, self._undo_stack)
        self._ui.dockWidget_source_options.setWidget(self._ui_options_widget)
        self._ui.source_data_table.verticalHeader().display_all = False

        # connect signals
        self._ui_options_widget.about_to_undo.connect(self.select_table)
        self._ui.source_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.source_list.customContextMenuRequested.connect(self.show_source_table_context_menu)
        self._ui.source_list.selectionModel().currentChanged.connect(self._change_selected_table)
        self._ui.source_data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._ui.source_data_table.customContextMenuRequested.connect(self._ui_preview_menu.request_menu)

        # signals for connector
        self._connector.connection_ready.connect(self.request_new_tables_from_connector)
        self._connector.data_ready.connect(self.update_preview_data)
        self._connector.tables_ready.connect(self.update_tables)
        self._connector.mapped_data_ready.connect(self.mapped_data_ready.emit)
        # when data is ready set loading status to False.
        self._connector.connection_ready.connect(lambda: self.set_loading_status(False))
        self._connector.data_ready.connect(lambda: self.set_loading_status(False))
        self._connector.tables_ready.connect(lambda: self.set_loading_status(False))
        self._connector.mapped_data_ready.connect(lambda: self.set_loading_status(False))
        # when data is getting fetched set loading status to True
        self._connector.fetching_data.connect(lambda: self.set_loading_status(True))
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
        """
        Sets selected table and requests data from connector
        """
        item = self._source_table_model.table_at(selected.row())
        if item.name not in self._table_mappings:
            self._table_mappings[item.name] = MappingListModel([ObjectClassMapping()], item.name, self._undo_stack)
        self.source_table_selected.emit(item.name, self._table_mappings[item.name])
        self._connector.set_table(item.name)
        self._connector.request_data(item.name, max_rows=100)

    def _select_table_row(self, row):
        selection_model = self._ui.source_list.selectionModel()
        index = self._source_table_model.index(row, 0)
        selection_model.setCurrentIndex(index, QItemSelectionModel.Select)

    @Slot(str)
    def select_table(self, table):
        """
        Selects given table in the source table list.

        Args:
            table (str): source table name
        """
        index = self._source_table_model.table_index(table)
        selection_model = self._ui.source_list.selectionModel()
        if selection_model.hasSelection() and index == selection_model.selection().indexes()[0]:
            return
        selection_model.setCurrentIndex(index, QItemSelectionModel.ClearAndSelect)

    def request_mapped_data(self):
        tables_mappings = {t: self._table_mappings[t].get_mappings() for t in self.checked_tables}
        self._connector.request_mapped_data(tables_mappings, max_rows=-1)

    @Slot(dict)
    def update_tables(self, tables):
        """
        Updates list of tables
        """
        new_tables = list()
        for t_name, t_mapping in tables.items():
            if t_name not in self._table_mappings:
                if t_mapping is None:
                    t_mapping = ObjectClassMapping()
                specification = MappingSpecificationModel(t_name, "", t_mapping, self._undo_stack)
                self._table_mappings[t_name] = MappingListModel([specification], t_name, self._undo_stack)
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
        table_items = [SourceTableItem(name, name in tables_to_select) for name in tables]
        self._source_table_model.reset(table_items)

        # current selected table
        current_index = self._ui.source_list.selectionModel().currentIndex()
        # reselect table if existing otherwise select first table
        if current_index.isValid():
            self._select_table_row(current_index.row())
        elif tables:
            self._select_table_row(0)
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
                table: MappingListModel(
                    [MappingSpecificationModel.from_dict(m, table, self._undo_stack) for m in mapping_specifications],
                    table,
                    self._undo_stack,
                )
                for table, mapping_specifications in settings.get("table_mappings", {}).items()
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
        table_items = [SourceTableItem(name, name in selected_tables) for name in self._table_mappings]
        self._source_table_model.reset(table_items)

    def import_mappings(self, mappings_dict):
        """
        Restores mappings from a dict.

        Args:
            mappings_dict (dict): serialized mappings
        """
        current = self._ui.source_list.selectionModel().currentIndex()
        self._restore_mappings(mappings_dict)
        self._ui.source_list.selectionModel().setCurrentIndex(current, QItemSelectionModel.ClearAndSelect)

    def get_settings_dict(self):
        """Returns a dictionary with type of connector, connector options for tables,
        mappings for tables, selected tables.

        Returns:
            dict: dict with settings
        """
        tables = self._source_table_model.table_names()
        selected_tables = self._source_table_model.checked_table_names()

        table_mappings = {
            t: [m.to_dict() for m in mappings.mapping_specifications]
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
        if mapping_specification is None:
            return
        if mapping_specification.last_pivot_row == -1:
            pivoted_rows = []
        else:
            pivoted_rows = list(range(mapping_specification.last_pivot_row + 1))
        self._ui.source_data_table.verticalHeader().sections_with_buttons = pivoted_rows

    @Slot(QPoint)
    def show_source_table_context_menu(self, pos):
        """
        Shows context menu for source tables.

        Args:
            pos (QPoint): Mouse position
        """
        global_pos = self._ui.source_list.mapToGlobal(pos)
        index = self._ui.source_list.indexAt(pos)
        table = index.data()
        source_list_menu = TableMenu(
            self._ui.source_list, global_pos, bool(self._copied_options), self._copied_mapping is not None
        )
        option = source_list_menu.get_action()
        source_list_menu.deleteLater()
        if option == "Copy mappings":
            self._copied_mapping = self._copy_mappings(table)
            return
        if option == "Copy options":
            self._copied_options = self._options_to_dict(table)
            return
        if option == "Copy options and mappings":
            self._copied_options = self._options_to_dict(table)
            self._copied_mapping = self._copy_mappings(table)
            return
        if option == "Paste mappings":
            previous = self._copy_mappings(table)
            self._undo_stack.push(PasteMappings(self, table, self._copied_mapping, previous))
            return
        if option == "Paste options":
            previous = self._options_to_dict(table)
            self._undo_stack.push(PasteOptions(self, table, self._copied_options, previous))
            return
        if option == "Paste options and mappings":
            previous_mappings = [deepcopy(m) for m in self._table_mappings[table].get_mappings()]
            previous_options = self._options_to_dict(table)
            self._undo_stack.beginMacro("paste options and mappings")
            self._undo_stack.push(PasteMappings(self, table, self._copied_mapping, previous_mappings))
            self._undo_stack.push(PasteOptions(self, table, self._copied_options, previous_options))
            self._undo_stack.endMacro()
            return

    def _copy_mappings(self, table):
        """
        Copies the mappings of the given source table.

        Args:
            table (str): source table name

        Returns:
            dict: copied mappings
        """
        mapping_list = self._table_mappings.get(table)
        if mapping_list is None:
            return {}
        return {
            specification.mapping_name: deepcopy(specification.mapping)
            for specification in mapping_list.mapping_specifications
        }

    def _options_to_dict(self, table):
        """
        Serializes mapping options to a dict.

        Args:
            table (str): source table name

        Returns:
            dict: serialized options
        """
        options = self._connector.table_options
        col_types = self._connector.table_types
        row_types = self._connector.table_row_types
        all_options = dict()
        all_options["options"] = deepcopy(options.get(table, {}))
        all_options["col_types"] = deepcopy(col_types.get(table, {}))
        all_options["row_types"] = deepcopy(row_types.get(table, {}))
        return all_options

    def paste_mappings(self, table, mappings):
        """
        Pastes mappings to given table

        Args:
            table (str): source table name
            mappings (dict): mappings to paste
        """
        self._table_mappings[table].reset(deepcopy(mappings), table)
        index = self._ui.source_list.selectionModel().currentIndex()
        current_table = index.data()
        if table == current_table:
            self.source_table_selected.emit(table, self._table_mappings[table])
        else:
            self.select_table(table)

    def paste_options(self, table, options):
        """
        Pastes all mapping options to given table.

        Args:
            table (str): source table name
            options (dict): options
        """
        self._connector.set_table_options({table: deepcopy(options.get("options", {}))})
        self._connector.set_table_types({table: deepcopy(options.get("col_types", {}))})
        self._connector.set_table_row_types({table: deepcopy(options.get("row_types", {}))})
        self.select_table(table)


class MappingTableMenu(QMenu):
    """
    A context menu for the source data table, to let users define a Mapping from a data table.
    """

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent)
        self._model = None

    def set_model(self, model):
        """
        Sets target mapping specification.

        Args:
            model (MappingSpecificationModel): mapping specification
        """
        self._model = model

    def set_mapping(self, name="", map_type=None, value=None):
        if self._model is None:
            return
        self._model.change_component_mapping(name, map_type, value)

    def request_menu(self, pos=None):
        if not self._model:
            return
        indexes = self.parent().selectedIndexes()
        if not indexes:
            return
        self.clear()
        index = indexes[0]
        row = index.row() + 1
        col = index.column() + 1

        def create_callback(name, map_type, value):
            return lambda: self.set_mapping(name, map_type, value)

        mapping_names = [
            self._model.data(self._model.createIndex(i, 0), Qt.DisplayRole) for i in range(self._model.rowCount())
        ]

        menus = [
            ("Map column to...", "Column", col),
            ("Map header to...", "Column Header", col),
            ("Map row to...", "Row", row),
            ("Map all headers to...", "Headers", 0),
        ]

        for title, map_type, value in menus:
            m = self.addMenu(title)
            for name in mapping_names:
                m.addAction(name).triggered.connect(create_callback(name, map_type, value))

        global_pos = self.parent().mapToGlobal(QPoint(5, 20))
        menu_pos = global_pos + pos
        self.move(menu_pos)
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
