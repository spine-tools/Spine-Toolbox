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

from PySide2.QtSql import QSqlRelationalTableModel, QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlRelation
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
        # Sql query model
        self.join_model = None
        # Proxy models
        self.object_tree_model = QTreeProxyModel(self)
        # Sql table models
        self.object_parameter_model = None
        self.relationship_parameter_model = None
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # init ui
        self.ui.treeView_object.setEditTriggers(QAbstractItemView.SelectedClicked|QAbstractItemView.EditKeyPressed)
        self.ui.tableView_object_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_relationship_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
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
        # object class join model
        self.join_model = QSqlQueryModel()
        self.join_model.setQuery("""
            SELECT oc.id as object_class_id,
                oc.name as object_class_name,
                oc.description as object_class_description,
                oc.display_order as object_class_display_order,
                o.id as object_id,
                o.name as object_name,
                o.description as object_description,
				rc.id as relationship_class_id,
				rc.name as relationship_class_name,
				r.related_object_id as related_object_id,
				r.related_object_name as related_object_name
            FROM object_class as oc
            LEFT JOIN object as o
            ON oc.id=o.class_id
			LEFT JOIN (
                SELECT parent_class_id as object_class_id,
                    id,
                    name
                FROM relationship_class as rc
				UNION ALL
                    SELECT child_class_id as object_class_id,
                    id,
                    name
                    FROM relationship_class as rc
			) as rc
            ON oc.id=rc.object_class_id
			LEFT JOIN (
                SELECT r.parent_object_id as object_id,
					r.class_id,
                    o.id as related_object_id,
                    o.name as related_object_name
                FROM relationship as r
				JOIN object as o
				ON r.child_object_id=o.id
				UNION ALL
					SELECT r.child_object_id as object_id,
						r.class_id,
						o.id as related_object_id,
						o.name as related_object_name
					FROM relationship as r
					JOIN object as o
					ON r.parent_object_id=o.id
			) as r
			ON r.class_id=rc.id
            AND o.id=r.object_id
            ORDER BY object_class_display_order, object_id, relationship_class_id, related_object_id
        """)
        # TODO: Check if query is ok
        # object tree model and view
        self.object_tree_model = QTreeProxyModel(self)
        self.object_tree_model.setSourceModel(self.join_model)
        self.ui.treeView_object.setModel(self.object_tree_model)
        #self.ui.treeView_object.expandAll()
        self.ui.treeView_object.resizeColumnToContents(0)
        #self.ui.treeView_object.colapseAll()
        # object and relationship parameter
        self.object_parameter_model = QSqlRelationalTableModel(self, database)
        self.object_parameter_model.setTable("parameter_value")
        self.object_parameter_model.setRelation(0, QSqlRelation("parameter", "id", "name"));
        self.object_parameter_model.select()
        self.object_parameter_model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
        self.relationship_parameter_model = QSqlRelationalTableModel(self, database)
        self.relationship_parameter_model.setTable("parameter_value")
        self.relationship_parameter_model.select()
        self.relationship_parameter_model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
        # object and relationship parameter view
        self.ui.tableView_object_parameter.setModel(self.object_parameter_model)
        object_id_sec = self.object_parameter_model.record().indexOf("object_id")
        self.ui.tableView_object_parameter.hideColumn(object_id_sec)
        self.ui.tableView_relationship_parameter.setModel(self.relationship_parameter_model)

    @Slot("QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, index):
        """Populate tableViews whenever an object item is selected in the treeView"""
        logging.debug("filter_parameter_models")
        if not index.isValid():
            # invisible root
            return
        if index.internalId() < self.object_tree_model.base:
            # object class
            return
        if index.internalId() < self.object_tree_model.base**2:
            # object
            object_row = self.object_tree_model.mapToSource(index).row()
            object_id = self.join_model.record(object_row).value("object_id")
            object_class_id = self.join_model.record(object_row).value("object_class_id")
            clause = "object_id={}".format(object_id)
            self.object_parameter_model.setFilter(clause)
            return
            #clause = """object_id in
            #    (SELECT r.id from relationship as r
            #    join relationship_class as rc
            #    on r.class_id=rc.id
            #    where r.parent_object_id='{}'
            #    and rc.parent_class_id='{}')
            #""".format(object_id, class_id)
            #self.parameter_as_parent_model.setFilter(clause)
            #clause = """object_id in
            #    (SELECT r.id from relationship as r
            #    join relationship_class as rc
            #    on r.class_id=rc.id
            #    where r.child_object_id='{}'
            #    and rc.child_class_id='{}')
            #""".format(object_id, class_id)
            #self.parameter_as_child_model.setFilter(clause)

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
            if self.join_model.insertRow(ind.row(), ind.parent()):
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

# TODO: try to put these inside the model
class ObjectClass:
    def __init__(self):
        self.object = list()
        self.offset = None

class Object:
    def __init__(self):
        self.relationship_class = list()
        self.offset = None

class RelationshipClass:
    def __init__(self):
        self.count = 0
        self.offset = None

class QTreeProxyModel(QAbstractProxyModel):
    """A class to view the object table in a tree view"""

    def __init__(self, parent=None):
        """Init class"""
        super().__init__(parent)
        self.object_class = list()
        self.object_class_name_sec = None
        self.object_name_sec = None
        self.relationship_class_name_sec = None
        self.related_object_name_sec = None
        self.base = None

    def setSourceModel(self, model):
        """Sets the given sourceModel to be processed by the proxy model."""
        #logging.debug("set source")
        self.beginResetModel()
        super().setSourceModel(model)
        # Find out sections in each source model
        header = self.sourceModel().record()
        self.object_class_name_sec = header.indexOf("object_class_name")
        self.object_name_sec = header.indexOf("object_name")
        self.relationship_class_name_sec = header.indexOf("relationship_class_name")
        self.related_object_name_sec = header.indexOf("related_object_name")
        self.reset_model()
        self.endResetModel()

    def reset_model(self):
        """
            Sweep the source query and find out offset of each element
        """
        new_object_class = None
        new_object = None
        new_relationship_class = None
        last_object_class_id = -1
        last_object_id = -1
        last_relationship_class_id = -1
        for i in range(self.sourceModel().rowCount()):
            rec = self.sourceModel().record(i)
            object_class_id = rec.value("object_class_id")
            object_id = rec.value("object_id")
            relationship_class_id = rec.value("relationship_class_id")
            related_object_id = rec.value("related_object_id")
            if object_class_id != last_object_class_id:
                last_object_class_id = object_class_id
                last_object_id = object_id
                last_relationship_class_id = relationship_class_id
                if new_object_class:
                    if new_object:
                        if new_relationship_class:
                            new_object.relationship_class.append(new_relationship_class)
                            new_relationship_class = None
                        new_object_class.object.append(new_object)
                        new_object = None
                    self.object_class.append(new_object_class)
                new_object_class = ObjectClass()
                new_object_class.offset = i
                if object_id:
                    new_object = Object()
                    new_object.offset = i
                    if relationship_class_id:
                        new_relationship_class = RelationshipClass()
                        new_relationship_class.offset = i
                        if related_object_id:
                            new_relationship_class.count += 1
            elif object_id != last_object_id:
                last_object_id = object_id
                last_relationship_class_id = relationship_class_id
                if new_object:
                    if new_relationship_class:
                        new_object.relationship_class.append(new_relationship_class)
                        new_relationship_class = None
                    new_object_class.object.append(new_object)
                    new_object = None
                if object_id:
                    new_object = Object()
                    new_object.offset = i
                    if relationship_class_id:
                        new_relationship_class = RelationshipClass()
                        new_relationship_class.offset = i
                        if related_object_id:
                            new_relationship_class.count += 1
            elif relationship_class_id != last_relationship_class_id:
                last_relationship_class_id = relationship_class_id
                if new_relationship_class:
                    new_object.relationship_class.append(new_relationship_class)
                    new_relationship_class = None
                if relationship_class_id:
                    new_relationship_class = RelationshipClass()
                    new_relationship_class.offset = i
                    if related_object_id:
                        new_relationship_class.count += 1
            elif related_object_id:
                new_relationship_class.count += 1
        # last row
        if new_object_class:
            if new_object:
                if new_relationship_class:
                    new_object.relationship_class.append(new_relationship_class)
                    new_relationship_class = None
                new_object_class.object.append(new_object)
                new_object = None
            self.object_class.append(new_object_class)

        # compute base for handling internal indices
        self.base = len(self.object_class)
        for object_class in self.object_class:
            if len(object_class.object) > self.base:
                self.base = len(object_class.object)
            for object_ in object_class.object:
                if len(object_.relationship_class) > self.base:
                    self.base = len(object_.relationship_class)
                for relationship_class in object_.relationship_class:
                    if relationship_class.count > self.base:
                        self.base = relationship_class.count
        self.base += 1

    def flags(self, index):
        """Returns flags for table items."""
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def columnCount(self, parent):
        """Returns the number of columns under the given parent"""
        #logging.debug("colcount")
        return 1

    def rowCount(self, parent):
        """Returns the number of rows under the given parent"""
        #logging.debug("rowcount")
        if not parent.isValid():
            # root
            return len(self.object_class)
        if parent.internalId() < self.base:
            # object class
            object_class = self.object_class[parent.row()]
            return len(object_class.object)
        if parent.internalId() < self.base**2:
            # object
            object_class = self.object_class[parent.parent().row()]
            object_ = object_class.object[parent.row()]
            return len(object_.relationship_class)
        if parent.internalId() < self.base**3:
            # relationship class
            object_class = self.object_class[parent.parent().parent().row()]
            object_ = object_class.object[parent.parent().row()]
            relationship_class = object_.relationship_class[parent.row()]
            return relationship_class.count
        return 0

    def index(self, row, column, parent=QModelIndex()):
        """Returns the index of the item in the model specified by the given row,
        column and parent index.
        """
        #logging.debug("index")
        if row < 0 or column < 0:
            return QModelIndex()
        if not parent.isValid():
            # object class
            return self.createIndex(row, column, row + 1)
        if parent.internalId() < self.base:
            # object
            return self.createIndex(row, column, parent.internalId() + (row + 1) * self.base)
        if parent.internalId() < self.base**2:
            # relationship class
            return self.createIndex(row, column, parent.internalId() + (row + 1) * (self.base**2))
        # related object
        return self.createIndex(row, column, parent.internalId() + (row + 1) * (self.base**3))

    def parent(self, index):
        """Returns the parent of the model item with the given index. """
        #logging.debug("parent")
        if not index.isValid():
            # invisible root
            return QModelIndex()
        if index.internalId() < self.base:
            # object class
            return QModelIndex()
        if index.internalId() < self.base**2:
            # object
            parent_index = index.internalId() % self.base
            parent_row = parent_index - 1
            return self.createIndex(parent_row, 0, parent_index)
        if index.internalId() < self.base**3:
            # relationship class
            parent_index = index.internalId() % self.base**2
            parent_row = int(parent_index / self.base) - 1
            return self.createIndex(parent_row, 0, parent_index)
        # related object
        parent_index = index.internalId() % self.base**3
        parent_row = int(parent_index / self.base**2) - 1
        return self.createIndex(parent_row, 0, parent_index)

    def mapToSource(self, proxy_index):
        """Return the model index in the source model that corresponds to the
        proxy_index in the proxy model"""
        #logging.debug("mapto")
        if not proxy_index.isValid():
            return QModelIndex()
        if proxy_index.internalId() < self.base:
            # object class
            object_class = self.object_class[proxy_index.row()]
            return self.sourceModel().index(object_class.offset, self.object_class_name_sec)
        if proxy_index.internalId() < self.base**2:
            # object
            object_class = self.object_class[proxy_index.parent().row()]
            object_ = object_class.object[proxy_index.row()]
            return self.sourceModel().index(object_.offset, self.object_name_sec)
        if proxy_index.internalId() < self.base**3:
            # relationship class
            object_class = self.object_class[proxy_index.parent().parent().row()]
            object_ = object_class.object[proxy_index.parent().row()]
            relationship_class = object_.relationship_class[proxy_index.row()]
            return self.sourceModel().index(relationship_class.offset, self.relationship_class_name_sec)
        # related object
        object_class = self.object_class[proxy_index.parent().parent().parent().row()]
        object_ = object_class.object[proxy_index.parent().parent().row()]
        relationship_class = object_.relationship_class[proxy_index.parent().row()]
        related_object_row = proxy_index.row()
        return self.sourceModel().index(relationship_class.offset + related_object_row, self.related_object_name_sec)

    def mapFromSource(self, source_index):
        """Return the model index in the proxy model that corresponds to the
        source_index from the source model"""
        #logging.debug("mapfrom")
        #class_id = self.sourceModel().record(source_index.row()).value("class_id")
        #source_column = source_index.column()
        #if source_column in [self.object_name_sec, self.object_description_sec]:
        #    row = source_index.row() - self.class_offset[class_id]
        #    column = 0 if source_column == self.object_name_sec else 1
        #    parent_row = self.class_display_order[class_id]
        #    return self.createIndex(row, column, parent_row)
        #elif source_column in [self.class_name_sec, self.class_description_sec]:
        #    row = self.class_display_order[class_id]
        #    column = 0 if source_column == self.class_name_sec else 1
        #    return self.createIndex(row, column, 0)
        return QModelIndex()

    def hasChildren(self, parent):
        """Return whether or not parent has children in the model"""
        #logging.debug("haschildren")
        if parent.internalId() >= self.base**3:
            # related object
            return False
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """Inserts count rows into the model before the given row.
        Items in the new row will be children of the item represented
        by the parent model index.
        """
        logging.debug("insert rows")
        if index.internalId() == 0: # object_class table
            pass

    def setData(self, index, value, role=Qt.EditRole):
        """Sets the role data for the item at index to value."""
        logging.debug("set data")
        if role != Qt.EditRole:
            return False
        q = QSqlQuery()
        name = index.sibling(index.row(), 0).data()
        if index.internalId() == sys.maxsize: # object_class table
            if index.column() == 0: # name
                # object_class table
                q.prepare("""
                    UPDATE object_class
                    SET name=? WHERE name=?
                """)
                q.addBindValue(value)
                q.addBindValue(name)
                q.exec_()
                # object table
                q.prepare("""
                    UPDATE object
                    SET class_name=? WHERE class_name=?
                """)
                q.addBindValue(value)
                q.addBindValue(name)
                q.exec_()
            if index.column() == 1: # description
                # object_class table
                q.prepare("""
                    UPDATE object_class
                    SET description=? WHERE name=?
                """)
                q.addBindValue(value)
                q.addBindValue(name)
                q.exec_()
        else: # object table
            if index.column() == 0: # name
                q.prepare("""
                    UPDATE object
                    SET name=? WHERE name=?
                """)
                q.addBindValue(value)
                q.addBindValue(name)
                q.exec_()
            if index.column() == 1: # description
                q.prepare("""
                    UPDATE object
                    SET description=? WHERE name=?
                """)
                q.addBindValue(value)
                q.addBindValue(name)
                q.exec_()
        # commit
        self.sourceModel().query().exec_()
        self.class_object_count_model.query().exec_()
        self.reset_models()
        self.dataChanged.emit(index, index, Qt.EditRole)
        # TODO: keep going with remaining tables
        # TODO: save all executed sql statements
        return True
