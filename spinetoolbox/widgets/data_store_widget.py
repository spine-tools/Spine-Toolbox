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
from PySide2.QtWidgets import (
    QMainWindow,
    QErrorMessage,
    QDockWidget,
    QMessageBox,
    QDialog,
    QFileDialog,
    QInputDialog,
    QTreeView,
    QTableView,
)
from PySide2.QtCore import Qt, Signal, Slot, QSettings
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon
from spinedb_api import copy_database
from ..config import MAINWINDOW_SS
from .edit_db_items_dialogs import ManageParameterTagsDialog
from .custom_menus import ParameterValueListContextMenu
from ..widgets.parameter_view_mixin import ParameterViewMixin
from ..widgets.tree_view_mixin import TreeViewMixin
from ..widgets.graph_view_mixin import GraphViewMixin
from ..widgets.tabular_view_mixin import TabularViewMixin
from ..widgets.toolbars import ParameterTagToolBar
from ..widgets.db_session_history_dialog import DBSessionHistoryDialog
from ..widgets.notification import NotificationStack
from ..mvcmodels.parameter_value_list_model import ParameterValueListModel
from ..helpers import busy_effect
from .import_widget import ImportDialog
from ..spine_io.exporters.excel import export_spine_database_to_xlsx


class DataStoreFormBase(QMainWindow):
    """Base class for DataStoreForm"""

    msg = Signal(str)
    msg_error = Signal(str)

    def __init__(self, db_mngr, *db_urls):
        """Initializes form.

        Args:
            db_mngr (SpineDBManager): The manager to use
            *db_urls (tuple): Database url, codename.
        """
        super().__init__(flags=Qt.Window)
        from ..ui.data_store_view import Ui_MainWindow

        self.db_urls = list(db_urls)
        self.db_url = self.db_urls[0]
        self.db_mngr = db_mngr
        self.db_maps = [
            self.db_mngr.get_db_map_for_listener(self, url, codename=codename) for url, codename in self.db_urls
        ]
        self.db_map = self.db_maps[0]
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.takeCentralWidget()
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStyleSheet(MAINWINDOW_SS)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.err_msg = QErrorMessage(self)
        self.notification_stack = NotificationStack(self)
        self.err_msg.setWindowTitle("Error")
        self.parameter_tag_toolbar = ParameterTagToolBar(self, self.db_mngr, *self.db_maps)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)
        self.selected_ent_cls_ids = {"object class": {}, "relationship class": {}}
        self.selected_ent_ids = {"object": {}, "relationship": {}}
        self.selected_parameter_tag_ids = dict()
        self.selected_param_def_ids = {"object class": {}, "relationship class": {}}
        self.parameter_value_list_model = ParameterValueListModel(self, self.db_mngr, *self.db_maps)
        fm = QFontMetrics(QFont("", 0))
        self.default_row_height = 1.2 * fm.lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        self._selection_source = None
        self._selection_locked = False
        self._focusable_childs = [self.ui.treeView_parameter_value_list]
        self.settings_group = 'treeViewWidget'
        self.undo_action = None
        self.redo_action = None
        db_names = ", ".join(["{0}".format(db_map.codename) for db_map in self.db_maps])
        self.setWindowTitle("{0}[*] - Data store view".format(db_names))
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
        # Menu actions
        self.ui.actionCommit.triggered.connect(self.commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)
        self.ui.actionView_history.triggered.connect(self.show_history_dialog)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.menuEdit.aboutToShow.connect(self._handle_menu_edit_about_to_show)
        self.ui.actionImport.triggered.connect(self.show_import_file_dialog)
        self.ui.actionExport.triggered.connect(self.export_database)
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionRemove_selection.triggered.connect(self.remove_selection)
        self.ui.actionManage_parameter_tags.triggered.connect(self.show_manage_parameter_tags_form)
        self.parameter_tag_toolbar.manage_tags_action_triggered.connect(self.show_manage_parameter_tags_form)
        self.parameter_tag_toolbar.tag_button_toggled.connect(self._handle_tag_button_toggled)
        self.ui.treeView_parameter_value_list.selectionModel().selectionChanged.connect(
            self._handle_parameter_value_list_selection_changed
        )
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
        selection_available = self._selection_source is not None
        self.ui.actionCopy.setEnabled(selection_available)
        self.ui.actionRemove_selection.setEnabled(selection_available)
        object_classes_selected = self._selection_source is self.ui.treeView_object and bool(
            self._selection_source.model().selected_object_class_indexes
        )
        objects_selected = self._selection_source is self.ui.treeView_object and bool(
            self._selection_source.model().selected_object_indexes
        )
        relationship_classes_selected = self._selection_source in (
            self.ui.treeView_object,
            self.ui.treeView_relationship,
        ) and bool(self._selection_source.model().selected_relationship_class_indexes)
        relationships_selected = self._selection_source in (
            self.ui.treeView_object,
            self.ui.treeView_relationship,
        ) and bool(self._selection_source.model().selected_relationship_indexes)
        self.ui.actionEdit_object_classes.setEnabled(object_classes_selected)
        self.ui.actionEdit_objects.setEnabled(objects_selected)
        self.ui.actionEdit_relationship_classes.setEnabled(relationship_classes_selected)
        self.ui.actionEdit_relationships.setEnabled(relationships_selected)
        self.ui.actionPaste.setEnabled(True)
        focus_widget = self._find_focus_child()
        self.ui.actionPaste.setEnabled(focus_widget is not None)

    def _find_focus_child(self):
        for child in self._focusable_childs:
            if child.hasFocus():
                return child

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

    def _accept_selection(self, widget):
        """Clears selection from all widgets except the given one, so there's only one selection
        in the form at a time. In addition, registers the given widget as the official source
        for all operations involving selections (copy, remove, edit), but only in case it *has* a selection."""
        if not self._selection_locked:
            self._selection_source = widget if widget.selectionModel().hasSelection() else None
            self._selection_locked = True
            for w in self.findChildren(QTreeView) + self.findChildren(QTableView):
                if w != widget:
                    w.selectionModel().clearSelection()
            self._selection_locked = False
            return True
        return False

    @Slot(bool)
    def remove_selection(self, checked=False):
        """Removes selection of items."""
        if not self._selection_source:
            return
        self._selection_source.model().remove_selection_requested.emit()

    @Slot(bool)
    def copy(self, checked=False):
        """Copies data to clipboard."""
        if not self._selection_source:
            return
        self._selection_source.copy()

    @Slot(bool)
    def paste(self, checked=False):
        """Pastes data from clipboard."""
        focus_widget = self._find_focus_child()
        if not focus_widget:
            return
        focus_widget.paste()

    @Slot(bool)
    def show_import_file_dialog(self, checked=False):
        """Shows dialog to allow user to select a file to import."""
        db_map = next(iter(self.db_maps))
        if db_map.has_pending_changes():
            commit_warning = QMessageBox(parent=self)
            commit_warning.setText("Please commit or rollback before importing data")
            commit_warning.setStandardButtons(QMessageBox.Ok)
            commit_warning.exec()
            return
        dialog = ImportDialog(self.qsettings, parent=self)
        # assume that dialog is modal, if not use accepted, rejected signals
        if dialog.exec() == QDialog.Accepted:
            if db_map.has_pending_changes():
                self.msg.emit("Import successful")
                self.init_models()
        dialog.close()
        dialog.deleteLater()

    @Slot(bool)
    def export_database(self, checked=False):
        """Exports data from database into a file."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        db_map = self._select_database()
        if db_map is None:  # Database selection cancelled
            return
        proj_dir = self.db_mngr.parent().project_dir  # Parent should be SpineToolboxProject
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export to file", proj_dir, "Excel file (*.xlsx);;SQlite database (*.sqlite *.db)"
        )
        if not file_path:  # File selection cancelled
            return
        if selected_filter.startswith("SQlite"):
            self.export_to_sqlite(db_map, file_path)
        elif selected_filter.startswith("Excel"):
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
            self.msg.emit("Excel file successfully exported.")
        except PermissionError:
            self.msg_error.emit(
                "Unable to export to file <b>{0}</b>.<br/>" "Close the file in Excel and try again.".format(filename)
            )
        except OSError:
            self.msg_error.emit("[OSError] Unable to export to file <b>{0}</b>".format(filename))

    @busy_effect
    def export_to_sqlite(self, db_map, file_path):
        """Exports data from database into SQlite file."""
        dst_url = 'sqlite:///{0}'.format(file_path)
        copy_database(dst_url, db_map, overwrite=True)
        self.msg.emit("SQlite file successfully exported.")

    @Slot(bool)
    def refresh_session(self, checked=False):
        self.db_mngr.refresh_session(*self.db_maps)

    @Slot(bool)
    def commit_session(self, checked=False):
        """Commits session."""
        self.db_mngr.commit_session(*self.db_maps)

    @Slot(bool)
    def rollback_session(self, checked=False):
        self.db_mngr.rollback_session(*self.db_maps)

    def receive_session_committed(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        db_names = ", ".join([x.codename for x in db_maps])
        msg = f"All changes in {db_names} committed successfully."
        self.msg.emit(msg)

    def receive_session_rolled_back(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        self.init_models()
        db_names = ", ".join([x.codename for x in db_maps])
        msg = f"All changes in {db_names} rolled back successfully."
        self.msg.emit(msg)

    @Slot(bool)
    def receive_session_refreshed(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        self.init_models()
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

    @Slot("QItemSelection", "QItemSelection")
    def _handle_parameter_value_list_selection_changed(self, selected, deselected):
        """Accepts selection."""
        self._accept_selection(self.ui.treeView_parameter_value_list)

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

    def notify_items_changed(self, action, item_type, db_map_data):
        """Enables or disables actions and informs the user about what just happened."""
        count = sum(len(data) for data in db_map_data.values())
        msg = f"Successfully {action} {count} {item_type} item(s)"
        self.msg.emit(msg)

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
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)

    def save_window_state(self):
        """Save window state parameters (size, position, state) via QSettings."""
        self.qsettings.beginGroup(self.settings_group)
        self.qsettings.setValue("windowSize", self.size())
        self.qsettings.setValue("windowPosition", self.pos())
        self.qsettings.setValue("windowState", self.saveState(version=1))
        self.qsettings.setValue("windowMaximized", self.windowState() == Qt.WindowMaximized)
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
        # Save UI form state
        self.save_window_state()
        event.accept()


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
        self.ui.dockWidget_relationship_tree.hide()
        self.ui.dockWidget_parameter_value_list.hide()
        self.ui.dockWidget_pivot_table.hide()
        self.ui.dockWidget_frozen_table.hide()
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_entity_graph, Qt.Horizontal)
        self.splitDockWidget(self.ui.dockWidget_entity_graph, self.ui.dockWidget_object_parameter_value, Qt.Vertical)
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_item_palette, Qt.Vertical)
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
        self.end_style_change()
        self.ui.graphicsView.reset_zoom()
