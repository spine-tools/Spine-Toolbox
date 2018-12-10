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
Widget shown to user when opening a 'datapackage.json' file
in Data Connection item.

:author: M. Marin (KTH)
:date:   7.7.2018
"""

import os
from config import STATUSBAR_SS
from ui.spine_datapackage_form import Ui_MainWindow
from widgets.custom_delegates import ForeignKeysDelegate, LineEditDelegate, CheckBoxDelegate
from PySide2.QtWidgets import QMainWindow, QHeaderView, QMessageBox, QPushButton, QErrorMessage, QAction, \
    QToolButton
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QItemSelectionModel, QModelIndex, QSize
from PySide2.QtGui import QGuiApplication, QFontMetrics, QFont, QIcon
from models import MinimalTableModel, DatapackageResourcesModel, DatapackageFieldsModel, DatapackageForeignKeysModel
from ui.spine_datapackage_form import Ui_MainWindow
from widgets.custom_delegates import ResourceNameDelegate, ForeignKeysDelegate, LineEditDelegate, CheckBoxDelegate
from spinedatabase_api import OBJECT_CLASS_NAMES
from datapackage import Package


class SpineDatapackageWidget(QMainWindow):
    """A widget to allow user to edit a datapackage and convert it
    to a Spine database in SQLite.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        data_connection (DataConnection): Data Connection associated to this widget
        datapackage (CustomPackage): Datapackage to load and use
    """
    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, data_connection):
        """Initialize class."""
        super().__init__(flags=Qt.Window)  # TODO: Set parent as toolbox here if it makes sense
        # TODO: Maybe set the parent as ToolboxUI so that its stylesheet is inherited. This may need
        # TODO: reimplementing the window minimizing and maximizing actions as well as setting the window modality
        self._data_connection = data_connection
        self.object_class_name_list = OBJECT_CLASS_NAMES
        self.datapackage = None
        self.descriptor_tree_context_menu = None
        self.selected_resource_name = None
        self.resource_data = dict()
        self.resources_model = DatapackageResourcesModel(self)
        self.fields_model = DatapackageFieldsModel(self)
        self.foreign_keys_model = DatapackageForeignKeysModel(self)
        self.foreign_keys_model.set_default_row(length=1)
        self.resource_data_model = MinimalTableModel(self)
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        self.err_msg = QErrorMessage(self)
        self.remove_row_icon = QIcon(":/icons/minus.png")
        #  Set up the user interface from Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.restore_ui()
        # Add status bar to form
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Set up corner widgets
        button = QPushButton("Descriptor")
        button.setFlat(True)
        button.setLayoutDirection(Qt.LeftToRight)
        button.mousePressEvent = lambda e: e.ignore()
        self.ui.tabWidget_resources.setCornerWidget(button, Qt.TopRightCorner)
        button = QPushButton("Resource")
        button.setLayoutDirection(Qt.LeftToRight)
        button.setFlat(True)
        button.mousePressEvent = lambda e: e.ignore()
        self.ui.tabWidget_data_schema.setCornerWidget(button, Qt.TopRightCorner)
        self.ui.treeView_resources.setModel(self.resources_model)
        self.ui.tableView_fields.setModel(self.fields_model)
        self.ui.tableView_foreign_keys.setModel(self.foreign_keys_model)
        self.ui.tableView_resource_data.setModel(self.resource_data_model)
        # self.ui.tableView_resource_data.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_resource_data.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_resource_data.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_fields.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_fields.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_foreign_keys.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_foreign_keys.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.connect_signals()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def show(self):
        """Show form and init datapackage."""
        super().show()
        self.load_datapackage()

    @Slot(bool, name="load_datapackage")
    def load_datapackage(self):
        """Try and initialize datapackage, and reset resource model if successful"""
        if not self.init_datapackage():
            return
        self.load_resource_data()
        self.resources_model.reset_model(self.datapackage)
        first_index = self.resources_model.index(0, 0)
        if not first_index.isValid():
            return
        self.ui.treeView_resources.selectionModel().select(first_index, QItemSelectionModel.Select)
        self.reset_resource_models(first_index, QModelIndex())

    def connect_signals(self):
        """Connect signals to slots."""
        # Message actions
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        # DC destroyed
        self._data_connection.destroyed.connect(self.close)
        # Delegates
        # Resource name
        line_edit_delegate = LineEditDelegate(self)
        line_edit_delegate.data_committed.connect(self._handle_resource_name_data_committed)
        self.ui.treeView_resources.setItemDelegateForColumn(0, line_edit_delegate)
        # Field name
        line_edit_delegate = LineEditDelegate(self)
        line_edit_delegate.data_committed.connect(self._handle_field_name_data_committed)
        self.ui.tableView_fields.setItemDelegateForColumn(0, line_edit_delegate)
        # Primary key
        checkbox_delegate = CheckBoxDelegate(self)
        checkbox_delegate.data_committed.connect(self._handle_primary_key_data_committed)
        self.ui.tableView_fields.setItemDelegateForColumn(2, checkbox_delegate)
        self.ui.tableView_resource_data.setItemDelegate(line_edit_delegate)
        # Foreign keys
        foreign_keys_delegate = ForeignKeysDelegate(self)
        foreign_keys_delegate.data_committed.connect(self._handle_foreign_keys_data_committed)
        self.ui.tableView_foreign_keys.setItemDelegate(foreign_keys_delegate)
        self.foreign_keys_model.rowsInserted.connect(self._handle_foreign_keys_model_rows_inserted)
        # Selected resource changed
        self.ui.treeView_resources.selectionModel().currentChanged.connect(self.reset_resource_models)
        # Actions
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        self.ui.actionLoad_datapackage.triggered.connect(self.load_datapackage)
        # self.ui.actionExport_to_Spine.triggered.connect(self.export)

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

    @Slot(str, name="add_error_message")
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show
        """
        self.err_msg.showMessage(msg)

    def init_datapackage(self):
        """Init datapackage from 'datapackage.json' file in data directory,
        or infer one from CSV files in that directory."""
        file_path = os.path.join(self._data_connection.data_dir, "datapackage.json")
        if os.path.exists(file_path):
            self.datapackage = CustomPackage(file_path)
            msg = "Datapackage succesfully loaded from {}".format(file_path)
            self.msg.emit(msg)
            return True
        data_files = self._data_connection.data_files()
        if ".csv" in [os.path.splitext(f)[1] for f in data_files]:
            self.datapackage = CustomPackage(base_path=self._data_connection.data_dir)
            self.datapackage.infer(os.path.join(self._data_connection.data_dir, '*.csv'))
            msg = "Datapackage succesfully inferred from {}".format(self._data_connection.data_dir)
            self.msg.emit(msg)
            return True
        self.msg_error.emit("Unable to load a datapackage from <b>{0}</b>. "
                            "Please add some CSV files to that folder  "
                            "and try again".format(self._data_connection.data_dir))
        return False

    def save_datapackage(self):
        """Write datapackage to file 'datapackage.json' in data directory."""
        if os.path.isfile(os.path.join(self._data_connection.data_dir, "datapackage.json")):
            msg = ('<b>Replacing file "datapackage.json" in "{}"</b>. '
                   'Are you sure?').format(os.path.basename(self._data_connection.data_dir))
            # noinspection PyCallByClass, PyTypeChecker
            answer = QMessageBox.question(
                self, 'Replace "datapackage.json"', msg, QMessageBox.Yes, QMessageBox.No)
            if not answer == QMessageBox.Yes:
                return False
        if self.datapackage.save(os.path.join(self._data_connection.data_dir, 'datapackage.json')):
            msg = '"datapackage.json" saved in {}'.format(self._data_connection.data_dir)
            self.msg.emit(msg)
            return True
        msg = 'Failed to save "datapackage.json" in {}'.format(self._data_connection.data_dir)
        self.msg_error.emit(msg)
        return False

    def load_resource_data(self):
        """Load resource data into a local list of tables."""
        for resource in self.datapackage.resources:
            self.resource_data[resource.name] = resource.read(cast=False)

    @Slot("QModelIndex", "QModelIndex", name="reset_resource_models")
    def reset_resource_models(self, current, previous):
        """Reset resource data and schema models whenever a new resource is selected."""
        new_selected_resource_name = current.data(Qt.DisplayRole)
        self.selected_resource_name = new_selected_resource_name
        self.reset_resource_data_model()
        schema = self.datapackage.get_resource(self.selected_resource_name).schema
        self.fields_model.reset_model(schema)
        self.foreign_keys_model.reset_model(schema)
        self.ui.tableView_fields.resizeColumnsToContents()
        self.ui.tableView_foreign_keys.resizeColumnsToContents()
        # Add buttons
        self._handle_foreign_keys_model_rows_inserted(
            QModelIndex(), 0, self.foreign_keys_model.rowCount() - 1)
        # Resize last section that has the button to remove row
        self.ui.tableView_foreign_keys.horizontalHeader().resizeSection(
            self.foreign_keys_model.columnCount() - 1, self.default_row_height)

    def reset_resource_data_model(self):
        """Reset resource data model with data from newly selected resource."""
        data = self.resource_data[self.selected_resource_name]
        field_names = self.datapackage.get_resource(self.selected_resource_name).schema.field_names
        self.resource_data_model.set_horizontal_header_labels(field_names)
        self.resource_data_model.reset_model(data)
        self.ui.tableView_resource_data.resizeColumnsToContents()
        # Replace delegate
        line_edit_delegate = LineEditDelegate(self)
        self.ui.tableView_resource_data.setItemDelegate(line_edit_delegate)
        line_edit_delegate.data_committed.connect(self.update_resource_data)

    @Slot("QModelIndex", "QVariant", name="update_resource_data")
    def update_resource_data(self, index, new_value):
        """Update resource data with newly edited data."""
        if not self.resource_data_model.setData(index, new_value, Qt.EditRole):
            return
        self.ui.tableView_resource_data.resizeColumnsToContents()

    @Slot("QModelIndex", "QVariant", name="_handle_resource_name_data_committed")
    def _handle_resource_name_data_committed(self, index, new_name):
        """Called when line edit delegate wants to edit resource name data.
        Update resources model and descriptor with new resource name."""
        if not new_name:
            return
        old_name = index.data(Qt.DisplayRole)
        if not self.resources_model.setData(index, new_name, Qt.EditRole):
            return
        resource_data = self.resource_data.pop(self.selected_resource_name)
        if resource_data is None:
            msg = "Couldn't find key in resource data dict. Something is wrong."
            logging.debug(msg)
            return
        self.resource_data[new_name] = resource_data
        self.selected_resource_name = new_name
        self.datapackage.rename_resource(old_name, new_name)

    @Slot("QModelIndex", "QVariant", name="_handle_field_name_data_committed")
    def _handle_field_name_data_committed(self, index, new_name):
        """Called when line edit delegate wants to edit field name data.
        Update name in fields_model, resource_data_model's header and datapackage descriptor.
        """
        if not new_name:
            return
        old_name = index.data(Qt.DisplayRole)
        if not self.fields_model.setData(index, new_name, Qt.EditRole):
            return
        self.datapackage.rename_field(self.selected_resource_name, old_name, new_name)
        field_names = self.datapackage.get_resource(self.selected_resource_name).schema.field_names
        self.resource_data_model.set_horizontal_header_labels(field_names)
        self.ui.tableView_resource_data.resizeColumnsToContents()
        schema = self.datapackage.get_resource(self.selected_resource_name).schema
        self.foreign_keys_model.reset_model(schema)

    @Slot("QModelIndex", name="_handle_primary_key_data_committed")
    def _handle_primary_key_data_committed(self, index):
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

    @Slot("QModelIndex", "QVariant", name="_handle_foreign_keys_data_committed")
    def _handle_foreign_keys_data_committed(self, index, value):
        # Store previous data in case we need to remove a foreign key
        previous_row_data = self.foreign_keys_model._main_data[index.row()][1:4]
        if not self.foreign_keys_model.setData(index, value, Qt.EditRole):
            return
        resource = self.selected_resource_name
        # Remove previous foreign key if any
        previous_removed = False
        if all(previous_row_data):
            fields_str, reference_resource, reference_fields_str = previous_row_data
            fields = fields_str.split(",")
            reference_fields = reference_fields_str.split(",")
            self.datapackage.remove_foreign_key(resource, fields, reference_resource, reference_fields)
            previous_removed = True
        # Check if we're ready to add a foreing key
        row_data = self.foreign_keys_model._main_data[index.row()][1:4]
        if all(row_data):
            fields_str, reference_resource, reference_fields_str = row_data
            fields = fields_str.split(",")
            reference_fields = reference_fields_str.split(",")
            if len(fields) != len(reference_fields):
                self.msg_error.emit("Both 'fields' and 'reference fields' lists should have the same lenght.")
                return
            self.datapackage.add_foreign_key(resource, fields, reference_resource, reference_fields)
            if not previous_removed:
                self.msg.emit("Successfully added foreing key.")
            else:
                self.msg.emit("Successfully updated foreing key.")

    @Slot("QModelIndex", "int", "int", name="_handle_foreign_keys_model_rows_inserted")
    def _handle_foreign_keys_model_rows_inserted(self, parent, first, last):
        column = self.foreign_keys_model.columnCount() - 1
        for row in range(first, last + 1):
            index = self.foreign_keys_model.index(row, column, parent)
            self.create_remove_foreign_keys_row_button(index)

    def create_remove_foreign_keys_row_button(self, index):
        """Create button to remove foreign keys row."""
        action = QAction()
        action.setIcon(self.remove_row_icon)
        button = QToolButton()
        button.setDefaultAction(action)
        button.setIconSize(QSize(20, 20))
        self.ui.tableView_foreign_keys.setIndexWidget(index, button)
        action.triggered.connect(lambda: self.remove_foreign_key_row(button))

    def remove_foreign_key_row(self, button):
        column = self.foreign_keys_model.columnCount() - 1
        for row in range(self.foreign_keys_model.rowCount()):
            index = self.foreign_keys_model.index(row, column)
            if button != self.ui.tableView_foreign_keys.indexWidget(index):
                continue
            # Remove fk from datapackage descriptor
            row_data = self.foreign_keys_model._main_data[row][1:4]
            self.foreign_keys_model.removeRows(row, 1)
            if not all(row_data):
                # Something is missing
                break
            fields_str, reference_resource, reference_fields_str = row_data
            fields = fields_str.split(",")
            reference_fields = reference_fields_str.split(",")
            resource = self.selected_resource_name
            self.datapackage.remove_foreign_key(resource, fields, reference_resource, reference_fields)
            self.msg.emit("Successfully removed foreing key.")
            break

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


class CustomPackage(Package):
    """Custom datapackage class."""
    def __init__(self, descriptor=None, base_path=None, strict=False, storage=None):
        super().__init__(descriptor, base_path, strict, storage)

    def rename_resource(self, old, new):
        resource_index = self.resource_names.index(old)
        self.descriptor['resources'][resource_index]['name'] = new
        self.commit()

    def rename_field(self, resource, old, new):
        resource_index = self.resource_names.index(resource)
        resource_dict = self.descriptor['resources'][resource_index]
        resource_schema = self.get_resource(resource).schema
        field_index = resource_schema.field_names.index(old)
        resource_dict['schema']['fields'][field_index]['name'] = new
        primary_key = resource_schema.primary_key
        foreign_keys = resource_schema.foreign_keys
        for i, field in enumerate(primary_key):
            if field == old:
                resource_dict['schema']['primaryKey'][primary_key_index] = new
        for i, foreign_key in enumerate(foreign_keys):
            for j, field in enumerate(foreign_key["fields"]):
                if field == old:
                    resource_dict['schema']['foreignKeys'][i]['fields'][j] = new
            for j, field in enumerate(foreign_key['reference']['fields']):
                if field == old:
                    resource_dict['schema']['foreignKeys'][i]['reference']['fields'][j] = new
        self.commit()

    def primary_keys_data(self):
        """Return primary keys in a 2-column list"""
        data = list()
        for resource in self.resources:
            for field in resource.schema.primary_key:
                table = resource.name
                data.append([table, field])
        return data

    def foreign_keys_data(self):
        """Return foreign keys in a 4-column list"""
        data = list()
        for resource in self.resources:
            for fk in resource.schema.foreign_keys:
                child_table = resource.name
                child_field = fk['fields'][0]
                parent_table = fk['reference']['resource']
                parent_field = fk['reference']['fields'][0]
                data.append([child_table, child_field, parent_table, parent_field])
        return data

    def set_primary_key(self, resource, *primary_key):
        """Set primary key for a given resource in the package"""
        i = self.resource_names.index(resource)
        self.descriptor['resources'][i]['schema']['primaryKey'] = primary_key
        self.commit()

    def append_to_primary_key(self, resource, field):
        """Append field to resources's primary key."""
        i = self.resource_names.index(resource)
        primary_key = self.descriptor['resources'][i]['schema'].setdefault('primaryKey', [])
        if field not in primary_key:
            primary_key.append(field)
        self.commit()

    def remove_from_primary_key(self, resource, field):
        """Remove field from resources's primary key."""
        i = self.resource_names.index(resource)
        primary_key = self.descriptor['resources'][i]['schema'].get('primaryKey')
        if not primary_key:
            return
        if field in primary_key:
            primary_key.remove(field)
        self.commit()

    def add_foreign_key(self, resource, fields, reference_resource, reference_fields):
        """Add foreign key to a given resource in the package"""
        i = self.resource_names.index(resource)
        foreign_key = {
            "fields": fields,
            "reference": {
                "resource": reference_resource,
                "fields": reference_fields
            }
        }
        foreign_keys = self.descriptor['resources'][i]['schema'].setdefault('foreignKeys', [])
        if foreign_key not in self.descriptor['resources'][i]['schema']['foreignKeys']:
            self.descriptor['resources'][i]['schema']['foreignKeys'].append(foreign_key)
            self.commit()

    def remove_primary_key(self, resource, *primary_key):
        """Remove the primary key for a given resource in the package"""
        i = self.resource_names.index(resource)
        if 'primaryKey' in self.descriptor['resources'][i]['schema']:
            descriptor_primary_key = self.descriptor['resources'][i]['schema']['primaryKey']
            if Counter(descriptor_primary_key) == Counter(primary_key):
                del self.descriptor['resources'][i]['schema']['primaryKey']
                self.commit()

    def remove_foreign_key(self, resource, fields, reference_resource, reference_fields):
        """Remove foreign key from the package"""
        i = self.resource_names.index(resource)
        foreign_key = {
            "fields": fields,
            "reference": {
                "resource": reference_resource,
                "fields": reference_fields
            }
        }
        try:
            foreign_keys = self.descriptor['resources'][i]['schema']['foreignKeys']
        except KeyError:
            return
        try:
            self.descriptor['resources'][i]['schema']['foreignKeys'].remove(foreign_key)
        except ValueError:
            return
        self.commit()
