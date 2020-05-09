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
Contains the DataStoreForm class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import os
import time  # just to measure loading time and sqlalchemy ORM performance
import json
from PySide2.QtWidgets import QMainWindow, QErrorMessage, QDockWidget, QMessageBox, QInputDialog
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon
from spinedb_api import export_data, SpineIntegrityError, SpineDBAPIError, ParameterValueEncoder
from ..config import MAINWINDOW_SS, APPLICATION_PATH
from .data_store_edit_items_dialogs import ManageParameterTagsDialog
from .data_store_manage_items_dialog import MassRemoveItemsDialog, CreateTemplateDialog
from .custom_menus import ParameterValueListContextMenu
from .data_store_parameter_view_mixin import ParameterViewMixin
from .data_store_tree_view_mixin import TreeViewMixin
from .data_store_graph_view_mixin import GraphViewMixin
from .data_store_tabular_view_mixin import TabularViewMixin
from .toolbars import ParameterTagToolBar
from .db_session_history_dialog import DBSessionHistoryDialog
from .notification import NotificationStack
from ..mvcmodels.parameter_value_list_model import ParameterValueListModel
from ..helpers import (
    busy_effect,
    ensure_window_is_on_screen,
    get_save_file_name_in_last_dir,
    get_open_file_name_in_last_dir,
)
from .import_widget import ImportDialog
from .parameter_value_editor import ParameterValueEditor
from ..spine_io.exporters.excel import export_spine_database_to_xlsx


class DataStoreFormBase(QMainWindow):
    """Base class for DataStoreForm"""

    msg = Signal(str)
    msg_error = Signal(str)
    error_box = Signal(str, str)

    def __init__(self, db_mngr, *db_urls):
        """Initializes form.

        Args:
            db_mngr (SpineDBManager): The manager to use
            *db_urls (tuple): Database url, codename.
        """
        super().__init__(flags=Qt.Window)
        from ..ui.data_store_view import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        self.db_urls = list(db_urls)
        self.db_url = self.db_urls[0]
        self.db_mngr = db_mngr
        self.db_maps = [
            self.db_mngr.get_db_map_for_listener(self, url, codename=codename) for url, codename in self.db_urls
        ]
        self.db_map = self.db_maps[0]
        self.db_mngr.set_logger_for_db_map(self, self.db_map)
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.takeCentralWidget()
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStyleSheet(MAINWINDOW_SS)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.qsettings = self.db_mngr.qsettings
        self.err_msg = QErrorMessage(self)
        self.err_msg.setWindowTitle("Error")
        self.err_msg.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.notification_stack = NotificationStack(self)
        self.parameter_tag_toolbar = ParameterTagToolBar(self, self.db_mngr, *self.db_maps)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)
        self.selected_ent_cls_ids = {"object class": {}, "relationship class": {}}
        self.selected_ent_ids = {"object": {}, "relationship": {}}
        self.selected_parameter_tag_ids = dict()
        self.selected_param_def_ids = {"object class": {}, "relationship class": {}}
        self.parameter_value_list_model = ParameterValueListModel(self, self.db_mngr, *self.db_maps)
        self.ui.treeView_parameter_value_list.setModel(self.parameter_value_list_model)
        self.silenced = False
        fm = QFontMetrics(QFont("", 0))
        self.default_row_height = 1.2 * fm.lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        self.settings_group = 'dataStoreForm'
        self.undo_action = None
        self.redo_action = None
        self.template_file_path = None
        db_names = ", ".join([f"{db_map.codename}" for db_map in self.db_maps])
        self.setWindowTitle(f"{db_names}[*] - Data store view")
        self.update_commit_enabled()

    def add_menu_actions(self):
        """Adds actions to View and Edit menu."""
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_parameter_value_list.toggleViewAction())
        self.ui.menuView.addAction(self.parameter_tag_toolbar.toggleViewAction())
        before = self.ui.menuEdit.actions()[0]
        self.undo_action = self.db_mngr.undo_action[self.db_map]
        self.redo_action = self.db_mngr.redo_action[self.db_map]
        self.ui.menuEdit.insertAction(before, self.undo_action)
        self.ui.menuEdit.insertAction(before, self.redo_action)
        self.ui.menuEdit.insertSeparator(before)

    def connect_signals(self):
        """Connects signals to slots."""
        # Message signals
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.err_msg.showMessage)
        self.error_box.connect(lambda title, msg: self.err_msg.showMessage(msg))
        # Menu actions
        self.ui.actionCommit.triggered.connect(self.commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)
        self.ui.actionView_history.triggered.connect(self.show_history_dialog)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.menuEdit.aboutToShow.connect(self._handle_menu_edit_about_to_show)
        self.ui.actionImport.triggered.connect(self.show_import_file_dialog)
        self.ui.actionExport.triggered.connect(self.export_database)
        self.ui.actionLoadTemplate.triggered.connect(self.load_template)
        self.ui.actionSaveAsTemplate.triggered.connect(self.save_as_template)
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionRemove_selection.triggered.connect(self.remove_selection)
        self.ui.actionManage_parameter_tags.triggered.connect(self.show_manage_parameter_tags_form)
        self.ui.actionMass_remove_items.triggered.connect(self.show_mass_remove_items_form)
        self.parameter_tag_toolbar.manage_tags_action_triggered.connect(self.show_manage_parameter_tags_form)
        self.parameter_tag_toolbar.tag_button_toggled.connect(self._handle_tag_button_toggled)
        self.ui.treeView_parameter_value_list.customContextMenuRequested.connect(
            self.show_parameter_value_list_context_menu
        )
        self.parameter_value_list_model.remove_selection_requested.connect(self.remove_parameter_value_lists)

    @Slot(int)
    def update_undo_redo_actions(self, index):
        undo_ages = {db_map: self.db_mngr.undo_stack[db_map].undo_age for db_map in self.db_maps}
        redo_ages = {db_map: self.db_mngr.undo_stack[db_map].redo_age for db_map in self.db_maps}
        undo_ages = {db_map: age for db_map, age in undo_ages.items() if age is not None}
        redo_ages = {db_map: age for db_map, age in redo_ages.items() if age is not None}
        new_undo_action = self.db_mngr.undo_action[max(undo_ages, key=undo_ages.get, default=self.db_map)]
        new_redo_action = self.db_mngr.redo_action[min(redo_ages, key=redo_ages.get, default=self.db_map)]
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
        self.parameter_tag_toolbar.init_toolbar()

    @Slot(str)
    def add_message(self, msg):
        """Appends regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        if self.silenced:
            return
        self.notification_stack.push(msg)

    def restore_dock_widgets(self):
        """Docks all floating and or hidden QDockWidgets back to the window."""
        for dock in self.findChildren(QDockWidget):
            dock.setVisible(True)
            dock.setFloating(False)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.parameter_tag_toolbar.setVisible(True)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)

    @Slot()
    def _handle_menu_edit_about_to_show(self):
        """Runs when the edit menu from the main menubar is about to show.
        Enables or disables actions according to selection status."""
        self.ui.actionCopy.setEnabled(self._focused_widget_has_callable("copy"))
        self.ui.actionRemove_selection.setEnabled(self._focused_widget_can_remove_selections())
        object_classes_selected = self._focused_widgets_model_has_non_empty_list("selected_object_class_indexes")
        objects_selected = self._focused_widgets_model_has_non_empty_list("selected_object_indexes")
        relationship_classes_selected = self._focused_widgets_model_has_non_empty_list(
            "selected_relationship_class_indexes"
        )
        relationships_selected = self._focused_widgets_model_has_non_empty_list("selected_relationship_indexes")
        self.ui.actionEdit_object_classes.setEnabled(object_classes_selected)
        self.ui.actionEdit_objects.setEnabled(objects_selected)
        self.ui.actionEdit_relationship_classes.setEnabled(relationship_classes_selected)
        self.ui.actionEdit_relationships.setEnabled(relationships_selected)
        self.ui.actionPaste.setEnabled(self._focused_widget_has_callable("paste"))

    def selected_entity_class_ids(self, entity_class_type):
        """Returns object class ids selected in object tree *and* parameter tag toolbar."""
        if self.selected_param_def_ids[entity_class_type] is None:
            return None
        tree_class_ids = self.selected_ent_cls_ids[entity_class_type]
        tag_class_ids = dict()
        for db_map, class_id in self.selected_param_def_ids[entity_class_type]:
            tag_class_ids.setdefault(db_map, set()).add(class_id)
        result = dict()
        for db_map in tree_class_ids.keys() | tag_class_ids.keys():
            tree_cls_ids = tree_class_ids.get(db_map, set())
            tag_cls_ids = tag_class_ids.get(db_map, set())
            if tree_cls_ids == set():
                result[db_map] = tag_cls_ids
            elif tag_cls_ids == set():
                result[db_map] = tree_cls_ids
            else:
                result[db_map] = tree_cls_ids & tag_cls_ids
        return result

    @Slot(bool)
    def remove_selection(self, checked=False):
        """Removes selection of items."""
        focus_widget = self.focusWidget()
        while focus_widget is not self:
            if hasattr(focus_widget, "model") and callable(focus_widget.model):
                model = focus_widget.model()
                if hasattr(model, "remove_selection_requested"):
                    model.remove_selection_requested.emit()
                    break
            focus_widget = focus_widget.parentWidget()

    @Slot(bool)
    def copy(self, checked=False):
        """Copies data to clipboard."""
        self._call_on_focused_widget("copy")

    @Slot(bool)
    def paste(self, checked=False):
        """Pastes data from clipboard."""
        self._call_on_focused_widget("paste")

    @Slot(bool)
    def load_template(self, checked=False):
        """Loads JSON template."""
        if not all(self.db_mngr.undo_stack[db_map].isClean() for db_map in self.db_maps):
            commit_warning = QMessageBox(parent=self)
            commit_warning.setText("Please commit or rollback before loading a template.")
            commit_warning.setStandardButtons(QMessageBox.Ok)
            commit_warning.exec()
            return
        self.qsettings.beginGroup(self.settings_group)
        file_path, _ = get_open_file_name_in_last_dir(
            self.qsettings, "loadTemplate", self, "Load template", self._get_base_dir(), "Template file (*.json)"
        )
        self.qsettings.endGroup()
        if not file_path:  # File selection cancelled
            return
        with open(file_path) as f:
            data = json.load(f)
        self.import_data(data)
        self.msg.emit(f"Template {file_path} successfully loaded.")

    @Slot(bool)
    def save_as_template(self, checked=False):
        self.qsettings.beginGroup(self.settings_group)
        self.template_file_path, _ = get_save_file_name_in_last_dir(
            self.qsettings, "saveAsTemplate", self, "Save as template", self._get_base_dir(), "Template file (*.json)"
        )
        self.qsettings.endGroup()
        if not self.template_file_path:  # File selection cancelled
            return
        dialog = CreateTemplateDialog(self, self.db_mngr, *self.db_maps)
        dialog.data_submitted.connect(self.do_save_as_template)
        dialog.show()

    @Slot(object)
    def do_save_as_template(self, db_map_selected_item_types):
        """Saves a db as a JSON template."""
        data = {}
        for db_map, selected_item_types in db_map_selected_item_types.items():
            export_items = dict()
            export_items["object_classes"] = "object class" in selected_item_types
            export_items["relationship_classes"] = "relationship class" in selected_item_types
            export_items["objects"] = "object" in selected_item_types
            export_items["relationships"] = "relationship" in selected_item_types
            export_items["object_parameters"] = export_items["relationship_parameters"] = (
                "parameter definition" in selected_item_types
            )
            export_items["object_parameter_values"] = export_items["relationship_parameter_values"] = (
                "parameter value" in selected_item_types
            )
            export_items["parameter_value_lists"] = "parameter value list" in selected_item_types
            # export_items["parameter_tags"] = "parameter tag" in selected_item_types
            for key, items in export_data(db_map, **export_items).items():
                data.setdefault(key, []).extend(items)
        indent = 4 * " "
        json_data = "{{{0}{1}{0}}}".format(
            "\n" if data else "",
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
                    for key, values in data.items()
                ]
            ),
        )
        with open(self.template_file_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        self.msg.emit(f"Template {self.template_file_path} successfully saved.")

    @Slot(bool)
    def show_import_file_dialog(self, checked=False):
        """Shows dialog to allow user to select a file to import."""
        dialog = ImportDialog(self.qsettings, parent=self)
        dialog.exec()

    @Slot(dict)
    def import_data(self, data):
        self.db_mngr.import_data(self.db_maps, data)

    @Slot(bool)
    def export_database(self, checked=False):
        """Exports data from database into a file."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        db_map = self._select_database()
        if db_map is None:  # Database selection cancelled
            return
        self.qsettings.beginGroup(self.settings_group)
        file_path, _ = get_save_file_name_in_last_dir(
            self.qsettings, "exportDB", self, "Export to file", self._get_base_dir(), "Excel file (*.xlsx)"
        )
        self.qsettings.endGroup()
        if not file_path:  # File selection cancelled
            return
        self.export_to_excel(db_map, file_path)

    def _select_database(self):
        """
        Lets user select a database from available databases.

        Shows a dialog from which user can select a single database.
        If there is only a single database it is selected automatically and no dialog is shown.

        Returns:
             the database map of the database or None if no database was selected
        """
        if len(self.db_maps) == 1:
            return next(iter(self.db_maps))
        db_names = [x.codename for x in self.db_maps]
        selected_database, ok = QInputDialog.getItem(
            self, "Select database", "Select database to export", db_names, editable=False
        )
        if not ok:
            return None
        return self.db_maps[db_names.index(selected_database)]

    @busy_effect
    def export_to_excel(self, db_map, file_path):
        """Exports data from database into Excel file."""
        filename = os.path.split(file_path)[1]
        try:
            export_spine_database_to_xlsx(db_map, file_path)
            self.msg.emit(f"File {file_path} successfully exported.")
        except PermissionError:
            self.msg_error.emit(
                "Unable to export to file <b>{0}</b>.<br/>" "Close the file in Excel and try again.".format(filename)
            )
        except OSError:
            self.msg_error.emit("[OSError] Unable to export to file <b>{0}</b>".format(filename))

    def reload_session(self, db_maps):
        """Reloads data from given db_maps."""
        self.init_models()
        self.db_mngr.fetch_db_maps_for_listener(self, *db_maps)
        db_names = ", ".join([x.codename for x in db_maps])
        self.msg.emit(f"Reloaded databases {db_names}")

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
        if cookie is self:
            db_names = ", ".join([x.codename for x in db_maps])
            msg = f"All changes in {db_names} committed successfully."
            self.msg.emit(msg)
        else:  # Commit done by an 'outside force'.
            self.reload_session(db_maps)

    def receive_session_rolled_back(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        self.init_models()
        self.db_mngr.fetch_db_maps_for_listener(self, *db_maps)
        db_names = ", ".join([x.codename for x in db_maps])
        msg = f"All changes in {db_names} rolled back successfully."
        self.msg.emit(msg)

    def receive_session_refreshed(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        self.init_models()
        self.db_mngr.fetch_db_maps_for_listener(self, *db_maps)
        self.msg.emit("Session refreshed.")

    @Slot("QVariant", bool)
    def _handle_tag_button_toggled(self, db_map_ids, checked):
        """Updates filter according to selected tags.
        """
        for db_map, id_ in db_map_ids:
            if checked:
                self.selected_parameter_tag_ids.setdefault(db_map, set()).add(id_)
            else:
                self.selected_parameter_tag_ids[db_map].remove(id_)
        selected_param_defs = self.db_mngr.find_cascading_parameter_definitions_by_tag(self.selected_parameter_tag_ids)
        if any(v for v in self.selected_parameter_tag_ids.values()) and not any(
            v for v in selected_param_defs.values()
        ):
            # There are tags selected but no matching parameter definitions ~> we need to reject them all
            self.selected_param_def_ids["object class"] = None
            self.selected_param_def_ids["relationship class"] = None
        else:
            self.selected_param_def_ids["object class"] = {}
            self.selected_param_def_ids["relationship class"] = {}
            for db_map, param_defs in selected_param_defs.items():
                for param_def in param_defs:
                    if "object_class_id" in param_def:
                        self.selected_param_def_ids["object class"].setdefault(
                            (db_map, param_def["object_class_id"]), set()
                        ).add(param_def["id"])
                    elif "relationship_class_id" in param_def:
                        self.selected_param_def_ids["relationship class"].setdefault(
                            (db_map, param_def["relationship_class_id"]), set()
                        ).add(param_def["id"])
        self.update_filter()

    @Slot(bool)
    def show_manage_parameter_tags_form(self, checked=False):
        dialog = ManageParameterTagsDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    @Slot("QPoint")
    def show_parameter_value_list_context_menu(self, pos):
        """
        Shows the context menu for parameter value list tree view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_parameter_value_list.indexAt(pos)
        global_pos = self.ui.treeView_parameter_value_list.viewport().mapToGlobal(pos)
        parameter_value_list_context_menu = ParameterValueListContextMenu(self, global_pos, index)
        parameter_value_list_context_menu.deleteLater()
        option = parameter_value_list_context_menu.get_action()
        if option == "Copy":
            self.ui.treeView_parameter_value_list.copy()
        elif option == "Remove selection":
            self.remove_parameter_value_lists()
        parameter_value_list_context_menu.deleteLater()

    @Slot()
    def remove_parameter_value_lists(self):
        """Removes selection of parameter value-lists.
        """
        db_map_typed_data_to_rm = {}
        db_map_data_to_upd = {}
        selected = [
            self.parameter_value_list_model.item_from_index(index)
            for index in self.ui.treeView_parameter_value_list.selectionModel().selectedIndexes()
        ]
        for db_item in self.parameter_value_list_model._invisible_root_item.children:
            db_map_typed_data_to_rm[db_item.db_map] = {"parameter value list": []}
            db_map_data_to_upd[db_item.db_map] = []
            for list_item in reversed(db_item.children[:-1]):
                if list_item.id:
                    if list_item in selected:
                        db_map_typed_data_to_rm[db_item.db_map]["parameter value list"].append(
                            {"id": list_item.id, "name": list_item.name}
                        )
                        continue
                    curr_value_list = list_item.compile_value_list()
                    value_list = [
                        value
                        for value_item, value in zip(list_item.children, curr_value_list)
                        if value_item not in selected
                    ]
                    if not value_list:
                        db_map_typed_data_to_rm[db_item.db_map]["parameter value list"].append(
                            {"id": list_item.id, "name": list_item.name}
                        )
                        continue
                    if value_list != curr_value_list:
                        item = {"id": list_item.id, "value_list": value_list}
                        db_map_data_to_upd[db_item.db_map].append(item)
                else:
                    # WIP lists, just remove everything selected
                    if list_item in selected:
                        db_item.remove_children(list_item.child_number(), list_item.child_number())
                        continue
                    for value_item in reversed(list_item.children[:-1]):
                        if value_item in selected:
                            list_item.remove_children(value_item.child_number(), value_item.child_number())
        self.db_mngr.update_parameter_value_lists(db_map_data_to_upd)
        self.db_mngr.remove_items(db_map_typed_data_to_rm)
        self.ui.treeView_parameter_value_list.selectionModel().clearSelection()

    @Slot(bool)
    def show_mass_remove_items_form(self, checked=False):
        dialog = MassRemoveItemsDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    @busy_effect
    @Slot("QModelIndex")
    def show_parameter_value_editor(self, index):
        """Shows the parameter value editor for the given index of given table view.
        """
        editor = ParameterValueEditor(index, parent=self)
        editor.show()

    def notify_items_changed(self, action, item_type, db_map_data):
        """Enables or disables actions and informs the user about what just happened."""
        count = sum(len(data) for data in db_map_data.values())
        msg = f"Successfully {action} {count} {item_type} item(s)"
        self.msg.emit(msg)

    def receive_object_classes_fetched(self, db_map_data):
        pass

    def receive_objects_fetched(self, db_map_data):
        pass

    def receive_relationship_classes_fetched(self, db_map_data):
        pass

    def receive_relationships_fetched(self, db_map_data):
        pass

    def receive_parameter_definitions_fetched(self, db_map_data):
        pass

    def receive_parameter_values_fetched(self, db_map_data):
        pass

    def receive_parameter_value_lists_fetched(self, db_map_data):
        self.notify_items_changed("fetched", "parameter value list", db_map_data)
        self.parameter_value_list_model.receive_parameter_value_lists_added(db_map_data)

    def receive_parameter_tags_fetched(self, db_map_data):
        self.notify_items_changed("fetched", "parameter tag", db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_added(db_map_data)

    def receive_object_classes_added(self, db_map_data):
        self.notify_items_changed("added", "object class", db_map_data)

    def receive_objects_added(self, db_map_data):
        self.notify_items_changed("added", "object", db_map_data)

    def receive_relationship_classes_added(self, db_map_data):
        self.notify_items_changed("added", "relationship class", db_map_data)

    def receive_relationships_added(self, db_map_data):
        self.notify_items_changed("added", "relationship", db_map_data)

    def receive_parameter_definitions_added(self, db_map_data):
        self.notify_items_changed("added", "parameter definition", db_map_data)

    def receive_parameter_values_added(self, db_map_data):
        self.notify_items_changed("added", "parameter value", db_map_data)

    def receive_parameter_value_lists_added(self, db_map_data):
        self.notify_items_changed("added", "parameter value list", db_map_data)
        self.parameter_value_list_model.receive_parameter_value_lists_added(db_map_data)

    def receive_parameter_tags_added(self, db_map_data):
        self.notify_items_changed("added", "parameter tag", db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_added(db_map_data)

    def receive_object_classes_updated(self, db_map_data):
        self.notify_items_changed("updated", "object class", db_map_data)

    def receive_objects_updated(self, db_map_data):
        self.notify_items_changed("updated", "object", db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        self.notify_items_changed("updated", "relationship class", db_map_data)

    def receive_relationships_updated(self, db_map_data):
        self.notify_items_changed("updated", "relationship", db_map_data)

    def receive_parameter_definitions_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter definition", db_map_data)

    def receive_parameter_values_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter value", db_map_data)

    def receive_parameter_value_lists_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter value list", db_map_data)
        self.parameter_value_list_model.receive_parameter_value_lists_updated(db_map_data)

    def receive_parameter_tags_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter tag", db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_updated(db_map_data)

    def receive_parameter_definition_tags_set(self, db_map_data):
        self.notify_items_changed("set", "parameter definition tag", db_map_data)

    def receive_object_classes_removed(self, db_map_data):
        self.notify_items_changed("removed", "object class", db_map_data)

    def receive_objects_removed(self, db_map_data):
        self.notify_items_changed("removed", "object", db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        self.notify_items_changed("removed", "relationship class", db_map_data)

    def receive_relationships_removed(self, db_map_data):
        self.notify_items_changed("removed", "relationship", db_map_data)

    def receive_parameter_definitions_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter definition", db_map_data)

    def receive_parameter_values_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter value", db_map_data)

    def receive_parameter_value_lists_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter value list", db_map_data)
        self.parameter_value_list_model.receive_parameter_value_lists_removed(db_map_data)

    def receive_parameter_tags_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter tag", db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_removed(db_map_data)

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
            if not self.db_mngr.remove_db_map_listener(db_map, self):
                event.ignore()
                return
            self.db_mngr.unset_logger_for_db_map(db_map)
        # Save UI form state
        self.save_window_state()
        QMainWindow.closeEvent(self, event)

    def _focused_widget_can_remove_selections(self):
        """Returns True if the currently focused widget or one of its parents can respond to actinoRemove_selection."""
        focus_widget = self.focusWidget()
        while focus_widget is not self:
            if hasattr(focus_widget, "model") and callable(focus_widget.model):
                model = focus_widget.model()
                if hasattr(model, "remove_selection_requested"):
                    return True
            focus_widget = focus_widget.parentWidget()
        return False

    def _focused_widget_has_callable(self, callable_name):
        """Returns True if the currently focused widget or one of its ancestors has the given callable."""
        focus_widget = self.focusWidget()
        while focus_widget is not None and focus_widget is not self:
            if hasattr(focus_widget, callable_name):
                method = getattr(focus_widget, callable_name)
                if callable(method):
                    return True
            focus_widget = focus_widget.parentWidget()
        return False

    def _focused_widgets_model_has_non_empty_list(self, list_name):
        """Returns True if the currently focused widget's or one of its ancestors' model has a non empty list."""
        focus_widget = self.focusWidget()
        while focus_widget is not self:
            if hasattr(focus_widget, "model") and callable(focus_widget.model):
                model = focus_widget.model()
                if hasattr(model, list_name):
                    a_list = getattr(model, list_name)
                    return bool(a_list)
            focus_widget = focus_widget.parentWidget()
        return False

    def _call_on_focused_widget(self, callable_name):
        """Calls the given callable on the currently focused widget or one of its ancestors."""
        focus_widget = self.focusWidget()
        while focus_widget is not None and focus_widget is not self:
            if hasattr(focus_widget, callable_name):
                method = getattr(focus_widget, callable_name)
                if callable(method):
                    method()
                    break
            focus_widget = focus_widget.parentWidget()


class DataStoreForm(TabularViewMixin, GraphViewMixin, ParameterViewMixin, TreeViewMixin, DataStoreFormBase):
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
        self.apply_tree_style()
        self.restore_ui()
        toc = time.process_time()
        self.msg.emit("Data store view created in {0:.2f} seconds".format(toc - tic))
        self.db_mngr.fetch_db_maps_for_listener(self, *self.db_maps)

    def connect_signals(self):
        super().connect_signals()
        self.ui.actionTree_style.triggered.connect(self.apply_tree_style)
        self.ui.actionGraph_style.triggered.connect(self.apply_graph_style)
        self.ui.actionTabular_style.triggered.connect(self.apply_tabular_style)

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
        self.resize(self._size)

    @Slot(bool)
    def apply_tree_style(self, checked=False):
        """Applies the tree style, inspired in the former tree view."""
        self.begin_style_change()
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_object_parameter_value, Qt.Horizontal)
        self.splitDockWidget(
            self.ui.dockWidget_object_parameter_value, self.ui.dockWidget_parameter_value_list, Qt.Horizontal
        )
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_relationship_tree, Qt.Vertical)
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
        self.ui.dockWidget_item_palette.hide()
        self.ui.dockWidget_pivot_table.hide()
        self.ui.dockWidget_frozen_table.hide()
        docks = [
            self.ui.dockWidget_object_tree,
            self.ui.dockWidget_object_parameter_value,
            self.ui.dockWidget_parameter_value_list,
        ]
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.3 * width, 0.5 * width, 0.2 * width], Qt.Horizontal)
        self.end_style_change()

    @Slot(bool)
    def apply_tabular_style(self, checked=False):
        """Applies the tree style, inspired in the former tabular view."""
        self.begin_style_change()
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_pivot_table, Qt.Horizontal)
        self.splitDockWidget(self.ui.dockWidget_pivot_table, self.ui.dockWidget_frozen_table, Qt.Horizontal)
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_relationship_tree, Qt.Vertical)
        self.ui.dockWidget_entity_graph.hide()
        self.ui.dockWidget_item_palette.hide()
        self.ui.dockWidget_object_parameter_value.hide()
        self.ui.dockWidget_object_parameter_definition.hide()
        self.ui.dockWidget_relationship_parameter_value.hide()
        self.ui.dockWidget_relationship_parameter_definition.hide()
        self.ui.dockWidget_parameter_value_list.hide()
        self.parameter_tag_toolbar.hide()
        docks = [self.ui.dockWidget_object_tree, self.ui.dockWidget_pivot_table, self.ui.dockWidget_frozen_table]
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.3 * width, 0.5 * width, 0.2 * width], Qt.Horizontal)
        self.end_style_change()

    @Slot(bool)
    def apply_graph_style(self, checked=False):
        """Applies the tree style, inspired in the former graph view."""
        self.begin_style_change()
        self.ui.dockWidget_parameter_value_list.hide()
        self.ui.dockWidget_pivot_table.hide()
        self.ui.dockWidget_frozen_table.hide()
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_entity_graph, Qt.Horizontal)
        self.splitDockWidget(self.ui.dockWidget_entity_graph, self.ui.dockWidget_object_parameter_value, Qt.Vertical)
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_relationship_tree, Qt.Vertical)
        self.splitDockWidget(self.ui.dockWidget_entity_graph, self.ui.dockWidget_item_palette, Qt.Horizontal)
        self.tabify_and_raise(
            [
                self.ui.dockWidget_object_parameter_value,
                self.ui.dockWidget_object_parameter_definition,
                self.ui.dockWidget_relationship_parameter_value,
                self.ui.dockWidget_relationship_parameter_definition,
            ]
        )
        docks = [self.ui.dockWidget_object_tree, self.ui.dockWidget_entity_graph]
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.3 * width, 0.7 * width], Qt.Horizontal)
        docks = [self.ui.dockWidget_entity_graph, self.ui.dockWidget_object_parameter_value]
        height = sum(d.size().height() for d in docks)
        self.resizeDocks(docks, [0.7 * height, 0.3 * height], Qt.Vertical)
        docks = [self.ui.dockWidget_entity_graph, self.ui.dockWidget_item_palette]
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.9 * width, 0.1 * width], Qt.Horizontal)
        self.end_style_change()
        self.ui.graphicsView.reset_zoom()

    def _get_base_dir(self):
        project = self.db_mngr.parent()
        if project is None:
            return APPLICATION_PATH
        return project.project_dir
