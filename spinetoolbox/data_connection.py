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
Module for data connection class.

:author: P. Savolainen (VTT)
:date:   19.12.2017
"""

import os
import shutil
import logging
from collections import Counter
from PySide2.QtCore import Slot, QUrl, QFileSystemWatcher, Qt
from PySide2.QtGui import QDesktopServices, QStandardItem, QStandardItemModel, QIcon, QPixmap
from PySide2.QtWidgets import QFileDialog, QMessageBox
from project_item import ProjectItem
from widgets.spine_datapackage_widget import SpineDatapackageWidget
from helpers import create_dir
from config import APPLICATION_PATH, HEADER_POINTSIZE
from datapackage import Package
from graphics_items import DataConnectionImage


class DataConnection(ProjectItem):
    """Data Connection class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        references (list): List of file references
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """
    def __init__(self, toolbox, name, description, references, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "Data Connection"
        # self._widget = DataConnectionWidget(self, self.item_type)
        self.reference_model = QStandardItemModel()  # References to files
        self.data_model = QStandardItemModel()  # Paths of project internal files. These are found in DC data directory
        self.datapackage_icon = QIcon(QPixmap(":/icons/datapkg.png"))
        self.data_dir_watcher = QFileSystemWatcher(self)
        # Make project directory for this Data Connection
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
            self.data_dir_watcher.addPath(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit("[OSError] Creating directory {0} failed."
                                         " Check permissions.".format(self.data_dir))
        # Populate references model
        self.references = references
        self.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = self.data_files()
        self.populate_data_list(data_files)
        self._graphics_item = DataConnectionImage(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self.spine_datapackage_form = None
        # self.ui.toolButton_datapackage.setMenu(self.datapackage_popup_menu)  # TODO: OBSOLETE?
        self._sigs = self.make_signal_handler_dict()

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._toolbox.ui.pushButton_dc_open.clicked] = self.open_directory
        s[self._toolbox.ui.toolButton_plus.clicked] = self.add_references
        s[self._toolbox.ui.toolButton_minus.clicked] = self.remove_references
        s[self._toolbox.ui.toolButton_add.clicked] = self.copy_to_project
        s[self._toolbox.ui.toolButton_datapackage.clicked] = self.call_infer_datapackage
        s[self._toolbox.ui.treeView_dc_references.doubleClicked] = self.open_reference
        s[self._toolbox.ui.treeView_dc_data.doubleClicked] = self.open_data_file
        s[self.data_dir_watcher.directoryChanged] = self.refresh
        s[self._toolbox.ui.treeView_dc_references.files_dropped] = self.add_files_to_references
        s[self._toolbox.ui.treeView_dc_data.files_dropped] = self.add_files_to_data_dir
        s[self._graphics_item.master().scene().files_dropped_on_dc] = self.receive_files_dropped_on_dc
        return s

    def activate(self):
        """Restore selections and connect signals."""
        self.restore_selections()  # Do this before connecting signals or funny things happen
        super().connect_signals()

    def deactivate(self):
        """Save selections and disconnect signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item {0} deactivation failed".format(self.name))
            return False
        return True

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_dc_name.setText(self.name)
        self._toolbox.ui.treeView_dc_references.setModel(self.reference_model)
        self._toolbox.ui.treeView_dc_data.setModel(self.data_model)
        self.refresh()

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""
        pass

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this data connection in the scene."""
        return self._graphics_item

    @Slot("QVariant", name="add_files_to_references")
    def add_files_to_references(self, paths):
        """Add multiple file paths to reference list.

        Args:
            paths (list): A list of paths to files
        """
        for path in paths:
            if path in self.references:
                self._toolbox.msg_warning.emit("Reference to file <b>{0}</b> already available".format(path))
                return
            self.references.append(os.path.abspath(path))
        self.populate_reference_list(self.references)

    @Slot("QGraphicsItem", "QVariant", name="receive_files_dropped_on_dc")
    def receive_files_dropped_on_dc(self, item, file_paths):
        """Called when files are dropped onto a data connection graphics item.
        If the item is this Data Connection's graphics item, add the files to data."""
        if item == self._graphics_item:
            self.add_files_to_data_dir(file_paths)

    @Slot("QVariant", name="add_files_to_data_dir")
    def add_files_to_data_dir(self, file_paths):
        """Add files to data directory"""
        for file_path in file_paths:
            src_dir, filename = os.path.split(file_path)
            self._toolbox.msg.emit("Copying file <b>{0}</b>".format(filename))
            try:
                shutil.copy(file_path, self.data_dir)
            except OSError:
                self._toolbox.msg_error.emit("[OSError] Copying failed")
                return
        data_files = self.data_files()
        self.populate_data_list(data_files)

    @Slot(bool, name="open_directory")
    def open_directory(self, checked):
        """Open file explorer in Data Connection data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(bool, name="add_references")
    def add_references(self, checked):
        """Let user select references to files for this data connection."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileNames(self._toolbox, "Add file references", APPLICATION_PATH, "*.*")
        file_paths = answer[0]
        if not file_paths:  # Cancel button clicked
            return
        for path in file_paths:
            if path in self.references:
                self._toolbox.msg_warning.emit("Reference to file <b>{0}</b> already available".format(path))
                continue
            self.references.append(os.path.abspath(path))
        self.populate_reference_list(self.references)

    @Slot(bool, name="remove_references")
    def remove_references(self, checked):
        """Remove selected references from reference list.
        Removes all references if nothing is selected.
        """
        indexes = self._toolbox.ui.treeView_dc_references.selectedIndexes()
        if not indexes:  # Nothing selected
            self.references.clear()
            self._toolbox.msg.emit("All references removed")
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.references.pop(row)
            self._toolbox.msg.emit("Selected references removed")
        self.populate_reference_list(self.references)

    @Slot(bool, name="copy_to_project")
    def copy_to_project(self, checked):
        """Copy files in the file reference list to project and update Data QTreeView."""
        if not self.references:
            self._toolbox.msg_warning.emit("No files to copy")
            return
        self._toolbox.msg.emit("Copying files to {0}".format(self.data_dir))
        for file_path in self.references:
            if not os.path.exists(file_path):
                self._toolbox.msg_error.emit("File <b>{0}</b> does not exist".format(file_path))
                continue
            src_dir, filename = os.path.split(file_path)
            self._toolbox.msg.emit("Copying file <b>{0}</b>".format(filename))
            try:
                shutil.copy(file_path, self.data_dir)
            except OSError:
                self._toolbox.msg_error.emit("[OSError] Copying failed")
                continue
        data_files = self.data_files()
        self.populate_data_list(data_files)

    @Slot("QModelIndex", name="open_reference")
    def open_reference(self, index):
        """Open reference in default program."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        else:
            reference = self.file_references()[index.row()]
            url = "file:///" + reference
            # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
            res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
            if not res:
                self._toolbox.msg_error.emit("Failed to open reference:<b>{0}</b>".format(reference))

    @Slot("QModelIndex", name="open_data_file")
    def open_data_file(self, index):
        """Open data file in default program."""
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        else:
            data_file = self.data_files()[index.row()]
            if data_file == "datapackage.json":
                self.show_spine_datapackage_form()
            else:
                url = "file:///" + os.path.join(self.data_dir, data_file)
                # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
                res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
                if not res:
                    self._toolbox.msg_error.emit("Failed to open file:<b>{0}</b>".format(data_file))

    @Slot(bool, name="call_infer_datapackage")
    def call_infer_datapackage(self, checked):
        """Infer datapackage from CSV files in data directory."""
        data_files = self.data_files()
        if not ".csv" in [os.path.splitext(f)[1] for f in data_files]:
            self._toolbox.msg_error.emit("The folder <b>{0}</b> does not have any CSV files. "
                                         "Add some and try again".format(self.data_dir))
            return
        self.infer_datapackage()

    def infer_datapackage(self):
        """Infer datapackage from CSV files in data directory and save it."""
        msg = "Inferring datapackage from {}".format(self.data_dir)
        self._toolbox.msg.emit(msg)
        datapackage = CustomPackage(base_path=self.data_dir)
        datapackage.infer(os.path.join(self.data_dir, '*.csv'))
        self.save_datapackage(datapackage)

    def save_datapackage(self, datapackage):
        """Write datapackage to file 'datapackage.json' in data directory."""
        if os.path.isfile(os.path.join(self.data_dir, "datapackage.json")):
            msg = ('<b>Replacing file "datapackage.json" in "{}"</b>. '
                   'Are you sure?').format(os.path.basename(self.data_dir))
            # noinspection PyCallByClass, PyTypeChecker
            answer = QMessageBox.question(
                self._toolbox, 'Replace "datapackage.json"', msg, QMessageBox.Yes, QMessageBox.No)
            if not answer == QMessageBox.Yes:
                return False
        if datapackage.save(os.path.join(self.data_dir, 'datapackage.json')):
            msg = '"datapackage.json" saved in {}'.format(self.data_dir)
            self._toolbox.msg.emit(msg)
            return True
        msg = 'Failed to save "datapackage.json" in {}'.format(self.data_dir)
        self._toolbox.msg_error.emit(msg)
        return False

    def load_datapackage(self):
        """Load datapackage from 'datapackage.json' file in data directory."""
        file_path = os.path.join(self.data_dir, "datapackage.json")
        if not os.path.exists(file_path):
            return None
        datapackage = CustomPackage(file_path)
        msg = "Datapackage loaded from {}".format(file_path)
        self._toolbox.msg.emit(msg)
        return datapackage

    def show_spine_datapackage_form(self):
        """Show spine_datapackage_form widget."""
        if self.spine_datapackage_form:
            self.spine_datapackage_form.raise_()
            return
        datapackage = self.load_datapackage()
        if not datapackage:
            return
        self.spine_datapackage_form = SpineDatapackageWidget(self._toolbox, self, datapackage)
        self.spine_datapackage_form.destroyed.connect(self.datapackage_form_destroyed)
        self.spine_datapackage_form.show()

    @Slot(name="datapackage_form_destroyed")
    def datapackage_form_destroyed(self):
        self.spine_datapackage_form = None

    def file_references(self):
        """Return a list of paths to files that are in this item as references (self.references)."""
        return self.references

    def data_files(self):
        """Return a list of files that are in the data directory."""
        if not os.path.isdir(self.data_dir):
            return None
        return os.listdir(self.data_dir)

    @Slot(name="refresh")
    def refresh(self):
        """Refresh data files QTreeView.
        NOTE: Might lead to performance issues."""
        d = self.data_files()
        self.populate_data_list(d)

    def find_file(self, fname, visited_items):
        """Search for filename in references and data and return the path if found."""
        # logging.debug("Looking for file {0} in DC {1}.".format(fname, self.name))
        if self in visited_items:
            self._toolbox.msg_warning.emit("There seems to be an infinite loop in your project. Please fix the "
                                           "connections and try again. Detected at {0}.".format(self.name))
            return None
        if fname in self.data_files():
            # logging.debug("{0} found in DC {1}".format(fname, self.name))
            self._toolbox.msg.emit("\t<b>{0}</b> found in Data Connection <b>{1}</b>".format(fname, self.name))
            path = os.path.join(self.data_dir, fname)
            return path
        for path in self.file_references():  # List of paths including file name
            p, fn = os.path.split(path)
            if fn == fname:
                # logging.debug("{0} found in DC {1}".format(fname, self.name))
                self._toolbox.msg.emit("\tReference for <b>{0}</b> found in Data Connection <b>{1}</b>"
                                       .format(fname, self.name))
                return path
        visited_items.append(self)
        for input_item in self._toolbox.connection_model.input_items(self.name):
            # Find item from project model
            found_index = self._toolbox.project_item_model.find_item(input_item)
            if not found_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(found_index)
            if item.item_type in ["Data Store", "Data Connection"]:
                path = item.find_file(fname, visited_items)
                if path is not None:
                    return path
        return None

    def add_reference_header(self):
        """Add header to files model. I.e. External Data Connection files."""
        h = QStandardItem("References")
        # Decrease font size
        font = h.font()
        font.setPointSize(HEADER_POINTSIZE)
        h.setFont(font)
        self.reference_model.setHorizontalHeaderItem(0, h)

    def add_data_header(self):
        """Add header to data model. I.e. Internal Data Connection files."""
        h = QStandardItem("Data")
        # Decrease font size
        font = h.font()
        font.setPointSize(HEADER_POINTSIZE)
        h.setFont(font)
        self.data_model.setHorizontalHeaderItem(0, h)

    def populate_reference_list(self, items):
        """List file references in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.reference_model.clear()
        self.add_reference_header()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                qitem.setData(item, Qt.ToolTipRole)
                self.reference_model.appendRow(qitem)

    def populate_data_list(self, items):
        """List project internal data (files) in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.data_model.clear()
        self.add_data_header()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                if item == 'datapackage.json':
                    qitem.setData(self.datapackage_icon, Qt.DecorationRole)
                self.data_model.appendRow(qitem)

    def update_name_label(self):
        """Update Data Connection tab name label. Used only when renaming project items."""
        self._toolbox.ui.label_dc_name.setText(self.name)


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
        if old in primary_key:
            primary_key_index = primary_key.index(old)
            resource_dict['schema']['primaryKey'][primary_key_index] = new
        # TODO: also rename the field in foreign keys
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

    def add_foreign_key(self, child_table, child_field, parent_table, parent_field):
        """Add foreign key to a given resource in the package"""
        foreign_key = {
            "fields": [child_field],
            "reference": {
                "resource": parent_table,
                "fields": [parent_field]
            }
        }
        i = self.resource_names.index(child_table)
        self.descriptor['resources'][i]['schema'].setdefault('foreignKeys', [])
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

    def remove_foreign_key(self, child_table, child_field, parent_table, parent_field):
        """Remove foreign key from the package"""
        i = self.resource_names.index(child_table)
        foreign_key = {
            "fields": [child_field],
            "reference": {
                "resource": parent_table,
                "fields": [parent_field]
            }
        }
        if 'foreignKeys' in self.descriptor['resources'][i]['schema']:
            if foreign_key in self.descriptor['resources'][i]['schema']['foreignKeys']:
                self.descriptor['resources'][i]['schema']['foreignKeys'].remove(foreign_key)
                self.commit()
