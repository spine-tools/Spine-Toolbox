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
Contains the SpineDBEditor class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import os
import time  # just to measure loading time and sqlalchemy ORM performance
import json
from PySide2.QtWidgets import QMainWindow, QErrorMessage, QDockWidget, QMenu, QMessageBox
from PySide2.QtCore import Qt, Signal, Slot, QPoint
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon
from sqlalchemy.engine.url import URL, make_url
from spinedb_api import (
    import_data,
    export_data,
    ParameterValueEncoder,
    create_new_spine_database,
    DiffDatabaseMapping,
    SpineDBAPIError,
    SpineDBVersionError,
    Anyone,
)
from spinetoolbox.spine_io.exporters.excel import export_spine_database_to_xlsx
from spinetoolbox.spine_io.importers.excel_reader import get_mapped_data_from_xlsx
from ...config import MAINWINDOW_SS, APPLICATION_PATH, ONLINE_DOCUMENTATION_URL
from .mass_select_items_dialogs import MassRemoveItemsDialog, MassExportItemsDialog
from .custom_qwidgets import OpenFileButton, OpenSQLiteFileButton, ShootingLabel, CustomInputDialog
from .parameter_view_mixin import ParameterViewMixin
from .tree_view_mixin import TreeViewMixin
from .graph_view_mixin import GraphViewMixin
from .tabular_view_mixin import TabularViewMixin
from .db_session_history_dialog import DBSessionHistoryDialog
from ...widgets.notification import NotificationStack
from ...helpers import (
    ensure_window_is_on_screen,
    get_save_file_name_in_last_dir,
    get_open_file_name_in_last_dir,
    format_string_list,
    focused_widget_has_callable,
    call_on_focused_widget,
    busy_effect,
    open_url,
)
from ...widgets.parameter_value_editor import ParameterValueEditor
from ...widgets.settings_widget import SpineDBEditorSettingsWidget
from ...spine_db_parcel import SpineDBParcel


class SpineDBEditorBase(QMainWindow):
    """Base class for SpineDBEditor (i.e. Spine database editor)."""

    msg = Signal(str)
    link_msg = Signal(str, "QVariant")
    msg_error = Signal(str)
    error_box = Signal(str, str)

    def __init__(self, db_mngr, *db_maps):
        """Initializes form.

        Args:
            db_mngr (SpineDBManager): The manager to use
            *db_maps (DiffDatabaseMapping): The db map to visualize.
        """
        super().__init__(flags=Qt.Window)
        from ..ui.spine_db_editor_window import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self.db_maps_by_codename = {db_map.codename: db_map for db_map in db_maps}
        self.db_urls = [db_map.db_url for db_map in self.db_maps]
        self.db_url = self.db_urls[0]
        self.db_mngr.register_listener(self, *self.db_maps)
        self.db_mngr.set_logger_for_db_map(self, self.first_db_map)  # FIXME
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.takeCentralWidget()
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStyleSheet(MAINWINDOW_SS)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.qsettings = self.db_mngr.qsettings
        self.settings_form = SpineDBEditorSettingsWidget(self.db_mngr)
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
        self.template_file_path = None
        db_names = ", ".join([f"{db_map.codename}" for db_map in self.db_maps])
        self.setWindowTitle(f"{db_names}[*] - Spine database editor")
        self.update_commit_enabled()

    @property
    def first_db_map(self):
        return self.db_maps[0]

    def _make_db_menu(self):
        if len(self.db_maps) <= 1:
            return None
        menu = QMenu("Database", self)
        actions = [menu.addAction(db_map.codename) for db_map in self.db_maps]
        for action in actions:
            action.setCheckable(True)
        return menu

    def add_menu_actions(self):
        """Adds actions to View and Edit menu."""
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_parameter_value_list.toggleViewAction())
        before = self.ui.menuEdit.actions()[0]
        self.undo_action = self.db_mngr.undo_action[self.first_db_map]
        self.redo_action = self.db_mngr.redo_action[self.first_db_map]
        self.ui.menuEdit.insertAction(before, self.undo_action)
        self.ui.menuEdit.insertAction(before, self.redo_action)
        self.ui.menuEdit.insertSeparator(before)

    def connect_signals(self):
        """Connects signals to slots."""
        # Message signals
        self.msg.connect(self.add_message)
        self.link_msg.connect(self.add_link_msg)
        self.msg_error.connect(self.err_msg.showMessage)
        self.error_box.connect(lambda title, msg: self.err_msg.showMessage(msg))
        # Menu actions
        self.ui.actionCommit.triggered.connect(self.commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)
        self.ui.actionView_history.triggered.connect(self.show_history_dialog)
        self.ui.actionSettings.triggered.connect(self.settings_form.show)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.menuEdit.aboutToShow.connect(self._handle_menu_edit_about_to_show)
        self.ui.actionImport.triggered.connect(self.import_file)
        self.ui.actionExport.triggered.connect(self.show_mass_export_items_dialog)
        self.ui.actionExport_session.triggered.connect(self.export_session)
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionRemove_selected.triggered.connect(self.remove_selected)
        self.ui.actionEdit_selected.triggered.connect(self.edit_selected)
        self.ui.actionMass_remove_items.triggered.connect(self.show_mass_remove_items_form)
        self.ui.dockWidget_exports.visibilityChanged.connect(self._handle_exports_visibility_changed)
        self.ui.actionUser_guide.triggered.connect(self.show_user_guide)

    @Slot(int)
    def update_undo_redo_actions(self, index):
        undo_ages = {db_map: self.db_mngr.undo_stack[db_map].undo_age for db_map in self.db_maps}
        redo_ages = {db_map: self.db_mngr.undo_stack[db_map].redo_age for db_map in self.db_maps}
        undo_ages = {db_map: age for db_map, age in undo_ages.items() if age is not None}
        redo_ages = {db_map: age for db_map, age in redo_ages.items() if age is not None}
        new_undo_action = self.db_mngr.undo_action[max(undo_ages, key=undo_ages.get, default=self.first_db_map)]
        new_redo_action = self.db_mngr.redo_action[min(redo_ages, key=redo_ages.get, default=self.first_db_map)]
        if new_undo_action != self.undo_action:
            self.ui.menuEdit.insertAction(self.undo_action, new_undo_action)
            self.ui.menuEdit.removeAction(self.undo_action)
            self.undo_action = new_undo_action
        if new_redo_action != self.redo_action:
            self.ui.menuEdit.insertAction(self.redo_action, new_redo_action)
            self.ui.menuEdit.removeAction(self.redo_action)
            self.redo_action = new_redo_action

    @Slot(bool)
    def update_commit_enabled(self, _clean=False):
        dirty = not all(self.db_mngr.undo_stack[db_map].isClean() for db_map in self.db_maps)
        self.ui.actionExport_session.setEnabled(dirty)
        self.ui.actionCommit.setEnabled(dirty)
        self.ui.actionRollback.setEnabled(dirty)
        self.ui.actionView_history.setEnabled(dirty)
        self.setWindowModified(dirty)

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

    def restore_dock_widgets(self):
        """Docks all floating and or hidden QDockWidgets back to the window."""
        for dock in self.findChildren(QDockWidget):
            dock.setVisible(True)
            dock.setFloating(False)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)

    @Slot()
    def _handle_menu_edit_about_to_show(self):
        """Runs when the edit menu from the main menubar is about to show.
        Enables or disables actions according to selection status."""
        # TODO: Try to also check if there's a selection to enable copy, remove, edit, etc.
        self.ui.actionCopy.setEnabled(focused_widget_has_callable(self, "copy"))
        self.ui.actionPaste.setEnabled(focused_widget_has_callable(self, "paste"))
        self.ui.actionRemove_selected.setEnabled(focused_widget_has_callable(self, "remove_selected"))
        self.ui.actionEdit_selected.setEnabled(focused_widget_has_callable(self, "edit_selected"))

    @Slot(bool)
    def remove_selected(self, checked=False):
        """Removes selected items."""
        call_on_focused_widget(self, "remove_selected")

    @Slot(bool)
    def edit_selected(self, checked=False):
        """Edits selected items."""
        call_on_focused_widget(self, "edit_selected")

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
            data = json.load(f)
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
            self.error_box.emit("Parse error", msg)
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
            return (Anyone,) if t in types else ()

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
        db_map = DiffDatabaseMapping(url, _create_engine=create_new_spine_database)
        import_data(db_map, **data_for_export)
        try:
            db_map.commit_session("Export initial data from Spine Toolbox.")
        except SpineDBAPIError as err:
            self.msg_error.emit(f"[SpineDBAPIError] Unable to export file <b>{db_map.codename}</b>: {err.msg}")
        else:
            self._insert_open_sqlite_file_button(file_path)

    def _open_sqlite_url(self, url, codename):
        """Opens sqlite url."""
        self.db_mngr.show_spine_db_editor({url: codename}, None)

    def _add_sqlite_url_to_project(self, url):
        """Adds sqlite url to project."""
        project = self.db_mngr._project
        if not project:
            return
        icon_path = project._toolbox.item_factories["Data Store"].icon()
        data_stores = project._project_item_model.items(category_name="Data Stores")
        data_stores = [x.project_item for x in data_stores]
        named_data_stores = {x.name: x for x in data_stores}
        data_store_names = list(named_data_stores)
        name = CustomInputDialog.get_item(
            self,
            "Add SQLite file to Project",
            "<p>Select a Data Store from the list to be the recipient:</p>",
            data_store_names,
            icons={name: QIcon(icon_path) for name in data_store_names},
            editable_text="Add new Data Store...",
        )
        if name is None:
            return
        data_store = named_data_stores.get(name)
        database = make_url(url).database
        url_as_dict = {"dialect": "sqlite", "database": database}
        if not data_store:
            data_store_dict = {name: {"type": "Data Store", "description": "", "x": 0, "y": 0, "url": url_as_dict}}
            project.add_project_items(data_store_dict)
            action = "added"
        elif data_store.update_url(**url_as_dict):
            action = "updated"
        else:
            self.msg.emit(f"Data Store <i>{name}</i> is already set to use url {url}")
            return
        link = "<a href='#'>undo</a>"
        stack = project._toolbox.undo_stack
        index = stack.index()
        open_link = lambda _, stack=stack, index=index: self._undo_add_sqlite_url_to_project(_, stack, index)
        self.link_msg.emit(f"Data Store <i>{name}</i> successfully {action}.<br>{link}", open_link)

    @Slot("str")
    def _undo_add_sqlite_url_to_project(self, _, stack, index):
        if not stack.canUndo() or stack.index() != index:
            self.msg.emit(f"Already undone.")
            return
        stack.undo()
        self.msg.emit(f"Successfully undone.")

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
        self._insert_open_file_button(file_path)

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
            self._insert_open_file_button(file_path)

    def _insert_open_file_button(self, file_path):
        button = OpenFileButton(file_path, self)
        self._insert_button_to_exports_widget(button)

    def _insert_open_sqlite_file_button(self, file_path):
        button = OpenSQLiteFileButton(file_path, self)
        self._insert_button_to_exports_widget(button)

    def _insert_button_to_exports_widget(self, button):
        """
        Inserts given button to the 'beginning' of the status bar and decorates the thing with a shooting label.
        """
        duplicates = [
            x
            for x in self.ui.dockWidget_exports.findChildren(OpenFileButton)
            if os.path.samefile(x.file_path, button.file_path)
        ]
        for dup in duplicates:
            self.ui.horizontalLayout_exports.removeWidget(dup)
        self.ui.horizontalLayout_exports.insertWidget(0, button)
        self.ui.dockWidget_exports.show()
        destination = QPoint(16, 0) + button.mapTo(self, QPoint(0, 0))
        label = ShootingLabel(destination - QPoint(0, 64), destination, self)
        pixmap = QIcon(":/icons/file-download.svg").pixmap(32, 32)
        label.setPixmap(pixmap)
        label.show()

    @Slot(bool)
    def _handle_exports_visibility_changed(self, visible):
        """Remove all buttons when exports dock is closed."""
        if visible:
            return
        for button in self.ui.dockWidget_exports.findChildren(OpenFileButton):
            self.ui.horizontalLayout_exports.removeWidget(button)
            button.hide()

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
        self.db_mngr.fetch_db_maps_for_listener(self, *db_maps)

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

    @Slot(bool)
    def show_user_guide(self, checked=False):
        """Opens Spine Toolbox documentation Spine db editor page in browser."""
        doc_url = f"{ONLINE_DOCUMENTATION_URL}/spine_db_editor/index.html"
        if not open_url(doc_url):
            self.msg_error.emit("Unable to open url <b>{0}</b>".format(doc_url))

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
        window_size = self.qsettings.value("windowSize")
        window_pos = self.qsettings.value("windowPosition")
        window_state = self.qsettings.value("windowState")
        window_maximized = self.qsettings.value("windowMaximized", defaultValue='false')
        n_screens = self.qsettings.value("n_screens", defaultValue=1)
        self.qsettings.endGroup()
        original_size = self.size()
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)
        ensure_window_is_on_screen(self, original_size)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        # noinspection PyArgumentList

    def save_window_state(self):
        """Save window state parameters (size, position, state) via QSettings."""
        self.qsettings.beginGroup(self.settings_group)
        self.qsettings.setValue("windowSize", self.size())
        self.qsettings.setValue("windowPosition", self.pos())
        self.qsettings.setValue("windowState", self.saveState(version=1))
        self.qsettings.setValue("windowMaximized", self.windowState() == Qt.WindowMaximized)
        self.qsettings.setValue("n_screens", len(QGuiApplication.screens()))
        self.qsettings.endGroup()

    def closeEvent(self, event):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event
        """
        for db_map in self.db_maps:
            if not self.db_mngr.unregister_listener(self, db_map):
                event.ignore()
                return
            self.db_mngr.unset_logger_for_db_map(db_map)
        # Save UI form state
        self.save_window_state()
        QMainWindow.closeEvent(self, event)

    def _focused_widget_has_callable(self, callable_name):
        """Returns True if the currently focused widget or one of its ancestors has the given callable."""
        return focused_widget_has_callable(self, callable_name)

    def _call_on_focused_widget(self, callable_name):
        """Calls the given callable on the currently focused widget or one of its ancestors."""
        call_on_focused_widget(self, callable_name)


class SpineDBEditor(TabularViewMixin, GraphViewMixin, ParameterViewMixin, TreeViewMixin, SpineDBEditorBase):
    """A widget to visualize Spine dbs."""

    def __init__(self, db_mngr, *db_urls):
        """Initializes everything.

        Args:
            db_mngr (SpineDBManager): The manager to use
            *db_urls (tuple): Database url, codename.
        """
        tic = time.process_time()
        super().__init__(db_mngr, *db_urls)
        self._size = None
        self.init_models()
        self.add_menu_actions()
        self.connect_signals()
        self.apply_stacked_style()
        self.restore_ui()
        toc = time.process_time()
        self.msg.emit("Spine database editor opened in {0:.2f} seconds".format(toc - tic))
        self.db_mngr.fetch_db_maps_for_listener(self, *self.db_maps)

    def connect_signals(self):
        super().connect_signals()
        self.ui.actionStacked_style.triggered.connect(self.apply_stacked_style)
        self.ui.actionGraph_style.triggered.connect(self.apply_graph_style)
        self.ui.actionPivot_style.triggered.connect(self.apply_pivot_style)

    def add_menu_actions(self):
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_exports.toggleViewAction())

    def tabify_and_raise(self, docks):
        """
        Tabifies docks in given list, then raises the first.

        Args:
            docks (list)
        """
        for first, second in zip(docks[:-1], docks[1:]):
            self.tabifyDockWidget(first, second)
        docks[0].raise_()

    def begin_style_change(self):
        """Begins a style change operation."""
        self._size = self.size()
        self.restore_dock_widgets()

    def end_style_change(self):
        """Ends a style change operation."""
        qApp.processEvents()  # pylint: disable=undefined-variable
        self.ui.dockWidget_exports.hide()
        self.resize(self._size)

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

    def _get_base_dir(self):
        project = self.db_mngr.parent()
        if project is None:
            return APPLICATION_PATH
        return project.project_dir
