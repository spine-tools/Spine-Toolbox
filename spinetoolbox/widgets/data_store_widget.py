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

from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView,\
    QDialog, QLineEdit, QInputDialog
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QStandardItem, QStandardItemModel
from ui.data_store_form import Ui_Form
from config import STATUSBAR_SS
from widgets.custom_menus import ObjectTreeContextMenu
from widgets.custom_qdialog import CustomQDialog
from helpers import busy_effect
from models import MinimalTableModel, CustomSortFilterProxyModel
import logging
import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, Bundle, aliased

class DataStoreForm(QWidget):
    """A widget to show and edit Spine objects in a data store."""

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
        self.Base = None
        self.engine = None
        self.ObjectClass = None
        self.Object = None
        self.RelationshipClass = None
        self.Relationship = None
        self.Parameter = None
        self.ParameterValue = None
        self.object_class = None
        self.Commit = None
        self.session = None
        self.bold_font = None
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
        self.ui.tableView_object_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_relationship_parameter.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # context menus
        self.object_tree_context_menu = None
        self.create_session()
        self.init_object_tree_model()
        #self.init_parameter_models()
        self.connect_signals()
        self.setWindowTitle("Spine Data Store    -- {} --".format(self.reference['database']))
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.pushButton_commit.clicked.connect(self.commit_clicked)
        self.ui.pushButton_close.clicked.connect(self.close_clicked)
        self.ui.pushButton_reset.clicked.connect(self.reset_clicked)
        #self.ui.treeView_object.currentIndexChanged.connect(self.filter_parameter_models)
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
        if not self.session:
            msg = "No session!"
            self.statusbar.showMessage(msg, 3000)
            return
        self.commit.comment = comment
        self.commit.date = datetime.datetime.now()
        try:
            self.session.commit()
        except IntegrityError as e:
            msg = "Could not commit the transaction: {}".format(e)
            self.statusbar.showMessage(msg, 3000)
            self.session.rollback()
            return
        self.new_commit()

    @Slot(name="reset_clicked")
    def reset_clicked(self):
        if self.session:
            self.session.rollback()
            self.new_commit()

    def create_session(self):
        """Create base, engine, reflect tables and create session."""
        db_url = self.reference['url']
        self.Base = automap_base()
        self.engine = create_engine(db_url) #, echo=True)
        self.Base.prepare(self.engine, reflect=True)
        self.ObjectClass = self.Base.classes.object_class
        self.Object = self.Base.classes.object
        self.RelationshipClass = self.Base.classes.relationship_class
        self.Relationship = self.Base.classes.relationship
        self.Parameter = self.Base.classes.parameter
        self.ParameterValue = self.Base.classes.parameter_value
        # bundles
        self.object_class = Bundle(
            'object_class',
            self.ObjectClass.id,
            self.ObjectClass.name,
            self.ObjectClass.display_order
        )
        self.Commit = self.Base.classes.commit
        self.session = Session(self.engine)
        self.new_commit()

    def new_commit(self):
        """Add row to commit table"""
        comment = 'in progress'
        user = self.reference['username']
        date = datetime.datetime.now()
        self.commit = self.Commit(comment=comment, date=date, user=user)
        self.session.add(self.commit)
        self.session.flush() # there shouldn't be any IntegrityError here


    def init_object_tree_model(self):
        """Initialize object tree model from source database."""
        self.object_tree_model.clear()
        db_name = self.reference['database']
        # create root item
        root_item = QStandardItem(db_name)
        self.bold_font = root_item.font()
        self.bold_font.setBold(True)
        root_item.setFont(self.bold_font)
        # get all object_classes
        for object_class in self.session.query(
                    self.ObjectClass.id,
                    self.ObjectClass.name,
                    self.ObjectClass.display_order,
                ).order_by(self.ObjectClass.display_order):
            # create object class item
            object_class_item = QStandardItem(object_class.name)
            object_class_item.setFont(self.bold_font)
            object_class_item.setData('object_class', Qt.UserRole)
            object_class_item.setData(object_class._asdict(), Qt.UserRole+1)
            # get objects of this class
            object_list = self.session.query(
                self.Object.id,
                self.Object.class_id,
                self.Object.name
            ).filter_by(class_id=object_class.id).all()
            # get relationship classes involving the present class
            # as parent
            relationship_class_as_parent_list = self.session.query(
                    self.RelationshipClass.id,
                    self.RelationshipClass.name,
                    self.RelationshipClass.child_object_class_id,
                    self.RelationshipClass.parent_object_class_id
                ).filter_by(parent_object_class_id=object_class.id)
            # ...as child
            relationship_class_as_child_list = self.session.query(
                    self.RelationshipClass.id,
                    self.RelationshipClass.name,
                    self.RelationshipClass.parent_object_class_id.label('child_object_class_id'),
                    self.RelationshipClass.child_object_class_id.label('parent_object_class_id')
                ).filter_by(parent_relationship_class_id=None).\
                filter_by(child_object_class_id=object_class.id)
            # recursively populate branches
            for object_ in object_list:
                # create object item
                object_item = QStandardItem(object_.name)
                object_item.setData('object', Qt.UserRole)
                object_item.setData(object_._asdict(), Qt.UserRole+1)
                for relationship_class in relationship_class_as_parent_list:
                    # create relationship class item
                    relationship_class_item = self.visit_relationship_class(
                        relationship_class,
                        object_,
                        role='parent'
                    )
                    object_item.appendRow(relationship_class_item)
                for relationship_class in relationship_class_as_child_list:
                    # create relationship class item
                    relationship_class_item = self.visit_relationship_class(
                        relationship_class,
                        object_,
                        role='child'
                    )
                    object_item.appendRow(relationship_class_item)
                object_class_item.appendRow(object_item)
            root_item.appendRow(object_class_item)
        self.object_tree_model.appendRow(root_item)
        # setup object tree view
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_object.header().hide()
        self.ui.treeView_object.expand(root_item.index())
        self.ui.treeView_object.resizeColumnToContents(0)

    def visit_relationship_class(self, relationship_class, object_, role=None):
        """Recursive function to create branches for relationships of relationships

        Args:
            relationship_class (KeyedTuple or dict): relationship class to explore
            object_ (KeyedTuple or dict): parent object
        """
        # create relationship class item
        relationship_class_item = QStandardItem(relationship_class.name)
        relationship_class_item.setFont(self.bold_font)
        relationship_class_item.setData('relationship_class', Qt.UserRole)
        relationship_class_item.setData(relationship_class._asdict(), Qt.UserRole+1)
        # get relationship classes having this relationship class as parent
        # (in our convention, relationship classes are never child classes
        # in other relationship classes)
        new_relationship_class_list = self.session.query(
                self.RelationshipClass.id,
                self.RelationshipClass.name,
                self.RelationshipClass.child_object_class_id,
                self.RelationshipClass.parent_relationship_class_id
            ).filter_by(parent_relationship_class_id=relationship_class.id).all()
        if 'parent_relationship_id' in object_.keys():
            # the parent object is itself a child object in other relationship
            # get new child objects in this new relationship class
            new_object_list = self.session.query(
                    self.Object.id,
                    self.Object.class_id,
                    self.Object.name,
                    self.Relationship.id.label('parent_relationship_id')
                ).filter(self.Object.id == self.Relationship.child_object_id).\
                filter(self.Relationship.class_id == relationship_class.id).\
                filter(self.Relationship.parent_relationship_id == object_.parent_relationship_id).all()
        else:
            # the parent object is a 'first-class' object. In the tree, this
            # object is located directly beneath an object class
            if role == 'parent':
                # get new child objects in this new relationship class
                new_object_list = self.session.query(
                        self.Object.id,
                        self.Object.class_id,
                        self.Object.name,
                        self.Relationship.id.label('parent_relationship_id')
                    ).filter(self.Object.id == self.Relationship.child_object_id).\
                    filter(self.Relationship.class_id == relationship_class.id).\
                    filter(self.Relationship.parent_object_id == object_.id).all()
            elif role == 'child':
                # get new child objects in this new relationship class
                new_object_list = self.session.query(
                        self.Object.id,
                        self.Object.class_id,
                        self.Object.name,
                        self.Relationship.id.label('parent_relationship_id')
                    ).filter(self.Object.id == self.Relationship.parent_object_id).\
                    filter(self.Relationship.class_id == relationship_class.id).\
                    filter(self.Relationship.child_object_id == object_.id).all()
        # recursively populate branches
        for new_object in new_object_list:
            # create child object item
            new_object_item = QStandardItem(new_object.name)
            new_object_item.setData('object', Qt.UserRole)
            new_object_item.setData(new_object._asdict(), Qt.UserRole+1)
            for new_relationship_class in new_relationship_class_list:
                # create next relationship class item
                new_relationship_class_item = self.visit_relationship_class(
                    new_relationship_class,
                    new_object
                )
                new_object_item.appendRow(new_relationship_class_item)
            relationship_class_item.appendRow(new_object_item)
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
        clicked_type = index.data(Qt.UserRole)
        if not clicked_type == 'object':
            return
        clicked_item = index.model().itemFromIndex(index)
        if clicked_item.hasChildren():
            return
        clicked_object = index.data(Qt.UserRole+1)
        root_item = index.model().invisibleRootItem().child(0)
        for i in range(root_item.rowCount()):
            object_class_item = root_item.child(i)
            object_class = object_class_item.data(Qt.UserRole+1)
            if object_class['id'] == clicked_object['class_id']:
                for j in range(object_class_item.rowCount()):
                    object_item = object_class_item.child(j)
                    object_ = object_item.data(Qt.UserRole+1)
                    if object_['id'] == clicked_object['id']:
                        object_index = index.model().indexFromItem(object_item)
                        self.ui.treeView_object.setCurrentIndex(object_index)
                        self.ui.treeView_object.scrollTo(object_index)
                        self.ui.treeView_object.expand(object_index)
                        return

    @Slot("QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, index):
        """Populate tableViews whenever an object item is selected in the treeView"""
        # logging.debug("filter_parameter_models")
        tree_level = 0
        root_index = index
        while root_index.parent().isValid():
            root_index = root_index.parent()
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

    def new_object_class(self, index):
        """Insert new object class.

        Args:
            index (QModelIndex): the index of either the root or an object class item
        """
        dialog = CustomQDialog(self, "New object class",
            name="Type name here...",
            description="Type description here...")
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        name = dialog.answer["name"]
        description = dialog.answer["description"]
        if index.parent().isValid(): # we are on an object class item
            # prepare to insert the new item just before the selected one
            root_item = index.model().itemFromIndex(index.parent())
            insert_at_row = index.row()
            child_item = root_item.child(insert_at_row)
            display_order = child_item.data(Qt.UserRole+1)['display_order'] - 1
        else: # we are on the root item
            # prepare to insert the new item and the end
            root_item = index.model().itemFromIndex(index)
            insert_at_row = root_item.rowCount()
            child_item = root_item.child(insert_at_row - 1)
            display_order = child_item.data(Qt.UserRole+1)['display_order']
        object_class = self.ObjectClass(
            name=name,
            description=description,
            display_order=display_order,
            commit_id=self.commit.id
        )
        self.session.add(object_class)
        try:
            self.session.flush() # to get object class id
        except IntegrityError as e:
            msg = "Could not insert new object class: {}".format(e)
            self.statusbar.showMessage(msg, 3000)
            self.session.rollback()
            return
        # manually add item to model as well
        object_class_item = QStandardItem(name)
        object_class_item.setFont(self.bold_font)
        object_class_item.setData('object_class', Qt.UserRole)
        object_class_item.setData(object_class.__dict__, Qt.UserRole+1)
        root_item.insertRow(insert_at_row, QStandardItem())
        root_item.setChild(insert_at_row, 0, object_class_item) # TODO: find out why is this necessary
        # scroll to newly inserted item in treeview
        object_class_index = index.model().indexFromItem(object_class_item)
        self.ui.treeView_object.setCurrentIndex(object_class_index)
        self.ui.treeView_object.scrollTo(object_class_index)

    def new_object(self, index):
        """Insert new object.

        Args:
            index (QModelIndex): the index of an object class item
        """
        dialog = CustomQDialog(self, "New object",
            name="Type name here...",
            description="Type description here...")
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        object_class_item = index.model().itemFromIndex(index)
        name = dialog.answer["name"]
        description = dialog.answer["description"]
        class_id = object_class_item.data(Qt.UserRole+1)['id']
        object_ = self.Object(
            class_id=class_id,
            name=name,
            description=description,
            commit_id=self.commit.id
        )
        self.session.add(object_)
        try:
            self.session.flush() # to get object id
        except IntegrityError as e:
            msg = "Could not insert new object: {}".format(e)
            self.statusbar.showMessage(msg, 3000)
            self.session.rollback()
            return
        # manually add item to model as well
        object_class = object_class_item.data(Qt.UserRole+1)
        object_item = QStandardItem(name)
        object_item.setData('object', Qt.UserRole)
        object_item.setData(object_.__dict__, Qt.UserRole+1)
        # get relationship classes involving the present object class
        # as parent
        relationship_class_as_parent_list = self.session.query(
                self.RelationshipClass.id,
                self.RelationshipClass.name,
                self.RelationshipClass.child_object_class_id,
                self.RelationshipClass.parent_object_class_id
            ).filter_by(parent_object_class_id=object_class['id'])
        # ...as child
        relationship_class_as_child_list = self.session.query(
                self.RelationshipClass.id,
                self.RelationshipClass.name,
                self.RelationshipClass.parent_object_class_id.label('child_object_class_id'),
                self.RelationshipClass.child_object_class_id.label('parent_object_class_id')
            ).filter_by(parent_relationship_class_id=None).\
            filter_by(child_object_class_id=object_class['id'])
        relationship_class_list = relationship_class_as_parent_list.\
                                    union(relationship_class_as_child_list).all()
        # create and append relationship class items
        for relationship_class in relationship_class_list:
            # no need to visit the relationship class here,
            # since this object does not have any relationships yet
            relationship_class_item = QStandardItem(relationship_class.name)
            relationship_class_item.setFont(self.bold_font)
            relationship_class_item.setData('relationship_class', Qt.UserRole)
            relationship_class_item.setData(relationship_class._asdict(), Qt.UserRole+1)
            object_item.appendRow(relationship_class_item)
        object_class_item.appendRow(object_item)
        # scroll to newly inserted item in treeview
        object_index = index.model().indexFromItem(object_item)
        self.ui.treeView_object.setCurrentIndex(object_index)
        self.ui.treeView_object.scrollTo(object_index)

    def new_relationship_class(self, index):
        """Insert new relationship class.

        Args:
            index (QModelIndex): the index of an object or relationship class item
        """
        # query object_class table
        child_object_class_list = self.session.query(self.ObjectClass).\
                order_by(self.ObjectClass.display_order)
        child_object_class_name_list = ['Select child object class...']
        child_object_class_name_list.extend([item.name for item in child_object_class_list])
        dialog = CustomQDialog(self, "New relationship class",
            name="Type name here...",
            child_object_class_name_list=child_object_class_name_list)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        name = dialog.answer['name']
        # get information about the parent
        parent_class_item = index.model().itemFromIndex(index)
        parent_type = parent_class_item.data(Qt.UserRole)
        parent_class = parent_class_item.data(Qt.UserRole+1)
        if parent_type == 'relationship_class':
            parent_relationship_class_id = parent_class['id']
            parent_object_class_id = None
        elif parent_type == 'object_class':
            parent_relationship_class_id = None
            parent_object_class_id = parent_class['id']
        # and about the child
        # get selected index from combobox, to look it up in child_class_list
        ind = dialog.answer['child_object_class_name_list']['index'] - 1
        child_object_class_id = child_object_class_list[ind].id
        relationship_class = self.RelationshipClass(
            name=name,
            parent_relationship_class_id=parent_relationship_class_id,
            parent_object_class_id=parent_object_class_id,
            child_object_class_id=child_object_class_id,
            commit_id=self.commit.id
        )
        self.session.add(relationship_class)
        try:
            self.session.flush() # to get the relationship class id
        except IntegrityError as e:
            msg = "Could not insert new relationship class: {}".format(e)
            self.statusbar.showMessage(msg, 3000)
            self.session.rollback()
            return
        # manually add items to model
        # append new relationship class item to objects of parent_class
        relationship_class_dict = relationship_class.__dict__
        for row in range(parent_class_item.rowCount()):
            object_item = parent_class_item.child(row)
            relationship_class_item = QStandardItem(name)
            relationship_class_item.setFont(self.bold_font)
            relationship_class_item.setData('relationship_class', Qt.UserRole)
            relationship_class_item.setData(relationship_class_dict, Qt.UserRole+1)
            object_item.appendRow(relationship_class_item)
        # ...and to objects of child class if parent class is an object class
        if parent_type == 'object_class':
            # find child_class_item in the first level
            root_item = index.model().invisibleRootItem().child(0)
            for row in range(root_item.rowCount()):
                object_class_item = root_item.child(row)
                object_class = object_class_item.data(Qt.UserRole+1)
                if object_class['id'] == child_object_class_id:
                    for row in range(object_class_item.rowCount()):
                        object_item = object_class_item.child(row)
                        relationship_class_item = QStandardItem(name)
                        relationship_class_item.setFont(self.bold_font)
                        relationship_class_item.setData('relationship_class', Qt.UserRole)
                        # invert relationship class and save it
                        relationship_class_dict['child_object_class_id'] = parent_object_class_id
                        relationship_class_dict['parent_object_class_id'] = child_object_class_id
                        relationship_class_item.setData(relationship_class_dict, Qt.UserRole+1)
                        object_item.appendRow(relationship_class_item)
                    return
        # now it seems meaningless to scroll somewhere

    def new_relationship(self, index):
        """Insert new relationship.

        Args:
            index (QModelIndex): the index of a relationship class item
        """
        relationship_class_item = index.model().itemFromIndex(index)
        relationship_class = relationship_class_item.data(Qt.UserRole+1)
        child_object_class_id = relationship_class['child_object_class_id']
        child_object_list = self.session.query(self.Object).\
            filter_by(class_id=child_object_class_id).all()
        if not child_object_list:
            child_object_class_name = self.session.query(self.ObjectClass).\
                filter_by(id=child_object_class_id).one().name
            msg = "There are no objects of child class {}.".format(child_object_class_name)
            self.statusbar.showMessage(msg, 3000)
            return
        child_object_name_list = ['Select child object...']
        child_object_name_list.extend([item.name for item in child_object_list])
        dialog = CustomQDialog(self, "New relationship",
            name="Type name here...",
            child_object_name_list=child_object_name_list)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        class_id = relationship_class['id']
        name = dialog.answer["name"]
        parent_object_item = index.model().itemFromIndex(index.parent())
        parent_object = parent_object_item.data(Qt.UserRole+1)
        if 'parent_relationship_id' in parent_object.keys():
            parent_relationship_id = parent_object['parent_relationship_id']
            parent_object_id = None
        else:
            parent_relationship_id = None
            parent_object_id = parent_object['id']
        # get selected index from combobox, to look it up in child_object_list
        ind = dialog.answer['child_object_name_list']['index'] - 1
        child_object_id = child_object_list[ind].id
        relationship = self.Relationship(
            class_id=class_id,
            name=name,
            parent_relationship_id=parent_relationship_id,
            parent_object_id=parent_object_id,
            child_object_id=child_object_id
        )
        self.session.add(relationship)
        try:
            self.session.flush() # to get the relationship id
        except IntegrityError as e:
            msg = "Could not insert new relationship: {}".format(e)
            self.statusbar.showMessage(msg, 3000)
            self.session.rollback()
            return
        # alternative 1, rebuild the whole model
        # self.init_object_tree_model()
        # alternative 2, manually add items to model
        # (pros: faster, doesn't collapse all items. cons: ugly, harder to maintain?)
        # add child object item to relationship class...
        # create new object
        new_object_name = dialog.answer['child_object_name_list']['text']
        new_object_item = QStandardItem(new_object_name)
        # query object table to get new object directly as dict
        new_object = self.session.query(
                self.Object.id,
                self.Object.class_id,
                self.Object.name
            ).filter_by(id=child_object_id).one_or_none()._asdict()
        # add parent relationship id manually
        # (this is better than joining relationship table in the query above)
        new_object['parent_relationship_id'] = relationship.id
        new_object_item.setData('object', Qt.UserRole)
        new_object_item.setData(new_object, Qt.UserRole+1)
        # get relationship classes having the present relationship class as parent
        new_relationship_class_list = self.session.query(
                self.RelationshipClass.id,
                self.RelationshipClass.name,
                self.RelationshipClass.child_object_class_id,
                self.RelationshipClass.parent_relationship_class_id
            ).filter_by(parent_relationship_class_id=relationship_class['id']).all()
        # create and append relationship class items
        for new_relationship_class in new_relationship_class_list:
            new_relationship_class_item = self.visit_relationship_class(
                new_relationship_class,
                new_object
            )
            new_object_item.appendRow(new_relationship_class_item)
        relationship_class_item.appendRow(new_object_item)
        # scroll to newly inserted item in treeview
        new_object_index = index.model().indexFromItem(new_object_item)
        self.ui.treeView_object.setCurrentIndex(new_object_index)
        self.ui.treeView_object.scrollTo(new_object_index)
        # ...and if parent class is an object class,
        # then add child object item to inverse relationship class...
        if 'parent_object_class_id' in relationship_class.keys()\
                and relationship_class['parent_object_class_id'] is not None:
            # find inverse relationship class item by traversing the tree from the root
            root_item = index.model().invisibleRootItem().child(0)
            inv_relationship_class_item = None
            for i in range(root_item.rowCount()):
                object_class_item = root_item.child(i)
                object_class = object_class_item.data(Qt.UserRole+1)
                if object_class['id'] == child_object_class_id:
                    for j in range(object_class_item.rowCount()):
                        object_item = object_class_item.child(j)
                        object_ = object_item.data(Qt.UserRole+1)
                        if object_['id'] == child_object_id:
                            for k in range(object_item.rowCount()):
                                relationship_class_item = object_item.child(k)
                                relationship_class = relationship_class_item.data(Qt.UserRole+1)
                                if relationship_class['id'] == class_id:
                                    inv_relationship_class_item = relationship_class_item
                                    break
                            break
                    break
            if inv_relationship_class_item:
                # create new object
                new_object_item = QStandardItem(parent_object['name'])
                # query object table to get new object directly as dict
                new_object = self.session.query(
                        self.Object.id,
                        self.Object.class_id,
                        self.Object.name
                    ).filter_by(id=parent_object_id).one_or_none()._asdict()
                # add parent relationship id manually
                new_object['parent_relationship_id'] = relationship.id
                new_object_item.setData('object', Qt.UserRole)
                new_object_item.setData(new_object, Qt.UserRole+1)
                # create and append relationship class items
                for new_relationship_class in new_relationship_class_list:
                    new_relationship_class_item = self.visit_relationship_class(
                        new_relationship_class,
                        new_object
                    )
                    new_object_item.appendRow(new_relationship_class_item)
                inv_relationship_class_item.appendRow(new_object_item)


    def rename_item(self, index):
        """Rename item in the database and treeview"""
        item = index.model().itemFromIndex(index)
        name = item.text()
        answer = QInputDialog.getText(self, "Rename item", "Enter new name:",\
            QLineEdit.Normal, name)
        new_name = answer[0]
        if not new_name: # cancel clicked
            return
        if new_name == name: # nothing to do here
            return
        # find out which table
        entity_type = item.data(Qt.UserRole)
        if entity_type == 'object_class':
            table = self.ObjectClass
        elif entity_type == 'object':
            table = self.Object
        elif entity_type == 'relationship_class':
            table = self.RelationshipClass
        else:
            return # should never happen
        # get item from table
        entity = item.data(Qt.UserRole+1)
        instance = self.session.query(table).filter_by(id=entity['id']).one_or_none()
        if instance:
            instance.name = new_name
            try:
                self.session.flush()
            except IntegrityError as e:
                msg = "Could not rename item: {}".format(e)
                self.statusbar.showMessage(msg, 3000)
                self.session.rollback()
                return
            # manually rename all items in model
            items = index.model().findItems(name, Qt.MatchRecursive)
            for it in items:
                ent_type = it.data(Qt.UserRole)
                ent = it.data(Qt.UserRole+1)
                if ent_type == entity_type and ent['id'] == entity['id']:
                    ent['name'] = new_name
                    it.setText(new_name)

    def remove_item(self, index):
        """Remove item from the treeview"""
        item = index.model().itemFromIndex(index)
        # find out which table
        entity_type = item.data(Qt.UserRole)
        if entity_type == 'object_class':
            table = self.ObjectClass
        elif entity_type == 'object':
            table = self.Object
        elif entity_type == 'relationship_class':
            table = self.RelationshipClass
        else:
            return # should never happen
        # get item from table
        entity = item.data(Qt.UserRole+1)
        instance = self.session.query(table).filter_by(id=entity['id']).one_or_none()
        if instance:
            self.session.delete(instance)
            try:
                self.session.flush()
            except IntegrityError as e:
                msg = "Could not insert new relationship class: {}".format(e)
                self.statusbar.showMessage(msg, 3000)
                self.session.rollback()
                return
            # manually remove all items in model
            def visit_and_remove(it):
                """Visit item and remove it if necessary.
                Returns:
                    True if item was removed, False otherwise
                """
                logging.debug(it.text())
                ent_type = it.data(Qt.UserRole)
                ent = it.data(Qt.UserRole+1)
                if ent_type == entity_type and ent['id'] == entity['id']:
                    ind = index.model().indexFromItem(it)
                    index.model().removeRows(ind.row(), 1, ind.parent())
                    return True
                if ent_type == 'relationship_class':
                    child_object_class_id = ent['child_object_class_id']
                    if child_object_class_id == entity['id']:
                        ind = index.model().indexFromItem(it)
                        index.model().removeRows(ind.row(), 1, ind.parent())
                        return True
                i = 0
                while True:
                    if i == it.rowCount():
                        break
                    if not visit_and_remove(it.child(i)):
                        i += 1
                return False
            root_item = index.model().invisibleRootItem().child(0)
            visit_and_remove(root_item)


    @Slot("QPoint", name="show_object_tree_context_menu")
    def show_object_tree_context_menu(self, pos):
        """Context menu for object tree.

        Args:
            pos (QPoint): Mouse position
        """
        # logging.debug("object tree context menu")
        index = self.ui.treeView_object.indexAt(pos)
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        self.object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, index)#
        option = self.object_tree_context_menu.get_action()
        if option == "New object class":
            self.new_object_class(index)
        elif option == "New object":
            self.new_object(index)
        elif option == "New relationship class":
            self.new_relationship_class(index)
        elif option == "New relationship":
            self.new_relationship(index)
        elif option == "Rename":
            self.rename_item(index)
        elif option == "Remove":
            self.remove_item(index)
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
            if self.session:
                self.session.rollback()
                self.session.close()
            if self.engine:
                self.engine.dispose()
            event.accept()
