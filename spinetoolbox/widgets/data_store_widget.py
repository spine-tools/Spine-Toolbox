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

import time  # just to measure loading time and sqlalchemy ORM performance
import logging
from PySide2.QtWidgets import QMainWindow, QWidget, QStatusBar, QHeaderView, QDialog, QLineEdit, QInputDialog, \
    QMessageBox
from PySide2.QtCore import Slot, Qt, QSettings
from PySide2.QtGui import QStandardItem, QFont, QFontMetrics
from ui.data_store_form import Ui_MainWindow
from config import STATUSBAR_SS
from widgets.custom_menus import ObjectTreeContextMenu, ParameterValueContextMenu, ParameterContextMenu
from widgets.lineedit_delegate import LineEditDelegate
from widgets.combobox_delegate import ComboBoxDelegate
from widgets.custom_qdialog import CustomQDialog, AddObjectClassesDialog, AddObjectsDialog, \
    AddRelationshipClassesDialog, AddRelationshipsDialog
from helpers import busy_effect
from models import ObjectTreeModel, MinimalTableModel, ObjectParameterValueProxy, RelationshipParameterValueProxy, \
    ObjectParameterProxy, RelationshipParameterProxy
from datetime import datetime, timezone
from sqlalchemy.ext.automap import automap_base, generate_relationship
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, aliased, interfaces


class DataStoreForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store."""

    def __init__(self, parent, data_store, engine, database, username):
        """ Initialize class.

        Args:
            parent (ToolBoxUI): QMainWindow instance
            data_store (DataStore): the DataStore instance that owns this form
            engine (Engine): The sql alchemy engine to use with this Store
            database (str): The database name
            username (str): The user name
        """
        tic = time.clock()
        super().__init__(flags=Qt.Window)
        self._data_store = data_store
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox Data Store")
        # Class attributes
        self._parent = parent
        self.engine = engine
        self.database = database
        self.username = username
        self.Base = None
        self.ObjectClass = None
        self.Object = None
        self.RelationshipClass = None
        self.Relationship = None
        self.Parameter = None
        self.ParameterValue = None
        self.object_class = None
        self.Commit = None
        self.session = None
        self.transactions = None
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Attempt to create base
        if not self.create_base_and_reflect_tables():
            self.close()
            return
        self.create_session()
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self)
        # Parameter value models
        self.object_parameter_value_model = MinimalTableModel(self)
        self.object_parameter_value_proxy = ObjectParameterValueProxy(self)
        self.relationship_parameter_value_model = MinimalTableModel(self)
        self.relationship_parameter_value_proxy = RelationshipParameterValueProxy(self)
        # Parameter (definition) models
        self.object_parameter_model = MinimalTableModel(self)
        self.object_parameter_proxy = ObjectParameterProxy(self)
        self.relationship_parameter_model = MinimalTableModel(self)
        self.relationship_parameter_proxy = RelationshipParameterProxy(self)
        # Add status bar to form
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        # context menus
        self.object_tree_context_menu = None
        self.object_parameter_value_context_menu = None
        self.relationship_parameter_value_context_menu = None
        self.object_parameter_context_menu = None
        self.relationship_parameter_context_menu = None
        # init models and views
        self.default_font_height = QFontMetrics(QFont("", 0)).lineSpacing()
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_models()
        self.init_parameter_value_views()
        self.init_parameter_views()
        self.connect_signals()
        self.restore_ui()
        self.setWindowTitle("Spine Data Store    -- {} --".format(self.database))
        toc = time.clock()
        logging.debug("Elapsed = {}".format(toc - tic))

    def connect_signals(self):
        """Connect signals to slots."""
        self._data_store.destroyed.connect(self.data_store_destroyed)
        self.ui.actionCommit.triggered.connect(self.commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionClose.triggered.connect(self.close_session)
        self.ui.actionAdd_object_classes.triggered.connect(self.add_object_classes)
        self.ui.actionAdd_objects.triggered.connect(self.add_objects)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.add_relationship_classes)
        self.ui.actionAdd_relationships.triggered.connect(self.add_relationships)
        self.ui.actionAdd_parameter.triggered.connect(self.add_parameter)
        self.ui.actionAdd_parameter_value.triggered.connect(self.add_parameter_value)
        self.ui.treeView_object.selectionModel().currentChanged.connect(self.filter_parameter_value_models)
        self.ui.treeView_object.selectionModel().currentChanged.connect(self.filter_parameter_models)
        self.ui.treeView_object.editKeyPressed.connect(self.rename_item)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.expand_at_top_level)
        self.ui.tableView_object_parameter_value.customContextMenuRequested.\
            connect(self.show_object_parameter_value_context_menu)
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.\
            connect(self.show_relationship_parameter_value_context_menu)
        self.ui.tableView_object_parameter.customContextMenuRequested.\
            connect(self.show_object_parameter_context_menu)
        self.ui.tableView_relationship_parameter.customContextMenuRequested.\
            connect(self.show_relationship_parameter_context_menu)

    @Slot(name="data_store_destroyed")
    def data_store_destroyed(self):
        """Close this form without commiting any changes when data store item is destroyed."""
        self._data_store = None
        self.close()

    @Slot(name="commit_session")
    def commit_session(self):
        """Commit changes to source database."""
        # comment = self.ui.lineEdit_commit_msg.text()
        if not self.session:
            msg = "No session!"
            self.ui.statusbar.showMessage(msg, 3000)
            return
        answer = QInputDialog.getMultiLineText(self, "Enter commit message", "Message:")
        comment = answer[0]
        if not comment:  # Cancel button clicked
            msg = "Commit message missing."
            self.ui.statusbar.showMessage(msg, 3000)
            return
        try:
            self.commit.comment = comment
            self.commit.date = datetime.now(timezone.utc)
            for i in reversed(range(len(self.transactions))):
                self.session.commit()
                del self.transactions[i]
            self.session.commit()  # also commit main transaction
        except DBAPIError as e:
            msg = "Error while trying to commit changes: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.commit.comment = None
            self.commit.date = None
            return
        msg = "All changes commited successfully."
        self.ui.statusbar.showMessage(msg, 5000)
        self.new_commit()

    @Slot(name="rollback_session")
    def rollback_session(self):
        if not self.session:
            return
        try:
            for i in reversed(range(len(self.transactions))):
                self.session.rollback()
                del self.transactions[i]
            self.session.rollback()  # also rollback main transaction
        except DBAPIError:
            msg = "Error while trying to rollback changes."
            self.ui.statusbar.showMessage(msg, 3000)
            return
        self.new_commit()
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_models()
        msg = "All changes (since last commit) rolled back successfully."
        self.ui.statusbar.showMessage(msg, 3000)
        # clear filters
        self.object_parameter_value_proxy.clear_filter()
        self.relationship_parameter_value_proxy.clear_filter()

    def create_base_and_reflect_tables(self):
        """Create base and reflect tables."""
        def _gen_relationship(base, direction, return_fn, attrname, local_cls, referred_cls, **kw):
            if direction is interfaces.ONETOMANY:
                kw['cascade'] = 'all, delete-orphan'
                kw['passive_deletes'] = True
            return generate_relationship(base, direction, return_fn, attrname, local_cls, referred_cls, **kw)

        self.Base = automap_base()
        self.Base.prepare(self.engine, reflect=True, generate_relationship=_gen_relationship)
        try:
            self.ObjectClass = self.Base.classes.object_class
            self.Object = self.Base.classes.object
            self.RelationshipClass = self.Base.classes.relationship_class
            self.Relationship = self.Base.classes.relationship
            self.Parameter = self.Base.classes.parameter
            self.ParameterValue = self.Base.classes.parameter_value
            self.Commit = self.Base.classes.commit
            return True
        except AttributeError as e:
            self._parent.msg_error.emit("Unable to parse database in the Spine format. "
                                        " Table <b>{}</b> is missing.".format(e))
            return False

    def create_session(self):
        """Create session."""
        self.session = Session(self.engine)
        self.new_commit()
        self.transactions = list()

    def new_commit(self):
        """Add row to commit table"""
        comment = 'In progress...'
        user = self.username
        date = datetime.now(timezone.utc)
        self.commit = self.Commit(comment=comment, date=date, user=user)
        try:
            self.session.add(self.commit)
            self.session.flush()
        except DBAPIError as e:
            msg = "Could not insert new commit item: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()

    def relationship_class_query(self, object_class_id):
        """Return relationship classes involving a given object class."""
        as_parent = self.session.query(
            self.RelationshipClass.id,
            self.RelationshipClass.name,
            self.RelationshipClass.child_object_class_id,
            self.RelationshipClass.parent_object_class_id
        ).filter_by(parent_object_class_id=object_class_id)
        as_child = self.session.query(
            self.RelationshipClass.id,
            self.RelationshipClass.name,
            self.RelationshipClass.parent_object_class_id,
            self.RelationshipClass.child_object_class_id
        ).filter(self.RelationshipClass.parent_object_class_id != object_class_id).\
        filter_by(
            parent_relationship_class_id=None,
            child_object_class_id=object_class_id
        )
        return {'as_parent': as_parent, 'as_child': as_child}

    def init_object_tree_model(self):
        """Initialize object tree model from source database."""
        self.object_tree_model.clear()
        db_name = self.database
        # create root item
        root_item = QStandardItem(db_name)
        # get all object_classes
        for object_class in self.session.query(
                    self.ObjectClass.id,
                    self.ObjectClass.name,
                    self.ObjectClass.display_order,
                ).order_by(self.ObjectClass.display_order):
            # create object class item
            object_class_item = QStandardItem(object_class.name)
            object_class_item.setData('object_class', Qt.UserRole)
            object_class_item.setData(object_class._asdict(), Qt.UserRole+1)
            # get objects of this class
            object_query = self.session.query(
                self.Object.id,
                self.Object.class_id,
                self.Object.name
            ).filter_by(class_id=object_class.id)
            # get relationship classes involving the present class
            relationship_class_query = self.relationship_class_query(object_class.id)
            # recursively populate branches
            for object_ in object_query:
                # create object item
                object_item = QStandardItem(object_.name)
                object_item.setData('object', Qt.UserRole)
                object_item.setData(object_._asdict(), Qt.UserRole+1)
                for relationship_class in relationship_class_query['as_parent']:
                    # create relationship class item
                    relationship_class_item = self.visit_relationship_class(
                        relationship_class,
                        object_._asdict(),
                        role='parent'
                    )
                    relationship_class_item.setData('relationship_class', Qt.UserRole)
                    object_item.appendRow(relationship_class_item)
                for relationship_class in relationship_class_query['as_child']:
                    # create relationship class item
                    relationship_class_item = self.visit_relationship_class(
                        relationship_class,
                        object_._asdict(),
                        role='child'
                    )
                    relationship_class_item.setData('relationship_class', Qt.UserRole)
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
        """Recursive function to create branches for relationships of relationships.

        Args:
            relationship_class (KeyedTuple or dict): relationship class to explore
            object_ (dict): parent object as dict
        """
        # create relationship class item
        relationship_class_item = QStandardItem(relationship_class.name)
        relationship_class_item.setData(relationship_class._asdict(), Qt.UserRole+1)
        # get relationship classes having this relationship class as 'parent'
        # (in our current convention, relationship classes are never the 'child'
        # in other relationship classes --but this may change)
        new_relationship_class_query = self.session.query(
            self.RelationshipClass.id,
            self.RelationshipClass.name,
            self.RelationshipClass.child_object_class_id,
            self.RelationshipClass.parent_relationship_class_id
        ).filter_by(parent_relationship_class_id=relationship_class.id)
        if 'relationship_id' not in object_:
            # the parent object is a 'first-class' object. In the tree, this
            # object is located directly beneath an object class
            if role == 'parent':
                # get new child objects in new relationship class
                # also save the relationship id for further tasks
                new_object_query = self.session.query(
                        self.Object.id,
                        self.Object.class_id,
                        self.Object.name,
                        self.Relationship.id.label('relationship_id')
                    ).filter(self.Object.id == self.Relationship.child_object_id).\
                    filter(self.Relationship.class_id == relationship_class.id).\
                    filter(self.Relationship.parent_object_id == object_['id'])
            elif role == 'child':
                # get new child objects in new relationship class
                new_object_query = self.session.query(
                        self.Object.id,
                        self.Object.class_id,
                        self.Object.name,
                        self.Relationship.id.label('relationship_id')
                    ).filter(self.Object.id == self.Relationship.parent_object_id).\
                    filter(self.Relationship.class_id == relationship_class.id).\
                    filter(self.Relationship.child_object_id == object_['id'])
        else:
            # the parent object is itself a 'related' object in other relationship
            # get new child objects in new relationship class
            new_object_query = self.session.query(
                self.Object.id,
                self.Object.class_id,
                self.Object.name,
                self.Relationship.id.label('relationship_id')
            ).filter(self.Object.id == self.Relationship.child_object_id).\
            filter(self.Relationship.class_id == relationship_class.id).\
            filter(self.Relationship.parent_relationship_id == object_['relationship_id'])
        # recursively populate branches
        for new_object in new_object_query:
            # create child object item
            new_object_item = QStandardItem(new_object.name)
            new_object_item.setData('related_object', Qt.UserRole)
            new_object_item.setData(new_object._asdict(), Qt.UserRole+1)
            for new_relationship_class in new_relationship_class_query:
                # create next relationship class item
                new_relationship_class_item = self.visit_relationship_class(
                    new_relationship_class,
                    new_object._asdict()
                )
                new_relationship_class_item.setData('meta_relationship_class', Qt.UserRole)
                new_object_item.appendRow(new_relationship_class_item)
            relationship_class_item.appendRow(new_object_item)
        return relationship_class_item

    def init_parameter_value_models(self):
        """Initialize parameter value models from source database."""
        # get all parameters
        parameter_value_subquery = self.session.query(
            self.Parameter.name.label('parameter_name'),
            self.ParameterValue.id.label('parameter_value_id'),
            self.ParameterValue.relationship_id,
            self.ParameterValue.object_id,
            self.ParameterValue.index,
            self.ParameterValue.value,
            self.ParameterValue.json,
            self.ParameterValue.expression,
            self.ParameterValue.time_pattern,
            self.ParameterValue.time_series_id,
            self.ParameterValue.stochastic_model_id
        ).filter(self.Parameter.id == self.ParameterValue.parameter_id).subquery()

        # just add the object class_id and name (this below is effectively a join)
        object_parameter_value_list = self.session.query(
            self.Object.class_id.label('object_class_id'),
            self.ObjectClass.name.label('object_class_name'),
            parameter_value_subquery.c.object_id,
            self.Object.name.label('object_name'),
            parameter_value_subquery.c.parameter_value_id,
            parameter_value_subquery.c.parameter_name,
            parameter_value_subquery.c.index,
            parameter_value_subquery.c.value,
            parameter_value_subquery.c.json,
            parameter_value_subquery.c.expression,
            parameter_value_subquery.c.time_pattern,
            parameter_value_subquery.c.time_series_id,
            parameter_value_subquery.c.stochastic_model_id
        ).filter(self.Object.id == parameter_value_subquery.c.object_id).\
        filter(self.Object.class_id == self.ObjectClass.id)

        # Get header
        header = object_parameter_value_list.column_descriptions
        self.object_parameter_value_model.header = [column['name'] for column in header]

        # here add the relationship_class_id and name,
        # parent relationship id and name, parent and child object id and name
        # (again this is a join)
        parent_relationship = aliased(self.Relationship)
        parent_object = aliased(self.Object)
        child_object = aliased(self.Object)
        relationship_parameter_value_list = self.session.query(
            self.Relationship.class_id.label('relationship_class_id'),
            self.RelationshipClass.name.label('relationship_class_name'),
            self.Relationship.id.label('relationship_id'),
            self.Relationship.parent_relationship_id,
            self.Relationship.parent_object_id,
            self.Relationship.child_object_id,
            parent_relationship.name.label('parent_relationship_name'),
            parent_object.name.label('parent_object_name'),
            child_object.name.label('child_object_name'),
            parameter_value_subquery.c.parameter_value_id,
            parameter_value_subquery.c.parameter_name,
            parameter_value_subquery.c.index,
            parameter_value_subquery.c.value,
            parameter_value_subquery.c.json,
            parameter_value_subquery.c.expression,
            parameter_value_subquery.c.time_pattern,
            parameter_value_subquery.c.time_series_id,
            parameter_value_subquery.c.stochastic_model_id
        # don't bring relationships with no parameters
        # ).outerjoin(parameter_value_subquery, self.Relationship.id == parameter_value_subquery.c.relationship_id).\
        ).filter(self.Relationship.id == parameter_value_subquery.c.relationship_id).\
        filter(self.Relationship.class_id == self.RelationshipClass.id).\
        outerjoin(parent_relationship, parent_relationship.id == self.Relationship.parent_relationship_id).\
        outerjoin(parent_object, parent_object.id == self.Relationship.parent_object_id).\
        filter(child_object.id == self.Relationship.child_object_id)

        # Get header
        header = relationship_parameter_value_list.column_descriptions
        self.relationship_parameter_value_model.header = [column['name'] for column in header]

        object_parameter_value = [list(row._asdict().values()) for row in object_parameter_value_list]
        self.object_parameter_value_model.reset_model(object_parameter_value)
        self.object_parameter_value_proxy.setSourceModel(self.object_parameter_value_model)

        relationship_parameter_value = [list(row._asdict().values()) for row in relationship_parameter_value_list]
        self.relationship_parameter_value_model.reset_model(relationship_parameter_value)
        self.relationship_parameter_value_proxy.setSourceModel(self.relationship_parameter_value_model)

    def init_parameter_models(self):
        """Initialize parameter (definition) models from source database."""
        # get all parameters, along with object class id and name (this below is effectively a join)
        object_parameter_list = self.session.query(
            self.ObjectClass.id.label('object_class_id'),
            self.ObjectClass.name.label('object_class_name'),
            self.Parameter.id.label('parameter_id'),
            self.Parameter.name.label('parameter_name'),
            self.Parameter.can_have_time_series,
            self.Parameter.can_have_time_pattern,
            self.Parameter.can_be_stochastic,
            self.Parameter.default_value,
            self.Parameter.is_mandatory,
            self.Parameter.precision,
            self.Parameter.minimum_value,
            self.Parameter.maximum_value
        ).filter(self.ObjectClass.id == self.Parameter.object_class_id).\
        order_by(self.Parameter.id)

        # Get header
        header = object_parameter_list.column_descriptions
        self.object_parameter_model.header = [column['name'] for column in header]

        relationship_parameter_list = self.session.query(
            self.RelationshipClass.id.label('relationship_class_id'),
            self.RelationshipClass.name.label('relationship_class_name'),
            self.Parameter.id.label('parameter_id'),
            self.Parameter.name.label('parameter_name'),
            self.Parameter.can_have_time_series,
            self.Parameter.can_have_time_pattern,
            self.Parameter.can_be_stochastic,
            self.Parameter.default_value,
            self.Parameter.is_mandatory,
            self.Parameter.precision,
            self.Parameter.minimum_value,
            self.Parameter.maximum_value
        ).filter(self.RelationshipClass.id == self.Parameter.relationship_class_id).\
        order_by(self.Parameter.id)

        # Get header
        header = relationship_parameter_list.column_descriptions
        self.relationship_parameter_model.header = [column['name'] for column in header]

        if object_parameter_list.all():
            object_parameter = [list(row._asdict().values()) for row in object_parameter_list]
            self.object_parameter_model.reset_model(object_parameter)
        self.object_parameter_proxy.setSourceModel(self.object_parameter_model)

        if relationship_parameter_list.all():
            relationship_parameter = [list(row._asdict().values()) for row in relationship_parameter_list]
            self.relationship_parameter_model.reset_model(relationship_parameter)
        self.relationship_parameter_proxy.setSourceModel(self.relationship_parameter_model)

    def init_parameter_value_views(self):
        self.init_object_parameter_value_view()
        self.init_relationship_parameter_value_view()

    def init_object_parameter_value_view(self):
        """Init the object parameter table view.
        """
        header = self.object_parameter_value_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_object_parameter_value.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_value.verticalHeader().\
            setDefaultSectionSize(self.default_font_height)
        # set model
        self.ui.tableView_object_parameter_value.setModel(self.object_parameter_value_proxy)
        # hide id columns
        self.ui.tableView_object_parameter_value.hideColumn(header.index("object_class_id"))
        self.ui.tableView_object_parameter_value.hideColumn(header.index("object_id"))
        self.ui.tableView_object_parameter_value.hideColumn(header.index("parameter_value_id"))
        # create line edit delegate and connect signals
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_parameter_value)
        self.ui.tableView_object_parameter_value.setItemDelegate(lineedit_delegate)
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()

    def init_relationship_parameter_value_view(self):
        """Init the relationship parameter table view.
        """
        header = self.relationship_parameter_value_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_relationship_parameter_value.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_value.verticalHeader().\
            setDefaultSectionSize(self.default_font_height)
        # set model
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_proxy)
        # hide id columns
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("relationship_class_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("parent_relationship_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("parent_object_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("child_object_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("relationship_id"))
        self.ui.tableView_relationship_parameter_value.hideColumn(header.index("parameter_value_id"))
        # create line edit delegate and connect signals
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_parameter_value)
        self.ui.tableView_relationship_parameter_value.setItemDelegate(lineedit_delegate)
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_parameter_views(self):
        self.init_object_parameter_view()
        self.init_relationship_parameter_view()

    def init_object_parameter_view(self):
        """Init the object parameter table view.
        """
        header = self.object_parameter_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_object_parameter.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter.verticalHeader().\
            setDefaultSectionSize(self.default_font_height)
        # set model
        self.ui.tableView_object_parameter.setModel(self.object_parameter_proxy)
        # hide id columns
        self.ui.tableView_object_parameter.hideColumn(header.index("object_class_id"))
        self.ui.tableView_object_parameter.hideColumn(header.index("parameter_id"))
        # create line edit delegate and connect signals
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_parameter)
        self.ui.tableView_object_parameter.setItemDelegate(lineedit_delegate)
        self.ui.tableView_object_parameter.resizeColumnsToContents()

    def init_relationship_parameter_view(self):
        """Init the object parameter table view.
        """
        header = self.relationship_parameter_model.header
        if not header:
            return
        # set column resize mode
        self.ui.tableView_relationship_parameter.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter.verticalHeader().\
            setDefaultSectionSize(self.default_font_height)
        # set model
        self.ui.tableView_relationship_parameter.setModel(self.relationship_parameter_proxy)
        # hide id columns
        self.ui.tableView_relationship_parameter.hideColumn(header.index("relationship_class_id"))
        # self.ui.tableView_relationship_parameter.hideColumn(header.index("parent_relationship_class_id"))
        # self.ui.tableView_relationship_parameter.hideColumn(header.index("parent_object_class_id"))
        # self.ui.tableView_relationship_parameter.hideColumn(header.index("child_object_class_id"))
        self.ui.tableView_relationship_parameter.hideColumn(header.index("parameter_id"))
        # create line edit delegate and connect signals
        lineedit_delegate = LineEditDelegate(self)
        lineedit_delegate.closeEditor.connect(self.update_parameter)
        self.ui.tableView_relationship_parameter.setItemDelegate(lineedit_delegate)
        self.ui.tableView_relationship_parameter.resizeColumnsToContents()

    @Slot("QModelIndex", name="expand_at_top_level")
    def expand_at_top_level(self, index):
        """Expand object at the top level"""
        # logging.debug("expand_at_top_level leaf")
        if not index.isValid():
            return # just to be safe
        clicked_type = index.data(Qt.UserRole)
        if not clicked_type:  # root item
            return
        if not clicked_type.endswith('object'):
            return
        clicked_item = index.model().itemFromIndex(index)
        if clicked_item.hasChildren():
            return
        self.expand_at_top_level_(index)

    def expand_at_top_level_(self, index):
        """Expand object at the top level (suite)"""
        clicked_object = index.data(Qt.UserRole+1)
        root_item = index.model().invisibleRootItem().child(0)
        found_object_class_item = None
        for i in range(root_item.rowCount()):
            object_class_item = root_item.child(i)
            object_class = object_class_item.data(Qt.UserRole+1)
            if object_class['id'] == clicked_object['class_id']:
                found_object_class_item = object_class_item
                break
        if not found_object_class_item:
            return
        for j in range(found_object_class_item.rowCount()):
            object_item = found_object_class_item.child(j)
            object_ = object_item.data(Qt.UserRole+1)
            if object_['id'] == clicked_object['id']:
                object_index = index.model().indexFromItem(object_item)
                self.ui.treeView_object.setCurrentIndex(object_index)
                self.ui.treeView_object.scrollTo(object_index)
                self.ui.treeView_object.expand(object_index)
                return

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_value_models(self, current, previous):
        """Populate tableViews whenever an object item is selected in the treeView"""
        # TODO: try to make it more sparse
        # logging.debug("filter_parameter_value_models")
        self.object_parameter_value_proxy.clear_filter()
        self.relationship_parameter_value_proxy.clear_filter()
        clicked_type = current.data(Qt.UserRole)
        # filter rows and bold name
        if clicked_type == 'object_class': # show all objects of this class
            object_class_id = current.data(Qt.UserRole+1)['id']
            self.object_parameter_value_proxy.object_class_id_filter = object_class_id
        elif clicked_type == 'object': # show only this object
            object_id = current.data(Qt.UserRole+1)['id']
            object_name = current.data(Qt.UserRole+1)['name']
            self.object_parameter_value_proxy.object_id_filter = object_id
            self.relationship_parameter_value_proxy.object_id_filter = object_id
            self.relationship_parameter_value_proxy.bold_name = object_name
        elif clicked_type == 'relationship_class':
            # show all related objects to this parent object, through this relationship class
            parent_object_id = current.parent().data(Qt.UserRole+1)['id']
            relationship_class_id = current.data(Qt.UserRole+1)['id']
            relationship_class_name = current.data(Qt.UserRole+1)['name']
            self.relationship_parameter_value_proxy.object_id_filter = parent_object_id
            self.relationship_parameter_value_proxy.relationship_class_id_filter = relationship_class_id
            self.relationship_parameter_value_proxy.bold_name = relationship_class_name
        elif clicked_type == 'related_object':
            # show only this object and this relationship
            object_id = current.data(Qt.UserRole+1)['id']
            object_name = current.data(Qt.UserRole+1)['name']
            relationship_id = current.data(Qt.UserRole+1)['relationship_id']
            self.object_parameter_value_proxy.object_id_filter = object_id
            self.relationship_parameter_value_proxy.relationship_id_filter = relationship_id
            self.relationship_parameter_value_proxy.bold_name = object_name
        elif clicked_type == 'meta_relationship_class':
            # show all related objects to this parent relationship, through this meta-relationship class
            parent_relationship_id = current.parent().data(Qt.UserRole+1)['relationship_id']
            relationship_class_id = current.data(Qt.UserRole+1)['id']
            relationship_class_name = current.data(Qt.UserRole+1)['name']
            self.relationship_parameter_value_proxy.parent_relationship_id_filter = parent_relationship_id
            self.relationship_parameter_value_proxy.relationship_class_id_filter = relationship_class_id
            self.relationship_parameter_value_proxy.bold_name = relationship_class_name
        # filter columns in relationship parameter value model
        header = self.relationship_parameter_value_model.header
        if header:
            if clicked_type == 'object':
                self.relationship_parameter_value_proxy.hide_column = header.index("parent_relationship_name")
            elif clicked_type == 'relationship_class':
                self.relationship_parameter_value_proxy.hide_column = header.index("parent_relationship_name")
            elif clicked_type == 'related_object':
                relationship_class_type = current.parent().data(Qt.UserRole)
                if relationship_class_type == 'meta_relationship_class': # hide parent_object_name
                    self.relationship_parameter_value_proxy.hide_column = header.index("parent_object_name")
                elif relationship_class_type == 'relationship_class': # hide parent_relationship_name
                    self.relationship_parameter_value_proxy.hide_column = header.index("parent_relationship_name")
            elif clicked_type == 'meta_relationship_class':
                self.relationship_parameter_value_proxy.hide_column = header.index("parent_object_name")
        # trick to trigger filtering
        self.object_parameter_value_proxy.setFilterRegExp("")
        self.relationship_parameter_value_proxy.setFilterRegExp("")

    @Slot("QModelIndex", "QModelIndex", name="filter_parameter_models")
    def filter_parameter_models(self, current, previous):
        """Populate tableViews whenever an object item is selected in the treeView"""
        # logging.debug("filter_parameter_models")
        self.object_parameter_proxy.clear_filter()
        self.relationship_parameter_proxy.clear_filter()
        clicked_type = current.data(Qt.UserRole)
        # filter rows
        if clicked_type == 'object_class': # show only this class
            object_class_id = current.data(Qt.UserRole+1)['id']
            self.object_parameter_proxy.object_class_id_filter = object_class_id
        elif clicked_type == 'object': # show only this object's class
            object_class_id = current.data(Qt.UserRole+1)['class_id']
            self.object_parameter_proxy.object_class_id_filter = object_class_id
        elif clicked_type and clicked_type.endswith('relationship_class'):
            relationship_class_id = current.data(Qt.UserRole+1)['id']
            self.relationship_parameter_proxy.relationship_class_id_filter = relationship_class_id
        elif clicked_type == 'related_object':
            relationship_class_id = current.parent().data(Qt.UserRole+1)['id']
            self.relationship_parameter_proxy.relationship_class_id_filter = relationship_class_id
        # trick to trigger filtering
        self.object_parameter_proxy.setFilterRegExp("")
        self.relationship_parameter_proxy.setFilterRegExp("")
        # resize columns
        self.ui.tableView_object_parameter.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter.resizeColumnsToContents()

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
        if option == "Add object classes":
            self.add_object_classes()
        elif option == "Add objects":
            self.call_add_objects(index)
        elif option == "Add relationship classes":
            self.call_add_relationship_classes(index)
        elif option == "Add relationships":
            self.call_add_relationships(index)
        elif option == "Expand at top level":
            self.expand_at_top_level_(index)
        elif option.startswith("Rename"):
            self.rename_item(index)
        elif option.startswith("Remove"):
            self.remove_item(index)
        elif option == "Add parameter":
            self.call_add_parameter(index)
        elif option == "Add parameter value":
            self.call_add_parameter_value(index)
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    def call_add_objects(self, index):
        class_name = index.data(Qt.UserRole+1)['name']
        self.add_objects(class_name=class_name)

    def call_add_relationship_classes(self, index):
        parent_class_name = index.data(Qt.UserRole+1)['name']
        self.add_relationship_classes(parent_class_name=parent_class_name)

    def call_add_relationships(self, index):
        relationship_class = index.data(Qt.UserRole+1)
        class_name = relationship_class['name']
        parent_name = None
        child_name = None
        top_object_type = index.parent().data(Qt.UserRole)
        top_object = index.parent().data(Qt.UserRole+1)
        if top_object_type == 'object':
            top_object_class_id = top_object['class_id']
            if top_object_class_id == relationship_class['parent_object_class_id']:
                parent_name = top_object['name']
            elif top_object_class_id == relationship_class['child_object_class_id']:
                child_name = top_object['name']
        elif top_object_type == 'related_object':
            parent_relationship_id = top_object['relationship_id']
            parent_name = self.session.query(self.Relationship.name).\
                filter_by(id=parent_relationship_id).one().name
        self.add_relationships(class_name=class_name, parent_name=parent_name, child_name=child_name)

    def call_add_parameter(self, tree_index):
        class_type = tree_index.data(Qt.UserRole)
        class_id = tree_index.data(Qt.UserRole+1)['id']
        if class_type == 'object_class':
            self.add_parameter(object_class_id=class_id)
        elif class_type.endswith('relationship_class'):
            self.add_parameter(relationship_class_id=class_id)

    def call_add_parameter_value(self, tree_index):
        item_type = tree_index.data(Qt.UserRole)
        item_data = tree_index.data(Qt.UserRole+1)
        if item_type == 'object':
            self.add_parameter_value(object_id=item_data['id'])
        elif item_type == 'related_object':
            self.add_parameter_value(relationship_id=item_data['relationship_id'])

    @Slot(name="add_object_classes")
    def add_object_classes(self):
        """Insert new object classes."""
        object_class_list = self.get_new_object_class_list()
        if not object_class_list:
            return
        for object_class in object_class_list:
            if self.add_object_class_to_db(object_class):
                self.add_object_class_to_model(object_class)

    def get_new_object_class_list(self):
        """Query the user's preferences for creating new object classes.

        Returns:
            object_class_list (list): List of instances to try and add
        """
        object_class_list = list()
        object_class_query = self.session.query(self.ObjectClass).\
            order_by(self.ObjectClass.display_order)
        dialog = AddObjectClassesDialog(self, object_class_query)
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            for object_class_args in dialog.object_class_args_list:
                object_class = self.ObjectClass(commit_id=self.commit.id, **object_class_args)
                object_class_list.append(object_class)
        return object_class_list

    def add_object_class_to_db(self, object_class):
        """Add object class to database.

        Args:
            object_class (self.Object_class)

        Returns:
            Boolean value depending on the result of the operation
        """
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(object_class)
            self.session.flush()
            return True
        except DBAPIError as e:
            msg = "Could not insert new object class '{}': {}".format(object_class.name, e.orig.args)
            msg_box = QMessageBox()
            msg_box.setText(msg)
            msg_box.exec_()
            # self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return False

    def add_object_class_to_model(self, object_class):
        """Add object class item at given row to the object tree model.

        Args:
            object_class (self.Object_class)
        """
        object_class_item = QStandardItem(object_class.name)
        object_class_item.setData('object_class', Qt.UserRole)
        object_class_item.setData(object_class.__dict__, Qt.UserRole+1)
        root_item = self.object_tree_model.invisibleRootItem().child(0)
        row = root_item.rowCount()
        for i in range(root_item.rowCount()):
            visited_object_class_item = root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole+1)
            if visited_object_class['display_order'] > object_class.display_order:
                row = i
                break
        root_item.insertRow(row, QStandardItem())
        root_item.setChild(row, 0, object_class_item)
        # scroll to newly inserted item in treeview
        object_class_index = self.object_tree_model.indexFromItem(object_class_item)
        self.ui.treeView_object.setCurrentIndex(object_class_index)
        self.ui.treeView_object.scrollTo(object_class_index)

    @Slot(name="add_objects")
    def add_objects(self, class_name=None):
        """Insert new objects."""
        object_list = self.get_new_object_list(class_name)
        if not object_list:
            return
        for object_ in object_list:
            if self.add_object_to_db(object_):
                self.add_object_to_model(object_)

    def get_new_object_list(self, class_name=None):
        """Query the user's preferences for creating new objects.

        Returns:
            object_list (list): List of instances to try and add
        """
        object_list = list()
        object_class_query = self.session.query(self.ObjectClass).\
            order_by(self.ObjectClass.display_order)
        dialog = AddObjectsDialog(self, object_class_query, class_name)
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            for object_args in dialog.object_args_list:
                object_ = self.Object(commit_id=self.commit.id, **object_args)
                object_list.append(object_)
        return object_list

    def add_object_to_db(self, object_):
        """Add object to database.

        Args:
            object_ (self.Object)

        Returns:
            Boolean value depending on the result of the operation
        """
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(object_)
            self.session.flush() # to get object id
            return True
        except DBAPIError as e:
            msg = "Could not insert new object '{}': {}".format(object_.name, e.orig.args)
            # self.ui.statusbar.showMessage(msg, 5000)
            msg_box = QMessageBox()
            msg_box.setText(msg)
            msg_box.exec_()
            self.session.rollback()
            return False

    def add_object_to_model(self, object_):
        """Add object item to the object tree model.

        Args:
            object_ (self.Object)
        """
        object_item = QStandardItem(object_.name)
        object_item.setData('object', Qt.UserRole)
        object_item.setData(object_.__dict__, Qt.UserRole+1)
        # get relationship classes involving the present object class
        relationship_class_query = self.relationship_class_query(object_.class_id)
        # create and append relationship class items
        for relationship_class in relationship_class_query['as_parent']:
            # no need to visit the relationship class here,
            # since this object does not have any relationships yet
            relationship_class_item = QStandardItem(relationship_class.name)
            relationship_class_item.setData('relationship_class', Qt.UserRole)
            relationship_class_item.setData(relationship_class._asdict(), Qt.UserRole+1)
            object_item.appendRow(relationship_class_item)
        for relationship_class in relationship_class_query['as_child']:
            # no need to visit the relationship class here,
            # since this object does not have any relationships yet
            relationship_class_item = QStandardItem(relationship_class.name)
            relationship_class_item.setData('relationship_class', Qt.UserRole)
            relationship_class_item.setData(relationship_class._asdict(), Qt.UserRole+1)
            object_item.appendRow(relationship_class_item)
        # find object class item among the children of the root
        root_item = self.object_tree_model.invisibleRootItem().child(0)
        object_class_item = None
        for i in range(root_item.rowCount()):
            visited_object_class_item = root_item.child(i)
            visited_object_class = visited_object_class_item.data(Qt.UserRole+1)
            if visited_object_class['id'] == object_.class_id:
                object_class_item = visited_object_class_item
                break
        if not object_class_item:
            self.ui.statusbar.showMessage("Object class item not found in model.")
            return
        object_class_item.appendRow(object_item)
        # scroll to newly inserted item in treeview
        object_index = self.object_tree_model.indexFromItem(object_item)
        self.ui.treeView_object.setCurrentIndex(object_index)
        self.ui.treeView_object.scrollTo(object_index)

    @Slot(name="add_relationship_classes")
    def add_relationship_classes(self, parent_class_name=None):
        """Insert new relationship class."""
        relationship_class_list = self.get_new_relationship_class_list(parent_class_name=parent_class_name)
        if not relationship_class_list:
            return
        for relationship_class in relationship_class_list:
            if self.add_relationship_class_to_db(relationship_class):
                self.add_relationship_class_to_model(relationship_class)

    def get_new_relationship_class_list(self, parent_class_name=None):
        """Query the user's preferences for creating new relationship classes.

        Returns:
            relationship_class_list (list): List of instances to try and add.
        """
        relationship_class_list = list()
        object_class_query = self.session.query(self.ObjectClass).\
            order_by(self.ObjectClass.display_order)
        relationship_class_query = self.session.query(self.RelationshipClass)
        dialog = AddRelationshipClassesDialog(
            self,
            object_class_query,
            relationship_class_query,
            parent_class_name=parent_class_name
        )
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            for relationship_class_args in dialog.relationship_class_args_list:
                relationship_class = self.RelationshipClass(commit_id=self.commit.id, **relationship_class_args)
                relationship_class_list.append(relationship_class)
        return relationship_class_list

    def add_relationship_class_to_db(self, relationship_class):
        """Add relationship class to database.

        Args:
            relationship_class (self.RelationshipClass): the relationship class to add

        Returns:
            Boolean value depending on the result of the operation
        """
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(relationship_class)
            self.session.flush() # to get the relationship class id
            return True
        except DBAPIError as e:
            msg = "Could not insert new relationship class '{}': {}".format(relationship_class.name, e.orig.args)
            # self.ui.statusbar.showMessage(msg, 5000)
            msg_box = QMessageBox()
            msg_box.setText(msg)
            msg_box.exec_()
            self.session.rollback()
            return False

    def add_relationship_class_to_model(self, relationship_class):
        """Add relationship class item to object tree model.

        Args:
            relationship_class (self.RelationshipClass): the relationship class to add
        """

        def visit_and_add_relationship_class(item):
            """Visit item, add relationship class if necessary and visit children."""
            # Visit children
            for i in range(item.rowCount()):
                visit_and_add_relationship_class(item.child(i))
            # Visit item
            ent_type = item.data(Qt.UserRole)
            # Skip root item
            if not ent_type:
                return
            if not ent_type.endswith('object'):
                return
            parent_class = item.parent().data(Qt.UserRole+1)
            if ent_type == 'object':
                cond = relationship_class.parent_object_class_id == parent_class['id']
            elif ent_type == 'related_object':
                cond = relationship_class.parent_relationship_class_id == parent_class['id']
            if cond:
                relationship_class_item = QStandardItem(relationship_class.name)
                relationship_class_item.setData(relationship_class_type, Qt.UserRole)
                relationship_class_item.setData(relationship_class.__dict__, Qt.UserRole+1)
                item.appendRow(relationship_class_item)
            # Don't add the mirror of a meta relationship class
            if relationship_class_type == 'meta_relationship_class':
                return
            # Don't add duplicate relationship class if parent and child are the same
            if relationship_class.parent_object_class_id == relationship_class.child_object_class_id:
                return
            # Add mirror relationship class
            if parent_class['id'] == relationship_class.child_object_class_id:
                relationship_class_item = QStandardItem(relationship_class.name)
                relationship_class_item.setData('relationship_class', Qt.UserRole)
                relationship_class_item.setData(relationship_class.__dict__, Qt.UserRole+1)
                item.appendRow(relationship_class_item)

        if relationship_class.parent_object_class_id is not None:
            relationship_class_type = 'relationship_class'
        elif relationship_class.parent_relationship_class_id is not None:
            relationship_class_type = 'meta_relationship_class'
        root_item = self.object_tree_model.invisibleRootItem().child(0)
        visit_and_add_relationship_class(root_item)

    @Slot(name="add_relationships")
    def add_relationships(self, class_name=None, parent_name=None, child_name=None):
        """Insert new relationship."""
        relationship_list = self.get_new_relationship_list(
            class_name=class_name,
            parent_name=parent_name,
            child_name=child_name
        )
        if not relationship_list:
            return
        for relationship in relationship_list:
            if self.add_relationship_to_db(relationship):
                self.add_relationship_to_model(relationship)

    def get_new_relationship_list(self, class_name=None, parent_name=None, child_name=None):
        """Query the user's preferences for creating new relationships.

        Returns:
            relationship_list (list): List of instances to try and add.
        """
        relationship_list = list()
        relationship_class_query = self.session.query(self.RelationshipClass)
        object_query = self.session.query(self.Object)
        relationship_query = self.session.query(self.Relationship)
        dialog = AddRelationshipsDialog(
            self,
            relationship_class_query,
            object_query,
            relationship_query,
            class_name=class_name,
            parent_name=parent_name,
            child_name=child_name
        )
        answer = dialog.exec_()
        if answer == QDialog.Accepted:
            for relationship_args in dialog.relationship_args_list:
                relationship = self.Relationship(commit_id=self.commit.id, **relationship_args)
                relationship_list.append(relationship)
        return relationship_list

    def add_relationship_to_db(self, relationship):
        """Add relationship to database.

        Args:
            relationship (self.Relationship): the relationship to add

        Returns:
            Boolean value depending on the result of the operation
        """
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(relationship)
            self.session.flush() # to get the relationship class id
            return True
        except DBAPIError as e:
            msg = "Could not insert new relationship '{}': {}".format(relationship.name, e.orig.args)
            # self.ui.statusbar.showMessage(msg, 5000)
            msg_box = QMessageBox()
            msg_box.setText(msg)
            msg_box.exec_()
            self.session.rollback()
            return False

    def add_relationship_to_model(self, relationship):
        """Add relationship item to object tree model.

        Args:
            relationship (self.Relationship): the relationship to add
        """

        def visit_and_add_relationship(item):
            """Visit item, add relationship if necessary and visit children."""
            # Visit children
            for i in range(item.rowCount()):
                visit_and_add_relationship(item.child(i))
            # visit item
            entity_type = item.data(Qt.UserRole)
            if not entity_type: # root item
                return
            if not entity_type.endswith('relationship_class'):
                return
            relationship_class = item.data(Qt.UserRole+1)
            if not relationship_class['id'] == relationship.class_id:
                return
            top_object = item.parent().data(Qt.UserRole+1)
            if 'relationship_id' in top_object:
                cond = relationship.parent_relationship_id == top_object['relationship_id']
            else:
                cond = relationship.parent_object_id == top_object['id']
            if cond:
                # query object table to get new object directly as dict
                new_object = self.session.query(
                    self.Object.id,
                    self.Object.class_id,
                    self.Object.name
                ).filter_by(id=relationship.child_object_id).one_or_none()._asdict()
                # add parent relationship id
                new_object['relationship_id'] = relationship.id
                new_object_item = QStandardItem(new_object['name'])
                new_object_item.setData('related_object', Qt.UserRole)
                new_object_item.setData(new_object, Qt.UserRole+1)
                # get relationship classes having the present relationship class as parent
                new_relationship_class_query = self.session.query(
                    self.RelationshipClass.id,
                    self.RelationshipClass.name,
                    self.RelationshipClass.child_object_class_id,
                    self.RelationshipClass.parent_relationship_class_id
                ).filter_by(parent_relationship_class_id=relationship_class['id'])
                # create and append relationship class items
                for new_relationship_class in new_relationship_class_query:
                    # no need to visit the relationship class here,
                    # since this relationship does not have any relationships yet
                    new_relationship_class_item = QStandardItem(new_relationship_class.name)
                    new_relationship_class_item.setData(new_relationship_class._asdict(), Qt.UserRole+1)
                    new_relationship_class_item.setData('meta_relationship_class', Qt.UserRole)
                    new_object_item.appendRow(new_relationship_class_item)
                item.appendRow(new_object_item)
            if relationship_class_type == 'meta_relationship_class':
                return  # we are done
            if relationship.child_object_id == top_object['id']:
                # query object table to get new object directly as dict
                new_object = self.session.query(
                    self.Object.id,
                    self.Object.class_id,
                    self.Object.name
                ).filter_by(id=relationship.parent_object_id).one_or_none()._asdict()
                # add parent relationship id manually
                new_object['relationship_id'] = relationship.id
                new_object_item = QStandardItem(new_object['name'])
                new_object_item.setData('related_object', Qt.UserRole)
                new_object_item.setData(new_object, Qt.UserRole+1)
                # get relationship classes having the present relationship class as parent
                new_relationship_class_query = self.session.query(
                    self.RelationshipClass.id,
                    self.RelationshipClass.name,
                    self.RelationshipClass.child_object_class_id,
                    self.RelationshipClass.parent_relationship_class_id
                ).filter_by(parent_relationship_class_id=relationship_class['id'])
                # create and append relationship class items
                for new_relationship_class in new_relationship_class_query:
                    # no need to visit the relationship class here,
                    # since this relationship does not have any relationships yet
                    new_relationship_class_item = QStandardItem(new_relationship_class.name)
                    new_relationship_class_item.setData(new_relationship_class._asdict(), Qt.UserRole+1)
                    new_relationship_class_item.setData('relationship_class', Qt.UserRole)
                    new_object_item.appendRow(new_relationship_class_item)
                item.appendRow(new_object_item)

        if relationship.parent_object_id is not None:
            relationship_class_type = 'relationship_class'
        elif relationship.parent_relationship_id is not None:
            relationship_class_type = 'meta_relationship_class'
        root_item = self.object_tree_model.invisibleRootItem().child(0)
        visit_and_add_relationship(root_item)

    def rename_item(self, renamed_index):
        """Rename item in the database and treeview"""
        renamed_item = self.object_tree_model.itemFromIndex(renamed_index)
        name = renamed_item.text()
        answer = QInputDialog.getText(self, "Rename item", "Enter new name:",\
            QLineEdit.Normal, name)
        new_name = answer[0]
        if not new_name: # cancel clicked
            return
        if new_name == name: # nothing to do here
            return
        # Get renamed instance
        renamed_type = renamed_item.data(Qt.UserRole)
        renamed = renamed_item.data(Qt.UserRole+1)
        if renamed_type == 'object_class':
            renamed_instance = self.session.query(self.ObjectClass).filter_by(id=renamed['id']).one_or_none()
        elif renamed_type.endswith('object'):
            renamed_instance = self.session.query(self.Object).filter_by(id=renamed['id']).one_or_none()
        elif renamed_type.endswith('relationship_class'):
            renamed_instance = self.session.query(self.RelationshipClass).filter_by(id=renamed['id']).one_or_none()
        else:
            return # should never happen
        if not renamed_instance:
            return
        try:
            self.transactions.append(self.session.begin_nested())
            renamed_instance.name = new_name
            renamed_instance.commit_id = self.commit.id
            self.session.flush()
        except DBAPIError as e:
            msg = "Could not rename item: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return
        # manually rename all items in model
        items = self.object_tree_model.findItems(name, Qt.MatchRecursive)
        for found_item in items:
            found_type = found_item.data(Qt.UserRole)
            found = found_item.data(Qt.UserRole+1)
            # NOTE: Using 'in' below ensures related objects are renamed when renaming objects and viceversa
            # And same for relationship classes and 'meta-relationship' classes
            if (found_type in renamed_type or renamed_type in found_type)\
                    and found['id'] == renamed['id']:
                found['name'] = new_name
                found_item.setData(found, Qt.UserRole+1)
                found_item.setText(new_name)
        # refresh parameter models
        self.init_parameter_value_models()
        self.init_parameter_models()

    def remove_item(self, removed_index):
        """Remove item from the treeview"""
        removed_item = self.object_tree_model.itemFromIndex(removed_index)
        # find out which table
        removed_type = removed_item.data(Qt.UserRole)
        removed = removed_item.data(Qt.UserRole+1)
        # Get removed id
        if removed_type == 'related_object':
            removed_id = removed['relationship_id']
        else:
            removed_id = removed['id']
        # Get removed instance
        if removed_type == 'object_class':
            removed_instance = self.session.query(self.ObjectClass).filter_by(id=removed_id).one_or_none()
        elif removed_type == 'object':
            removed_instance = self.session.query(self.Object).filter_by(id=removed_id).one_or_none()
        elif removed_type.endswith('relationship_class'):
            removed_instance = self.session.query(self.RelationshipClass).filter_by(id=removed_id).one_or_none()
        elif removed_type == 'related_object':
            removed_instance = self.session.query(self.Relationship).filter_by(id=removed_id).one_or_none()
        else:
            return # should never happen
        if not removed_instance:
            msg = "Could not find {} named {}. This should not happen.".format(removed_type, removed['name'])
            self.ui.statusbar.showMessage(msg, 5000)
            return
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(removed_instance)
            self.session.flush()
        except DBAPIError as e:
            msg = "Could not remove item: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return
        # Manually remove items in model corresponding to the removed item
        def visit_and_remove(visited_item):
            """Visit item, remove it if necessary and visit children."""
            # Visit children in reverse order, so we don't mess up in case of removal
            for i in reversed(range(visited_item.rowCount())):
                visit_and_remove(visited_item.child(i))
            # Visit item
            visited_type = visited_item.data(Qt.UserRole)
            visited = visited_item.data(Qt.UserRole+1)
            # Skip root
            if not visited_type:
                return
            # Get visited id
            if visited_type == 'related_object':
                visited_id = visited['relationship_id']
            else:
                visited_id = visited['id']
            if visited_type == removed_type and visited_id == removed_id:
                visited_index = self.object_tree_model.indexFromItem(visited_item)
                self.object_tree_model.removeRows(visited_index.row(), 1, visited_index.parent())
                return
            # When removing an object class, also remove relationship classes that involve it
            if removed_type == 'object_class' and visited_type.endswith('relationship_class'):
                child_object_class_id = visited['child_object_class_id']
                if 'parent_object_class_id' in visited:
                    parent_object_class_id = visited['parent_object_class_id']
                else:
                    parent_object_class_id = None
                if removed_id in [child_object_class_id, parent_object_class_id]:
                    visited_index = self.object_tree_model.indexFromItem(visited_item)
                    self.object_tree_model.removeRows(visited_index.row(), 1, visited_index.parent())
                    return
            # When removing an object, also remove relationships that involve it
            if removed_type == 'object' and visited_type == 'related_object':
                if removed_id == visited['id']:
                    visited_index = self.object_tree_model.indexFromItem(visited_item)
                    self.object_tree_model.removeRows(visited_index.row(), 1, visited_index.parent())
                    return
        root_item = self.object_tree_model.invisibleRootItem().child(0)
        visit_and_remove(root_item)
        # refresh parameter models
        self.init_parameter_value_models()
        self.init_parameter_models()

    @Slot(name="add_parameter")
    def add_parameter(self, **kwargs):
        """Insert new parameter."""
        parameter = self.get_new_parameter(**kwargs)
        if not parameter:
            return
        if self.add_parameter_to_db(parameter):
            self.add_parameter_to_model(parameter)

    def get_new_parameter(self, **kwargs):
        """Query the user's preferences for creating a new parameter."""
        question = {}
        if 'name' not in kwargs:
            question.update({"name": "Type name here..."})
        if 'object_class_id' not in kwargs\
                and 'relationship_class_id' not in kwargs:
            class_name_list = ['Select class...']
            object_class_query = self.session.query(self.ObjectClass).\
                    order_by(self.ObjectClass.display_order)
            relationship_class_query = self.session.query(self.RelationshipClass)
            class_name_list.extend([item.name for item in object_class_query])
            class_name_list.extend([item.name for item in relationship_class_query])
            question.update({"class_name_list": class_name_list})
        dialog = CustomQDialog(self, "Add parameter", **question)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        if 'name' in dialog.answer:
            kwargs.update({'name': dialog.answer['name']})
        if 'class_name_list' in dialog.answer:
            ind = dialog.answer['class_name_list']['index'] - 1
            if ind < object_class_query.count():
                kwargs.update({'object_class_id': object_class_query[ind].id})
                # relationship_class_type = 'relationship_class'
            else:
                ind = ind - object_class_query.count()
                kwargs.update({'relationship_class_id': relationship_class_query[ind].id})
        return self.Parameter(commit_id=self.commit.id, **kwargs)

    def add_parameter_to_db(self, parameter):
        """Add parameter to database. Return boolean value depending on the
        result of the operation.

        Args:
            parameter (self.Parameter): the parameter to add
        """
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(parameter)
            self.session.flush() # to get the relationship class id
            return True
        except DBAPIError as e:
            msg = "Could not insert new parameter: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return False

    def add_parameter_to_model(self, parameter):
        """Add parameter item to the object or relationship parameter model.

        Args:
            parameter (self.Parameter)
        """
        self.init_parameter_models()
        # Scroll to concerned row in object parameter table
        if parameter.object_class_id:
            self.ui.tableView_object_parameter.resizeColumnsToContents()
            source_row = self.object_parameter_model.rowCount()-1
            source_column = self.object_parameter_model.header.index("parameter_name")
            source_index = self.object_parameter_model.index(source_row, source_column)
            proxy_index = self.object_parameter_proxy.mapFromSource(source_index)
            self.ui.tabWidget_object.setCurrentIndex(1)
            self.ui.tableView_object_parameter.setCurrentIndex(proxy_index)
            self.ui.tableView_object_parameter.scrollTo(proxy_index)
        # Scroll to concerned row in relationship parameter table
        elif parameter.relationship_class_id:
            self.ui.tableView_relationship_parameter.resizeColumnsToContents()
            source_row = self.relationship_parameter_model.rowCount()-1
            source_column = self.relationship_parameter_model.header.index("parameter_name")
            source_index = self.relationship_parameter_model.index(source_row, source_column)
            proxy_index = self.relationship_parameter_proxy.mapFromSource(source_index)
            self.ui.tabWidget_relationship.setCurrentIndex(1)
            self.ui.tableView_relationship_parameter.setCurrentIndex(proxy_index)
            self.ui.tableView_relationship_parameter.scrollTo(proxy_index)
        # Scroll to concerned object class in treeview if necessary
        if parameter.object_class_id:
            current_index = self.ui.treeView_object.currentIndex()
            current_type = current_index.data(Qt.UserRole)
            if current_type == 'object_class':
                current_id = current_index.data(Qt.UserRole+1)['id']
                if current_id == parameter.object_class_id:
                    return  # We're already in the right one
            # Search it and scroll to it
            for item in self.object_tree_model.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                item_type = item.data(Qt.UserRole)
                if not item_type: # root
                    continue
                item_id = item.data(Qt.UserRole+1)['id']
                if item_type == 'object_class' and item_id == parameter.object_class_id:
                    object_class_index = self.object_tree_model.indexFromItem(item)
                    self.ui.treeView_object.setCurrentIndex(object_class_index)
                    self.ui.treeView_object.scrollTo(object_class_index)
                    break
        # Scroll to concerned relationship class in treeview if necessary
        elif parameter.relationship_class_id:
            current_index = self.ui.treeView_object.currentIndex()
            current_type = current_index.data(Qt.UserRole)
            if current_type.endswith('relationship_class'):
                current_id = current_index.data(Qt.UserRole+1)['id']
                if current_id == parameter.relationship_class_id:
                    return  # We're already in the right one
            # Search the first one that matches and scroll to it
            for item in self.object_tree_model.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                item_type = item.data(Qt.UserRole)
                if not item_type: # root
                    continue
                item_id = item.data(Qt.UserRole+1)['id']
                if item_type.endswith('relationship_class') and item_id == parameter.relationship_class_id:
                    relationship_class_index = self.object_tree_model.indexFromItem(item)
                    self.ui.treeView_object.setCurrentIndex(relationship_class_index)
                    self.ui.treeView_object.scrollTo(relationship_class_index)
                    break

    def object_parameter_names(self, object_id):
        """Return unassigned parameter names for object

        Args:
            object_id (int): object id
        """
        object_class_id = self.session.query(self.Object.class_id).\
            filter_by(id=object_id).one().class_id
        parameter_name_query = self.session.query(self.Parameter.name).\
            filter_by(object_class_id=object_class_id).\
            filter( # filter out parameters already assigned
                ~self.Parameter.id.in_(
                    self.session.query(self.ParameterValue.parameter_id).\
                    filter_by(object_id=object_id)
                )
            )
        return [row.name for row in parameter_name_query]

    def relationship_parameter_names(self, relationship_id):
        """Return unassigned parameter names for relationship

        Args:
            relationship_id (int): relationship id
        """
        relationship_class_id = self.session.query(self.Relationship.class_id).\
            filter_by(id=relationship_id).one().class_id
        parameter_name_query = self.session.query(self.Parameter.name).\
            filter_by(relationship_class_id=relationship_class_id).\
            filter( # filter out parameters already assigned
                ~self.Parameter.id.in_(
                    self.session.query(self.ParameterValue.parameter_id).\
                    filter_by(relationship_id=relationship_id)
                )
            )
        return [row.name for row in parameter_name_query]

    @Slot(name="add_parameter_value")
    def add_parameter_value(self, **kwargs):
        """Insert new parameter."""
        parameter_value = self.get_new_parameter_value(**kwargs)
        if not parameter_value:
            return
        if self.add_parameter_value_to_db(parameter_value):
            self.add_parameter_value_to_model(parameter_value)

    def get_new_parameter_value(self, **kwargs):
        """Query the user's preferences for creating a new parameter value."""
        # We need to ask for the object or relationship first
        question = {}
        if 'object_id' not in kwargs and 'relationship_id' not in kwargs:
            object_or_relationship_name_list = ['Select object or relationship...']
            object_query = self.session.query(self.Object)
            relationship_query = self.session.query(self.Relationship)
            object_or_relationship_name_list.extend([item.name for item in object_query])
            object_or_relationship_name_list.extend([item.name for item in relationship_query])
            question.update({"object_or_relationship_name_list": object_or_relationship_name_list})
            dialog = CustomQDialog(self, "Add parameter value", **question)
            answer = dialog.exec_()
            if answer != QDialog.Accepted:
                return
            ind = dialog.answer['object_or_relationship_name_list']['index'] - 1
            if ind < object_query.count():
                kwargs.update({'object_id': object_query[ind].id})
            else:
                ind = ind - object_query.count()
                kwargs.update({'relationship_id': relationship_query[ind].id})
        # Prepare second question
        question = {}
        if 'parameter_id' not in kwargs:
            parameter_name_list = ['Select parameter...']
            if 'object_id' in kwargs:
                object_parameter_names = self.object_parameter_names(kwargs['object_id'])
                if not object_parameter_names:
                    self.ui.statusbar.showMessage("All parameters for this object are already created", 3000)
                    return
                parameter_name_list.extend(object_parameter_names)
            elif 'relationship_id' in kwargs:
                relationship_parameter_names = self.relationship_parameter_names(kwargs['relationship_id'])
                if not relationship_parameter_names:
                    self.ui.statusbar.showMessage("All parameters for this relationship are already created", 3000)
                    return
                parameter_name_list.extend(relationship_parameter_names)
            question.update({"parameter_name_list": parameter_name_list})
        if 'value' not in kwargs:
            question.update({"value": "Enter value here..."})
        if 'json' not in kwargs:
            question.update({"json": "Enter json here..."})
        dialog = CustomQDialog(self, "Add parameter value", **question)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return None
        if 'parameter_name_list' in dialog.answer:
            if dialog.answer['parameter_name_list']['index'] == 0:
                return None
            parameter_name = dialog.answer['parameter_name_list']['text']
            parameter_id = self.session.query(self.Parameter).\
                filter_by(name=parameter_name).one().id
            kwargs.update({"parameter_id": parameter_id})
        if 'value' in dialog.answer:
            # Only retrieve value if not an empty string
            if dialog.answer['value']:
                kwargs.update({'value': dialog.answer['value']})
        if 'json' in dialog.answer:
            # Only retrieve json if not an empty string
            if dialog.answer['json']:
                kwargs.update({'json': dialog.answer['json']})
        return self.ParameterValue(commit_id=self.commit.id, **kwargs)

    def add_parameter_value_to_db(self, parameter_value):
        """Add parameter value to database. Return boolean value depending on the
        result of the operation.

        Args:
            parameter_value (self.ParameterValue): the parameter value to add
        """
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.add(parameter_value)
            self.session.flush() # to get the relationship class id
            return True
        except DBAPIError as e:
            msg = "Could not insert new parameter value: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return False

    def add_parameter_value_to_model(self, parameter_value):
        """Add parameter value item to the object or relationship parameter value model.

        Args:
            parameter_value (self.ParameterValue)
        """
        self.init_parameter_value_models()
        # Scroll to concerned row in object parameter value table
        if parameter_value.object_id:
            self.ui.tableView_object_parameter_value.resizeColumnsToContents()
            source_row = self.object_parameter_value_model.rowCount()-1
            source_column = self.object_parameter_value_model.header.index("parameter_name")
            source_index = self.object_parameter_value_model.index(source_row, source_column)
            proxy_index = self.object_parameter_value_proxy.mapFromSource(source_index)
            self.ui.tabWidget_object.setCurrentIndex(0)
            self.ui.tableView_object_parameter_value.setCurrentIndex(proxy_index)
            self.ui.tableView_object_parameter_value.scrollTo(proxy_index)
        # Scroll to concerned row in relationship parameter value table
        elif parameter_value.relationship_id:
            self.relationship_parameter_proxy.setFilterRegExp("")
            self.ui.tableView_relationship_parameter.resizeColumnsToContents()
            source_row = self.relationship_parameter_model.rowCount()-1
            source_column = self.relationship_parameter_model.header.index("parameter_name")
            source_index = self.relationship_parameter_model.index(source_row, source_column)
            proxy_index = self.relationship_parameter_proxy.mapFromSource(source_index)
            self.ui.tabWidget_relationship.setCurrentIndex(0)
            self.ui.tableView_relationship_parameter.setCurrentIndex(proxy_index)
            self.ui.tableView_relationship_parameter.scrollTo(proxy_index)
        # Scroll to concerned object in treeview if necessary
        if parameter_value.object_id:
            current_index = self.ui.treeView_object.currentIndex()
            current_type = current_index.data(Qt.UserRole)
            if current_type == 'object':
                current_id = current_index.data(Qt.UserRole+1)['id']
                if current_id == parameter_value.object_id:
                    return  # We're already in the right one
            # Search it and scroll to it
            for item in self.object_tree_model.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                item_type = item.data(Qt.UserRole)
                if not item_type: # root
                    continue
                if item_type != 'object':
                    continue
                item_id = item.data(Qt.UserRole+1)['id']
                if item_id == parameter_value.object_id:
                    object_index = self.object_tree_model.indexFromItem(item)
                    self.ui.treeView_object.setCurrentIndex(object_index)
                    self.ui.treeView_object.scrollTo(object_index)
                    break
        # Scroll to concerned related_object in treeview if necessary
        elif parameter_value.relationship_id:
            current_index = self.ui.treeView_object.currentIndex()
            current_type = current_index.data(Qt.UserRole)
            if current_type == 'related_object':
                current_relationship_id = current_index.data(Qt.UserRole+1)['relationship_id']
                if current_relationship_id == parameter_value.relationship_id:
                    return  # We're already in the right one
            # Search the first one that matches and scroll to it
            for item in self.object_tree_model.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                item_type = item.data(Qt.UserRole)
                if not item_type: # root
                    continue
                if item_type != 'related_object':
                    continue
                item_relationship_id = item.data(Qt.UserRole+1)['relationship_id']
                if item_relationship_id == parameter_value.relationship_id:
                    relationship_index = self.object_tree_model.indexFromItem(item)
                    self.ui.treeView_object.setCurrentIndex(relationship_index)
                    self.ui.treeView_object.scrollTo(relationship_index)
                    break

    @Slot("QPoint", name="show_object_parameter_value_context_menu")
    def show_object_parameter_value_context_menu(self, pos):
        """Context menu for object parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        # logging.debug("object parameter value context menu")
        index = self.ui.tableView_object_parameter_value.indexAt(pos)
        # self.ui.tableView_object_parameter_value.selectRow(index.row())
        global_pos = self.ui.tableView_object_parameter_value.viewport().mapToGlobal(pos)
        self.object_parameter_value_context_menu = ParameterValueContextMenu(self, global_pos, index)
        option = self.object_parameter_value_context_menu.get_action()
        if option == "Remove row":
            self.remove_parameter_value(index)
        # elif option == "Edit field":
        #     self.ui.tableView_object_parameter_value.edit(index)
        # self.ui.tableView_object_parameter_value.selectionModel().clearSelection()
        self.object_parameter_value_context_menu.deleteLater()
        self.object_parameter_value_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_value_context_menu")
    def show_relationship_parameter_value_context_menu(self, pos):
        """Context menu for relationship parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        # logging.debug("relationship parameter value context menu")
        index = self.ui.tableView_relationship_parameter_value.indexAt(pos)
        # self.ui.tableView_relationship_parameter_value.selectRow(index.row())
        global_pos = self.ui.tableView_relationship_parameter_value.viewport().mapToGlobal(pos)
        self.relationship_parameter_value_context_menu = ParameterValueContextMenu(self, global_pos, index)
        option = self.relationship_parameter_value_context_menu.get_action()
        if option == "Remove row":
            self.remove_parameter_value(index)
        # elif option == "Edit field":
        #     self.ui.tableView_relationship_parameter_value.edit(index)
        # self.ui.tableView_relationship_parameter_value.selectionModel().clearSelection()
        self.relationship_parameter_value_context_menu.deleteLater()
        self.relationship_parameter_value_context_menu = None

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_parameter_value")
    def update_parameter_value(self, editor, hint):
        """Update (object or relationship) parameter_value table with newly edited data.
        If successful, also update item in the model.
        """
        # logging.debug("update parameter value")
        index = editor.index
        proxy_model = index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        header = source_model.header
        id_column = header.index('parameter_value_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_value_id = sibling.data()
        parameter_value = self.session.query(self.ParameterValue).\
            filter_by(id=parameter_value_id).one_or_none()
        if not parameter_value:
            logging.debug("entry not found in parameter_value table")
            return
        field_name = header[source_index.column()]
        value = getattr(parameter_value, field_name)
        data_type = type(value)
        try:
            new_value = data_type(editor.text())
        except TypeError:
            new_value = editor.text()
        except ValueError:
            # Note: try to avoid this by setting up a good validator in line edit delegate
            self.ui.statusbar.showMessage("The value entered doesn't fit the datatype.")
            return
        if value == new_value:
            self.ui.statusbar.showMessage("Parameter value not changed", 3000)
            return
        try:
            self.transactions.append(self.session.begin_nested())
            setattr(parameter_value, field_name, new_value)
            parameter_value.commit_id = self.commit.id
            self.session.flush()
        except DBAPIError as e:
            msg = "Could not update parameter value: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return
        # manually update item in model
        source_model.setData(source_index, new_value)

    def remove_parameter_value(self, proxy_index):
        """Remove row from (object or relationship) parameter_value table.
        If succesful, also remove row from model"""
        proxy_model = proxy_index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(proxy_index)
        id_column = source_model.header.index('parameter_value_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_value_id = sibling.data()
        parameter_value = self.session.query(self.ParameterValue).\
            filter_by(id=parameter_value_id).one_or_none()
        if not parameter_value:
            logging.debug("entry not found in parameter_value table")
            return
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(parameter_value)
            self.session.flush()
        except DBAPIError as e:
            msg = "Could not remove parameter value: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return
        # manually remove row from model
        source_model.removeRows(source_index.row(), 1)

    @Slot("QPoint", name="show_object_parameter_context_menu")
    def show_object_parameter_context_menu(self, pos):
        """Context menu for object parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        # logging.debug("object parameter context menu")
        index = self.ui.tableView_object_parameter.indexAt(pos)
        # self.ui.tableView_object_parameter.selectRow(index.row())
        global_pos = self.ui.tableView_object_parameter.viewport().mapToGlobal(pos)
        self.object_parameter_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.object_parameter_context_menu.get_action()
        if option == "Remove row":
            self.remove_parameter(index)
        # elif option == "Edit field":
        #     self.ui.tableView_object_parameter.edit(index)
        # self.ui.tableView_object_parameter.selectionModel().clearSelection()
        self.object_parameter_context_menu.deleteLater()
        self.object_parameter_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_context_menu")
    def show_relationship_parameter_context_menu(self, pos):
        """Context menu for relationship parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        # logging.debug("relationship parameter context menu")
        index = self.ui.tableView_relationship_parameter.indexAt(pos)
        # self.ui.tableView_relationship_parameter.selectRow(index.row())
        global_pos = self.ui.tableView_relationship_parameter.viewport().mapToGlobal(pos)
        self.relationship_parameter_context_menu = ParameterContextMenu(self, global_pos, index)
        option = self.relationship_parameter_context_menu.get_action()
        if option == "Remove row":
            self.remove_parameter(index)
        # elif option == "Edit field":
        #     self.ui.tableView_relationship_parameter.edit(index)
        # self.ui.tableView_relationship_parameter.selectionModel().clearSelection()
        self.relationship_parameter_context_menu.deleteLater()
        self.relationship_parameter_context_menu = None

    @Slot("QWidget", "QAbstractItemDelegate.EndEditHint", name="update_parameter")
    def update_parameter(self, editor, hint):
        """Update parameter table with newly edited data.
        If successful, also update item in the model.
        """
        # logging.debug("update parameter")
        index = editor.index
        proxy_model = index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        header = source_model.header
        id_column = header.index('parameter_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_id = sibling.data()
        parameter = self.session.query(self.Parameter).\
            filter_by(id=parameter_id).one_or_none()
        if not parameter:
            logging.debug("entry not found in parameter table")
            return
        field_name = header[index.column()]
        if field_name == 'parameter_name':
            field_name = 'name'
        value = getattr(parameter, field_name)
        data_type = type(value)
        try:
            new_value = data_type(editor.text())
        except ValueError:
            # NOTE: try to avoid this by setting up a good validator in line edit delegate
            self.ui.statusbar.showMessage("The value entered doesn't fit the datatype.")
            return
        if value == new_value:
            logging.debug("parameter not changed")
            return
        try:
            self.transactions.append(self.session.begin_nested())
            setattr(parameter, field_name, new_value)
            parameter.commit_id = self.commit.id
            self.session.flush()
        except DBAPIError as e:
            msg = "Could not update parameter: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return
        # manually update item in model
        source_model.setData(source_index, new_value)
        # refresh parameter value models to reflect name change
        if field_name == 'name':
            self.init_parameter_value_models()

    def remove_parameter(self, proxy_index):
        """Remove row from (object or relationship) parameter table.
        If succesful, also remove row from model"""
        proxy_model = proxy_index.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(proxy_index)
        id_column = source_model.header.index('parameter_id')
        sibling = source_index.sibling(source_index.row(), id_column)
        parameter_id = sibling.data()
        parameter = self.session.query(self.Parameter).\
            filter_by(id=parameter_id).one_or_none()
        if not parameter:
            logging.debug("entry not found in parameter table")
            return
        try:
            self.transactions.append(self.session.begin_nested())
            self.session.delete(parameter)
            self.session.flush()
        except DBAPIError as e:
            msg = "Could not remove parameter: {}".format(e.orig.args)
            self.ui.statusbar.showMessage(msg, 5000)
            self.session.rollback()
            return
        # manually remove row from model
        source_model.removeRows(source_index.row(), 1)
        # refresh parameter value models to reflect any change
        self.init_parameter_value_models()

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("mainWindow/windowSize")
        window_pos = self.qsettings.value("mainWindow/windowPosition")
        splitter_tree_parameter_state = self.qsettings.value("mainWindow/splitterTreeParameterState")
        window_maximized = self.qsettings.value("mainWindow/windowMaximized", defaultValue='false')  # returns string
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if splitter_tree_parameter_state:
            self.ui.splitter_tree_parameter.restoreState(splitter_tree_parameter_state)

    @Slot(name="close_session")
    def close_session(self):
        """Close this form without commiting any changes."""
        self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if self._data_store is not None:
            self._data_store.destroyed.disconnect(self.data_store_destroyed)
        # save qsettings
        self.qsettings.setValue("mainWindow/splitterTreeParameterState", self.ui.splitter_tree_parameter.saveState())
        self.qsettings.setValue("mainWindow/windowSize", self.size())
        self.qsettings.setValue("mainWindow/windowPosition", self.pos())
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("mainWindow/windowMaximized", True)
        else:
            self.qsettings.setValue("mainWindow/windowMaximized", False)
        # close sql session
        if self.session:
            self.session.rollback()
            self.session.close()
        if self.engine:
            self.engine.dispose()
        if event:
            event.accept()
