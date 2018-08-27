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
Widget shown to user when opening a 'datapackage.json' file
in Data Connection item.

:author: Manuel Marin <manuelma@kth.se>
:date:   7.7.2018
"""

from config import STATUSBAR_SS
from ui.spine_datapackage_form import Ui_MainWindow
from widgets.combobox_delegate import ComboBoxDelegate, CheckableComboBoxDelegate
from widgets.lineedit_delegate import LineEditDelegate
from widgets.checkbox_delegate import CheckBoxDelegate
from widgets.custom_menus import DescriptorTreeContextMenu
from PySide2.QtWidgets import QMainWindow, QHeaderView, QMessageBox
from PySide2.QtCore import Qt, Signal, Slot, QSettings
from models import MinimalTableModel, DatapackageResourcesModel, DatapackageFieldsModel, DatapackageForeignKeysModel
from spinedatabase_api import OBJECT_CLASS_NAMES


class SpineDatapackageWidget(QMainWindow):
    """A widget to allow user to edit a datapackage and convert it
    to a Spine database in SQLite.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        data_connection (DataConnection): Data Connection associated to this widget
        datapackage (CustomPackage): Datapackage to load and use
    """

    msg = Signal(str, name="msg")
    msg_error = Signal(str, str, str, name="msg_error")

    def __init__(self, parent, data_connection, datapackage):
        """Initialize class."""
        super().__init__(flags=Qt.Window)
        self._parent = parent
        self._data_connection = data_connection
        self.object_class_name_list = OBJECT_CLASS_NAMES
        self.datapackage = datapackage
        self.descriptor_tree_context_menu = None
        self.selected_resource_name = None
        self.resource_tables = dict()
        self.resources_model = DatapackageResourcesModel(self)
        self.fields_model = DatapackageFieldsModel(self)
        self.foreign_keys_model = DatapackageForeignKeysModel(self)
        self.resource_data_model = MinimalTableModel()
        #  Set up the user interface from Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox datapackage form")
        self.restore_ui()
        self.ui.toolButton_insert_foreign_key.setDefaultAction(self.ui.actionInsert_foreign_key)
        self.ui.toolButton_remove_foreign_keys.setDefaultAction(self.ui.actionRemove_foreign_keys)
        self.load_resource_data()
        # Add status bar to form
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Set name of export action
        self.ui.treeView_resources.setModel(self.resources_model)
        self.ui.treeView_fields.setModel(self.fields_model)
        self.ui.treeView_foreign_keys.setModel(self.foreign_keys_model)
        self.ui.tableView_resource_data.setModel(self.resource_data_model)
        self.ui.treeView_resources.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.treeView_fields.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.treeView_foreign_keys.header().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_resource_data.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_resource_data.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.connect_signals()
        self.resources_model.reset_model(self.datapackage)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        # Message actions
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        # DC destroyed
        self._data_connection.destroyed.connect(self.close)
        # Delegates
        # Resource data
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_resource_data)
        self.ui.tableView_resource_data.setItemDelegate(lineedit_delegate)
        # Resource name
        combobox_delegate = ComboBoxDelegate(self)
        combobox_delegate.closeEditor.connect(self.update_resource_name)
        self.ui.treeView_resources.setItemDelegateForColumn(0, combobox_delegate)
        # Field name
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_field_name)
        self.ui.treeView_fields.setItemDelegateForColumn(0, lineedit_delegate)
        # Primary key
        checkbox_delegate = CheckBoxDelegate(self)
        checkbox_delegate.commit_data.connect(self.update_primary_key)
        self.ui.treeView_fields.setItemDelegateForColumn(2, checkbox_delegate)
        self.ui.tableView_resource_data.setItemDelegate(lineedit_delegate)
        # Foreign key fields, ref resource,
        combobox_delegate = CheckableComboBoxDelegate(self)
        combobox_delegate.closeEditor.connect(self.update_foreign_key_fields)
        self.ui.treeView_foreign_keys.setItemDelegateForColumn(0, combobox_delegate)
        combobox_delegate = ComboBoxDelegate(self)
        combobox_delegate.closeEditor.connect(self.update_foreign_key_ref_resource)
        self.ui.treeView_foreign_keys.setItemDelegateForColumn(1, combobox_delegate)
        combobox_delegate = CheckableComboBoxDelegate(self)
        combobox_delegate.closeEditor.connect(self.update_foreign_key_ref_fields)
        self.ui.treeView_foreign_keys.setItemDelegateForColumn(2, combobox_delegate)
        # Selected resource changed
        self.ui.treeView_resources.selectionModel().selectionChanged.connect(self.filter_resource_data)
        # Actions
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        self.ui.actionInsert_foreign_key.triggered.connect(self.insert_foreign_key_row)
        self.ui.actionRemove_foreign_keys.triggered.connect(self.remove_foreign_key_rows)
        # Rows inserted
        self.resources_model.rowsInserted.connect(self.setup_new_resource_row)
        self.foreign_keys_model.rowsInserted.connect(self.setup_new_foreign_key_row)

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("mainWindow/windowSize")
        window_pos = self.qsettings.value("mainWindow/windowPosition")
        splitter_state = self.qsettings.value("mainWindow/splitterState")
        window_maximized = self.qsettings.value("mainWindow/windowMaximized", defaultValue='false')
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if splitter_state:
            self.ui.splitter.restoreState(splitter_state)

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Append regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        current_msg = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(current_msg + " " + msg, 5000)

    @Slot(str, str, str, name="add_error_message")
    def add_error_message(self, title, text, info=None):
        """Show error message in message box.

        Args:
            msg (str): String to show in QMessageBox
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        if info:
            msg_box.setInformativeText(info)
        msg_box.exec_()

    @Slot("QModelIndex", "int", "int", name="setup_new_resource_row")
    def setup_new_resource_row(self, parent, first, last):
        index = self.resources_model.index(first, 0, parent)
        self.resources_model.setData(index, self.object_class_name_list, Qt.UserRole)
        self.check_resource_name(index)

    @Slot("QModelIndex", "int", "int", name="setup_new_foreign_key_row")
    def setup_new_foreign_key_row(self, parent, first, last):
        index = self.foreign_keys_model.index(first, 0, parent)
        field_names = self.datapackage.get_resource(self.selected_resource_name).schema.field_names
        self.foreign_keys_model.setData(index, field_names, Qt.UserRole)
        resource_names = self.datapackage.resource_names
        self.foreign_keys_model.setData(index.sibling(index.row(), 1), resource_names, Qt.UserRole)

    def check_resource_name(self, index):
        name = index.data(Qt.DisplayRole)
        if name in self.object_class_name_list:
            self.resources_model.set_name_valid(index, True)
        else:
            self.resources_model.set_name_valid(index, False)

    def load_resource_data(self):
        """Load resource data into a local list of tables."""
        for resource in self.datapackage.resources:
            self.resource_tables[resource.name] = resource.read(cast=False)

    @Slot(name="save_datapackage")
    def save_datapackage(self):  # TODO: handle zip as well?
        """Save datapackage.json to datadir."""
        self._data_connection.save_datapackage(self.datapackage)

    @Slot("QModelIndex", "QModelIndex", name="filter_resource_data")
    def filter_resource_data(self, selected, deselected):
        """Filter resource data whenever a new resource is selected."""
        try:
            new_selected_resource_name = selected.indexes()[0].data(Qt.DisplayRole)
        except IndexError:
            return
        if self.selected_resource_name == new_selected_resource_name:  # selected resource not changed
            return
        self.selected_resource_name = new_selected_resource_name
        self.reset_resource_data_model()
        schema = self.datapackage.get_resource(self.selected_resource_name).schema
        self.fields_model.reset_model(schema)
        self.foreign_keys_model.reset_model(schema)

    def reset_resource_data_model(self):
        """Reset resource data model with data from newly selected resource."""
        table = self.resource_tables[self.selected_resource_name]
        field_names = self.datapackage.get_resource(self.selected_resource_name).schema.field_names
        self.resource_data_model.set_horizontal_header_labels(field_names)
        self.resource_data_model.reset_model(table)
        self.ui.tableView_resource_data.resizeColumnsToContents()

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_resource_data")
    def update_resource_data(self, editor, hint):
        # TODO: Slot line has 3 arguments but def line has only 2 (editor and hint). Which one is correct?
        """Update resource data with newly edited data."""
        index = editor.index
        new_value = editor.text()
        if not self.resource_data_model.setData(index, new_value, Qt.EditRole):
            return
        self.ui.tableView_resource_data.resizeColumnsToContents()
        self.resource_tables[self.selected_resource_name][index.row()][index.column()] = new_value

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_resource_name")
    def update_resource_name(self, editor, hint):
        # TODO: Slot line has 3 arguments but def line has only 2 (editor and hint). Which one is correct?
        """Update resources model and descriptor with new resource name."""
        new_name = editor.currentText()
        if not new_name:
            return
        index = editor.index
        old_name = index.data(Qt.DisplayRole)
        if not self.resources_model.setData(index, new_name, Qt.EditRole):
            return
        self.check_resource_name(index)
        resource_data = self.resource_tables.pop(self.selected_resource_name, None)
        if resource_data is None:
            msg = "Couldn't find key in resource data dict. Something is wrong."
            self.msg.emit(msg)
            return
        self.resource_tables[new_name] = resource_data
        self.selected_resource_name = new_name
        self.datapackage.rename_resource(old_name, new_name)

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_resource_data")
    def update_field_name(self, editor, hint):
        # TODO: Slot line has 3 arguments but def line has only 2 (editor and hint). Which one is correct?
        """Called when line edit delegate wants to edit field name data.
        Update name in fields_model, resource_data_model's header and datapackage descriptor.
        """
        index = editor.index
        new_name = editor.text()
        # Save old name to look up field
        old_name = index.data(Qt.DisplayRole)
        if not self.fields_model.setData(index, new_name, Qt.EditRole):
            return
        header = self.resource_data_model.header
        section = header.index(old_name)
        header[section] = new_name
        self.ui.tableView_resource_data.resizeColumnsToContents()
        self.datapackage.rename_field(self.selected_resource_name, old_name, new_name)

    @Slot("QModelIndex", name="update_primary_key")
    def update_primary_key(self, index):
        # TODO: Should 'name' be in arguments?
        """Called when checkbox delegate wants to edit primary key data.
        Add or remove primary key field accordingly.
        """
        status = index.data(Qt.EditRole)
        field_name = index.sibling(index.row(), 0).data(Qt.DisplayRole)
        if status is False:  # Add to primary key
            self.fields_model.setData(index, True, Qt.EditRole)
            self.datapackage.append_to_primary_key(self.selected_resource_name, field_name)
        else:  # Remove from primary key
            self.fields_model.setData(index, False, Qt.EditRole)
            self.datapackage.remove_from_primary_key(self.selected_resource_name, field_name)

    @Slot(name="insert_foreign_key_row")
    def insert_foreign_key_row(self):
        row = self.ui.treeView_foreign_keys.currentIndex().row()+1
        self.foreign_keys_model.insert_empty_row(row)

    @Slot(name="remove_foreign_key_rows")
    def remove_foreign_key_rows(self):
        selection = self.ui.treeView_foreign_keys.selectionModel().selection()
        row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_set.update(range(top, bottom+1))
        for row in reversed(list(row_set)):
            self.foreign_keys_model.removeRows(row, 1)

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_foreign_key_fields")
    def update_foreign_key_fields(self, editor, hint):
        # TODO: Slot line has 3 arguments but def line has only 2 (editor and hint). Which one is correct?
        print('upd fk fields')
        model = editor.model()
        for i in range(model.rowCount()):
            index = model.index(i, 0)
            print(index.data(Qt.DisplayRole))
            print(index.data(Qt.CheckStateRole))
        index = editor.index
        value = editor.currentText()
        self.foreign_keys_model.setData(index, value, Qt.EditRole)

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_foreign_key_ref_resource")
    def update_foreign_key_ref_resource(self, editor, hint):
        # TODO: Slot line has 3 arguments but def line has only 2 (editor and hint). Which one is correct?
        index = editor.index
        value = editor.currentText()
        self.foreign_keys_model.setData(index, value, Qt.EditRole)

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_foreign_key_ref_fields")
    def update_foreign_key_ref_fields(self, editor, hint):
        # TODO: Slot line has 3 arguments but def line has only 2 (editor and hint). Which one is correct?
        index = editor.index
        value = editor.currentText()
        self.foreign_keys_model.setData(index, value, Qt.EditRole)

        # Iterate over resources (again) to create relationships
        #for resource in self.datapackage.resources:
        #    parent_object_class_name = resource.name
        #    if parent_object_class_name not in self.object_class_name_list:
        #        continue
        #    relationship_class_id_dict = dict()
        #    child_object_class_id_dict = dict()
        #    for field in resource.schema.fields:
        #        # A field whose named starts with the object_class is an index and should be skipped
        #        if field.name.startswith(parent_object_class_name):
        #            continue
        #        # Fields whose name ends with an object class name are foreign keys
        #        # and used to create relationships
        #        child_object_class_name = None
        #        for x in self.object_class_name_list:
        #            if field.name.endswith(x):
        #                child_object_class_name = x
        #                break
        #        if child_object_class_name:
        #            relationship_class_name = resource.name + "_" + field.name
        #            relationship_class_id_dict[field.name] = self.session.query(self.RelationshipClass.id).\
        #                filter_by(name=relationship_class_name).one().id
        #            child_object_class_id_dict[field.name] = self.session.query(self.ObjectClass.id).\
        #                filter_by(name=child_object_class_name).one().id
        #    for i, row in enumerate(self.resource_tables[resource.name][1:]):
        #        row_dict = dict(zip(resource.schema.field_names, row))
        #        if parent_object_class_name in row_dict:
        #            parent_object_name = row_dict[parent_object_class_name]
        #        else:
        #            parent_object_name = parent_object_class_name + str(i)
        #        parent_object_id = self.session.query(self.Object.id).\
        #            filter_by(name=parent_object_name).one().id
        #        for field_name, value in row_dict.items():
        #            if field_name in relationship_class_id_dict:
        #                relationship_class_id = relationship_class_id_dict[field_name]
        #                child_object_name = None
        #                child_object_ref = value
        #                child_object_class_id = child_object_class_id_dict[field_name]
        #                child_object_class_name = self.session.query(self.ObjectClass.name).\
        #                    filter_by(id=child_object_class_id).one().name
        #                child_resource = self.datapackage.get_resource(child_object_class_name)
        #                # Collect index and primary key columns in child resource
        #                indices = list()
        #                primary_key = None
        #                for j, field in enumerate(child_resource.schema.fields):
        #                    # A field whose named starts with the object_class is an index
        #                    if field.name.startswith(child_object_class_name):
        #                        indices.append(j)
        #                        # A field named exactly as the object_class is the primary key
        #                        if field.name == child_object_class_name:
        #                            primary_key = j
        #                # Look up the child object ref. in the child resource table
        #                for k, row in enumerate(self.resource_tables[child_resource.name][1:]):
        #                    if child_object_ref in [row[j] for j in indices]:
        #                        # Found reference in index values
        #                        if primary_key is not None:
        #                            child_object_name = row[primary_key]
        #                        else:
        #                            child_object_name = child_object_class_name + str(k)
        #                        break
        #                if child_object_name is None:
        #                    msg = "Couldn't find object ref {} to create relationship for field {}".\
        #                        format(child_object_ref, field_name)
        #                    self.ui.statusbar.showMessage(msg, 5000)
        #                    continue
        #                child_object_id = self.session.query(self.Object.id).\
        #                    filter_by(name=child_object_name, class_id=child_object_class_id).one().id
        #                relationship_name = parent_object_name + field_name + child_object_name
        #                relationship = self.Relationship(
        #                    commit_id=1,
        #                    class_id=relationship_class_id,
        #                    parent_object_id=parent_object_id,
        #                    child_object_id=child_object_id,
        #                    name=relationship_name
        #                )
        #                try:
        #                    self.session.add(relationship)
        #                    self.session.flush()
        #                    object_id = object_.id
        #                except DBAPIError as e:
        #                    msg = "Failed to insert relationship {0} for object {1} of class {2}: {3}".\
        #                        format(field_name, parent_object_name, parent_object_class_name, e.orig.args)
        #                    self.ui.statusbar.showMessage(msg, 5000)
        #                    self.session.rollback()
        #                    return False

    @Slot("QPoint", name="show_descriptor_tree_context_menu")
    def show_descriptor_tree_context_menu(self, pos):
        # TODO: Obsolete?
        """Context menu for descriptor treeview.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_descriptor.indexAt(pos)
        global_pos = self.ui.treeView_descriptor.viewport().mapToGlobal(pos)
        self.descriptor_tree_context_menu = DescriptorTreeContextMenu(self, global_pos, index)
        option = self.descriptor_tree_context_menu.get_action()
        if option == "Expand all children":
            self.ui.treeView_descriptor.expand(index)
            if not self.descriptor_model.hasChildren(index):
                return
            for i in range(self.descriptor_model.rowCount(index)):
                child_index = self.descriptor_model.index(i, 0, index)
                self.ui.treeView_descriptor.expand(child_index)
        elif option == "Collapse all children":
            self.ui.treeView_descriptor.collapse(index)
            if not self.descriptor_model.hasChildren(index):
                return
            for i in range(self.descriptor_model.rowCount(index)):
                child_index = self.descriptor_model.index(i, 0, index)
                self.ui.treeView_descriptor.collapse(child_index)

    def closeEvent(self, event=None):
        """Handle close event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue("mainWindow/splitterState", self.ui.splitter.saveState())
        self.qsettings.setValue("mainWindow/windowSize", self.size())
        self.qsettings.setValue("mainWindow/windowPosition", self.pos())
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("mainWindow/windowMaximized", True)
        else:
            self.qsettings.setValue("mainWindow/windowMaximized", False)
        if event:
            event.accept()
