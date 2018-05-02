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

from PySide2.QtSql import QSqlTableModel, QSqlDatabase, QSqlQueryModel
from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView, QAbstractItemView
from PySide2.QtCore import Slot, Qt, QAbstractProxyModel, QModelIndex
from ui.data_store_form import Ui_Form
from config import STATUSBAR_SS
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
        # Sql query model
        self.object_class_join_model = None
        self.class_object_count_model = None
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
        #self.object_class_model.primeInsert.connect(self.object_class_inserted)

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

        self.object_class_join_model = QSqlQueryModel()
        self.object_class_join_model.setQuery("""
            SELECT oc.name as class_name,
                oc.description as class_description,
                oc.display_order as class_display_order,
                o.name as object_name,
                o.description as object_description
            from object_class as oc
            LEFT JOIN object as o
            ON oc.name=o.class_name
            ORDER BY class_display_order
        """)

        self.class_object_count_model = QSqlQueryModel()
        self.class_object_count_model.setQuery("""
            SELECT oc.name as class_name,
                o.count as object_count,
                oc.display_order as class_display_order
            FROM object_class as oc
            LEFT JOIN (
                SELECT class_name, count(*) as count
                FROM object GROUP BY class_name
            ) as o
            ON oc.name=o.class_name
            ORDER BY class_display_order
        """)

        self.object_tree_model = QTreeProxyModel(self)
        self.object_tree_model.set_models(self.object_class_join_model,\
                                            self.class_object_count_model)
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_object.expandAll()
        self.ui.treeView_object.resizeColumnToContents(0)
        self.ui.treeView_object.resizeColumnToContents(1)

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
        class_name = self.class_object_count_model.record(index.internalId()).value("class_name")
        clause = "object_name='{}'".format(object_name)
        self.object_parameter_model.setFilter(clause)
        clause = """object_name in
            (SELECT r.name from relationship as r
            join relationship_class as rc
            on r.class_name=rc.name
            where r.parent_object_name='{}'
            and rc.parent_class_name='{}')
        """.format(object_name, class_name)
        self.parameter_as_parent_model.setFilter(clause)
        clause = """object_name in
            (SELECT r.name from relationship as r
            join relationship_class as rc
            on r.class_name=rc.name
            where r.child_object_name='{}'
            and rc.child_class_name='{}')
        """.format(object_name, class_name)
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
        self.class_object_count_model = None
        self.class_display_order = dict()
        self.class_object_count = dict()
        self.class_offset = dict()
        self.class_name_sec = None
        self.class_description_sec = None
        self.object_name_sec = None
        self.object_description_sec = None

    def setSourceModel(self, model):
        """Sets the given sourceModel to be processed by the proxy model."""
        #logging.debug("set source")
        self.beginResetModel()
        super().setSourceModel(model)
        self.endResetModel()

    def set_models(self, object_class_join_model, class_object_count_model):
        """Setup models"""
        self.setSourceModel(object_class_join_model)
        self.class_object_count_model = class_object_count_model
        # Find out sections in each source model
        header = self.sourceModel().record()
        self.class_name_sec = header.indexOf("class_name")
        self.class_description_sec = header.indexOf("class_description")
        self.object_name_sec = header.indexOf("object_name")
        self.object_description_sec = header.indexOf("object_description")

        offset = 0
        for i in range(self.class_object_count_model.rowCount()):
            class_name = self.class_object_count_model.record(i).value("class_name")
            self.class_offset[class_name] = offset
            object_count = self.class_object_count_model.record(i).value("object_count")
            if not object_count:
                object_count = 0
            self.class_object_count[class_name] = object_count
            if object_count == 0:
                object_count = 1
            offset += object_count
            self.class_display_order[class_name] = i

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
            return self.class_object_count_model.rowCount()
        if parent.internalId() == sys.maxsize: # class
            class_name = self.class_object_count_model.record(parent.row()).value("class_name")
            return self.class_object_count[class_name]
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
        # logging.debug("mapto")
        if not proxy_index.isValid():
            return QModelIndex()
        if proxy_index.internalId() == sys.maxsize: # class
            class_name = self.class_object_count_model.record(proxy_index.row()).value("class_name")
            row = self.class_offset[class_name]
            column = self.class_name_sec if proxy_index.column() == 0 else\
                    self.class_description_sec
            return self.sourceModel().index(row, column)
        class_name = self.class_object_count_model.record(proxy_index.internalId()).value("class_name")
        row = self.class_offset[class_name] + proxy_index.row()
        column = self.object_name_sec if proxy_index.column() == 0 else self.object_description_sec
        return self.sourceModel().index(row, column)

    #def setData(self, index, value, role=Qt.EditRole):
    #    """Sets the role data for the item at index to value."""
    #    logging.debug("set data")
    #    if role != Qt.EditRole:
    #        return False
    #    if index.internalId() == sys.maxsize:
    #        logging.debug("hello")
    #        self.dataChanged.emit(index, index, Qt.EditRole)
    #        return True
    #    return super().setData(index, value, role)

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
        source_column = source_index.column()
        if source_column in [self.object_name_sec, self.object_description_sec]:
            row = source_index.row() - self.class_offset[class_name]
            column = 0 if source_column == self.object_name_sec else 1
            parent_row = self.class_display_order[class_name]
            return self.createIndex(row, column, parent_row)
        elif source_column in [self.class_name_sec, self.class_description_sec]:
            row = self.class_display_order[class_name]
            column = 0 if source_column == self.class_name_sec else 1
            return self.createIndex(row, column, sys.maxsize)
        return QModelIndex()

    def hasChildren(self, parent):
        """Return whether or not parent has children in the model"""
        #logging.debug("haschildren")
        return True
        if not parent.isValid():
            return True
        if parent.internalId() == sys.maxsize:
            return True
        return False
