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

import os
import shutil
import logging
from config import STATUSBAR_SS
from ui.spine_datapackage_form import Ui_MainWindow
from widgets.lineedit_delegate import LineEditDelegate
from widgets.custom_menus import DescriptorTreeContextMenu
from widgets.custom_qdialog import EditDatapackagePrimaryKeysDialog
from PySide2.QtWidgets import QMainWindow, QHeaderView, QMessageBox, QDialog
from PySide2.QtCore import Qt, Signal, Slot, QSettings, SIGNAL
from PySide2.QtGui import QStandardItemModel, QStandardItem, QFont, QFontMetrics
from helpers import busy_effect
from models import MinimalTableModel, DatapackageDescriptorModel
from spinedatabase_api import SpineDBAPIError


class SpineDatapackageWidget(QMainWindow):
    """A widget to allow user to edit a datapackage and convert it
    to a Spine database in SQLite.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        data_connection (DataConnection): Data Connection associated to this widget
        datapackage (CustomPackage): Datapackage to load and use
        mapping (DatabaseMapping): Mapping to an empty sqlite database to work with
        temp_filename (str): The sqlite filename
    """

    msg = Signal(str, name="msg")
    msg_error = Signal(str, str, str, name="msg_error")

    def __init__(self, parent, data_connection, datapackage, mapping, temp_filename):
        """Initialize class."""
        super().__init__(flags=Qt.Window)
        self._parent = parent
        self._data_connection = data_connection
        self.output_data_stores = None
        self.mapping = mapping
        self.temp_filename = temp_filename
        self.object_class_name_list = [item.name for item in self.mapping.object_class_list()]
        self.datapackage = datapackage
        self.block_resource_name_combobox = True
        self.descriptor_tree_context_menu = None
        self.current_resource_name = None
        self.resource_tables = dict()
        self.export_name = self._data_connection.name + '.sqlite'
        self.descriptor_model = DatapackageDescriptorModel(self)
        self.descriptor_model.header.extend(["Key", "Value"])
        self.resource_data_model = MinimalTableModel()
        #  Set up the user interface from Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox datapackage form")
        self.restore_ui()
        # Add status bar to form
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # Set name of export action
        self.ui.actionExport.setText("Export as '{0}'".format(self.export_name))
        self.ui.treeView_descriptor.setModel(self.descriptor_model)
        self.ui.tableView_resource_data.setModel(self.resource_data_model)
        self.ui.tableView_resource_data.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_resource_data.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.load_resource_data()
        self.descriptor_model.build_tree(self.datapackage.descriptor)
        self.resize_descriptor_treeview()
        self.connect_signals()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        self._data_connection.destroyed.connect(self.close)
        self.ui.treeView_descriptor.expanded.connect(self.resize_descriptor_treeview)
        self.ui.treeView_descriptor.collapsed.connect(self.resize_descriptor_treeview)
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionExport.triggered.connect(self.export)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        self.ui.actionPrimary_keys.triggered.connect(self.edit_primary_keys)
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_resource_data)
        self.ui.tableView_resource_data.setItemDelegate(lineedit_delegate)
        self.ui.treeView_descriptor.selectionModel().currentChanged.connect(self.update_current_resource_name)
        self.ui.treeView_descriptor.customContextMenuRequested.connect(self.show_descriptor_tree_context_menu)
        self.ui.comboBox_resource_name.currentTextChanged.connect(self.update_resource_name)

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

    def load_resource_data(self):
        """Load resource data into a local list of tables."""
        for resource in self.datapackage.resources:
            table = list()
            table.append(resource.schema.field_names)
            table.extend(resource.read(cast=False))
            self.resource_tables[resource.name] = table

    @Slot(name="save_datapackage")
    def save_datapackage(self):  #TODO: handle zip as well?
        """Save datapackage.json to datadir."""
        self._data_connection.save_datapackage(self.datapackage)

    def edit_primary_keys(self):
        """Show dialog to edit primary keys."""
        dialog = EditDatapackagePrimaryKeysDialog(self, self.datapackage)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        print("to remove {}".format(dialog.keys_to_remove))
        print("to set {}".format(dialog.keys_to_set))
        # First remove, then set
        for row in dialog.keys_to_remove:
            self.datapackage.remove_primary_key(*row)
            self.descriptor_model.remove_primary_key(*row)
        for row in dialog.keys_to_set:
            self.datapackage.set_primary_key(*row)
            self.descriptor_model.set_primary_key(*row)

    @Slot("QModelIndex", name="resize_descriptor_treeview")
    def resize_descriptor_treeview(self, index=None):
        self.ui.treeView_descriptor.resizeColumnToContents(0)

    @Slot("QModelIndex", "QModelIndex", name="update_current_resource_name")
    def update_current_resource_name(self, current, previous):
        """Update current resource name whenever a new resource item is selected
        in the descriptor treeView."""
        index = current
        selected_resource_name = None
        while index.parent().isValid():
            if index.parent().data(Qt.DisplayRole) == 'resources':
                selected_resource_name = index.data(Qt.DisplayRole)  # resource name
                break
            index = index.parent()
        if selected_resource_name is None:
            return
        if self.current_resource_name == selected_resource_name:  # selected resource not changed
            return
        self.current_resource_name = selected_resource_name
        self.reset_resource_data_model()
        self.reset_resource_name_combo()

    def reset_resource_data_model(self):
        """Reset resource data model with data from currently selected resource."""
        table = self.resource_tables[self.current_resource_name]
        self.resource_data_model.header = table[0]  # We need a header for columnCount in MinimalTableModel
        self.resource_data_model.reset_model(table)
        gray_background = self._parent.palette().button()
        for column in range(self.resource_data_model.columnCount()):
            index = self.resource_data_model.index(0, column)
            self.resource_data_model.setData(index, gray_background, Qt.BackgroundRole)
        self.ui.tableView_resource_data.resizeColumnsToContents()

    def reset_resource_name_combo(self):
        """Reset resource name combo according to currently selected resource."""
        self.block_resource_name_combobox = True
        self.ui.comboBox_resource_name.clear()
        self.ui.comboBox_resource_name.addItems(self.object_class_name_list)
        font_metric = QFontMetrics(QFont("", 0))
        max_resource_name_width = max(font_metric.width(x) for x in self.object_class_name_list)
        max_width = max_resource_name_width
        if self.current_resource_name not in self.object_class_name_list:
            self.ui.comboBox_resource_name.insertItem(0, self.current_resource_name + ' (unsupported)')
            self.ui.comboBox_resource_name.setCurrentIndex(0)
            width = font_metric.width(self.current_resource_name + ' (unsupported)')
            max_width = max(max_width, width)
        else:
            ind = self.object_class_name_list.index(self.current_resource_name)
            self.ui.comboBox_resource_name.setCurrentIndex(ind)
        # Set combobox width based on items
        self.ui.comboBox_resource_name.setMinimumWidth(max_width + 24)
        self.block_resource_name_combobox = False

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_resource_data")
    def update_resource_data(self, editor, hint):
        """Update resource data with newly edited data."""
        index = editor.index
        # Save old name to look up field in datapackage and descriptor model
        old_name = index.data(Qt.DisplayRole)
        if not self.resource_data_model.setData(index, editor.text(), Qt.EditRole):
            return
        self.ui.tableView_resource_data.resizeColumnsToContents()
        self.resource_tables[self.current_resource_name][index.row()][index.column()] = editor.text()
        # Update descriptor in datapackage in case a field name was modified
        if index.row() == 0:
            self.update_field_name(old_name, editor.text())

    def update_field_name(self, old_name, new_name):
        """Update descriptor (datapackage and model) with new field name
        from resource data table."""
        self.datapackage.rename_field(self.current_resource_name, old_name, new_name)
        self.descriptor_model.rename_field(self.current_resource_name, old_name, new_name)

    @Slot("str", name="update_resource_name")
    def update_resource_name(self, new_name):
        """Update descriptor (datapackage and model) with new resource name from comboBox."""
        if self.block_resource_name_combobox:
            return
        # Update resource table
        resource_data = self.resource_tables.pop(self.current_resource_name, None)
        if resource_data is None:
            msg = "Couldn't find key in resource data dict. Something is wrong."
            self.msg.emit(msg)
            return
        self.resource_tables[new_name] = resource_data
        self.datapackage.rename_resource(self.current_resource_name, new_name)
        self.descriptor_model.rename_resource(self.current_resource_name, new_name)
        self.current_resource_name = new_name
        # Remove unsupported name from combobox
        ind = self.ui.comboBox_resource_name.findText("unsupported", Qt.MatchContains)
        if ind == -1:
            return
        self.block_resource_name_combobox = True
        self.ui.comboBox_resource_name.removeItem(ind)
        self.block_resource_name_combobox = False

    @Slot(name="export")
    def export(self):
        """Check if everything is fine (destination, resource names), launch conversion,
        save output as .sqlite in destination Data Stores' directory, and clean up session
        for future conversions."""
        output_data_directories = list()
        for output_item in self._parent.connection_model.output_items(self._data_connection.name):
            found_item = self._parent.project_item_model.find_item(output_item, Qt.MatchExactly | Qt.MatchRecursive)
            if found_item:
                if found_item.data(Qt.UserRole).item_type == 'Data Store':
                    output_data_directories.append(found_item.data(Qt.UserRole).data_dir)
        if not output_data_directories:
            title = "Destination not found"
            text = ("The datapackage cannot be exported because the Data Connection <b>{}</b> "
                    "is not connected to any destination Data Stores.").format(self._data_connection.name)
            info = "Connect <b>{}</b> to a Data Store and try again.".format(self._data_connection.name)
            self.msg_error.emit(title, text, info)
            return
        unsupported_names = list()
        for resource in self.datapackage.resources:
            if resource.name not in self.object_class_name_list:
                unsupported_names.append(resource.name)
        if unsupported_names:
            text = ("The following resources have unsupported names "
                    "and will be ignored by the conversion process:<ul>")
            for name in unsupported_names:
                text += "<li>{}</li>".format(name)
            text += "</ul>"
            text += ("Do you want to proceed anyway?")
            answer = QMessageBox.question(None, 'Unsupported resource names"', text, QMessageBox.Yes, QMessageBox.Cancel)
            if answer != QMessageBox.Yes:
                return
        if not self.convert():
            return
        for data_dir in output_data_directories:
            target_filename = os.path.join(data_dir, self.export_name)
            try:
                shutil.copy(self.temp_filename, target_filename)
                msg = "File '{0}' saved in {1}".format(self.export_name, data_dir)
                self.msg.emit(msg)
            except OSError:
                msg = "[OSError] Unable to copy file to {}.".format(data_dir)
                self.msg.emit(msg)
        self.mapping.reset()

    @busy_effect
    def convert(self):
        """Convert datapackage to Spine database."""
        self.mapping.new_commit()
        for resource in self.datapackage.resources:
            object_class_name = resource.name
            if object_class_name not in self.object_class_name_list:
                continue
            object_class = self.mapping.single_object_class(name=object_class_name).one_or_none()
            if not object_class:
                continue
            object_class_id = object_class.id
            primary_key = resource.schema.primary_key
            foreign_keys = resource.schema.foreign_keys
            for field in resource.schema.fields:
                if not field.name in primary_key:
                    if not self.try_and_add_parameter(field.name, foreign_keys, object_class_id):
                        self.try_and_add_relationship_class(field.name, foreign_keys, object_class_id)
            for i, row in enumerate(self.resource_tables[resource.name][1:]):
                row_dict = dict(zip(resource.schema.field_names, row))
                object_ = self.try_and_add_object(primary_key, row_dict, object_class_name + str(i), object_class_id)
                if not object_:
                    continue
                object_id = object_.id
                for field_name, value in row_dict.items():
                    if field_name in primary_key:
                        continue
                    self.try_and_add_parameter_value(field_name, foreign_keys, object_id, value)
        try:
            self.mapping.commit_session("Automatically created by Spine Toolbox.")
            return True
        except SpineDBAPIError as e:
            self.msg_error.emit("SpineDBAPIError",  e.msg, "")
            return False

    def try_and_add_parameter(self, field_name, foreign_keys, object_class_id):
        """"""
        if field_name in [x for a in foreign_keys for x in a["fields"]]:
            return False
        try:
            self.mapping.add_parameter(
                object_class_id=object_class_id,
                name=field_name
            )
        except SpineDBAPIError as e:
            self.msg_error.emit("SpineDBAPIError",  e.msg, "")
        return True

    def try_and_add_relationship_class(self, field_name, foreign_keys, object_class_id):
        """"""
        # Find out child object class names from foreign keys
        child_object_class_name_list = list()
        for foreign_key in foreign_keys:
            if field_name in foreign_key['fields']:
                child_object_class_name = foreign_key['reference']['resource']
                if child_object_class_name not in self.object_class_name_list:
                    continue
                child_object_class_name_list.append(child_object_class_name)
        for child_object_class_name in child_object_class_name_list:
            child_object_class = self.mapping.single_object_class(name=child_object_class_name).one_or_none()
            if not child_object_class:
                continue
            relationship_class_name = object_class_name + "_" + child_object_class.name
            try:
                self.mapping.add_wide_relationship_class(
                    object_class_id_list=[object_class_id, child_object_class.id],
                    name=relationship_class_name
                )
            except SpineDBAPIError as e:
                self.msg_error.emit("SpineDBAPIError",  e.msg, "")

    def try_and_add_object(self, primary_key, row_dict, default_name, object_class_id):
        """"""
        if primary_key:
            object_name = "_".join(row_dict[field] for field in primary_key)
        else:
            object_name = default_name
        try:
            object_ = self.mapping.add_object(
                class_id=object_class_id,
                name=object_name
            )
            return object_
        except SpineDBAPIError as e:
            #self.msg_error.emit("SpineDBAPIError",  e.msg, "")
            self.msg.emit(e.msg)
            return None

    def try_and_add_parameter_value(self, field_name, foreign_keys, object_id, value):
        """"""
        if field_name in [x for a in foreign_keys for x in a["fields"]]:
            return
        parameter = self.mapping.single_parameter(name=field_name).one_or_none()
        if not parameter:
            return
        try:
            self.mapping.add_parameter_value(
                object_id=object_id,
                parameter_id=parameter.id,
                value=value
            )
        except SpineDBAPIError as e:
            self.msg_error.emit("SpineDBAPIError",  e.msg, "")

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
        self.mapping.close()
        if event:
            event.accept()
