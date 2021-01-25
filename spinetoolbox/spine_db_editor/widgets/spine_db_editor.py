######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the SpineDBEditor class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import os
import json
from sqlalchemy.engine.url import URL
from PySide2.QtWidgets import (
    QMainWindow,
    QErrorMessage,
    QDockWidget,
    QMessageBox,
    QMenu,
    QTreeView,
    QTableView,
    QTabBar,
)
from PySide2.QtCore import Qt, Signal, Slot, QTimer
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QKeySequence, QIcon
from spinedb_api import (
    import_data,
    export_data,
    ParameterValueEncoder,
    create_new_spine_database,
    DiffDatabaseMapping,
    SpineDBAPIError,
    SpineDBVersionError,
    Asterisk,
)
from spine_engine.spine_io.exporters.excel import export_spine_database_to_xlsx
from spine_engine.spine_io.importers.excel_reader import get_mapped_data_from_xlsx
from .custom_menus import MainMenu
from .mass_select_items_dialogs import MassRemoveItemsDialog, MassExportItemsDialog
from .parameter_view_mixin import ParameterViewMixin
from .tree_view_mixin import TreeViewMixin
from .graph_view_mixin import GraphViewMixin
from .tabular_view_mixin import TabularViewMixin
from .db_session_history_dialog import DBSessionHistoryDialog
from .url_toolbar import UrlToolBar
from ...widgets.notification import NotificationStack
from ...helpers import (
    get_save_file_name_in_last_dir,
    get_open_file_name_in_last_dir,
    format_string_list,
    call_on_focused_widget,
    busy_effect,
    CharIconEngine,
)
from ...widgets.parameter_value_editor import ParameterValueEditor
from ...widgets.custom_qwidgets import ToolBarWidgetAction
from ...spine_db_parcel import SpineDBParcel
from ...config import MAINWINDOW_SS, APPLICATION_PATH


class SpineDBEditorBase(QMainWindow):
    """Base class for SpineDBEditor (i.e. Spine database editor)."""

    msg = Signal(str)
    link_msg = Signal(str, "QVariant")
    msg_error = Signal(str)
    dirty_changed = Signal(bool)
    file_exported = Signal(str)
    sqlite_file_exported = Signal(str)

    def __init__(self, db_mngr):
        """Initializes form.

        Args:
            db_mngr (SpineDBManager): The manager to use
        """
        super().__init__(flags=Qt.Window)
        from ..ui.spine_db_editor_window import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        self.db_mngr = db_mngr
        self.db_maps = []
        self.db_urls = []
        self.db_url = None
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.takeCentralWidget()
        self.url_toolbar = UrlToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.url_toolbar)
        self.setStyleSheet(MAINWINDOW_SS)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.qsettings = self.db_mngr.qsettings
        self.err_msg = QErrorMessage(self)
        self.err_msg.setWindowTitle("Error")
        self.err_msg.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.notification_stack = NotificationStack(self)
        self.silenced = False
        fm = QFontMetrics(QFont("", 0))
        self.default_row_height = 1.2 * fm.lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        self.settings_group = "spineDBEditor"
        self.undo_action = None
        self.redo_action = None
        self.ui.actionUndo.setShortcuts(QKeySequence.Undo)
        self.ui.actionRedo.setShortcuts(QKeySequence.Redo)
        self.update_commit_enabled()
        self.setContextMenuPolicy(Qt.NoContextMenu)

    @property
    def toolbox(self):
        return self.db_mngr.parent()

    @property
    def settings_subgroup(self):
        return ";".join(self.db_urls)

    @property
    def db_names(self):
        return ", ".join([f"{db_map.codename}" for db_map in self.db_maps])

    @property
    def first_db_map(self):
        return self.db_maps[0]

    @property
    def db_url_codenames(self):
        return {db_map.db_url: db_map.codename for db_map in self.db_maps}

    def load_db_urls(self, db_url_codenames, create=False, update_history=True):
        if not db_url_codenames:
            return
        if not self.tear_down():
            return
        self.db_maps = []
        for url, codename in db_url_codenames.items():
            db_map = self.db_mngr.get_db_map(url, self, codename=codename, create=create)
            if db_map is not None:
                self.db_maps.append(db_map)
        if not self.db_maps:
            return
        self.db_urls = [db_map.db_url for db_map in self.db_maps]
        self.url_toolbar.set_current_urls(self.db_urls)
        self.db_url = self.db_urls[0]
        self.db_mngr.register_listener(self, *self.db_maps)
        self.init_models()
        self.init_add_undo_redo_actions()
        self.fetch_db_maps()
        self.restore_ui()
        if update_history:
            self.url_toolbar.add_urls_to_history(self.db_urls)

    def init_add_undo_redo_actions(self):
        new_undo_action = self.db_mngr.undo_action[self.first_db_map]
        new_redo_action = self.db_mngr.redo_action[self.first_db_map]
        self._replace_undo_redo_actions(new_undo_action, new_redo_action)

    def fetch_db_maps(self, *db_maps):
        if not db_maps:
            db_maps = self.db_maps
        fetcher = self.db_mngr.get_fetcher(self)
        fetcher.fetch(db_maps)
        self.setWindowTitle(f"{self.db_names}")

    @Slot(bool)
    def load_previous_urls(self, _=False):
        urls = self.url_toolbar.get_previous_urls()
        self.load_db_urls({url: None for url in urls}, update_history=False)

    @Slot(bool)
    def load_next_urls(self, _=False):
        urls = self.url_toolbar.get_next_urls()
        self.load_db_urls({url: None for url in urls}, update_history=False)

    @Slot(bool)
    def open_db_file(self, _=False):
        self.qsettings.beginGroup(self.settings_group)
        file_path, _ = get_open_file_name_in_last_dir(
            self.qsettings, "openSQLiteUrl", self, "Open SQLite file", self._get_base_dir(), "SQLite (*.sqlite)"
        )
        self.qsettings.endGroup()
        if not file_path:
            return
        url = "sqlite:///" + file_path
        self.load_db_urls({url: None})

    @Slot(bool)
    def create_db_file(self, _=False):
        self.qsettings.beginGroup(self.settings_group)
        file_path, _ = get_save_file_name_in_last_dir(
            self.qsettings, "createSQLiteUrl", self, "Create SQLite file", self._get_base_dir(), "SQLite (*.sqlite)"
        )
        self.qsettings.endGroup()
        if not file_path:
            return
        url = "sqlite:///" + file_path
        self.load_db_urls({url: None}, create=True)

    def _make_docks_menu(self):
        """Returns a menu with all dock toggle/view actions. Called by ``self.add_main_menu()``.

        Returns:
            QMenu
        """
        menu = QMenu(self)
        menu.addAction(self.ui.dockWidget_relationship_tree.toggleViewAction())
        menu.addSeparator()
        menu.addAction(self.ui.dockWidget_object_parameter_value.toggleViewAction())
        menu.addAction(self.ui.dockWidget_object_parameter_definition.toggleViewAction())
        menu.addAction(self.ui.dockWidget_relationship_parameter_value.toggleViewAction())
        menu.addAction(self.ui.dockWidget_relationship_parameter_definition.toggleViewAction())
        menu.addSeparator()
        menu.addAction(self.ui.dockWidget_pivot_table.toggleViewAction())
        menu.addAction(self.ui.dockWidget_frozen_table.toggleViewAction())
        menu.addSeparator()
        menu.addAction(self.ui.dockWidget_entity_graph.toggleViewAction())
        menu.addSeparator()
        menu.addAction(self.ui.dockWidget_tool_feature_tree.toggleViewAction())
        menu.addAction(self.ui.dockWidget_parameter_value_list.toggleViewAction())
        menu.addAction(self.ui.dockWidget_alternative_scenario_tree.toggleViewAction())
        menu.addAction(self.ui.dockWidget_parameter_tag.toggleViewAction())
        menu.addSeparator()
        menu.addAction(self.ui.dockWidget_exports.toggleViewAction())
        return menu

    def add_main_menu(self):
        """Adds a menu with main actions to toolbar."""
        menu = MainMenu(self)
        file_action = ToolBarWidgetAction("File", menu)
        file_action.tool_bar.addActions([self.ui.actionNew_db_file, self.ui.actionOpen_db_file])
        file_action.tool_bar.addSeparator()
        file_action.tool_bar.addActions([self.ui.actionImport, self.ui.actionExport, self.ui.actionExport_session])
        edit_action = ToolBarWidgetAction("Edit", menu)
        edit_action.tool_bar.addActions([self.ui.actionUndo, self.ui.actionRedo])
        edit_action.tool_bar.addSeparator()
        edit_action.tool_bar.addActions([self.ui.actionCopy, self.ui.actionPaste])
        edit_action.tool_bar.addSeparator()
        edit_action.tool_bar.addAction(self.ui.actionMass_remove_items)
        view_action = ToolBarWidgetAction("View", menu)
        view_action.tool_bar.addActions(
            [self.ui.actionStacked_style, self.ui.actionPivot_style, self.ui.actionGraph_style]
        )
        view_action.tool_bar.addSeparator()
        docks_menu_action = view_action.tool_bar.addAction(QIcon(CharIconEngine("\uf2d0")), "Doc&ks...")
        docks_menu_action.setMenu(self._make_docks_menu())
        docks_menu_button = view_action.tool_bar.widgetForAction(docks_menu_action)
        docks_menu_button.setPopupMode(docks_menu_button.InstantPopup)
        pivot_mode_action = ToolBarWidgetAction("Pivot mode", menu)
        pivot_mode_action.tool_bar.addActions(self.input_type_action_group.actions())
        session_action = ToolBarWidgetAction("Session", menu)
        session_action.tool_bar.addActions([self.ui.actionCommit, self.ui.actionRollback])
        session_action.tool_bar.addSeparator()
        session_action.tool_bar.addAction(self.ui.actionView_history)
        menu.addAction(file_action)
        menu.addSeparator()
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(view_action)
        menu.addSeparator()
        menu.addAction(pivot_mode_action)
        menu.addSeparator()
        menu.addAction(session_action)
        menu.addSeparator()
        menu.addAction(self.ui.actionUser_guide)
        menu.addAction(self.ui.actionSettings)
        menu.aboutToShow.connect(self.refresh_copy_paste_actions)
        menu_action = self.url_toolbar.add_main_menu(menu)
        # Add actions to activate shortcuts
        self.addActions(
            [
                self.ui.actionNew_db_file,
                self.ui.actionOpen_db_file,
                self.ui.actionImport,
                self.ui.actionExport,
                self.ui.actionUndo,
                self.ui.actionRedo,
                self.ui.actionCopy,
                self.ui.actionPaste,
                self.ui.actionCommit,
                self.ui.actionRollback,
                menu_action,
            ]
        )

    def connect_signals(self):
        """Connects signals to slots."""
        # Message signals
        self.msg.connect(self.add_message)
        self.link_msg.connect(self.add_link_msg)
        self.msg_error.connect(self.err_msg.showMessage)
        # Menu actions
        self.ui.actionCommit.triggered.connect(self.commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionView_history.triggered.connect(self.show_history_dialog)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionNew_db_file.triggered.connect(self.create_db_file)
        self.ui.actionOpen_db_file.triggered.connect(self.open_db_file)
        self.ui.actionImport.triggered.connect(self.import_file)
        self.ui.actionExport.triggered.connect(self.show_mass_export_items_dialog)
        self.ui.actionExport_session.triggered.connect(self.export_session)
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionMass_remove_items.triggered.connect(self.show_mass_remove_items_form)

    @Slot(int)
    def update_undo_redo_actions(self, index):
        undo_ages = {db_map: self.db_mngr.undo_stack[db_map].undo_age for db_map in self.db_maps}
        redo_ages = {db_map: self.db_mngr.undo_stack[db_map].redo_age for db_map in self.db_maps}
        undo_ages = {db_map: age for db_map, age in undo_ages.items() if age is not None}
        redo_ages = {db_map: age for db_map, age in redo_ages.items() if age is not None}
        new_undo_action = self.db_mngr.undo_action[max(undo_ages, key=undo_ages.get, default=self.first_db_map)]
        new_redo_action = self.db_mngr.redo_action[max(redo_ages, key=redo_ages.get, default=self.first_db_map)]
        self._replace_undo_redo_actions(new_undo_action, new_redo_action)

    def _replace_undo_redo_actions(self, new_undo_action, new_redo_action):
        if new_undo_action != self.undo_action:
            if self.undo_action:
                self.ui.actionUndo.triggered.disconnect(self.undo_action.triggered)
            self.ui.actionUndo.triggered.connect(new_undo_action.triggered)
            self.undo_action = new_undo_action
        if new_redo_action != self.redo_action:
            if self.redo_action:
                self.ui.actionRedo.triggered.disconnect(self.redo_action.triggered)
            self.ui.actionRedo.triggered.connect(new_redo_action.triggered)
            self.redo_action = new_redo_action
        QTimer.singleShot(0, self._refresh_undo_redo_actions)

    @Slot()
    def _refresh_undo_redo_actions(self):
        self.ui.actionUndo.setEnabled(self.undo_action.isEnabled())
        self.ui.actionUndo.setToolTip(f"<p>{self.undo_action.text()}")
        self.ui.actionRedo.setEnabled(self.redo_action.isEnabled())
        self.ui.actionRedo.setToolTip(f"<p>{self.redo_action.text()}")

    @Slot(bool)
    def update_commit_enabled(self, _clean=False):
        dirty = not all(self.db_mngr.undo_stack[db_map].isClean() for db_map in self.db_maps)
        self.ui.actionExport_session.setEnabled(dirty)
        self.ui.actionCommit.setEnabled(dirty)
        self.ui.actionRollback.setEnabled(dirty)
        self.ui.actionView_history.setEnabled(dirty)
        self.setWindowModified(dirty)
        self.dirty_changed.emit(dirty)

    @Slot(bool)
    def show_history_dialog(self, checked=False):
        dialog = DBSessionHistoryDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    def init_models(self):
        """Initializes models."""
        self.parameter_value_list_model.build_tree()
        for item in self.parameter_value_list_model.visit_all():
            index = self.parameter_value_list_model.index_from_item(item)
            self.ui.treeView_parameter_value_list.expand(index)
        self.ui.treeView_parameter_value_list.resizeColumnToContents(0)
        self.ui.treeView_parameter_value_list.header().hide()

    @Slot(str)
    def add_message(self, msg):
        """Pushes message to notification stack.

        Args:
            msg (str): String to show in the notification
        """
        if self.silenced:
            return
        self.notification_stack.push(msg)

    @Slot(str, "QVariant")
    def add_link_msg(self, msg, open_link=None):
        """Pushes link message to notification stack.

        Args:
            msg (str): String to show in notification
        """
        if self.silenced:
            return
        self.notification_stack.push_link(msg, open_link=open_link)

    @Slot()
    def refresh_copy_paste_actions(self):
        """Runs when menus are about to show.
        Enables or disables actions according to selection status."""
        self.ui.actionCopy.setEnabled(bool(call_on_focused_widget(self, "can_copy")))
        self.ui.actionPaste.setEnabled(bool(call_on_focused_widget(self, "can_paste")))

    @Slot(bool)
    def copy(self, checked=False):
        """Copies data to clipboard."""
        call_on_focused_widget(self, "copy")

    @Slot(bool)
    def paste(self, checked=False):
        """Pastes data from clipboard."""
        call_on_focused_widget(self, "paste")

    @Slot(dict)
    def import_data(self, data):
        self.db_mngr.import_data({db_map: data for db_map in self.db_maps})

    @Slot(bool)
    def import_file(self, checked=False):
        """Import file. It supports SQLite, JSON, and Excel."""
        self.qsettings.beginGroup(self.settings_group)
        file_path, selected_filter = get_open_file_name_in_last_dir(
            self.qsettings,
            "importFileIntoDB",
            self,
            "Import file",
            self._get_base_dir(),
            "SQLite (*.sqlite);; JSON file (*.json);; Excel file (*.xlsx)",
        )
        self.qsettings.endGroup()
        if not file_path:  # File selection cancelled
            return
        if selected_filter.startswith("JSON"):
            self.import_from_json(file_path)
        elif selected_filter.startswith("SQLite"):
            self.import_from_sqlite(file_path)
        elif selected_filter.startswith("Excel"):
            self.import_from_excel(file_path)
        else:
            raise ValueError()

    def import_from_json(self, file_path):
        with open(file_path) as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError as err:
                self.msg_error.emit(f"File {file_path} is not a valid json: {err}")
                return
        self.import_data(data)
        filename = os.path.split(file_path)[1]
        self.msg.emit(f"File {filename} successfully imported.")

    def import_from_sqlite(self, file_path):
        url = URL("sqlite", database=file_path)
        filename = os.path.split(file_path)[1]
        try:
            db_map = DiffDatabaseMapping(url)
        except (SpineDBAPIError, SpineDBVersionError) as err:
            self.msg.emit(f"Could'n import file {filename}: {str(err)}")
            return
        data = export_data(db_map)
        self.import_data(data)
        self.msg.emit(f"File {filename} successfully imported.")

    def import_from_excel(self, file_path):
        filename = os.path.split(file_path)[1]
        try:
            mapped_data, errors = get_mapped_data_from_xlsx(file_path)
        except Exception as err:  # pylint: disable=broad-except
            self.msg.emit(f"Could'n import file {filename}: {str(err)}")
            raise err  # NOTE: This is so the programmer gets to see the traceback
        if errors:
            msg = f"The following errors where found parsing {filename}:" + format_string_list(errors)
            self.msg_error.emit(msg)
        self.import_data(mapped_data)
        self.msg.emit(f"File {filename} successfully imported.")

    @staticmethod
    def _make_data_for_export(db_map_item_ids):
        data = {}
        for db_map, item_ids in db_map_item_ids.items():
            for key, items in export_data(db_map, **item_ids).items():
                data.setdefault(key, []).extend(items)
        return data

    @Slot(bool)
    def show_mass_export_items_dialog(self, checked=False):
        """Shows dialog for user to select dbs and items for export."""
        dialog = MassExportItemsDialog(self, self.db_mngr, *self.db_maps)
        dialog.data_submitted.connect(self.mass_export_items)
        dialog.show()

    @Slot(bool)
    def export_session(self, checked=False):
        """Exports changes made in the current session as reported by DiffDatabaseMapping.
        """
        db_map_diff_ids = {db_map: db_map.diff_ids() for db_map in self.db_maps}
        db_map_obj_cls_ids = {db_map: diff_ids["object_class"] for db_map, diff_ids in db_map_diff_ids.items()}
        db_map_rel_cls_ids = {db_map: diff_ids["relationship_class"] for db_map, diff_ids in db_map_diff_ids.items()}
        db_map_obj_ids = {db_map: diff_ids["object"] for db_map, diff_ids in db_map_diff_ids.items()}
        db_map_rel_ids = {db_map: diff_ids["relationship"] for db_map, diff_ids in db_map_diff_ids.items()}
        db_map_par_val_lst_ids = {
            db_map: diff_ids["parameter_value_list"] for db_map, diff_ids in db_map_diff_ids.items()
        }
        db_map_par_def_ids = {db_map: diff_ids["parameter_definition"] for db_map, diff_ids in db_map_diff_ids.items()}
        db_map_par_val_ids = {db_map: diff_ids["parameter_value"] for db_map, diff_ids in db_map_diff_ids.items()}
        db_map_ent_group_ids = {db_map: diff_ids["entity_group"] for db_map, diff_ids in db_map_diff_ids.items()}
        parcel = SpineDBParcel(self.db_mngr)
        parcel._push_object_class_ids(db_map_obj_cls_ids)
        parcel._push_object_ids(db_map_obj_ids)
        parcel._push_relationship_class_ids(db_map_rel_cls_ids)
        parcel._push_relationship_ids(db_map_rel_ids)
        parcel._push_parameter_definition_ids(db_map_par_def_ids, "object")
        parcel._push_parameter_definition_ids(db_map_par_def_ids, "relationship")
        parcel._push_parameter_value_ids(db_map_par_val_ids, "object")
        parcel._push_parameter_value_ids(db_map_par_val_ids, "relationship")
        parcel._push_parameter_value_list_ids(db_map_par_val_lst_ids)
        parcel._push_object_group_ids(db_map_ent_group_ids)
        self.export_data(parcel.data)

    def mass_export_items(self, db_map_item_types):
        def _ids(t, types):
            return Asterisk if t in types else ()

        db_map_obj_cls_ids = {db_map: _ids("object_class", types) for db_map, types in db_map_item_types.items()}
        db_map_rel_cls_ids = {db_map: _ids("relationship_class", types) for db_map, types in db_map_item_types.items()}
        db_map_obj_ids = {db_map: _ids("object", types) for db_map, types in db_map_item_types.items()}
        db_map_rel_ids = {db_map: _ids("relationship", types) for db_map, types in db_map_item_types.items()}
        db_map_par_val_lst_ids = {
            db_map: _ids("parameter_value_list", types) for db_map, types in db_map_item_types.items()
        }
        db_map_par_def_ids = {
            db_map: _ids("parameter_definition", types) for db_map, types in db_map_item_types.items()
        }
        db_map_par_val_ids = {db_map: _ids("parameter_value", types) for db_map, types in db_map_item_types.items()}
        db_map_ent_group_ids = {db_map: _ids("entity_group", types) for db_map, types in db_map_item_types.items()}
        db_map_alt_ids = {db_map: _ids("alternative", types) for db_map, types in db_map_item_types.items()}
        db_map_scen_ids = {db_map: _ids("scenario", types) for db_map, types in db_map_item_types.items()}
        db_map_scen_alt_ids = {
            db_map: _ids("scenario_alternative", types) for db_map, types in db_map_item_types.items()
        }
        parcel = SpineDBParcel(self.db_mngr)
        parcel._push_object_class_ids(db_map_obj_cls_ids)
        parcel._push_object_ids(db_map_obj_ids)
        parcel._push_relationship_class_ids(db_map_rel_cls_ids)
        parcel._push_relationship_ids(db_map_rel_ids)
        parcel._push_parameter_definition_ids(db_map_par_def_ids, "object")
        parcel._push_parameter_definition_ids(db_map_par_def_ids, "relationship")
        parcel._push_parameter_value_ids(db_map_par_val_ids, "object")
        parcel._push_parameter_value_ids(db_map_par_val_ids, "relationship")
        parcel._push_parameter_value_list_ids(db_map_par_val_lst_ids)
        parcel._push_object_group_ids(db_map_ent_group_ids)
        parcel._push_alternative_ids(db_map_alt_ids)
        parcel._push_scenario_ids(db_map_scen_ids)
        parcel._push_scenario_alternative_ids(db_map_scen_alt_ids)
        self.export_data(parcel.data)

    @Slot(object)
    def export_data(self, db_map_ids_for_export):
        """Exports data from given dictionary into a file.

        Args:
            db_map_ids_for_export: Dictionary mapping db maps to keyword arguments for spinedb_api.export_data
        """
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        self.qsettings.beginGroup(self.settings_group)
        file_path, selected_filter = get_save_file_name_in_last_dir(
            self.qsettings,
            "exportDB",
            self,
            "Export file",
            self._get_base_dir(),
            "SQLite (*.sqlite);; JSON file (*.json);; Excel file (*.xlsx)",
        )
        self.qsettings.endGroup()
        if not file_path:  # File selection cancelled
            return
        data_for_export = self._make_data_for_export(db_map_ids_for_export)
        if selected_filter.startswith("JSON"):
            self.export_to_json(file_path, data_for_export)
        elif selected_filter.startswith("SQLite"):
            self.export_to_sqlite(file_path, data_for_export)
        elif selected_filter.startswith("Excel"):
            self.export_to_excel(file_path, data_for_export)
        else:
            raise ValueError()

    def export_to_sqlite(self, file_path, data_for_export):
        """Exports given data into SQLite file."""
        url = URL("sqlite", database=file_path)
        if not self.db_mngr.is_url_available(url, self):
            return
        create_new_spine_database(url)
        db_map = DiffDatabaseMapping(url)
        import_data(db_map, **data_for_export)
        try:
            db_map.commit_session("Export initial data from Spine Toolbox.")
        except SpineDBAPIError as err:
            self.msg_error.emit(f"[SpineDBAPIError] Unable to export file <b>{db_map.codename}</b>: {err.msg}")
        else:
            self.sqlite_file_exported.emit(file_path)

    def export_to_json(self, file_path, data_for_export):
        """Exports given data into JSON file."""
        indent = 4 * " "
        json_data = "{{{0}{1}{0}}}".format(
            "\n" if data_for_export else "",
            ",\n".join(
                [
                    indent
                    + json.dumps(key)
                    + ": [{0}{1}{0}]".format(
                        "\n" + indent if values else "",
                        (",\n" + indent).join(
                            [indent + json.dumps(value, cls=ParameterValueEncoder) for value in values]
                        ),
                    )
                    for key, values in data_for_export.items()
                ]
            ),
        )
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        self.file_exported.emit(file_path)

    @busy_effect
    def export_to_excel(self, file_path, data_for_export):
        """Exports given data into Excel file."""
        # NOTE: We import data into an in-memory Spine db and then export that to excel.
        url = URL("sqlite", database="")
        db_map = DiffDatabaseMapping(url, create=True)
        import_data(db_map, **data_for_export)
        file_name = os.path.split(file_path)[1]
        try:
            export_spine_database_to_xlsx(db_map, file_path)
        except PermissionError:
            self.msg_error.emit(
                f"Unable to export file <b>{file_name}</b>.<br/>" "Close the file in Excel and try again."
            )
        except OSError:
            self.msg_error.emit(f"[OSError] Unable to export file <b>{file_name}</b>.")
        else:
            self.file_exported.emit(file_path)

    @staticmethod
    def _parse_db_map_metadata(db_map_metadata):
        s = "<ul>"
        for db_map_name, element_metadata in db_map_metadata.items():
            s += f"<li>{db_map_name}<ul>"
            for element_name, metadata in element_metadata.items():
                s += f"<li>{element_name}<ul>"
                for name, value in metadata.items():
                    s += f"<li>{name}: {value}</li>"
                s += "</ul>"
            s += "</ul>"
        s += "</ul>"
        return s

    @staticmethod
    def _metadata_per_entity(db_map, entity_ids):
        d = {}
        sq = db_map.ext_entity_metadata_sq
        for x in db_map.query(sq).filter(db_map.in_(sq.c.entity_id, entity_ids)):
            d.setdefault(x.entity_name, {}).setdefault(x.metadata_name, []).append(x.metadata_value)
        return d

    def show_db_map_entity_metadata(self, db_map_ids):
        metadata = {
            db_map.codename: self._metadata_per_entity(db_map, entity_ids) for db_map, entity_ids in db_map_ids.items()
        }
        QMessageBox.information(self, "Entity metadata", self._parse_db_map_metadata(metadata))

    @staticmethod
    def _metadata_per_parameter_value(db_map, param_val_ids):
        d = {}
        sq = db_map.ext_parameter_value_metadata_sq
        for x in db_map.query(sq).filter(db_map.in_(sq.c.parameter_value_id, param_val_ids)):
            param_val_name = (x.entity_name, x.parameter_name, x.alternative_name)
            d.setdefault(param_val_name, {}).setdefault(x.metadata_name, []).append(x.metadata_value)
        return d

    def show_db_map_parameter_value_metadata(self, db_map_ids):
        metadata = {
            db_map.codename: self._metadata_per_parameter_value(db_map, param_val_ids)
            for db_map, param_val_ids in db_map_ids.items()
        }
        QMessageBox.information(self, "Parameter value metadata", self._parse_db_map_metadata(metadata))

    def reload_session(self, db_maps):
        """Reloads data from given db_maps."""
        self.init_models()
        self.fetch_db_maps(*db_maps)

    @Slot(bool)
    def refresh_session(self, checked=False):
        self.db_mngr.refresh_session(*self.db_maps)

    @Slot(bool)
    def commit_session(self, checked=False):
        """Commits session."""
        self.db_mngr.commit_session(*self.db_maps, cookie=self)

    @Slot(bool)
    def rollback_session(self, checked=False):
        self.db_mngr.rollback_session(*self.db_maps)

    def receive_session_committed(self, db_maps, cookie):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        db_names = ", ".join([x.codename for x in db_maps])
        if cookie is self:
            msg = f"All changes in {db_names} committed successfully."
            self.msg.emit(msg)
        else:  # Commit done by an 'outside force'.
            self.reload_session(db_maps)
            self.msg.emit(f"Databases {db_names} reloaded from an external action.")

    def receive_session_rolled_back(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        self.reload_session(db_maps)
        db_names = ", ".join([x.codename for x in db_maps])
        msg = f"All changes in {db_names} rolled back successfully."
        self.msg.emit(msg)

    def receive_session_refreshed(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        self.reload_session(db_maps)
        self.msg.emit("Session refreshed.")

    @Slot(bool)
    def show_mass_remove_items_form(self, checked=False):
        dialog = MassRemoveItemsDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    @busy_effect
    @Slot("QModelIndex")
    def show_parameter_value_editor(self, index):
        """Shows the parameter_value editor for the given index of given table view.
        """
        editor = ParameterValueEditor(index, parent=self)
        editor.show()

    def receive_error_msg(self, db_map_error_log):
        msgs = []
        for db_map, error_log in db_map_error_log.items():
            if isinstance(error_log, str):
                error_log = [error_log]
            msg = "From " + db_map.codename + ":" + format_string_list(error_log)
            msgs.append(msg)
        self.msg_error.emit(format_string_list(msgs))

    def notify_items_changed(self, action, item_type, db_map_data):
        """Enables or disables actions and informs the user about what just happened."""
        count = sum(len(data) for data in db_map_data.values())
        msg = f"Successfully {action} {count} {item_type} item(s)"
        self.msg.emit(msg)

    def receive_scenarios_fetched(self, db_map_data):
        pass

    def receive_alternatives_fetched(self, db_map_data):
        pass

    def receive_object_classes_fetched(self, db_map_data):
        pass

    def receive_objects_fetched(self, db_map_data):
        pass

    def receive_relationship_classes_fetched(self, db_map_data):
        pass

    def receive_relationships_fetched(self, db_map_data):
        pass

    def receive_entity_groups_fetched(self, db_map_data):
        pass

    def receive_parameter_definitions_fetched(self, db_map_data):
        pass

    def receive_parameter_values_fetched(self, db_map_data):
        pass

    def receive_parameter_value_lists_fetched(self, db_map_data):
        self.parameter_value_list_model.add_parameter_value_lists(db_map_data)

    def receive_parameter_tags_fetched(self, db_map_data):
        pass

    def receive_features_fetched(self, db_map_data):
        pass

    def receive_tools_fetched(self, db_map_data):
        pass

    def receive_tool_features_fetched(self, db_map_data):
        pass

    def receive_tool_feature_methods_fetched(self, db_map_data):
        pass

    def receive_scenarios_added(self, db_map_data):
        self.notify_items_changed("added", "scenario", db_map_data)

    def receive_alternatives_added(self, db_map_data):
        self.notify_items_changed("added", "alternative", db_map_data)

    def receive_object_classes_added(self, db_map_data):
        self.notify_items_changed("added", "object_class", db_map_data)

    def receive_objects_added(self, db_map_data):
        self.notify_items_changed("added", "object", db_map_data)

    def receive_relationship_classes_added(self, db_map_data):
        self.notify_items_changed("added", "relationship_class", db_map_data)

    def receive_relationships_added(self, db_map_data):
        self.notify_items_changed("added", "relationship", db_map_data)

    def receive_entity_groups_added(self, db_map_data):
        self.notify_items_changed("added", "entity_group", db_map_data)

    def receive_parameter_definitions_added(self, db_map_data):
        self.notify_items_changed("added", "parameter_definition", db_map_data)

    def receive_parameter_values_added(self, db_map_data):
        self.notify_items_changed("added", "parameter_value", db_map_data)

    def receive_parameter_value_lists_added(self, db_map_data):
        self.notify_items_changed("added", "parameter_value_list", db_map_data)

    def receive_parameter_tags_added(self, db_map_data):
        self.notify_items_changed("added", "parameter_tag", db_map_data)

    def receive_features_added(self, db_map_data):
        self.notify_items_changed("added", "feature", db_map_data)

    def receive_tools_added(self, db_map_data):
        self.notify_items_changed("added", "tool", db_map_data)

    def receive_tool_features_added(self, db_map_data):
        self.notify_items_changed("added", "tool_feature", db_map_data)

    def receive_tool_feature_methods_added(self, db_map_data):
        self.notify_items_changed("added", "tool_feature_method", db_map_data)

    def receive_scenarios_updated(self, db_map_data):
        self.notify_items_changed("updated", "scenario", db_map_data)

    def receive_alternatives_updated(self, db_map_data):
        self.notify_items_changed("updated", "alternative", db_map_data)

    def receive_object_classes_updated(self, db_map_data):
        self.notify_items_changed("updated", "object_class", db_map_data)

    def receive_objects_updated(self, db_map_data):
        self.notify_items_changed("updated", "object", db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        self.notify_items_changed("updated", "relationship_class", db_map_data)

    def receive_relationships_updated(self, db_map_data):
        self.notify_items_changed("updated", "relationship", db_map_data)

    def receive_parameter_definitions_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter_definition", db_map_data)

    def receive_parameter_values_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter_value", db_map_data)

    def receive_parameter_value_lists_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter_value_list", db_map_data)

    def receive_parameter_tags_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter_tag", db_map_data)

    def receive_features_updated(self, db_map_data):
        self.notify_items_changed("updated", "feature", db_map_data)

    def receive_tools_updated(self, db_map_data):
        self.notify_items_changed("updated", "tool", db_map_data)

    def receive_tool_features_updated(self, db_map_data):
        self.notify_items_changed("updated", "tool_feature", db_map_data)

    def receive_tool_feature_methods_updated(self, db_map_data):
        self.notify_items_changed("updated", "tool_feature_method", db_map_data)

    def receive_parameter_definition_tags_set(self, db_map_data):
        self.notify_items_changed("set", "parameter_definition tag", db_map_data)

    def receive_scenarios_removed(self, db_map_data):
        self.notify_items_changed("removed", "scenarios", db_map_data)

    def receive_alternatives_removed(self, db_map_data):
        self.notify_items_changed("removed", "alternatives", db_map_data)

    def receive_object_classes_removed(self, db_map_data):
        self.notify_items_changed("removed", "object_class", db_map_data)

    def receive_objects_removed(self, db_map_data):
        self.notify_items_changed("removed", "object", db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        self.notify_items_changed("removed", "relationship_class", db_map_data)

    def receive_relationships_removed(self, db_map_data):
        self.notify_items_changed("removed", "relationship", db_map_data)

    def receive_entity_groups_removed(self, db_map_data):
        self.notify_items_changed("removed", "entity_group", db_map_data)

    def receive_parameter_definitions_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter_definition", db_map_data)

    def receive_parameter_values_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter_value", db_map_data)

    def receive_parameter_value_lists_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter_value_list", db_map_data)

    def receive_parameter_tags_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter_tag", db_map_data)

    def receive_features_removed(self, db_map_data):
        self.notify_items_changed("removed", "feature", db_map_data)

    def receive_tools_removed(self, db_map_data):
        self.notify_items_changed("removed", "tool", db_map_data)

    def receive_tool_features_removed(self, db_map_data):
        self.notify_items_changed("removed", "tool_feature", db_map_data)

    def receive_tool_feature_methods_removed(self, db_map_data):
        self.notify_items_changed("removed", "tool_feature_method", db_map_data)

    def restore_ui(self):
        """Restore UI state from previous session."""
        self.qsettings.beginGroup(self.settings_group)
        self.qsettings.beginGroup(self.settings_subgroup)
        window_state = self.qsettings.value("windowState")
        self.qsettings.endGroup()
        self.qsettings.endGroup()
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions

    def save_window_state(self):
        """Save window state parameters (size, position, state) via QSettings."""
        self.qsettings.beginGroup(self.settings_group)
        self.qsettings.beginGroup(self.settings_subgroup)
        self.qsettings.setValue("windowState", self.saveState(version=1))
        self.qsettings.endGroup()
        self.qsettings.endGroup()

    def tear_down(self):
        if not self.db_mngr.unregister_listener(self, *self.db_maps):
            return False
        # Save UI form state
        self.save_window_state()
        return True

    def closeEvent(self, event):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event
        """
        if not self.tear_down():
            event.ignore()
            return
        super().closeEvent(event)


class SpineDBEditor(TabularViewMixin, GraphViewMixin, ParameterViewMixin, TreeViewMixin, SpineDBEditorBase):
    """A widget to visualize Spine dbs."""

    def __init__(self, db_mngr, db_url_codenames=None, create=False):
        """Initializes everything.

        Args:
            db_mngr (SpineDBManager): The manager to use
            db_url_codenames (dict): mapping url to codename.
        """
        super().__init__(db_mngr)
        self._size = None
        dock_views = {d: d.findChild(QTreeView) or d.findChild(QTableView) for d in self.findChildren(QDockWidget)}
        self._dock_views = {d: v for d, v in dock_views.items() if v is not None}
        self._refresh_timer = QTimer(self)  # Used to limit refresh
        self._refresh_timer.setSingleShot(True)
        self.add_main_menu()
        self.connect_signals()
        self.apply_stacked_style()
        self.load_db_urls(db_url_codenames, create=create)

    def connect_signals(self):
        super().connect_signals()
        self.ui.actionStacked_style.triggered.connect(self.apply_stacked_style)
        self.ui.actionGraph_style.triggered.connect(self.apply_graph_style)
        self.ui.actionPivot_style.triggered.connect(self.apply_pivot_style)
        self._refresh_timer.timeout.connect(self._refresh_tab_order)
        for dock in self._dock_views:
            dock.visibilityChanged.connect(self._restart_refresh_timer)

    @Slot(bool)
    def _restart_refresh_timer(self, _visible=None):
        self._refresh_timer.start(10)

    @Slot()
    def _refresh_tab_order(self):
        visible_docks = []
        for dock, view in self._dock_views.items():
            if dock.pos().x() >= 0 and not dock.isFloating():
                visible_docks.append(dock)
                view.setFocusPolicy(Qt.StrongFocus)
            else:
                view.setFocusPolicy(Qt.ClickFocus)
        if not visible_docks:
            return
        sorted_docks = sorted(visible_docks, key=lambda d: (d.pos().x(), d.pos().y()))
        tab_bars = {}
        for tab_bar in self.findChildren(QTabBar):
            i = tab_bar.currentIndex()
            if i != -1:
                tab_bars[tab_bar.tabText(i)] = tab_bar
        sorted_widgets = []
        for dock in sorted_docks:
            sorted_widgets.append(self._dock_views[dock])
            tab_bar = tab_bars.get(dock.windowTitle())
            if tab_bar is not None:
                sorted_widgets.append(tab_bar)
        self.setTabOrder(self.url_toolbar.line_edit, sorted_widgets[0])
        for first, second in zip(sorted_widgets[:-1], sorted_widgets[1:]):
            self.setTabOrder(first, second)

    def tabify_and_raise(self, docks):
        """
        Tabifies docks in given list, then raises the first.

        Args:
            docks (list)
        """
        for first, second in zip(docks[:-1], docks[1:]):
            self.tabifyDockWidget(first, second)
        docks[0].raise_()

    def restore_dock_widgets(self):
        """Docks all floating and or hidden QDockWidgets back to the window."""
        for dock in self._dock_views:
            dock.setVisible(True)
            dock.setFloating(False)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def begin_style_change(self):
        """Begins a style change operation."""
        for dock in self._dock_views:
            dock.visibilityChanged.disconnect(self._restart_refresh_timer)
        self._size = self.size()
        self.restore_dock_widgets()

    def end_style_change(self):
        """Ends a style change operation."""
        qApp.processEvents()  # pylint: disable=undefined-variable
        self.ui.dockWidget_exports.hide()
        self.resize(self._size)
        for dock in self._dock_views:
            dock.visibilityChanged.connect(self._restart_refresh_timer)
        self._restart_refresh_timer()

    @Slot(bool)
    def apply_stacked_style(self, checked=False):
        """Applies the stacked style, inspired in the former tree view."""
        self.begin_style_change()
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_object_parameter_value, Qt.Horizontal)
        self.splitDockWidget(
            self.ui.dockWidget_object_parameter_value, self.ui.dockWidget_tool_feature_tree, Qt.Horizontal
        )
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_relationship_tree, Qt.Vertical)
        self.splitDockWidget(self.ui.dockWidget_tool_feature_tree, self.ui.dockWidget_parameter_value_list, Qt.Vertical)
        self.splitDockWidget(
            self.ui.dockWidget_parameter_value_list, self.ui.dockWidget_alternative_scenario_tree, Qt.Vertical
        )
        self.splitDockWidget(
            self.ui.dockWidget_alternative_scenario_tree, self.ui.dockWidget_parameter_tag, Qt.Vertical
        )
        self.splitDockWidget(
            self.ui.dockWidget_object_parameter_value, self.ui.dockWidget_relationship_parameter_value, Qt.Vertical
        )
        self.tabify_and_raise(
            [self.ui.dockWidget_object_parameter_value, self.ui.dockWidget_object_parameter_definition]
        )
        self.tabify_and_raise(
            [self.ui.dockWidget_relationship_parameter_value, self.ui.dockWidget_relationship_parameter_definition]
        )
        self.ui.dockWidget_entity_graph.hide()
        self.ui.dockWidget_pivot_table.hide()
        self.ui.dockWidget_frozen_table.hide()
        docks = [
            self.ui.dockWidget_object_tree,
            self.ui.dockWidget_object_parameter_value,
            self.ui.dockWidget_parameter_value_list,
        ]
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.2 * width, 0.6 * width, 0.2 * width], Qt.Horizontal)
        docks = [
            self.ui.dockWidget_tool_feature_tree,
            self.ui.dockWidget_parameter_value_list,
            self.ui.dockWidget_alternative_scenario_tree,
            self.ui.dockWidget_parameter_tag,
        ]
        height = sum(d.size().height() for d in docks)
        self.resizeDocks(docks, [0.3 * height, 0.3 * height, 0.3 * height, 0.1 * height], Qt.Vertical)
        self.end_style_change()

    @Slot(bool)
    def apply_pivot_style(self, checked=False):
        """Applies the pivot style, inspired in the former tabular view."""
        self.begin_style_change()
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_pivot_table, Qt.Horizontal)
        self.splitDockWidget(self.ui.dockWidget_pivot_table, self.ui.dockWidget_frozen_table, Qt.Horizontal)
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_relationship_tree, Qt.Vertical)
        self.splitDockWidget(self.ui.dockWidget_frozen_table, self.ui.dockWidget_tool_feature_tree, Qt.Vertical)
        self.splitDockWidget(
            self.ui.dockWidget_tool_feature_tree, self.ui.dockWidget_alternative_scenario_tree, Qt.Vertical
        )
        self.ui.dockWidget_entity_graph.hide()
        self.ui.dockWidget_object_parameter_value.hide()
        self.ui.dockWidget_object_parameter_definition.hide()
        self.ui.dockWidget_relationship_parameter_value.hide()
        self.ui.dockWidget_relationship_parameter_definition.hide()
        self.ui.dockWidget_parameter_value_list.hide()
        self.ui.dockWidget_parameter_tag.hide()
        docks = [self.ui.dockWidget_object_tree, self.ui.dockWidget_pivot_table, self.ui.dockWidget_frozen_table]
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.2 * width, 0.6 * width, 0.2 * width], Qt.Horizontal)
        self.end_style_change()

    @Slot(bool)
    def apply_graph_style(self, checked=False):
        """Applies the graph style, inspired in the former graph view."""
        self.begin_style_change()
        self.ui.dockWidget_pivot_table.hide()
        self.ui.dockWidget_frozen_table.hide()
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_entity_graph, Qt.Horizontal)
        self.splitDockWidget(
            self.ui.dockWidget_entity_graph, self.ui.dockWidget_alternative_scenario_tree, Qt.Horizontal
        )
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_relationship_tree, Qt.Vertical)
        self.splitDockWidget(self.ui.dockWidget_entity_graph, self.ui.dockWidget_object_parameter_value, Qt.Vertical)
        self.splitDockWidget(
            self.ui.dockWidget_alternative_scenario_tree, self.ui.dockWidget_tool_feature_tree, Qt.Vertical
        )
        self.splitDockWidget(self.ui.dockWidget_tool_feature_tree, self.ui.dockWidget_parameter_value_list, Qt.Vertical)
        self.splitDockWidget(self.ui.dockWidget_parameter_value_list, self.ui.dockWidget_parameter_tag, Qt.Vertical)
        self.tabify_and_raise(
            [
                self.ui.dockWidget_object_parameter_value,
                self.ui.dockWidget_object_parameter_definition,
                self.ui.dockWidget_relationship_parameter_value,
                self.ui.dockWidget_relationship_parameter_definition,
            ]
        )
        docks = [
            self.ui.dockWidget_object_tree,
            self.ui.dockWidget_entity_graph,
            self.ui.dockWidget_parameter_value_list,
        ]
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.2 * width, 0.6 * width, 0.2 * width], Qt.Horizontal)
        docks = [self.ui.dockWidget_entity_graph, self.ui.dockWidget_object_parameter_value]
        height = sum(d.size().height() for d in docks)
        self.resizeDocks(docks, [0.7 * height, 0.3 * height], Qt.Vertical)
        docks = [
            self.ui.dockWidget_alternative_scenario_tree,
            self.ui.dockWidget_parameter_value_list,
            self.ui.dockWidget_parameter_tag,
        ]
        height = sum(d.size().height() for d in docks)
        self.resizeDocks(docks, [0.4 * height, 0.4 * height, 0.2 * height], Qt.Vertical)
        self.end_style_change()
        self.ui.graphicsView.reset_zoom()

    @staticmethod
    def _get_base_dir():
        return APPLICATION_PATH
