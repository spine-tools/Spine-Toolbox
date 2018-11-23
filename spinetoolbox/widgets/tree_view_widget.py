######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Widget to show Data Store tree view form.

:author: M. Marin (KTH)
:date:   21.4.2018
"""

import os
import time  # just to measure loading time and sqlalchemy ORM performance
import logging
import json
from PySide2.QtWidgets import QMainWindow, QHeaderView, QDialog, QLineEdit, QInputDialog, \
    QMessageBox, QCheckBox, QFileDialog, QApplication, QErrorMessage, QPushButton
from PySide2.QtCore import Signal, Slot, Qt, QSettings
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon, QPixmap
from ui.tree_view_form import Ui_MainWindow
from config import STATUSBAR_SS
from spinedatabase_api import SpineDBAPIError, SpineIntegrityError
from widgets.custom_menus import ObjectTreeContextMenu, ParameterContextMenu
from widgets.custom_delegates import ObjectParameterValueDelegate, ObjectParameterDelegate, \
    RelationshipParameterValueDelegate, RelationshipParameterDelegate
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, \
    AddRelationshipClassesDialog, AddRelationshipsDialog, \
    EditObjectClassesDialog, EditObjectsDialog, \
    EditRelationshipClassesDialog, EditRelationshipsDialog, \
    CommitDialog
from models import ObjectTreeModel, ObjectParameterValueModel, ObjectParameterDefinitionModel, \
    RelationshipParameterDefinitionModel, RelationshipParameterValueModel, \
    ObjectParameterDefinitionProxy, ObjectParameterValueProxy, \
    RelationshipParameterDefinitionProxy, RelationshipParameterValueProxy
from excel_import_export import import_xlsx_to_db, export_spine_database_to_xlsx
from spinedatabase_api import copy_database
from datapackage_import_export import import_datapackage
from helpers import busy_effect, relationship_pixmap, object_pixmap


class TreeViewForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        data_store (DataStore): The DataStore instance that owns this form
        db_map (DiffDatabaseMapping): The object relational database mapping
        database (str): The database name
    """
    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, data_store, db_map, database):
        """Initialize class."""
        tic = time.clock()
        super().__init__(flags=Qt.Window)
        # TODO: Maybe set the parent as ToolboxUI so that its stylesheet is inherited. This may need
        # reimplementing the window minimizing and maximizing actions as well as setting the window modality
        self._data_store = data_store
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Set up status bar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Set up corner widgets
        icon = QIcon(":/icons/relationship_parameter_icon.png")
        button = QPushButton(icon, "Relationship parameter")
        button.setFlat(True)
        button.setLayoutDirection(Qt.LeftToRight)
        button.mousePressEvent = lambda e: e.ignore()
        self.ui.tabWidget_relationship.setCornerWidget(button, Qt.TopRightCorner)
        icon = QIcon(":/icons/object_parameter_icon.png")
        button = QPushButton(icon, "Object parameter")
        button.setLayoutDirection(Qt.LeftToRight)
        button.setFlat(True)
        button.mousePressEvent = lambda e: e.ignore()
        self.ui.tabWidget_object.setCornerWidget(button, Qt.TopRightCorner)
        # Class attributes
        self.err_msg = QErrorMessage(self)
        # DB db_map
        self.db_map = db_map
        self.database = database
        self.object_icon_dict = {}
        self.relationship_icon_dict = {}
        self.init_icon_dicts()
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self)
        # Parameter value models
        self.object_parameter_value_model = ObjectParameterValueModel(self)
        self.object_parameter_value_proxy = ObjectParameterValueProxy(self)
        self.relationship_parameter_value_model = RelationshipParameterValueModel(self)
        self.relationship_parameter_value_proxy = RelationshipParameterValueProxy(self)
        # Parameter (definition) models
        self.object_parameter_definition_model = ObjectParameterDefinitionModel(self)
        self.object_parameter_definition_proxy = ObjectParameterDefinitionProxy(self)
        self.relationship_parameter_definition_model = RelationshipParameterDefinitionModel(self)
        self.relationship_parameter_definition_proxy = RelationshipParameterDefinitionProxy(self)
        # Context menus
        self.object_tree_context_menu = None
        self.object_parameter_value_context_menu = None
        self.relationship_parameter_value_context_menu = None
        self.object_parameter_context_menu = None
        self.relationship_parameter_context_menu = None
        # Others
        self.clipboard = QApplication.clipboard()
        self.clipboard_text = self.clipboard.text()
        self.focus_widget = None  # Last widget which had focus before showing a menu from the menubar
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        self.fully_expand_icon = QIcon(QPixmap(":/icons/fully_expand.png"))
        self.fully_collapse_icon = QIcon(QPixmap(":/icons/fully_collapse.png"))
        self.find_next_icon = QIcon(QPixmap(":/icons/find_next.png"))
        # init models and views
        self.init_models()
        self.init_views()
        self.setup_delegates()
        self.setup_buttons()
        self.connect_signals()
        self.restore_ui()
        self.setWindowTitle("Data store tree view    -- {} --".format(self.database))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        toc = time.clock()
        self.msg.emit("Tree view form created in {} seconds".format(toc - tic))

    def setup_buttons(self):
        """Specify actions and menus for add/remove parameter buttons."""
        # Setup button actions
        self.ui.toolButton_add_object_parameter_values.\
            setDefaultAction(self.ui.actionAdd_object_parameter_values)
        self.ui.toolButton_remove_object_parameter_values.\
            setDefaultAction(self.ui.actionRemove_object_parameter_values)
        self.ui.toolButton_add_relationship_parameter_values.\
            setDefaultAction(self.ui.actionAdd_relationship_parameter_values)
        self.ui.toolButton_remove_relationship_parameter_values.\
            setDefaultAction(self.ui.actionRemove_relationship_parameter_values)
        self.ui.toolButton_add_object_parameter_definitions.\
            setDefaultAction(self.ui.actionAdd_object_parameter_definitions)
        self.ui.toolButton_remove_object_parameter_definitions.\
            setDefaultAction(self.ui.actionRemove_object_parameter_definitions)
        self.ui.toolButton_add_relationship_parameter_definitions.\
            setDefaultAction(self.ui.actionAdd_relationship_parameter_definitions)
        self.ui.toolButton_remove_relationship_parameter_definitions.\
            setDefaultAction(self.ui.actionRemove_relationship_parameter_definitions)

    def setup_delegates(self):
        """Set delegates for tables."""
        # Object parameter
        table_view = self.ui.tableView_object_parameter_definition
        delegate = ObjectParameterDelegate(table_view, self.db_map)
        table_view.setItemDelegate(delegate)
        # Object parameter value
        table_view = self.ui.tableView_object_parameter_value
        delegate = ObjectParameterValueDelegate(table_view, self.db_map)
        table_view.setItemDelegate(delegate)
        # Relationship parameter
        table_view = self.ui.tableView_relationship_parameter_definition
        delegate = RelationshipParameterDelegate(table_view, self.db_map)
        table_view.setItemDelegate(delegate)
        # Relationship parameter value
        table_view = self.ui.tableView_relationship_parameter_value
        delegate = RelationshipParameterValueDelegate(table_view, self.db_map)
        table_view.setItemDelegate(delegate)

    def connect_signals(self):
        """Connect signals to slots."""
        # Message signals
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        # Menu actions
        self.ui.actionImport.triggered.connect(self.show_import_file_dialog)
        self.ui.actionExport.triggered.connect(self.show_export_file_dialog)
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionAdd_object_classes.triggered.connect(self.show_add_object_classes_form)
        self.ui.actionAdd_objects.triggered.connect(self.show_add_objects_form)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.show_add_relationship_classes_form)
        self.ui.actionAdd_relationships.triggered.connect(self.show_add_relationships_form)
        self.ui.actionAdd_object_parameter_values.triggered.connect(self.add_object_parameter_values)
        self.ui.actionAdd_relationship_parameter_values.triggered.connect(self.add_relationship_parameter_values)
        self.ui.actionAdd_object_parameter_definitions.triggered.connect(self.add_object_parameter_definitions)
        self.ui.actionAdd_relationship_parameter_definitions.triggered.\
            connect(self.add_relationship_parameter_definitions)
        self.ui.actionEdit_object_classes.triggered.connect(self.show_edit_object_classes_form)
        self.ui.actionEdit_objects.triggered.connect(self.show_edit_objects_form)
        self.ui.actionEdit_relationship_classes.triggered.connect(self.show_edit_relationship_classes_form)
        self.ui.actionEdit_relationships.triggered.connect(self.show_edit_relationships_form)
        self.ui.actionRemove_object_tree_items.triggered.connect(self.remove_object_tree_items)
        self.ui.actionRemove_object_parameter_definitions.triggered.connect(self.remove_object_parameter_definitions)
        self.ui.actionRemove_object_parameter_values.triggered.connect(self.remove_object_parameter_values)
        self.ui.actionRemove_relationship_parameter_definitions.triggered.\
            connect(self.remove_relationship_parameter_definitions)
        self.ui.actionRemove_relationship_parameter_values.triggered.connect(self.remove_relationship_parameter_values)
        # Copy and paste
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        # Object tree
        self.ui.treeView_object.selectionModel().selectionChanged.connect(self.receive_object_tree_selection_changed)
        self.ui.treeView_object.edit_key_pressed.connect(self.edit_object_tree_items)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.find_next_leaf)
        # Autofilter parameter tables
        self.ui.tableView_object_parameter_definition.filter_changed.connect(self.apply_autofilter)
        self.ui.tableView_object_parameter_value.filter_changed.connect(self.apply_autofilter)
        self.ui.tableView_relationship_parameter_definition.filter_changed.connect(self.apply_autofilter)
        self.ui.tableView_relationship_parameter_value.filter_changed.connect(self.apply_autofilter)
        # Parameter tables delegate commit data
        self.ui.tableView_object_parameter_definition.itemDelegate().commit_model_data.\
            connect(self.set_parameter_definition_data)
        self.ui.tableView_object_parameter_value.itemDelegate().commit_model_data.\
            connect(self.set_parameter_value_data)
        self.ui.tableView_relationship_parameter_definition.itemDelegate().commit_model_data.\
            connect(self.set_parameter_definition_data)
        self.ui.tableView_relationship_parameter_value.itemDelegate().commit_model_data.\
            connect(self.set_parameter_value_data)
        # Parameter tables selection changes
        self.ui.tableView_object_parameter_definition.selectionModel().selectionChanged.\
            connect(self.receive_object_parameter_selection_changed)
        self.ui.tableView_object_parameter_value.selectionModel().selectionChanged.\
            connect(self.receive_object_parameter_value_selection_changed)
        self.ui.tableView_relationship_parameter_definition.selectionModel().selectionChanged.\
            connect(self.receive_relationship_parameter_selection_changed)
        self.ui.tableView_relationship_parameter_value.selectionModel().selectionChanged.\
            connect(self.receive_relationship_parameter_value_selection_changed)
        # Parameter tabwidgets current changed
        self.ui.tabWidget_object.currentChanged.connect(self.receive_object_parameter_tab_changed)
        self.ui.tabWidget_relationship.currentChanged.connect(self.receive_relationship_parameter_tab_changed)
        # Parameter tables context menu requested
        self.ui.tableView_object_parameter_definition.customContextMenuRequested.\
            connect(self.show_object_parameter_context_menu)
        self.ui.tableView_object_parameter_value.customContextMenuRequested.\
            connect(self.show_object_parameter_value_context_menu)
        self.ui.tableView_relationship_parameter_definition.customContextMenuRequested.\
            connect(self.show_relationship_parameter_context_menu)
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.\
            connect(self.show_relationship_parameter_value_context_menu)
        # Clipboard data changed
        self.clipboard.dataChanged.connect(self.clipboard_data_changed)
        # Menu about to show
        self.ui.menuFile.aboutToShow.connect(self.receive_menu_about_to_show)
        self.ui.menuEdit.aboutToShow.connect(self.receive_menu_about_to_show)
        self.ui.menuSession.aboutToShow.connect(self.receive_menu_about_to_show)
        # DS destroyed
        self._data_store.destroyed.connect(self.close)
        # Others
        self.relationship_parameter_value_proxy.layoutChanged.connect(self.hide_unused_object_name_columns)

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Append regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        current_msg = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(" ".join([current_msg, msg]), 5000)

    @Slot(str, name="add_error_message")
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show in QErrorMessage
        """
        self.err_msg.showMessage(msg)

    @Slot(name="clipboard_data_changed")
    def clipboard_data_changed(self):
        """Store data from clipboard."""
        self.clipboard_text = self.clipboard.text()

    @Slot(name="copy")
    def copy(self):
        """Copy data to clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.copy()
        except AttributeError:
            pass

    @Slot(name="paste")
    def paste(self):
        """Paste data from clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.paste(self.clipboard_text)
        except AttributeError:
            pass

    @Slot("QItemSelection", "QItemSelection", name="receive_object_parameter_selection_changed")
    def receive_object_parameter_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        selection = self.ui.tableView_object_parameter_definition.selectionModel().selection()
        index = self.ui.tabWidget_object.currentIndex()
        self.ui.actionRemove_object_parameter_definitions.setEnabled(index == 1 and not selection.isEmpty())

    @Slot("QItemSelection", "QItemSelection", name="receive_object_parameter_value_selection_changed")
    def receive_object_parameter_value_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        selection = self.ui.tableView_object_parameter_value.selectionModel().selection()
        index = self.ui.tabWidget_object.currentIndex()
        self.ui.actionRemove_object_parameter_values.setEnabled(index == 0 and not selection.isEmpty())

    @Slot("QItemSelection", "QItemSelection", name="receive_relationship_parameter_selection_changed")
    def receive_relationship_parameter_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        selection = self.ui.tableView_relationship_parameter_definition.selectionModel().selection()
        index = self.ui.tabWidget_relationship.currentIndex()
        self.ui.actionRemove_relationship_parameter_definitions.setEnabled(index == 1 and not selection.isEmpty())

    @Slot("QItemSelection", "QItemSelection", name="receive_relationship_parameter_value_selection_changed")
    def receive_relationship_parameter_value_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        selection = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        index = self.ui.tabWidget_relationship.currentIndex()
        self.ui.actionRemove_relationship_parameter_values.setEnabled(index == 0 and not selection.isEmpty())

    @Slot("int", name="receive_object_parameter_tab_changed")
    def receive_object_parameter_tab_changed(self, index):
        """Enable/disable the option to remove rows."""
        if index == 0:
            self.object_parameter_value_proxy.apply_filter()
        else:
            self.object_parameter_definition_proxy.apply_filter()
        selected = self.ui.tableView_object_parameter_definition.selectionModel().selection()
        self.ui.actionRemove_object_parameter_definitions.setEnabled(index == 1 and not selected.isEmpty())
        selected = self.ui.tableView_object_parameter_value.selectionModel().selection()
        self.ui.actionRemove_object_parameter_values.setEnabled(index == 0 and not selected.isEmpty())

    @Slot("int", name="receive_relationship_parameter_tab_changed")
    def receive_relationship_parameter_tab_changed(self, index):
        """Enable/disable the option to remove rows."""
        if index == 0:
            self.relationship_parameter_value_proxy.apply_filter()
        else:
            self.relationship_parameter_definition_proxy.apply_filter()
        selected = self.ui.tableView_relationship_parameter_definition.selectionModel().selection()
        self.ui.actionRemove_relationship_parameter_definitions.setEnabled(index == 1 and not selected.isEmpty())
        selected = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        self.ui.actionRemove_relationship_parameter_values.setEnabled(index == 0 and not selected.isEmpty())

    @Slot(name="receive_menu_about_to_show")
    def receive_menu_about_to_show(self):
        """Called when a menu from the menubar is about to show.
        Adjust copy paste actions depending on which widget has the focus.
        Enable/disable actions to edit object tree items depending on selection.
        Enable/disable actions to remove object tree items depending on selection.
        """
        # Copy/paste actions
        if self.focusWidget() != self.ui.menubar:
            self.focus_widget = self.focusWidget()
        self.ui.actionCopy.setText("Copy")
        self.ui.actionPaste.setText("Paste")
        self.ui.actionCopy.setEnabled(False)
        self.ui.actionPaste.setEnabled(False)
        if self.focus_widget == self.ui.treeView_object:
            if not self.ui.treeView_object.selectionModel().selection().isEmpty():
                self.ui.actionCopy.setText("Copy from object tree")
                self.ui.actionCopy.setEnabled(True)
        elif self.focus_widget == self.ui.tableView_object_parameter_definition:
            if not self.ui.tableView_object_parameter_definition.selectionModel().selection().isEmpty():
                self.ui.actionCopy.setText("Copy from object parameter definition")
                self.ui.actionCopy.setEnabled(True)
            if self.clipboard_text:
                self.ui.actionPaste.setText("Paste to object parameter definition")
                self.ui.actionPaste.setEnabled(True)
        elif self.focus_widget == self.ui.tableView_object_parameter_value:
            if not self.ui.tableView_object_parameter_value.selectionModel().selection().isEmpty():
                self.ui.actionCopy.setText("Copy from object parameter value")
                self.ui.actionCopy.setEnabled(True)
            if self.clipboard_text:
                self.ui.actionPaste.setText("Paste to object parameter value")
                self.ui.actionPaste.setEnabled(True)
        elif self.focus_widget == self.ui.tableView_relationship_parameter_definition:
            if not self.ui.tableView_relationship_parameter_definition.selectionModel().selection().isEmpty():
                self.ui.actionCopy.setText("Copy from relationship parameter definition")
                self.ui.actionCopy.setEnabled(True)
            if self.clipboard_text:
                self.ui.actionPaste.setText("Paste to relationship parameter definition")
                self.ui.actionPaste.setEnabled(True)
        elif self.focus_widget == self.ui.tableView_relationship_parameter_value:
            if not self.ui.tableView_relationship_parameter_value.selectionModel().selection().isEmpty():
                self.ui.actionCopy.setText("Copy from relationship parameter value")
                self.ui.actionCopy.setEnabled(True)
            if self.clipboard_text:
                self.ui.actionPaste.setText("Paste to relationship parameter value")
                self.ui.actionPaste.setEnabled(True)
        # Edit object tree item actions
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        item_types = {x.data(Qt.UserRole) for x in indexes}
        self.ui.actionEdit_object_classes.setEnabled('object_class' in item_types)
        self.ui.actionEdit_objects.setEnabled('object' in item_types)
        self.ui.actionEdit_relationship_classes.setEnabled('relationship_class' in item_types)
        self.ui.actionEdit_relationships.setEnabled('relationship' in item_types)
        # Remove object tree items action
        self.ui.actionRemove_object_tree_items.setEnabled(len(indexes) > 0)

    @Slot(name="show_import_file_dialog")
    def show_import_file_dialog(self):
        """Show dialog to allow user to select a file to import."""
        answer = QFileDialog.getOpenFileName(
            self, "Select file to import", self._data_store.project().project_dir, "*.*")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self.import_file(file_path)

    @busy_effect
    def import_file(self, file_path):
        """Import data from file into current database."""
        if file_path.lower().endswith('datapackage.json'):
            try:
                import_datapackage(self, file_path)
                self.init_parameter_value_models()
                self.init_parameter_definition_models()
                self.msg.emit("Datapackage successfully imported.")
            except SpineDBAPIError as e:
                self.msg_error.emit("Unable to import datapackage: {}.".format(e.msg))
        elif file_path.lower().endswith('xlsx'):
            error_log = []
            try:
                insert_log, error_log = import_xlsx_to_db(self.db_map, file_path)
                self.msg.emit("Excel file successfully imported.")
                self.set_commit_rollback_actions_enabled(True)
                # logging.debug(insert_log)
                self.init_models()
            except SpineIntegrityError as e:
                self.msg_error.emit(e.msg)
            except SpineDBAPIError as e:
                self.msg_error.emit("Unable to import Excel file: {}".format(e.msg))
            finally:
                if not len(error_log) == 0:
                    msg = "Something went wrong in importing an Excel file " \
                          "into the current session. Here is the error log:\n\n{0}".format(error_log)
                    # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
                    QMessageBox.information(self, "Excel import may have failed", msg)
                    # logging.debug(error_log)

    @Slot(name="show_export_file_dialog")
    def show_export_file_dialog(self):
        """Show dialog to allow user to select a file to export."""
        answer = QFileDialog.getSaveFileName(self,
                                             "Export to file",
                                             self._data_store.project().project_dir,
                                             "Excel file (*.xlsx);;SQlite database (*.sqlite *.db)")
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
            self.msg_error.emit("Unable to export to file <b>{0}</b>.<br/>"
                                "Close the file in Excel and try again.".format(filename))
        except OSError:
            self.msg_error.emit("[OSError] Unable to export to file <b>{0}</b>".format(filename))

    @busy_effect
    def export_to_sqlite(self, file_path):
        """Export data from database into SQlite file."""
        # Remove file if exists (at this point, the user has confirmed that overwritting is ok)
        try:
            os.remove(file_path)
        except OSError:
            pass
        dst_url = 'sqlite:///{0}'.format(file_path)
        copy_database(dst_url, self.db_map.db_url)
        self.msg.emit("SQlite file successfully exported.")

    def set_commit_rollback_actions_enabled(self, on):
        self.ui.actionCommit.setEnabled(on)
        self.ui.actionRollback.setEnabled(on)

    @Slot(name="show_commit_session_dialog")
    def show_commit_session_dialog(self):
        """Query user for a commit message and commit changes to source database."""
        if not self.db_map.has_pending_changes():
            self.msg.emit("Nothing to commit yet.")
            return
        dialog = CommitDialog(self, self.database)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        self.commit_session(dialog.commit_msg)

    @busy_effect
    def commit_session(self, commit_msg):
        try:
            self.db_map.commit_session(commit_msg)
            self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes committed successfully."
        self.msg.emit(msg)

    @Slot(name="rollback_session")
    def rollback_session(self):
        try:
            self.db_map.rollback_session()
            self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes since last commit rolled back successfully."
        self.msg.emit(msg)
        self.init_models()

    @Slot(name="refresh_session")
    def refresh_session(self):
        msg = "Session refreshed."
        self.msg.emit(msg)
        self.init_models()

    def init_icon_dicts(self):
        self.object_icon_dict = {}
        object_icon = lambda x: QIcon(object_pixmap(x))
        for object_class in self.db_map.object_class_list():
            self.object_icon_dict[object_class.id] = object_icon(object_class.name)
        self.relationship_icon_dict = {}
        relationship_icon = lambda x: QIcon(relationship_pixmap(x.split(",")))
        for relationship_class in self.db_map.wide_relationship_class_list():
            object_class_name_list = relationship_class.object_class_name_list
            self.relationship_icon_dict[relationship_class.id] = relationship_icon(object_class_name_list)

    def init_models(self):
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_definition_models()

    def init_object_tree_model(self):
        """Initialize object tree model."""
        self.object_tree_model.build_tree(self.database)
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.hasChildren())
        # setup object tree view
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_object.header().hide()
        self.ui.treeView_object.expand(self.object_tree_model.root_item.index())
        self.ui.treeView_object.resizeColumnToContents(0)

    def init_parameter_value_models(self):
        """Initialize parameter value models from source database."""
        self.object_parameter_value_model.init_model()
        self.relationship_parameter_value_model.init_model()
        self.object_parameter_value_proxy.setSourceModel(self.object_parameter_value_model)
        self.relationship_parameter_value_proxy.setSourceModel(self.relationship_parameter_value_model)

    def init_parameter_definition_models(self):
        """Initialize parameter (definition) models from source database."""
        self.object_parameter_definition_model.init_model()
        self.relationship_parameter_definition_model.init_model()
        self.object_parameter_definition_proxy.setSourceModel(self.object_parameter_definition_model)
        self.relationship_parameter_definition_proxy.setSourceModel(self.relationship_parameter_definition_model)

    def init_views(self):
        self.init_object_parameter_value_view()
        self.init_relationship_parameter_value_view()
        self.init_object_parameter_view()
        self.init_relationship_parameter_view()

    def init_object_parameter_value_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_object_parameter_value.setModel(self.object_parameter_value_proxy)
        h = self.object_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('object_class_id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('object_id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter_value.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()

    def init_relationship_parameter_value_view(self):
        """Init the relationship parameter table view."""
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_proxy)
        h = self.relationship_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('relationship_class_id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_class_id_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_class_name_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_id_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter_value.horizontalHeader().\
            setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_object_parameter_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_object_parameter_definition.setModel(self.object_parameter_definition_proxy)
        h = self.object_parameter_definition_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('object_class_id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_definition.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter_definition.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_object_parameter_definition.resizeColumnsToContents()

    def init_relationship_parameter_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_relationship_parameter_definition.setModel(self.relationship_parameter_definition_proxy)
        h = self.relationship_parameter_definition_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('relationship_class_id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('object_class_id_list'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_definition.verticalHeader().\
            setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().\
            setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_relationship_parameter_definition.resizeColumnsToContents()

    @Slot("QModelIndex", name="find_next_leaf")
    def find_next_leaf(self, index):
        """If index corresponds to a relationship, then expand the next ocurrence of it."""
        if not index.isValid():
            return # just to be safe
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
        """Expand next occurrence of a relationship."""
        next_index = self.object_tree_model.next_relationship_index(index)
        if not next_index:
            return
        self.ui.treeView_object.setCurrentIndex(next_index)
        self.ui.treeView_object.scrollTo(next_index)
        self.ui.treeView_object.expand(next_index)

    @Slot("QItemSelection", "QItemSelection", name="receive_object_tree_selection_changed")
    def receive_object_tree_selection_changed(self, selected, deselected):
        """Called when the object tree selection changes.
        Update filter proxy models accordingly."""
        selected_object_class_ids = set()
        selected_object_ids = set()
        selected_relationship_class_ids = set()
        selected_object_id_lists = set()
        deselected_object_class_ids = set()
        deselected_object_ids = set()
        deselected_relationship_class_ids = set()
        deselected_object_id_lists = set()
        for index in deselected.indexes():
            item_type = index.data(Qt.UserRole)
            item = index.data(Qt.UserRole + 1)
            if item_type == 'object_class':
                deselected_object_class_ids.add(item['id'])
            elif item_type == 'object':
                deselected_object_ids.add(item['id'])
            elif item_type == 'relationship_class':
                deselected_relationship_class_ids.add(item['id'])
            elif item_type == 'relationship':
                deselected_object_id_lists.add(item['object_id_list'])
        self.object_parameter_definition_proxy.diff_update_object_class_id_set(deselected_object_class_ids)
        self.object_parameter_value_proxy.diff_update_object_class_id_set(deselected_object_class_ids)
        self.object_parameter_value_proxy.diff_update_object_id_set(deselected_object_ids)
        self.relationship_parameter_definition_proxy.\
            diff_update_relationship_class_id_set(deselected_relationship_class_ids)
        self.relationship_parameter_definition_proxy.diff_update_object_class_id_set(deselected_object_class_ids)
        self.relationship_parameter_value_proxy.diff_update_relationship_class_id_set(
            deselected_relationship_class_ids)
        self.relationship_parameter_value_proxy.diff_update_object_class_id_set(deselected_object_class_ids)
        self.relationship_parameter_value_proxy.diff_update_object_id_set(deselected_object_ids)
        self.relationship_parameter_value_proxy.diff_update_object_id_list_set(deselected_object_id_lists)
        for index in selected.indexes():
            item_type = index.data(Qt.UserRole)
            item = index.data(Qt.UserRole + 1)
            if item_type == 'object_class':
                selected_object_class_ids.add(item['id'])
            elif item_type == 'object':
                selected_object_ids.add(item['id'])
            elif item_type == 'relationship_class':
                selected_relationship_class_ids.add(item['id'])
            elif item_type == 'relationship':
                selected_object_id_lists.add(item['object_id_list'])
        self.object_parameter_definition_proxy.update_object_class_id_set(selected_object_class_ids)
        self.object_parameter_value_proxy.update_object_class_id_set(selected_object_class_ids)
        self.object_parameter_value_proxy.update_object_id_set(selected_object_ids)
        self.relationship_parameter_definition_proxy.update_relationship_class_id_set(selected_relationship_class_ids)
        self.relationship_parameter_definition_proxy.update_object_class_id_set(selected_object_class_ids)
        self.relationship_parameter_value_proxy.update_relationship_class_id_set(selected_relationship_class_ids)
        self.relationship_parameter_value_proxy.update_object_class_id_set(selected_object_class_ids)
        self.relationship_parameter_value_proxy.update_object_id_set(selected_object_ids)
        self.relationship_parameter_value_proxy.update_object_id_list_set(selected_object_id_lists)
        if self.ui.tabWidget_object.currentIndex() == 0:
            self.object_parameter_value_proxy.apply_filter()
        else:
            self.object_parameter_definition_proxy.apply_filter()
        if self.ui.tabWidget_relationship.currentIndex() == 0:
            self.relationship_parameter_value_proxy.apply_filter()
        else:
            self.relationship_parameter_definition_proxy.apply_filter()

    @Slot(name="hide_unused_object_name_columns")
    def hide_unused_object_name_columns(self):
        """Hide unused object name columns in relationship parameter value view."""
        max_object_count = len(self.relationship_parameter_value_model.object_name_range)
        object_count = self.relationship_parameter_value_proxy.object_count
        if not object_count:
            object_count = max_object_count
        object_name_1_column = self.relationship_parameter_value_model.object_name_range.start
        for column in range(object_name_1_column, object_name_1_column + object_count):
            self.ui.tableView_relationship_parameter_value.horizontalHeader().showSection(column)
        for column in range(object_name_1_column + object_count, object_name_1_column + max_object_count):
            self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(column)

    @Slot("QObject", "int", "QStringList", name="apply_autofilter")
    def apply_autofilter(self, proxy_model, column, text_list):
        """Called when the tableview wants to trigger the subfilter."""
        header = proxy_model.sourceModel().horizontal_header_labels()
        kwargs = {header[column]: text_list}
        proxy_model.add_rule(**kwargs)
        proxy_model.apply_filter()

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
        if option == "Copy":
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
        elif option.startswith("Remove selected"):
            self.remove_object_tree_items()
        elif option == "Add parameter definitions":
            self.call_add_parameters(index)
        elif option == "Add parameter values":
            self.call_add_parameter_values(index)
        elif option == "Fully expand":
            self.fully_expand_selection()
        elif option == "Fully collapse":
            self.fully_collapse_selection()
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    def fully_expand_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            self.object_tree_model.forward_sweep(index, call=self.ui.treeView_object.expand)

    def fully_collapse_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            self.object_tree_model.forward_sweep(index, call=self.ui.treeView_object.collapse)

    def call_show_add_objects_form(self, index):
        class_id = index.data(Qt.UserRole + 1)['id']
        self.show_add_objects_form(class_id=class_id)

    def call_show_add_relationship_classes_form(self, index):
        object_class_id = index.data(Qt.UserRole + 1)['id']
        self.show_add_relationship_classes_form(object_class_id=object_class_id)

    def call_show_add_relationships_form(self, index):
        relationship_class = index.data(Qt.UserRole + 1)
        object_ = index.parent().data(Qt.UserRole + 1)
        object_class = index.parent().parent().data(Qt.UserRole + 1)
        self.show_add_relationships_form(
            relationship_class_id=relationship_class['id'],
            object_id=object_['id'],
            object_class_id=object_class['id'])

    def call_add_parameters(self, tree_index):
        class_type = tree_index.data(Qt.UserRole)
        if class_type == 'object_class':
            self.add_object_parameter_definitions()
        elif class_type == 'relationship_class':
            self.add_relationship_parameter_definitions()

    def call_add_parameter_values(self, tree_index):
        entity_type = tree_index.data(Qt.UserRole)
        if entity_type == 'object':
            self.add_object_parameter_values()
        elif entity_type == 'relationship':
            self.add_relationship_parameter_values()

    @Slot(name="show_add_object_classes_form")
    def show_add_object_classes_form(self):
        """Show dialog to let user select preferences for new object classes."""
        dialog = AddObjectClassesDialog(self)
        dialog.show()

    def add_object_classes(self, object_classes):
        """Insert new object classes."""
        for object_class in object_classes:
            self.object_tree_model.add_object_class(object_class)
        self.set_commit_rollback_actions_enabled(True)
        self.ui.actionExport.setEnabled(True)
        msg = "Successfully added new object classes '{}'.".format("', '".join([x.name for x in object_classes]))
        self.msg.emit(msg)

    @Slot(name="show_add_objects_form")
    def show_add_objects_form(self, class_id=None):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, class_id=class_id)
        dialog.show()

    def add_objects(self, objects):
        """Insert new objects."""
        for object_ in objects:
            self.object_tree_model.add_object(object_)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully added new objects '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)

    def show_add_relationship_classes_form(self, object_class_id=None):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(self, object_class_one_id=object_class_id)
        dialog.show()

    def add_relationship_classes(self, wide_relationship_classes):
        """Insert new relationship classes."""
        object_name_list_lengths = list()
        for wide_relationship_class in wide_relationship_classes:
            self.object_tree_model.add_relationship_class(wide_relationship_class)
            object_name_list_lengths.append(len(wide_relationship_class.object_class_id_list.split(',')))
        object_name_list_length = max(object_name_list_lengths)
        self.relationship_parameter_value_model.extend_object_name_range(object_name_list_length)
        self.hide_unused_object_name_columns()
        self.set_commit_rollback_actions_enabled(True)
        relationship_class_name_list = "', '".join([x.name for x in wide_relationship_classes])
        msg = "Successfully added new relationship classes '{}'.".format(relationship_class_name_list)
        self.msg.emit(msg)

    @Slot(name="show_add_relationships_form")
    def show_add_relationships_form(self, relationship_class_id=None, object_id=None, object_class_id=None):
        """Show dialog to let user select preferences for new relationships."""
        dialog = AddRelationshipsDialog(
            self,
            relationship_class_id=relationship_class_id,
            object_id=object_id,
            object_class_id=object_class_id
        )
        dialog.show()

    def add_relationships(self, wide_relationships):
        """Insert new relationships."""
        for wide_relationship in wide_relationships:
            self.object_tree_model.add_relationship(wide_relationship)
        self.set_commit_rollback_actions_enabled(True)
        relationship_name_list = "', '".join([x.name for x in wide_relationships])
        msg = "Successfully added new relationships '{}'.".format(relationship_name_list)
        self.msg.emit(msg)

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

    def show_edit_object_classes_form(self):
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole) != "object_class":
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditObjectClassesDialog(self, kwargs_list)
        dialog.show()

    @busy_effect
    def update_object_classes(self, object_classes, orig_kwargs_list):
        """Update object classes."""
        self.object_tree_model.update_object_classes(object_classes)
        new_names = list()
        curr_names = list()
        for object_class in object_classes:
            try:
                curr_name = next(x for x in orig_kwargs_list if x["id"] == object_class.id)["name"]
                curr_names.append(curr_name)
                new_names.append(object_class.name)
            except StopIteration:
                continue
        self.rename_items_in_parameter_models('object_class', new_names, curr_names)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully updated object classes '{}'.".format("', '".join([x.name for x in object_classes]))
        self.msg.emit(msg)

    def show_edit_objects_form(self):
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole) != "object":
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditObjectsDialog(self, kwargs_list)
        dialog.show()

    @busy_effect
    def update_objects(self, objects, orig_kwargs_list):
        """Update objects."""
        self.object_tree_model.update_objects(objects)
        new_names = list()
        curr_names = list()
        for object_ in objects:
            try:
                curr_name = next(x for x in orig_kwargs_list if x["id"] == object_.id)["name"]
                curr_names.append(curr_name)
                new_names.append(object_.name)
            except StopIteration:
                continue
        self.rename_items_in_parameter_models('object', new_names, curr_names)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully updated objects '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)

    def show_edit_relationship_classes_form(self):
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole) != "relationship_class":
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditRelationshipClassesDialog(self, kwargs_list)
        dialog.show()

    @busy_effect
    def update_relationship_classes(self, wide_relationship_classes, orig_kwargs_list):
        """Update relationship classes."""
        self.object_tree_model.update_relationship_classes(wide_relationship_classes)
        new_names = list()
        curr_names = list()
        for wide_relationship_class in wide_relationship_classes:
            try:
                curr_name = next(x for x in orig_kwargs_list if x["id"] == wide_relationship_class.id)["name"]
                curr_names.append(curr_name)
                new_names.append(wide_relationship_class.name)
            except StopIteration:
                continue
        self.rename_items_in_parameter_models('relationship_class', new_names, curr_names)
        self.set_commit_rollback_actions_enabled(True)
        relationship_class_name_list = "', '".join([x.name for x in wide_relationship_classes])
        msg = "Successfully updated relationship classes '{}'.".format(relationship_class_name_list)
        self.msg.emit(msg)

    def show_edit_relationships_form(self):
        current = self.ui.treeView_object.currentIndex()
        if current.data(Qt.UserRole) != "relationship":
            return
        class_id = current.data(Qt.UserRole + 1)['class_id']
        wide_relationship_class = self.db_map.single_wide_relationship_class(id=class_id).one_or_none()
        if not wide_relationship_class:
            return
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole) != "relationship":
                continue
            # Only edit relationships of the same class as the one in current index, for now...
            if index.data(Qt.UserRole + 1)['class_id'] != class_id:
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditRelationshipsDialog(self, kwargs_list, wide_relationship_class)
        dialog.show()

    @busy_effect
    def update_relationships(self, wide_relationships, orig_kwargs_list):
        """Update relationships."""
        self.object_tree_model.update_relationships(wide_relationships)
        # NOTE: we don't need to call rename_items_in_parameter_models here, for now
        self.set_commit_rollback_actions_enabled(True)
        relationship_name_list = "', '".join([x.name for x in wide_relationships])
        msg = "Successfully updated relationships '{}'.".format(relationship_name_list)
        self.msg.emit(msg)

    def rename_items_in_parameter_models(self, renamed_type, new_names, curr_names):
        """Rename items in parameter definition and value models."""
        self.object_parameter_definition_model.rename_items(renamed_type, new_names, curr_names)
        self.object_parameter_value_model.rename_items(renamed_type, new_names, curr_names)
        self.relationship_parameter_definition_model.rename_items(renamed_type, new_names, curr_names)
        self.relationship_parameter_value_model.rename_items(renamed_type, new_names, curr_names)

    @busy_effect
    def remove_object_tree_items(self):
        """Remove all selected items from the object treeview."""
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        removed_id_dict = {}
        for index in indexes:
            removed_type = index.data(Qt.UserRole)
            removed_id = index.data(Qt.UserRole + 1)['id']
            removed_id_dict.setdefault(removed_type, set()).add(removed_id)
        try:
            self.db_map.remove_items(**{k + "_ids": v for k, v in removed_id_dict.items()})
            removed_name_dict = {}
            for key, value in removed_id_dict.items():
                removed_name_dict.update(self.object_tree_model.remove_items(key, *value))
            for key, value in removed_name_dict.items():
                self.object_parameter_definition_model.remove_items(key, *value)
                self.object_parameter_value_model.remove_items(key, *value)
                self.relationship_parameter_definition_model.remove_items(key, *value)
                self.relationship_parameter_value_model.remove_items(key, *value)
            self.set_commit_rollback_actions_enabled(True)
            self.ui.actionExport.setEnabled(self.object_tree_model.root_item.hasChildren())
            self.msg.emit("Successfully removed items.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @Slot("QPoint", name="show_object_parameter_value_context_menu")
    def show_object_parameter_value_context_menu(self, pos):
        """Context menu for object parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_object_parameter_value.indexAt(pos)
        global_pos = self.ui.tableView_object_parameter_value.viewport().mapToGlobal(pos)
        remove_icon = self.ui.actionRemove_object_parameter_values.icon()
        self.object_parameter_value_context_menu = ParameterContextMenu(self, global_pos, index, remove_icon)
        option = self.object_parameter_value_context_menu.get_action()
        if option == "Remove selected":
            self.remove_object_parameter_values()
        elif option == "Copy":
            self.ui.tableView_object_parameter_value.copy()
        elif option == "Paste":
            self.ui.tableView_object_parameter_value.paste(self.clipboard_text)
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
        remove_icon = self.ui.actionRemove_relationship_parameter_values.icon()
        self.relationship_parameter_value_context_menu = ParameterContextMenu(self, global_pos, index, remove_icon)
        option = self.relationship_parameter_value_context_menu.get_action()
        if option == "Remove selected":
            self.remove_relationship_parameter_values()
        elif option == "Copy":
            self.ui.tableView_relationship_parameter_value.copy()
        elif option == "Paste":
            self.ui.tableView_relationship_parameter_value.paste(self.clipboard_text)
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
        remove_icon = self.ui.actionRemove_object_parameter_definitions.icon()
        self.object_parameter_context_menu = ParameterContextMenu(self, global_pos, index, remove_icon)
        option = self.object_parameter_context_menu.get_action()
        if option == "Remove selected":
            self.remove_object_parameter_definitions()
        elif option == "Copy":
            self.ui.tableView_object_parameter_definition.copy()
        elif option == "Paste":
            self.ui.tableView_object_parameter_definition.paste(self.clipboard_text)
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
        remove_icon = self.ui.actionRemove_relationship_parameter_definitions.icon()
        self.relationship_parameter_context_menu = ParameterContextMenu(self, global_pos, index, remove_icon)
        option = self.relationship_parameter_context_menu.get_action()
        if option == "Remove selected":
            self.remove_relationship_parameter_definitions()
        elif option == "Copy":
            self.ui.tableView_relationship_parameter_definition.copy()
        elif option == "Paste":
            self.ui.tableView_relationship_parameter_definition.paste(self.clipboard_text)
        self.relationship_parameter_context_menu.deleteLater()
        self.relationship_parameter_context_menu = None

    @Slot(name="add_object_parameter_values")
    def add_object_parameter_values(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter value row if needed.
        """
        model = self.object_parameter_value_model
        proxy_index = self.ui.tableView_object_parameter_value.currentIndex()
        index = self.object_parameter_value_proxy.mapToSource(proxy_index)
        row = model.rowCount() - 1
        tree_selection = self.ui.treeView_object.selectionModel().selection()
        if not tree_selection.isEmpty():
            object_class_name_column = model.horizontal_header_labels().index('object_class_name')
            object_name_column = model.horizontal_header_labels().index('object_name')
            row_column_tuples = list()
            data = list()
            i = 0
            for tree_index in tree_selection.indexes():
                if tree_index.data(Qt.UserRole) == 'object_class':
                    object_class_name = tree_index.data(Qt.DisplayRole)
                    object_name = None
                elif tree_index.data(Qt.UserRole) == 'object':
                    object_class_name = tree_index.parent().data(Qt.DisplayRole)
                    object_name = tree_index.data(Qt.DisplayRole)
                else:
                    continue
                row_column_tuples.append((row + i, object_class_name_column))
                row_column_tuples.append((row + i, object_name_column))
                data.extend([object_class_name, object_name])
                i += 1
            if i > 0:
                model.insertRows(row, i)
                indexes = [model.index(row, column) for row, column in row_column_tuples]
                model.batch_set_data(indexes, data)
        self.ui.tabWidget_object.setCurrentIndex(0)
        self.object_parameter_value_proxy.apply_filter()

    @Slot(name="add_relationship_parameter_values")
    def add_relationship_parameter_values(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter value row if needed.
        """
        model = self.relationship_parameter_value_model
        proxy_index = self.ui.tableView_relationship_parameter_value.currentIndex()
        index = self.relationship_parameter_value_proxy.mapToSource(proxy_index)
        row = model.rowCount() - 1
        tree_selection = self.ui.treeView_object.selectionModel().selection()
        if not tree_selection.isEmpty():
            relationship_class_name_column = model.horizontal_header_labels().index('relationship_class_name')
            object_name_1_column = model.object_name_range.start
            row_column_tuples = list()
            data = list()
            i = 0
            for tree_index in tree_selection.indexes():
                if tree_index.data(Qt.UserRole) == 'relationship_class':
                    selected_object_class_name = tree_index.parent().parent().data(Qt.DisplayRole)
                    object_name = tree_index.parent().data(Qt.DisplayRole)
                    relationship_class_name = tree_index.data(Qt.DisplayRole)
                    object_class_name_list = tree_index.data(Qt.UserRole + 1)["object_class_name_list"].split(",")
                    object_name_list = list()
                    for object_class_name in object_class_name_list:
                        if object_class_name == selected_object_class_name:
                            object_name_list.append(object_name)
                        else:
                            object_name_list.append(None)
                elif tree_index.data(Qt.UserRole) == 'relationship':
                    relationship_class_name = tree_index.parent().data(Qt.DisplayRole)
                    object_name_list = tree_index.data(Qt.UserRole + 1)["object_name_list"].split(",")
                else:
                    continue
                row_column_tuples.append((row + i, relationship_class_name_column))
                data.append(relationship_class_name)
                for j, object_name in enumerate(object_name_list):
                    row_column_tuples.append((row + i, object_name_1_column + j))
                    data.append(object_name)
                i += 1
            if i > 0:
                model.insertRows(row, i)
                indexes = [model.index(row, column) for row, column in row_column_tuples]
                model.batch_set_data(indexes, data)
        self.ui.tabWidget_relationship.setCurrentIndex(0)
        self.relationship_parameter_value_proxy.apply_filter()

    @Slot(name="add_object_parameter_definitions")
    def add_object_parameter_definitions(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter value row if needed.
        """
        model = self.object_parameter_definition_model
        proxy_index = self.ui.tableView_object_parameter_definition.currentIndex()
        index = self.object_parameter_definition_proxy.mapToSource(proxy_index)
        row = model.rowCount() - 1
        tree_selection = self.ui.treeView_object.selectionModel().selection()
        if not tree_selection.isEmpty():
            object_class_name_column = model.horizontal_header_labels().index('object_class_name')
            row_column_tuples = list()
            data = list()
            i = 0
            for tree_index in tree_selection.indexes():
                if tree_index.data(Qt.UserRole) == 'object_class':
                    object_class_name = tree_index.data(Qt.DisplayRole)
                elif tree_index.data(Qt.UserRole) == 'object':
                    object_class_name = tree_index.parent().data(Qt.DisplayRole)
                else:
                    continue
                row_column_tuples.append((row + i, object_class_name_column))
                data.append(object_class_name)
                i += 1
            if i > 0:
                model.insertRows(row, i)
                indexes = [model.index(row, column) for row, column in row_column_tuples]
                model.batch_set_data(indexes, data)
        self.ui.tabWidget_object.setCurrentIndex(1)
        self.object_parameter_definition_proxy.apply_filter()

    @Slot(name="add_relationship_parameter_definitions")
    def add_relationship_parameter_definitions(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter row if needed.
        """
        model = self.relationship_parameter_definition_model
        proxy_index = self.ui.tableView_relationship_parameter_definition.currentIndex()
        index = self.relationship_parameter_definition_proxy.mapToSource(proxy_index)
        row = model.rowCount() - 1
        tree_selection = self.ui.treeView_object.selectionModel().selection()
        if not tree_selection.isEmpty():
            relationship_class_name_column = model.horizontal_header_labels().index('relationship_class_name')
            row_column_tuples = list()
            data = list()
            i = 0
            for tree_index in tree_selection.indexes():
                if tree_index.data(Qt.UserRole) == 'relationship_class':
                    relationship_class_name = tree_index.data(Qt.DisplayRole)
                elif tree_index.data(Qt.UserRole) == 'relationship':
                    relationship_class_name = tree_index.parent().data(Qt.DisplayRole)
                else:
                    continue
                row_column_tuples.append((row + i, relationship_class_name_column))
                data.append(relationship_class_name)
                i += 1
            if i > 0:
                model.insertRows(row, i)
                indexes = [model.index(row, column) for row, column in row_column_tuples]
                model.batch_set_data(indexes, data)
        self.ui.tabWidget_relationship.setCurrentIndex(1)
        self.relationship_parameter_definition_proxy.apply_filter()

    @Slot("QModelIndex", "QVariant", name="set_parameter_value_data")
    def set_parameter_value_data(self, index, new_value):
        """Update (object or relationship) parameter value with newly edited data."""
        if new_value is None:
            return
        proxy_model = index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        source_model.setData(source_index, new_value)

    @Slot("QModelIndex", "QVariant", name="set_parameter_definition_data")
    def set_parameter_definition_data(self, index, new_value):
        """Update (object or relationship) parameter definition with newly edited data."""
        if new_value is None:
            return
        proxy_model = index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        parameter_name_column = source_model.horizontal_header_labels().index('parameter_name')
        if source_index.column() == parameter_name_column:
            curr_name = source_index.data(Qt.DisplayRole)
        if source_model.setData(source_index, new_value) and source_index.column() == parameter_name_column:
            new_name = source_index.data(Qt.DisplayRole)
            self.object_parameter_value_model.rename_items("parameter", [new_name], [curr_name])
            self.relationship_parameter_value_model.rename_items("parameter", [new_name], [curr_name])

    @busy_effect
    @Slot(name="remove_object_parameter_values")
    def remove_object_parameter_values(self):
        selection = self.ui.tableView_object_parameter_value.selectionModel().selection()
        source_row_set = self.source_row_set(selection, self.object_parameter_value_proxy)
        parameter_value_ids = set()
        id_column = self.object_parameter_value_model.horizontal_header_labels().index("id")
        for source_row in source_row_set:
            if self.object_parameter_value_model.is_work_in_progress(source_row):
                continue
            source_index = self.object_parameter_value_model.index(source_row, id_column)
            parameter_value_ids.add(source_index.data(Qt.EditRole))
        try:
            self.db_map.remove_items(parameter_value_ids=parameter_value_ids)
            self.object_parameter_value_model.remove_row_set(source_row_set)
            self.set_commit_rollback_actions_enabled(True)
            self.msg.emit("Successfully removed parameter vales.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    @Slot(name="remove_relationship_parameter_values")
    def remove_relationship_parameter_values(self):
        selection = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        source_row_set = self.source_row_set(selection, self.relationship_parameter_value_proxy)
        parameter_value_ids = set()
        id_column = self.relationship_parameter_value_model.horizontal_header_labels().index("id")
        for source_row in source_row_set:
            if self.relationship_parameter_value_model.is_work_in_progress(source_row):
                continue
            source_index = self.relationship_parameter_value_model.index(source_row, id_column)
            parameter_value_ids.add(source_index.data(Qt.EditRole))
        try:
            self.db_map.remove_items(parameter_value_ids=parameter_value_ids)
            self.relationship_parameter_value_model.remove_row_set(source_row_set)
            self.set_commit_rollback_actions_enabled(True)
            self.msg.emit("Successfully removed parameter vales.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    @Slot(name="remove_object_parameter_definitions")
    def remove_object_parameter_definitions(self):
        selection = self.ui.tableView_object_parameter_definition.selectionModel().selection()
        source_row_set = self.source_row_set(selection, self.object_parameter_definition_proxy)
        parameter_ids = set()
        parameter_names = set()
        id_column = self.object_parameter_definition_model.horizontal_header_labels().index("id")
        name_column = self.object_parameter_definition_model.horizontal_header_labels().index("parameter_name")
        for source_row in source_row_set:
            if self.object_parameter_definition_model.is_work_in_progress(source_row):
                continue
            source_index = self.object_parameter_definition_model.index(source_row, id_column)
            parameter_ids.add(source_index.data(Qt.EditRole))
            source_index = self.object_parameter_definition_model.index(source_row, name_column)
            parameter_names.add(source_index.data(Qt.DisplayRole))
        try:
            self.db_map.remove_items(parameter_ids=parameter_ids)
            self.object_parameter_definition_model.remove_row_set(source_row_set)
            self.object_parameter_value_model.remove_items("parameter", *parameter_names)
            self.set_commit_rollback_actions_enabled(True)
            self.msg.emit("Successfully removed parameters.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    @Slot(name="remove_relationship_parameter_definitions")
    def remove_relationship_parameter_definitions(self):
        selection = self.ui.tableView_relationship_parameter_definition.selectionModel().selection()
        source_row_set = self.source_row_set(selection, self.relationship_parameter_definition_proxy)
        parameter_ids = set()
        parameter_names = set()
        id_column = self.relationship_parameter_definition_model.horizontal_header_labels().index("id")
        name_column = self.relationship_parameter_definition_model.horizontal_header_labels().index("parameter_name")
        for source_row in source_row_set:
            if self.relationship_parameter_definition_model.is_work_in_progress(source_row):
                continue
            source_index = self.relationship_parameter_definition_model.index(source_row, id_column)
            parameter_ids.add(source_index.data(Qt.EditRole))
            source_index = self.relationship_parameter_definition_model.index(source_row, name_column)
            parameter_names.add(source_index.data(Qt.DisplayRole))
        try:
            self.db_map.remove_items(parameter_ids=parameter_ids)
            self.relationship_parameter_definition_model.remove_row_set(source_row_set)
            self.relationship_parameter_value_model.remove_items("parameter", *parameter_names)
            self.set_commit_rollback_actions_enabled(True)
            self.msg.emit("Successfully removed parameters.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    def source_row_set(self, selection, proxy_model):
        """A set of source rows corresponding to a selection of proxy indexes
        from any of the following models:
        object_parameter_definition_model, relationship_parameter_definition_model,
        object_parameter_value_model, relationship_parameter_value_model
        """
        if selection.isEmpty():
            return {}
        proxy_row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            proxy_row_set.update(range(top, bottom + 1))
        return {proxy_model.map_row_to_source(r) for r in proxy_row_set}

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("treeViewWidget/windowSize")
        window_pos = self.qsettings.value("treeViewWidget/windowPosition")
        splitter_tree_parameter_state = self.qsettings.value("treeViewWidget/splitterTreeParameterState")
        window_maximized = self.qsettings.value("treeViewWidget/windowMaximized", defaultValue='false')  # returns str
        n_screens = self.qsettings.value("mainWindow/n_screens", defaultValue=1)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if splitter_tree_parameter_state:
            self.ui.splitter_tree_parameter.restoreState(splitter_tree_parameter_state)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)

    def show_commit_session_prompt(self):
        """Shows the commit session message box."""
        config = self._data_store._toolbox._config
        commit_at_exit = config.get("settings", "commit_at_exit")
        if commit_at_exit == "0":
            # Don't commit session and don't show message box
            return
        elif commit_at_exit == "1":  # Default
            # Show message box
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Commit pending changes")
            msg.setText("The current session has uncommitted changes. Do you want to commit them now?")
            msg.setInformativeText("WARNING: If you choose not to commit, all changes will be lost.")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()
            chk = chkbox.checkState()
            if answer == QMessageBox.Yes:
                self.show_commit_session_dialog()
                if chk == 2:
                    # Save preference into config file
                    config.set("settings", "commit_at_exit", "2")
            else:
                if chk == 2:
                    # Save preference into config file
                    config.set("settings", "commit_at_exit", "0")
        elif commit_at_exit == "2":
            # Commit session and don't show message box
            self.show_commit_session_dialog()
        else:
            config.set("settings", "commit_at_exit", "1")
        return

    def close_editors(self):
        """Close any open editor in the parameter table views.
        Call this before closing the database mapping."""
        current = self.ui.tableView_object_parameter_definition.currentIndex()
        if self.ui.tableView_object_parameter_definition.isPersistentEditorOpen(current):
            self.ui.tableView_object_parameter_definition.closePersistentEditor(current)
        current = self.ui.tableView_object_parameter_value.currentIndex()
        if self.ui.tableView_object_parameter_value.isPersistentEditorOpen(current):
            self.ui.tableView_object_parameter_value.closePersistentEditor(current)
        current = self.ui.tableView_relationship_parameter_definition.currentIndex()
        if self.ui.tableView_relationship_parameter_definition.isPersistentEditorOpen(current):
            self.ui.tableView_relationship_parameter_definition.closePersistentEditor(current)
        current = self.ui.tableView_relationship_parameter_value.currentIndex()
        if self.ui.tableView_relationship_parameter_value.isPersistentEditorOpen(current):
            self.ui.tableView_relationship_parameter_value.closePersistentEditor(current)

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue(
            "treeViewWidget/splitterTreeParameterState",
            self.ui.splitter_tree_parameter.saveState())
        self.qsettings.setValue("treeViewWidget/windowSize", self.size())
        self.qsettings.setValue("treeViewWidget/windowPosition", self.pos())
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("treeViewWidget/windowMaximized", True)
        else:
            self.qsettings.setValue("treeViewWidget/windowMaximized", False)
        self.close_editors()
        if self.db_map.has_pending_changes():
            self.show_commit_session_prompt()
        self.db_map.close()
        if event:
            event.accept()
