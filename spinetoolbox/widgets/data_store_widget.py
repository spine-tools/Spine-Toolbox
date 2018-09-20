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
    RelationshipParameterModel, RelationshipParameterValueModel, CustomSortFilterProxyModel
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
        self.object_parameter_value_proxy = CustomSortFilterProxyModel(self)
        self.relationship_parameter_value_model = RelationshipParameterValueModel(self)
        self.relationship_parameter_value_proxy = CustomSortFilterProxyModel(self)
        # Parameter (definition) models
        self.object_parameter_model = ObjectParameterModel(self)
        self.object_parameter_proxy = CustomSortFilterProxyModel(self)
        self.relationship_parameter_model = RelationshipParameterModel(self)
        self.relationship_parameter_proxy = CustomSortFilterProxyModel(self)
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
        self.ui.actionImport.triggered.connect(self.import_file)
        self.ui.actionExport.triggered.connect(self.export_file)
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
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

    @Slot(name="import_file")
    def import_file(self):
        """Import data from file into current database."""
        answer = QFileDialog.getOpenFileName(
            self, "Select file to import", self._data_store.project().project_dir, "*.*")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
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
            except:
                self.msg_error.emit("Unable to import Excel file")

    @Slot(name="export_file")
    def export_file(self):
        """export data from database into file."""
        answer = QFileDialog.getSaveFileName(self, "Export to file", self._data_store.project().project_dir, "*.xlsx")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
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

    def init_models(self):
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_models()
        # clear filters
        self.object_parameter_value_proxy.clear_filter()
        self.relationship_parameter_value_proxy.clear_filter()

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
        self.object_parameter_value_model.init_model()
        self.object_parameter_value_proxy.setSourceModel(self.object_parameter_value_model)
        self.relationship_parameter_value_model.init_model()
        self.relationship_parameter_value_proxy.setSourceModel(self.relationship_parameter_value_model)

    def init_parameter_models(self):
        """Initialize parameter (definition) models from source database."""
        self.object_parameter_model.init_model()
        self.object_parameter_proxy.setSourceModel(self.object_parameter_model)
        self.relationship_parameter_model.init_model()
        self.relationship_parameter_proxy.setSourceModel(self.relationship_parameter_model)

    def init_views(self):
        self.init_object_parameter_value_view()
        self.init_relationship_parameter_value_view()
        self.init_object_parameter_view()
        self.init_relationship_parameter_view()

    def init_object_parameter_value_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_object_parameter_value.setModel(self.object_parameter_value_proxy)
        h = self.object_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('parameter_value_id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter_value.horizontalHeader().setResizeContentsPrecision(1)
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()

    def init_relationship_parameter_value_view(self):
        """Init the relationship parameter table view."""
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_proxy)
        h = self.relationship_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('parameter_value_id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setResizeContentsPrecision(1)
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_object_parameter_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_object_parameter.setModel(self.object_parameter_proxy)
        h = self.object_parameter_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter.horizontalHeader().hideSection(h('parameter_id'))
        self.ui.tableView_object_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter.horizontalHeader().setResizeContentsPrecision(1)
        self.ui.tableView_object_parameter.resizeColumnsToContents()

    def init_relationship_parameter_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_relationship_parameter.setModel(self.relationship_parameter_proxy)
        h = self.relationship_parameter_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter.horizontalHeader().hideSection(h('parameter_id'))
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
        """Filer parameter value tableViews whenever an item is selected in the treeView"""
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
                relationship_class_list = self.db_map.wide_relationship_class_list(object_class_id=object_class_id)
                relationship_class_name = [x.name for x in relationship_class_list]
                self.object_parameter_value_proxy.add_rule(object_class_name=object_class_name)
                self.relationship_parameter_value_proxy.add_rule(relationship_class_name=relationship_class_name)
                max_object_count = max(
                    [len(x.object_class_id_list.split(',')) for x in relationship_class_list], default=0)
            elif selected_type == 'object':
                object_class_name = parent['name']
                object_class_id = parent['id']
                object_name = selected['name']
                relationship_class_list = self.db_map.wide_relationship_class_list(object_class_id=object_class_id)
                relationship_class_name = [x.name for x in relationship_class_list]
                object_name_header = self.relationship_parameter_value_model.object_name_header
                object_name_dict = {x: object_name for x in object_name_header}
                self.object_parameter_value_proxy.add_rule(object_class_name=object_class_name)
                self.object_parameter_value_proxy.add_rule(object_name=object_name)
                self.relationship_parameter_value_proxy.add_rule(relationship_class_name=relationship_class_name)
                self.relationship_parameter_value_proxy.add_rule(**object_name_dict)
                max_object_count = max(
                    [len(x.object_class_id_list.split(',')) for x in relationship_class_list], default=0)
            elif selected_type == 'relationship_class':
                selected_object_class_name = grand_parent['name']
                object_name = parent['name']
                relationship_class_name = selected['name']
                object_class_name_list = selected['object_class_name_list'].split(',')
                object_name_dict = {}
                object_name_header = self.relationship_parameter_value_model.object_name_header
                for i, object_class_name in enumerate(object_class_name_list):
                    if object_class_name == selected_object_class_name:
                        object_name_dict[object_name_header[i]] = object_name
                self.relationship_parameter_value_proxy.add_rule(relationship_class_name=relationship_class_name)
                self.relationship_parameter_value_proxy.add_rule(**object_name_dict)
                max_object_count = len(object_class_name_list)
            elif selected_type == 'relationship':
                relationship_class_name = parent['name']
                object_name_list = selected['object_name_list'].split(',')
                self.relationship_parameter_value_proxy.add_rule(relationship_class_name=relationship_class_name)
                object_name_header = self.relationship_parameter_value_model.object_name_header
                for i, x in enumerate(object_name_header):
                    try:
                        object_name = object_name_list[i]
                        kwargs = {x: object_name}
                        self.relationship_parameter_value_proxy.add_rule(**kwargs)
                    except IndexError:
                        break
                max_object_count = len(object_name_list)
        if max_object_count:
            object_name_header = self.relationship_parameter_value_model.object_name_header
            for j in range(max_object_count, len(object_name_header)):
                self.relationship_parameter_value_proxy.reject_column(object_name_header[j])
        self.object_parameter_value_proxy.apply_filter()
        self.relationship_parameter_value_proxy.apply_filter()
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

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
            relationship_class_list = self.db_map.wide_relationship_class_list(object_class_id=object_class_id)
            relationship_class_name = [x.name for x in relationship_class_list]
            self.object_parameter_proxy.add_rule(object_class_name=object_class_name)
            self.relationship_parameter_proxy.add_rule(relationship_class_name=relationship_class_name)
        elif selected_type == 'object':
            object_class_name = parent['name']
            object_class_id = parent['id']
            relationship_class_list = self.db_map.wide_relationship_class_list(object_class_id=object_class_id)
            relationship_class_name = [x.name for x in relationship_class_list]
            self.object_parameter_proxy.add_rule(object_class_name=object_class_name)
            self.relationship_parameter_proxy.add_rule(relationship_class_name=relationship_class_name)
        elif selected_type == 'relationship_class':
            relationship_class_name = selected['name']
            self.relationship_parameter_proxy.add_rule(relationship_class_name=relationship_class_name)
        elif selected_type == 'relationship':
            relationship_class_name = parent['name']
            self.relationship_parameter_proxy.add_rule(relationship_class_name=relationship_class_name)
        self.object_parameter_proxy.apply_filter()
        self.relationship_parameter_proxy.apply_filter()
        self.ui.tableView_object_parameter.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter.resizeColumnsToContents()

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
        self.object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, index)#
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
        for object_class_args in object_class_args_list:
            try:
                object_class = self.db_map.add_object_class(**object_class_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_object_class(object_class._asdict())
            msg = "Successfully added new object class '{}'.".format(object_class.name)
            self.msg.emit(msg)

    @Slot(name="show_add_objects_form")
    def show_add_objects_form(self, class_id=None):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, self.db_map, class_id=class_id)
        dialog.confirmed.connect(self.add_objects)
        dialog.show()

    @Slot("QVariant", name="add_objects")
    def add_objects(self, object_args_list):
        """Insert new objects."""
        for object_args in object_args_list:
            try:
                object_ = self.db_map.add_object(**object_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_object(object_._asdict())
            msg = "Successfully added new object '{}'.".format(object_.name)
            self.msg.emit(msg)

    def show_add_relationship_classes_form(self, object_class_id=None):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(self, self.db_map, object_class_one_id=object_class_id)
        dialog.confirmed.connect(self.add_relationship_classes)
        dialog.show()

    @Slot("QVariant", name="add_relationship_classes")
    def add_relationship_classes(self, wide_relationship_class_args_list):
        """Insert new relationship classes."""
        for wide_relationship_class_args in wide_relationship_class_args_list:
            try:
                wide_relationship_class = self.db_map.add_wide_relationship_class(**wide_relationship_class_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_relationship_class(wide_relationship_class._asdict())
            dim_count = len(wide_relationship_class.object_class_id_list.split(','))
            object_name_header = self.relationship_parameter_value_model.object_name_header
            max_dim_count = len(object_name_header)
            ext_object_name_header = ["object_name_" + str(i+1) for i in range(max_dim_count, dim_count)]
            if ext_object_name_header:
                header = self.relationship_parameter_value_model.horizontal_header_labels()
                section = header.index(object_name_header[-1]) + 1
                self.relationship_parameter_value_model.insertColumns(section, len(ext_object_name_header))
                self.relationship_parameter_value_model.insert_horizontal_header_labels(
                    section, ext_object_name_header)
                object_name_header.extend(ext_object_name_header)
            msg = "Successfully added new relationship class '{}'.".format(wide_relationship_class.name)
            self.msg.emit(msg)

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
        for wide_relationship_args in wide_relationship_args_list:
            try:
                wide_relationship = self.db_map.add_wide_relationship(**wide_relationship_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_relationship(wide_relationship._asdict())
            msg = "Successfully added new relationship '{}'.".format(wide_relationship_args['name'])
            self.msg.emit(msg)

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
        self.init_parameter_value_models()
        self.init_parameter_models()

    def remove_items(self):
        """Remove all selected items from the object treeview."""
        selection = self.ui.treeView_object.selectionModel().selection()
        if not selection:
            return
        for index in reversed(selection.indexes()):
            self.remove_item(index, refresh_parameter_views=False)
        self.init_parameter_value_models()
        self.init_parameter_models()

    def remove_item(self, removed_index, refresh_parameter_views=False):
        """Remove item from the treeview"""
        removed_item = self.object_tree_model.itemFromIndex(removed_index)
        removed_type = removed_item.data(Qt.UserRole)
        removed = removed_item.data(Qt.UserRole+1)
        removed_id = removed['id']
        try:
            if removed_type == 'object_class':
                self.db_map.remove_object_class(id=removed_id)
                msg = "Successfully removed object class."
            elif removed_type == 'object':
                self.db_map.remove_object(id=removed_id)
                msg = "Successfully removed object."
            elif removed_type.endswith('relationship_class'):
                self.db_map.remove_relationship_class(id=removed_id)
                msg = "Successfully removed relationship class."
            elif removed_type == 'relationship':
                self.db_map.remove_relationship(id=removed_id)
                msg = "Successfully removed relationship."
            else:
                return # should never happen
            self.msg.emit(msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        self.object_tree_model.remove_item(removed_type, removed_id)
        if not refresh_parameter_views:
            return
        self.init_parameter_value_models()
        self.init_parameter_models()

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
        source_model.setData(source_index, new_value)

    @Slot(name="remove_object_parameter_values")
    def remove_object_parameter_values(self):
        selection = self.ui.tableView_object_parameter_value.selectionModel().selection()
        row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_set.update(range(top, bottom+1))
        for row in reversed(list(row_set)):
            proxy_index = self.object_parameter_value_proxy.index(row, 0)
            self.remove_single_parameter_value(proxy_index)

    @Slot(name="remove_object_parameters")
    def remove_object_parameters(self):
        selection = self.ui.tableView_object_parameter.selectionModel().selection()
        row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_set.update(range(top, bottom+1))
        for row in reversed(list(row_set)):
            proxy_index = self.object_parameter_proxy.index(row, 0)
            self.remove_single_parameter(proxy_index)

    @Slot(name="remove_relationship_parameter_values")
    def remove_relationship_parameter_values(self):
        selection = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_set.update(range(top, bottom+1))
        for row in reversed(list(row_set)):
            proxy_index = self.relationship_parameter_value_proxy.index(row, 0)
            self.remove_single_parameter_value(proxy_index)

    @Slot(name="remove_relationship_parameters")
    def remove_relationship_parameters(self):
        selection = self.ui.tableView_relationship_parameter.selectionModel().selection()
        row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_set.update(range(top, bottom+1))
        for row in reversed(list(row_set)):
            proxy_index = self.relationship_parameter_proxy.index(row, 0)
            self.remove_single_parameter(proxy_index)

    def remove_single_parameter_value(self, proxy_index):
        """Remove row from (object or relationship) parameter_value table.
        If successful, also remove row from model"""
        proxy_model = proxy_index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(proxy_index)
        id_column = source_model.horizontal_header_labels().index('parameter_value_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_value_id = sibling.data()
        # Only attempt to remove parameter value from db if it's not a 'work-in-progress'
        if parameter_value_id:
            try:
                self.db_map.remove_parameter_value(parameter_value_id)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                return
        source_model.removeRows(source_index.row(), 1)

    def remove_single_parameter(self, proxy_index):
        """Remove row from (object or relationship) parameter table.
        If succesful, also remove row from model"""
        proxy_model = proxy_index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(proxy_index)
        id_column = source_model.horizontal_header_labels().index('parameter_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_id = sibling.data()
        # Only attempt to remove parameter from db if it's not a 'work-in-progress'
        if parameter_id:
            try:
                self.db_map.remove_parameter(parameter_id)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                return
        source_model.removeRows(source_index.row(), 1)
        self.init_parameter_value_models()

    @Slot(name="add_parameter_values")
    def add_parameter_values(self):
        """Sweep object treeview selection. For each object and relationship in the selection,
        add a parameter value row."""
        selection = self.ui.treeView_object.selectionModel().selection()

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
