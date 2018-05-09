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
from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView, QAbstractItemView,\
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QInputDialog
from PySide2.QtCore import Slot, Qt, QAbstractProxyModel, QModelIndex
from ui.data_store_form import Ui_Form
from config import STATUSBAR_SS
from widgets.custom_menus import ObjectTreeContextMenu
from helpers import busy_effect
from models import QTreeProxyModel
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
            ORDER BY object_class_display_order, object_class_id, object_id, relationship_class_id, related_object_id
        """)
        # TODO: Check if query is ok
        # object tree model and view
        self.object_tree_model.setSourceModel(self.join_model)
        self.ui.treeView_object.setModel(self.object_tree_model)
        #self.ui.treeView_object.expandAll()
        self.ui.treeView_object.resizeColumnToContents(0)
        #self.ui.treeView_object.colapseAll()
        # object and relationship parameter
        self.object_parameter_model = QSqlRelationalTableModel(self, database)
        self.object_parameter_model.setTable("parameter_value")
        self.object_parameter_model.setRelation(0, QSqlRelation("parameter", "id", "name"));
        self.object_parameter_model.setRelation(1, QSqlRelation("object", "id", "name"));
        self.object_parameter_model.select()
        self.object_parameter_model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
        self.object_parameter_model.setHeaderData(0, Qt.Horizontal, "parameter name")
        self.object_parameter_model.setHeaderData(1, Qt.Horizontal, "object name")
        self.relationship_parameter_model = QSqlRelationalTableModel(self, database)
        self.relationship_parameter_model.setTable("parameter_value")
        self.relationship_parameter_model.select()
        self.relationship_parameter_model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
        # object and relationship parameter view
        self.ui.tableView_object_parameter.setModel(self.object_parameter_model)
        #object_id_sec = self.object_parameter_model.record().indexOf("object_id")
        #self.ui.tableView_object_parameter.hideColumn(object_id_sec)
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
            object_class_row = self.object_tree_model.mapToSource(index).row()
            object_class_id = self.join_model.record(object_class_row).value("object_class_id")
            clause = "object_id IN (SELECT id FROM object WHERE class_id={})".format(object_class_id)
            self.object_parameter_model.setFilter(clause)
            return
        if index.internalId() < self.object_tree_model.base_2:
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
        if ind.internalId() < ind.model().base:
            table = 'object_class'
        elif ind.internalId() < ind.model().base_2:
            table = 'object'
        else:
            table = 'relationship_class'
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        self.object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, ind)#
        option = self.object_tree_context_menu.get_action()
        if option.startswith("New"):
            dialog = CustomQDialog(self, option,
                name="Type name here...",
                description="Type description here...")
            answer = dialog.exec_()
            if answer == QDialog.Accepted:
                name = dialog.answer["name"]
                description = dialog.answer["description"]
                source_row = ind.model().mapToSource(ind).row()
                source_record = ind.model().sourceModel().record(source_row)
                if table == 'object_class':
                    display_order = source_record.value("object_class_display_order")
                    self.add_item(table, name=name, description=description, display_order=display_order)
                elif table == 'object':
                    class_id = source_record.value("object_class_id")
                    self.add_item(table, class_id=class_id, name=name, description=description)
        elif option == "Rename":
            name = ind.data()
            answer = QInputDialog.getText(self, "Rename item", "Enter new name:",\
                QLineEdit.Normal, name)
            new_name = answer[0]
            if not new_name: # cancel clicked
                return
            if new_name == name:
                return
            self.rename_item(table, name, new_name)
        elif option == "Remove":
            self.object_tree_model.removeRow(ind.row(), ind.parent())
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    def add_item(self, table, **kwargs): #name, description, display_order):
        """Add new item given by kwargs to table"""
        q = QSqlQuery()
        columns = list()
        values = list()
        for key in kwargs:
            columns.append("`{}`".format(key))
            values.append("?")
        columns = ', '.join(columns)
        values = ', '.join(values)
        sql = "INSERT INTO `{}` ({}) VALUES ({})".format(table, columns, values)
        q.prepare(sql)
        for key,value in kwargs.items():
            q.addBindValue(value)
        q.exec_()
        del q
        self.join_model.query().exec_()
        self.object_tree_model.reset_model()

    def rename_item(self, table, name, new_name):
        """Rename item in table from name to new_name"""
        q = QSqlQuery()
        sql = "UPDATE `{}` SET name=? WHERE name=?".format(table)
        q.prepare(sql)
        q.addBindValue(new_name)
        q.addBindValue(name)
        q.exec_()
        del q
        self.join_model.query().exec_()


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


class CustomQDialog(QDialog):
    """A class to create custom forms with several line edits,
    used when creating new object classes, objects, and so on"""
    def __init__(self, parent=None, title="", **kwargs):
        """Initialize class

        Args:
            parent (QWidget): the parent of this dialog, needed to center it properly
            title (str): window title
            kwargs (dict): keys to use when collecting the answer in output dict, values are placeholder texts
        """
        super().__init__(parent)
        self.line_edit = dict()
        self.answer = dict()
        self.setWindowTitle(title)
        form = QFormLayout(self)
        for key,value in kwargs.items():
            line_edit = QLineEdit(self)
            line_edit.setPlaceholderText(value)
            self.line_edit[key] = line_edit
            form.addRow(line_edit)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        form.addRow(button_box)

    @Slot(name="save_and_accept")
    def save_and_accept(self):
        """Collect answer in output dict and accept"""
        for key,value in self.line_edit.items():
            self.answer[key] = value.text()
        self.accept()
