#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Widget to show Data Store Form.

:author: M. Marin (KTH)
:date:   21.4.2018
"""

import os
import time  # just to measure loading time and sqlalchemy ORM performance
import logging
from PySide2.QtWidgets import QMainWindow, QHeaderView, QDialog, QLineEdit, QInputDialog, \
    QMessageBox, QFileDialog, QApplication
from PySide2.QtCore import Signal, Slot, Qt, QSettings
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon
from ui.data_store_form import Ui_MainWindow
from config import STATUSBAR_SS
from spinedatabase_api import SpineDBAPIError
from widgets.custom_menus import ObjectTreeContextMenu, ParameterContextMenu
from widgets.custom_delegates import ObjectParameterValueDelegate, ObjectParameterDelegate, \
    RelationshipParameterValueDelegate, RelationshipParameterDelegate
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, AddRelationshipClassesDialog, \
    AddRelationshipsDialog, CommitDialog
from models import ObjectTreeModel, ObjectParameterValueModel, ObjectParameterModel, \
    RelationshipParameterModel, RelationshipParameterValueModel, \
    ObjectParameterProxy, ObjectParameterValueProxy, RelationshipParameterProxy, RelationshipParameterValueProxy
from excel_import_export import import_xlsx_to_db, export_spine_database_to_xlsx
from datapackage_import_export import import_datapackage
from helpers import busy_effect


class DataStoreForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        data_store (DataStore): The DataStore instance that owns this form
        db_map (DatabaseMapping): The object relational database mapping
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
        # NOTE: Alternatively, make this class inherit from QWidget rather than QMainWindow,
        # and implement the menubar by hand
        self._data_store = data_store
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.actionCopy.setIcon(QIcon.fromTheme("edit-copy"))
        self.ui.actionPaste.setIcon(QIcon.fromTheme("edit-paste"))
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Set up status bar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Class attributes
        # DB db_map
        self.db_map = db_map
        self.database = database
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self)
        # Parameter value models
        self.object_parameter_value_model = ObjectParameterValueModel(self)
        self.object_parameter_value_proxy = ObjectParameterValueProxy(self)
        self.relationship_parameter_value_model = RelationshipParameterValueModel(self)
        self.relationship_parameter_value_proxy = RelationshipParameterValueProxy(self)
        # Parameter (definition) models
        self.object_parameter_model = ObjectParameterModel(self)
        self.object_parameter_proxy = ObjectParameterProxy(self)
        self.relationship_parameter_model = RelationshipParameterModel(self)
        self.relationship_parameter_proxy = RelationshipParameterProxy(self)
        # Context menus
        self.object_tree_context_menu = None
        self.object_parameter_value_context_menu = None
        self.relationship_parameter_value_context_menu = None
        self.object_parameter_context_menu = None
        self.relationship_parameter_context_menu = None
        # Others
        self.clipboard = QApplication.clipboard()
        self.clipboard_text = self.clipboard.text()
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        # init models and views
        self.init_models()
        self.init_views()
        self.setup_delegates()
        self.setup_buttons()
        self.connect_signals()
        self.restore_ui()
        self.setWindowTitle("Spine Data Store    -- {} --".format(self.database))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        toc = time.clock()
        logging.debug("Data Store form created in {} seconds".format(toc - tic))

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
        self.ui.toolButton_add_object_parameters.\
            setDefaultAction(self.ui.actionAdd_object_parameters)
        self.ui.toolButton_remove_object_parameters.\
            setDefaultAction(self.ui.actionRemove_object_parameters)
        self.ui.toolButton_add_relationship_parameters.\
            setDefaultAction(self.ui.actionAdd_relationship_parameters)
        self.ui.toolButton_remove_relationship_parameters.\
            setDefaultAction(self.ui.actionRemove_relationship_parameters)

    def setup_delegates(self):
        """Set delegates for tables."""
        self.ui.tableView_object_parameter_value.setItemDelegate(ObjectParameterValueDelegate(self))
        self.ui.tableView_relationship_parameter_value.setItemDelegate(RelationshipParameterValueDelegate(self))
        self.ui.tableView_object_parameter.setItemDelegate(ObjectParameterDelegate(self))
        self.ui.tableView_relationship_parameter.setItemDelegate(RelationshipParameterDelegate(self))

    def connect_signals(self):
        """Connect signals to slots."""
        # Event log signals
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        # Menu commands
        self.ui.actionImport.triggered.connect(self.show_import_file_dialog)
        self.ui.actionExport.triggered.connect(self.show_export_file_dialog)
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionAdd_object_classes.triggered.connect(self.show_add_object_classes_form)
        self.ui.actionAdd_objects.triggered.connect(self.show_add_objects_form)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.show_add_relationship_classes_form)
        self.ui.actionAdd_relationships.triggered.connect(self.show_add_relationships_form)
        self.ui.actionAdd_object_parameter_values.triggered.connect(self.add_object_parameter_values)
        self.ui.actionAdd_relationship_parameter_values.triggered.connect(self.add_relationship_parameter_values)
        self.ui.actionAdd_object_parameters.triggered.connect(self.add_object_parameters)
        self.ui.actionAdd_relationship_parameters.triggered.connect(self.add_relationship_parameters)
        self.ui.actionRemove_object_parameters.triggered.connect(self.remove_object_parameters)
        self.ui.actionRemove_object_parameter_values.triggered.connect(self.remove_object_parameter_values)
        self.ui.actionRemove_relationship_parameters.triggered.connect(self.remove_relationship_parameters)
        self.ui.actionRemove_relationship_parameter_values.triggered.connect(self.remove_relationship_parameter_values)
        # Copy and paste
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        # Object tree
        self.ui.treeView_object.selectionModel().currentChanged.connect(self.filter_parameter_value_models)
        self.ui.treeView_object.selectionModel().currentChanged.connect(self.filter_parameter_models)
        self.ui.treeView_object.editKeyPressed.connect(self.rename_item)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.expand_next_leaf)
        # Horizontal header subfilter
        self.ui.tableView_object_parameter_value.filter_changed.connect(self.apply_parameter_model_subfilter)
        self.ui.tableView_relationship_parameter_value.filter_changed.connect(self.apply_parameter_model_subfilter)
        self.ui.tableView_object_parameter.filter_changed.connect(self.apply_parameter_model_subfilter)
        self.ui.tableView_relationship_parameter.filter_changed.connect(self.apply_parameter_model_subfilter)
        # Parameter table editors
        self.ui.tableView_object_parameter_value.itemDelegate().commitData.\
            connect(self.update_parameter_value_in_model)
        self.ui.tableView_relationship_parameter_value.itemDelegate().commitData.\
            connect(self.update_parameter_value_in_model)
        self.ui.tableView_object_parameter.itemDelegate().commitData.\
            connect(self.update_parameter_in_model)
        self.ui.tableView_relationship_parameter.itemDelegate().commitData.\
            connect(self.update_parameter_in_model)
        # Context menu requested
        self.ui.tableView_object_parameter_value.customContextMenuRequested.\
            connect(self.show_object_parameter_value_context_menu)
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.\
            connect(self.show_relationship_parameter_value_context_menu)
        self.ui.tableView_object_parameter.customContextMenuRequested.\
            connect(self.show_object_parameter_context_menu)
        self.ui.tableView_relationship_parameter.customContextMenuRequested.\
            connect(self.show_relationship_parameter_context_menu)
        # Clipboard data changed
        self.clipboard.dataChanged.connect(self.clipboard_data_changed)
        # Edit menu about to show
        self.ui.menuEdit.aboutToShow.connect(self.set_paste_enabled)
        # DS destroyed
        self._data_store.destroyed.connect(self.close)

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
        """Show error message in message box.

        Args:
            msg (str): String to show in QMessageBox
        """
        QApplication.restoreOverrideCursor()
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Operation failed")
        msg_box.setText(msg)
        msg_box.exec_()

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
        except AttributeError as err:
            self.msg.emit("Cannot copy from widget ({0}): {1}".format(focus_widget.objectName(), err))

    @Slot(name="paste")
    def paste(self):
        """Paste data from clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.paste(self.clipboard_text)
        except AttributeError as err:
            self.msg.emit("Cannot paste to widget ({0}): {1}".format(focus_widget.objectName(), err))

    @Slot(name="set_paste_enabled")
    def set_paste_enabled(self):
        """Called when Edit menu is about to show.
        Enable or disable paste options depending on wheter or not
        the focus is on one of the parameter tables.
        """
        on = False
        on |= self.ui.tableView_object_parameter.hasFocus()
        on |= self.ui.tableView_relationship_parameter.hasFocus()
        on |= self.ui.tableView_object_parameter_value.hasFocus()
        on |= self.ui.tableView_relationship_parameter_value.hasFocus()
        self.ui.actionPaste.setEnabled(on)

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
                self.init_parameter_models()
                self.msg.emit("Datapackage successfully imported.")
            except SpineDBAPIError as e:
                self.msg_error.emit("Unable to import datapackage: {}.".format(e.msg))
        elif file_path.lower().endswith('xlsx'):
            try:
                insert_log, error_log = import_xlsx_to_db(self.db_map, file_path)
                self.msg.emit("Excel file successfully imported.")
                logging.debug(insert_log)
                logging.debug(error_log)
                self.init_models()
            except SpineDBAPIError as e:
                self.msg_error.emit("Unable to import Excel file: {}".format(e.msg))

    @Slot(name="show_export_file_dialog")
    def show_export_file_dialog(self):
        """Show dialog to allow user to select a file to export."""
        answer = QFileDialog.getSaveFileName(self, "Export to file", self._data_store.project().project_dir, "*.xlsx")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self.export_file(file_path)

    @busy_effect
    def export_file(self, file_path):
        """Export data from database into file."""
        if file_path.lower().endswith('datapackage.json'):
            pass
        elif file_path.lower().endswith('xlsx'):
            filename = os.path.split(file_path)[1]
            try:
                export_spine_database_to_xlsx(self.db_map, file_path)
                self.msg.emit("Excel file successfully exported.")
            except PermissionError:
                self.msg_error.emit("Unable to export to file <b>{0}</b>.<br/>"
                                    "Close the file in Excel and try again.".format(filename))
            except OSError:
                self.msg_error.emit("[OSError] Unable to export to file <b>{0}</b>".format(filename))
        else:
            self.msg_error.emit("Unsupported file format")

    @Slot(name="show_commit_session_dialog")
    def show_commit_session_dialog(self):
        """Query user for a commit message and commit changes to source database."""
        dialog = CommitDialog(self, self.database)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        self.commit_session(dialog.commit_msg)

    @busy_effect
    def commit_session(self, commit_msg):
        try:
            self.db_map.commit_session(commit_msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes committed successfully."
        self.msg.emit(msg)

    @Slot(name="rollback_session")
    def rollback_session(self):
        try:
            self.db_map.rollback_session()
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

    def init_models(self):
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_models()

    def init_object_tree_model(self):
        """Initialize object tree model."""
        root_item = self.object_tree_model.build_tree(self.database)
        # setup object tree view
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_object.header().hide()
        self.ui.treeView_object.expand(root_item.index())
        self.ui.treeView_object.resizeColumnToContents(0)

    def init_parameter_value_models(self):
        """Initialize parameter value models from source database."""
        self.object_parameter_value_proxy.setSourceModel(self.object_parameter_value_model)
        self.relationship_parameter_value_proxy.setSourceModel(self.relationship_parameter_value_model)
        self.object_parameter_value_model.init_model()
        self.relationship_parameter_value_model.init_model()

    def init_parameter_models(self):
        """Initialize parameter (definition) models from source database."""
        self.object_parameter_proxy.setSourceModel(self.object_parameter_model)
        self.relationship_parameter_proxy.setSourceModel(self.relationship_parameter_model)
        self.object_parameter_model.init_model()
        self.relationship_parameter_model.init_model()

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
        self.ui.tableView_object_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter_value.horizontalHeader().setResizeContentsPrecision(1)
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()

    def init_relationship_parameter_value_view(self):
        """Init the relationship parameter table view."""
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_proxy)
        h = self.relationship_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setResizeContentsPrecision(1)
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_object_parameter_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_object_parameter.setModel(self.object_parameter_proxy)
        h = self.object_parameter_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_object_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter.horizontalHeader().setResizeContentsPrecision(1)
        self.ui.tableView_object_parameter.resizeColumnsToContents()

    def init_relationship_parameter_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_relationship_parameter.setModel(self.relationship_parameter_proxy)
        h = self.relationship_parameter_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter.horizontalHeader().setResizeContentsPrecision(1)
        self.ui.tableView_relationship_parameter.resizeColumnsToContents()

    @Slot("QModelIndex", name="expand_next_leaf")
    def expand_next_leaf(self, index):
        """Check if index corresponds to a relationship and expand next."""
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
        self.expand_next(index)

    def expand_next(self, index):
        """Expand next occurrence of a relationship."""
        next_index = self.object_tree_model.next_relationship_index(index)
        if not next_index:
            return
        self.ui.treeView_object.setCurrentIndex(next_index)
        self.ui.treeView_object.scrollTo(next_index)
        self.ui.treeView_object.expand(next_index)

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_value_models(self, current, previous):
        """Filter parameter value tableViews whenever an item is selected in the treeView"""
        self.object_parameter_value_proxy.clear_filter()
        self.relationship_parameter_value_proxy.clear_filter()
        selected_type = current.data(Qt.UserRole)
        max_object_count = None
        if not selected_type == 'root':
            selected = current.data(Qt.UserRole+1)
            parent = current.parent().data(Qt.UserRole+1)
            grand_parent = current.parent().parent().data(Qt.UserRole+1)
            if selected_type == 'object_class':
                object_class_name = selected['name']
                object_class_id = selected['id']
                # TODO: get his query from other place. Maybe send a signal when relationship classes change?
                relationship_class_list = self.db_map.wide_relationship_class_list(object_class_id=object_class_id)
                relationship_class_name_list = [x.name for x in relationship_class_list]
                self.object_parameter_value_proxy.object_class_name = object_class_name
                self.relationship_parameter_value_proxy.relationship_class_name_list = relationship_class_name_list
                max_object_count = max(
                    [len(x.object_class_id_list.split(',')) for x in relationship_class_list], default=0)
            elif selected_type == 'object':
                object_class_name = parent['name']
                object_class_id = parent['id']
                object_name = selected['name']
                # TODO: get his query from other place. Maybe send a signal when relationship classes change?
                relationship_class_list = self.db_map.wide_relationship_class_list(object_class_id=object_class_id)
                relationship_class_name_list = [x.name for x in relationship_class_list]
                self.object_parameter_value_proxy.object_class_name = object_class_name
                self.object_parameter_value_proxy.object_name = object_name
                self.relationship_parameter_value_proxy.relationship_class_name_list = relationship_class_name_list
                self.relationship_parameter_value_proxy.object_name = object_name
                max_object_count = max(
                    [len(x.object_class_id_list.split(',')) for x in relationship_class_list], default=0)
            elif selected_type == 'relationship_class':
                object_name = parent['name']
                relationship_class_name = selected['name']
                object_class_id_list = selected['object_class_id_list'].split(',')
                self.relationship_parameter_value_proxy.relationship_class_name = relationship_class_name
                self.relationship_parameter_value_proxy.object_name = object_name
                max_object_count = len(object_class_id_list)
            elif selected_type == 'relationship':
                relationship_class_name = parent['name']
                object_name_list = selected['object_name_list'].split(',')
                self.relationship_parameter_value_proxy.relationship_class_name = relationship_class_name
                self.relationship_parameter_value_proxy.object_name_list = object_name_list
                max_object_count = len(object_name_list)
        if max_object_count:
            object_name_header = self.relationship_parameter_value_model.object_name_header
            for j in range(max_object_count, len(object_name_header)):
                self.relationship_parameter_value_proxy.reject_column(object_name_header[j])
        self.object_parameter_value_proxy.apply_filter()
        self.relationship_parameter_value_proxy.apply_filter()

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, current, previous):
        """Filter parameter tableViews whenever an item is selected in the treeView"""
        self.object_parameter_proxy.clear_filter()
        self.relationship_parameter_proxy.clear_filter()
        selected_type = current.data(Qt.UserRole)
        if not selected_type:
            return
        selected = current.data(Qt.UserRole+1)
        parent = current.parent().data(Qt.UserRole+1)
        if selected_type == 'object_class':
            object_class_name = selected['name']
            object_class_id = selected['id']
            # TODO: get his query from other place. Maybe send a signal when relationship classes change?
            relationship_class_list = self.db_map.wide_relationship_class_list(object_class_id=object_class_id)
            relationship_class_name_list = [x.name for x in relationship_class_list]
            self.object_parameter_proxy.object_class_name = object_class_name
            self.relationship_parameter_proxy.relationship_class_name_list = relationship_class_name_list
        elif selected_type == 'object':
            object_class_name = parent['name']
            object_class_id = parent['id']
            # TODO: get his query from other place. Maybe send a signal when relationship classes change?
            relationship_class_list = self.db_map.wide_relationship_class_list(object_class_id=object_class_id)
            relationship_class_name_list = [x.name for x in relationship_class_list]
            self.object_parameter_proxy.object_class_name = object_class_name
            self.relationship_parameter_proxy.relationship_class_name_list = relationship_class_name_list
        elif selected_type == 'relationship_class':
            relationship_class_name = selected['name']
            self.relationship_parameter_proxy.relationship_class_name = relationship_class_name
        elif selected_type == 'relationship':
            relationship_class_name = parent['name']
            self.relationship_parameter_proxy.relationship_class_name = relationship_class_name
        self.object_parameter_proxy.apply_filter()
        self.relationship_parameter_proxy.apply_filter()

    @Slot("QObject", name="apply_parameter_model_subfilter")
    def apply_parameter_model_subfilter(self, proxy_model, column, text_list):
        """Called when the tableview wants to trigger the subfilter."""
        header = proxy_model.sourceModel().horizontal_header_labels()
        proxy_model.remove_subrule(header[column])
        if text_list:
            kwargs = {header[column]: text_list}
            proxy_model.add_subrule(**kwargs)
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
        elif option == "Expand next":
            self.expand_next(index)
        elif option.startswith("Rename"):
            self.rename_item(index)
        elif option.startswith("Remove selected"):
            self.remove_items()
        elif option == "Add parameters":
            self.call_add_parameters(index)
        elif option == "Add parameter values":
            self.call_add_parameter_values(index)
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    def call_show_add_objects_form(self, index):
        class_id = index.data(Qt.UserRole+1)['id']
        self.show_add_objects_form(class_id=class_id)

    def call_show_add_relationship_classes_form(self, index):
        object_class_id = index.data(Qt.UserRole+1)['id']
        self.show_add_relationship_classes_form(object_class_id=object_class_id)

    def call_show_add_relationships_form(self, index):
        relationship_class = index.data(Qt.UserRole+1)
        object_ = index.parent().data(Qt.UserRole+1)
        object_class = index.parent().parent().data(Qt.UserRole+1)
        self.show_add_relationships_form(
            relationship_class_id=relationship_class['id'],
            object_id=object_['id'],
            object_class_id=object_class['id'])

    def call_add_parameters(self, tree_index):
        class_type = tree_index.data(Qt.UserRole)
        if class_type == 'object_class':
            self.add_object_parameters()
        elif class_type == 'relationship_class':
            self.add_relationship_parameters()

    def call_add_parameter_values(self, tree_index):
        entity_type = tree_index.data(Qt.UserRole)
        if entity_type == 'object':
            self.add_object_parameter_values()
        elif entity_type == 'relationship':
            self.add_relationship_parameter_values()

    @Slot(name="show_add_object_classes_form")
    def show_add_object_classes_form(self):
        """Show dialog to let user select preferences for new object classes."""
        dialog = AddObjectClassesDialog(self, self.db_map)
        dialog.confirmed.connect(self.add_object_classes)
        dialog.show()

    @Slot("QVariant", name="add_object_classes")
    def add_object_classes(self, object_class_args_list):
        """Insert new object classes."""
        try:
            object_classes = self.db_map.add_object_classes(*object_class_args_list)
            for object_class in object_classes:
                self.object_tree_model.add_object_class(object_class)
            msg = "Successfully added new object classes {}.".format(", ".join([x.name for x in object_classes]))
            self.msg.emit(msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @Slot(name="show_add_objects_form")
    def show_add_objects_form(self, class_id=None):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, self.db_map, class_id=class_id)
        dialog.confirmed.connect(self.add_objects)
        dialog.show()

    @Slot("QVariant", name="add_objects")
    def add_objects(self, object_args_list):
        """Insert new objects."""
        try:
            objects = self.db_map.add_objects(*object_args_list)
            for object_ in objects:
                self.object_tree_model.add_object(object_)
            msg = "Successfully added new objects {}.".format(", ".join([x.name for x in objects]))
            self.msg.emit(msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    def show_add_relationship_classes_form(self, object_class_id=None):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(self, self.db_map, object_class_one_id=object_class_id)
        dialog.confirmed.connect(self.add_relationship_classes)
        dialog.show()

    @Slot("QVariant", name="add_relationship_classes")
    def add_relationship_classes(self, wide_relationship_class_args_list):
        """Insert new relationship classes."""
        try:
            wide_relationship_classes = self.db_map.add_wide_relationship_classes(*wide_relationship_class_args_list)
            dim_count_list = list()
            for wide_relationship_class in wide_relationship_classes:
                self.object_tree_model.add_relationship_class(wide_relationship_class)
                dim_count_list.append(len(wide_relationship_class.object_class_id_list.split(',')))
            max_dim_count = max(dim_count_list)
            self.relationship_parameter_value_model.extend_object_name_header(max_dim_count)
            relationship_class_name_list = ", ".join([x.name for x in wide_relationship_classes])
            msg = "Successfully added new relationship classes {}.".format(relationship_class_name_list)
            self.msg.emit(msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @Slot(name="show_add_relationships_form")
    def show_add_relationships_form(self, relationship_class_id=None, object_id=None, object_class_id=None):
        """Show dialog to let user select preferences for new relationships."""
        dialog = AddRelationshipsDialog(
            self,
            self.db_map,
            relationship_class_id=relationship_class_id,
            object_id=object_id,
            object_class_id=object_class_id
        )
        dialog.confirmed.connect(self.add_relationships)
        dialog.show()

    @Slot("QVariant", name="add_relationships")
    def add_relationships(self, wide_relationship_args_list):
        """Insert new relationships."""
        try:
            wide_relationships = self.db_map.add_wide_relationships(*wide_relationship_args_list)
            for wide_relationship in wide_relationships:
                self.object_tree_model.add_relationship(wide_relationship)
            msg = "Successfully added new relationships {}.".format(", ".join([x.name for x in wide_relationships]))
            self.msg.emit(msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    def rename_item(self, renamed_index):
        """Rename item in the database and treeview"""
        renamed_item = self.object_tree_model.itemFromIndex(renamed_index)
        curr_name = renamed_item.text()
        answer = QInputDialog.getText(
            self, "Rename item", "Enter new name:", QLineEdit.Normal, curr_name)
        new_name = answer[0]
        if not new_name: # cancel clicked
            return
        if new_name == curr_name: # nothing to do here
            return
        renamed_type = renamed_item.data(Qt.UserRole)
        renamed = renamed_item.data(Qt.UserRole+1)
        try:
            if renamed_type == 'object_class':
                object_class = self.db_map.rename_object_class(renamed['id'], new_name)
                msg = "Successfully renamed object class to '{}'.".format(object_class.name)
            elif renamed_type == 'object':
                object_ = self.db_map.rename_object(renamed['id'], new_name)
                msg = "Successfully renamed object to '{}'.".format(object_.name)
            elif renamed_type == 'relationship_class':
                relationship_class = self.db_map.rename_relationship_class(renamed['id'], new_name)
                msg = "Successfully renamed relationship class to '{}'.".format(relationship_class.name)
            elif renamed_type == 'relationship':
                relationship = self.db_map.rename_relationship(renamed['id'], new_name)
                msg = "Successfully renamed relationship to '{}'.".format(relationship.name)
            else:
                return # should never happen
            self.msg.emit(msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        self.object_tree_model.rename_item(new_name, curr_name, renamed_type, renamed['id'])
        self.object_parameter_model.rename_item(new_name, curr_name, renamed_type)
        self.object_parameter_value_model.rename_item(new_name, curr_name, renamed_type)
        self.relationship_parameter_model.rename_item(new_name, curr_name, renamed_type)
        self.relationship_parameter_value_model.rename_item(new_name, curr_name, renamed_type)
        current = self.ui.treeView_object.currentIndex()
        self.filter_parameter_value_models(current, current)
        self.filter_parameter_models(current, current)

    @busy_effect
    def remove_items(self):
        """Remove all selected items from the object treeview."""
        selection = self.ui.treeView_object.selectionModel().selection()
        if not selection:
            return
        removed_id_dict = {}
        removed_name_dict = {}
        for index in selection.indexes():
            removed_type = index.data(Qt.UserRole)
            removed_item = index.data(Qt.UserRole+1)
            removed_id_dict.setdefault(removed_type, set()).add(removed_item['id'])
            removed_name_dict.setdefault(removed_type, set()).add(removed_item['name'])
        try:
            self.db_map.remove_items(**{k + "_ids": v for k, v in removed_id_dict.items()})
            for key, value in removed_id_dict.items():
                self.object_tree_model.remove_items(key, *value)
            for key, value in removed_name_dict.items():
                self.object_parameter_model.remove_items(key, *value)
                self.object_parameter_value_model.remove_items(key, *value)
                self.relationship_parameter_model.remove_items(key, *value)
                self.relationship_parameter_value_model.remove_items(key, *value)
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
        self.object_parameter_value_context_menu = ParameterContextMenu(self, global_pos, index)
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
        self.relationship_parameter_value_context_menu = ParameterContextMenu(self, global_pos, index)
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
        index = self.ui.tableView_object_parameter.indexAt(pos)
        global_pos = self.ui.tableView_object_parameter.viewport().mapToGlobal(pos)
        self.object_parameter_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.object_parameter_context_menu.get_action()
        if option == "Remove selected":
            self.remove_object_parameters()
        elif option == "Copy":
            self.ui.tableView_object_parameter.copy()
        elif option == "Paste":
            self.ui.tableView_object_parameter.paste(self.clipboard_text)
        self.object_parameter_context_menu.deleteLater()
        self.object_parameter_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_context_menu")
    def show_relationship_parameter_context_menu(self, pos):
        """Context menu for relationship parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_relationship_parameter.indexAt(pos)
        global_pos = self.ui.tableView_relationship_parameter.viewport().mapToGlobal(pos)
        self.relationship_parameter_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.relationship_parameter_context_menu.get_action()
        if option == "Remove selected":
            self.remove_relationship_parameters()
        elif option == "Copy":
            self.ui.tableView_relationship_parameter.copy()
        elif option == "Paste":
            self.ui.tableView_relationship_parameter.paste(self.clipboard_text)
        self.relationship_parameter_context_menu.deleteLater()
        self.relationship_parameter_context_menu = None

    @Slot("QWidget", name="update_parameter_value_in_model")
    def update_parameter_value_in_model(self, editor):
        """Update (object or relationship) parameter_value table with newly edited data."""
        new_value = editor.text()
        if not new_value:
            return
        index = editor.index()
        proxy_model = index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        source_model.setData(source_index, new_value)

    @Slot("QWidget", name="update_parameter_in_model")
    def update_parameter_in_model(self, editor):
        """Update parameter (object or relationship) with newly edited data.
        """
        new_value = editor.text()
        if not new_value:
            return
        index = editor.index()
        proxy_model = index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        parameter_name_column = source_model.horizontal_header_labels().index('parameter_name')
        if source_index.column() == parameter_name_column:
            curr_name = source_index.data(Qt.DisplayRole)
        if source_model.setData(source_index, new_value) and source_index.column() == parameter_name_column:
            new_name = source_index.data(Qt.DisplayRole)
            self.object_parameter_value_model.rename_item(new_name, curr_name, "parameter")
            self.relationship_parameter_value_model.rename_item(new_name, curr_name, "parameter")

    @Slot(name="remove_object_parameter_values")
    def remove_object_parameter_values(self):
        selection = self.ui.tableView_object_parameter_value.selectionModel().selection()
        self.remove_parameters(selection)

    @Slot(name="remove_relationship_parameter_values")
    def remove_relationship_parameter_values(self):
        selection = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        self.remove_parameters(selection)

    @Slot(name="remove_object_parameters")
    def remove_object_parameters(self):
        selection = self.ui.tableView_object_parameter.selectionModel().selection()
        self.remove_parameters(selection)

    @Slot(name="remove_relationship_parameters")
    def remove_relationship_parameters(self):
        selection = self.ui.tableView_relationship_parameter.selectionModel().selection()
        self.remove_parameters(selection)

    def remove_parameters(self, selection):
        indexes = selection.indexes()
        if not indexes:
            return
        proxy_model = indexes[0].model()
        source_model = proxy_model.sourceModel()
        proxy_row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            proxy_row_set.update(range(top, bottom + 1))
        source_row_set = {proxy_model.map_row_to_source(r) for r in proxy_row_set}
        parameter_value_ids = set()
        id_column = source_model.horizontal_header_labels().index('id')
        for source_row in source_row_set:
            if source_model.is_work_in_progress(source_row):
                continue
            source_index = source_model.index(source_row, id_column)
            parameter_value_ids.add(source_index.data(Qt.DisplayRole))
        try:
            self.db_map.remove_items(parameter_value_ids=parameter_value_ids)
            for source_row in reversed(list(source_row_set)):
                source_model.removeRows(source_row, 1)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @Slot(name="add_object_parameter_values")
    def add_object_parameter_values(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter value row if needed.
        """
        model = self.object_parameter_value_model
        proxy_index = self.ui.tableView_object_parameter_value.currentIndex()
        index = self.object_parameter_value_proxy.mapToSource(proxy_index)
        row = index.row()+1
        selection = self.ui.treeView_object.selectionModel().selection()
        some_inserted = False
        if selection:
            object_class_name_column = model.horizontal_header_labels().index('object_class_name')
            object_name_column = model.horizontal_header_labels().index('object_name')
            i = 0
            for index in selection.indexes():
                if index.data(Qt.UserRole) == 'object_class':
                    object_class_name = index.data(Qt.DisplayRole)
                    object_name = None
                elif index.data(Qt.UserRole) == 'object':
                    object_class_name = index.parent().data(Qt.DisplayRole)
                    object_name = index.data(Qt.DisplayRole)
                else:
                    continue
                model.insertRows(row + i, 1)
                model.set_work_in_progress(row + i, True)
                model.setData(model.index(row + i, object_class_name_column), object_class_name)
                model.setData(model.index(row + i, object_name_column), object_name)
                some_inserted = True
                i += 1
        if not some_inserted:
            model.insertRows(row, 1)
            model.set_work_in_progress(row, True)
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
        row = index.row()+1
        selection = self.ui.treeView_object.selectionModel().selection()
        some_inserted = False
        if selection:
            relationship_class_name_column = model.horizontal_header_labels().index('relationship_class_name')
            object_name_1_column = model.horizontal_header_labels().index('object_name_1')
            i = 0
            for index in selection.indexes():
                if index.data(Qt.UserRole) == 'relationship_class':
                    selected_object_class_name = index.parent().parent().data(Qt.DisplayRole)
                    object_name = index.parent().data(Qt.DisplayRole)
                    relationship_class_name = index.data(Qt.DisplayRole)
                    object_class_name_list = index.data(Qt.UserRole+1)["object_class_name_list"].split(",")
                    object_name_list = list()
                    for object_class_name in object_class_name_list:
                        if object_class_name == selected_object_class_name:
                            object_name_list.append(object_name)
                        else:
                            object_name_list.append(None)
                elif index.data(Qt.UserRole) == 'relationship':
                    relationship_class_name = index.parent().data(Qt.DisplayRole)
                    object_name_list = index.data(Qt.UserRole+1)["object_name_list"].split(",")
                else:
                    continue
                model.insertRows(row + i, 1)
                model.set_work_in_progress(row + i, True)
                model.setData(model.index(row + i, relationship_class_name_column), relationship_class_name)
                for j, object_name in enumerate(object_name_list):
                    model.setData(model.index(row + i, object_name_1_column + j), object_name)
                some_inserted = True
                i += 1
        if not some_inserted:
            model.insertRows(row, 1)
            model.set_work_in_progress(row, True)
        self.ui.tabWidget_relationship.setCurrentIndex(0)
        self.relationship_parameter_value_proxy.apply_filter()

    @Slot(name="add_object_parameters")
    def add_object_parameters(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter value row if needed.
        """
        model = self.object_parameter_model
        proxy_index = self.ui.tableView_object_parameter.currentIndex()
        index = self.object_parameter_proxy.mapToSource(proxy_index)
        row = index.row()+1
        selection = self.ui.treeView_object.selectionModel().selection()
        some_inserted = False
        if selection:
            object_class_name_column = model.horizontal_header_labels().index('object_class_name')
            i = 0
            for index in selection.indexes():
                if index.data(Qt.UserRole) == 'object_class':
                    object_class_name = index.data(Qt.DisplayRole)
                else:
                    continue
                model.insertRows(row + i, 1)
                model.set_work_in_progress(row + i, True)
                model.setData(model.index(row + i, object_class_name_column), object_class_name)
                some_inserted = True
                i += 1
        if not some_inserted:
            model.insertRows(row, 1)
            model.set_work_in_progress(row, True)
        self.ui.tabWidget_object.setCurrentIndex(1)
        self.object_parameter_proxy.apply_filter()

    @Slot(name="add_relationship_parameters")
    def add_relationship_parameters(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter row if needed.
        """
        model = self.relationship_parameter_model
        proxy_index = self.ui.tableView_relationship_parameter.currentIndex()
        index = self.relationship_parameter_proxy.mapToSource(proxy_index)
        row = index.row()+1
        selection = self.ui.treeView_object.selectionModel().selection()
        some_inserted = False
        if selection:
            relationship_class_name_column = model.horizontal_header_labels().index('relationship_class_name')
            i = 0
            for index in selection.indexes():
                if index.data(Qt.UserRole) == 'relationship_class':
                    relationship_class_name = index.data(Qt.DisplayRole)
                else:
                    continue
                model.insertRows(row + i, 1)
                model.set_work_in_progress(row + i, True)
                model.setData(model.index(row + i, relationship_class_name_column), relationship_class_name)
                some_inserted = True
                i += 1
        if not some_inserted:
            model.insertRows(row, 1)
            model.set_work_in_progress(row, True)
        self.ui.tabWidget_relationship.setCurrentIndex(1)
        self.relationship_parameter_proxy.apply_filter()

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("dataStoreWidget/windowSize")
        window_pos = self.qsettings.value("dataStoreWidget/windowPosition")
        splitter_tree_parameter_state = self.qsettings.value("dataStoreWidget/splitterTreeParameterState")
        window_maximized = self.qsettings.value("dataStoreWidget/windowMaximized", defaultValue='false')  # returns str
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

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue("dataStoreWidget/splitterTreeParameterState", self.ui.splitter_tree_parameter.saveState())
        self.qsettings.setValue("dataStoreWidget/windowSize", self.size())
        self.qsettings.setValue("dataStoreWidget/windowPosition", self.pos())
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("dataStoreWidget/windowMaximized", True)
        else:
            self.qsettings.setValue("dataStoreWidget/windowMaximized", False)
        self.db_map.close()
        if event:
            event.accept()
