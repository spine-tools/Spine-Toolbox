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
import datetime
from sqlalchemy import MetaData, Table, create_engine, text

class DataStoreForm(QWidget):
    """A widget to show and edit Spine objects in a data store."""

    class RootItem(QStandardItem):
        def __init__(self, text=None):
            super().__init__(text)
            self.object_class_data = None

    class ClassItem(QStandardItem):
        def __init__(self, text=None):
            super().__init__(text)
            self.id = None
            self.display_order = None
            self.relationship_class_data = None

    class ObjectItem(QStandardItem):
        def __init__(self, text=None):
            super().__init__(text)
            self.id = None
            self.class_id = None
            self.relationship_id = None

    def __init__(self, parent, reference):
        """ Initialize class.

        Args:
            parent (ToolBoxUI): QMainWindow instance
            reference (dict): Dictionary containing information about the data source
        """
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Class attributes
        self._parent = parent
        self.reference = reference
        self.source_engine = None
        self.source_meta = None
        self.source_conn = None
        self.source_trans = None
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
        self.setup_connection()
        self.init_object_tree_model()
        self.init_parameter_models()
        self.connect_signals()
        self.setWindowTitle("Spine Data Store    -- {} --".format(self.reference['database']))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.pushButton_commit.clicked.connect(self.commit_clicked)
        self.ui.pushButton_close.clicked.connect(self.close_clicked)
        self.ui.pushButton_reset.clicked.connect(self.reset_clicked)
        self.ui.treeView_object.currentIndexChanged.connect(self.filter_parameter_models)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.expand_leaf)

    @Slot(name="commit_clicked")
    def commit_clicked(self):
        """Coomit changes to source database."""
        comment = self.ui.lineEdit_commit_msg.text()
        if not comment:
            msg = "Commit message missing."
            self.statusbar.showMessage(msg, 3000)
            return
        if not self.source_conn:
            msg = "Not connected!"
            self.statusbar.showMessage(msg, 3000)
            return
        if not self.source_trans:
            msg = "No transaction!"
            self.statusbar.showMessage(msg, 3000)
            return
        date = datetime.datetime.now()
        commit_table = Table('commit', self.source_meta, autoload=True)
        upd = commit_table.update().where(commit_table.c.id == self.commit_id).\
            values(comment=comment, date=date)
        self.source_conn.execute(upd)
        self.source_trans.commit()
        self.source_trans = self.source_conn.begin()
        self.update_commit_id()

    @Slot(name="reset_clicked")
    def reset_clicked(self):
        if self.source_trans:
            self.source_trans.rollback()


    def setup_connection(self):
        """Create engine, metadata, connection and transaction."""
        db_url = self.reference['url']
        self.source_engine = create_engine(db_url)
        self.source_meta = MetaData(bind=self.source_engine)
        self.source_conn = self.source_engine.connect()
        self.source_trans = self.source_conn.begin()
        self.update_commit_id()

    def update_commit_id(self):
        """Get new commit id"""
        commit_table = Table('commit', self.source_meta, autoload=True)
        user = self.reference['username']
        date = datetime.datetime.now()
        ins = commit_table.insert().values(comment='in progress', date=date, user=user)
        result = self.source_conn.execute(ins)
        self.commit_id = result.inserted_primary_key[0]


    def init_object_tree_model(self):
        """Initialize object tree model from source database."""
        db_name = self.reference['database']
        root_item = self.RootItem(db_name)
        object_class_result = self.source_conn.execute("""
            SELECT id, name, display_order FROM object_class ORDER BY display_order
        """)
        object_class_data = [{k:v for k,v in row.items()} for row in object_class_result]
        root_item.object_class_data = object_class_data
        for object_class_row in object_class_data:
            object_class_item = self.ClassItem(object_class_row['name'])
            object_class_item.id = object_class_row['id']
            object_class_item.display_order = object_class_row['display_order']
            relationship_class_result = self.source_conn.execute(
                text("""
                    SELECT id, name
                    FROM relationship_class as rc
                    WHERE parent_type='object_class'
                    AND child_type='object_class'
                    AND (
                        parent_class_id=:object_class_id
                        OR child_class_id=:object_class_id
                    )
                """),
                object_class_id=object_class_item.id
            )
            relationship_class_data = [{k:v for k,v in row.items()} for row in relationship_class_result]
            object_class_item.relationship_class_data = relationship_class_data
            object_result = self.source_conn.execute(
                text("SELECT id, name FROM object WHERE class_id=:object_class_id"),
                object_class_id=object_class_item.id
            )
            for object_row in object_result:
                object_item = self.ObjectItem(object_row['name'])
                object_item.id = object_row['id']
                object_item.class_id = object_class_item.id
                for relationship_class_row in relationship_class_data:
                    relationship_class_item = self.visit(object_item, relationship_class_row)
                    object_item.appendRow(relationship_class_item)
                object_class_item.appendRow(object_item)
            root_item.appendRow(object_class_item)
        self.object_tree_model.appendRow(root_item)
        # setup object tree view
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_object.header().hide()
        self.ui.treeView_object.expand(root_item.index())
        self.ui.treeView_object.resizeColumnToContents(0)

    def visit(self, object_item, relationship_class_row):
        """Recursive function to create branches for relationships of relationships"""
        relationship_class_item = self.ClassItem(relationship_class_row['name'])
        relationship_class_item.id = relationship_class_row['id']
        relationship_class_result = self.source_conn.execute(
            text("""
                SELECT id, name
                FROM relationship_class as rc
                WHERE parent_type='relationship_class'
                AND child_type='object_class'
                AND parent_class_id=:relationship_class_id
            """),
            relationship_class_id=relationship_class_item.id
        )
        relationship_class_data = [{k:v for k,v in row.items()} for row in relationship_class_result]
        relationship_class_item.relationship_class_data = relationship_class_data
        if not object_item.relationship_id:
            related_object_result = self.source_conn.execute(
                text("""
                    SELECT o.id, o.name, o.class_id, r.id as relationship_id
                    FROM relationship as r
                    JOIN object as o
                    ON r.child_object_id=o.id
                    WHERE r.class_id=:relationship_class_id
                    AND r.parent_object_id=:object_id
                """),
                relationship_class_id=relationship_class_item.id,
                object_id=object_item.id
            )
        else:
            related_object_result = self.source_conn.execute(
                text("""
                    SELECT o.id, o.name, o.class_id, r.id as relationship_id
                    FROM relationship as r
                    JOIN object as o
                    ON r.child_object_id=o.id
                    WHERE r.class_id=:relationship_class_id
                    AND r.parent_object_id=:relationship_id
                """),
                relationship_class_id=relationship_class_item.id,
                relationship_id=object_item.relationship_id
            )
        for related_object_row in related_object_result:
            related_object_item = self.ObjectItem(related_object_row['name'])
            related_object_item.id = related_object_row['id']
            related_object_item.class_id = related_object_row['class_id']
            related_object_item.relationship_id = related_object_row['relationship_id']
            for relationship_class_row2 in relationship_class_data:
                relationship_class_item2 = self.visit(related_object_item, relationship_class_row2)
                related_object_item.appendRow(relationship_class_item2)
            relationship_class_item.appendRow(related_object_item)
        return relationship_class_item


    def init_parameter_models(self):
        """Initialize parameter models from source database."""
        parameter_data = list()
        results = self.source_conn.execute("""
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


    @Slot("QModelIndex", name="expand_leaf")
    def expand_leaf(self, index):
        """Expand leaf object into 'first class' object"""
        # logging.debug("expand leaf")
        clicked_item = index.model().itemFromIndex(index)
        if isinstance(clicked_item, self.ObjectItem) and not clicked_item.hasChildren():
            leaf_object_name = clicked_item.data(Qt.DisplayRole)
            items = index.model().findItems(leaf_object_name, Qt.MatchRecursive, column=0)
            for item in items:
                candidate_index = index.model().indexFromItem(item)
                if candidate_index != index:
                    self.ui.treeView_object.setCurrentIndex(candidate_index)
                    self.ui.treeView_object.scrollTo(candidate_index)
                    self.ui.treeView_object.expand(candidate_index)
                    break


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
            pass
        elif tree_level == 1: # object class
            object_class_item = index.model().itemFromIndex(index)
            object_class_id = object_class_item.id
            self.object_parameter_proxy_model.filter_object_class_id = object_class_id
            self.object_parameter_proxy_model.filter_object_id = None
            self.object_parameter_proxy_model.setFilterRegExp("")   # trick to trigger sorting
        elif tree_level == 2: # object class
            object_class_item = index.model().itemFromIndex(index.parent())
            object_item = index.model().itemFromIndex(index)
            object_class_id = object_class_item.id
            object_id = object_item.id
            self.object_parameter_proxy_model.filter_object_class_id = object_class_id
            self.object_parameter_proxy_model.filter_object_id = object_id
            self.object_parameter_proxy_model.setFilterRegExp("")   # trick to trigger filtering

    def new_object_class(self, ind):
        """Insert new object class.

        Args:
            ind (QModelIndex): the index of either the root or an object class item
        """
        dialog = CustomQDialog(self, "New object class",
            name="Type name here...",
            description="Type description here...")
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            name = dialog.answer["name"]
            description = dialog.answer["description"]
            if ind.parent().isValid(): # we are on an object class item
                root_item = ind.model().itemFromIndex(ind.parent())
                insert_at_row = ind.row() # insert before
                display_order = root_item.child(insert_at_row).display_order - 1 # insert before
            else: # we are on the root item
                root_item = ind.model().itemFromIndex(ind)
                insert_at_row = root_item.rowCount() # insert last
                display_order = root_item.child(insert_at_row-1).display_order # insert last
            object_class_id = self.insert_item(
                'object_class',
                name=name,
                description=description,
                display_order=display_order
            )
            # if insert is successful, add item to model as well
            if object_class_id:
                object_class_item = self.ClassItem(name)
                object_class_item.id = object_class_id
                object_class_item.display_order = display_order
                root_item.insertRow(insert_at_row, QStandardItem())
                root_item.setChild(insert_at_row, 0, object_class_item) # TODO: find out why is this necessary
                object_class_ind = ind.model().indexFromItem(object_class_item)
                self.ui.treeView_object.setCurrentIndex(object_class_ind)

    def new_object(self, ind):
        """Insert new object.

        Args:
            ind (QModelIndex): the index of an object class item
        """
        dialog = CustomQDialog(self, "New object",
            name="Type name here...",
            description="Type description here...")
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            object_class_item = ind.model().itemFromIndex(ind)
            name = dialog.answer["name"]
            description = dialog.answer["description"]
            class_id = object_class_item.id
            object_id = self.insert_item('object', class_id=class_id, name=name, description=description)
            # if insert is successful, add item to model as well
            if object_id:
                object_item = self.ObjectItem(name)
                object_item.id = object_id
                # append relationship class items from object class item
                relationship_class_data = object_class_item.relationship_class_data
                relationship_class_name = [row['name'] for row in relationship_class_data]
                for rc_name in relationship_class_name:
                    relationship_class_item = QStandardItem(rc_name)
                    object_item.appendRow(relationship_class_item)
                object_class_item.appendRow(object_item)
                self.ui.treeView_object.expand(ind)
                self.ui.treeView_object.setCurrentIndex(ind.model().indexFromItem(object_item))

    def new_relationship_class(self, ind):
        """Insert new relationship class.

        Args:
            ind (QModelIndex): the index of an object class item
        """
        object_class_data = ind.model().itemFromIndex(ind.parent()).object_class_data
        object_class_name = [row['name'] for row in object_class_data]
        related_class_name = ['Select related class...']
        related_class_name.extend(object_class_name)
        dialog = CustomQDialog(self, "New relationship class",
            name="Type name here...",
            related_class_name=related_class_name)
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            name = dialog.answer['name']
            parent_type='object_class'
            parent_class_id = ind.model().itemFromIndex(ind).id
            child_type='object_class'
            child_class_row = dialog.answer['related_class_name']['index'] - 1
            child_class_id = object_class_data[child_class_row]['id']
            relationship_class_id = self.insert_item(
                'relationship_class',
                name=name,
                parent_type=parent_type,
                parent_class_id=parent_class_id,
                child_type=child_type,
                child_class_id=child_class_id
            )
            # if insert is successful, add item to model as well
            if relationship_class_id:
                object_class_item = ind.model().itemFromIndex(ind)
                object_class_item.relationship_class_data.append({
                    'id': relationship_class_id,
                    'name': name,
                })
                for row in range(object_class_item.rowCount()):
                    object_item = object_class_item.child(row)
                    relationship_class_item = QStandardItem(name)
                    object_item.appendRow(relationship_class_item)


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
            self.new_object_class(ind)
        elif option == "New object":
            self.new_object(ind)
        elif option == "New relationship class":
            self.new_relationship_class(ind)
        elif option == "Rename":
            name = ind.data(Qt.DisplayRole)
            answer = QInputDialog.getText(self, "Rename item", "Enter new name:",\
                QLineEdit.Normal, name)
            new_name = answer[0]
            if not new_name: # cancel clicked
                return
            if new_name == name:
                return
            self.rename_item(table, name, new_name)
        elif option == "Remove":
            ind.model().removeRow(ind.row(), ind.parent())
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    def insert_item(self, table, **kwargs):
        """Add new insert statement commit list"""
        # TODO: find the most correct way to manage return codes
        source_table = Table(table, self.source_meta, autoload=True)
        kwargs['commit_id'] = self.commit_id
        try:
            ins = source_table.insert().values(**kwargs)
            result = self.source_conn.execute(ins)
            last_id = result.inserted_primary_key[0]
            return last_id
        except Exception as e:
            self.statusbar.showMessage(str(e), 3000)
            return False

    def update_item(self, table, name, new_name):
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
            if self.source_trans:
                self.source_trans.rollback()
                self.source_trans.close()
            if self.source_conn:
                self.source_conn.close()
            if self.source_engine:
                self.source_engine.dispose()
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
                self.answer[key] = {
                    'text': value.currentText(),
                    'index': value.currentIndex()
                }
        self.accept()
