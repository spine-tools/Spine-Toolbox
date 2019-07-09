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
import logging
from PySide2.QtWidgets import QFileDialog, QApplication, QDockWidget, QTreeView, QTableView
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtGui import QIcon
from ui.tree_view_form import Ui_MainWindow
from spinedb_api import SpineDBAPIError
from widgets.data_store_widget import DataStoreForm
from widgets.custom_menus import (
    ObjectTreeContextMenu,
    RelationshipTreeContextMenu,
    ParameterContextMenu,
    ParameterValueListContextMenu,
)
from widgets.custom_qdialog import RemoveTreeItemsDialog
from treeview_models import ObjectTreeModel, RelationshipTreeModel
from excel_import_export import import_xlsx_to_db, export_spine_database_to_xlsx
from spinedb_api import copy_database
from datapackage_import_export import datapackage_to_spine
from helpers import busy_effect


class TreeViewForm(DataStoreForm):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        project (SpineToolboxProject): The project instance that owns this form
        ui: UI definition of the form that is initialized
        db_maps: named DiffDatabaseMapping instances
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

    def __init__(self, data_store, **db_maps):
        """Initialize class."""
        tic = time.process_time()
        super().__init__(data_store, Ui_MainWindow(), **db_maps)
        self.takeCentralWidget()
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self)
        self.relationship_tree_model = RelationshipTreeModel(self)
        self.selected_rel_tree_indexes = {}
        # Context menus
        self.object_tree_context_menu = None
        self.relationship_tree_context_menu = None
        self.object_parameter_value_context_menu = None
        self.relationship_parameter_value_context_menu = None
        self.object_parameter_context_menu = None
        self.relationship_parameter_context_menu = None
        self.parameter_value_list_context_menu = None
        # Others
        self.widget_with_selection = None
        self.paste_to_widget = None
        self.fully_expand_icon = QIcon(":/icons/menu_icons/angle-double-right.svg")
        self.fully_collapse_icon = QIcon(":/icons/menu_icons/angle-double-left.svg")
        self.find_next_icon = QIcon(":/icons/menu_icons/ellipsis-h.png")
        self.settings_group = 'treeViewWidget'
        self.do_clear_other_selections = True
        self.restore_dock_widgets()
        self.restore_ui()
        # init models and views
        self.init_models()
        self.init_views()
        self.setup_delegates()
        self.add_toggle_view_actions()
        self.connect_signals()
        self.setWindowTitle(
            "Data store tree view    -- {} --".format(", ".join([self.db_map_to_name[x] for x in self.db_maps]))
        )
        toc = time.process_time()
        self.msg.emit("Tree view form created in {} seconds".format(toc - tic))

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_relationship_tree.toggleViewAction())
        super().add_toggle_view_actions()

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        qApp.focusChanged.connect(self.update_paste_action)  # qApp comes with PySide2.QtWidgets.QApplication
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
        self.ui.actionExport.triggered.connect(self.show_export_file_dialog)
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
        # Parameter tags
        self.ui.actionManage_parameter_tags.triggered.connect(self.show_manage_parameter_tags_form)
        # Dock Widgets
        self.ui.actionRestore_Dock_Widgets.triggered.connect(self.restore_dock_widgets)
        # Object tree misc
        self.ui.treeView_object.edit_key_pressed.connect(self.edit_object_tree_items)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.find_next_leaf)
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
            if name == "object tree":
                self.ui.actionRemove_selection.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
            elif name == "relationship tree":
                self.ui.actionRemove_selection.setIcon(QIcon(":/icons/menu_icons/cubes_minus.svg"))
            elif name == "object parameter definition":
                self.ui.actionRemove_selection.setIcon(QIcon(":/icons/menu_icons/cog_minus.svg"))
            elif name == "object parameter value":
                self.ui.actionRemove_selection.setIcon(QIcon(":/icons/menu_icons/cog_minus.svg"))
            elif name == "relationship parameter definition":
                self.ui.actionRemove_selection.setIcon(QIcon(":/icons/menu_icons/cog_minus.svg"))
            elif name == "relationship parameter value":
                self.ui.actionRemove_selection.setIcon(QIcon(":/icons/menu_icons/cog_minus.svg"))
            elif name == "parameter value list":
                self.ui.actionRemove_selection.setIcon(QIcon(":/icons/minus.png"))

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
        if not self.widget_with_selection:
            return
        name = self.widget_with_selection.accessibleName()
        if name == "object tree":
            self.show_remove_object_tree_items_form()
        elif name == "relationship tree":
            self.show_remove_relationship_tree_items_form()
        elif name == "object parameter definition":
            self.remove_object_parameter_definitions()
        elif name == "object parameter value":
            self.remove_object_parameter_values()
        elif name == "relationship parameter definition":
            self.remove_relationship_parameter_definitions()
        elif name == "relationship parameter value":
            self.remove_relationship_parameter_values()
        elif name == "parameter value list":
            self.remove_parameter_value_lists()

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
        answer = QFileDialog.getOpenFileName(self, "Select file to import", self._project.project_dir, "*.*")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self.import_file(file_path)

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
                insert_log, error_log = import_xlsx_to_db(self.db_map, file_path)
                self.msg.emit("Excel file successfully imported.")
                self.commit_available.emit(True)
                # logging.debug(insert_log)
                self.init_models()
            except SpineDBAPIError as e:
                self.msg_error.emit("Unable to import Excel file: {}".format(e.msg))
            finally:
                if not len(error_log) == 0:
                    msg = (
                        "Something went wrong in importing an Excel file "
                        "into the current session. Here is the error log:\n\n{0}".format([e.msg for e in error_log])
                    )
                    # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
                    self.msg_error.emit(msg)
                    # logging.debug(error_log)

    @Slot("bool", name="show_export_file_dialog")
    def show_export_file_dialog(self, checked=False):
        """Show dialog to allow user to select a file to export."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getSaveFileName(
            self, "Export to file", self._project.project_dir, "Excel file (*.xlsx);;SQlite database (*.sqlite *.db)"
        )
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        if answer[1].startswith("SQlite"):
            self.export_to_sqlite(file_path)
        elif answer[1].startswith("Excel"):
            self.export_to_excel(file_path)

    @busy_effect
    def export_to_excel(self, file_path):
        """Export data from database into Excel file."""
        filename = os.path.split(file_path)[1]
        try:
            export_spine_database_to_xlsx(self.db_map, file_path)
            self.msg.emit("Excel file successfully exported.")
        except PermissionError:
            self.msg_error.emit(
                "Unable to export to file <b>{0}</b>.<br/>" "Close the file in Excel and try again.".format(filename)
            )
        except OSError:
            self.msg_error.emit("[OSError] Unable to export to file <b>{0}</b>".format(filename))

    @busy_effect
    def export_to_sqlite(self, file_path):
        """Export data from database into SQlite file."""
        dst_url = 'sqlite:///{0}'.format(file_path)
        copy_database(dst_url, self.db_map.db_url, overwrite=True)
        self.msg.emit("SQlite file successfully exported.")

    def init_models(self):
        """Initialize models."""
        super().init_models()
        self.init_relationship_tree_model()

    def init_object_tree_model(self):
        """Initialize object tree model."""
        self.object_tree_model.build_tree()
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.hasChildren())

    def init_relationship_tree_model(self):
        """Initialize relationship tree model."""
        self.relationship_tree_model.build_tree()

    def init_views(self):
        """Initialize model views."""
        super().init_views()
        self.init_relationship_tree_view()

    def init_relationship_tree_view(self):
        """Init object tree view."""
        self.ui.treeView_relationship.setModel(self.relationship_tree_model)
        for i in range(self.object_tree_model.rowCount()):
            self.ui.treeView_relationship.expand(self.relationship_tree_model.index(i, 0))
        self.ui.treeView_relationship.resizeColumnToContents(0)

    @Slot("QModelIndex", name="find_next_leaf")
    def find_next_leaf(self, index):
        """If object tree index corresponds to a relationship, then expand the next ocurrence of it."""
        if not index.isValid():
            return  # just to be safe
        clicked_type = index.data(Qt.UserRole)
        if not clicked_type:  # root item
            return
        if not clicked_type == 'relationship':
            return
        clicked_item = index.model().itemFromIndex(index)
        if clicked_item.hasChildren():
            return
        self.find_next(index)

    def find_next(self, index):
        """Expand next occurrence of a relationship in object tree."""
        next_index = self.object_tree_model.next_relationship_index(index)
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
        self.set_default_parameter_rows(self.ui.treeView_object.selectionModel().selection())
        for index in deselected.indexes():
            item_type = index.data(Qt.UserRole)
            self.selected_obj_tree_indexes[item_type].pop(index)
        for index in selected.indexes():
            item_type = index.data(Qt.UserRole)
            self.selected_obj_tree_indexes.setdefault(item_type, {})[index] = None
        self.object_tree_selection_available.emit(any(v for v in self.selected_obj_tree_indexes.values()))
        self.object_class_selection_available.emit(len(self.selected_obj_tree_indexes.get('object_class', {})) > 0)
        self.object_selection_available.emit(len(self.selected_obj_tree_indexes.get('object', {})) > 0)
        if self.do_clear_other_selections:
            self.relationship_class_selection_available.emit(
                len(self.selected_obj_tree_indexes.get('relationship_class', {})) > 0
            )
            self.relationship_selection_available.emit(len(self.selected_obj_tree_indexes.get('relationship', {})) > 0)
            self.clear_other_selections(self.ui.treeView_object)
            self.update_filter()

    @busy_effect
    @Slot("QItemSelection", "QItemSelection", name="_handle_relationship_tree_selection_changed")
    def _handle_relationship_tree_selection_changed(self, selected, deselected):
        """Called when the relationship tree selection changes.
        Set default rows and apply filters on parameter models."""
        self.set_default_parameter_rows(self.ui.treeView_relationship.selectionModel().selection())
        for index in deselected.indexes():
            item_type = index.data(Qt.UserRole)
            self.selected_rel_tree_indexes[item_type].pop(index)
        for index in selected.indexes():
            item_type = index.data(Qt.UserRole)
            self.selected_rel_tree_indexes.setdefault(item_type, {})[index] = None
        self.relationship_tree_selection_available.emit(any(v for v in self.selected_rel_tree_indexes.values()))
        if self.do_clear_other_selections:
            self.relationship_class_selection_available.emit(
                len(self.selected_rel_tree_indexes.get('relationship_class', {})) > 0
            )
            self.relationship_selection_available.emit(len(self.selected_rel_tree_indexes.get('relationship', {})) > 0)
            self.clear_other_selections(self.ui.treeView_relationship)
            self.update_filter()

    def set_default_parameter_rows(self, selection):
        """Set default rows for parameter models according to selection in object tree."""
        return  # For now
        if selection.isEmpty():
            return
        index = selection.indexes()[-1]
        item_type = index.data(Qt.UserRole)
        if item_type == 'object_class':
            default_row = dict(
                object_class_id=index.data(Qt.UserRole + 1)['id'], object_class_name=index.data(Qt.UserRole + 1)['name']
            )
            model = self.object_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.object_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'object':
            default_row = dict(
                object_class_id=index.parent().data(Qt.UserRole + 1)['id'],
                object_class_name=index.parent().data(Qt.UserRole + 1)['name'],
            )
            model = self.object_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            default_row.update(
                dict(object_id=index.data(Qt.UserRole + 1)['id'], object_name=index.data(Qt.UserRole + 1)['name'])
            )
            model = self.object_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'relationship_class':
            default_row = dict(
                relationship_class_id=index.data(Qt.UserRole + 1)['id'],
                relationship_class_name=index.data(Qt.UserRole + 1)['name'],
                object_class_id_list=index.data(Qt.UserRole + 1)['object_class_id_list'],
                object_class_name_list=index.data(Qt.UserRole + 1)['object_class_name_list'],
            )
            model = self.relationship_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.relationship_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'relationship':
            default_row = dict(
                relationship_class_id=index.parent().data(Qt.UserRole + 1)['id'],
                relationship_class_name=index.parent().data(Qt.UserRole + 1)['name'],
                object_class_id_list=index.parent().data(Qt.UserRole + 1)['object_class_id_list'],
                object_class_name_list=index.parent().data(Qt.UserRole + 1)['object_class_name_list'],
            )
            model = self.relationship_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            default_row.update(
                dict(
                    relationship_id=index.data(Qt.UserRole + 1)['id'],
                    object_id_list=index.data(Qt.UserRole + 1)['object_id_list'],
                    object_name_list=index.data(Qt.UserRole + 1)['object_name_list'],
                )
            )
            model = self.relationship_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'root':
            default_row = dict()
            model = self.object_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.object_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.relationship_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.relationship_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)

    def update_filter(self):
        """Update filters on parameter models according to selected and deselected object tree indexes."""
        # Prepare stuff
        # Collect object tree indexes
        rel_inds = {
            (db_map, ind): None
            for ind in self.selected_obj_tree_indexes.get('relationship', {})
            for db_map in ind.data(Qt.UserRole + 1)
        }
        rel_cls_inds = {
            (db_map, ind): None
            for ind in self.selected_obj_tree_indexes.get('relationship_class', {})
            for db_map in ind.data(Qt.UserRole + 1)
        }
        rel_cls_inds.update({(db_map, ind.parent()): None for db_map, ind in rel_inds})
        obj_inds = {
            (db_map, ind): None
            for ind in self.selected_obj_tree_indexes.get('object', {})
            for db_map in ind.data(Qt.UserRole + 1)
        }
        obj_inds.update({(db_map, ind.parent()): None for db_map, ind in rel_cls_inds})
        obj_cls_inds = {
            (db_map, ind): None
            for ind in self.selected_obj_tree_indexes.get('object_class', {})
            for db_map in ind.data(Qt.UserRole + 1)
        }
        obj_cls_inds.update({(db_map, ind.parent()): None for db_map, ind in obj_inds})
        # Add relationship tree indexes
        more_rel_inds = {
            (db_map, ind): None
            for ind in self.selected_rel_tree_indexes.get('relationship', {})
            for db_map in ind.data(Qt.UserRole + 1)
        }
        more_rel_cls_inds = {
            (db_map, ind): None
            for ind in self.selected_rel_tree_indexes.get('relationship_class', {})
            for db_map in ind.data(Qt.UserRole + 1)
        }
        rel_inds.update(more_rel_inds)
        rel_cls_inds.update({(db_map, ind.parent()): None for db_map, ind in more_rel_inds})
        rel_cls_inds.update(more_rel_cls_inds)
        # Update selected
        self.selected_object_class_ids = set(
            (db_map, ind.data(Qt.UserRole + 1)[db_map]['id']) for db_map, ind in obj_cls_inds
        )
        self.selected_object_ids = dict()
        for db_map, ind in obj_inds:
            d = ind.data(Qt.UserRole + 1)[db_map]
            self.selected_object_ids.setdefault((db_map, d['class_id']), set()).add(
                (self.db_map_to_name[db_map], d['id'])
            )
        self.selected_relationship_class_ids = set(
            (db_map, ind.data(Qt.UserRole + 1)[db_map]['id']) for db_map, ind in rel_cls_inds
        )
        self.selected_object_id_lists = dict()
        for db_map, ind in rel_inds:
            d = ind.data(Qt.UserRole + 1)[db_map]
            self.selected_object_id_lists.setdefault((db_map, d['class_id']), set()).add(
                (self.db_map_to_name[db_map], d['object_id_list'])
            )
        self.do_update_filter()

    @Slot("QPoint", name="show_object_tree_context_menu")
    def show_object_tree_context_menu(self, pos):
        """Context menu for object tree.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_object.indexAt(pos)
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        self.object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, index)
        option = self.object_tree_context_menu.get_action()
        if option == "Copy text":
            self.ui.treeView_object.copy()
        elif option == "Add object classes":
            self.show_add_object_classes_form()
        elif option == "Add objects":
            self.call_show_add_objects_form(index)
        elif option == "Add relationship classes":
            self.call_show_add_relationship_classes_form(index)
        elif option == "Add relationships":
            self.call_show_add_relationships_form(index)
        elif option == "Edit object classes":
            self.show_edit_object_classes_form()
        elif option == "Edit objects":
            self.show_edit_objects_form()
        elif option == "Edit relationship classes":
            self.show_edit_relationship_classes_form()
        elif option == "Edit relationships":
            self.show_edit_relationships_form()
        elif option == "Find next":
            self.find_next(index)
        elif option.startswith("Remove selection"):
            self.show_remove_object_tree_items_form()
        elif option == "Fully expand":
            self.fully_expand_selection()
        elif option == "Fully collapse":
            self.fully_collapse_selection()
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    @Slot("QPoint", name="show_relationship_tree_context_menu")
    def show_relationship_tree_context_menu(self, pos):
        """Context menu for relationship tree.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_relationship.indexAt(pos)
        global_pos = self.ui.treeView_relationship.viewport().mapToGlobal(pos)
        self.relationship_tree_context_menu = RelationshipTreeContextMenu(self, global_pos, index)
        option = self.relationship_tree_context_menu.get_action()
        if option == "Copy text":
            self.ui.treeView_relationship.copy()
        elif option == "Add relationship classes":
            self.show_add_relationship_classes_form()
        elif option == "Add relationships":
            self.call_show_add_relationships_form(index)
        elif option == "Edit relationship classes":
            self.show_edit_relationship_classes_form()
        elif option == "Edit relationships":
            self.show_edit_relationships_form()
        elif option.startswith("Remove selection"):
            self.show_remove_relationship_tree_items_form()
        else:  # No option selected
            pass
        self.relationship_tree_context_menu.deleteLater()
        self.relationship_tree_context_menu = None

    def fully_expand_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            self.object_tree_model.forward_sweep(index, call=self.ui.treeView_object.expand)

    def fully_collapse_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            self.object_tree_model.forward_sweep(index, call=self.ui.treeView_object.collapse)

    def call_show_add_objects_form(self, index):
        class_name = index.data(Qt.DisplayRole)
        self.show_add_objects_form(class_name=class_name)

    def call_show_add_relationship_classes_form(self, index):
        object_class_one_name = index.data(Qt.DisplayRole)
        self.show_add_relationship_classes_form(object_class_one_name=object_class_one_name)

    def call_show_add_relationships_form(self, index):
        relationship_class_key = (index.data(Qt.DisplayRole), index.data(Qt.ToolTipRole))
        if index.model() == self.object_tree_model:
            object_name = index.parent().data(Qt.DisplayRole)
            object_class_name = index.parent().parent().data(Qt.DisplayRole)
            self.show_add_relationships_form(
                relationship_class_key=relationship_class_key,
                object_class_name=object_class_name,
                object_name=object_name,
            )
        else:
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

    def show_remove_object_tree_items_form(self):
        """Show form to remove items from object treeview."""
        kwargs = {
            item_type: [ind.data(Qt.UserRole + 1) for ind in self.selected_obj_tree_indexes.get(item_type, {})]
            for item_type in ('object_class', 'object', 'relationship_class', 'relationship')
        }
        dialog = RemoveTreeItemsDialog(self, **kwargs)
        dialog.show()

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
            object_class_ids = item_type_ids.get("object_class", ())
            object_ids = item_type_ids.get("object", ())
            relationship_class_ids = item_type_ids.get("relationship_class", ())
            relationship_ids = item_type_ids.get("relationship", ())
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
                # self.object_parameter_definition_model.remove_object_classes(db_map, object_classes)
                # self.object_parameter_value_model.remove_object_classes(db_map, object_classes)
                # self.relationship_parameter_definition_model.remove_object_classes(db_map, object_classes)
                # self.relationship_parameter_value_model.remove_object_classes(db_map,object_classes)
            if object_ids:
                self.object_tree_model.remove_objects(db_map, object_ids)
                self.relationship_tree_model.remove_objects(db_map, object_ids)
                # self.object_parameter_value_model.remove_objects(db_map, objects)
                # self.relationship_parameter_value_model.remove_objects(db_map, objects)
            if relationship_class_ids:
                self.object_tree_model.remove_relationship_classes(db_map, relationship_class_ids)
                self.relationship_tree_model.remove_relationship_classes(db_map, relationship_class_ids)
                # self.relationship_parameter_definition_model.remove_relationship_classes(db_map, relationship_classes)
                # self.relationship_parameter_value_model.remove_relationship_classes(db_map, relationship_classes)
            if relationship_ids:
                self.object_tree_model.remove_relationships(db_map, relationship_ids)
                self.relationship_tree_model.remove_relationships(db_map, relationship_ids)
                # self.relationship_parameter_value_model.remove_relationships(db_map, relationships)
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
        index = self.ui.tableView_object_parameter_value.indexAt(pos)
        global_pos = self.ui.tableView_object_parameter_value.viewport().mapToGlobal(pos)
        self.object_parameter_value_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.object_parameter_value_context_menu.get_action()
        if option == "Remove selection":
            self.remove_object_parameter_values()
        elif option == "Copy":
            self.ui.tableView_object_parameter_value.copy()
        elif option == "Paste":
            self.ui.tableView_object_parameter_value.paste()
        self.object_parameter_value_context_menu.deleteLater()
        self.object_parameter_value_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_value_context_menu")
    def show_relationship_parameter_value_context_menu(self, pos):
        """Context menu for relationship parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_relationship_parameter_value.indexAt(pos)
        global_pos = self.ui.tableView_relationship_parameter_value.viewport().mapToGlobal(pos)
        self.relationship_parameter_value_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.relationship_parameter_value_context_menu.get_action()
        if option == "Remove selection":
            self.remove_relationship_parameter_values()
        elif option == "Copy":
            self.ui.tableView_relationship_parameter_value.copy()
        elif option == "Paste":
            self.ui.tableView_relationship_parameter_value.paste()
        self.relationship_parameter_value_context_menu.deleteLater()
        self.relationship_parameter_value_context_menu = None

    @Slot("QPoint", name="show_object_parameter_context_menu")
    def show_object_parameter_context_menu(self, pos):
        """Context menu for object parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_object_parameter_definition.indexAt(pos)
        global_pos = self.ui.tableView_object_parameter_definition.viewport().mapToGlobal(pos)
        self.object_parameter_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.object_parameter_context_menu.get_action()
        if option == "Remove selection":
            self.remove_object_parameter_definitions()
        elif option == "Copy":
            self.ui.tableView_object_parameter_definition.copy()
        elif option == "Paste":
            self.ui.tableView_object_parameter_definition.paste()
        self.object_parameter_context_menu.deleteLater()
        self.object_parameter_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_context_menu")
    def show_relationship_parameter_context_menu(self, pos):
        """Context menu for relationship parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_relationship_parameter_definition.indexAt(pos)
        global_pos = self.ui.tableView_relationship_parameter_definition.viewport().mapToGlobal(pos)
        self.relationship_parameter_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.relationship_parameter_context_menu.get_action()
        if option == "Remove selection":
            self.remove_relationship_parameter_definitions()
        elif option == "Copy":
            self.ui.tableView_relationship_parameter_definition.copy()
        elif option == "Paste":
            self.ui.tableView_relationship_parameter_definition.paste()
        self.relationship_parameter_context_menu.deleteLater()
        self.relationship_parameter_context_menu = None

    @Slot("QPoint", name="show_parameter_value_list_context_menu")
    def show_parameter_value_list_context_menu(self, pos):
        """Context menu for relationship parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_parameter_value_list.indexAt(pos)
        global_pos = self.ui.treeView_parameter_value_list.viewport().mapToGlobal(pos)
        self.parameter_value_list_context_menu = ParameterValueListContextMenu(self, global_pos, index)
        self.parameter_value_list_context_menu.deleteLater()
        option = self.parameter_value_list_context_menu.get_action()
        if option == "Copy":
            self.ui.treeView_parameter_value_list.copy()
        elif option == "Remove selection":
            self.remove_parameter_value_lists()

    @busy_effect
    def remove_object_parameter_values(self):
        """Remove selection rows from object parameter value table."""
        selection = self.ui.tableView_object_parameter_value.selectionModel().selection()
        row_dict = dict()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_dict[top] = bottom - top + 1
        model = self.object_parameter_value_model
        id_column = model.horizontal_header_labels().index("id")
        parameter_value_ids = set()
        for row, count in row_dict.items():
            parameter_value_ids.update(model.index(i, id_column).data() for i in range(row, row + count))
        try:
            self.db_map.remove_items(parameter_value_ids=parameter_value_ids)
            for row in reversed(sorted(row_dict)):
                count = row_dict[row]
                self.object_parameter_value_model.removeRows(row, count)
            self.commit_available.emit(True)
            self.msg.emit("Successfully removed parameter values.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    def remove_relationship_parameter_values(self):
        """Remove selection rows from relationship parameter value table."""
        selection = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        row_dict = dict()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_dict[top] = bottom - top + 1
        model = self.relationship_parameter_value_model
        id_column = model.horizontal_header_labels().index("id")
        parameter_value_ids = set()
        for row, count in row_dict.items():
            parameter_value_ids.update(model.index(i, id_column).data() for i in range(row, row + count))
        try:
            self.db_map.remove_items(parameter_value_ids=parameter_value_ids)
            for row in reversed(sorted(row_dict)):
                count = row_dict[row]
                self.relationship_parameter_value_model.removeRows(row, count)
            self.commit_available.emit(True)
            self.msg.emit("Successfully removed parameter values.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    def remove_object_parameter_definitions(self):
        """Remove selection rows from object parameter definition table."""
        selection = self.ui.tableView_object_parameter_definition.selectionModel().selection()
        row_dict = dict()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_dict[top] = bottom - top + 1
        model = self.object_parameter_definition_model
        parameter_definition_ids = set()
        parameter_dict = dict()
        header = model.horizontal_header_labels()
        object_class_id_column = header.index("object_class_id")
        id_column = header.index("id")
        for row, count in row_dict.items():
            for i in range(row, row + count):
                object_class_id = model.index(i, object_class_id_column).data(Qt.DisplayRole)
                id_ = model.index(i, id_column).data(Qt.DisplayRole)
                parameter_definition_ids.add(id_)
                parameter_dict.setdefault(object_class_id, set()).add(id_)
        try:
            self.db_map.remove_items(parameter_definition_ids=parameter_definition_ids)
            for row in reversed(sorted(row_dict)):
                count = row_dict[row]
                self.object_parameter_definition_model.removeRows(row, count)
            self.object_parameter_value_model.remove_parameters(parameter_dict)
            self.commit_available.emit(True)
            self.msg.emit("Successfully removed parameter definitions.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    def remove_relationship_parameter_definitions(self):
        """Remove selection rows from relationship parameter definition table."""
        selection = self.ui.tableView_relationship_parameter_definition.selectionModel().selection()
        row_dict = dict()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_dict[top] = bottom - top + 1
        model = self.relationship_parameter_definition_model
        parameter_definition_ids = set()
        parameter_dict = dict()
        header = model.horizontal_header_labels()
        relationship_class_id_column = header.index("relationship_class_id")
        id_column = header.index("id")
        for row, count in row_dict.items():
            for i in range(row, row + count):
                relationship_class_id = model.index(i, relationship_class_id_column).data(Qt.DisplayRole)
                id_ = model.index(i, id_column).data(Qt.DisplayRole)
                parameter_definition_ids.add(id_)
                parameter_dict.setdefault(relationship_class_id, set()).add(id_)
        try:
            self.db_map.remove_items(parameter_definition_ids=parameter_definition_ids)
            for row in reversed(sorted(row_dict)):
                count = row_dict[row]
                self.relationship_parameter_definition_model.removeRows(row, count)
            self.relationship_parameter_value_model.remove_parameters(parameter_dict)
            self.commit_available.emit(True)
            self.msg.emit("Successfully removed parameter definitions.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    def remove_parameter_value_lists(self):
        """Remove selection parameter value_lists.
        """
        indexes = self.ui.treeView_parameter_value_list.selectionModel().selectedIndexes()
        parented_indexes = {}
        toplevel_indexes = []
        for index in indexes:
            parent = index.parent()
            if parent.isValid():
                parented_indexes.setdefault(parent, list()).append(index)
            else:
                toplevel_indexes.append(index)
        # Remove top level indexes from parented indexes, since they will be fully removed anyways
        for index in toplevel_indexes:
            parented_indexes.pop(index, None)
        # Get items to update
        model = self.parameter_value_list_model
        to_update = list()
        for parent, indexes in parented_indexes.items():
            id = parent.internalPointer().id
            removed_rows = [ind.row() for ind in indexes]
            all_rows = range(model.rowCount(parent) - 1)
            value_list = [model.index(row, 0, parent).data(Qt.EditRole) for row in all_rows if row not in removed_rows]
            to_update.append(dict(id=id, value_list=value_list))
        # Get ids to remove
        removed_ids = [ind.internalPointer().id for ind in toplevel_indexes]
        try:
            # NOTE: this below should never fail with SpineIntegrityError,
            # since we're removing from items that were already there
            self.db_map.update_wide_parameter_value_lists(*to_update)
            self.db_map.remove_items(parameter_value_list_ids=removed_ids)
            self.commit_available.emit(True)
            for row in sorted([ind.row() for ind in toplevel_indexes], reverse=True):
                self.parameter_value_list_model.removeRow(row)
            for parent, indexes in parented_indexes.items():
                for row in sorted([ind.row() for ind in indexes], reverse=True):
                    self.parameter_value_list_model.removeRow(row, parent)
            self.object_parameter_definition_model.clear_parameter_value_lists(removed_ids)
            self.relationship_parameter_definition_model.clear_parameter_value_lists(removed_ids)
            self.msg.emit("Successfully removed parameter value list(s).")
        except SpineDBAPIError as e:
            self._tree_view_form.msg_error.emit(e.msg)
