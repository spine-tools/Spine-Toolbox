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

:author: M. Marin (KTH)
:date:   7.7.2018
"""

from config import STATUSBAR_SS
from ui.spine_datapackage_form import Ui_MainWindow
from widgets.custom_delegates import ResourceNameDelegate, ForeignKeysDelegate, LineEditDelegate, CheckBoxDelegate
from PySide2.QtWidgets import QMainWindow, QHeaderView, QMessageBox
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QItemSelectionModel
from PySide2.QtGui import QGuiApplication
from models import MinimalTableModel, DatapackageResourcesModel, DatapackageFieldsModel, DatapackageForeignKeysModel
from spinedatabase_api import OBJECT_CLASS_NAMES


class SpineDatapackageWidget(QMainWindow):
    """A widget to allow user to edit a datapackage and convert it
    to a Spine database in SQLite.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        data_connection (DataConnection): Data Connection associated to this widget
        datapackage (CustomPackage): Datapackage to load and use
    """
    msg = Signal(str, name="msg")
    msg_error = Signal(str, str, str, name="msg_error")

    def __init__(self, toolbox, data_connection, datapackage):
        """Initialize class."""
        super().__init__(flags=Qt.Window)  # TODO: Set parent as toolbox here if it makes sense
        # TODO: Maybe set the parent as ToolboxUI so that its stylesheet is inherited. This may need
        # TODO: reimplementing the window minimizing and maximizing actions as well as setting the window modality
        self._toolbox = toolbox
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
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.restore_ui()
        self.ui.toolButton_insert_foreign_key.setDefaultAction(self.ui.actionInsert_foreign_key)
        self.ui.toolButton_remove_foreign_keys.setDefaultAction(self.ui.actionRemove_foreign_keys)
        self.load_resource_data()
        # Add status bar to form
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
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
        first_index = self.resources_model.index(0, 0)
        if first_index.isValid():
            self.ui.treeView_resources.selectionModel().select(first_index, QItemSelectionModel.Select)
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
        lineedit_delegate.commitData.connect(self.update_resource_data)
        self.ui.tableView_resource_data.setItemDelegate(lineedit_delegate)
        # Resource name
        resource_name_delegate = ResourceNameDelegate(self)
        resource_name_delegate.commitData.connect(self.update_resource_name)
        self.ui.treeView_resources.setItemDelegateForColumn(0, resource_name_delegate)
        # Field name
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.commitData.connect(self.update_field_name)
        self.ui.treeView_fields.setItemDelegateForColumn(0, lineedit_delegate)
        # Primary key
        checkbox_delegate = CheckBoxDelegate(self)
        checkbox_delegate.commit_data.connect(self.update_primary_key)
        self.ui.treeView_fields.setItemDelegateForColumn(2, checkbox_delegate)
        self.ui.tableView_resource_data.setItemDelegate(lineedit_delegate)
        # Foreign keys
        foreign_keys_delegate = ForeignKeysDelegate(self)
        foreign_keys_delegate.commitData.connect(self.update_foreign_keys)
        self.ui.treeView_foreign_keys.setItemDelegate(foreign_keys_delegate)
        # Selected resource changed
        self.ui.treeView_resources.selectionModel().selectionChanged.connect(self.reset_resource_models)
        # Actions
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        self.ui.actionInsert_foreign_key.triggered.connect(self.insert_foreign_key_row)
        self.ui.actionRemove_foreign_keys.triggered.connect(self.remove_foreign_key_rows)
        # Rows inserted or Data changed
        self.resources_model.rowsInserted.connect(self.resources_model_rows_inserted)
        self.resources_model.dataChanged.connect(self.resources_model_data_changed)

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("dataPackageWidget/windowSize")
        window_pos = self.qsettings.value("dataPackageWidget/windowPosition")
        splitter_state = self.qsettings.value("dataPackageWidget/splitterState")
        window_maximized = self.qsettings.value("dataPackageWidget/windowMaximized", defaultValue='false')
        n_screens = self.qsettings.value("mainWindow/n_screens", defaultValue=1)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if splitter_state:
            self.ui.splitter.restoreState(splitter_state)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)

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

    @Slot("QModelIndex", "int", "int", name="resources_model_rows_inserted")
    def resources_model_rows_inserted(self, parent, first, last):
        self.check_resource_name(first)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="resources_model_data_changed")
    def resources_model_data_changed(self, top_left, bottom_right, roles):
        if Qt.EditRole not in roles:
            return
        self.check_resource_name(top_left.row())

    def check_resource_name(self, row):
        index = self.resources_model.index(row, 0)
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

    @Slot("QModelIndex", "QModelIndex", name="reset_resource_models")
    def reset_resource_models(self, selected, deselected):
        """Reset resource data and schema models whenever a new resource is selected."""
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

    @Slot("QWidget", name="update_resource_data")
    def update_resource_data(self, editor):
        """Update resource data with newly edited data."""
        index = editor.index()
        new_value = editor.text()
        if not self.resource_data_model.setData(index, new_value, Qt.EditRole):
            return
        self.ui.tableView_resource_data.resizeColumnsToContents()
        self.resource_tables[self.selected_resource_name][index.row()][index.column()] = new_value

    @Slot("QWidget", name="update_resource_name")
    def update_resource_name(self, editor):
        """Update resources model and descriptor with new resource name."""
        new_name = editor.currentText()
        if not new_name:
            return
        index = editor.index()
        old_name = index.data(Qt.DisplayRole)
        if not self.resources_model.setData(index, new_name, Qt.EditRole):
            return
        resource_data = self.resource_tables.pop(self.selected_resource_name, None)
        if resource_data is None:
            msg = "Couldn't find key in resource data dict. Something is wrong."
            self.msg.emit(msg)
            return
        self.resource_tables[new_name] = resource_data
        self.selected_resource_name = new_name
        self.datapackage.rename_resource(old_name, new_name)

    @Slot("QWidget", name="update_field_name")
    def update_field_name(self, editor):
        """Called when line edit delegate wants to edit field name data.
        Update name in fields_model, resource_data_model's header and datapackage descriptor.
        """
        index = editor.index()
        new_name = editor.text()
        # Save old name to look up field
        old_name = index.data(Qt.DisplayRole)
        if not self.fields_model.setData(index, new_name, Qt.EditRole):
            return
        header = self.resource_data_model.horizontal_header_labels()
        section = header.index(old_name)
        self.resource_data_model.setHeaderData(section, Qt.Horizontal, new_name, Qt.EditRole)
        self.ui.tableView_resource_data.resizeColumnsToContents()
        self.datapackage.rename_field(self.selected_resource_name, old_name, new_name)

    @Slot("QModelIndex", name="update_primary_key")
    def update_primary_key(self, index):
        # TODO: Should 'name' be in arguments?
        # Not sure: the `commit_data` signal from `CheckBoxDelegate` only passes an index
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

    @Slot("QWidget", name="update_foreign_keys")
    def update_foreign_keys(self, editor):
        index = editor.index()
        value = editor.text()
        self.foreign_keys_model.setData(index, value, Qt.EditRole)

    def closeEvent(self, event=None):
        """Handle close event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue("dataPackageWidget/splitterState", self.ui.splitter.saveState())
        self.qsettings.setValue("dataPackageWidget/windowSize", self.size())
        self.qsettings.setValue("dataPackageWidget/windowPosition", self.pos())
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("dataPackageWidget/windowMaximized", True)
        else:
            self.qsettings.setValue("dataPackageWidget/windowMaximized", False)
        if event:
            event.accept()
