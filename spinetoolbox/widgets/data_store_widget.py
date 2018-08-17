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

:author: Manuel Marin <manuelma@kth.se>
:date:   21.4.2018
"""

import time  # just to measure loading time and sqlalchemy ORM performance
import logging
from PySide2.QtWidgets import QMainWindow, QWidget, QHeaderView, QDialog, QLineEdit, QInputDialog, \
    QMessageBox
from PySide2.QtCore import Signal, Slot, Qt, QSettings
from PySide2.QtGui import QStandardItem, QFont, QFontMetrics
from ui.data_store_form import Ui_MainWindow
from config import STATUSBAR_SS
from spinedatabase_api import SpineDBAPIError
from widgets.custom_menus import ObjectTreeContextMenu, ParameterValueContextMenu, ParameterContextMenu
from widgets.lineedit_delegate import LineEditDelegate
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, AddRelationshipClassesDialog, \
    AddRelationshipsDialog, AddParametersDialog, AddParameterValuesDialog, CommitDialog
from models import ObjectTreeModel, MinimalTableModel, ObjectParameterValueProxy, \
    RelationshipParameterValueProxy, ObjectParameterProxy, RelationshipParameterProxy


class DataStoreForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store."""

    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, data_store, mapping, database):
        """ Initialize class.

        Args:
            data_store (DataStore): The DataStore instance that owns this form
            mapping (DatabaseMapping): The object relational mapping
            database (str): The database name
        """
        tic = time.clock()
        super().__init__(flags=Qt.Window)
        self._data_store = data_store
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox Data Store")
        # Class attributes
        self.mapping = mapping
        self.database = database
        self.mapping.new_commit()
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self)
        # Parameter value models
        self.object_parameter_value_model = MinimalTableModel(self)
        self.object_parameter_value_proxy = ObjectParameterValueProxy(self)
        self.relationship_parameter_value_model = MinimalTableModel(self)
        self.relationship_parameter_value_proxy = RelationshipParameterValueProxy(self)
        # Parameter (definition) models
        self.object_parameter_model = MinimalTableModel(self)
        self.object_parameter_proxy = ObjectParameterProxy(self)
        self.relationship_parameter_model = MinimalTableModel(self)
        self.relationship_parameter_proxy = RelationshipParameterProxy(self)
        # Set up status bar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Context menus
        self.object_tree_context_menu = None
        self.object_parameter_value_context_menu = None
        self.relationship_parameter_value_context_menu = None
        self.object_parameter_context_menu = None
        self.relationship_parameter_context_menu = None
        # init models and views
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_models()
        self.init_parameter_value_views()
        self.init_parameter_views()
        self.connect_signals()
        self.restore_ui()
        self.setWindowTitle("Spine Data Store    -- {} --".format(self.database))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        toc = time.clock()
        logging.debug("Elapsed = {}".format(toc - tic))

    def connect_signals(self):
        """Connect signals to slots."""
        # Event log signals
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        # Menu commands
        self.ui.actionCommit.triggered.connect(self.commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionClose.triggered.connect(self.close_session)
        self.ui.actionAdd_object_classes.triggered.connect(self.add_object_classes)
        self.ui.actionAdd_objects.triggered.connect(self.add_objects)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.add_relationship_classes)
        self.ui.actionAdd_relationships.triggered.connect(self.add_relationships)
        self.ui.actionAdd_parameters.triggered.connect(self.add_parameters)
        self.ui.actionAdd_parameter_values.triggered.connect(self.add_parameter_values)
        # Object tree
        #self.ui.treeView_object.selectionModel().currentChanged.connect(self.filter_parameter_value_models)
        #self.ui.treeView_object.selectionModel().currentChanged.connect(self.filter_parameter_models)
        self.ui.treeView_object.editKeyPressed.connect(self.rename_item)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.expand_next_leaf)
        self.object_tree_model.rowsInserted.connect(self.scroll_to_new_item)
        # Parameter tables
        self.ui.tableView_object_parameter_value.customContextMenuRequested.\
            connect(self.show_object_parameter_value_context_menu)
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.\
            connect(self.show_relationship_parameter_value_context_menu)
        self.ui.tableView_object_parameter.customContextMenuRequested.\
            connect(self.show_object_parameter_context_menu)
        self.ui.tableView_relationship_parameter.customContextMenuRequested.\
            connect(self.show_relationship_parameter_context_menu)
        self.object_parameter_model.row_with_data_inserted.\
            connect(self.scroll_to_new_object_parameter)
        self.relationship_parameter_model.row_with_data_inserted.\
            connect(self.scroll_to_new_relationship_parameter)
        self.object_parameter_value_model.row_with_data_inserted.\
            connect(self.scroll_to_new_object_parameter_value)
        self.relationship_parameter_value_model.row_with_data_inserted.\
            connect(self.scroll_to_new_relationship_parameter_value)
        # DS destroyed
        self._data_store.destroyed.connect(self.data_store_destroyed)

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Append regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        current_msg = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(current_msg + " " + msg, 5000)

    @Slot(str, name="add_error_message")
    def add_error_message(self, msg):
        """Show error message in message box.

        Args:
            msg (str): String to show in QMessageBox
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(msg)
        msg_box.exec_()

    @Slot(name="data_store_destroyed")
    def data_store_destroyed(self):
        """Close this form without commiting any changes when data store item is destroyed."""
        self._data_store = None
        self.close()

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
        msg = "All changes commited successfully."
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
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_models()
        # clear filters
        self.object_parameter_value_proxy.reset()
        self.relationship_parameter_value_proxy.reset()

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
        self.object_parameter_value_model.header = [column['name'] for column in header]
        self.object_parameter_value_model.reset_model(object_parameter_value_data)
        self.object_parameter_value_proxy.setSourceModel(self.object_parameter_value_model)
        # Relationship
        relationship_parameter_value_list = self.mapping.relationship_parameter_value_list()
        header = relationship_parameter_value_list.column_descriptions
        self.relationship_parameter_value_model.header = [column['name'] for column in header]
        relationship_parameter_value_data = [list(row._asdict().values()) for row in relationship_parameter_value_list]
        self.relationship_parameter_value_model.reset_model(relationship_parameter_value_data)
        self.relationship_parameter_value_proxy.setSourceModel(self.relationship_parameter_value_model)

    def init_parameter_models(self):
        """Initialize parameter (definition) models from source database."""
        # Object
        object_parameter_list = self.mapping.object_parameter_list()
        header = object_parameter_list.column_descriptions
        self.object_parameter_model.header = [column['name'] for column in header]
        object_parameter_data = [list(row._asdict().values()) for row in object_parameter_list]
        self.object_parameter_model.reset_model(object_parameter_data)
        self.object_parameter_proxy.setSourceModel(self.object_parameter_model)
        # Relationship
        relationship_parameter_list = self.mapping.relationship_parameter_list()
        header = relationship_parameter_list.column_descriptions
        self.relationship_parameter_model.header = [column['name'] for column in header]
        relationship_parameter_data = [list(row._asdict().values()) for row in relationship_parameter_list]
        self.relationship_parameter_model.reset_model(relationship_parameter_data)
        self.relationship_parameter_proxy.setSourceModel(self.relationship_parameter_model)

    def init_parameter_value_views(self):
        self.init_object_parameter_value_view()
        self.init_relationship_parameter_value_view()

    def init_object_parameter_value_view(self):
        """Init the object parameter table view."""
        header = self.object_parameter_value_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_object_parameter_value.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_value.verticalHeader().\
            setDefaultSectionSize(self.default_row_height)
        # set model
        self.ui.tableView_object_parameter_value.setModel(self.object_parameter_value_proxy)
        # hide id columns
        self.ui.tableView_object_parameter_value.hideColumn(header.index("object_class_id"))
        self.ui.tableView_object_parameter_value.hideColumn(header.index("object_id"))
        self.ui.tableView_object_parameter_value.hideColumn(header.index("parameter_value_id"))
        # create line edit delegate and connect signals
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_parameter_value)
        self.ui.tableView_object_parameter_value.setItemDelegate(lineedit_delegate)
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()

    def init_relationship_parameter_value_view(self):
        """Init the relationship parameter table view."""
        header = self.relationship_parameter_value_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_relationship_parameter_value.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_value.verticalHeader().\
            setDefaultSectionSize(self.default_row_height)
        # set model
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_proxy)
        # hide id columns
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("relationship_class_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("relationship_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("object_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("parameter_value_id"))
        # create line edit delegate and connect signals
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_parameter_value)
        self.ui.tableView_relationship_parameter_value.setItemDelegate(lineedit_delegate)
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_parameter_views(self):
        self.init_object_parameter_view()
        self.init_relationship_parameter_view()

    def init_object_parameter_view(self):
        """Init the object parameter table view."""
        header = self.object_parameter_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_object_parameter.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter.verticalHeader().\
            setDefaultSectionSize(self.default_row_height)
        # set model
        self.ui.tableView_object_parameter.setModel(self.object_parameter_proxy)
        # hide id columns
        self.ui.tableView_object_parameter.hideColumn(header.index("object_class_id"))
        self.ui.tableView_object_parameter.hideColumn(header.index("parameter_id"))
        # create line edit delegate and connect signals
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_parameter)
        self.ui.tableView_object_parameter.setItemDelegate(lineedit_delegate)
        self.ui.tableView_object_parameter.resizeColumnsToContents()

    def init_relationship_parameter_view(self):
        """Init the object parameter table view."""
        header = self.relationship_parameter_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_relationship_parameter.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter.verticalHeader().\
            setDefaultSectionSize(self.default_row_height)
        # set model
        self.ui.tableView_relationship_parameter.setModel(self.relationship_parameter_proxy)
        # hide id columns
        self.ui.tableView_relationship_parameter.hideColumn(header.index("relationship_class_id"))
        self.ui.tableView_relationship_parameter.hideColumn(header.index("parameter_id"))
        # create line edit delegate and connect signals
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_parameter)
        self.ui.tableView_relationship_parameter.setItemDelegate(lineedit_delegate)
        self.ui.tableView_relationship_parameter.resizeColumnsToContents()

    @Slot("QModelIndex", "int", "int", name="scroll_to_new_item")
    def scroll_to_new_item(self, parent, first, last):
        """Scroll to newly inserted item in the object treeView."""
        last_index = self.object_tree_model.index(last, 0, parent)
        self.ui.treeView_object.setCurrentIndex(last_index)
        self.ui.treeView_object.scrollTo(last_index)

    @Slot("QModelIndex", "int", name="scroll_to_new_object_parameter")
    def scroll_to_new_object_parameter(self, parent, row):
        """Scroll to newly inserted parameter in the object parameter tableview."""
        self.ui.tabWidget_object.setCurrentIndex(1)
        self.object_parameter_proxy.apply()
        self.ui.tableView_object_parameter.resizeColumnsToContents()
        index = self.object_parameter_model.index(row, 0, parent)
        proxy_index = self.object_parameter_proxy.mapFromSource(index)
        self.ui.tableView_object_parameter.scrollTo(proxy_index)

    @Slot("QModelIndex", "int", name="scroll_to_new_relationship_parameter")
    def scroll_to_new_relationship_parameter(self, parent, row):
        """Scroll to newly inserted parameter in the relationship parameter tableview."""
        self.ui.tabWidget_relationship.setCurrentIndex(1)
        self.relationship_parameter_proxy.apply()
        self.ui.tableView_relationship_parameter.resizeColumnsToContents()
        index = self.relationship_parameter_model.index(row, 0, parent)
        proxy_index = self.relationship_parameter_proxy.mapFromSource(index)
        self.ui.tableView_relationship_parameter.scrollTo(proxy_index)

    @Slot("QModelIndex", "int", name="scroll_to_new_object_parameter_value")
    def scroll_to_new_object_parameter_value(self, parent, row):
        """Scroll to newly inserted parameter in the object parameter value tableview."""
        self.ui.tabWidget_object.setCurrentIndex(0)
        self.object_parameter_value_proxy.apply()
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()
        index = self.object_parameter_value_model.index(row, 0, parent)
        proxy_index = self.object_parameter_value_proxy.mapFromSource(index)
        self.ui.tableView_object_parameter_value.scrollTo(proxy_index)

    @Slot("QModelIndex", "int", name="scroll_to_new_relationship_parameter_value")
    def scroll_to_new_relationship_parameter_value(self, parent, row):
        """Scroll to newly inserted parameter in the relationship parameter value tableview."""
        self.ui.tabWidget_relationship.setCurrentIndex(0)
        self.relationship_parameter_value_proxy.apply()
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()
        index = self.relationship_parameter_value_model.index(row, 0, parent)
        proxy_index = self.relationship_parameter_value_proxy.mapFromSource(index)
        self.ui.tableView_relationship_parameter_value.scrollTo(proxy_index)

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
        """Expand next ocurrence of a relationship."""
        next_index = self.object_tree_model.next_relationship_index(index)
        if not next_index:
            return
        self.ui.treeView_object.setCurrentIndex(next_index)
        self.ui.treeView_object.scrollTo(next_index)
        self.ui.treeView_object.expand(next_index)

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_value_models(self, current, previous):
        """Populate tableViews whenever an object item is selected in the treeView"""
        self.object_parameter_value_proxy.reset()
        self.relationship_parameter_value_proxy.reset()
        selected_type = current.data(Qt.UserRole)
        if not selected_type:
            return
        selected = current.data(Qt.UserRole+1)
        parent = current.parent().data(Qt.UserRole+1)
        if selected_type == 'object_class':
            object_class_name = selected['name']
            self.object_parameter_value_proxy.add_condition(object_class_name=object_class_name)
        elif selected_type == 'object':
            object_name = selected['name']
            self.object_parameter_value_proxy.add_condition(object_name=object_name)
            self.relationship_parameter_value_proxy.add_condition(parent_object_name=object_name,
                child_object_name=object_name)
            self.relationship_parameter_value_proxy.hide_column("parent_relationship_name")
        elif selected_type == 'proto_relationship_class':
            relationship_class_name = selected['name']
            object_name = parent['name']
            self.relationship_parameter_value_proxy.add_condition(parent_object_name=object_name,
                child_object_name=object_name)
            self.relationship_parameter_value_proxy.add_condition(relationship_class_name=relationship_class_name)
            self.relationship_parameter_value_proxy.hide_column("parent_relationship_name")
        elif selected_type == 'related_object':
            object_name = selected['name']
            self.object_parameter_value_proxy.add_condition(object_name=object_name)
            relationship_name = selected['relationship_name']
            self.relationship_parameter_value_proxy.add_condition(parent_object_name=object_name,
                child_object_name=object_name, parent_relationship_name=relationship_name)
        elif selected_type == 'meta_relationship_class':
            relationship_class_name = selected['name']
            relationship_name = parent['relationship_name']
            self.relationship_parameter_value_proxy.add_condition(parent_relationship_name=relationship_name)
            self.relationship_parameter_value_proxy.add_condition(relationship_class_name=relationship_class_name)
            self.relationship_parameter_value_proxy.hide_column("parent_object_name")
        self.object_parameter_value_proxy.apply()
        self.relationship_parameter_value_proxy.apply()
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, current, previous):
        """Populate tableViews whenever an object item is selected in the treeView"""
        self.object_parameter_proxy.reset()
        self.relationship_parameter_proxy.reset()
        selected_type = current.data(Qt.UserRole)
        if not selected_type:
            return
        selected = current.data(Qt.UserRole+1)
        parent = current.parent().data(Qt.UserRole+1)
        if selected_type == 'object_class': # show only this class
            object_class_name = selected['name']
            self.object_parameter_proxy.add_condition(object_class_name=object_class_name)
        elif selected_type == 'object': # show only this object's class
            object_class_name = parent['name']
            self.object_parameter_proxy.add_condition(object_class_name=object_class_name)
        elif selected_type.endswith('relationship_class'):
            relationship_class_name = selected['name']
            self.relationship_parameter_proxy.add_condition(relationship_class_name=relationship_class_name)
        elif selected_type == 'related_object':
            relationship_class_name = parent['name']
            self.relationship_parameter_proxy.add_condition(relationship_class_name=relationship_class_name)
        self.object_parameter_proxy.apply()
        self.relationship_parameter_proxy.apply()
        self.ui.tableView_object_parameter.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter.resizeColumnsToContents()

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
        class_id = tree_index.data(Qt.UserRole+1)['id']
        if class_type == 'object_class':
            self.add_parameters(object_class_id=class_id)
        elif class_type == 'relationship_class':
            self.add_parameters(relationship_class_id=class_id)

    def call_add_parameter_values(self, tree_index):
        class_id = tree_index.parent().data(Qt.UserRole+1)['id']
        entity_type = tree_index.data(Qt.UserRole)
        if entity_type == 'object':
            object_id = tree_index.data(Qt.UserRole+1)['id']
            self.add_parameter_values(object_class_id=class_id, object_id=object_id)
        elif entity_type == 'relationship':
            relationship_id = tree_index.data(Qt.UserRole+1)['id']
            self.add_parameter_values(relationship_class_id=class_id, relationship_id=relationship_id)

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
        for wide_relationship_class in dialog.wide_relationship_class_list:
            try:
                new_wide_relationship_class = self.mapping.add_wide_relationship_class(wide_relationship_class)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_relationship_class(new_wide_relationship_class)
            msg = "Successfully added new relationship class '{}'.".format(new_wide_relationship_class['name'])
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
        for wide_relationship in dialog.wide_relationship_list:
            try:
                new_wide_relationship = self.mapping.add_wide_relationship(wide_relationship)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_tree_model.add_relationship(new_wide_relationship)
            msg = "Successfully added new relationship '{}'.".format(new_wide_relationship['name'])
            self.msg.emit(msg)

    @Slot(name="add_parameters")
    def add_parameters(self, object_class_id=None, relationship_class_id=None):
        """Insert new parameters."""
        dialog = AddParametersDialog(
            self,
            self.mapping,
            object_class_id=object_class_id,
            relationship_class_id=relationship_class_id
        )
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for parameter_args in dialog.parameter_args_list:
            try:
                parameter = self.mapping.add_parameter(**parameter_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.add_parameter_to_model(parameter.__dict__)
            msg = "Successfully added new parameter '{}'.".format(parameter.name)
            self.msg.emit(msg)

    def add_parameter_to_model(self, parameter):
        """Add parameter item to the object or relationship parameter model.

        Args:
            parameter (dict)
        """
        if 'object_class_id' in parameter:
            object_parameter = self.mapping.single_object_parameter(parameter['id'])
            if not object_parameter:
                return
            self.object_parameter_proxy.reset()
            self.object_parameter_proxy.add_condition(parameter_name=parameter['name'])
            object_parameter_row_data = object_parameter._asdict().values()
            row = self.object_parameter_model.rowCount()
            self.object_parameter_model.insert_row_with_data(row, object_parameter_row_data)
        elif 'relationship_class_id' in parameter:
            relationship_parameter = self.mapping.single_relationship_parameter(parameter['id'])
            if not relationship_parameter:
                return
            self.relationship_parameter_proxy.reset()
            self.relationship_parameter_proxy.add_condition(parameter_name=parameter['name'])
            relationship_parameter_row_data = relationship_parameter._asdict().values()
            row = self.relationship_parameter_model.rowCount()
            self.relationship_parameter_model.insert_row_with_data(row, relationship_parameter_row_data)

    @Slot(name="add_parameter_values")
    def add_parameter_values(self, object_class_id=None, relationship_class_id=None,
            object_id=None, relationship_id=None):
        """Insert new parameter values."""
        dialog = AddParameterValuesDialog(
            self,
            self.mapping,
            object_class_id=object_class_id,
            relationship_class_id=relationship_class_id,
            object_id=object_id,
            relationship_id=relationship_id
        )
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for parameter_value_args in dialog.parameter_value_args_list:
            try:
                parameter_value = self.mapping.add_parameter_value(**parameter_value_args)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.add_parameter_value_to_model(parameter_value.__dict__)
            msg = "Successfully added new parameter value."
            self.msg.emit(msg)

    def add_parameter_value_to_model(self, parameter_value):
        """Add parameter value item to the object or relationship parameter value model.

        Args:
            parameter_value (dict)
        """
        if 'object_id' in parameter_value:
            object_parameter_value = self.mapping.single_object_parameter_value(parameter_value['id'])
            if not object_parameter_value:
                return
            self.object_parameter_value_proxy.reset()
            parameter_name = object_parameter_value.parameter_name
            self.object_parameter_value_proxy.add_condition(parameter_name=parameter_name)
            object_parameter_value_row_data = object_parameter_value._asdict().values()
            row = self.object_parameter_value_model.rowCount()
            self.object_parameter_value_model.insert_row_with_data(row, object_parameter_value_row_data)
        elif 'relationship_id' in parameter_value:
            relationship_parameter_value = self.mapping.single_relationship_parameter_value(parameter_value['id'])
            if not relationship_parameter_value:
                return
            self.relationship_parameter_value_proxy.reset()
            parameter_name = relationship_parameter_value.parameter_name
            self.relationship_parameter_value_proxy.add_condition(parameter_name=parameter_name)
            relationship_parameter_value_row_data = relationship_parameter_value._asdict().values()
            row = self.relationship_parameter_value_model.rowCount()
            self.relationship_parameter_value_model.insert_row_with_data(row, relationship_parameter_value_row_data)

    def rename_item(self, renamed_index):
        """Rename item in the database and treeview"""
        renamed_item = self.object_tree_model.itemFromIndex(renamed_index)
        curr_name = renamed_item.text()
        answer = QInputDialog.getText(self, "Rename item", "Enter new name:",\
            QLineEdit.Normal, curr_name)
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
            elif renamed_type.endswith('object'):
                object_ = self.mapping.rename_object(renamed['id'], new_name)
                msg = "Successfully renamed object to '{}'.".format(object_.name)
            elif renamed_type.endswith('relationship_class'):
                relationship_class = self.mapping.rename_relationship_class(renamed['id'], new_name)
                msg = "Successfully renamed relationship class to '{}'.".format(relationship_class.name)
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
        # self.ui.tableView_object_parameter_value.selectRow(index.row())
        global_pos = self.ui.tableView_object_parameter_value.viewport().mapToGlobal(pos)
        self.object_parameter_value_context_menu = ParameterValueContextMenu(self, global_pos, index)
        option = self.object_parameter_value_context_menu.get_action()
        if option == "Remove parameter value":
            self.remove_parameter_value(index)
        self.object_parameter_value_context_menu.deleteLater()
        self.object_parameter_value_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_value_context_menu")
    def show_relationship_parameter_value_context_menu(self, pos):
        """Context menu for relationship parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_relationship_parameter_value.indexAt(pos)
        # self.ui.tableView_relationship_parameter_value.selectRow(index.row())
        global_pos = self.ui.tableView_relationship_parameter_value.viewport().mapToGlobal(pos)
        self.relationship_parameter_value_context_menu = ParameterValueContextMenu(self, global_pos, index)
        option = self.relationship_parameter_value_context_menu.get_action()
        if option == "Remove parameter value":
            self.remove_parameter_value(index)
        self.relationship_parameter_value_context_menu.deleteLater()
        self.relationship_parameter_value_context_menu = None

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_parameter_value")
    def update_parameter_value(self, editor, hint):
        """Update (object or relationship) parameter_value table with newly edited data.
        If successful, also update item in the model.
        """
        index = editor.index
        proxy_model = index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        header = source_model.header
        id_column = header.index('parameter_value_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_value_id = sibling.data()
        field_name = header[source_index.column()]
        new_value = editor.text()
        try:
            self.mapping.update_parameter_value(parameter_value_id, field_name, new_value)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        source_model.setData(source_index, new_value)
        msg = "Parameter value succesfully updated."
        self.msg.emit(msg)

    def remove_parameter_value(self, proxy_index):
        """Remove row from (object or relationship) parameter_value table.
        If succesful, also remove row from model"""
        proxy_model = proxy_index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(proxy_index)
        id_column = source_model.header.index('parameter_value_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_value_id = sibling.data()
        try:
            self.mapping.remove_parameter_value(parameter_value_id)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        source_model.removeRows(source_index.row(), 1)

    @Slot("QPoint", name="show_object_parameter_context_menu")
    def show_object_parameter_context_menu(self, pos):
        """Context menu for object parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_object_parameter.indexAt(pos)
        # self.ui.tableView_object_parameter.selectRow(index.row())
        global_pos = self.ui.tableView_object_parameter.viewport().mapToGlobal(pos)
        self.object_parameter_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.object_parameter_context_menu.get_action()
        if option == "Remove parameter":
            self.remove_parameter(index)
        self.object_parameter_context_menu.deleteLater()
        self.object_parameter_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_context_menu")
    def show_relationship_parameter_context_menu(self, pos):
        """Context menu for relationship parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_relationship_parameter.indexAt(pos)
        # self.ui.tableView_relationship_parameter.selectRow(index.row())
        global_pos = self.ui.tableView_relationship_parameter.viewport().mapToGlobal(pos)
        self.relationship_parameter_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.relationship_parameter_context_menu.get_action()
        if option == "Remove parameter":
            self.remove_parameter(index)
        self.relationship_parameter_context_menu.deleteLater()
        self.relationship_parameter_context_menu = None

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_parameter")
    def update_parameter(self, editor, hint):
        """Update parameter table with newly edited data.
        If successful, also update item in the model.
        """
        index = editor.index
        proxy_model = index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        header = source_model.header
        id_column = header.index('parameter_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_id = sibling.data()
        field_name = header[index.column()]
        if field_name == 'parameter_name':
            field_name = 'name'
        new_value = editor.text()
        try:
            self.mapping.update_parameter(parameter_id, field_name, new_value)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        source_model.setData(source_index, new_value)
        msg = "Parameter succesfully updated."
        self.msg.emit(msg)
        self.init_parameter_models()
        # refresh parameter value models to reflect name change
        if field_name == 'name':
            self.init_parameter_value_models()

    def remove_parameter(self, proxy_index):
        """Remove row from (object or relationship) parameter table.
        If succesful, also remove row from model"""
        proxy_model = proxy_index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(proxy_index)
        id_column = source_model.header.index('parameter_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_id = sibling.data()
        try:
            self.mapping.remove_parameter(parameter_id)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        source_model.removeRows(source_index.row(), 1)
        self.init_parameter_value_models()

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("mainWindow/windowSize")
        window_pos = self.qsettings.value("mainWindow/windowPosition")
        splitter_tree_parameter_state = self.qsettings.value("mainWindow/splitterTreeParameterState")
        window_maximized = self.qsettings.value("mainWindow/windowMaximized", defaultValue='false')  # returns string
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if splitter_tree_parameter_state:
            self.ui.splitter_tree_parameter.restoreState(splitter_tree_parameter_state)

    @Slot(name="close_session")
    def close_session(self):
        """Close this form without commiting any changes."""
        self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if self._data_store is not None:
            self._data_store.destroyed.disconnect(self.data_store_destroyed)
        # save qsettings
        self.qsettings.setValue("mainWindow/splitterTreeParameterState", self.ui.splitter_tree_parameter.saveState())
        self.qsettings.setValue("mainWindow/windowSize", self.size())
        self.qsettings.setValue("mainWindow/windowPosition", self.pos())
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("mainWindow/windowMaximized", True)
        else:
            self.qsettings.setValue("mainWindow/windowMaximized", False)
        self.mapping.close()
        if event:
            event.accept()
