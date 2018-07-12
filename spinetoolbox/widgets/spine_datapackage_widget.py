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
Widget shown to user when pressing Datapackage options toolButton
on Data Connection item.

:author: Manuel Marin <manuelma@kth.se>
:date:   7.7.2018
"""

import os
import shutil
import tempfile
import logging
from config import STATUSBAR_SS
from ui.spine_datapackage_form import Ui_MainWindow
from widgets.lineedit_delegate import LineEditDelegate
from widgets.custom_menus import DescriptorTreeContextMenu
from PySide2.QtWidgets import QMainWindow, QHeaderView, QMessageBox
from PySide2.QtCore import Qt, Slot, QSettings, SIGNAL
from PySide2.QtGui import QStandardItemModel, QStandardItem, QFont, QFontMetrics
from helpers import create_fresh_Spine_database, busy_effect
from models import MinimalTableModel, DatapackageDescriptorModel
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from datapackage import Package


class SpineDatapackageWidget(QMainWindow):
    """A widget to allow user to edit a datapackage and convert it
    to a Spine database in SQLite.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        data_connection (DataConnection): Data Connection associated to this widget
    """
    def __init__(self, parent, data_connection):
        """Initialize class."""
        super().__init__(flags=Qt.Window)
        self._parent = parent
        self._data_connection = data_connection
        self.output_data_stores = None
        self.engine = None
        self.temp_filename = None
        self.Base = None
        self.session = None
        self.ObjectClass = None
        self.Object = None
        self.RelationshipClass = None
        self.Relationship = None
        self.Parameter = None
        self.ParameterValue = None
        self.Commit = None
        self.datapackage = None
        self.object_class_name_list = None
        self.block_resource_name_combobox = True
        self.font_metric = QFontMetrics(QFont("", 0))
        self.max_resource_name_width = None
        self.descriptor_tree_context_menu = None
        self.current_resource_index = None
        self.resource_tables = dict()
        self.export_name = self._data_connection.name + '.sqlite'
        self.descriptor_model = DatapackageDescriptorModel(self)
        self.descriptor_model.header.extend(["Key", "Value"])
        self.resource_data_model = MinimalTableModel()
        #  Set up the user interface from Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox datapackage form")
        # Add status bar to form
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Set name of export action
        self.ui.actionExport.setText("Export as '{0}'".format(self.export_name))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.create_engine()
        if not self.create_base_and_reflect_tables():
            self.close()
            return
        self.create_session()
        self.ui.treeView_descriptor.setModel(self.descriptor_model)
        self.ui.tableView_resource_data.setModel(self.resource_data_model)
        self.ui.tableView_resource_data.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_resource_data.verticalHeader().\
            setSectionResizeMode(QHeaderView.ResizeToContents)
        self.load_datapackage()
        self.connect_signals()
        self.restore_ui()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.treeView_descriptor.expanded.connect(self.resize_descriptor_treeview)
        self.ui.treeView_descriptor.collapsed.connect(self.resize_descriptor_treeview)
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionExport.triggered.connect(self.export)
        self.ui.actionInfer_datapackage.triggered.connect(self.call_infer_datapackage)
        self.ui.actionLoad_datapackage.triggered.connect(self.call_load_datapackage)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        resource_data_lineedit_delegate = LineEditDelegate(self)
        resource_data_lineedit_delegate.closeEditor.connect(self.update_resource_data)
        self.ui.tableView_resource_data.setItemDelegate(resource_data_lineedit_delegate)
        self.ui.treeView_descriptor.selectionModel().currentChanged.\
            connect(self.update_current_resource_index)
        self.ui.treeView_descriptor.customContextMenuRequested.\
            connect(self.show_descriptor_tree_context_menu)
        self.ui.comboBox_resource_name.currentTextChanged.connect(self.update_current_resource_name)

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("mainWindow/windowSize")
        window_pos = self.qsettings.value("mainWindow/windowPosition")
        splitter_state = self.qsettings.value("mainWindow/splitterState")
        window_maximized = self.qsettings.value("mainWindow/windowMaximized", defaultValue='false')  # returns string
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if splitter_state:
            self.ui.splitter.restoreState(splitter_state)

    def create_engine(self):
        """Create engine with a fresh Spine database."""
        self.temp_filename = os.path.join(tempfile.gettempdir(), 'Spine.sqlite')
        url = "sqlite:///" + self.temp_filename
        self.engine = create_engine(url)
        create_fresh_Spine_database(self.engine)

    def create_base_and_reflect_tables(self):
        """Create base and reflect tables."""
        self.Base = automap_base()
        self.Base.prepare(self.engine, reflect=True)
        try:
            self.ObjectClass = self.Base.classes.object_class
            self.Object = self.Base.classes.object
            self.RelationshipClass = self.Base.classes.relationship_class
            self.Relationship = self.Base.classes.relationship
            self.Parameter = self.Base.classes.parameter
            self.ParameterValue = self.Base.classes.parameter_value
            self.Commit = self.Base.classes.commit
            return True
        except AttributeError as e:
            self._parent.msg_error.emit("Unable to parse database in the Spine format. "
                                        " Table <b>{}</b> is missing.".format(e))
            return False

    def create_session(self):
        """Create session."""
        self.session = Session(self.engine)
        object_class_name_query = self.session.query(self.ObjectClass.name)
        self.object_class_name_list = [item.name for item in object_class_name_query]
        self.max_resource_name_width = max(self.font_metric.width(x) for x in self.object_class_name_list)

    def load_resource_data(self):
        """Load resource data into a local list of tables."""
        if not self.datapackage:
            return
        for resource in self.datapackage.resources:
            table = list()
            table.append(resource.schema.field_names)
            table.extend(resource.read(cast=False))
            self.resource_tables[resource.name] = table

    @Slot(name="call_load_datapackage")
    def call_load_datapackage(self):
        """Attempt to load existing datapackage.json file in data directory."""
        file_path = os.path.join(self._data_connection.data_dir, "datapackage.json")
        if not os.path.exists(file_path):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Datapackage descriptor not found")
            text = ("A file called 'datapackage.json' could not be found "
                    "in the Data Connection folder <b>{0}</b>. ".\
                    format(self._data_connection.data_dir))
            msg.setText(text)
            msg.setInformativeText("Unable to load datapackage. "
                                   "Do you want to try and <i>infer</i> one instead?")
            msg.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            answer = msg.exec_()  # Show message box
            if answer == QMessageBox.Yes:
                self.call_infer_datapackage()
            return
        self.load_datapackage()

    @busy_effect
    def load_datapackage(self, load_resource_data=True):
        """"""
        file_path = os.path.join(self._data_connection.data_dir, "datapackage.json")
        if not os.path.exists(file_path):
            return
        msg = "Loading datapackage from {}".format(file_path)
        self.ui.statusbar.showMessage(msg)
        self.datapackage = Package(file_path)
        msg = "Datapackage loaded from {}".format(file_path)
        self.ui.statusbar.showMessage(msg, 5000)
        self.init_descriptor_model()
        if load_resource_data:
            self.load_resource_data()

    @Slot(name="call_infer_datapackage")
    def call_infer_datapackage(self, load_resource_data=True):
        """Infer datapackage from CSV files in data directory."""
        data_files = self._data_connection.data_files()
        if not ".csv" in [os.path.splitext(f)[1] for f in data_files]:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Resources not found")
            text = ("The Data Connection folder <b>{0}</b> does not seem to have "
                    "any CSV resource files.".\
                    format(self._data_connection.data_dir))
            msg.setText(text)
            msg.setInformativeText("Unable to infer datapackage. "
                                   "Please add some CSV files and try again.")
            msg.setStandardButtons(QMessageBox.Ok)
            answer = msg.exec_()  # Show message box
            return
        self.infer_datapackage()

    @busy_effect
    def infer_datapackage(self, load_resource_data=True):
        """"""
        msg = "Inferring datapackage from {}".format(self._data_connection.data_dir)
        self.ui.statusbar.showMessage(msg)
        self.datapackage = Package(base_path = self._data_connection.data_dir)
        self.datapackage.infer(os.path.join(self._data_connection.data_dir, '*.csv'))
        msg = "Datapackage inferred from {}".format(self._data_connection.data_dir)
        self.ui.statusbar.showMessage(msg, 5000)
        self.init_descriptor_model()
        if load_resource_data:
            self.load_resource_data()

    @Slot(name="save_datapackage")
    def save_datapackage(self):  #TODO: handle zip as well?
        """Save datapackage.json to datadir"""
        if not self.datapackage:
            msg = "Load or infer a datapackage first."
            self.ui.statusbar.showMessage(msg, 5000)
            return
        if os.path.exists(os.path.join(self._data_connection.data_dir, "datapackage.json")):
            msg = '<b>Replacing file "datapackage.json" in "{}"</b>.'\
                  ' Are you sure?'.format(os.path.basename(self._data_connection.data_dir))
            # noinspection PyCallByClass, PyTypeChecker
            answer = QMessageBox.question(None, 'Replace "datapackage.json"', msg, QMessageBox.Yes, QMessageBox.No)
            if not answer == QMessageBox.Yes:
                return False
        if self.datapackage.save(os.path.join(self._data_connection.data_dir, 'datapackage.json')):
            msg = '"datapackage.json" saved in {}'.format(self._data_connection.data_dir)
            self.ui.statusbar.showMessage(msg, 5000)
            return True
            msg = 'Failed to save "datapackage.json" in {}'.format(self._data_connection.data_dir)
            self.ui.statusbar.showMessage(msg, 5000)
        return False

    def init_descriptor_model(self):
        """Init datapackage descriptor model"""
        self.descriptor_model.clear()
        self.resource_data_model.reset_model([])
        self.current_resource_index = None
        self.block_resource_name_combobox = True
        self.ui.comboBox_resource_name.clear()
        self.block_resource_name_combobox = False
        def visit(parent_item, value):
            for key,new_value in value.items():
                key_item = QStandardItem(str(key))
                key_item.setData(key, Qt.UserRole)
                value_item = None
                if isinstance(new_value, dict):
                    visit(key_item, new_value)
                elif isinstance(new_value, list):
                    visit(key_item, dict(enumerate(new_value)))
                else:
                    value_item = QStandardItem(str(new_value))
                row = list()
                row.append(key_item)
                if value_item:
                    row.append(value_item)
                parent_item.appendRow(row)
        visit(self.descriptor_model, self.datapackage.descriptor)
        self.ui.treeView_descriptor.resizeColumnToContents(0)

    @Slot("QModelIndex", name="resize_descriptor_treeview")
    def resize_descriptor_treeview(self, index):
        self.ui.treeView_descriptor.resizeColumnToContents(0)

    @Slot("QModelIndex", "QModelIndex", name="update_current_resource_index")
    def update_current_resource_index(self, current, previous):
        """Update current resource index whenever a new resource item is selected
        in the descriptor treeView."""
        index = current
        selected_resource_index = None
        while index.parent().isValid():
            if index.parent().data(Qt.UserRole) == 'resources':
                selected_resource_index = index.data(Qt.UserRole)  # resource pos in json array
                break
            index = index.parent()
        if selected_resource_index is None:
            return
        if self.current_resource_index == selected_resource_index:  # selected resource not changed
            return
        self.current_resource_index = selected_resource_index
        self.reset_resource_data_model()
        self.reset_resource_name_combo()

    def reset_resource_data_model(self):
        """"""
        current_resource_name = self.datapackage.resources[self.current_resource_index].name
        table = self.resource_tables[current_resource_name]
        self.resource_data_model.header = table[0]  # TODO: find out why this is needed
        self.resource_data_model.reset_model(table)
        self.ui.tableView_resource_data.resizeColumnsToContents()

    def reset_resource_name_combo(self):
        """"""
        self.block_resource_name_combobox = True
        self.ui.comboBox_resource_name.clear()
        resource_name = self.datapackage.resources[self.current_resource_index].name
        self.ui.comboBox_resource_name.addItems(self.object_class_name_list)
        max_width = self.max_resource_name_width
        if resource_name not in self.object_class_name_list:
            self.ui.comboBox_resource_name.insertItem(0, resource_name + ' (unsupported)')
            self.ui.comboBox_resource_name.setCurrentIndex(0)
            width = self.font_metric.width(resource_name + ' (unsupported)')
            max_width = max(max_width, width)
        else:
            ind = self.object_class_name_list.index(resource_name)
            self.ui.comboBox_resource_name.setCurrentIndex(ind)
        # Set combobox width based on items
        self.ui.comboBox_resource_name.setMinimumWidth(max_width + 24)
        self.block_resource_name_combobox = False

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_resource_data")
    def update_resource_data(self, editor, hint):
        """Update resource data with newly edited data."""
        index = editor.index
        if not self.resource_data_model.setData(index, editor.text(), Qt.EditRole):
            return
        self.ui.tableView_resource_data.resizeColumnsToContents()
        # Update descriptor in datapackage in case a field name was modified
        if index.row() == 0:
            self.update_field_name(index.column(), editor.text())

    def update_field_name(self, field_index, new_name):
        """Update descriptor (datapackage and model) with new field name
        from resource data table."""
        # Update datapackage descriptor
        resource_dict = self.datapackage.descriptor['resources'][self.current_resource_index]
        resource_dict['schema']['fields'][field_index]['name'] = new_name
        self.datapackage.commit()
        # Update descriptor model
        key_chain = ['resources', self.current_resource_index, 'schema', 'fields', field_index, 'name']
        key, item = self.descriptor_model.find_item(key_chain)
        if key != key_chain[-1]:
            msg = "Couldn't find field in datapackage descriptor. Something is wrong."
            self.ui.statusbar.showMessage(msg, 5000)
            return
        ind = item.index()
        sib = ind.sibling(ind.row(), 1)
        self.descriptor_model.setData(sib, new_name, Qt.EditRole)

    @Slot("str", name="update_current_resource_name")
    def update_current_resource_name(self, text):
        """Update descriptor (datapackage and model) with new resource name from comboBox."""
        if self.block_resource_name_combobox:
            return
        # Update resource table
        current_resource_name = self.datapackage.descriptor['resources'][self.current_resource_index]['name']
        self.resource_tables[text] = self.resource_tables.pop(current_resource_name, None)
        # Update datapackage descriptor
        self.datapackage.descriptor['resources'][self.current_resource_index]['name'] = text
        self.datapackage.commit()
        # Update descriptor model
        key_chain = ['resources', self.current_resource_index, 'name']
        key, item = self.descriptor_model.find_item(key_chain)
        if key != key_chain[-1]:
            msg = "Couldn't find resource in datapackage descriptor. Something is wrong."
            self.ui.statusbar.showMessage(msg, 5000)
            return
        ind = item.index()
        sib = ind.sibling(ind.row(), 1)
        self.descriptor_model.setData(sib, text, Qt.EditRole)
        # Remove unsupported name from combobox
        ind = self.ui.comboBox_resource_name.findText("unsupported", Qt.MatchContains)
        if ind == -1:
            return
        self.ui.comboBox_resource_name.removeItem(ind)

    @Slot(name="export")
    def export(self):
        """Check if everything is fine (destination, resource names), launch conversion,
        save output as .sqlite in destination Data Stores' directory, and clean up session
        for future conversions."""
        if not self.datapackage:
            msg = "No datapackage to export. Load or infer one first."
            self.ui.statusbar.showMessage(msg, 5000)
            return
        output_data_directories = list()
        for output_item in self._parent.connection_model.output_items(self._data_connection.name):
            found_item = self._parent.project_item_model.find_item(output_item, Qt.MatchExactly | Qt.MatchRecursive)
            if found_item:
                if found_item.data(Qt.UserRole).item_type == 'Data Store':
                    output_data_directories.append(found_item.data(Qt.UserRole).data_dir)
        if not output_data_directories:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Destination not found")
            text = ("The datapackage cannot be exported because the Data Connection <b>{}</b> "
                    "is not connected to any destination Data Stores.").format(self._data_connection.name)
            msg.setText(text)
            msg.setInformativeText("Connect <b>{}</b> to a Data Store and try again.".\
                format(self._data_connection.name))
            msg.setStandardButtons(QMessageBox.Ok)
            answer = msg.exec_()  # Show message box
            return
        unsupported_names = list()
        for resource in self.datapackage.resources:
            if resource.name not in self.object_class_name_list:
                unsupported_names.append(resource.name)
        if unsupported_names:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Unsupported resource names")
            text = ("The following resources have unsupported names "
                    "and will be ignored by the conversion process:<ul>")
            for name in unsupported_names:
                text += "<li>{}</li>".format(name)
            text += "</ul>"
            msg.setText(text)
            msg.setInformativeText("Do you want to proceed anyway?")
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
            answer = msg.exec_()  # Show message box
            if answer != QMessageBox.Yes:
                return
        if self.convert():
            for dir in output_data_directories:
                target_filename = os.path.join(dir, self.export_name)
                try:
                    shutil.copy(self.temp_filename, target_filename)
                except OSError:
                    msg = "Conversion failed. [OSError] Unable to copy file from temporary location."
                    self.ui.statusbar.showMessage(msg, 5000)
                    return
            msg = "File '{0}' saved in {1}".format(self.export_name, output_data_directories)
            self.ui.statusbar.showMessage(msg, 5000)
        # Clean up session after converting
        try:
            self.session.query(self.Object).delete()
            self.session.query(self.RelationshipClass).delete()
            self.session.query(self.Relationship).delete()
            self.session.query(self.Parameter).delete()
            self.session.query(self.ParameterValue).delete()
            self.session.query(self.Commit).delete()
            self.session.flush()
        except Exception as e:
            # TODO: handle this better, maybe open a new session
            self.actionExport.setEnabled(False)
            msg = self.ui.statusbar.message()
            msg = " Could not clean up session. Export has been disabled. {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)

    @busy_effect
    def convert(self):
        """Convert datapackage to Spine database."""
        for resource in self.datapackage.resources:
            object_class_name = resource.name
            if object_class_name not in self.object_class_name_list:
                continue
            object_class_id = self.session.query(self.ObjectClass.id).\
                filter_by(name=object_class_name).one().id
            parameter_id_dict = dict()
            for field in resource.schema.fields:
                # A field whose named starts with the object_class is an index and should be skipped
                if field.name.startswith(object_class_name):
                    continue
                # Fields whose name ends with an object class name are foreign keys
                # and used to create relationships
                child_object_class_name = None
                for x in self.object_class_name_list:
                    if field.name.endswith(x):
                        child_object_class_name = x
                        break
                if child_object_class_name:
                    # Relationship class
                    child_object_class_id = self.session.query(self.ObjectClass.id).\
                        filter_by(name=child_object_class_name).one().id
                    relationship_class_name = resource.name + "_" + field.name
                    relationship_class = self.RelationshipClass(
                        commit_id=1,
                        parent_object_class_id=object_class_id,
                        child_object_class_id=child_object_class_id,
                        name=relationship_class_name
                    )
                    try:
                        self.session.add(relationship_class)
                        self.session.flush()
                    except DBAPIError as e:
                        msg = ("Failed to insert relationship class {0} for object class {1}: {2}".\
                            format(relationship_class_name, object_class_name, e.orig.args))
                        self.ui.statusbar.showMessage(msg, 5000)
                        self.session.rollback()
                        return False
                else:
                    # Parameter
                    parameter_name = field.name
                    parameter = self.Parameter(
                        commit_id=1,
                        object_class_id=object_class_id,
                        name=parameter_name
                    )
                    try:
                        self.session.add(parameter)
                        self.session.flush()
                        parameter_id_dict[field.name] = parameter.id
                    except DBAPIError as e:
                        msg = ("Failed to insert parameter {0} for object class {1}: {2}".\
                            format(parameter_name, object_class_name, e.orig.args))
                        self.ui.statusbar.showMessage(msg, 5000)
                        self.session.rollback()
                        return False
            # Iterate over resource data to create objects and parameter values
            object_id_dict = dict()
            for i, row in enumerate(self.resource_tables[resource.name][1:]):
                row_dict = dict(zip(resource.schema.field_names, row))
                # Get object name from primery key
                if object_class_name in row_dict:
                    object_name = row_dict[object_class_name]
                else:
                    object_name = object_class_name + str(i)
                object_ = self.Object(
                    commit_id=1,
                    class_id=object_class_id,
                    name=object_name
                )
                try:
                    self.session.add(object_)
                    self.session.flush()
                    object_id = object_.id
                except DBAPIError as e:
                    msg = "Failed to insert object {0} to object class {1}: {2}".\
                        format(object_name, object_class_name, e.orig.args)
                    self.ui.statusbar.showMessage(msg, 5000)
                    self.session.rollback()
                    return False
                object_id_dict[i] = object_.id
                for field_name, value in row_dict.items():
                    if field_name in parameter_id_dict:
                        parameter_id = parameter_id_dict[field_name]
                        parameter_value = self.ParameterValue(
                            commit_id=1,
                            object_id=object_id,
                            parameter_id=parameter_id,
                            value=value
                        )
                        try:
                            self.session.add(parameter_value)
                            self.session.flush()
                            object_id = object_.id
                        except DBAPIError as e:
                            msg = "Failed to insert parameter value {0} for object {1} of class {2}: {3}".\
                                format(field_name, object_name, object_class_name, e.orig.args)
                            self.ui.statusbar.showMessage(msg, 5000)
                            self.session.rollback()
                            return False
        # Iterate over resources (again) to create relationships
        for resource in self.datapackage.resources:
            parent_object_class_name = resource.name
            if parent_object_class_name not in self.object_class_name_list:
                continue
            relationship_class_id_dict = dict()
            child_object_class_id_dict = dict()
            for field in resource.schema.fields:
                # A field whose named starts with the object_class is an index and should be skipped
                if field.name.startswith(parent_object_class_name):
                    continue
                # Fields whose name ends with an object class name are foreign keys
                # and used to create relationships
                child_object_class_name = None
                for x in self.object_class_name_list:
                    if field.name.endswith(x):
                        child_object_class_name = x
                        break
                if child_object_class_name:
                    relationship_class_name = resource.name + "_" + field.name
                    relationship_class_id_dict[field.name] = self.session.query(self.RelationshipClass.id).\
                        filter_by(name=relationship_class_name).one().id
                    child_object_class_id_dict[field.name] = self.session.query(self.ObjectClass.id).\
                        filter_by(name=child_object_class_name).one().id
            for i, row in enumerate(self.resource_tables[resource.name][1:]):
                row_dict = dict(zip(resource.schema.field_names, row))
                if parent_object_class_name in row_dict:
                    parent_object_name = row_dict[parent_object_class_name]
                else:
                    parent_object_name = parent_object_class_name + str(i)
                parent_object_id = self.session.query(self.Object.id).\
                    filter_by(name=parent_object_name).one().id
                for field_name, value in row_dict.items():
                    if field_name in relationship_class_id_dict:
                        relationship_class_id = relationship_class_id_dict[field_name]
                        child_object_name = None
                        child_object_ref = value
                        child_object_class_id = child_object_class_id_dict[field_name]
                        child_object_class_name = self.session.query(self.ObjectClass.name).\
                            filter_by(id=child_object_class_id).one().name
                        child_resource = self.datapackage.get_resource(child_object_class_name)
                        # Collect index and primary key columns in child resource
                        indices = list()
                        primary_key = None
                        for j, field in enumerate(child_resource.schema.fields):
                            # A field whose named starts with the object_class is an index
                            if field.name.startswith(child_object_class_name):
                                indices.append(j)
                                # A field named exactly as the object_class is the primary key
                                if field.name == child_object_class_name:
                                    primary_key = j
                        # Look up the child object ref. in the child resource table
                        for k, row in enumerate(self.resource_tables[child_resource.name][1:]):
                            if child_object_ref in [row[j] for j in indices]:
                                # Found reference in index values
                                if primary_key is not None:
                                    child_object_name = row[primary_key]
                                else:
                                    child_object_name = child_object_class_name + str(k)
                                break
                        if child_object_name is None:
                            msg = "Couldn't find object ref {} to create relationship for field {}".\
                                format(child_object_ref, field_name)
                            self.ui.statusbar.showMessage(msg, 5000)
                            continue
                        child_object_id = self.session.query(self.Object.id).\
                            filter_by(name=child_object_name, class_id=child_object_class_id).one().id
                        relationship_name = parent_object_name + field_name + child_object_name
                        relationship = self.Relationship(
                            commit_id=1,
                            class_id=relationship_class_id,
                            parent_object_id=parent_object_id,
                            child_object_id=child_object_id,
                            name=relationship_name
                        )
                        try:
                            self.session.add(relationship)
                            self.session.flush()
                            object_id = object_.id
                        except DBAPIError as e:
                            msg = "Failed to insert relationship {0} for object {1} of class {2}: {3}".\
                                format(field_name, parent_object_name, parent_object_class_name, e.orig.args)
                            self.ui.statusbar.showMessage(msg, 5000)
                            self.session.rollback()
                            return False
        try:
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False

    @Slot("QPoint", name="show_descriptor_tree_context_menu")
    def show_descriptor_tree_context_menu(self, pos):
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
        # close sql session
        if self.session:
            self.session.rollback()
            self.session.close()
        if self.engine:
            self.engine.dispose()
        if self.temp_filename:
            try:
                os.remove(self.temp_filename)
            except OSError:
                pass
        if event:
            event.accept()
