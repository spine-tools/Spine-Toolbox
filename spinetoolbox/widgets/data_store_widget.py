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

from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView, QAbstractItemView,\
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QInputDialog, QComboBox
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QStandardItem, QStandardItemModel
from ui.data_store_form import Ui_Form
from config import STATUSBAR_SS
from widgets.custom_menus import ObjectTreeContextMenu
from helpers import busy_effect
from models import MinimalTableModel, CustomSortFilterProxyModel
import logging
from sqlalchemy import inspect, create_engine, text

class DataStoreForm(QWidget):
    """A widget to show and edit Spine objects in a data store."""

    def __init__(self, parent, reference):
        """ Initialize class.

        Args:
            parent (ToolBoxUI): QMainWindow instance
            reference (tuple): Database name and url to create sqlalchemy engine
        """
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self._parent = parent
        # Object tree model
        self.object_tree_model = QStandardItemModel(self)
        # Parameter models
        self.object_parameter_model = MinimalTableModel(self)
        self.object_parameter_proxy_model = CustomSortFilterProxyModel(self)
        self.relationship_parameter_model = MinimalTableModel(self)
        self.relationship_parameter_proxy_model = CustomSortFilterProxyModel(self)
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
        self.init_models(reference)
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

    def init_models(self, reference):
        """Import data from sqlite file into models.
        Args:
            db_url (tuple): Database name and url to create sqlalchemy engine.
        Returns:
            true
        """
        db_name = reference[0]
        db_url = reference[1]
        self.setWindowTitle("Spine Data Store    -- {} --".format(db_name))
        # Create source engine to obtain data for our models
        source_engine = create_engine(db_url)
        # Populate object tree model
        root_item = QStandardItem(db_name)
        object_class_result = source_engine.execute("""
            SELECT id, name FROM object_class ORDER BY display_order
        """)
        for object_class_row in object_class_result:
            relationship_class_result = source_engine.execute(
                text("""
                    SELECT parent_class_id as object_class_id,
                        id,
                        name
                    FROM relationship_class as rc
                    WHERE parent_type='object_class'
                    AND parent_class_id=:object_class_id
                    UNION ALL
                        SELECT child_class_id as object_class_id,
                        id,
                        name
                        FROM relationship_class as rc
                        WHERE parent_type='object_class'
                        AND child_class_id=:object_class_id
                """),
                object_class_id=object_class_row['id']
            )
            relationship_class_list = [row for row in relationship_class_result]
            object_class_item = QStandardItem(object_class_row['name'])
            object_class_item.setData(object_class_row['id'], Qt.UserRole)
            object_result = source_engine.execute(
                text("""
                    SELECT id, name FROM object WHERE class_id=:object_class_id
                """),
                object_class_id=object_class_row['id']
            )
            for object_row in object_result:
                object_item = QStandardItem(object_row['name'])
                object_item.setData(object_row['id'], Qt.UserRole)
                for relationship_class_row in relationship_class_list:
                    relationship_class_item = QStandardItem(relationship_class_row['name'])
                    related_object_result = source_engine.execute(
                        text("""
                            SELECT o.id as id,
                                o.name as name
                            FROM relationship as r
                            JOIN object as o
                            ON r.child_object_id=o.id
                            WHERE r.class_id=:relationship_class_id
                            AND r.parent_object_id=:object_id
                            UNION ALL
                                SELECT o.id as id,
                                    o.name as name
                                FROM relationship as r
                                JOIN object as o
                                ON r.parent_object_id=o.id
                                WHERE r.class_id=:relationship_class_id
                                AND r.child_object_id=:object_id
                        """),
                        relationship_class_id=relationship_class_row['id'],
                        object_id=object_row['id']
                    )
                    for related_object_row in related_object_result:
                        related_object_item = QStandardItem(related_object_row['name'])
                        relationship_class_item.appendRow(related_object_item)
                    object_item.appendRow(relationship_class_item)
                object_class_item.appendRow(object_item)
            root_item.appendRow(object_class_item)
        self.object_tree_model.appendRow(root_item)
        # setup object tree view
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_object.header().hide()
        self.ui.treeView_object.expand(root_item.index())
        self.ui.treeView_object.resizeColumnToContents(0)

        parameter_data = list()
        results = source_engine.execute("""
            SELECT o.name as object_name,
                p.name as parameter_name,
                p.object_class_id,
                pv.*
            FROM parameter_value as pv
            JOIN parameter as p
            ON p.id=pv.parameter_id
            JOIN object as o
            ON pv.object_id=o.id
            WHERE p.object_type='object_class'
        """)
        column_names = results.keys()
        for parameter_row in results:
            parameter_data.append(parameter_row)
        self.object_parameter_model.header = column_names
        self.object_parameter_model.reset_model(parameter_data)
        self.object_parameter_proxy_model.setSourceModel(self.object_parameter_model)
        self.ui.tableView_object_parameter.setModel(self.object_parameter_proxy_model)
        self.ui.tableView_object_parameter.hideColumn(column_names.index("object_class_id"))
        self.ui.tableView_object_parameter.hideColumn(column_names.index("object_id"))
        self.ui.tableView_object_parameter.hideColumn(column_names.index("parameter_id"))
        self.relationship_parameter_model.header = column_names
        self.relationship_parameter_model.reset_model(parameter_data)
        self.ui.tableView_relationship_parameter.setModel(self.relationship_parameter_proxy_model)


    @Slot("QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, index):
        """Populate tableViews whenever an object item is selected in the treeView"""
        # logging.debug("filter_parameter_models")
        tree_level = 0
        index_copy = index
        while index_copy.parent().isValid():
            index_copy = index_copy.parent()
            tree_level += 1
        if tree_level == 0: # root
            return
        elif tree_level == 1: # object class
            object_class_item = index.model().itemFromIndex(index)
            object_class_id = object_class_item.data(Qt.UserRole)
            self.object_parameter_proxy_model.filter_object_class_id = object_class_id
            self.object_parameter_proxy_model.filter_object_id = None
            self.object_parameter_proxy_model.setFilterRegExp("")   # trick to trigger sorting
        elif tree_level == 2: # object class
            object_class_item = index.model().itemFromIndex(index.parent())
            object_item = index.model().itemFromIndex(index)
            object_class_id = object_class_item.data(Qt.UserRole)
            object_id = object_item.data(Qt.UserRole)
            self.object_parameter_proxy_model.filter_object_class_id = object_class_id
            self.object_parameter_proxy_model.filter_object_id = object_id
            self.object_parameter_proxy_model.setFilterRegExp("")   # trick to trigger sorting


    @Slot("QPoint", name="show_object_tree_context_menu")
    def show_object_tree_context_menu(self, pos):
        """Context menu for object tree.

        Args:
            pos (QPoint): Mouse position
        """
        # logging.debug("object tree context menu")
        ind = self.ui.treeView_object.indexAt(pos)
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        self.object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, ind)#
        option = self.object_tree_context_menu.get_action()
        if option == "New object class":
            dialog = CustomQDialog(self, "New object class",
                name="Type name here...",
                description="Type description here...")
            answer = dialog.exec_()
            if answer == QDialog.Accepted:
                name = dialog.answer["name"]
                description = dialog.answer["description"]
                source_row = ind.model().mapToSource(ind).row()
                source_record = ind.model().sourceModel().record(source_row)
                display_order = source_record.value("object_class_display_order")
                self.add_item('object_class', name=name, description=description, display_order=display_order)
        elif option == "New object":
            dialog = CustomQDialog(self, "New object",
                name="Type name here...",
                description="Type description here...")
            answer = dialog.exec_()
            if answer == QDialog.Accepted:
                name = dialog.answer["name"]
                description = dialog.answer["description"]
                source_row = ind.model().mapToSource(ind).row()
                source_record = ind.model().sourceModel().record(source_row)
                class_id = source_record.value("object_class_id")
                self.add_item('object', class_id=class_id, name=name, description=description)
        elif option == "New relationship class":
            q = QSqlQuery()
            q.exec_("SELECT name FROM object_class ORDER BY display_order")
            related_class_name = list()
            related_class_name.append("Select related class name...")
            while q.next():
                related_class_name.append(q.value(0))
            dialog = CustomQDialog(self, "New relationship class",
                name="Type name here...",
                related_class_name=related_class_name)
            answer = dialog.exec_()
            if answer == QDialog.Accepted:
                name = dialog.answer["name"]
                related_class_name = dialog.answer["related_class_name"]
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
        self.join_model.select() #query().exec_()
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

# TODO: move this to another file
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
        self.input = dict()
        self.answer = dict()
        self.setWindowTitle(title)
        form = QFormLayout(self)
        for key,value in kwargs.items():
            if isinstance(value, str): # line edit
                input_ = QLineEdit(self)
                input_.setPlaceholderText(value)
            elif isinstance(value, list): # combo box
                input_ = QComboBox(self)
                input_.addItems(value)
            self.input[key] = input_
            form.addRow(input_)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        form.addRow(button_box)

    @Slot(name="save_and_accept")
    def save_and_accept(self):
        """Collect answer in output dict and accept"""
        for key,value in self.input.items():
            if isinstance(value, QLineEdit):
                self.answer[key] = value.text()
            elif isinstance(value, QComboBox):
                self.answer[key] = value.currentText()
        self.accept()
