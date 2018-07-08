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
Widget shown to user when pressing Convert to Spine or smething like that
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
from widgets.custom_qdialog import CustomQDialog
from widgets.custom_menus import DatapackageTreeContextMenu
from PySide2.QtWidgets import QMainWindow, QHeaderView, QMessageBox, QDialog, QCheckBox
from PySide2.QtCore import Qt, Slot, QSettings
from PySide2.QtGui import QStandardItemModel, QStandardItem, QFont
from helpers import create_fresh_Spine_database, busy_effect
from models import MinimalTableModel
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from datapackage import Package


class SpineDatapackageWidget(QMainWindow):
    """A widget to request user's preferences for converting data
    from a datapackage into Spine data structure.

    Attributes:
        data_connection (DataConnection): Data Connection that owns this widget.
    """
    def __init__(self, parent, data_connection):
        """Initialize class."""
        super().__init__(flags=Qt.Window)
        self._parent = parent
        self._data_connection = data_connection
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
        self.selected_resource = None
        self.datapackage_tree_context_menu = None
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        #  Set up the user interface from Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Convert datapackage to Spine")
        # Add status bar to form
        # Add status bar to form
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.create_engine()
        if not self.create_base_and_reflect_tables():
            self.close()
            return
        self.create_session()
        self.datapackage_model = QStandardItemModel(self)
        self.datapackage_model_header = ["Key", "Value"]
        self.datapackage_model.data = self.datapackage_model_data
        self.datapackage_model.flags = self.datapackage_model_flags
        self.datapackage_model.headerData = self.datapackage_model_header_data
        self.load_datapackage()
        self.ui.treeView_datapackage.setModel(self.datapackage_model)
        self.resource_data_model = MinimalTableModel()
        self.ui.tableView_resource_data.setModel(self.resource_data_model)
        self.ui.tableView_resource_data.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_resource_data.verticalHeader().\
            setSectionResizeMode(QHeaderView.ResizeToContents)
        self.connect_signals()
        self.restore_ui()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.treeView_datapackage.expanded.connect(self.resize_treeview_datapackage)
        self.ui.treeView_datapackage.collapsed.connect(self.resize_treeview_datapackage)
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionConvert.triggered.connect(self.convert_triggered)
        self.ui.actionInfer_datapackage.triggered.connect(self.infer_datapackage)
        self.ui.actionLoad_datapackage.triggered.connect(self.load_datapackage)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        # self.ui.actionResource_Spine_names.triggered.connect(self.call_edit_resource_Spine_names)
        # self.ui.actionField_Spine_names.triggered.connect(self.call_edit_field_Spine_names)
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_datapackage)
        self.ui.treeView_datapackage.setItemDelegateForColumn(1, lineedit_delegate)
        self.ui.treeView_datapackage.selectionModel().currentChanged.connect(self.populate_resource_table)
        self.ui.treeView_datapackage.customContextMenuRequested.\
            connect(self.show_datapackage_tree_context_menu)

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

    @Slot(name="load_datapackage")
    def load_datapackage(self):
        """Attempt to load existing datapackage.json file in data directory."""
        file_path = os.path.join(self._data_connection.data_dir, "datapackage.json")
        if not os.path.exists(file_path):
            msg = "File 'datapackage.json' not found in {}."\
                  " Try 'Infer new datapackage' instead.".format(self._data_connection.data_dir)
            self.ui.statusbar.showMessage(msg, 5000)
            return
        self.datapackage = Package(file_path)
        msg = "Datapackage loaded from {}".format(file_path)
        self.ui.statusbar.showMessage(msg, 3000)
        self.spinify_datapackage()
        self.init_datapackage_model()

    @Slot(name="infer_datapackage")
    def infer_datapackage(self):
        data_files = self._data_connection.data_files()
        if not ".csv" in [os.path.splitext(f)[1] for f in data_files]:
            msg = ("The folder {} does not have any CSV files."
                   " Add some and try again.".format(self._data_connection.data_dir))
            self.ui.statusbar.showMessage(msg, 5000)
            return
        self.datapackage = Package(base_path = self._data_connection.data_dir)
        self.datapackage.infer(os.path.join(self._data_connection.data_dir, '*.csv'))
        msg = "Datapackage inferred from {}".format(self._data_connection.data_dir)
        self.ui.statusbar.showMessage(msg, 3000)
        self.spinify_datapackage()
        self.init_datapackage_model()

    @Slot(name="save_datapackage")
    def save_datapackage(self):  #TODO: handle zip as well?
        """Save datapackage.json to datadir"""
        if os.path.exists(os.path.join(self._data_connection.data_dir, "datapackage.json")):
            msg = '<b>Replacing file "datapackage.json" in "{}"</b>.'\
                  ' Are you sure?'.format(os.path.basename(self._data_connection.data_dir))
            # noinspection PyCallByClass, PyTypeChecker
            answer = QMessageBox.question(None, 'Replace datapackage.json', msg, QMessageBox.Yes, QMessageBox.No)
            if not answer == QMessageBox.Yes:
                return False
        if self.datapackage.save(os.path.join(self._data_connection.data_dir, 'datapackage.json')):
            msg = "datapackage.json saved in {}".format(self._data_connection.data_dir)
            self.ui.statusbar.showMessage(msg, 3000)
            return True
            msg = "Failed to save datapackage.json in {}".format(self._data_connection.data_dir)
            self.ui.statusbar.showMessage(msg, 5000)
        return False

    def spinify_datapackage(self):
        """Add spine related items to datapackage's descriptor."""
        for resource in self.datapackage.descriptor['resources']:
            if 'Spine_name' not in resource:
                resource.update({'Spine_name': resource['name']})
            for field in resource['schema']['fields']:
                if 'Spine_name' not in field:
                    field.update({'Spine_name': field['name']})
        self.datapackage.commit()

    def init_datapackage_model(self):
        """"""
        self.datapackage_model.clear()
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
        visit(self.datapackage_model, self.datapackage.descriptor)
        self.ui.treeView_datapackage.resizeColumnToContents(0)

    def datapackage_model_data(self, index, role=Qt.DisplayRole):
        """Returns enabled flags for the given index.

        Args:
            index (QModelIndex): Index of Tool
        """
        if role == Qt.FontRole:
            if 'Spine' in index.sibling(index.row(), 0).data(Qt.DisplayRole):
                return self.bold_font
        return QStandardItemModel.data(self.datapackage_model, index, role)

    def datapackage_model_flags(self, index):
        """Returns enabled flags for the given index.

        Args:
            index (QModelIndex): Index of Tool
        """
        if index.column() == 1 and 'Spine' in index.sibling(index.row(), 0).data(Qt.UserRole):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def datapackage_model_header_data(self, section, orientation, role=Qt.DisplayRole):
        """Set headers."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                h = self.datapackage_model_header[section]
            except IndexError:
                return None
            return h
        else:
            return None

    @Slot("QModelIndex", name="resize_treeview_datapackage")
    def resize_treeview_datapackage(self, index):
        self.ui.treeView_datapackage.resizeColumnToContents(0)

    @Slot("QModelIndex", "QModelIndex", name="populate_resource_table")
    def populate_resource_table(self, current, previous):
        """Populate resource tableView whenever a resource item is selected in the treeView"""
        index = current
        selected_resource = None
        while index.parent().isValid():
            if index.parent().data(Qt.UserRole) == 'resources':
                selected_resource = index.data(Qt.UserRole)  # resource pos in json array
                break
            index = index.parent()
        if selected_resource is None:
            return
        if self.selected_resource == selected_resource:  # selected resource not changed
            return
        self.selected_resource = selected_resource
        resource = self.datapackage.resources[self.selected_resource]
        table = resource.read(cast=False)
        self.resource_data_model.header = resource.schema.field_names
        self.resource_data_model.reset_model(table)
        self.ui.tableView_resource_data.resizeColumnsToContents()

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_datapackage")
    def update_datapackage(self, editor, hint):
        """Update datapackage with newly edited data.
        """
        index = editor.index
        if not self.datapackage_model.setData(index, editor.text(), Qt.DisplayRole):
            return
        keys = list()
        final_key = index.sibling(index.row(), 0).data(Qt.DisplayRole)
        index = index.parent()
        while index.isValid():
            keys.append(index.data(Qt.UserRole))
            index = index.parent()
        item = self.datapackage.descriptor
        for key in reversed(keys):
            item = item[key]
        item[final_key] = editor.text()
        # if field name has changed update resource data table header.
        if 'fields' in keys and 'name' == final_key:
            section = keys[keys.index('fields')-1]  # section is one position before 'fields'
            self.resource_data_model.setHeaderData(section, Qt.Horizontal, editor.text())
        self.datapackage.commit()

    @Slot(name="call_edit_resource_Spine_names")
    def call_edit_resource_Spine_names(self):
        config = self._parent.get_conf()
        tip = config.getboolean("settings", "show_resource_Spine_names_tip")
        if tip:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Resource Spine-names")
            msg.setText("Resource Spine-names are used for mapping datapackage resources "
                        "to Spine object classes. "
                        "<b>By setting a resource's Spine-name, you can control how its data is processed "
                        "when the datapackage is converted to Spine format</b>, "
                        "as per the following rule:"
                        "<ul><li>If a resource's Spine-name is one of Spine object class names, "
                        "then its data is used "
                        "to create objects, parameters, and relationships for that class.</li></ul>")
            msg.setInformativeText("Click Ok to edit resource Spine-names.")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            chkbox = QCheckBox()
            chkbox.setText("Do not show this message again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()  # Show message box
            if answer == QMessageBox.Cancel:
                return
            if answer == QMessageBox.Ok:
                # Update conf file according to checkbox status
                if not chkbox.checkState():
                    show_tip = True
                else:
                    show_tip = False
                config.setboolean("settings", "show_resource_Spine_names_tip", show_tip)
        self.edit_resource_Spine_names()

    @Slot(name="call_edit_field_Spine_names")
    def call_edit_field_Spine_names(self):
        config = self._parent.get_conf()
        tip = config.getboolean("settings", "show_field_Spine_names_tip")
        if tip:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Field Spine-names")
            msg.setText("Field Spine-names are used for mapping datapackage fields "
                        "to Spine relationship classes and parameters. "
                        "<b>By setting a field's Spine-name, you can control how its data is processed "
                        "when the datapackage is converted to Spine format</b>, "
                        "as per the following rules:"
                        "<ul><li>If a field's Spine-name is the same as the resource where it belongs, "
                        "then it is considered a <b>primary key</b> "
                        "and its value is used to name the objects of the class associated "
                        "with the resource.</li></ul>"
                        "<ul><li>If a field's Spine-name <i>contains</i> the Spine-name of a resource, "
                        "then it is considered a <b>foreign key</b> "
                        "and its value is looked up in the <b>primary key</b> "
                        "of the referenced resource to create a relationship "
                        " between the two associated classes.</li></ul>")
            msg.setInformativeText("Click Ok to edit field Spine-names.")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            chkbox = QCheckBox()
            chkbox.setText("Do not show this message again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()  # Show message box
            if answer == QMessageBox.Cancel:
                return
            if answer == QMessageBox.Ok:
                # Update conf file according to checkbox status
                if not chkbox.checkState():
                    show_tip = True
                else:
                    show_tip = False
                config.setboolean("settings", "show_field_Spine_names_tip", show_tip)
        self.edit_field_Spine_names()

    def edit_resource_Spine_names(self, resource_name_list=None):
        if not resource_name_list:
            resource_name_list = self.datapackage.resource_names
        question = {}
        for name in resource_name_list:
            resource_Spine_name_list = list()
            resource_Spine_name_list.append("Select Spine-name for " + name + "...")
            resource_Spine_name_list.extend(self.object_class_name_list)
            question.update({name: resource_Spine_name_list})
        dialog = CustomQDialog(None, "Edit resource Spine-names", **question)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for name in dialog.answer:
            ind = dialog.answer[name]['index']
            if ind == 0:
                continue
            new_name = dialog.answer[name]['text']
            resource = self.datapackage.get_resource(name)
            resource.descriptor['Spine_name'] = new_name
            resource.commit()
            resource_name_list.remove(name)
            # TODO: update datapackage tree model

    def edit_field_Spine_names(self, field_name_list=None):
        if not field_name_list:
            question = {}
            resource_name_list = list()
            resource_name_list.append("Select resource...")
            resource_name_list.extend(self.datapackage.resource_names)
            question.update({'resource_name_list': resource_name_list})
            dialog = CustomQDialog(None, "Edit field Spine-names", **question)
            answer = dialog.exec_()
            if answer != QDialog.Accepted:
                return
            ind = dialog.answer['resource_name_list']['index']
            if ind == 0:
                return
            resource_name = resource_name_list[ind]
            field_name_list = self.datapackage.get_resource(resource_name).schema.field_names
        question = {}
        for name in field_name_list:
            question.update({name: "Type Spine-name for " + name + "..."})
        dialog = CustomQDialog(None, "Edit field Spine-names", **question)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        for name in dialog.answer:
            ind = dialog.answer[name]['index']
            if ind == 0:
                continue
            new_name = dialog.answer[name]['text']
        # TODO: eventually finish this

    @Slot(name="convert_triggered")
    def convert_triggered(self):
        unsupported_names = list()
        for resource in self.datapackage.resources:
            if resource.descriptor['Spine_name'] not in self.object_class_name_list:
                unsupported_names.append(resource.descriptor['Spine_name'])
        if unsupported_names:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Unsupported resource Spine-names")
            msg.setText("Resource Spine-names are used for mapping datapackage resources "
                        "to Spine object classes. "
                        "<b>If a resource's Spine-name is one of Spine object class names, "
                        "then its data will be used by the conversion process "
                        "to create objects, parameters, and relationships for that class.</b>")
            msg.setInformativeText("Some resources in the datapackage have unsupported Spine-names. "
                                   "Do you want to edit them before continuing?")
            msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.No | QMessageBox.Yes)
            answer = msg.exec_()  # Show message box
            if answer == QMessageBox.Cancel:
                return
            if answer == QMessageBox.Yes:
                self.edit_resource_Spine_names(unsupported_names)
        self.convert()

    @busy_effect
    def convert(self):
        for resource in self.datapackage.resources:
            object_class_name = resource.descriptor['Spine_name']
            if object_class_name not in self.object_class_name_list:
                continue
            object_class_id = self.session.query(self.ObjectClass.id).\
                filter_by(name=object_class_name).one().id
            relationship_class_id_dict = dict()
            parameter_id_dict = dict()
            field_Spine_name_list = list()
            for field in resource.schema.fields:
                field_Spine_name_list.append(field.descriptor['Spine_name'])
                # Fields whose name contains an object_class name are taken as relationships
                matched = list(filter(lambda x: x in field.descriptor['Spine_name'], self.object_class_name_list))
                if matched:
                    # Relationship class
                    child_object_class_id = self.session.query(self.ObjectClass.id).\
                        filter_by(name=matched[0]).one().id
                    name = resource.descriptor['Spine_name'] + "_" + field.descriptor['Spine_name']
                    relationship_class = self.RelationshipClass(
                        commit_id=1,
                        parent_object_class_id=object_class_id,
                        child_object_class_id=child_object_class_id,
                        name=name
                    )
                    self.session.add(relationship_class)
                    try:
                        self.session.flush()
                        relationship_class_id_dict[field.descriptor['Spine_name']] = relationship_class.id
                    except DBAPIError as e:
                        msg = ("Failed to insert relationship class {0} "
                              "for object class {1}: {2}".format(name, object_class_name, e.orig.args))
                        self.ui.statusbar.showMessage(msg, 5000)
                        self.session.rollback()
                        return
                else:
                    # Parameter
                    name = field.descriptor['Spine_name']
                    parameter = self.Parameter(
                        commit_id=1,
                        object_class_id=object_class_id,
                        name=name
                    )
                    self.session.add(parameter)
                    try:
                        self.session.flush()
                        parameter_id_dict[field.descriptor['Spine_name']] = parameter.id
                    except DBAPIError as e:
                        msg = ("Failed to insert parameter {0} "
                               "for object class {1}: {2}".format(name, object_class_name, e.orig.args))
                        self.ui.statusbar.showMessage(msg, 5000)
                        self.session.rollback()
                        return
            for i, row in enumerate(resource.iter(cast=False)):
                row_dict = dict(zip(field_Spine_name_list, row))
                # If a field is named after the object class, it contains the object name
                if resource.descriptor['Spine_name'] in row_dict:
                    object_name = row[resource.descriptor['Spine_name']]
                else:
                    object_name = resource.descriptor['Spine_name'] + str(i)
                object_ = self.Object(
                    commit_id=1,
                    class_id=object_class_id,
                    name=object_name
                )
                self.session.add(object_)
                try:
                    self.session.flush()
                    object_id = object_.id
                except DBAPIError as e:
                    msg = "Failed to insert object {}: {}".format(object_name, e.orig.args)
                    self.ui.statusbar.showMessage(msg, 5000)
                    self.session.rollback()
                    return
                for key, value in row_dict.items():
                    if key == resource.descriptor['Spine_name']:
                        continue
                    elif key in relationship_class_id_dict:
                        relationship_class_id = relationship_class_id_dict[key]
                        relationship_name = object_name + key
                        relationship = self.Relationship(
                            commit_id=1,
                            class_id=relationship_class_id,
                            parent_object_id=object_id,
                            child_object_id=value,  # FIXME: get the right id from inspecting the target object
                            name=relationship_name
                        )
                        self.session.add(relationship)
                        try:
                            self.session.flush()
                            object_id = object_.id
                        except DBAPIError as e:
                            msg = "Failed to insert relationship {}: {}".format(key, e.orig.args)
                            self.ui.statusbar.showMessage(msg, 5000)
                            self.session.rollback()
                            return
                    elif key in parameter_id_dict:
                        parameter_id = parameter_id_dict[key]
                        parameter_value = self.ParameterValue(
                            commit_id=1,
                            object_id=object_id,
                            parameter_id=parameter_id,
                            value=value
                        )
                        self.session.add(parameter_value)
                        try:
                            self.session.flush()
                            object_id = object_.id
                        except DBAPIError as e:
                            msg = "Failed to insert parameter value {}: {}".format(key, e.orig.args)
                            self.ui.statusbar.showMessage(msg, 5000)
                            self.session.rollback()
                            return
        self.session.commit()
        target_filename = os.path.join(self._data_connection.data_dir, 'Spine.sqlite')
        try:
            shutil.copy(self.temp_filename, target_filename)
        except OSError:
            msg = "Conversion failed. [OSError] Unable to copy file from temporary location."
            self.ui.statusbar.showMessage(msg, 5000)
            return
        msg = "Conversion finished. File 'Spine.sqlite' saved in {}".format(self._data_connection.data_dir)
        self.ui.statusbar.showMessage(msg, 5000)
        # Clean up
        try:
            self.session.query(self.Object).delete()
            self.session.query(self.RelationshipClass).delete()
            self.session.query(self.Relationship).delete()
            self.session.query(self.Parameter).delete()
            self.session.query(self.ParameterValue).delete()
            self.session.query(self.Commit).delete()
            self.session.flush()
        except Exception as e:
            msg = "Could not clean up session: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)

    @Slot("QPoint", name="show_datapackage_tree_context_menu")
    def show_datapackage_tree_context_menu(self, pos):
        """Context menu for datapackage treeview.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_datapackage.indexAt(pos)
        global_pos = self.ui.treeView_datapackage.viewport().mapToGlobal(pos)
        self.datapackage_tree_context_menu = DatapackageTreeContextMenu(self, global_pos, index)
        option = self.datapackage_tree_context_menu.get_action()
        if option == "Expand all children":
            self.ui.treeView_datapackage.expand(index)
            if not self.datapackage_model.hasChildren(index):
                return
            for i in range(self.datapackage_model.rowCount(index)):
                child_index = self.datapackage_model.index(i, 0, index)
                self.ui.treeView_datapackage.expand(child_index)
        elif option == "Collapse all children":
            self.ui.treeView_datapackage.collapse(index)
            if not self.datapackage_model.hasChildren(index):
                return
            for i in range(self.datapackage_model.rowCount(index)):
                child_index = self.datapackage_model.index(i, 0, index)
                self.ui.treeView_datapackage.collapse(child_index)

    def closeEvent(self, event=None):
        """Handle close window.

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
