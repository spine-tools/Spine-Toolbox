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
Module for data connection class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.12.2017
"""

import os
import shutil
import logging
from PySide2.QtCore import Slot, QUrl, QFileSystemWatcher, Qt
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QFileDialog
from metaobject import MetaObject
from widgets.data_connection_subwindow_widget import DataConnectionWidget
from widgets.spine_datapackage_widget import SpineDatapackageWidget
# from widgets.edit_datapackage_keys_widget import EditDatapackageKeysWidget
# from widgets.custom_menus import DatapackagePopupMenu
from helpers import create_dir
from config import APPLICATION_PATH
# from datapackage import Package
from graphics_items import DataConnectionImage

class DataConnection(MetaObject):
    """Data Connection class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        references (list): List of file references
    """
    def __init__(self, parent, name, description, project, references, x, y):
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Data Connection"
        self.item_category = "Data Connections"
        self._project = project
        # self.package = None
        self._widget = DataConnectionWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._widget.make_header_for_references()
        self._widget.make_header_for_data()
        self.data_dir_watcher = QFileSystemWatcher(self)
        # Make directory for Data Connection
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        self.references = references
        try:
            create_dir(self.data_dir)
            self.data_dir_watcher.addPath(self.data_dir)
        except OSError:
            self._parent.msg_error.emit("[OSError] Creating directory {0} failed."
                                        " Check permissions.".format(self.data_dir))
        # Populate references model
        self._widget.populate_reference_list(self.references)
        # Populate data (files) model
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)
        self._graphics_item = DataConnectionImage(self._parent, x - 35, y - 35, 70, 70, self.name)
        self.spine_datapackage_form = None
        self.connect_signals()
        # self.datapackage_popup_menu = DatapackagePopupMenu(self)
        # self._widget.ui.toolButton_datapackage.setMenu(self.datapackage_popup_menu)

    def connect_signals(self):
        """Connect this data connection's signals to slots."""
        self._widget.ui.pushButton_open.clicked.connect(self.open_directory)
        self._widget.ui.toolButton_plus.clicked.connect(self.add_references)
        self._widget.ui.toolButton_minus.clicked.connect(self.remove_references)
        self._widget.ui.toolButton_add.clicked.connect(self.copy_to_project)
        self._widget.ui.toolButton_datapackage.clicked.connect(self.show_spine_datapackage_form)
        self._widget.ui.treeView_references.doubleClicked.connect(self.open_reference)
        self._widget.ui.treeView_data.doubleClicked.connect(self.open_data_file)
        self._widget.ui.treeView_references.file_dropped.connect(self.add_file_to_references)
        self._widget.ui.treeView_data.file_dropped.connect(self.add_file_to_data_dir)
        self.data_dir_watcher.directoryChanged.connect(self.refresh)

    def set_icon(self, icon):
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this data connection in the scene."""
        return self._graphics_item

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    @Slot("QString", name="add_file_to_references")
    def add_file_to_references(self, path):
        """Add filepath to reference list"""
        if path in self.references:
            self._parent.msg_warning.emit("Reference to file <b>{0}</b> already available".format(path))
            return
        self.references.append(os.path.abspath(path))
        self._widget.populate_reference_list(self.references)

    @Slot("QString", name="add_file_to_data_dir")
    def add_file_to_data_dir(self, file_path):
        """Add file to data directory"""
        src_dir, filename = os.path.split(file_path)
        self._parent.msg.emit("Copying file <b>{0}</b>".format(filename))
        try:
            shutil.copy(file_path, self.data_dir)
        except OSError:
            self._parent.msg_error.emit("[OSError] Copying failed")
            return
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)

    @Slot(name="open_directory")
    def open_directory(self):
        """Open file explorer in Data Connection data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._parent.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(name="add_references")
    def add_references(self):
        """Let user select references to files for this data connection."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileNames(self._parent, "Add file references", APPLICATION_PATH, "*.*")
        file_paths = answer[0]
        if not file_paths:  # Cancel button clicked
            return
        for path in file_paths:
            if path in self.references:
                self._parent.msg_warning.emit("Reference to file <b>{0}</b> already available".format(path))
                continue
            self.references.append(os.path.abspath(path))
        self._widget.populate_reference_list(self.references)

    @Slot(name="remove_references")
    def remove_references(self):
        """Remove selected references from reference list.
        Removes all references if nothing is selected.
        """
        indexes = self._widget.ui.treeView_references.selectedIndexes()
        if not indexes:  # Nothing selected
            self.references.clear()
            self._parent.msg.emit("All references removed")
        else:
            rows = [ind.row() for ind in indexes]
            rows.sort(reverse=True)
            for row in rows:
                self.references.pop(row)
            self._parent.msg.emit("Selected references removed")
        self._widget.populate_reference_list(self.references)

    @Slot(name="copy_to_project")
    def copy_to_project(self):
        """Copy files in the file reference list to project and update Data QTreeView."""
        if not self.references:
            self._parent.msg_warning.emit("No files to copy")
            return
        self._parent.msg.emit("Copying files to {0}".format(self.data_dir))
        for file_path in self.references:
            if not os.path.exists(file_path):
                self._parent.msg_error.emit("File <b>{0}</b> does not exist".format(file_path))
                continue
            src_dir, filename = os.path.split(file_path)
            self._parent.msg.emit("Copying file <b>{0}</b>".format(filename))
            try:
                shutil.copy(file_path, self.data_dir)
            except OSError:
                self._parent.msg_error.emit("[OSError] Copying failed")
                continue
        data_files = self.data_files()
        self._widget.populate_data_list(data_files)

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
                self._parent.msg_error.emit("Failed to open reference:<b>{0}</b>".format(reference))

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
            url = "file:///" + os.path.join(self.data_dir, data_file)
            # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
            res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
            if not res:
                self._parent.msg_error.emit("Failed to open file:<b>{0}</b>".format(data_file))

    # @Slot(name="show_edit_keys_form")
    # def show_edit_keys_form(self):
    #     """Show edit keys widget."""
    #     if not os.path.exists(os.path.join(self.data_dir, "datapackage.json")):
    #         self._parent.msg_error.emit("Create a datapackage first.")
    #         return
    #     self.package = CustomPackage(os.path.join(self.data_dir, 'datapackage.json'))
    #     self.edit_datapackage_keys_form = EditDatapackageKeysWidget(self)
    #     self.edit_datapackage_keys_form.show()

    @Slot(name="show_spine_datapackage_form")
    def show_spine_datapackage_form(self):
        """Show spine_datapackage_form widget."""
        self.spine_datapackage_form = SpineDatapackageWidget(self._parent, self)
        self.spine_datapackage_form.show()

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
        self._widget.populate_data_list(d)

    def find_file(self, fname, visited_items):
        """Search for filename in references and data and return the path if found."""
        logging.debug("Looking for file {0} in DC {1}.".format(fname, self.name))
        if self in visited_items:
            logging.debug("Infinite loop detected while visiting {0}.".format(self.name))
            return None
        if fname in self.data_files():
            logging.debug("{0} found in DC {1}".format(fname, self.name))
            self._parent.msg.emit("\t<b>{0}</b> found in DC <b>{1}</b>".format(fname, self.name))
            path = os.path.join(self.data_dir, fname)
            return path
        for path in self.file_references():  # List of paths including file name
            p, fn = os.path.split(path)
            if fn == fname:
                logging.debug("{0} found in DC {1}".format(fname, self.name))
                self._parent.msg.emit("\tReference for <b>{0}</b> found in DC <b>{1}</b>"
                                        .format(fname, self.name))
                return path
        visited_items.append(self)
        for input_item in self._parent.connection_model.input_items(self.name):
            # Find item from project model
            found_item = self._parent.project_item_model.find_item(input_item, Qt.MatchExactly | Qt.MatchRecursive)
            if not found_item:
                self._parent.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item_data = found_item.data(Qt.UserRole)
            if item_data.item_type in ["Data Store", "Data Connection"]:
                path = item_data.find_file(fname, visited_items)
                if path is not None:
                    return path
        return None


# class CustomPackage(Package):
#     """Custom Package class to manage keys more directly."""
#     def __init__(self, descriptor=None, base_path=None, strict=False, storage=None):
#         super().__init__(descriptor, base_path, strict, storage)
#
#     def primary_keys_data(self):
#         """Return primary keys in a 2-column array"""
#         data = list()
#         for resource in self.resources:
#             for field in resource.schema.primary_key:
#                 table = resource.name
#                 data.append([table, field])
#         return data
#
#     def foreign_keys_data(self):
#         """Return foreign keys in a 4-column array"""
#         data = list()
#         for resource in self.resources:
#             for fk in resource.schema.foreign_keys:
#                 child_table = resource.name
#                 child_field = fk['fields'][0]
#                 parent_table = fk['reference']['resource']
#                 parent_field = fk['reference']['fields'][0]
#                 data.append([child_table, child_field, parent_table, parent_field])
#         return data
#
#     def add_primary_key(self, table, field):
#         """Add primary key to the package"""
#         i = self.resource_names.index(table)
#         self.descriptor['resources'][i]['schema']['primaryKey'] = [field]
#         self.commit()
#
#     def add_foreign_key(self, child_table, child_field, parent_table, parent_field):
#         """Add foreign key to the package"""
#         i = self.resource_names.index(child_table)
#         foreign_key = {
#             "fields": [child_field],
#             "reference": {
#                 "resource": parent_table,
#                 "fields": [parent_field]
#             }
#         }
#         self.descriptor['resources'][i]['schema'].setdefault('foreignKeys', [])
#         if foreign_key not in self.descriptor['resources'][i]['schema']['foreignKeys']:
#             self.descriptor['resources'][i]['schema']['foreignKeys'].append(foreign_key)
#             self.commit()
#
#     def rm_primary_key(self, table, field):
#         """Remove primary key from the package"""
#         i = self.resource_names.index(table)
#         if 'primaryKey' in self.descriptor['resources'][i]['schema']:
#             if self.descriptor['resources'][i]['schema']['primaryKey'] == [field]:
#                 del self.descriptor['resources'][i]['schema']['primaryKey']
#                 self.commit()
#
#     def rm_foreign_key(self, child_table, child_field, parent_table, parent_field):
#         """Remove foreign key from the package"""
#         i = self.resource_names.index(child_table)
#         foreign_key = {
#             "fields": [child_field],
#             "reference": {
#                 "resource": parent_table,
#                 "fields": [parent_field]
#             }
#         }
#         if 'foreignKeys' in self.descriptor['resources'][i]['schema']:
#             if foreign_key in self.descriptor['resources'][i]['schema']['foreignKeys']:
#                 self.descriptor['resources'][i]['schema']['foreignKeys'].remove(foreign_key)
#                 self.commit()
