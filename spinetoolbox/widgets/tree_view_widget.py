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
Contains the TreeViewForm class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import os
import time  # just to measure loading time and sqlalchemy ORM performance
from PySide2.QtWidgets import QFileDialog, QDockWidget, QInputDialog, QTreeView, QTableView, QMessageBox, QDialog
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtGui import QIcon
from spinedb_api import copy_database, SpineDBAPIError
from .data_store_widget import DataStoreForm
from .custom_menus import (
    EditableParameterValueContextMenu,
    EntityTreeContextMenu,
    ParameterContextMenu,
    ParameterValueListContextMenu,
)
from .custom_qdialog import RemoveTreeItemsDialog
from .import_widget import ImportDialog
from .report_plotting_failure import report_plotting_failure
from ..mvcmodels.entity_tree_models import ObjectTreeModel, RelationshipTreeModel
from ..excel_import_export import import_xlsx_to_db, export_spine_database_to_xlsx
from ..datapackage_import_export import datapackage_to_spine
from ..helpers import busy_effect, rows_to_row_count_tuples
from ..plotting import plot_selection, PlottingError, GraphAndTreeViewPlottingHints


class TreeViewForm(DataStoreForm):
    """
    A widget to show and edit Spine objects in a data store.

    Attributes:
        project (SpineToolboxProject): The project instance that owns this form
        db_maps (dict): named DiffDatabaseMapping instances
    """

    object_class_selection_available = Signal("bool", name="object_class_selection_available")
    object_selection_available = Signal("bool", name="object_selection_available")
    relationship_class_selection_available = Signal("bool", name="relationship_class_selection_available")
    relationship_selection_available = Signal("bool", name="relationship_selection_available")
    object_tree_selection_available = Signal("bool", name="object_tree_selection_available")
    relationship_tree_selection_available = Signal("bool", name="relationship_tree_selection_available")
    obj_parameter_definition_selection_available = Signal("bool", name="obj_parameter_definition_selection_available")
    obj_parameter_value_selection_available = Signal("bool", name="obj_parameter_value_selection_available")
    rel_parameter_definition_selection_available = Signal("bool", name="rel_parameter_definition_selection_available")
    rel_parameter_value_selection_available = Signal("bool", name="rel_parameter_value_selection_available")
    parameter_value_list_selection_available = Signal("bool", name="parameter_value_list_selection_available")

    def __init__(self, project, db_maps):
        """Initialize class."""
        from ..ui.tree_view_form import Ui_MainWindow

        tic = time.process_time()
        super().__init__(project, Ui_MainWindow(), db_maps)
        self.takeCentralWidget()
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self, db_maps)
        self.relationship_tree_model = RelationshipTreeModel(self, db_maps)
        self.selected_rel_tree_indexes = {}
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_relationship.setModel(self.relationship_tree_model)
        # Others
        self.widget_with_selection = None
        self.paste_to_widget = None
        self.settings_group = 'treeViewWidget'
        self.do_clear_other_selections = True
        self.restore_dock_widgets()
        self.restore_ui()
        # init models
        self.init_models()
        self.setup_delegates()
        self.add_toggle_view_actions()
        self.connect_signals()
        self.setWindowTitle("Data store tree view    -- {} --".format(", ".join(list(db_maps.keys()))))
        toc = time.process_time()
        self.msg.emit("Tree view form created in {} seconds".format(toc - tic))

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_relationship_tree.toggleViewAction())
        super().add_toggle_view_actions()

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        qApp.focusChanged.connect(self.update_paste_action)  # pylint: disable=undefined-variable
        # Action availability
        self.object_class_selection_available.connect(self.ui.actionEdit_object_classes.setEnabled)
        self.object_selection_available.connect(self.ui.actionEdit_objects.setEnabled)
        self.relationship_class_selection_available.connect(self.ui.actionEdit_relationship_classes.setEnabled)
        self.relationship_selection_available.connect(self.ui.actionEdit_relationships.setEnabled)
        self.object_tree_selection_available.connect(self._handle_object_tree_selection_available)
        self.relationship_tree_selection_available.connect(self._handle_relationship_tree_selection_available)
        self.obj_parameter_definition_selection_available.connect(
            self._handle_obj_parameter_definition_selection_available
        )
        self.obj_parameter_value_selection_available.connect(self._handle_obj_parameter_value_selection_available)
        self.rel_parameter_definition_selection_available.connect(
            self._handle_rel_parameter_definition_selection_available
        )
        self.rel_parameter_value_selection_available.connect(self._handle_rel_parameter_value_selection_available)
        self.parameter_value_list_selection_available.connect(self._handle_parameter_value_list_selection_available)
        # Menu actions
        # Import export
        self.ui.actionImport.triggered.connect(self.show_import_file_dialog)
        self.ui.actionExport.triggered.connect(self.export_database)
        # Copy and paste
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        # Add and edit object tree
        self.ui.actionAdd_object_classes.triggered.connect(self.show_add_object_classes_form)
        self.ui.actionAdd_objects.triggered.connect(self.show_add_objects_form)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.show_add_relationship_classes_form)
        self.ui.actionAdd_relationships.triggered.connect(self.show_add_relationships_form)
        self.ui.actionEdit_object_classes.triggered.connect(self.show_edit_object_classes_form)
        self.ui.actionEdit_objects.triggered.connect(self.show_edit_objects_form)
        self.ui.actionEdit_relationship_classes.triggered.connect(self.show_edit_relationship_classes_form)
        self.ui.actionEdit_relationships.triggered.connect(self.show_edit_relationships_form)
        # Remove
        self.ui.actionRemove_selection.triggered.connect(self.remove_selection)
        self.object_tree_model.remove_selection_requested.connect(self.show_remove_object_tree_items_form)
        self.relationship_tree_model.remove_selection_requested.connect(self.show_remove_relationship_tree_items_form)
        self.object_parameter_definition_model.remove_selection_requested.connect(
            self.remove_object_parameter_definitions
        )
        self.object_parameter_value_model.remove_selection_requested.connect(self.remove_object_parameter_values)
        self.relationship_parameter_definition_model.remove_selection_requested.connect(
            self.remove_relationship_parameter_definitions
        )
        self.relationship_parameter_value_model.remove_selection_requested.connect(
            self.remove_relationship_parameter_values
        )
        self.parameter_value_list_model.remove_selection_requested.connect(self.remove_parameter_value_lists)
        # Parameter tags
        self.ui.actionManage_parameter_tags.triggered.connect(self.show_manage_parameter_tags_form)
        # Dock Widgets
        self.ui.actionRestore_Dock_Widgets.triggered.connect(self.restore_dock_widgets)
        # Object tree misc
        self.ui.treeView_object.edit_key_pressed.connect(self.edit_object_tree_items)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.find_next_relationship)
        # Relationship tree
        self.ui.treeView_relationship.selectionModel().selectionChanged.connect(
            self._handle_relationship_tree_selection_changed
        )
        self.ui.treeView_relationship.edit_key_pressed.connect(self.edit_relationship_tree_items)
        self.ui.treeView_relationship.customContextMenuRequested.connect(self.show_relationship_tree_context_menu)
        # Parameter tables selection changes
        self.ui.tableView_object_parameter_definition.selectionModel().selectionChanged.connect(
            self._handle_object_parameter_definition_selection_changed
        )
        self.ui.tableView_object_parameter_value.selectionModel().selectionChanged.connect(
            self._handle_object_parameter_value_selection_changed
        )
        self.ui.tableView_relationship_parameter_definition.selectionModel().selectionChanged.connect(
            self._handle_relationship_parameter_definition_selection_changed
        )
        self.ui.tableView_relationship_parameter_value.selectionModel().selectionChanged.connect(
            self._handle_relationship_parameter_value_selection_changed
        )
        # Parameter value_list tree selection changed
        self.ui.treeView_parameter_value_list.selectionModel().selectionChanged.connect(
            self._handle_parameter_value_list_selection_changed
        )
        # Parameter tables context menu requested
        self.ui.tableView_object_parameter_definition.customContextMenuRequested.connect(
            self.show_object_parameter_context_menu
        )
        self.ui.tableView_object_parameter_value.customContextMenuRequested.connect(
            self.show_object_parameter_value_context_menu
        )
        self.ui.tableView_relationship_parameter_definition.customContextMenuRequested.connect(
            self.show_relationship_parameter_context_menu
        )
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.connect(
            self.show_relationship_parameter_value_context_menu
        )
        # Parameter value_list context menu requested
        self.ui.treeView_parameter_value_list.customContextMenuRequested.connect(
            self.show_parameter_value_list_context_menu
        )

    @Slot(name="restore_dock_widgets")
    def restore_dock_widgets(self):
        """Dock all floating and or hidden QDockWidgets back to the window at 'factory' positions."""
        # Place docks
        for dock in self.findChildren(QDockWidget):
            dock.setVisible(True)
            dock.setFloating(False)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_object_parameter_value, Qt.Horizontal)
        # Split and tabify
        self.splitDockWidget(self.ui.dockWidget_object_tree, self.ui.dockWidget_relationship_tree, Qt.Vertical)
        self.splitDockWidget(
            self.ui.dockWidget_object_parameter_value, self.ui.dockWidget_parameter_value_list, Qt.Horizontal
        )
        self.splitDockWidget(
            self.ui.dockWidget_object_parameter_value, self.ui.dockWidget_relationship_parameter_value, Qt.Vertical
        )
        self.tabifyDockWidget(self.ui.dockWidget_object_parameter_value, self.ui.dockWidget_object_parameter_definition)
        self.tabifyDockWidget(
            self.ui.dockWidget_relationship_parameter_value, self.ui.dockWidget_relationship_parameter_definition
        )
        self.ui.dockWidget_object_parameter_value.raise_()
        self.ui.dockWidget_relationship_parameter_value.raise_()

    def update_copy_and_remove_actions(self):
        """Update copy and remove actions according to selections across the widgets."""
        if not self.widget_with_selection:
            self.ui.actionCopy.setEnabled(False)
            self.ui.actionRemove_selection.setEnabled(False)
        else:
            name = self.widget_with_selection.accessibleName()
            self.ui.actionCopy.setEnabled(True)
            self.ui.actionRemove_selection.setEnabled(True)
            self.ui.actionRemove_selection.setIcon(self.widget_with_selection.model().remove_icon)

    @Slot("bool", name="_handle_object_tree_selection_available")
    def _handle_object_tree_selection_available(self, on):
        if on:
            self.widget_with_selection = self.ui.treeView_object
        elif self.ui.treeView_object == self.widget_with_selection:
            self.widget_with_selection = None
        self.update_copy_and_remove_actions()

    @Slot("bool", name="_handle_relationship_tree_selection_available")
    def _handle_relationship_tree_selection_available(self, on):
        if on:
            self.widget_with_selection = self.ui.treeView_relationship
        elif self.ui.treeView_relationship == self.widget_with_selection:
            self.widget_with_selection = None
        self.update_copy_and_remove_actions()

    @Slot("bool", name="_handle_obj_parameter_definition_selection_available")
    def _handle_obj_parameter_definition_selection_available(self, on):
        if on:
            self.widget_with_selection = self.ui.tableView_object_parameter_definition
        elif self.ui.tableView_object_parameter_definition == self.widget_with_selection:
            self.widget_with_selection = None
        self.update_copy_and_remove_actions()

    @Slot("bool", name="_handle_obj_parameter_value_selection_available")
    def _handle_obj_parameter_value_selection_available(self, on):
        if on:
            self.widget_with_selection = self.ui.tableView_object_parameter_value
        elif self.ui.tableView_object_parameter_value == self.widget_with_selection:
            self.widget_with_selection = None
        self.update_copy_and_remove_actions()

    @Slot("bool", name="_handle_rel_parameter_definition_selection_available")
    def _handle_rel_parameter_definition_selection_available(self, on):
        if on:
            self.widget_with_selection = self.ui.tableView_relationship_parameter_definition
        elif self.ui.tableView_relationship_parameter_definition == self.widget_with_selection:
            self.widget_with_selection = None
        self.update_copy_and_remove_actions()

    @Slot("bool", name="_handle_rel_parameter_value_selection_available")
    def _handle_rel_parameter_value_selection_available(self, on):
        if on:
            self.widget_with_selection = self.ui.tableView_relationship_parameter_value
        elif self.ui.tableView_relationship_parameter_value == self.widget_with_selection:
            self.widget_with_selection = None
        self.update_copy_and_remove_actions()

    @Slot("bool", name="_handle_parameter_value_list_selection_available")
    def _handle_parameter_value_list_selection_available(self, on):
        if on:
            self.widget_with_selection = self.ui.treeView_parameter_value_list
        elif self.ui.treeView_parameter_value_list == self.widget_with_selection:
            self.widget_with_selection = None
        self.update_copy_and_remove_actions()

    @Slot("QWidget", "QWidget", name="update_paste_action")
    def update_paste_action(self, old, new):
        self.paste_to_widget = None
        self.ui.actionPaste.setEnabled(False)
        try:
            if new.canPaste():
                self.paste_to_widget = new
                self.ui.actionPaste.setEnabled(True)
        except AttributeError:
            pass

    @Slot("bool", name="copy")
    def copy(self, checked=False):
        """Copy data to clipboard."""
        if not self.widget_with_selection:
            return
        self.widget_with_selection.copy()

    @Slot("bool", name="paste")
    def paste(self, checked=False):
        """Paste data from clipboard."""
        if not self.paste_to_widget:
            return
        self.paste_to_widget.paste()

    @Slot("bool", name="remove_selection")
    def remove_selection(self, checked=False):
        """Remove selection of items."""
        # TODO: Try and do this in the corresponding classes
        if not self.widget_with_selection:
            return
        self.widget_with_selection.model().remove_selection_requested.emit()

    @Slot("QItemSelection", "QItemSelection", name="_handle_object_parameter_definition_selection_changed")
    def _handle_object_parameter_definition_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        model = self.ui.tableView_object_parameter_definition.selectionModel()
        self.obj_parameter_definition_selection_available.emit(model.hasSelection())
        if self.do_clear_other_selections:
            self.clear_other_selections(self.ui.tableView_object_parameter_definition)

    @Slot("QItemSelection", "QItemSelection", name="_handle_object_parameter_value_selection_changed")
    def _handle_object_parameter_value_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        model = self.ui.tableView_object_parameter_value.selectionModel()
        self.obj_parameter_value_selection_available.emit(model.hasSelection())
        if self.do_clear_other_selections:
            self.clear_other_selections(self.ui.tableView_object_parameter_value)

    @Slot("QItemSelection", "QItemSelection", name="_handle_relationship_parameter_definition_selection_changed")
    def _handle_relationship_parameter_definition_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        model = self.ui.tableView_relationship_parameter_definition.selectionModel()
        self.rel_parameter_definition_selection_available.emit(model.hasSelection())
        if self.do_clear_other_selections:
            self.clear_other_selections(self.ui.tableView_relationship_parameter_definition)

    @Slot("QItemSelection", "QItemSelection", name="_handle_relationship_parameter_value_selection_changed")
    def _handle_relationship_parameter_value_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        model = self.ui.tableView_relationship_parameter_value.selectionModel()
        self.rel_parameter_value_selection_available.emit(model.hasSelection())
        if self.do_clear_other_selections:
            self.clear_other_selections(self.ui.tableView_relationship_parameter_value)

    @Slot("QItemSelection", "QItemSelection", name="_handle_parameter_value_list_selection_changed")
    def _handle_parameter_value_list_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        model = self.ui.treeView_parameter_value_list.selectionModel()
        self.parameter_value_list_selection_available.emit(model.hasSelection())
        if self.do_clear_other_selections:
            self.clear_other_selections(self.ui.treeView_parameter_value_list)

    @Slot("int", name="_handle_object_parameter_tab_changed")
    def _handle_object_parameter_tab_changed(self, index):
        """Update filter."""
        if index == 0:
            self.object_parameter_value_model.update_filter()
        else:
            self.object_parameter_definition_model.update_filter()

    @Slot("int", name="_handle_relationship_parameter_tab_changed")
    def _handle_relationship_parameter_tab_changed(self, index):
        """Update filter."""
        if index == 0:
            self.relationship_parameter_value_model.update_filter()
        else:
            self.relationship_parameter_definition_model.update_filter()

    @Slot("bool", name="show_import_file_dialog")
    def show_import_file_dialog(self, checked=False):
        """Show dialog to allow user to select a file to import."""
        db_map = next(iter(self.db_maps.values()))
        if db_map.has_pending_changes():
            commit_warning = QMessageBox()
            commit_warning.setText("Please commit or rollback before importing data")
            commit_warning.setStandardButtons(QMessageBox.Ok)
            commit_warning.exec()
            return
        dialog = ImportDialog(parent=self)
        # assume that dialog is modal, if not use accepted, rejected signals
        if dialog.exec() == QDialog.Accepted:
            if db_map.has_pending_changes():
                self.msg.emit("Import was successfull")
                self.commit_available.emit(True)
                self.init_models()

    @busy_effect
    def import_file(self, file_path, checked=False):
        """Import data from file into current database."""
        if file_path.lower().endswith('datapackage.json'):
            try:
                datapackage_to_spine(self.db_map, file_path)
                self.msg.emit("Datapackage successfully imported.")
                self.commit_available.emit(True)
                self.init_models()
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
        elif file_path.lower().endswith('xlsx'):
            error_log = []
            try:
                _, error_log = import_xlsx_to_db(self.db_map, file_path)
                self.msg.emit("Excel file successfully imported.")
                self.commit_available.emit(True)
                self.init_models()
            except SpineDBAPIError as e:
                self.msg_error.emit("Unable to import Excel file: {}".format(e.msg))
            finally:
                if error_log:
                    msg = (
                        "Something went wrong in importing an Excel file "
                        "into the current session. Here is the error log:\n\n{0}".format([e.msg for e in error_log])
                    )
                    # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
                    self.msg_error.emit(msg)

    @Slot("bool", name="export_database")
    def export_database(self, checked=False):
        """Exports a database to a file."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        db_map = self._select_database()
        if db_map is None:  # Database selection cancelled
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export to file", self._project.project_dir, "Excel file (*.xlsx);;SQlite database (*.sqlite *.db)"
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
            return next(iter(self.db_maps.values()))
        db_names = list(self.db_maps.keys())
        selected_database, ok = QInputDialog.getItem(
            self, "Select database", "Select database to export", db_names, editable=False
        )
        if not ok:
            return None
        return self.db_maps[selected_database]

    @busy_effect
    def export_to_excel(self, db_map, file_path):
        """Export data from database into Excel file."""
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
        """Export data from database into SQlite file."""
        dst_url = 'sqlite:///{0}'.format(file_path)
        copy_database(dst_url, db_map, overwrite=True)
        self.msg.emit("SQlite file successfully exported.")

    def init_models(self):
        """Initialize models."""
        super().init_models()
        self.init_relationship_tree_model()

    def init_object_tree_model(self):
        """Initialize object tree model."""
        super().init_object_tree_model()
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.has_children())

    def init_relationship_tree_model(self):
        """Initialize relationship tree model."""
        self.relationship_tree_model.build_tree()
        self.ui.treeView_relationship.expand(self.relationship_tree_model.root_index)
        self.ui.treeView_relationship.resizeColumnToContents(0)

    @Slot("QModelIndex", name="find_next_relationship")
    def find_next_relationship(self, index):
        """Expand next occurrence of a relationship in object tree."""
        next_index = self.object_tree_model.find_next_relationship_index(index)
        if not next_index:
            return
        self.ui.treeView_object.setCurrentIndex(next_index)
        self.ui.treeView_object.scrollTo(next_index)
        self.ui.treeView_object.expand(next_index)

    def clear_other_selections(self, *skip_widgets):
        """Clear selections in all widgets except `skip_widgets`."""
        self.do_clear_other_selections = False
        for w in self.findChildren(QTreeView) + self.findChildren(QTableView):
            if w in skip_widgets:
                continue
            w.selectionModel().clearSelection()
        self.do_clear_other_selections = True

    @busy_effect
    @Slot("QItemSelection", "QItemSelection", name="_handle_object_tree_selection_changed")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Called when the object tree selection changes.
        Set default rows and apply filters on parameter models."""
        for index in deselected.indexes():
            self.object_tree_model.deselect_index(index)
        for index in selected.indexes():
            self.object_tree_model.select_index(index)
        self.object_tree_selection_available.emit(any(v for v in self.object_tree_model.selected_indexes.values()))
        self.object_class_selection_available.emit(bool(self.object_tree_model.selected_object_class_indexes))
        self.object_selection_available.emit(bool(self.object_tree_model.selected_object_indexes))
        if self.do_clear_other_selections:
            self.relationship_class_selection_available.emit(
                bool(self.object_tree_model.selected_relationship_class_indexes)
            )
            self.relationship_selection_available.emit(bool(self.object_tree_model.selected_relationship_indexes))
            self.clear_other_selections(self.ui.treeView_object)
            self.set_default_parameter_data(self.ui.treeView_object.currentIndex())
            self.update_filter()

    @busy_effect
    @Slot("QItemSelection", "QItemSelection", name="_handle_relationship_tree_selection_changed")
    def _handle_relationship_tree_selection_changed(self, selected, deselected):
        """Called when the relationship tree selection changes.
        Set default rows and apply filters on parameter models."""
        for index in deselected.indexes():
            self.relationship_tree_model.deselect_index(index)
        for index in selected.indexes():
            self.relationship_tree_model.select_index(index)
        self.relationship_tree_selection_available.emit(
            any(v for v in self.relationship_tree_model.selected_indexes.values())
        )
        if self.do_clear_other_selections:
            self.relationship_class_selection_available.emit(
                bool(self.relationship_tree_model.selected_relationship_class_indexes)
            )
            self.relationship_selection_available.emit(bool(self.relationship_tree_model.selected_relationship_indexes))
            self.clear_other_selections(self.ui.treeView_relationship)
            self.set_default_parameter_data(self.ui.treeView_relationship.currentIndex())
            self.update_filter()

    def update_filter(self):
        """Update filters on parameter models according to selected and deselected object tree indexes."""
        # Prepare stuff
        # Collect object tree indexes
        rel_inds = {
            (db_map, ind): None
            for ind in self.object_tree_model.selected_relationship_indexes
            for db_map in ind.internalPointer().db_maps
        }
        rel_cls_inds = {
            (db_map, ind): None
            for ind in self.object_tree_model.selected_relationship_class_indexes
            for db_map in ind.internalPointer().db_maps
        }
        rel_cls_inds.update({(db_map, ind.parent()): None for db_map, ind in rel_inds})
        obj_inds = {
            (db_map, ind): None
            for ind in self.object_tree_model.selected_object_indexes
            for db_map in ind.internalPointer().db_maps
        }
        obj_inds.update({(db_map, ind.parent()): None for db_map, ind in rel_cls_inds})
        obj_cls_inds = {
            (db_map, ind): None
            for ind in self.object_tree_model.selected_object_class_indexes
            for db_map in ind.internalPointer().db_maps
        }
        obj_cls_inds.update({(db_map, ind.parent()): None for db_map, ind in obj_inds})
        # Add relationship tree indexes
        more_rel_inds = {
            (db_map, ind): None
            for ind in self.relationship_tree_model.selected_relationship_indexes
            for db_map in ind.internalPointer().db_maps
        }
        more_rel_cls_inds = {
            (db_map, ind): None
            for ind in self.relationship_tree_model.selected_relationship_class_indexes
            for db_map in ind.internalPointer().db_maps
        }
        rel_inds.update(more_rel_inds)
        rel_cls_inds.update({(db_map, ind.parent()): None for db_map, ind in more_rel_inds})
        rel_cls_inds.update(more_rel_cls_inds)
        # Update selected
        self.selected_object_class_ids = dict()
        for db_map, ind in obj_cls_inds:
            d = ind.internalPointer().db_map_data(db_map)
            self.selected_object_class_ids.setdefault(db_map, set()).add(d['id'])
        self.selected_object_ids = dict()
        for db_map, ind in obj_inds:
            d = ind.internalPointer().db_map_data(db_map)
            self.selected_object_ids.setdefault((db_map, d['class_id']), set()).add(d['id'])
        self.selected_relationship_class_ids = dict()
        for db_map, ind in rel_cls_inds:
            d = ind.internalPointer().db_map_data(db_map)
            self.selected_relationship_class_ids.setdefault(db_map, set()).add(d['id'])
        self.selected_object_id_lists = dict()
        for db_map, ind in rel_inds:
            d = ind.internalPointer().db_map_data(db_map)
            self.selected_object_id_lists.setdefault((db_map, d['class_id']), set()).add(d['object_id_list'])
        self.do_update_filter()

    @Slot("QPoint", name="show_object_tree_context_menu")
    def show_object_tree_context_menu(self, pos):
        """Context menu for object tree.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_object.indexAt(pos)
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        object_tree_context_menu = EntityTreeContextMenu(self, global_pos, index)
        option = object_tree_context_menu.get_action()
        if option == "Copy text":
            self.ui.treeView_object.copy()
        elif option == "Add object classes":
            self.show_add_object_classes_form()
        elif option == "Add objects":
            self.call_show_add_objects_form(index)
        elif option == "Add relationship classes":
            self.call_show_add_relationship_classes_form(index)
        elif option == "Add relationships":
            self.call_show_add_relationships_form_from_object_tree(index)
        elif option == "Edit object classes":
            self.show_edit_object_classes_form()
        elif option == "Edit objects":
            self.show_edit_objects_form()
        elif option == "Edit relationship classes":
            self.show_edit_relationship_classes_form()
        elif option == "Edit relationships":
            self.show_edit_relationships_form()
        elif option == "Find next":
            self.find_next_relationship(index)
        elif option == "Remove selection":
            self.show_remove_object_tree_items_form()
        elif option == "Fully expand":
            self.fully_expand_selection()
        elif option == "Fully collapse":
            self.fully_collapse_selection()
        else:  # No option selected
            pass
        object_tree_context_menu.deleteLater()

    @Slot("QPoint", name="show_relationship_tree_context_menu")
    def show_relationship_tree_context_menu(self, pos):
        """Context menu for relationship tree.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_relationship.indexAt(pos)
        global_pos = self.ui.treeView_relationship.viewport().mapToGlobal(pos)
        relationship_tree_context_menu = EntityTreeContextMenu(self, global_pos, index)
        option = relationship_tree_context_menu.get_action()
        if option == "Copy text":
            self.ui.treeView_relationship.copy()
        elif option == "Add relationship classes":
            self.show_add_relationship_classes_form()
        elif option == "Add relationships":
            self.call_show_add_relationships_form_from_relationship_tree(index)
        elif option == "Edit relationship classes":
            self.show_edit_relationship_classes_form()
        elif option == "Edit relationships":
            self.show_edit_relationships_form()
        elif option == "Remove selection":
            self.show_remove_relationship_tree_items_form()
        else:  # No option selected
            pass
        relationship_tree_context_menu.deleteLater()

    @busy_effect
    def fully_expand_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            for item in self.object_tree_model.visit_all(index):
                self.ui.treeView_object.expand(self.object_tree_model.index_from_item(item))

    @busy_effect
    def fully_collapse_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            if index.column() != 0:
                continue
            for item in self.object_tree_model.visit_all(index):
                self.ui.treeView_object.collapse(self.object_tree_model.index_from_item(item))

    def call_show_add_objects_form(self, index):
        class_name = index.internalPointer().unique_identifier
        self.show_add_objects_form(class_name=class_name)

    def call_show_add_relationship_classes_form(self, index):
        object_class_one_name = index.internalPointer().unique_identifier
        self.show_add_relationship_classes_form(object_class_one_name=object_class_one_name)

    def call_show_add_relationships_form_from_object_tree(self, index):
        item = index.internalPointer()
        relationship_class_key = item.unique_identifier
        object_name = item._parent.unique_identifier
        object_class_name = item._parent._parent.unique_identifier
        self.show_add_relationships_form(
            relationship_class_key=relationship_class_key, object_class_name=object_class_name, object_name=object_name
        )

    def call_show_add_relationships_form_from_relationship_tree(self, index):
        item = index.internalPointer()
        relationship_class_key = item.unique_identifier
        self.show_add_relationships_form(relationship_class_key=relationship_class_key)

    def add_object_classes(self, object_class_d):
        """Insert new object classes."""
        if super().add_object_classes(object_class_d):
            self.ui.actionExport.setEnabled(True)
            return True
        return False

    def add_relationship_classes_to_models(self, db_map, added):
        super().add_relationship_classes_to_models(db_map, added)
        self.relationship_tree_model.add_relationship_classes(db_map, added)

    def add_relationships_to_models(self, db_map, added):
        super().add_relationships_to_models(db_map, added)
        self.relationship_tree_model.add_relationships(db_map, added)

    def edit_object_tree_items(self):
        """Called when F2 is pressed while the object tree has focus.
        Call the appropriate method to show the edit form,
        depending on the current index."""
        current = self.ui.treeView_object.currentIndex()
        current_type = current.data(Qt.UserRole)
        if current_type == 'object_class':
            self.show_edit_object_classes_form()
        elif current_type == 'object':
            self.show_edit_objects_form()
        elif current_type == 'relationship_class':
            self.show_edit_relationship_classes_form()
        elif current_type == 'relationship':
            self.show_edit_relationships_form()

    def edit_relationship_tree_items(self):
        """Called when F2 is pressed while the relationship tree has focus.
        Call the appropriate method to show the edit form,
        depending on the current index."""
        current = self.ui.treeView_object.currentIndex()
        current_type = current.data(Qt.UserRole)
        if current_type == 'relationship_class':
            self.show_edit_relationship_classes_form()
        elif current_type == 'relationship':
            self.show_edit_relationships_form()

    def update_object_classes_in_models(self, db_map, updated):
        super().update_object_classes_in_models(db_map, updated)
        self.relationship_tree_model.update_object_classes(db_map, updated)

    def update_objects_in_models(self, db_map, updated):
        super().update_objects_in_models(db_map, updated)
        self.relationship_tree_model.update_objects(db_map, updated)

    def update_relationship_classes_in_models(self, db_map, updated):
        super().update_relationship_classes_in_models(db_map, updated)
        self.relationship_tree_model.update_relationship_classes(db_map, updated)

    def update_relationships_in_models(self, db_map, updated):
        super().update_relationships_in_models(db_map, updated)
        self.relationship_tree_model.update_relationships(db_map, updated)

    @Slot(name="show_remove_object_tree_items_form")
    def show_remove_object_tree_items_form(self):
        """Show form to remove items from object treeview."""
        kwargs = {
            item_type: [ind.data(Qt.UserRole + 1) for ind in self.selected_obj_tree_indexes.get(item_type, {})]
            for item_type in ('object_class', 'object', 'relationship_class', 'relationship')
        }
        dialog = RemoveTreeItemsDialog(self, **kwargs)
        dialog.show()

    @Slot(name="show_remove_relationship_tree_items_form")
    def show_remove_relationship_tree_items_form(self):
        """Show form to remove items from relationship treeview."""
        kwargs = {
            item_type: [ind.data(Qt.UserRole + 1) for ind in self.selected_rel_tree_indexes.get(item_type, {})]
            for item_type in ('relationship_class', 'relationship')
        }
        dialog = RemoveTreeItemsDialog(self, **kwargs)
        dialog.show()

    @busy_effect
    def remove_tree_items(self, item_d):
        """Remove items from tree views."""
        removed = 0
        for db_map, item_type_ids in item_d.items():
            object_classes = item_type_ids.get("object_class", ())
            objects = item_type_ids.get("object", ())
            relationship_classes = item_type_ids.get("relationship_class", ())
            relationships = item_type_ids.get("relationship", ())
            object_class_ids = {x['id'] for x in object_classes}
            object_ids = {x['id'] for x in objects}
            relationship_class_ids = {x['id'] for x in relationship_classes}
            relationship_ids = {x['id'] for x in relationships}
            try:
                db_map.remove_items(
                    object_class_ids=object_class_ids,
                    object_ids=object_ids,
                    relationship_class_ids=relationship_class_ids,
                    relationship_ids=relationship_ids,
                )
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            if object_class_ids:
                self.object_tree_model.remove_object_classes(db_map, object_class_ids)
                self.relationship_tree_model.remove_object_classes(db_map, object_class_ids)
                self.object_parameter_definition_model.remove_object_classes(db_map, object_classes)
                self.object_parameter_value_model.remove_object_classes(db_map, object_classes)
                self.relationship_parameter_definition_model.remove_object_classes(db_map, object_classes)
                self.relationship_parameter_value_model.remove_object_classes(db_map, object_classes)
            if object_ids:
                self.object_tree_model.remove_objects(db_map, object_ids)
                self.relationship_tree_model.remove_objects(db_map, object_ids)
                self.object_parameter_value_model.remove_objects(db_map, objects)
                self.relationship_parameter_value_model.remove_objects(db_map, objects)
            if relationship_class_ids:
                self.object_tree_model.remove_relationship_classes(db_map, relationship_class_ids)
                self.relationship_tree_model.remove_relationship_classes(db_map, relationship_class_ids)
                self.relationship_parameter_definition_model.remove_relationship_classes(db_map, relationship_classes)
                self.relationship_parameter_value_model.remove_relationship_classes(db_map, relationship_classes)
            if relationship_ids:
                self.object_tree_model.remove_relationships(db_map, relationship_ids)
                self.relationship_tree_model.remove_relationships(db_map, relationship_ids)
                self.relationship_parameter_value_model.remove_relationships(db_map, relationships)
            removed += len(object_class_ids) + len(object_ids) + len(relationship_class_ids) + len(relationship_ids)
        if not removed:
            return
        self.commit_available.emit(True)
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.hasChildren())
        self.msg.emit("Successfully removed {} item(s).".format(removed))
        # Update selected (object and relationship) tree indexes
        self.selected_obj_tree_indexes = {}
        for index in self.ui.treeView_object.selectedIndexes():
            item_type = index.data(Qt.UserRole)
            self.selected_obj_tree_indexes.setdefault(item_type, {})[index] = None
        self.selected_rel_tree_indexes = {}
        for index in self.ui.treeView_relationship.selectedIndexes():
            item_type = index.data(Qt.UserRole)
            self.selected_rel_tree_indexes.setdefault(item_type, {})[index] = None
        # Emit selection_available signals
        self.object_tree_selection_available.emit(any(v for v in self.selected_obj_tree_indexes.values()))
        self.object_class_selection_available.emit(len(self.selected_obj_tree_indexes.get('object_class', {})) > 0)
        self.object_selection_available.emit(len(self.selected_obj_tree_indexes.get('object', {})) > 0)
        self.relationship_tree_selection_available.emit(any(v for v in self.selected_rel_tree_indexes.values()))
        self.relationship_class_selection_available.emit(
            len(self.selected_obj_tree_indexes.get('relationship_class', {}))
            + len(self.selected_rel_tree_indexes.get('relationship_class', {}))
            > 0
        )
        self.relationship_selection_available.emit(
            len(self.selected_obj_tree_indexes.get('relationship', {}))
            + len(self.selected_rel_tree_indexes.get('relationship', {}))
            > 0
        )

    @Slot("QPoint", name="show_object_parameter_value_context_menu")
    def show_object_parameter_value_context_menu(self, pos):
        """Context menu for object parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        self._show_parameter_context_menu(
            pos, self.ui.tableView_object_parameter_value, "value", self.remove_object_parameter_values
        )

    @Slot("QPoint", name="show_relationship_parameter_value_context_menu")
    def show_relationship_parameter_value_context_menu(self, pos):
        """Context menu for relationship parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        self._show_parameter_context_menu(
            pos, self.ui.tableView_relationship_parameter_value, "value", self.remove_relationship_parameter_values
        )

    @Slot("QPoint", name="show_object_parameter_context_menu")
    def show_object_parameter_context_menu(self, pos):
        """Context menu for object parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        self._show_parameter_context_menu(pos, self.ui.tableView_object_parameter_definition, "default_value")

    @Slot("QPoint", name="show_relationship_parameter_context_menu")
    def show_relationship_parameter_context_menu(self, pos):
        """Context menu for relationship parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        self._show_parameter_context_menu(pos, self.ui.tableView_relationship_parameter_definition, "default_value")

    def _show_parameter_context_menu(self, position, table_view, value_column_header):
        """
        Show a context menu for parameter tables.

        Args:
            position (QPoint): local mouse position in the table view
            table_view (QTableView): the table view where the context menu was triggered
            value_column_header (str): column header for editable/plottable values
        """
        index = table_view.indexAt(position)
        global_pos = table_view.mapToGlobal(position)
        model = table_view.model()
        flags = model.flags(index)
        editable = (flags & Qt.ItemIsEditable) == Qt.ItemIsEditable
        is_value = model.headerData(index.column(), Qt.Horizontal) == value_column_header
        if editable and is_value:
            menu = EditableParameterValueContextMenu(self, global_pos, index)
        else:
            menu = ParameterContextMenu(self, global_pos, index)
        option = menu.get_action()
        if option == "Open in editor...":
            self.show_parameter_value_editor(index, table_view)
        elif option == "Plot":
            selection = table_view.selectedIndexes()
            try:
                hints = GraphAndTreeViewPlottingHints(table_view)
                plot_widget = plot_selection(model, selection, hints)
            except PlottingError as error:
                report_plotting_failure(error)
                return
            if (
                table_view is self.ui.tableView_object_parameter_value
                or table_view is self.ui.tableView_object_parameter_definition
            ):
                plot_window_title = "Object parameter plot -- {} --".format(value_column_header)
            elif (
                table_view is self.ui.tableView_relationship_parameter_value
                or table_view is self.ui.tableView_relationship_parameter_definition
            ):
                plot_window_title = "Relationship parameter plot    -- {} --".format(value_column_header)
            else:
                plot_window_title = "Plot"
            plot_widget.setWindowTitle(plot_window_title)
            plot_widget.show()
        elif option == "Remove selection":
            table_view.model().remove_selection_requested.emit()
        elif option == "Copy":
            table_view.copy()
        elif option == "Paste":
            table_view.paste()
        menu.deleteLater()

    @Slot("QPoint", name="show_parameter_value_list_context_menu")
    def show_parameter_value_list_context_menu(self, pos):
        """
        Context menu for relationship parameter table view.

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

    @Slot(name="remove_object_parameter_values")
    def remove_object_parameter_values(self):
        """Remove selected rows from object parameter value table."""
        self._remove_parameter_values(self.ui.tableView_object_parameter_value)

    @Slot(name="remove_relationship_parameter_values")
    def remove_relationship_parameter_values(self):
        """Remove selected rows from relationship parameter value table."""
        self._remove_parameter_values(self.ui.tableView_relationship_parameter_value)

    def _remove_parameter_values(self, table_view):
        """
        Remove selected rows from parameter value table.

        Args:
            table_view (QTableView): remove selection from this view
        """
        selection = table_view.selectionModel().selection()
        rows = list()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            rows += range(top, bottom + 1)
        # Get parameters values grouped by db_map
        d = dict()
        model = table_view.model()
        for row in rows:
            db_map = model.item_at_row(row).db_map
            d.setdefault(db_map, set()).add(model.item_at_row(row).id)
        # Remove the parameter value rows
        for row, count in sorted(rows_to_row_count_tuples(rows), reverse=True):
            model.removeRows(row, count)
        # Remove from the db
        for db_map, parameter_value_ids in d.items():
            try:
                db_map.remove_items(parameter_value_ids=parameter_value_ids)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
        if rows:
            self.commit_available.emit(True)
            self.msg.emit("Successfully removed {} parameter value(s).".format(len(rows)))

    @Slot(name="remove_object_parameter_definitions")
    def remove_object_parameter_definitions(self):
        """Remove selected rows from object parameter definition table."""
        self._remove_parameter_definitions(
            self.ui.tableView_object_parameter_definition, self.object_parameter_value_model
        )

    @Slot(name="remove_relationship_parameter_definitions")
    def remove_relationship_parameter_definitions(self):
        """Remove selected rows from relationship parameter definition table."""
        self._remove_parameter_definitions(
            self.ui.tableView_relationship_parameter_definition, self.relationship_parameter_value_model
        )

    def _remove_parameter_definitions(self, table_view, value_model):
        """
        Remove selected rows from parameter table.

        Args:
            table_view (QTableView): remove rows from this table
            value_model (QAbstractTableModel): remove parameters from this model
        """
        selection = table_view.selectionModel().selection()
        rows = list()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            rows += range(top, bottom + 1)
        # Get parameters grouped by db_map
        d = dict()
        model = table_view.model()
        for row in rows:
            db_map = model.item_at_row(row).db_map
            if not db_map:
                continue
            d.setdefault(db_map, []).append(
                {"entity_class_id": model.item_at_row(row).entity_class.id, "id": model.item_at_row(row).id}
            )
        # Remove the parameter definition rows
        for row, count in sorted(rows_to_row_count_tuples(rows), reverse=True):
            model.removeRows(row, count)
        # Remove from the db and from the parameter value model
        for db_map, parameters in d.items():
            try:
                db_map.remove_items(parameter_definition_ids={x['id'] for x in parameters})
                value_model.remove_parameters(db_map, parameters)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
        if rows:
            self.commit_available.emit(True)
            self.msg.emit("Successfully removed {} parameter definition(s).".format(len(rows)))

    @Slot(name="remove_parameter_value_lists")
    def remove_parameter_value_lists(self):
        """Remove selection of parameter value_lists.
        """
        indexes = self.ui.treeView_parameter_value_list.selectedIndexes()
        value_indexes = {}
        list_indexes = {}
        for index in indexes:
            parent = index.parent()
            if not parent.isValid():
                continue
            if parent.internalPointer().level == 1:
                value_indexes.setdefault(parent, list()).append(index)
            elif parent.internalPointer().level == 0:
                list_indexes.setdefault(parent, list()).append(index)
        # Remove list indexes from value indexes, since they will be fully removed anyways
        for indexes in list_indexes.values():
            for index in indexes:
                value_indexes.pop(index, None)
        # Get items to update
        model = self.parameter_value_list_model
        item_d = dict()
        for parent, indexes in value_indexes.items():
            db_map = parent.parent().internalPointer().id
            id_ = parent.internalPointer().id
            removed_rows = [ind.row() for ind in indexes]
            all_rows = range(model.rowCount(parent) - 1)
            remaining_rows = [row for row in all_rows if row not in removed_rows]
            value_list = [model.index(row, 0, parent).data(Qt.EditRole) for row in remaining_rows]
            item_d.setdefault(db_map, {}).setdefault("to_upd", []).append(dict(id=id_, value_list=value_list))
        # Get ids to remove
        for parent, indexes in list_indexes.items():
            db_map = parent.internalPointer().id
            item_d.setdefault(db_map, {}).setdefault("to_rm", set()).update(ind.internalPointer().id for ind in indexes)
        for db_map, d in item_d.items():
            to_update = d.get("to_upd", None)
            to_remove = d.get("to_rm", None)
            try:
                if to_update:
                    # NOTE: SpineIntegrityError can never happen here... right???
                    db_map.update_wide_parameter_value_lists(*to_update)
                if to_remove:
                    db_map.remove_items(parameter_value_list_ids=to_remove)
                self.object_parameter_definition_model.clear_parameter_value_lists(db_map, to_remove)
                self.relationship_parameter_definition_model.clear_parameter_value_lists(db_map, to_remove)
            except SpineDBAPIError as e:
                self._tree_view_form.msg_error.emit(e.msg)
                return
        for parent, indexes in list_indexes.items():
            for row in sorted([ind.row() for ind in indexes], reverse=True):
                self.parameter_value_list_model.removeRow(row, parent)
        for parent, indexes in value_indexes.items():
            for row in sorted([ind.row() for ind in indexes], reverse=True):
                self.parameter_value_list_model.removeRow(row, parent)
        self.commit_available.emit(True)
        self.msg.emit("Successfully removed parameter value list(s).")
