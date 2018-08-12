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
            data_store (DataStore): the DataStore instance that owns this form
            mapping (DatabaseMapping): The object that holds the object relation mapping
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
        self.mapping.set_parent(self)
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
        # context menus
        self.object_tree_context_menu = None
        self.object_parameter_value_context_menu = None
        self.relationship_parameter_value_context_menu = None
        self.object_parameter_context_menu = None
        self.relationship_parameter_context_menu = None
        # init models and views
        self.default_font_height = QFontMetrics(QFont("", 0)).lineSpacing()
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
        self.ui.treeView_object.selectionModel().currentChanged.connect(self.filter_parameter_value_models)
        self.ui.treeView_object.selectionModel().currentChanged.connect(self.filter_parameter_models)
        self.ui.treeView_object.editKeyPressed.connect(self.rename_item)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.tree_index_double_click)
        # Parameter tables
        self.ui.tableView_object_parameter_value.customContextMenuRequested.\
            connect(self.show_object_parameter_value_context_menu)
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.\
            connect(self.show_relationship_parameter_value_context_menu)
        self.ui.tableView_object_parameter.customContextMenuRequested.\
            connect(self.show_object_parameter_context_menu)
        self.ui.tableView_relationship_parameter.customContextMenuRequested.\
            connect(self.show_relationship_parameter_context_menu)
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
        self.mapping.commit_session(dialog.commit_msg)

    @Slot(name="rollback_session")
    def rollback_session(self):
        self.mapping.rollback_session()
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_models()
        # clear filters
        self.object_parameter_value_proxy.clear_filter()
        self.relationship_parameter_value_proxy.clear_filter()

    def init_object_tree_model(self):
        """Initialize object tree model."""
        root_item = self.object_tree_model.init_model(self.database)
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
        object_parameter_value = [list(row._asdict().values()) for row in object_parameter_value_list]
        self.object_parameter_value_model.header = [column['name'] for column in header]
        self.object_parameter_value_model.reset_model(object_parameter_value)
        self.object_parameter_value_proxy.setSourceModel(self.object_parameter_value_model)
        # Relationship
        relationship_parameter_value_list = self.mapping.relationship_parameter_value_list()
        header = relationship_parameter_value_list.column_descriptions
        self.relationship_parameter_value_model.header = [column['name'] for column in header]
        relationship_parameter_value = [list(row._asdict().values()) for row in relationship_parameter_value_list]
        self.relationship_parameter_value_model.reset_model(relationship_parameter_value)
        self.relationship_parameter_value_proxy.setSourceModel(self.relationship_parameter_value_model)

    def init_parameter_models(self):
        """Initialize parameter (definition) models from source database."""
        # Object
        object_parameter_list = self.mapping.object_parameter_list()
        header = object_parameter_list.column_descriptions
        self.object_parameter_model.header = [column['name'] for column in header]
        if object_parameter_list.all():
            object_parameter = [list(row._asdict().values()) for row in object_parameter_list]
            self.object_parameter_model.reset_model(object_parameter)
            self.object_parameter_proxy.setSourceModel(self.object_parameter_model)
        # Relationship
        relationship_parameter_list = self.mapping.relationship_parameter_list()
        header = relationship_parameter_list.column_descriptions
        self.relationship_parameter_model.header = [column['name'] for column in header]
        if relationship_parameter_list.all():
            relationship_parameter = [list(row._asdict().values()) for row in relationship_parameter_list]
            self.relationship_parameter_model.reset_model(relationship_parameter)
        self.relationship_parameter_proxy.setSourceModel(self.relationship_parameter_model)

    def init_parameter_value_views(self):
        self.init_object_parameter_value_view()
        self.init_relationship_parameter_value_view()

    def init_object_parameter_value_view(self):
        """Init the object parameter table view.
        """
        header = self.object_parameter_value_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_object_parameter_value.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_value.verticalHeader().\
            setDefaultSectionSize(self.default_font_height)
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
        """Init the relationship parameter table view.
        """
        header = self.relationship_parameter_value_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_relationship_parameter_value.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_value.verticalHeader().\
            setDefaultSectionSize(self.default_font_height)
        # set model
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_proxy)
        # hide id columns
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("relationship_class_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("parent_relationship_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("parent_object_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("child_object_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("relationship_id"))
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
        """Init the object parameter table view.
        """
        header = self.object_parameter_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_object_parameter.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter.verticalHeader().\
            setDefaultSectionSize(self.default_font_height)
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
        """Init the object parameter table view.
        """
        header = self.relationship_parameter_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_relationship_parameter.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter.verticalHeader().\
            setDefaultSectionSize(self.default_font_height)
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

    @Slot("QModelIndex", name="tree_index_double_click")
    def tree_index_double_click(self, index):
        """Handle double clicking on the object treeView."""
        if not index.isValid():
            return # just to be safe
        clicked_type = index.data(Qt.UserRole)
        if not clicked_type:  # root item
            return
        if not clicked_type.endswith('object'):
            return
        clicked_item = index.model().itemFromIndex(index)
        if clicked_item.hasChildren():
            return
        self.expand_at_top_level(index)

    def expand_at_top_level(self, index):
        """Expand object at the top level."""
        clicked_object = index.data(Qt.UserRole+1)
        root_item = index.model().invisibleRootItem().child(0)
        found_object_class_item = None
        for i in range(root_item.rowCount()):
            object_class_item = root_item.child(i)
            object_class = object_class_item.data(Qt.UserRole+1)
            if object_class['id'] == clicked_object['class_id']:
                found_object_class_item = object_class_item
                break
        if not found_object_class_item:
            return
        for j in range(found_object_class_item.rowCount()):
            object_item = found_object_class_item.child(j)
            object_ = object_item.data(Qt.UserRole+1)
            if object_['id'] == clicked_object['id']:
                object_index = index.model().indexFromItem(object_item)
                self.ui.treeView_object.setCurrentIndex(object_index)
                self.ui.treeView_object.scrollTo(object_index)
                self.ui.treeView_object.expand(object_index)
                return

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_value_models(self, current, previous):
        """Populate tableViews whenever an object item is selected in the treeView"""
        # TODO: try to make it more sparse
        # logging.debug("filter_parameter_value_models")
        self.object_parameter_value_proxy.clear_filter()
        self.relationship_parameter_value_proxy.clear_filter()
        clicked_type = current.data(Qt.UserRole)
        # filter rows and bold name
        if clicked_type == 'object_class': # show all objects of this class
            object_class_id = current.data(Qt.UserRole+1)['id']
            self.object_parameter_value_proxy.object_class_id_filter = object_class_id
        elif clicked_type == 'object': # show only this object
            object_id = current.data(Qt.UserRole+1)['id']
            object_name = current.data(Qt.UserRole+1)['name']
            self.object_parameter_value_proxy.object_id_filter = object_id
            self.relationship_parameter_value_proxy.object_id_filter = object_id
            self.relationship_parameter_value_proxy.bold_name = object_name
        elif clicked_type == 'relationship_class':
            # show all related objects to this parent object, through this relationship class
            parent_object_id = current.parent().data(Qt.UserRole+1)['id']
            relationship_class_id = current.data(Qt.UserRole+1)['id']
            relationship_class_name = current.data(Qt.UserRole+1)['name']
            self.relationship_parameter_value_proxy.object_id_filter = parent_object_id
            self.relationship_parameter_value_proxy.relationship_class_id_filter = relationship_class_id
            self.relationship_parameter_value_proxy.bold_name = relationship_class_name
        elif clicked_type == 'related_object':
            # show only this object and this relationship
            object_id = current.data(Qt.UserRole+1)['id']
            object_name = current.data(Qt.UserRole+1)['name']
            relationship_id = current.data(Qt.UserRole+1)['relationship_id']
            self.object_parameter_value_proxy.object_id_filter = object_id
            self.relationship_parameter_value_proxy.relationship_id_filter = relationship_id
            self.relationship_parameter_value_proxy.bold_name = object_name
        elif clicked_type == 'meta_relationship_class':
            # show all related objects to this parent relationship, through this meta-relationship class
            parent_relationship_id = current.parent().data(Qt.UserRole+1)['relationship_id']
            relationship_class_id = current.data(Qt.UserRole+1)['id']
            relationship_class_name = current.data(Qt.UserRole+1)['name']
            self.relationship_parameter_value_proxy.parent_relationship_id_filter = parent_relationship_id
            self.relationship_parameter_value_proxy.relationship_class_id_filter = relationship_class_id
            self.relationship_parameter_value_proxy.bold_name = relationship_class_name
        # filter columns in relationship parameter value model
        header = self.relationship_parameter_value_model.header
        if header:
            if clicked_type == 'object':
                self.relationship_parameter_value_proxy.hide_column = header.index("parent_relationship_name")
            elif clicked_type == 'relationship_class':
                self.relationship_parameter_value_proxy.hide_column = header.index("parent_relationship_name")
            elif clicked_type == 'related_object':
                relationship_class_type = current.parent().data(Qt.UserRole)
                if relationship_class_type == 'meta_relationship_class': # hide parent_object_name
                    self.relationship_parameter_value_proxy.hide_column = header.index("parent_object_name")
                elif relationship_class_type == 'relationship_class': # hide parent_relationship_name
                    self.relationship_parameter_value_proxy.hide_column = header.index("parent_relationship_name")
            elif clicked_type == 'meta_relationship_class':
                self.relationship_parameter_value_proxy.hide_column = header.index("parent_object_name")
        # trick to trigger filtering
        self.object_parameter_value_proxy.setFilterRegExp("")
        self.relationship_parameter_value_proxy.setFilterRegExp("")

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, current, previous):
        """Populate tableViews whenever an object item is selected in the treeView"""
        # logging.debug("filter_parameter_models")
        self.object_parameter_proxy.clear_filter()
        self.relationship_parameter_proxy.clear_filter()
        clicked_type = current.data(Qt.UserRole)
        # filter rows
        if clicked_type == 'object_class': # show only this class
            object_class_id = current.data(Qt.UserRole+1)['id']
            self.object_parameter_proxy.object_class_id_filter = object_class_id
        elif clicked_type == 'object': # show only this object's class
            object_class_id = current.data(Qt.UserRole+1)['class_id']
            self.object_parameter_proxy.object_class_id_filter = object_class_id
        elif clicked_type and clicked_type.endswith('relationship_class'):
            relationship_class_id = current.data(Qt.UserRole+1)['id']
            self.relationship_parameter_proxy.relationship_class_id_filter = relationship_class_id
        elif clicked_type == 'related_object':
            relationship_class_id = current.parent().data(Qt.UserRole+1)['id']
            self.relationship_parameter_proxy.relationship_class_id_filter = relationship_class_id
        # trick to trigger filtering
        self.object_parameter_proxy.setFilterRegExp("")
        self.relationship_parameter_proxy.setFilterRegExp("")
        # resize columns
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
        elif option == "Expand at top level":
            self.expand_at_top_level(index)
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
        parent_class_type = index.data(Qt.UserRole)
        parent_class_id = index.data(Qt.UserRole+1)['id']
        if parent_class_type == 'object_class':
            self.add_relationship_classes(parent_object_class_id=parent_class_id)
        elif parent_class_type.endswith('relationship_class'):
            self.add_relationship_classes(parent_relationship_class_id=parent_class_id)

    def call_add_relationships(self, index):
        relationship_class = index.data(Qt.UserRole+1)
        class_id = relationship_class['id']
        parent_relationship_id = None
        parent_object_id = None
        child_object_id = None
        top_object_type = index.parent().data(Qt.UserRole)
        top_object = index.parent().data(Qt.UserRole+1)
        if top_object_type == 'object':
            top_object_class_id = top_object['class_id']
            if top_object_class_id == relationship_class['parent_object_class_id']:
                parent_object_id = top_object['id']
            elif top_object_class_id == relationship_class['child_object_class_id']:
                child_object_id = top_object['id']
        elif top_object_type == 'related_object':
            parent_relationship_id = top_object['relationship_id']
        self.add_relationships(
            class_id=class_id,
            parent_relationship_id=parent_relationship_id,
            parent_object_id=parent_object_id,
            child_object_id=child_object_id
        )

    def call_add_parameters(self, tree_index):
        class_type = tree_index.data(Qt.UserRole)
        class_id = tree_index.data(Qt.UserRole+1)['id']
        if class_type == 'object_class':
            self.add_parameters(object_class_id=class_id)
        elif class_type.endswith('relationship_class'):
            self.add_parameters(relationship_class_id=class_id)

    def call_add_parameter_values(self, tree_index):
        class_id = tree_index.parent().data(Qt.UserRole+1)['id']
        entity_type = tree_index.data(Qt.UserRole)
        if entity_type == 'object':
            object_id = tree_index.data(Qt.UserRole+1)['id']
            self.add_parameter_values(object_class_id=class_id, object_id=object_id)
        elif entity_type == 'related_object':
            relationship_id = tree_index.data(Qt.UserRole+1)['relationship_id']
            self.add_parameter_values(relationship_class_id=class_id, relationship_id=relationship_id)

    @Slot(name="add_object_classes")
    def add_object_classes(self):
        """Insert new object classes."""
        dialog = AddObjectClassesDialog(self, self.mapping)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for object_class_args in dialog.object_class_args_list:
            object_class = self.mapping.add_object_class(**object_class_args)
            if object_class:
                self.add_object_class_to_model(object_class.__dict__)

    def add_object_class_to_model(self, object_class):
        """Add object class item to the object tree model.

        Args:
            object_class (dict)
        """
        object_class_item = self.object_tree_model.add_object_class(object_class)
        # Add new item to root item at convenient position
        root_item = self.object_tree_model.invisibleRootItem().child(0)
        row = root_item.rowCount()
        for i in range(root_item.rowCount()):
            visited_object_class_item = root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole+1)
            if visited_object_class['display_order'] > object_class['display_order']:
                row = i
                break
        root_item.insertRow(row, QStandardItem())
        root_item.setChild(row, 0, object_class_item)
        # scroll to newly inserted item in treeview
        object_class_index = self.object_tree_model.indexFromItem(object_class_item)
        self.ui.treeView_object.setCurrentIndex(object_class_index)
        self.ui.treeView_object.scrollTo(object_class_index)

    @Slot(name="add_objects")
    def add_objects(self, class_id=None):
        """Insert new objects."""
        dialog = AddObjectsDialog(self, self.mapping, class_id=class_id)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for object_args in dialog.object_args_list:
            object_ = self.mapping.add_object(**object_args)
            if object_:
                self.add_object_to_model(object_.__dict__)

    def add_object_to_model(self, object_):
        """Add object item to the object tree model.

        Args:
            object_ (dict)
        """
        # find object class item among the children of the root
        root_item = self.object_tree_model.invisibleRootItem().child(0)
        object_class_item = None
        for i in range(root_item.rowCount()):
            visited_object_class_item = root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole+1)
            if visited_object_class['id'] == object_['class_id']:
                object_class_item = visited_object_class_item
                break
        if not object_class_item:
            self.msg.emit("Object class item not found in model. This is probably a bug.")
            return
        # get relationship classes involving the present class
        relationship_class_as_parent_list = self.mapping.relationship_class_list(
            parent_object_class_id=object_['class_id'])
        relationship_class_as_child_list = self.mapping.relationship_class_list(
            child_object_class_id=object_['class_id'])
        object_item = self.object_tree_model.add_object(object_, relationship_class_as_parent_list,
            relationship_class_as_child_list)
        object_class_item.appendRow(object_item)
        # scroll to newly inserted item in treeview
        object_index = self.object_tree_model.indexFromItem(object_item)
        self.ui.treeView_object.setCurrentIndex(object_index)
        self.ui.treeView_object.scrollTo(object_index)

    @Slot(name="add_relationship_classes")
    def add_relationship_classes(self, parent_relationship_class_id=None, parent_object_class_id=None):
        """Insert new relationship class."""
        dialog = AddRelationshipClassesDialog(self, self.mapping,
            parent_relationship_class_id=parent_relationship_class_id,
            parent_object_class_id=parent_object_class_id)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for relationship_class_args in dialog.relationship_class_args_list:
            relationship_class = self.mapping.add_relationship_class(**relationship_class_args)
            if relationship_class:
                self.add_relationship_class_to_model(relationship_class.__dict__)

    def add_relationship_class_to_model(self, relationship_class):
        """Add relationship class item to object tree model.

        Args:
            relationship_class (dict): the relationship class to add
        """
        if 'parent_object_class_id' in relationship_class:
            self.object_tree_model.visit_and_add_relationship_class(relationship_class)
        elif 'parent_relationship_class_id' in relationship_class:
            self.object_tree_model.visit_and_add_meta_relationship_class(relationship_class)

    @Slot(name="add_relationships")
    def add_relationships(self, class_id=None, parent_relationship_id=None, parent_object_id=None,
            child_object_id=None):
        """Insert new relationship."""
        dialog = AddRelationshipsDialog(
            self,
            self.mapping,
            class_id=class_id,
            parent_relationship_id=parent_relationship_id,
            parent_object_id=parent_object_id,
            child_object_id=child_object_id
        )
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for relationship_args in dialog.relationship_args_list:
            relationship = self.mapping.add_relationship(**relationship_args)
            if relationship:
                self.add_relationship_to_model(relationship.__dict__)

    def add_relationship_to_model(self, relationship):
        """Add relationship item to object tree model.

        Args:
            relationship (dict): the relationship to add
        """
        meta_relationship_class_list = self.mapping.meta_relationship_class_list(
            parent_relationship_class_id=relationship['class_id'])
        if 'parent_object_id' in relationship:
            self.object_tree_model.visit_and_add_relationship(relationship,
                meta_relationship_class_list)
        elif 'parent_relationship_id' in relationship:
            self.object_tree_model.visit_and_add_meta_relationship(relationship,
                meta_relationship_class_list)

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
            parameter = self.mapping.add_parameter(**parameter_args)
            if parameter:
                self.add_parameter_to_model(parameter.__dict__)

    def add_parameter_to_model(self, parameter):
        """Add parameter item to the object or relationship parameter model.

        Args:
            parameter (dict)
        """
        self.init_parameter_models()
        # Scroll to concerned row in object parameter table
        if 'object_class_id' in parameter:
            self.ui.tableView_object_parameter.resizeColumnsToContents()
            source_row = self.object_parameter_model.rowCount()-1
            source_column = self.object_parameter_model.header.index("parameter_name")
            source_index = self.object_parameter_model.index(source_row, source_column)
            proxy_index = self.object_parameter_proxy.mapFromSource(source_index)
            self.ui.tabWidget_object.setCurrentIndex(1)
            self.ui.tableView_object_parameter.setCurrentIndex(proxy_index)
            self.ui.tableView_object_parameter.scrollTo(proxy_index)
        # Scroll to concerned row in relationship parameter table
        elif 'relationship_class_id' in parameter:
            self.ui.tableView_relationship_parameter.resizeColumnsToContents()
            source_row = self.relationship_parameter_model.rowCount()-1
            source_column = self.relationship_parameter_model.header.index("parameter_name")
            source_index = self.relationship_parameter_model.index(source_row, source_column)
            proxy_index = self.relationship_parameter_proxy.mapFromSource(source_index)
            self.ui.tabWidget_relationship.setCurrentIndex(1)
            self.ui.tableView_relationship_parameter.setCurrentIndex(proxy_index)
            self.ui.tableView_relationship_parameter.scrollTo(proxy_index)
        # Scroll to concerned object class in treeview if necessary
        if 'object_class_id' in parameter:
            current_index = self.ui.treeView_object.currentIndex()
            current_type = current_index.data(Qt.UserRole)
            if current_type == 'object_class':
                current_id = current_index.data(Qt.UserRole+1)['id']
                if current_id == parameter['object_class_id']:
                    return  # We're already in the right one
            # Search it and scroll to it
            for item in self.object_tree_model.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                item_type = item.data(Qt.UserRole)
                if not item_type: # root
                    continue
                item_id = item.data(Qt.UserRole+1)['id']
                if item_type == 'object_class' and item_id == parameter['object_class_id']:
                    object_class_index = self.object_tree_model.indexFromItem(item)
                    self.ui.treeView_object.setCurrentIndex(object_class_index)
                    self.ui.treeView_object.scrollTo(object_class_index)
                    break
        # Scroll to concerned relationship class in treeview if necessary
        elif 'relationship_class_id' in parameter:
            current_index = self.ui.treeView_object.currentIndex()
            current_type = current_index.data(Qt.UserRole)
            if current_type.endswith('relationship_class'):
                current_id = current_index.data(Qt.UserRole+1)['id']
                if current_id == parameter['relationship_class_id']:
                    return  # We're already in the right one
            # Search the first one that matches and scroll to it
            for item in self.object_tree_model.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                item_type = item.data(Qt.UserRole)
                if not item_type: # root
                    continue
                item_id = item.data(Qt.UserRole+1)['id']
                if item_type.endswith('relationship_class') and item_id == parameter['relationship_class_id']:
                    relationship_class_index = self.object_tree_model.indexFromItem(item)
                    self.ui.treeView_object.setCurrentIndex(relationship_class_index)
                    self.ui.treeView_object.scrollTo(relationship_class_index)
                    break

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
            parameter_value = self.mapping.add_parameter_value(**parameter_value_args)
            if parameter_value:
                self.add_parameter_value_to_model(parameter_value.__dict__)

    def add_parameter_value_to_model(self, parameter_value):
        """Add parameter value item to the object or relationship parameter value model.

        Args:
            parameter_value (dict)
        """
        self.init_parameter_value_models()
        # Scroll to concerned row in object parameter value table
        if 'object_id' in parameter_value:
            self.ui.tableView_object_parameter_value.resizeColumnsToContents()
            source_row = self.object_parameter_value_model.rowCount()-1
            source_column = self.object_parameter_value_model.header.index("parameter_name")
            source_index = self.object_parameter_value_model.index(source_row, source_column)
            proxy_index = self.object_parameter_value_proxy.mapFromSource(source_index)
            self.ui.tabWidget_object.setCurrentIndex(0)
            self.ui.tableView_object_parameter_value.setCurrentIndex(proxy_index)
            self.ui.tableView_object_parameter_value.scrollTo(proxy_index)
        # Scroll to concerned row in relationship parameter value table
        elif 'relationship_id' in parameter_value:
            self.relationship_parameter_proxy.setFilterRegExp("")
            self.ui.tableView_relationship_parameter.resizeColumnsToContents()
            source_row = self.relationship_parameter_model.rowCount()-1
            source_column = self.relationship_parameter_model.header.index("parameter_name")
            source_index = self.relationship_parameter_model.index(source_row, source_column)
            proxy_index = self.relationship_parameter_proxy.mapFromSource(source_index)
            self.ui.tabWidget_relationship.setCurrentIndex(0)
            self.ui.tableView_relationship_parameter.setCurrentIndex(proxy_index)
            self.ui.tableView_relationship_parameter.scrollTo(proxy_index)
        # Scroll to concerned object in treeview if necessary
        if 'object_id' in parameter_value:
            current_index = self.ui.treeView_object.currentIndex()
            current_type = current_index.data(Qt.UserRole)
            if current_type == 'object':
                current_id = current_index.data(Qt.UserRole+1)['id']
                if current_id == parameter_value['object_id']:
                    return  # We're already in the right one
            # Search it and scroll to it
            for item in self.object_tree_model.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                item_type = item.data(Qt.UserRole)
                if not item_type: # root
                    continue
                if item_type != 'object':
                    continue
                item_id = item.data(Qt.UserRole+1)['id']
                if item_id == parameter_value['object_id']:
                    object_index = self.object_tree_model.indexFromItem(item)
                    self.ui.treeView_object.setCurrentIndex(object_index)
                    self.ui.treeView_object.scrollTo(object_index)
                    break
        # Scroll to concerned related_object in treeview if necessary
        elif 'relationship_id' in parameter_value:
            current_index = self.ui.treeView_object.currentIndex()
            current_type = current_index.data(Qt.UserRole)
            if current_type == 'related_object':
                current_relationship_id = current_index.data(Qt.UserRole+1)['relationship_id']
                if current_relationship_id == parameter_value['relationship_id']:
                    return  # We're already in the right one
            # Search the first one that matches and scroll to it
            for item in self.object_tree_model.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                item_type = item.data(Qt.UserRole)
                if not item_type: # root
                    continue
                if item_type != 'related_object':
                    continue
                item_relationship_id = item.data(Qt.UserRole+1)['relationship_id']
                if item_relationship_id == parameter_value['relationship_id']:
                    relationship_index = self.object_tree_model.indexFromItem(item)
                    self.ui.treeView_object.setCurrentIndex(relationship_index)
                    self.ui.treeView_object.scrollTo(relationship_index)
                    break

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
        # Get renamed instance
        renamed_type = renamed_item.data(Qt.UserRole)
        renamed = renamed_item.data(Qt.UserRole+1)
        if renamed_type == 'object_class':
            renamed_instance = self.mapping.rename_object_class(renamed['id'], new_name)
        elif renamed_type.endswith('object'):
            renamed_instance = self.mapping.rename_object(renamed['id'], new_name)
        elif renamed_type.endswith('relationship_class'):
            renamed_instance = self.mapping.rename_relationship_class(renamed['id'], new_name)
        else:
            return # should never happen
        if not renamed_instance:
            return
        self.object_tree_model.visit_and_rename(new_name, curr_name, renamed_type, renamed['id'])
        self.init_parameter_value_models()
        self.init_parameter_models()

    def remove_item(self, removed_index):
        """Remove item from the treeview"""
        removed_item = self.object_tree_model.itemFromIndex(removed_index)
        removed_type = removed_item.data(Qt.UserRole)
        removed = removed_item.data(Qt.UserRole+1)
        # Get removed id
        if removed_type == 'related_object':
            removed_id = removed['relationship_id']
        else:
            removed_id = removed['id']
        # Get removed instance
        if removed_type == 'object_class':
            removed_instance = self.mapping.remove_object_class(id=removed_id)
        elif removed_type == 'object':
            removed_instance = self.mapping.remove_object(id=removed_id)
        elif removed_type.endswith('relationship_class'):
            removed_instance = self.mapping.remove_relationship_class(id=removed_id)
        elif removed_type == 'related_object':
            removed_instance = self.mapping.remove_relationship(id=removed_id)
        else:
            return # should never happen
        if not removed_instance:
            return
        self.object_tree_model.visit_and_remove(removed_type, removed_id)
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
        if self.mapping.update_parameter_value(parameter_value_id, field_name, new_value):
            source_model.setData(source_index, new_value)

    def remove_parameter_value(self, proxy_index):
        """Remove row from (object or relationship) parameter_value table.
        If succesful, also remove row from model"""
        proxy_model = proxy_index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(proxy_index)
        id_column = source_model.header.index('parameter_value_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_value_id = sibling.data()
        if self.mapping.remove_parameter_value(parameter_value_id):
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
        if self.mapping.update_parameter(parameter_id, field_name, new_value):
            source_model.setData(source_index, new_value)
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
        if self.mapping.remove_parameter(parameter_id):
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
