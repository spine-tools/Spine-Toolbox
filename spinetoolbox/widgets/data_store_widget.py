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
from widgets.custom_menus import ObjectTreeContextMenu, ParameterContextMenu, QSpinBoxMenu
from widgets.custom_delegates import ObjectParameterValueDelegate, ObjectParameterDelegate, \
    RelationshipParameterValueDelegate, RelationshipParameterDelegate
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, AddRelationshipClassesDialog, \
    AddRelationshipsDialog, CommitDialog
from models import ObjectTreeModel, ParameterTableModel, CustomSortFilterProxyModel
from excel_import_export import import_xlsx_to_db, export_spine_database_to_xlsx
from datapackage_import_export import import_datapackage


class DataStoreForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        data_store (DataStore): The DataStore instance that owns this form
        mapping (DatabaseMapping): The object relational mapping
        database (str): The database name
    """
    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, data_store, mapping, database):
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
        self.ui.actionPaste_into_new_rows.setIcon(QIcon.fromTheme("edit-paste"))
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Set up status bar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Class attributes
        # DB mapping
        self.mapping = mapping
        self.database = database
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self)
        # Parameter value models
        self.object_parameter_value_model = ParameterTableModel(self)
        self.object_parameter_value_proxy = CustomSortFilterProxyModel(self)
        self.relationship_parameter_value_model = ParameterTableModel(self)
        self.relationship_parameter_value_proxy = CustomSortFilterProxyModel(self)
        # Parameter (definition) models
        self.object_parameter_model = ParameterTableModel(self)
        self.object_parameter_proxy = CustomSortFilterProxyModel(self)
        self.relationship_parameter_model = ParameterTableModel(self)
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
        logging.debug("Elapsed = {}".format(toc - tic))

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
        #Setup Button menus
        spin_box_menu = QSpinBoxMenu(self, value=10, prefix="Add ", suffix=" rows")
        spin_box_menu.data_committed.connect(self.add_object_parameter_values)
        self.ui.toolButton_add_object_parameter_values.setMenu(spin_box_menu)
        spin_box_menu = QSpinBoxMenu(self, value=10, prefix="Add ", suffix=" rows")
        spin_box_menu.data_committed.connect(self.add_relationship_parameter_values)
        self.ui.toolButton_add_relationship_parameter_values.setMenu(spin_box_menu)
        spin_box_menu = QSpinBoxMenu(self, value=10, prefix="Add ", suffix=" rows")
        spin_box_menu.data_committed.connect(self.add_object_parameters)
        self.ui.toolButton_add_object_parameters.setMenu(spin_box_menu)
        spin_box_menu = QSpinBoxMenu(self, value=10, prefix="Add ", suffix=" rows")
        spin_box_menu.data_committed.connect(self.add_relationship_parameters)
        self.ui.toolButton_add_relationship_parameters.setMenu(spin_box_menu)

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
        self.ui.actionCommit.triggered.connect(self.commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionAdd_object_classes.triggered.connect(self.add_object_classes)
        self.ui.actionAdd_objects.triggered.connect(self.add_objects)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.add_relationship_classes)
        self.ui.actionAdd_relationships.triggered.connect(self.add_relationships)
        self.ui.actionAdd_object_parameters.triggered.connect(self.add_object_parameters)
        self.ui.actionAdd_object_parameter_values.triggered.connect(self.add_object_parameter_values)
        self.ui.actionAdd_relationship_parameters.triggered.connect(self.add_relationship_parameters)
        self.ui.actionAdd_relationship_parameter_values.triggered.connect(self.add_relationship_parameter_values)
        self.ui.actionRemove_object_parameters.triggered.connect(self.remove_object_parameters)
        self.ui.actionRemove_object_parameter_values.triggered.connect(self.remove_object_parameter_values)
        self.ui.actionRemove_relationship_parameters.triggered.connect(self.remove_relationship_parameters)
        self.ui.actionRemove_relationship_parameter_values.triggered.connect(self.remove_relationship_parameter_values)
        # Copy and paste
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionPaste_into_new_rows.triggered.connect(self.paste_into_new_rows)
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
        # Data from editor committed
        # Parameter value tables
        self.ui.tableView_object_parameter_value.itemDelegate().commitData.\
            connect(self.update_parameter_value_in_model)
        self.ui.tableView_relationship_parameter_value.itemDelegate().commitData.\
            connect(self.update_parameter_value_in_model)
        # Parameter tables
        self.ui.tableView_object_parameter.itemDelegate().commitData.\
            connect(self.update_parameter_in_model)
        self.ui.tableView_relationship_parameter.itemDelegate().commitData.\
            connect(self.update_parameter_in_model)
        # Model data changed
        self.object_parameter_value_model.dataChanged.connect(self.object_parameter_value_data_changed)
        self.relationship_parameter_value_model.dataChanged.connect(self.relationship_parameter_value_data_changed)
        self.object_parameter_model.dataChanged.connect(self.object_parameter_data_changed)
        self.relationship_parameter_model.dataChanged.connect(self.relationship_parameter_data_changed)
        # Model rows inserted
        self.object_parameter_value_model.rowsInserted.connect(self.setup_object_parameter_value_rows)
        self.relationship_parameter_value_model.rowsInserted.connect(self.setup_relationship_parameter_value_rows)
        self.object_parameter_model.rowsInserted.connect(self.setup_object_parameter_rows)
        self.relationship_parameter_model.rowsInserted.connect(self.setup_relationship_parameter_rows)
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
        except AttributeError:
            self.msg.emit("Cannot copy from widget ({})".format(focus_widget.objectName()))

    @Slot(name="paste")
    def paste(self):
        """Paste data from clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.paste(self.clipboard_text)
        except AttributeError:
            self.msg.emit("Cannot paste to widget ({})".format(focus_widget.objectName()))

    @Slot(name="paste_into_new_rows")
    def paste_into_new_rows(self):
        """Paste data from clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.paste(self.clipboard_text, into_new_rows=True)
        except AttributeError:
            self.msg.emit("Cannot paste to widget ({})".format(focus_widget.objectName()))

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
        self.ui.actionPaste_into_new_rows.setEnabled(on)

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
                insert_log, error_log = import_xlsx_to_db(self.mapping, file_path)
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
                export_spine_database_to_xlsx(self.mapping, file_path)
                self.msg.emit("Excel file successfully exported.")
            except PermissionError:
                self.msg_error.emit("Unable to export to file <b>{0}</b>.<br/>"
                                    "Close the file in Excel and try again.".format(filename))
            except OSError:
                self.msg_error.emit("[OSError] Unable to export to file <b>{0}</b>".format(filename))
        else:
            self.msg_error.emit("Unsupported file format")

    @Slot(name="commit_session")
    def commit_session(self):
        """Query user for a commit message and commit changes to source database."""
        dialog = CommitDialog(self, self.database)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        try:
            self.mapping.commit_session(dialog.commit_msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes committed successfully."
        self.msg.emit(msg)

    @Slot(name="rollback_session")
    def rollback_session(self):
        try:
            self.mapping.rollback_session()
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
        # Object
        object_parameter_value_list = self.mapping.object_parameter_value_list()
        header = object_parameter_value_list.column_descriptions
        object_parameter_value_data = [list(row._asdict().values()) for row in object_parameter_value_list]
        self.object_parameter_value_model.set_horizontal_header_labels([column['name'] for column in header])
        self.object_parameter_value_model.reset_model(object_parameter_value_data)
        self.object_parameter_value_model.make_columns_fixed(
            'object_class_name', 'object_name', 'parameter_name', 'parameter_value_id')
        self.object_parameter_value_proxy.setSourceModel(self.object_parameter_value_model)
        # Relationship
        relationship_parameter_value_list = self.mapping.relationship_parameter_value_list()
        # Determine the lenght of the largest 'object_name_list'
        max_object_name_list_len = max([len(x.object_name_list.split(',')) for x in relationship_parameter_value_list])
        print(max_object_name_list_len)
        header = [x['name'] for x in relationship_parameter_value_list.column_descriptions]
        object_name_list_index = header.index("object_name_list")
        del header[object_name_list_index]
        for i in range(max_object_name_list_len):
            header.insert(object_name_list_index, "object_name")
        self.relationship_parameter_value_model.set_horizontal_header_labels(header)
        relationship_parameter_value_data = [list(row._asdict().values()) for row in relationship_parameter_value_list]
        self.relationship_parameter_value_model.reset_model(relationship_parameter_value_data)
        self.relationship_parameter_value_model.make_columns_fixed(
            'relationship_class_name', 'object_name', 'parameter_name', 'parameter_value_id')
        self.relationship_parameter_value_proxy.setSourceModel(self.relationship_parameter_value_model)

    def init_parameter_models(self):
        """Initialize parameter (definition) models from source database."""
        # Object
        object_parameter_list = self.mapping.object_parameter_list()
        header = object_parameter_list.column_descriptions
        self.object_parameter_model.set_horizontal_header_labels([column['name'] for column in header])
        object_parameter_data = [list(row._asdict().values()) for row in object_parameter_list]
        self.object_parameter_model.reset_model(object_parameter_data)
        self.object_parameter_model.make_columns_fixed('object_class_name')
        self.object_parameter_proxy.setSourceModel(self.object_parameter_model)
        # Relationship
        relationship_parameter_list = self.mapping.relationship_parameter_list()
        header = relationship_parameter_list.column_descriptions
        self.relationship_parameter_model.set_horizontal_header_labels([column['name'] for column in header])
        relationship_parameter_data = [list(row._asdict().values()) for row in relationship_parameter_list]
        self.relationship_parameter_model.reset_model(relationship_parameter_data)
        self.relationship_parameter_model.make_columns_fixed('relationship_class_name', 'object_class_name_list')
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
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()

    def init_relationship_parameter_value_view(self):
        """Init the relationship parameter table view."""
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_proxy)
        h = self.relationship_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('parameter_value_id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_object_parameter_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_object_parameter.setModel(self.object_parameter_proxy)
        h = self.object_parameter_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter.horizontalHeader().hideSection(h('parameter_id'))
        self.ui.tableView_object_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter.resizeColumnsToContents()

    def init_relationship_parameter_view(self):
        """Init the object parameter table view."""
        self.ui.tableView_relationship_parameter.setModel(self.relationship_parameter_proxy)
        h = self.relationship_parameter_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter.horizontalHeader().hideSection(h('parameter_id'))
        self.ui.tableView_relationship_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter.verticalHeader().setDefaultSectionSize(self.default_row_height)
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
        """Populate tableViews whenever an object item is selected in the treeView"""
        self.object_parameter_value_proxy.clear_filter()
        self.relationship_parameter_value_proxy.clear_filter()
        selected_type = current.data(Qt.UserRole)
        if not selected_type == 'root':
            selected = current.data(Qt.UserRole+1)
            parent = current.parent().data(Qt.UserRole+1)
            if selected_type == 'object_class':
                object_class_name = selected['name']
                object_class_id = selected['id']
                relationship_class_list = self.mapping.wide_relationship_class_list(object_class_id=object_class_id)
                relationship_class_name = [x.name for x in relationship_class_list]
                self.object_parameter_value_proxy.add_rule(object_class_name=object_class_name)
                self.relationship_parameter_value_proxy.add_rule(relationship_class_name=relationship_class_name)
            elif selected_type == 'object':
                object_class_name = parent['name']
                object_class_id = parent['id']
                object_name = selected['name']
                object_id = selected['id']
                relationship_class_list = self.mapping.wide_relationship_class_list(object_class_id=object_class_id)
                relationship_class_name = [x.name for x in relationship_class_list]
                relationship_list = self.mapping.wide_relationship_list(object_id=object_id)
                object_name_list = [x.object_name_list for x in relationship_list]
                self.object_parameter_value_proxy.add_rule(
                    object_class_name=object_class_name, object_name=object_name)
                self.relationship_parameter_value_proxy.add_rule(
                    relationship_class_name=relationship_class_name, object_name_list=object_name_list)
            elif selected_type == 'relationship_class':
                relationship_class_name = selected['name']
                self.relationship_parameter_value_proxy.add_rule(relationship_class_name=relationship_class_name)
            elif selected_type == 'relationship':
                relationship_class_name = parent['name']
                object_name_list = selected['object_name_list']
                self.relationship_parameter_value_proxy.add_rule(
                    relationship_class_name=relationship_class_name, object_name_list=object_name_list)
        self.object_parameter_value_proxy.apply_filter()
        self.relationship_parameter_value_proxy.apply_filter()
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, current, previous):
        """Populate tableViews whenever an object item is selected in the treeView"""
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
            relationship_class_list = self.mapping.wide_relationship_class_list(object_class_id=object_class_id)
            relationship_class_name = [x.name for x in relationship_class_list]
            self.object_parameter_proxy.add_rule(object_class_name=object_class_name)
            self.relationship_parameter_proxy.add_rule(relationship_class_name=relationship_class_name)
        elif selected_type == 'object':
            object_class_name = parent['name']
            object_class_id = parent['id']
            relationship_class_list = self.mapping.wide_relationship_class_list(object_class_id=object_class_id)
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
        if option == "Add object classes":
            self.add_object_classes()
        elif option == "Add objects":
            self.call_add_objects(index)
        elif option == "Add relationship classes":
            self.call_add_relationship_classes(index)
        elif option == "Add relationships":
            self.call_add_relationships(index)
        elif option == "Expand next":
            self.expand_next(index)
        elif option.startswith("Rename"):
            self.rename_item(index)
        elif option.startswith("Remove"):
            self.remove_item(index)
        elif option == "Add parameters":
            self.call_add_parameters(index)
        elif option == "Add parameter values":
            self.call_add_parameter_values(index)
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    def call_add_objects(self, index):
        class_id = index.data(Qt.UserRole+1)['id']
        self.add_objects(class_id=class_id)

    def call_add_relationship_classes(self, index):
        object_class_id = index.data(Qt.UserRole+1)['id']
        self.add_relationship_classes(object_class_id=object_class_id)

    def call_add_relationships(self, index):
        relationship_class = index.data(Qt.UserRole+1)
        object_ = index.parent().data(Qt.UserRole+1)
        object_class = index.parent().parent().data(Qt.UserRole+1)
        self.add_relationships(
            relationship_class_id=relationship_class['id'],
            object_id=object_['id'],
            object_class_id=object_class['id']
        )

    def call_add_parameters(self, tree_index):
        class_type = tree_index.data(Qt.UserRole)
        if class_type == 'object_class':
            self.add_object_parameters(count=1)
        elif class_type == 'relationship_class':
            self.add_relationship_parameters(count=1)

    def call_add_parameter_values(self, tree_index):
        entity_type = tree_index.data(Qt.UserRole)
        if entity_type == 'object':
            self.add_object_parameter_values(count=1)
        elif entity_type == 'relationship':
            self.add_relationship_parameter_values(count=1)

    @Slot(name="add_object_classes")
    def add_object_classes(self):
        """Insert new object classes."""
        dialog = AddObjectClassesDialog(self, self.mapping)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for object_class_args in dialog.object_class_args_list:
            try:
                object_class = self.mapping.add_object_class(**object_class_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_object_class(object_class.__dict__)
            msg = "Successfully added new object class '{}'.".format(object_class.name)
            self.msg.emit(msg)

    @Slot(name="add_objects")
    def add_objects(self, class_id=None):
        """Insert new objects."""
        dialog = AddObjectsDialog(self, self.mapping, class_id=class_id)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for object_args in dialog.object_args_list:
            try:
                object_ = self.mapping.add_object(**object_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_object(object_.__dict__)
            msg = "Successfully added new object '{}'.".format(object_.name)
            self.msg.emit(msg)

    @Slot(name="add_relationship_classes")
    def add_relationship_classes(self, object_class_id=None):
        """Insert new relationship class."""
        dialog = AddRelationshipClassesDialog(self, self.mapping,
            object_class_one_id=object_class_id)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for wide_relationship_class_args in dialog.wide_relationship_class_args_list:
            try:
                wide_relationship_class = self.mapping.add_wide_relationship_class(**wide_relationship_class_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_relationship_class(wide_relationship_class._asdict())
            msg = "Successfully added new relationship class '{}'.".format(wide_relationship_class.name)
            self.msg.emit(msg)

    @Slot(name="add_relationships")
    def add_relationships(self, relationship_class_id=None, object_id=None, object_class_id=None):
        """Insert new relationship."""
        dialog = AddRelationshipsDialog(
            self,
            self.mapping,
            relationship_class_id=relationship_class_id,
            object_id=object_id,
            object_class_id=object_class_id
        )
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for wide_relationship_args in dialog.wide_relationship_args_list:
            try:
                wide_relationship = self.mapping.add_wide_relationship(**wide_relationship_args)
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
                object_class = self.mapping.rename_object_class(renamed['id'], new_name)
                msg = "Successfully renamed object class to '{}'.".format(object_class.name)
            elif renamed_type == 'object':
                object_ = self.mapping.rename_object(renamed['id'], new_name)
                msg = "Successfully renamed object to '{}'.".format(object_.name)
            elif renamed_type == 'relationship_class':
                relationship_class = self.mapping.rename_relationship_class(renamed['id'], new_name)
                msg = "Successfully renamed relationship class to '{}'.".format(relationship_class.name)
            elif renamed_type == 'relationship':
                relationship = self.mapping.rename_relationship(renamed['id'], new_name)
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

    def remove_item(self, removed_index):
        """Remove item from the treeview"""
        removed_item = self.object_tree_model.itemFromIndex(removed_index)
        removed_type = removed_item.data(Qt.UserRole)
        removed = removed_item.data(Qt.UserRole+1)
        removed_id = removed['id']
        try:
            if removed_type == 'object_class':
                self.mapping.remove_object_class(id=removed_id)
                msg = "Successfully removed object class."
            elif removed_type == 'object':
                self.mapping.remove_object(id=removed_id)
                msg = "Successfully removed object."
            elif removed_type.endswith('relationship_class'):
                self.mapping.remove_relationship_class(id=removed_id)
                msg = "Successfully removed relationship class."
            elif removed_type == 'relationship':
                self.mapping.remove_relationship(id=removed_id)
                msg = "Successfully removed relationship."
            else:
                return # should never happen
            self.msg.emit(msg)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        self.object_tree_model.remove_item(removed_type, removed_id)
        # refresh parameter models
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
        elif option == "Paste into new row(s)":
            self.ui.tableView_object_parameter_value.paste(self.clipboard_text, into_new_rows=True)
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
        elif option == "Paste into new row(s)":
            self.ui.tableView_relationship_parameter_value.paste(self.clipboard_text, into_new_rows=True)
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
        elif option == "Paste into new row(s)":
            self.ui.tableView_object_parameter.paste(self.clipboard_text, into_new_rows=True)
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
        elif option == "Paste into new row(s)":
            self.ui.tableView_relationship_parameter.paste(self.clipboard_text, into_new_rows=True)
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
                self.mapping.remove_parameter_value(parameter_value_id)
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
                self.mapping.remove_parameter(parameter_id)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                return
        source_model.removeRows(source_index.row(), 1)
        self.init_parameter_value_models()

    @Slot("int", name="add_object_parameter_values")
    def add_object_parameter_values(self, count=None):
        """Insert count new rows in object parameter value model, so the user can select
        values for a new parameter value.
        """
        if not count:
            count = 1
        proxy_index = self.ui.tableView_object_parameter_value.currentIndex()
        index = self.object_parameter_value_proxy.mapToSource(proxy_index)
        row = index.row()+1
        model = self.object_parameter_value_model
        model.insertRows(row, count)
        self.ui.tabWidget_object.setCurrentIndex(0)
        self.object_parameter_value_proxy.apply_filter()
        # It seems scrolling is not necessary
        self.ui.tableView_object_parameter_value.scrollTo(proxy_index)

    @Slot("QModelIndex", "int", "int", name="setup_object_parameter_value_rows")
    def setup_object_parameter_value_rows(self, parent, first, last):
        """Called when inserting new rows into the model.
        Set defaults and mark row as 'work in progress'.
        """
        model = self.object_parameter_value_model
        h = model.horizontal_header_labels().index
        object_class_name = None
        object_name = None
        for column, value in self.object_parameter_value_proxy.rule_dict.items():
            if column == h('object_class_name'):
                object_class_name = value
            if column == h('object_name'):
                object_name = value
        for row in range(first, last + 1):
            model.set_work_in_progress(row, True)
            if object_class_name:
                model.setData(model.index(row, h('object_class_name')), object_class_name)
            if object_name:
                model.setData(model.index(row, h('object_name')), object_name)

    @Slot("int", name="add_object_parameters")
    def add_object_parameters(self, count=None):
        """Insert count new rows in object parameter model, so the user can select
        values for a new parameter.
        """
        if not count:
            count = 1
        proxy_index = self.ui.tableView_object_parameter.currentIndex()
        index = self.object_parameter_proxy.mapToSource(proxy_index)
        row = index.row()+1
        model = self.object_parameter_model
        model.insertRows(row, count)
        self.ui.tabWidget_object.setCurrentIndex(1)
        self.object_parameter_proxy.apply_filter()
        # It seems scrolling is not necessary
        self.ui.tableView_object_parameter.scrollTo(proxy_index)

    @Slot("QModelIndex", "int", "int", name="setup_object_parameter_rows")
    def setup_object_parameter_rows(self, parent, first, last):
        """Called when inserting new rows into the model.
        Set defaults and mark row as 'work in progress'.
        """
        model = self.object_parameter_model
        h = model.horizontal_header_labels().index
        object_class_name = None
        for column, value in self.object_parameter_proxy.rule_dict.items():
            if column == h('object_class_name'):
                object_class_name = value
        for row in range(first, last + 1):
            model.set_work_in_progress(row, True)
            if object_class_name:
                model.setData(model.index(row, h('object_class_name')), object_class_name)

    @Slot("int", name="add_relationship_parameter_values")
    def add_relationship_parameter_values(self, count):
        """Insert count new rows in relationship parameter value model, so the user can select
        values for a new parameter value.
        """
        if not count:
            count = 1
        proxy_index = self.ui.tableView_relationship_parameter_value.currentIndex()
        index = self.relationship_parameter_value_proxy.mapToSource(proxy_index)
        row = index.row()+1
        model = self.relationship_parameter_value_model
        model.insertRows(row, count)
        self.ui.tabWidget_relationship.setCurrentIndex(0)
        self.relationship_parameter_value_proxy.apply_filter()
        # It seems scrolling is not necessary
        self.ui.tableView_relationship_parameter_value.scrollTo(proxy_index)

    @Slot("QModelIndex", "int", "int", name="setup_relationship_parameter_value_rows")
    def setup_relationship_parameter_value_rows(self, parent, first, last):
        """Called when inserting new rows into the model.
        Set defaults and mark row as 'work in progress'.
        """
        model = self.relationship_parameter_value_model
        h = model.horizontal_header_labels().index
        relationship_class_name = None
        object_name_list = None
        for column, value in self.relationship_parameter_value_proxy.rule_dict.items():
            if column == h('relationship_class_name') and not isinstance(value, list):
                relationship_class_name = value
            if column == h('object_name_list') and not isinstance(value, list):
                object_name_list = value
        for row in range(first, last + 1):
            model.set_work_in_progress(row, True)
            if relationship_class_name:
                model.setData(model.index(row, h('relationship_class_name')), relationship_class_name)
            if object_name_list:
                model.setData(model.index(row, h('object_name_list')), object_name_list)

    @Slot("int", name="add_relationship_parameters")
    def add_relationship_parameters(self, count):
        """Insert count new rows in relationship parameter model, so the user can select
        values for a new parameter.
        """
        if not count:
            count = 1
        proxy_index = self.ui.tableView_relationship_parameter.currentIndex()
        index = self.relationship_parameter_proxy.mapToSource(proxy_index)
        row = index.row()+1
        model = self.relationship_parameter_model
        model.insertRows(row, count)
        self.ui.tabWidget_relationship.setCurrentIndex(1)
        model.make_columns_fixed_for_row(row, 'object_class_name_list')
        self.relationship_parameter_proxy.apply_filter()
        # It seems scrolling is not necessary
        self.ui.tableView_relationship_parameter.scrollTo(proxy_index)

    @Slot("QModelIndex", "int", "int", name="setup_relationship_parameter_rows")
    def setup_relationship_parameter_rows(self, parent, first, last):
        """Called when inserting new rows into the model.
        Set defaults and mark row as 'work in progress'.
        """
        model = self.relationship_parameter_model
        h = model.horizontal_header_labels().index
        relationship_class_name = None
        for column, value in self.relationship_parameter_proxy.rule_dict.items():
            if column == h('relationship_class_name') and not isinstance(value, list):
                relationship_class_name = value
        for row in range(first, last + 1):
            model.set_work_in_progress(row, True)
            if relationship_class_name:
                model.setData(model.index(row, h('relationship_class_name')), relationship_class_name)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="object_parameter_value_data_changed")
    def object_parameter_value_data_changed(self, top_left, bottom_right, roles):
        """Called when data in the object parameter value model changes. Add new parameter
        or edit existing ones."""
        if not top_left.isValid():
            return
        if Qt.EditRole not in roles:
            return
        if top_left.data(Qt.DisplayRole) is None:
            return
        model = self.object_parameter_value_model
        if model.is_being_reset:
            return
        row = top_left.row()
        header = model.horizontal_header_labels()
        h = model.horizontal_header_labels().index
        if model.is_work_in_progress(row):
            # Try and fill object class name from object name, to make user's life easier
            if top_left.column() == h('object_name'):
                object_name = top_left.sibling(row, h('object_name')).data(Qt.DisplayRole)
                object_ = self.mapping.single_object(name=object_name).one_or_none()
                if not object_:
                    return
                object_class = self.mapping.single_object_class(id=object_.class_id).one_or_none()
                if not object_class:
                    return
                object_class_name = object_class.name
                model.setData(top_left.sibling(row, h('object_class_name')), object_class_name, Qt.EditRole)
                return
            # Try and fill object class name from parameter name, to make user's life easier
            if top_left.column() == h('parameter_name'):
                parameter_name = top_left.sibling(row, h('parameter_name')).data(Qt.DisplayRole)
                parameter = self.mapping.single_parameter(name=parameter_name).one_or_none()
                if not parameter:
                    return
                object_class = self.mapping.single_object_class(id=parameter.object_class_id).one_or_none()
                if not object_class:
                    return
                object_class_name = object_class.name
                model.setData(top_left.sibling(row, h('object_class_name')), object_class_name, Qt.EditRole)
                return
            # Now try and add the parameter value
            object_name = top_left.sibling(row, h('object_name')).data(Qt.DisplayRole)
            object_ = self.mapping.single_object(name=object_name).one_or_none()
            if not object_:
                return
            parameter_name = top_left.sibling(row, h('parameter_name')).data(Qt.DisplayRole)
            parameter = self.mapping.single_parameter(name=parameter_name).one_or_none()
            if not parameter:
                return
            # Pack all remaining fields in case the user 'misbehaves' and edit those before entering the parameter name
            kwargs = {}
            for column in range(h('parameter_name')+1, model.columnCount()):
                kwargs[header[column]] = top_left.sibling(row, column).data(Qt.DisplayRole)
            try:
                parameter_value = self.mapping.add_parameter_value(
                    object_id=object_.id,
                    parameter_id=parameter.id,
                    **kwargs
                )
                model.set_work_in_progress(row, False)
                model.make_columns_fixed_for_row(
                    row, 'object_class_name', 'object_name', 'parameter_name', 'parameter_value_id')
                model.setData(top_left.sibling(row, h('parameter_value_id')), parameter_value.id, Qt.EditRole)
                msg = "Successfully added new parameter value."
                self.msg.emit(msg)
            except SpineDBAPIError as e:
                model.setData(top_left, None, Qt.EditRole)
                self.msg_error.emit(e.msg)
        elif top_left.flags() & Qt.ItemIsEditable:
            self.update_parameter_value_in_db(top_left)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="object_parameter_data_changed")
    def object_parameter_data_changed(self, top_left, bottom_right, roles):
        """Called when data in the object parameter model changes. Add new parameter
        or edit existing ones."""
        if not top_left.isValid():
            return
        if Qt.EditRole not in roles:
            return
        if top_left.data(Qt.DisplayRole) is None:
            return
        model = self.object_parameter_model
        if model.is_being_reset:
            return
        row = top_left.row()
        header = model.horizontal_header_labels()
        h = model.horizontal_header_labels().index
        if model.is_work_in_progress(row):
            object_class_name = top_left.sibling(row, h('object_class_name')).data(Qt.DisplayRole)
            object_class = self.mapping.single_object_class(name=object_class_name).one_or_none()
            if not object_class:
                return
            parameter_name = top_left.sibling(row, h('parameter_name')).data(Qt.DisplayRole)
            if not parameter_name:
                return
            # Pack all remaining fields in case the user 'misbehaves' and edit those before entering the parameter name
            kwargs = {}
            for column in range(h('parameter_name')+1, model.columnCount()):
                kwargs[header[column]] = top_left.sibling(row, column).data(Qt.DisplayRole)
            try:
                parameter = self.mapping.add_parameter(object_class_id=object_class.id, name=parameter_name, **kwargs)
                model.set_work_in_progress(row, False)
                model.make_columns_fixed_for_row(row, 'object_class_name', 'parameter_id')
                model.setData(top_left.sibling(row, h('parameter_id')), parameter.id, Qt.EditRole)
                msg = "Successfully added new parameter."
                self.msg.emit(msg)
            except SpineDBAPIError as e:
                model.setData(top_left, None, Qt.EditRole)
                self.msg_error.emit(e.msg)
        elif top_left.flags() & Qt.ItemIsEditable:
            self.update_parameter_in_db(top_left)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="relationship_parameter_value_data_changed")
    def relationship_parameter_value_data_changed(self, top_left, bottom_right, roles):
        """Called when data in the relationship parameter value model changes. Add new parameter
        or edit existing ones."""
        if not top_left.isValid():
            return
        if Qt.EditRole not in roles:
            return
        if top_left.data(Qt.DisplayRole) is None:
            return
        model = self.relationship_parameter_value_model
        if model.is_being_reset:
            return
        row = top_left.row()
        header = model.horizontal_header_labels()
        h = model.horizontal_header_labels().index
        if model.is_work_in_progress(row):
            # Try and fill relationship class name from parameter name, to make user's life easier
            if top_left.column() == h('parameter_name'):
                parameter_name = top_left.sibling(row, h('parameter_name')).data(Qt.DisplayRole)
                parameter = self.mapping.single_parameter(name=parameter_name).one_or_none()
                if not parameter:
                    return
                relationship_class = self.mapping.single_wide_relationship_class(id=parameter.relationship_class_id).\
                    one_or_none()
                if not relationship_class:
                    return
                relationship_class_name = relationship_class.name
                model.setData(
                    top_left.sibling(row, h('relationship_class_name')), relationship_class_name, Qt.EditRole)
                return
            # Try to add new parameter value
            # Start by adding the relationship
            relationship_class_name = top_left.sibling(row, h('relationship_class_name')).data(Qt.DisplayRole)
            relationship_class = self.mapping.single_wide_relationship_class(name=relationship_class_name).\
                one_or_none()
            if not relationship_class:
                return None
            object_name_list = top_left.sibling(row, h('object_name_list')).data(Qt.DisplayRole)
            if not object_name_list:
                return
            object_id_list = list()
            for object_name in object_name_list.split(','):
                object_ = self.mapping.single_object(name=object_name).one_or_none()
                if not object_:
                    logging.debug("Couldn't find object '{}', something is wrong.".format(object_name))
                    return
                object_id_list.append(object_.id)
            # Create relationship name
            relationship_name = "__".join(object_name_list.split(','))
            base_relationship_name = relationship_name
            i = 0
            while True:
                other_relationship = self.mapping.single_wide_relationship(name=relationship_name).one_or_none()
                if not other_relationship:
                    break
                relationship_name = base_relationship_name + str(i)
                i += 1
            try:
                relationship = self.mapping.add_wide_relationship(
                    name=relationship_name,
                    object_id_list=object_id_list,
                    class_id=relationship_class.id
                )
                self.object_tree_model.add_relationship(relationship._asdict())
                msg = "Successfully added new relationship '{}'.".format(relationship.name)
                self.msg.emit(msg)
            except SpineDBAPIError as e:
                # Maybe the relationship already exists, try to retrieve it
                relationship = self.mapping.single_wide_relationship(
                    class_id=relationship_class.id, object_name_list=object_name_list).one_or_none()
                if not relationship:
                    model.setData(top_left, None, Qt.EditRole)
                    self.msg_error.emit(e.msg)
                    return
                msg = "Successfully retrieved relationship '{}'.".format(relationship.name)
                self.msg.emit(msg)
            # Continue adding the parameter value
            parameter_name = top_left.sibling(row, h('parameter_name')).data(Qt.DisplayRole)
            parameter = self.mapping.single_parameter(name=parameter_name).one_or_none()
            if not parameter:
                return
            # Pack all remaining fields in case the user 'misbehaves' and edit those before entering the parameter name
            kwargs = {}
            for column in range(h('parameter_name')+1, model.columnCount()):
                kwargs[header[column]] = top_left.sibling(row, column).data(Qt.DisplayRole)
            try:
                parameter_value = self.mapping.add_parameter_value(
                    relationship_id=relationship.id,
                    parameter_id=parameter.id,
                    **kwargs
                )
                model.set_work_in_progress(row, False)
                model.make_columns_fixed_for_row(
                    row,
                    'relationship_class_name',
                    'object_name_list',
                    'parameter_name',
                    'parameter_value_id'
                )
                model.setData(top_left.sibling(row, h('parameter_value_id')), parameter_value.id, Qt.EditRole)
                model.setData(top_left.sibling(row, h('relationship_class_name')), relationship_class_name, Qt.EditRole)
                msg = "Successfully added new parameter value."
                self.msg.emit(msg)
            except SpineDBAPIError as e:
                model.setData(top_left, None, Qt.EditRole)
                self.msg_error.emit(e.msg)
        elif top_left.flags() & Qt.ItemIsEditable:
            self.update_parameter_value_in_db(top_left)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="relationship_parameter_data_changed")
    def relationship_parameter_data_changed(self, top_left, bottom_right, roles):
        """Called when data in the relationship parameter model changes. Add new parameter
        or edit existing ones."""
        if not top_left.isValid():
            return
        if Qt.EditRole not in roles:
            return
        if top_left.data(Qt.DisplayRole) is None:
            return
        model = self.relationship_parameter_model
        if model.is_being_reset:
            return
        proxy = self.relationship_parameter_proxy
        row = top_left.row()
        header = model.horizontal_header_labels()
        h = model.horizontal_header_labels().index
        if model.is_work_in_progress(row):
            # Autocomplete object class name list
            if top_left.column() == h('relationship_class_name'):
                relationship_class_name = top_left.data(Qt.DisplayRole)
                relationship_class = self.mapping.single_wide_relationship_class(name=relationship_class_name).\
                    one_or_none()
                if relationship_class:
                    sibling = top_left.sibling(row, h('object_class_name_list'))
                    model.setData(sibling, relationship_class.object_class_name_list, Qt.EditRole)
            # Try to add new parameter
            relationship_class_name = top_left.sibling(row, h('relationship_class_name')).data(Qt.DisplayRole)
            relationship_class = self.mapping.single_wide_relationship_class(name=relationship_class_name).\
                one_or_none()
            if not relationship_class:
                return
            parameter_name = top_left.sibling(row, h('parameter_name')).data(Qt.DisplayRole)
            if not parameter_name:
                return
            # Pack all remaining fields in case the user 'misbehaves' and edit those before entering the parameter name
            kwargs = {}
            for column in range(h('parameter_name')+1, model.columnCount()):
                kwargs[header[column]] = top_left.sibling(row, column).data(Qt.DisplayRole)
            try:
                parameter = self.mapping.add_parameter(
                    relationship_class_id=relationship_class.id,
                    name=parameter_name,
                    **kwargs
                )
                model.set_work_in_progress(row, False)
                model.make_columns_fixed_for_row(row, 'relationship_class_name', 'parameter_id')
                model.setData(top_left.sibling(row, h('parameter_id')), parameter.id, Qt.EditRole)
                msg = "Successfully added new parameter."
                self.msg.emit(msg)
            except SpineDBAPIError as e:
                model.setData(top_left, None, Qt.EditRole)
                self.msg_error.emit(e.msg)
        elif top_left.flags() & Qt.ItemIsEditable:
            self.update_parameter_in_db(top_left)

    def update_parameter_value_in_db(self, index):
        """After updating a parameter value in the model, try and update it in the database.
        Undo the model update if unsuccessful.
        """
        model = index.model()
        header = model.horizontal_header_labels()
        h = header.index
        id_column = h('parameter_value_id')
        sibling = index.sibling(index.row(), id_column)
        parameter_value_id = sibling.data()
        if not parameter_value_id:
            return
        field_name = header[index.column()]
        new_value = index.data(Qt.DisplayRole)
        try:
            self.mapping.update_parameter_value(parameter_value_id, field_name, new_value)
            msg = "Parameter value successfully updated."
            self.msg.emit(msg)
        except SpineDBAPIError as e:
            model.setData(index, None, Qt.EditRole)
            self.msg.emit(e.msg)

    def update_parameter_in_db(self, index):
        """After updating a parameter in the model, try and update it in the database.
        Undo the model update if unsuccessful.
        """
        model = index.model()
        header = model.horizontal_header_labels()
        id_column = header.index('parameter_id')
        sibling = index.sibling(index.row(), id_column)
        parameter_id = sibling.data()
        field_name = header[index.column()]
        new_value = index.data(Qt.DisplayRole)
        if field_name == 'parameter_name':
            field_name = 'name'
        try:
            self.mapping.update_parameter(parameter_id, field_name, new_value)
            msg = "Parameter successfully updated."
            self.msg.emit(msg)
            # refresh parameter value models to reflect name change
            if field_name == 'name':
                self.init_parameter_value_models()
        except SpineDBAPIError as e:
            model.setData(index, None, Qt.EditRole)
            self.msg.emit(e.msg)

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
        self.mapping.close()
        if event:
            event.accept()
