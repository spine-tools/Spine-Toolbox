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

from PySide2.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery
from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView, QAbstractItemView
from PySide2.QtCore import Slot, Qt, SIGNAL, QAbstractProxyModel, QModelIndex, QSortFilterProxyModel
from ui.data_store_form import Ui_Form
from config import STATUSBAR_SS
from models import MinimalTableModel
from widgets.custom_menus import ObjectTreeContextMenu
from helpers import busy_effect
import logging
import os
import sys

class DataStoreForm(QWidget):
    """A widget to show and edit Spine objects in a data store."""

    def __init__(self, parent, file_path):
        """ Initialize class.

        Args:
            parent (ToolBoxUI): QMainWindow instance
            file_path (str): Path to the SQLite file with the database
        """
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self._parent = parent
        # Sql table models
        self.object_class_model = None
        self.object_model = None
        # Proxy models
        self.object_tree_model = QTreeProxyModel(self)
        self.object_parameter_model = None
        self.parameter_as_parent_model = None
        self.parameter_as_child_model = None
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # init ui
        self.ui.treeView_object.setEditTriggers(QAbstractItemView.SelectedClicked|QAbstractItemView.EditKeyPressed)
        self.ui.tableView_object_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_parameter_as_parent.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_parameter_as_child.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # context menus
        self.object_tree_context_menu = None
        self.init_models(file_path)
        self.connect_signals()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        #self.ui.pushButton_commit.clicked.connect(self.commit_clicked)
        self.ui.pushButton_close.clicked.connect(self.close_clicked)
        #self.ui.pushButton_reset.clicked.connect(self.reset_clicked)
        self.ui.treeView_object.currentIndexChanged.connect(self.filter_parameter_models)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.object_class_model.primeInsert.connect(self.object_class_inserted)

    @Slot("int", "QSqlRecord", name="object_class_inserted")
    def object_class_inserted(self, row, record):
        """Populate new object class record with initial values"""
        logging.debug("obj class inserted")
        record.setValue("name", "New object class")
        record.setValue("description", "Type description here...")
        # TODO: Fill in remaining fields

    @busy_effect
    def init_models(self, file_path):
        """Import data from sqlite file into models.
        Args:
            file_path (str): A path to a sqlite file.
        Returns:
            true
        """
        database_name = os.path.basename(file_path)
        self.setWindowTitle("Spine Data Store    -- {} --".format(database_name))
        database = QSqlDatabase.addDatabase("QSQLITE")
        database.setDatabaseName(file_path)
        if not database.open():
            self._parent.msg.emit("Connection to <b>{0}</b> failed.".format(database_name))
            return
        self.object_class_model = QSqlTableModel(self, database)
        self.object_class_model.setTable("object_class")
        self.object_class_model.select()
        self.object_class_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.object_model = QSqlTableModel(self, database)
        self.object_model.setTable("object")
        self.object_model.select()
        self.object_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.object_tree_model = QTreeProxyModel(self)
        self.object_tree_model.set_models(self.object_model, self.object_class_model)
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_object.resizeColumnToContents(0) # TODO: try to improve this
        self.ui.treeView_object.resizeColumnToContents(1) # TODO: try to improve this
        self.ui.treeView_object.expandAll()
        #self.ui.treeView_object.setEditTriggers(QAbstractItemView.SelectedClicked|QAbstractItemView.EditKeyPressed)

        self.object_parameter_model = QSqlTableModel(self, database)
        self.object_parameter_model.setTable("parameter")
        self.object_parameter_model.select()
        self.object_parameter_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.parameter_as_parent_model = QSqlTableModel(self, database)
        self.parameter_as_parent_model.setTable("parameter")
        self.parameter_as_parent_model.select()
        self.parameter_as_parent_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.parameter_as_child_model = QSqlTableModel(self, database)
        self.parameter_as_child_model.setTable("parameter")
        self.parameter_as_child_model.select()
        self.parameter_as_child_model.setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.ui.tableView_object_parameter.setModel(self.object_parameter_model)
        object_name_sec = self.object_parameter_model.record().indexOf("object_name")
        self.ui.tableView_object_parameter.hideColumn(object_name_sec)
        self.ui.tableView_parameter_as_parent.setModel(self.parameter_as_parent_model)
        self.ui.tableView_parameter_as_child.setModel(self.parameter_as_child_model)

    @Slot("QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, index):
        """Populate tableViews whenever an object item is selected on the treeView"""
        # logging.debug("filter_parameter_models")
        if not index.isValid():
            return
        if index.internalId() == sys.maxsize:
            return
        object_name = index.data()
        object_class_name = self.object_class_model.record(index.internalId()).value("name")
        clause = "object_name='{}'".format(object_name)
        self.object_parameter_model.setFilter(clause)
        clause = """object_name in
            (SELECT r.name from relationship as r
            join relationship_class as rc
            on r.class_name=rc.name
            where r.parent_object_name='{}'
            and rc.parent_class_name='{}')
        """.format(object_name, object_class_name)
        self.parameter_as_parent_model.setFilter(clause)
        clause = """object_name in
            (SELECT r.name from relationship as r
            join relationship_class as rc
            on r.class_name=rc.name
            where r.child_object_name='{}'
            and rc.child_class_name='{}')
        """.format(object_name, object_class_name)
        self.parameter_as_child_model.setFilter(clause)

    @Slot("QPoint", name="show_object_tree_context_menu")
    def show_object_tree_context_menu(self, pos):
        """Context menu for object tree.

        Args:
            pos (QPoint): Mouse position
        """
        logging.debug("object tree context menu")
        ind = self.ui.treeView_object.indexAt(pos)
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        self.object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, ind)#
        option = self.object_tree_context_menu.get_action()
        if option.startswith("New"):
            if self.object_tree_model.insertRow(ind.row(), ind.parent()):
                self.ui.treeView_object.edit(ind)
            #self.object_tree_model.setData(ind.child(0,0), option)
            #self.ui.treeView_object.setCurrentIndex(ind.child(0,0))
            #self.ui.treeView_object.edit(ind.child(0,0))
        elif option == "Rename":
            self.ui.treeView_object.edit(ind)
        elif option == "Remove":
            self.object_tree_model.removeRow(ind.row(), ind.parent())
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    @Slot(name="close_clicked")
    def close_clicked(self):
        """Close this form without commiting any changes."""
        self.close()

    def keyPressEvent(self, e):
        """Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()


class QTreeProxyModel(QAbstractProxyModel):
    """A class to view the object table in a tree view"""

    def __init__(self, parent=None):
        """Init class"""
        super().__init__(parent)
        self.header = list()
        self.object_class_model = None
        self.class_display_order = dict()
        self.class_count = dict()
        self.class_offset = dict()
        self.object_name_sec = None
        self.object_class_name_sec = None
        self.object_description_sec = None
        self.class_name_sec = None
        self.class_description_sec = None

    def set_models(self, object_model, object_class_model):
        """Setup models"""
        self.setSourceModel(object_model)
        self.object_class_model = object_class_model
        # Find out sections in each source model
        object_header = self.sourceModel().record()
        class_header = self.object_class_model.record()
        self.object_name_sec = object_header.indexOf("name")
        self.object_class_name_sec = object_header.indexOf("class_name")
        self.object_description_sec = object_header.indexOf("description")
        self.class_name_sec = class_header.indexOf("name")
        self.class_description_sec = class_header.indexOf("description")
        # insert dummy column to object table to map class description from/to it
        # this enables editing of class description in treeView
        self.sourceModel().insertColumn(self.sourceModel().columnCount())
        self.object_class_desc_sec = self.sourceModel().columnCount()-1
        # TODO: remove this column before commit
        # self.sourceModel().removeColumn(self.sourceModel().columnCount()-1)

        # Sort both models by class_name to compute correct offsets
        self.sourceModel().sort(object_header.indexOf("class_name"), Qt.AscendingOrder)
        self.object_class_model.sort(self.class_name_sec, Qt.AscendingOrder)
        offset = 0
        for i in range(self.object_class_model.rowCount()):
            class_name = self.object_class_model.record(i).value("name")
            self.class_offset[class_name] = offset
            count = 0
            for j in range(self.sourceModel().rowCount()):
                if self.sourceModel().record(j).value("class_name") == class_name:
                    count += 1
            self.class_count[class_name] = count
            offset += count
        # Sort class model by display order
        self.object_class_model.sort(class_header.indexOf("display_order"), Qt.AscendingOrder)
        # Compute class display order
        for i in range(self.object_class_model.rowCount()):
            class_name = self.object_class_model.record(i).value("name")
            self.class_display_order[class_name] = i
        self.setHeaderData(0, Qt.Horizontal, "name")
        self.setHeaderData(1, Qt.Horizontal, "description")

    def insertRows(self, row, count, parent=QModelIndex()):
        """Inserts count rows into the model before the given row.
        Items in the new row will be children of the item represented
        by the parent model index."""
        if not parent.isValid(): # New class
            self.object_class_model.insertRows(row, count, QModelIndex())
            return True
        if parent.internalId() == sys.maxsize:
            self.sourceModel().insertRows(0, count, QModelIndex())
            return True
        return False

    def flags(self, index):
        """Returns flags for table items."""
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def columnCount(self, parent):
        """Returns the number of columns under the given parent"""
        #logging.debug("colcount")
        return 2

    def rowCount(self, parent):
        """Returns the number of rows under the given parent"""
        #logging.debug("rowcount")
        if not parent.isValid(): # root
            return self.object_class_model.rowCount()
        if parent.internalId() == sys.maxsize: # class
            class_name = self.object_class_model.record(parent.row()).value("name")
            return self.class_count[class_name]
        return 0

    def index(self, row, column, parent=QModelIndex()):
        """Returns the index of the item in the model specified by the given row,
        column and parent index.
        """
        #logging.debug("index")
        if not parent.isValid():
            return self.createIndex(row, column, sys.maxsize)
        return self.createIndex(row, column, parent.row())

    def mapToSource(self, proxy_index):
        """Return the model index in the source model that corresponds to the
        proxy_index in the proxy model"""
        #logging.debug("mapto")
        if not proxy_index.isValid():
            return QModelIndex()
        if proxy_index.internalId() == sys.maxsize: # class
            class_name = self.object_class_model.record(proxy_index.row()).value("name")
            row = self.class_offset[class_name] + 1
            column = self.object_class_name_sec if proxy_index.column() == 0 else self.object_class_desc_sec
            return self.sourceModel().index(row, column)
        class_name = self.object_class_model.record(proxy_index.internalId()).value("name")
        row = self.class_offset[class_name] + proxy_index.row()
        column = self.object_name_sec if proxy_index.column() == 0 else self.object_description_sec
        return self.sourceModel().index(row, column)

    def data(self, index, role=Qt.DisplayRole):
        """Read class description from object_class_model"""
        #logging.debug("data")
        if not index.isValid():
            return None
        if index.internalId() == sys.maxsize and index.column() == 1:
            column = self.class_description_sec
            object_class_index = self.object_class_model.createIndex(index.row(), column)
            return self.object_class_model.data(object_class_index, role)
        return super().data(index, role)

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Get headers."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                h = self.header[section]
            except IndexError:
                return None
            return h
        else:
            return None

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        """Set headers"""
        # logging.debug("set header data")
        if orientation == Qt.Horizontal and role == Qt.EditRole:
            self.header.insert(section, value)
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return False

    def parent(self, index):
        """Returns the parent of the model item with the given index. """
        #logging.debug("parent")
        if not index.isValid():
            return QModelIndex()
        if index.internalId() == sys.maxsize:
            return QModelIndex()
        parent_row = index.internalId()
        return self.createIndex(parent_row, 0, sys.maxsize)

    def mapFromSource(self, source_index):
        """Return the model index in the proxy model that corresponds to the
        source_index from the source model"""
        #logging.debug("mapfrom")
        class_name = self.sourceModel().record(source_index.row()).value("class_name")
        if source_index.column() == self.object_class_name_sec:
            row = self.class_display_order[class_name]
            column = 0
            internal_id = sys.maxsize
        elif source_index.column() == self.object_class_desc_sec:
            row = self.class_display_order[class_name]
            column = 1
            internal_id = sys.maxsize   # TODO: what is this?
        elif source_index.column() == self.object_name_sec:
            row = source_index.row() - self.class_offset[class_name]
            column = 0
            internal_id = self.class_display_order[class_name]
        elif source_index.column() == self.object_description_sec:
            row = source_index.row() - self.class_offset[class_name]
            column = 1
            internal_id = self.class_display_order[class_name]
        else:
            return QModelIndex()
        return self.createIndex(row, column, internal_id)

    def hasChildren(self, parent):
        """Return whether or not parent has children in the model"""
        #logging.debug("haschildren")
        return True
        if not parent.isValid():
            return True
        if parent.internalId() == sys.maxsize:
            return True
        return False

    def setSourceModel(self, model):
        """Sets the given sourceModel to be processed by the proxy model."""
        #logging.debug("set source")
        self.beginResetModel()
        super().setSourceModel(model)
        self.endResetModel()
