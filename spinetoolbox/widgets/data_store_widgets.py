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
Classes for data store widgets.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import os
import time  # just to measure loading time and sqlalchemy ORM performance
import logging
import json
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from PySide2.QtWidgets import QMainWindow, QHeaderView, QDialog, QToolButton, QMessageBox, QCheckBox, \
    QFileDialog, QApplication, QErrorMessage, QLabel, QGraphicsScene, QGraphicsRectItem, QAction, \
    QButtonGroup, QSizePolicy, QHBoxLayout, QWidget, QWidgetAction
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QPointF, QRectF, QSize
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon, QPixmap, QPalette
from ui.tree_view_form import Ui_MainWindow as tree_view_form_ui
from ui.graph_view_form import Ui_MainWindow as graph_view_form_ui
from config import MAINWINDOW_SS, STATUSBAR_SS
from spinedatabase_api import SpineDBAPIError, SpineIntegrityError
from widgets.custom_menus import ObjectTreeContextMenu, ParameterContextMenu, \
    ObjectItemContextMenu, GraphViewContextMenu
from widgets.custom_delegates import ObjectParameterValueDelegate, ObjectParameterDefinitionDelegate, \
    RelationshipParameterValueDelegate, RelationshipParameterDefinitionDelegate
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, \
    AddRelationshipClassesDialog, AddRelationshipsDialog, \
    EditObjectClassesDialog, EditObjectsDialog, \
    EditRelationshipClassesDialog, EditRelationshipsDialog, \
    CommitDialog
from widgets.custom_qwidgets import ZoomWidget
from models import ObjectTreeModel, ObjectClassListModel, RelationshipClassListModel, \
    ObjectParameterDefinitionModel, ObjectParameterValueModel, \
    RelationshipParameterDefinitionModel, RelationshipParameterValueModel, \
    JSONArrayModel
from graphics_items import ObjectItem, ArcItem, CustomTextItem
from excel_import_export import import_xlsx_to_db, export_spine_database_to_xlsx
from spinedatabase_api import copy_database
from datapackage_import_export import datapackage_to_spine
from helpers import busy_effect, relationship_pixmap, object_pixmap, fix_name_ambiguity


class DataStoreForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        data_store (DataStore): The DataStore instance that owns this form
        db_map (DiffDatabaseMapping): The object relational database mapping
        database (str): The database name
        ui (Ui_MainWindow(object)): The ui to load the form with
    """
    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, data_store, db_map, database, ui):
        """Initialize class."""
        super().__init__(flags=Qt.Window)
        self._data_store = data_store
        # Setup UI from Qt Designer file
        self.ui = ui
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        # Set up status bar and apply style sheet
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        self.setStyleSheet(MAINWINDOW_SS)
        # Set up corner widgets
        self.set_corner_widgets()
        # Class attributes
        self.err_msg = QErrorMessage(self)
        # DB db_map
        self.db_map = db_map
        self.database = database
        self.object_icon_dict = {}
        self.relationship_icon_dict = {}
        # Object tree model
        self.object_tree_model = ObjectTreeModel(self)
        self.selected_object_class_ids = set()
        self.selected_object_ids = dict()
        self.selected_relationship_class_ids = set()
        self.selected_object_id_lists = dict()
        # Parameter value models
        self.object_parameter_value_model = ObjectParameterValueModel(self)
        self.relationship_parameter_value_model = RelationshipParameterValueModel(self)
        # Parameter definition models
        self.object_parameter_definition_model = ObjectParameterDefinitionModel(self)
        self.relationship_parameter_definition_model = RelationshipParameterDefinitionModel(self)
        # Other
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        # Message signals
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        # Menu actions
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)
        self.ui.actionClose.triggered.connect(self.close)
        # Object tree
        self.ui.treeView_object.selectionModel().selectionChanged.connect(self._handle_object_tree_selection_changed)
        # Parameter tables delegate commit data
        self.ui.tableView_object_parameter_definition.itemDelegate().data_committed.\
            connect(self.set_parameter_definition_data)
        self.ui.tableView_object_parameter_value.itemDelegate().data_committed.\
            connect(self.set_parameter_value_data)
        self.ui.tableView_relationship_parameter_definition.itemDelegate().data_committed.\
            connect(self.set_parameter_definition_data)
        self.ui.tableView_relationship_parameter_value.itemDelegate().data_committed.\
            connect(self.set_parameter_value_data)
        # DS destroyed
        self._data_store.destroyed.connect(self.close)

    def qsettings(self):
        """Returns the QSettings instance from ToolboxUI."""
        return self._data_store._toolbox.qsettings()

    def set_corner_widgets(self):
        """Set corner widgets (icon and text on the tab bar) to both QTabWidgets."""
        icon_size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Corner widget for object parameter tab widget
        corner_widget1 = QWidget()
        icon_label1 = QLabel()
        icon_label1.setSizePolicy(icon_size_policy)
        icon_label1.setMinimumSize(QSize(16, 16))
        icon_label1.setMaximumSize(QSize(16, 16))
        icon_label1.setPixmap(QPixmap(":/icons/object_parameter_icon.png"))
        icon_label1.setScaledContents(True)
        text_label1 = QLabel("Object parameter")
        obj_layout = QHBoxLayout()
        obj_layout.setContentsMargins(6, 2, 0, 2)
        obj_layout.addWidget(text_label1)
        obj_layout.addWidget(icon_label1)
        corner_widget1.setLayout(obj_layout)
        self.ui.tabWidget_object_parameter.setCornerWidget(corner_widget1, Qt.TopRightCorner)
        # Corner widget for relationship parameter tab widget
        corner_widget2 = QWidget()
        icon_label2 = QLabel()
        icon_label2.setSizePolicy(icon_size_policy)
        icon_label2.setMinimumSize(QSize(16, 16))
        icon_label2.setMaximumSize(QSize(16, 16))
        icon_label2.setPixmap(QPixmap(":/icons/relationship_parameter_icon.png"))
        icon_label2.setScaledContents(True)
        text_label2 = QLabel("Relationship parameter")
        rel_layout = QHBoxLayout()
        rel_layout.addWidget(text_label2)
        rel_layout.addWidget(icon_label2)
        rel_layout.setContentsMargins(6, 2, 0, 2)
        corner_widget2.setLayout(rel_layout)
        self.ui.tabWidget_relationship_parameter.setCornerWidget(corner_widget2, Qt.TopRightCorner)

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Append regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        current_msg = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage("\t".join([msg, current_msg]), 5000)

    @Slot(str, name="add_error_message")
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show in QErrorMessage
        """
        self.err_msg.showMessage(msg)

    def set_commit_rollback_actions_enabled(self, on):
        self.ui.actionCommit.setEnabled(on)
        self.ui.actionRollback.setEnabled(on)

    @Slot("bool", name="show_commit_session_dialog")
    def show_commit_session_dialog(self, checked=False):
        """Query user for a commit message and commit changes to source database."""
        if not self.db_map.has_pending_changes():
            self.msg.emit("Nothing to commit yet.")
            return
        dialog = CommitDialog(self, self.database)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        self.commit_session(dialog.commit_msg)

    @busy_effect
    def commit_session(self, commit_msg):
        try:
            self.db_map.commit_session(commit_msg)
            self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes committed successfully."
        self.msg.emit(msg)

    @Slot("bool", name="rollback_session")
    def rollback_session(self, checked=False):
        try:
            self.db_map.rollback_session()
            self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes since last commit rolled back successfully."
        self.msg.emit(msg)
        self.init_models()

    @Slot("bool", name="refresh_session")
    def refresh_session(self, checked=False):
        msg = "Session refreshed."
        self.msg.emit(msg)
        self.init_models()

    def object_icon(self, object_class_name):
        """An appropriate object icon for `object_class_name`."""
        if not object_class_name:
            return QIcon()
        try:
            icon = self.object_icon_dict[object_class_name]
        except KeyError:
            icon = QIcon(object_pixmap(object_class_name))
            self.object_icon_dict[object_class_name] = icon
        return icon

    def relationship_icon(self, object_class_name_list):
        """An appropriate relationship icon for `object_class_name_list`."""
        if not object_class_name_list:
            return QIcon()
        try:
            icon = self.relationship_icon_dict[object_class_name_list]
        except KeyError:
            icon = QIcon(relationship_pixmap(object_class_name_list.split(",")))
            self.relationship_icon_dict[object_class_name_list] = icon
        return icon

    def init_models(self):
        """Initialize models."""
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_definition_models()

    def init_parameter_value_models(self):
        """Initialize parameter value models from source database."""
        self.object_parameter_value_model.reset_model()
        self.relationship_parameter_value_model.reset_model()

    def init_parameter_definition_models(self):
        """Initialize parameter (definition) models from source database."""
        self.object_parameter_definition_model.reset_model()
        self.relationship_parameter_definition_model.reset_model()

    def init_views(self):
        """Initialize model views."""
        self.init_object_tree_view()
        self.init_object_parameter_value_view()
        self.init_relationship_parameter_value_view()
        self.init_object_parameter_definition_view()
        self.init_relationship_parameter_definition_view()

    def init_object_tree_view(self):
        """Init object tree view."""
        self.ui.treeView_object.setModel(self.object_tree_model)
        self.ui.treeView_object.header().hide()
        self.ui.treeView_object.expand(self.object_tree_model.root_item.index())
        self.ui.treeView_object.resizeColumnToContents(0)

    def init_object_parameter_value_view(self):
        """Init object parameter value view."""
        self.ui.tableView_object_parameter_value.setModel(self.object_parameter_value_model)
        h = self.object_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('object_class_id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('object_id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('parameter_id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter_value.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()

    def init_relationship_parameter_value_view(self):
        """Init relationship parameter value view."""
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_model)
        h = self.relationship_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('relationship_class_id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_class_id_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_class_name_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('relationship_id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_id_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('parameter_id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_value.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter_value.horizontalHeader().\
            setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_object_parameter_definition_view(self):
        """Init object parameter definition view."""
        self.ui.tableView_object_parameter_definition.setModel(self.object_parameter_definition_model)
        h = self.object_parameter_definition_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('object_class_id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_definition.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter_definition.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_object_parameter_definition.resizeColumnsToContents()

    def init_relationship_parameter_definition_view(self):
        """Init relationship parameter definition view."""
        self.ui.tableView_relationship_parameter_definition.setModel(self.relationship_parameter_definition_model)
        h = self.relationship_parameter_definition_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('relationship_class_id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('object_class_id_list'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().\
            setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_relationship_parameter_definition.verticalHeader().\
            setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().\
            setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_relationship_parameter_definition.resizeColumnsToContents()

    def setup_delegates(self):
        """Set delegates for tables."""
        # Object parameter
        table_view = self.ui.tableView_object_parameter_definition
        delegate = ObjectParameterDefinitionDelegate(self)
        table_view.setItemDelegate(delegate)
        # Object parameter value
        table_view = self.ui.tableView_object_parameter_value
        delegate = ObjectParameterValueDelegate(self)
        table_view.setItemDelegate(delegate)
        # Relationship parameter
        table_view = self.ui.tableView_relationship_parameter_definition
        delegate = RelationshipParameterDefinitionDelegate(self)
        table_view.setItemDelegate(delegate)
        # Relationship parameter value
        table_view = self.ui.tableView_relationship_parameter_value
        delegate = RelationshipParameterValueDelegate(self)
        table_view.setItemDelegate(delegate)

    @Slot("bool", name="show_add_object_classes_form")
    def show_add_object_classes_form(self, checked=False):
        """Show dialog to let user select preferences for new object classes."""
        dialog = AddObjectClassesDialog(self)
        dialog.show()

    @Slot("bool", name="show_add_objects_form")
    def show_add_objects_form(self, checked=False, class_id=None):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, class_id=class_id)
        dialog.show()

    @Slot("bool", name="show_add_relationship_classes_form")
    def show_add_relationship_classes_form(self, checked=False, object_class_id=None):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(self, object_class_one_id=object_class_id)
        dialog.show()

    @Slot("bool", name="show_add_relationships_form")
    def show_add_relationships_form(
            self, checked=False, relationship_class_id=None, object_id=None, object_class_id=None):
        """Show dialog to let user select preferences for new relationships."""
        dialog = AddRelationshipsDialog(
            self,
            relationship_class_id=relationship_class_id,
            object_id=object_id,
            object_class_id=object_class_id
        )
        dialog.show()

    def add_object_classes(self, object_classes):
        """Insert new object classes."""
        self.object_tree_model.add_object_classes(object_classes)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully added new object class(es) '{}'.".format("', '".join([x.name for x in object_classes]))
        self.msg.emit(msg)

    @busy_effect
    def add_objects(self, objects):
        """Insert new objects."""
        self.object_tree_model.add_objects(objects)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully added new object(s) '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)

    def add_relationship_classes(self, relationship_classes):
        """Insert new relationship classes."""
        self.object_tree_model.add_relationship_classes(relationship_classes)
        self.set_commit_rollback_actions_enabled(True)
        relationship_class_name_list = "', '".join([x.name for x in relationship_classes])
        msg = "Successfully added new relationship class(es) '{}'.".format(relationship_class_name_list)
        self.msg.emit(msg)

    def add_relationships(self, relationships):
        """Insert new relationships."""
        self.object_tree_model.add_relationships(relationships)
        self.set_commit_rollback_actions_enabled(True)
        relationship_name_list = "', '".join([x.name for x in relationships])
        msg = "Successfully added new relationship(s) '{}'.".format(relationship_name_list)
        self.msg.emit(msg)

    @Slot("bool", name="show_edit_object_classes_form")
    def show_edit_object_classes_form(self, checked=False):
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole) != "object_class":
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditObjectClassesDialog(self, kwargs_list)
        dialog.show()

    @Slot("bool", name="show_edit_objects_form")
    def show_edit_objects_form(self, checked=False):
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole) != "object":
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditObjectsDialog(self, kwargs_list)
        dialog.show()

    @Slot("bool", name="show_edit_relationship_classes_form")
    def show_edit_relationship_classes_form(self, checked=False):
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole) != "relationship_class":
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditRelationshipClassesDialog(self, kwargs_list)
        dialog.show()

    @Slot("bool", name="show_edit_relationships_form")
    def show_edit_relationships_form(self, checked=False):
        current = self.ui.treeView_object.currentIndex()
        if current.data(Qt.UserRole) != "relationship":
            return
        class_id = current.data(Qt.UserRole + 1)['class_id']
        wide_relationship_class = self.db_map.single_wide_relationship_class(id=class_id).one_or_none()
        if not wide_relationship_class:
            return
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole) != "relationship":
                continue
            # Only edit relationships of the same class as the one in current index, for now...
            if index.data(Qt.UserRole + 1)['class_id'] != class_id:
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditRelationshipsDialog(self, kwargs_list, wide_relationship_class)
        dialog.show()

    @busy_effect
    def update_object_classes(self, object_classes):
        """Update object classes."""
        self.object_tree_model.update_object_classes(object_classes)
        self.object_parameter_value_model.rename_object_classes(object_classes)
        self.object_parameter_definition_model.rename_object_classes(object_classes)
        self.relationship_parameter_value_model.rename_object_classes(object_classes)
        self.relationship_parameter_definition_model.rename_object_classes(object_classes)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully updated object classes '{}'.".format("', '".join([x.name for x in object_classes]))
        self.msg.emit(msg)

    @busy_effect
    def update_objects(self, objects):
        """Update objects."""
        self.object_tree_model.update_objects(objects)
        self.object_parameter_value_model.rename_objects(objects)
        self.relationship_parameter_value_model.rename_objects(objects)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully updated objects '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)

    @busy_effect
    def update_relationship_classes(self, wide_relationship_classes):
        """Update relationship classes."""
        self.object_tree_model.update_relationship_classes(wide_relationship_classes)
        self.relationship_parameter_value_model.rename_relationship_classes(wide_relationship_classes)
        self.relationship_parameter_definition_model.rename_relationship_classes(wide_relationship_classes)
        self.set_commit_rollback_actions_enabled(True)
        relationship_class_name_list = "', '".join([x.name for x in wide_relationship_classes])
        msg = "Successfully updated relationship classes '{}'.".format(relationship_class_name_list)
        self.msg.emit(msg)

    @busy_effect
    def update_relationships(self, wide_relationships):
        """Update relationships."""
        self.object_tree_model.update_relationships(wide_relationships)
        self.set_commit_rollback_actions_enabled(True)
        relationship_name_list = "', '".join([x.name for x in wide_relationships])
        msg = "Successfully updated relationships '{}'.".format(relationship_name_list)
        self.msg.emit(msg)

    @Slot("QModelIndex", "QVariant", name="set_parameter_value_data")
    def set_parameter_value_data(self, index, new_value):
        """Update (object or relationship) parameter value with newly edited data."""
        if new_value is None:
            return
        index.model().setData(index, new_value)

    @Slot("QModelIndex", "QVariant", name="set_parameter_definition_data")
    def set_parameter_definition_data(self, index, new_value):
        """Update (object or relationship) parameter definition with newly edited data."""
        if new_value is None:
            return
        header = index.model().horizontal_header_labels()
        if index.model().setData(index, new_value) and header[index.column()] == 'parameter_name':
            parameter_id_column = header.index('id')
            parameter_id = index.sibling(index.row(), parameter_id_column).data(Qt.DisplayRole)
            try:
                object_class_id_column = header.index('object_class_id')
                object_class_id = index.sibling(index.row(), object_class_id_column).data(Qt.DisplayRole)
                self.object_parameter_value_model.rename_parameter(parameter_id, object_class_id, new_value)
            except ValueError:
                try:
                    relationship_class_id_column = header.index('relationship_class_id')
                    relationship_class_id = index.sibling(index.row(), relationship_class_id_column).\
                        data(Qt.DisplayRole)
                    self.relationship_parameter_value_model.rename_parameter(
                        parameter_id, relationship_class_id, new_value)
                except ValueError:
                    pass

    def show_commit_session_prompt(self):
        """Shows the commit session message box."""
        config = self._data_store._toolbox._config
        commit_at_exit = config.get("settings", "commit_at_exit")
        if commit_at_exit == "0":
            # Don't commit session and don't show message box
            return
        elif commit_at_exit == "1":  # Default
            # Show message box
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Commit pending changes")
            msg.setText("The current session has uncommitted changes. Do you want to commit them now?")
            msg.setInformativeText("WARNING: If you choose not to commit, all changes will be lost.")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()
            chk = chkbox.checkState()
            if answer == QMessageBox.Yes:
                self.show_commit_session_dialog()
                if chk == 2:
                    # Save preference into config file
                    config.set("settings", "commit_at_exit", "2")
            else:
                if chk == 2:
                    # Save preference into config file
                    config.set("settings", "commit_at_exit", "0")
        elif commit_at_exit == "2":
            # Commit session and don't show message box
            self.show_commit_session_dialog()
        else:
            config.set("settings", "commit_at_exit", "1")
        return

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings().value("{0}/windowSize".format(self.settings_key))
        window_pos = self.qsettings().value("{0}/windowPosition".format(self.settings_key))
        window_maximized = self.qsettings().value("{0}/windowMaximized".format(self.settings_key), defaultValue='false')
        n_screens = self.qsettings().value("{0}/n_screens".format(self.settings_key), defaultValue=1)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings().setValue("{}/windowSize".format(self.settings_key), self.size())
        self.qsettings().setValue("{}/windowPosition".format(self.settings_key), self.pos())
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings().setValue("{}/windowMaximized".format(self.settings_key), True)
        else:
            self.qsettings().setValue("{}/windowMaximized".format(self.settings_key), False)
        if self.db_map.has_pending_changes():
            self.show_commit_session_prompt()
        self.db_map.close()
        if event:
            event.accept()


class TreeViewForm(DataStoreForm):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        data_store (DataStore): The DataStore instance that owns this form
        db_map (DiffDatabaseMapping): The object relational database mapping
        database (str): The database name
    """
    def __init__(self, data_store, db_map, database):
        """Initialize class."""
        tic = time.clock()
        super().__init__(data_store, db_map, database, tree_view_form_ui())
        # Object tree selected indexes
        self.selected_tree_indexes = {}
        # JSON models
        self.object_parameter_json_model = JSONArrayModel(self)
        self.relationship_parameter_json_model = JSONArrayModel(self)
        # JSON splitter sizes
        self.object_parameter_json_splitter_sizes = None
        self.relationship_parameter_json_splitter_sizes = None
        # Context menus
        self.object_tree_context_menu = None
        self.object_parameter_value_context_menu = None
        self.relationship_parameter_value_context_menu = None
        self.object_parameter_context_menu = None
        self.relationship_parameter_context_menu = None
        # Others
        self.focus_widget = None  # Last widget which had focus before showing a menu from the menubar
        self.fully_expand_icon = QIcon(QPixmap(":/icons/fully_expand.png"))
        self.fully_collapse_icon = QIcon(QPixmap(":/icons/fully_collapse.png"))
        self.find_next_icon = QIcon(QPixmap(":/icons/find_next.png"))
        self.settings_key = 'treeViewWidget'
        # init models and views
        self.init_models()
        self.init_views()
        self.setup_delegates()
        self.setup_buttons()
        self.connect_signals()
        self.restore_ui()
        self.setWindowTitle("Data store tree view    -- {} --".format(self.database))
        # Ensure this window gets garbage-collected when closed
        toc = time.clock()
        self.msg.emit("Tree view form created in {} seconds".format(toc - tic))

    def setup_buttons(self):
        """Specify actions and menus for add/remove parameter buttons."""
        # Setup button actions
        self.ui.toolButton_add_object_parameter_values.\
            setDefaultAction(self.ui.actionAdd_object_parameter_values)
        self.ui.toolButton_remove_object_parameter_values.\
            setDefaultAction(self.ui.actionRemove_object_parameter_values)
        self.ui.toolButton_add_relationship_parameter_values.\
            setDefaultAction(self.ui.actionAdd_relationship_parameter_values)
        self.ui.toolButton_remove_relationship_parameter_values.\
            setDefaultAction(self.ui.actionRemove_relationship_parameter_values)
        self.ui.toolButton_add_object_parameter_definitions.\
            setDefaultAction(self.ui.actionAdd_object_parameter_definitions)
        self.ui.toolButton_remove_object_parameter_definitions.\
            setDefaultAction(self.ui.actionRemove_object_parameter_definitions)
        self.ui.toolButton_add_relationship_parameter_definitions.\
            setDefaultAction(self.ui.actionAdd_relationship_parameter_definitions)
        self.ui.toolButton_remove_relationship_parameter_definitions.\
            setDefaultAction(self.ui.actionRemove_relationship_parameter_definitions)

    def connect_signals(self):
        """Connect signals to slots."""
        # Menu actions
        super().connect_signals()
        self.ui.actionImport.triggered.connect(self.show_import_file_dialog)
        self.ui.actionExport.triggered.connect(self.show_export_file_dialog)
        self.ui.actionAdd_object_classes.triggered.connect(self.show_add_object_classes_form)
        self.ui.actionAdd_objects.triggered.connect(self.show_add_objects_form)
        self.ui.actionAdd_relationship_classes.triggered.connect(self.show_add_relationship_classes_form)
        self.ui.actionAdd_relationships.triggered.connect(self.show_add_relationships_form)
        self.ui.actionAdd_object_parameter_values.triggered.connect(self.add_object_parameter_values)
        self.ui.actionAdd_relationship_parameter_values.triggered.connect(self.add_relationship_parameter_values)
        self.ui.actionAdd_object_parameter_definitions.triggered.connect(self.add_object_parameter_definitions)
        self.ui.actionAdd_relationship_parameter_definitions.triggered.\
            connect(self.add_relationship_parameter_definitions)
        self.ui.actionEdit_object_classes.triggered.connect(self.show_edit_object_classes_form)
        self.ui.actionEdit_objects.triggered.connect(self.show_edit_objects_form)
        self.ui.actionEdit_relationship_classes.triggered.connect(self.show_edit_relationship_classes_form)
        self.ui.actionEdit_relationships.triggered.connect(self.show_edit_relationships_form)
        self.ui.actionRemove_object_tree_items.triggered.connect(self.remove_object_tree_items)
        self.ui.actionRemove_object_parameter_definitions.triggered.connect(self.remove_object_parameter_definitions)
        self.ui.actionRemove_object_parameter_values.triggered.connect(self.remove_object_parameter_values)
        self.ui.actionRemove_relationship_parameter_definitions.triggered.\
            connect(self.remove_relationship_parameter_definitions)
        self.ui.actionRemove_relationship_parameter_values.triggered.\
            connect(self.remove_relationship_parameter_values)
        # Copy and paste
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        # Object tree
        self.ui.treeView_object.edit_key_pressed.connect(self.edit_object_tree_items)
        self.ui.treeView_object.customContextMenuRequested.connect(self.show_object_tree_context_menu)
        self.ui.treeView_object.doubleClicked.connect(self.find_next_leaf)
        # Parameter value tables delegate json editor requested
        self.ui.tableView_object_parameter_value.itemDelegate().json_editor_requested.\
            connect(self.edit_object_parameter_json)
        self.ui.tableView_relationship_parameter_value.itemDelegate().json_editor_requested.\
            connect(self.edit_relationship_parameter_json)
        # Parameter tables selection changes
        self.ui.tableView_object_parameter_definition.selectionModel().selectionChanged.\
            connect(self._handle_object_parameter_definition_selection_changed)
        self.ui.tableView_object_parameter_value.selectionModel().selectionChanged.\
            connect(self._handle_object_parameter_value_selection_changed)
        self.ui.tableView_relationship_parameter_definition.selectionModel().selectionChanged.\
            connect(self._handle_relationship_parameter_definition_selection_changed)
        self.ui.tableView_relationship_parameter_value.selectionModel().selectionChanged.\
            connect(self._handle_relationship_parameter_value_selection_changed)
        # Parameter value tables current changed
        self.ui.tableView_object_parameter_value.selectionModel().currentChanged.\
            connect(self._handle_object_parameter_value_current_changed)
        self.ui.tableView_relationship_parameter_value.selectionModel().currentChanged.\
            connect(self._handle_relationship_parameter_value_current_changed)
        # JSON splitters moved
        self.ui.splitter_object_parameter_value_json.splitterMoved.\
            connect(self._handle_object_parameter_json_splitter_moved)
        self.ui.splitter_relationship_parameter_value_json.splitterMoved.\
            connect(self._handle_relationship_parameter_json_splitter_moved)
        # Parameter json editor tool buttons clicked
        self.ui.toolButton_object_parameter_json_raw.toggled.connect(self._handle_object_parameter_json_raw_toggled)
        self.ui.toolButton_relationship_parameter_json_raw.toggled.\
            connect(self._handle_relationship_parameter_json_raw_toggled)
        # Parameter json editor ok clicked
        self.ui.pushButton_object_parameter_json_ok.clicked.connect(self._handle_object_parameter_json_ok_clicked)
        self.ui.pushButton_relationship_parameter_json_ok.clicked.\
            connect(self._handle_relationship_parameter_json_ok_clicked)
        # Parameter tabwidgets current changed
        self.ui.tabWidget_object_parameter.currentChanged.connect(self._handle_object_parameter_tab_changed)
        self.ui.tabWidget_relationship_parameter.currentChanged.connect(self._handle_relationship_parameter_tab_changed)
        # Parameter tables context menu requested
        self.ui.tableView_object_parameter_definition.customContextMenuRequested.\
            connect(self.show_object_parameter_context_menu)
        self.ui.tableView_object_parameter_value.customContextMenuRequested.\
            connect(self.show_object_parameter_value_context_menu)
        self.ui.tableView_relationship_parameter_definition.customContextMenuRequested.\
            connect(self.show_relationship_parameter_context_menu)
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.\
            connect(self.show_relationship_parameter_value_context_menu)
        # Menu about to show
        self.ui.menuFile.aboutToShow.connect(self._handle_menu_about_to_show)
        self.ui.menuEdit.aboutToShow.connect(self._handle_menu_about_to_show)
        self.ui.menuSession.aboutToShow.connect(self._handle_menu_about_to_show)

    @Slot("bool", name="copy")
    def copy(self, checked=False):
        """Copy data to clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.copy()
        except AttributeError:
            pass

    @Slot("bool", name="paste")
    def paste(self, checked=False):
        """Paste data from clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.paste()
        except AttributeError:
            pass

    @Slot("int", "int", name="_handle_object_parameter_json_splitter_moved")
    def _handle_object_parameter_json_splitter_moved(self, pos, index):
        """Save splitter sizes for later."""
        self.object_parameter_json_splitter_sizes = self.ui.splitter_object_parameter_value_json.sizes()

    @Slot("int", "int", name="_handle_relationship_parameter_json_splitter_moved")
    def _handle_relationship_parameter_json_splitter_moved(self, pos, index):
        """Save splitter sizes for later."""
        self.relationship_parameter_json_splitter_sizes = self.ui.splitter_relationship_parameter_value_json.sizes()

    @Slot("QModelIndex","QModelIndex", name="_handle_object_parameter_value_current_changed")
    def _handle_object_parameter_value_current_changed(self, current, previous):
        """Call update object JSON editor."""
        self.update_object_json_editor(current)

    @Slot("QModelIndex","QModelIndex", name="_handle_relationship_parameter_value_current_changed")
    def _handle_relationship_parameter_value_current_changed(self, current, previous):
        """Call update relationship JSON editor."""
        self.update_relationship_json_editor(current)

    def update_object_json_editor(self, current):
        """Update object JSON editor.
        If current's column is the json column, then:
        - if JSON data from current index is different than the one loaded
        in the text edit or table view, reset them.
        - Adjust splitter sizes.
        Else (not the json column), fully collapse the editor.
        """
        header = self.object_parameter_value_model.horizontal_header_labels()
        data = current.data(Qt.EditRole)
        splitter = self.ui.splitter_object_parameter_value_json
        sizes = splitter.sizes()
        width = sum(sizes)
        if header[current.column()] == "json":
            if self.ui.textEdit_object_parameter_json.toPlainText() != data:
                if data:
                    formatted_data = json.dumps(json.loads(data), indent=4)
                    self.ui.textEdit_object_parameter_json.setPlainText(formatted_data)
                else:
                    self.ui.textEdit_object_parameter_json.clear()
            if self.object_parameter_json_model.json != data:
                if self.object_parameter_json_model.reset_model(data):
                    self.ui.tableView_object_parameter_json.show()
                    self.ui.tableView_object_parameter_json.resizeColumnsToContents()
                    self.ui.label_object_parameter_json_error.hide()
                else:
                    self.ui.label_object_parameter_json_error.setText(
                        "Unable to parse JSON as array."
                    )
                    self.ui.label_object_parameter_json_error.show()
                    self.ui.tableView_object_parameter_json.hide()
            if not self.object_parameter_json_splitter_sizes:
                # Apply reasonable sizes
                sizes[0] = .8 * width
                sizes[1] = .2 * width
                splitter.setSizes(sizes)
            else:
                # Apply stored sizes
                splitter.setSizes(self.object_parameter_json_splitter_sizes)
        else:
            # Hide
            splitter.setSizes([width, 0])

    def update_relationship_json_editor(self, current):
        """Update relationship JSON editor.
        If current's column is the json column, then:
        - if JSON data from current index is different than the one loaded
        in the text edit or table view, reset them.
        - Adjust splitter sizes.
        Else (not the json column), fully collapse the editor.
        """
        header = self.relationship_parameter_value_model.horizontal_header_labels()
        data = current.data(Qt.EditRole)
        splitter = self.ui.splitter_relationship_parameter_value_json
        sizes = splitter.sizes()
        width = sum(sizes)
        if header[current.column()] == "json":
            if self.ui.textEdit_relationship_parameter_json.toPlainText() != data:
                if data:
                    formatted_data = json.dumps(json.loads(data), indent=4)
                    self.ui.textEdit_relationship_parameter_json.setPlainText(formatted_data)
                else:
                    self.ui.textEdit_relationship_parameter_json.clear()
            if self.relationship_parameter_json_model.json != data:
                if self.relationship_parameter_json_model.reset_model(data):
                    self.ui.tableView_relationship_parameter_json.show()
                    self.ui.tableView_relationship_parameter_json.resizeColumnsToContents()
                    self.ui.label_relationship_parameter_json_error.hide()
                else:
                    self.ui.label_relationship_parameter_json_error.setText(
                        "Unable to parse JSON as array."
                    )
                    self.ui.label_relationship_parameter_json_error.show()
                    self.ui.tableView_relationship_parameter_json.hide()
            if not self.relationship_parameter_json_splitter_sizes:
                # Apply reasonable sizes
                sizes[0] = .8 * width
                sizes[1] = .2 * width
                splitter.setSizes(sizes)
            else:
                # Apply stored sizes
                splitter.setSizes(self.relationship_parameter_json_splitter_sizes)
        else:
            # Hide
            splitter.setSizes([width, 0])

    @Slot("bool", name="_handle_object_parameter_json_raw_toggled")
    def _handle_object_parameter_json_raw_toggled(self, checked):
        """Called when the user checks the obj { } button in the object parameter json editor.
        Activate the proper tab in the tabwidget."""
        if checked:
            self.ui.tabWidget_object_parameter_json.setCurrentIndex(0)
        else:
            self.ui.tabWidget_object_parameter_json.setCurrentIndex(1)
        current = self.ui.tableView_object_parameter_value.currentIndex()
        self.update_object_json_editor(current)

    @Slot("bool", name="_handle_relationship_parameter_json_raw_toggled")
    def _handle_relationship_parameter_json_raw_toggled(self, checked):
        """Called when the user checks the obj { } button in the relationship parameter json editor.
        Activate the proper tab in the tabwidget."""
        if checked:
            self.ui.tabWidget_relationship_parameter_json.setCurrentIndex(0)
        else:
            self.ui.tabWidget_relationship_parameter_json.setCurrentIndex(1)
        current = self.ui.tableView_relationship_parameter_value.currentIndex()
        self.update_relationship_json_editor(current)

    @Slot("bool", name="_handle_object_parameter_json_ok_clicked")
    def _handle_object_parameter_json_ok_clicked(self, checked=False):
        """Called when the user clicks ok in the object parameter json editor.
        Set json field in object parameter value table."""
        if self.ui.tabWidget_object_parameter_json.currentIndex() == 0:
            json = self.ui.textEdit_object_parameter_json.toPlainText()
        else:
            json = self.object_parameter_json_model.json()
        index = self.ui.tableView_object_parameter_value.currentIndex()
        self.set_parameter_value_data(index, json)

    @Slot("bool", name="_handle_relationship_parameter_json_ok_clicked")
    def _handle_relationship_parameter_json_ok_clicked(self, checked=False):
        """Called when the user clicks ok in the relationship parameter json editor.
        Set json field in relationship parameter value table."""
        if self.ui.tabWidget_relationship_parameter_json.currentIndex() == 0:
            json = self.ui.textEdit_relationship_parameter_json.toPlainText()
        else:
            json = self.relationship_parameter_json_model.json()
        index = self.ui.tableView_relationship_parameter_value.currentIndex()
        self.set_parameter_value_data(index, json)

    @Slot(name="edit_object_parameter_json")
    def edit_object_parameter_json(self):
        """Start editing object parameter json."""
        if self.ui.tabWidget_object_parameter_json.currentIndex() == 0:
            self.ui.textEdit_object_parameter_json.setFocus()
        else:
            index = self.object_parameter_json_model.index(0, 0)
            self.ui.tableView_object_parameter_json.scrollTo(index)
            self.ui.tableView_object_parameter_json.edit(index)

    @Slot(name="edit_relationship_parameter_json")
    def edit_relationship_parameter_json(self):
        """Start editing relationship parameter json."""
        if self.ui.tabWidget_relationship_parameter_json.currentIndex() == 0:
            self.ui.textEdit_relationship_parameter_json.setFocus()
        else:
            index = self.relationship_parameter_json_model.index(0, 0)
            self.ui.tableView_relationship_parameter_json.scrollTo(index)
            self.ui.tableView_relationship_parameter_json.edit(index)

    @Slot("QItemSelection", "QItemSelection", name="_handle_object_parameter_definition_selection_changed")
    def _handle_object_parameter_definition_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        selection = self.ui.tableView_object_parameter_definition.selectionModel().selection()
        tab_index = self.ui.tabWidget_object_parameter.currentIndex()
        self.ui.actionRemove_object_parameter_definitions.setEnabled(tab_index == 1 and not selection.isEmpty())

    @Slot("QItemSelection", "QItemSelection", name="_handle_object_parameter_value_selection_changed")
    def _handle_object_parameter_value_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        selection = self.ui.tableView_object_parameter_value.selectionModel().selection()
        tab_index = self.ui.tabWidget_object_parameter.currentIndex()
        self.ui.actionRemove_object_parameter_values.setEnabled(tab_index == 0 and not selection.isEmpty())

    @Slot("QItemSelection", "QItemSelection", name="_handle_relationship_parameter_definition_selection_changed")
    def _handle_relationship_parameter_definition_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        selection = self.ui.tableView_relationship_parameter_definition.selectionModel().selection()
        tab_index = self.ui.tabWidget_relationship_parameter.currentIndex()
        self.ui.actionRemove_relationship_parameter_definitions.setEnabled(tab_index == 1 and not selection.isEmpty())

    @Slot("QItemSelection", "QItemSelection", name="_handle_relationship_parameter_value_selection_changed")
    def _handle_relationship_parameter_value_selection_changed(self, selected, deselected):
        """Enable/disable the option to remove rows."""
        selection = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        tab_index = self.ui.tabWidget_relationship_parameter.currentIndex()
        self.ui.actionRemove_relationship_parameter_values.setEnabled(tab_index == 0 and not selection.isEmpty())

    @Slot("int", name="_handle_object_parameter_tab_changed")
    def _handle_object_parameter_tab_changed(self, index):
        """Apply filter. Enable/disable the option to remove rows."""
        if index == 0:
            self.object_parameter_value_model.update_filter()
        else:
            self.object_parameter_definition_model.update_filter()
        selected = self.ui.tableView_object_parameter_definition.selectionModel().selection()
        self.ui.actionRemove_object_parameter_definitions.setEnabled(index == 1 and not selected.isEmpty())
        selected = self.ui.tableView_object_parameter_value.selectionModel().selection()
        self.ui.actionRemove_object_parameter_values.setEnabled(index == 0 and not selected.isEmpty())

    @Slot("int", name="_handle_relationship_parameter_tab_changed")
    def _handle_relationship_parameter_tab_changed(self, index):
        """Apply filter. Enable/disable the option to remove rows."""
        if index == 0:
            self.relationship_parameter_value_model.update_filter()
        else:
            self.relationship_parameter_definition_model.update_filter()
        selected = self.ui.tableView_relationship_parameter_definition.selectionModel().selection()
        self.ui.actionRemove_relationship_parameter_definitions.setEnabled(index == 1 and not selected.isEmpty())
        selected = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        self.ui.actionRemove_relationship_parameter_values.setEnabled(index == 0 and not selected.isEmpty())

    @Slot(name="_handle_menu_about_to_show")
    def _handle_menu_about_to_show(self):
        """Called when a menu from the menubar is about to show.
        Adjust copy paste actions depending on which widget has the focus.
        Enable/disable actions to edit object tree items depending on selection.
        Enable/disable actions to remove object tree items depending on selection.
        """
        # Edit object tree item actions
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        item_types = {x.data(Qt.UserRole) for x in indexes}
        self.ui.actionEdit_object_classes.setEnabled('object_class' in item_types)
        self.ui.actionEdit_objects.setEnabled('object' in item_types)
        self.ui.actionEdit_relationship_classes.setEnabled('relationship_class' in item_types)
        self.ui.actionEdit_relationships.setEnabled('relationship' in item_types)
        # Remove object tree items action
        self.ui.actionRemove_object_tree_items.setEnabled(len(indexes) > 0)
        # Copy/paste actions
        if self.focusWidget() != self.ui.menubar:
            self.focus_widget = self.focusWidget()
        self.ui.actionCopy.setText("Copy")
        self.ui.actionPaste.setText("Paste")
        self.ui.actionCopy.setEnabled(False)
        self.ui.actionPaste.setEnabled(False)
        if self.focus_widget == self.ui.treeView_object:
            can_copy = not self.focus_widget.selectionModel().selection().isEmpty()
            focus_widget_name = "object tree"
        elif self.focus_widget == self.ui.tableView_object_parameter_definition:
            can_copy = not self.focus_widget.selectionModel().selection().isEmpty()
            focus_widget_name = "object parameter definition"
        elif self.focus_widget == self.ui.tableView_object_parameter_value:
            can_copy = not self.focus_widget.selectionModel().selection().isEmpty()
            focus_widget_name = "object parameter value"
        elif self.focus_widget == self.ui.tableView_object_parameter_json:
            can_copy = not self.focus_widget.selectionModel().selection().isEmpty()
            focus_widget_name = "object parameter json"
        elif self.focus_widget == self.ui.textEdit_object_parameter_json:
            can_copy = not self.focus_widget.textCursor().selection().isEmpty()
            focus_widget_name = "object parameter json"
        elif self.focus_widget == self.ui.tableView_relationship_parameter_json:
            can_copy = not self.focus_widget.selectionModel().selection().isEmpty()
            focus_widget_name = "relationship parameter json"
        elif self.focus_widget == self.ui.textEdit_relationship_parameter_json:
            can_copy = not self.focus_widget.textCursor().selection().isEmpty()
            focus_widget_name = "relationship parameter json"
        elif self.focus_widget == self.ui.tableView_relationship_parameter_definition:
            can_copy = not self.focus_widget.selectionModel().selection().isEmpty()
            focus_widget_name = "relationship parameter definition"
        elif self.focus_widget == self.ui.tableView_relationship_parameter_value:
            can_copy = not self.focus_widget.selectionModel().selection().isEmpty()
            focus_widget_name = "relationship parameter value"
        elif self.focus_widget == self.ui.tableView_relationship_parameter_json:
            can_copy = not self.focus_widget.selectionModel().selection().isEmpty()
            focus_widget_name = "relationship parameter json"
        else:
            return
        if can_copy:
            self.ui.actionCopy.setText("Copy from {}".format(focus_widget_name))
            self.ui.actionCopy.setEnabled(True)
        if focus_widget_name != "object tree" and self.focus_widget.canPaste():
            self.ui.actionPaste.setText("Paste to {}".format(focus_widget_name))
            self.ui.actionPaste.setEnabled(True)

    @Slot("bool", name="show_import_file_dialog")
    def show_import_file_dialog(self, checked=False):
        """Show dialog to allow user to select a file to import."""
        answer = QFileDialog.getOpenFileName(
            self, "Select file to import", self._data_store.project().project_dir, "*.*")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self.import_file(file_path)

    @busy_effect
    def import_file(self, file_path, checked=False):
        """Import data from file into current database."""
        if file_path.lower().endswith('datapackage.json'):
            try:
                datapackage_to_spine(self.db_map, file_path)
                self.msg.emit("Datapackage successfully imported.")
                self.set_commit_rollback_actions_enabled(True)
                self.init_models()
            except (SpineDBAPIError, SpineIntegrityError) as e:
                self.msg_error.emit(e.msg)
        elif file_path.lower().endswith('xlsx'):
            error_log = []
            try:
                insert_log, error_log = import_xlsx_to_db(self.db_map, file_path)
                self.msg.emit("Excel file successfully imported.")
                self.set_commit_rollback_actions_enabled(True)
                # logging.debug(insert_log)
                self.init_models()
            except SpineIntegrityError as e:
                self.msg_error.emit(e.msg)
            except SpineDBAPIError as e:
                self.msg_error.emit("Unable to import Excel file: {}".format(e.msg))
            finally:
                if not len(error_log) == 0:
                    msg = "Something went wrong in importing an Excel file " \
                          "into the current session. Here is the error log:\n\n{0}".format(error_log)
                    # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
                    self.msg_error.emit(msg)
                    # logging.debug(error_log)

    @Slot("bool", name="show_export_file_dialog")
    def show_export_file_dialog(self, checked=False):
        """Show dialog to allow user to select a file to export."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getSaveFileName(self,
                                             "Export to file",
                                             self._data_store.project().project_dir,
                                             "Excel file (*.xlsx);;SQlite database (*.sqlite *.db)")
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        if answer[1].startswith("SQlite"):
            self.export_to_sqlite(file_path)
        elif answer[1].startswith("Excel"):
            self.export_to_excel(file_path)

    @busy_effect
    def export_to_excel(self, file_path):
        """Export data from database into Excel file."""
        filename = os.path.split(file_path)[1]
        try:
            export_spine_database_to_xlsx(self.db_map, file_path)
            self.msg.emit("Excel file successfully exported.")
        except PermissionError:
            self.msg_error.emit("Unable to export to file <b>{0}</b>.<br/>"
                                "Close the file in Excel and try again.".format(filename))
        except OSError:
            self.msg_error.emit("[OSError] Unable to export to file <b>{0}</b>".format(filename))

    @busy_effect
    def export_to_sqlite(self, file_path):
        """Export data from database into SQlite file."""
        # Remove file if exists (at this point, the user has confirmed that overwritting is ok)
        try:
            os.remove(file_path)
        except OSError:
            pass
        dst_url = 'sqlite:///{0}'.format(file_path)
        copy_database(dst_url, self.db_map.db_url)
        self.msg.emit("SQlite file successfully exported.")

    def init_object_tree_model(self):
        """Initialize object tree model."""
        self.object_tree_model.build_tree(self.database)
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.hasChildren())

    def init_views(self):
        """Initialize model views."""
        super().init_views()
        self.init_parameter_json_editors()

    def init_parameter_json_editors(self):
        """Init object and relationship parameter json editors."""
        # Monospace font fot json text edits
        font = QFont()
        font.setFamily("Courier")
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(10)
        metrics = QFontMetrics(font)
        tab_stop_width = 4 * metrics.width(' ')
        # Object
        button_group = QButtonGroup(self)
        button_group.addButton(self.ui.toolButton_object_parameter_json_raw)
        button_group.addButton(self.ui.toolButton_object_parameter_json_table)
        self.ui.tabWidget_object_parameter_json.tabBar().hide()
        sizes = self.ui.splitter_object_parameter_value_json.sizes()
        self.ui.splitter_object_parameter_value_json.setSizes([sum(sizes), 0])
        self.ui.tableView_object_parameter_json.setModel(self.object_parameter_json_model)
        self.ui.tableView_object_parameter_json.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter_json.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.label_object_parameter_json_error.hide()
        self.ui.textEdit_relationship_parameter_json
        self.ui.textEdit_object_parameter_json.setFont(font)
        self.ui.textEdit_object_parameter_json.setTabStopWidth(tab_stop_width)
        # Relationship
        button_group = QButtonGroup(self)
        button_group.addButton(self.ui.toolButton_relationship_parameter_json_raw)
        button_group.addButton(self.ui.toolButton_relationship_parameter_json_table)
        self.ui.tabWidget_relationship_parameter_json.tabBar().hide()
        sizes = self.ui.splitter_relationship_parameter_value_json.sizes()
        self.ui.splitter_relationship_parameter_value_json.setSizes([sum(sizes), 0])
        self.ui.tableView_relationship_parameter_json.setModel(self.relationship_parameter_json_model)
        self.ui.tableView_relationship_parameter_json.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_relationship_parameter_json.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.label_relationship_parameter_json_error.hide()
        self.ui.textEdit_relationship_parameter_json.setFont(font)
        self.ui.textEdit_relationship_parameter_json.setTabStopWidth(tab_stop_width)

    @Slot("QModelIndex", name="find_next_leaf")
    def find_next_leaf(self, index):
        """If index corresponds to a relationship, then expand the next ocurrence of it."""
        if not index.isValid():
            return  # just to be safe
        clicked_type = index.data(Qt.UserRole)
        if not clicked_type:  # root item
            return
        if not clicked_type == 'relationship':
            return
        clicked_item = index.model().itemFromIndex(index)
        if clicked_item.hasChildren():
            return
        self.find_next(index)

    def find_next(self, index):
        """Expand next occurrence of a relationship."""
        next_index = self.object_tree_model.next_relationship_index(index)
        if not next_index:
            return
        self.ui.treeView_object.setCurrentIndex(next_index)
        self.ui.treeView_object.scrollTo(next_index)
        self.ui.treeView_object.expand(next_index)

    @busy_effect
    @Slot("QItemSelection", "QItemSelection", name="_handle_object_tree_selection_changed")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Called when the object tree selection changes.
        Set default rows and apply filters on parameter models."""
        self.set_default_parameter_rows()
        self.update_and_apply_filter(selected, deselected)
        self.update_json_editors()

    def update_json_editors(self):
        """Update data in json editors."""
        current = self.ui.tableView_object_parameter_value.currentIndex()
        self.update_object_json_editor(current)
        current = self.ui.tableView_relationship_parameter_value.currentIndex()
        self.update_relationship_json_editor(current)

    def set_default_parameter_rows(self):
        """Set default rows for parameter models according to selection in object tree."""
        selection = self.ui.treeView_object.selectionModel().selection()
        if selection.count() != 1:
            return
        index = selection.indexes()[0]
        item_type = index.data(Qt.UserRole)
        if item_type == 'object_class':
            default_row = dict(
                object_class_id=index.data(Qt.UserRole + 1)['id'],
                object_class_name=index.data(Qt.UserRole + 1)['name'])
            model = self.object_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.object_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'object':
            default_row = dict(
                object_class_id=index.parent().data(Qt.UserRole + 1)['id'],
                object_class_name=index.parent().data(Qt.UserRole + 1)['name'])
            model = self.object_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            default_row.update(dict(
                object_id=index.data(Qt.UserRole + 1)['id'],
                object_name=index.data(Qt.UserRole + 1)['name']))
            model = self.object_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'relationship_class':
            default_row = dict(
                relationship_class_id=index.data(Qt.UserRole + 1)['id'],
                relationship_class_name=index.data(Qt.UserRole + 1)['name'],
                object_class_id_list=index.data(Qt.UserRole + 1)['object_class_id_list'],
                object_class_name_list=index.data(Qt.UserRole + 1)['object_class_name_list'])
            model = self.relationship_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.relationship_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'relationship':
            default_row = dict(
                relationship_class_id=index.parent().data(Qt.UserRole + 1)['id'],
                relationship_class_name=index.parent().data(Qt.UserRole + 1)['name'],
                object_class_id_list=index.parent().data(Qt.UserRole + 1)['object_class_id_list'],
                object_class_name_list=index.parent().data(Qt.UserRole + 1)['object_class_name_list'])
            model = self.relationship_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            default_row.update(dict(
                relationship_id=index.data(Qt.UserRole + 1)['id'],
                object_id_list=index.data(Qt.UserRole + 1)['object_id_list'],
                object_name_list=index.data(Qt.UserRole + 1)['object_name_list']))
            model = self.relationship_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'root':
            default_row = dict()
            model = self.object_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.object_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.relationship_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            model = self.relationship_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)

    def update_and_apply_filter(self, selected, deselected):
        """Apply filters on parameter models according to selected and deselected object tree indexes."""
        for index in deselected.indexes():
            item_type = index.data(Qt.UserRole)
            self.selected_tree_indexes.setdefault(item_type, set()).remove(index)
        for index in selected.indexes():
            item_type = index.data(Qt.UserRole)
            self.selected_tree_indexes.setdefault(item_type, set()).add(index)
        self.update_selected_object_class_ids()
        self.update_selected_object_ids()
        self.update_selected_relationship_class_ids()
        self.update_selected_object_id_lists()
        if self.ui.tabWidget_object_parameter.currentIndex() == 0:
            self.object_parameter_value_model.update_filter()
        else:
            self.object_parameter_definition_model.update_filter()
        if self.ui.tabWidget_relationship_parameter.currentIndex() == 0:
            self.relationship_parameter_value_model.update_filter()
        else:
            self.relationship_parameter_definition_model.update_filter()

    def update_selected_object_class_ids(self):
        """Update set of selected object class id."""
        self.selected_object_class_ids = set(
            ind.data(Qt.UserRole + 1)['id']
            for ind in self.selected_tree_indexes.get('object_class', {}))
        self.selected_object_class_ids.update(set(
            ind.data(Qt.UserRole + 1)['class_id']
            for ind in self.selected_tree_indexes.get('object', {})))
        self.selected_object_class_ids.update(set(
            ind.parent().data(Qt.UserRole + 1)['class_id']
            for ind in self.selected_tree_indexes.get('relationship_class', {})))
        self.selected_object_class_ids.update(set(
            ind.parent().parent().data(Qt.UserRole + 1)['class_id']
            for ind in self.selected_tree_indexes.get('relationship', {})))

    def update_selected_object_ids(self):
        """Update set of selected object id."""
        self.selected_object_ids = {}
        for ind in self.selected_tree_indexes.get('object', {}):
            object_class_id = ind.data(Qt.UserRole + 1)['class_id']
            object_id = ind.data(Qt.UserRole + 1)['id']
            self.selected_object_ids.setdefault(object_class_id, set()).add(object_id)
        for ind in self.selected_tree_indexes.get('relationship_class', {}):
            object_class_id = ind.parent().data(Qt.UserRole + 1)['class_id']
            object_id = ind.parent().data(Qt.UserRole + 1)['id']
            self.selected_object_ids.setdefault(object_class_id, set()).add(object_id)
        for ind in self.selected_tree_indexes.get('relationship', {}):
            object_class_id = ind.parent().parent().data(Qt.UserRole + 1)['class_id']
            object_id = ind.parent().parent().data(Qt.UserRole + 1)['id']
            self.selected_object_ids.setdefault(object_class_id, set()).add(object_id)

    def update_selected_relationship_class_ids(self):
        """Update set of selected relationship class id."""
        self.selected_relationship_class_ids = set(
            ind.data(Qt.UserRole + 1)['id']
            for ind in self.selected_tree_indexes.get('relationship_class', {}))
        self.selected_relationship_class_ids.update(set(
            ind.data(Qt.UserRole + 1)['class_id']
            for ind in self.selected_tree_indexes.get('relationship', {})))

    def update_selected_object_id_lists(self):
        """Update set of selected object id list."""
        self.selected_object_id_lists = {}
        for ind in self.selected_tree_indexes.get('relationship', {}):
            relationship_class_id = ind.data(Qt.UserRole + 1)['class_id']
            object_id_list = ind.data(Qt.UserRole + 1)['object_id_list']
            self.selected_object_id_lists.setdefault(relationship_class_id, set()).add(object_id_list)

    @Slot("QPoint", name="show_object_tree_context_menu")
    def show_object_tree_context_menu(self, pos):
        """Context menu for object tree.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.treeView_object.indexAt(pos)
        global_pos = self.ui.treeView_object.viewport().mapToGlobal(pos)
        self.object_tree_context_menu = ObjectTreeContextMenu(self, global_pos, index)
        option = self.object_tree_context_menu.get_action()
        if option == "Copy":
            self.ui.treeView_object.copy()
        elif option == "Add object classes":
            self.show_add_object_classes_form()
        elif option == "Add objects":
            self.call_show_add_objects_form(index)
        elif option == "Add relationship classes":
            self.call_show_add_relationship_classes_form(index)
        elif option == "Add relationships":
            self.call_show_add_relationships_form(index)
        elif option == "Edit object classes":
            self.show_edit_object_classes_form()
        elif option == "Edit objects":
            self.show_edit_objects_form()
        elif option == "Edit relationship classes":
            self.show_edit_relationship_classes_form()
        elif option == "Edit relationships":
            self.show_edit_relationships_form()
        elif option == "Find next":
            self.find_next(index)
        elif option.startswith("Remove selected"):
            self.remove_object_tree_items()
        elif option == "Add parameter definitions":
            self.call_add_parameters(index)
        elif option == "Add parameter values":
            self.call_add_parameter_values(index)
        elif option == "Fully expand":
            self.fully_expand_selection()
        elif option == "Fully collapse":
            self.fully_collapse_selection()
        else:  # No option selected
            pass
        self.object_tree_context_menu.deleteLater()
        self.object_tree_context_menu = None

    def fully_expand_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            self.object_tree_model.forward_sweep(index, call=self.ui.treeView_object.expand)

    def fully_collapse_selection(self):
        for index in self.ui.treeView_object.selectionModel().selectedIndexes():
            self.object_tree_model.forward_sweep(index, call=self.ui.treeView_object.collapse)

    def call_show_add_objects_form(self, index):
        class_id = index.data(Qt.UserRole + 1)['id']
        self.show_add_objects_form(class_id=class_id)

    def call_show_add_relationship_classes_form(self, index):
        object_class_id = index.data(Qt.UserRole + 1)['id']
        self.show_add_relationship_classes_form(object_class_id=object_class_id)

    def call_show_add_relationships_form(self, index):
        relationship_class = index.data(Qt.UserRole + 1)
        object_ = index.parent().data(Qt.UserRole + 1)
        object_class = index.parent().parent().data(Qt.UserRole + 1)
        self.show_add_relationships_form(
            relationship_class_id=relationship_class['id'],
            object_id=object_['id'],
            object_class_id=object_class['id'])

    def call_add_parameters(self, tree_index):
        class_type = tree_index.data(Qt.UserRole)
        if class_type == 'object_class':
            self.add_object_parameter_definitions()
        elif class_type == 'relationship_class':
            self.add_relationship_parameter_definitions()

    def call_add_parameter_values(self, tree_index):
        entity_type = tree_index.data(Qt.UserRole)
        if entity_type == 'object':
            self.add_object_parameter_values()
        elif entity_type == 'relationship':
            self.add_relationship_parameter_values()

    def add_object_classes(self, object_classes):
        """Insert new object classes."""
        super().add_object_classes(object_classes)
        self.ui.actionExport.setEnabled(True)

    def edit_object_tree_items(self):
        """Called when F2 is pressed while the object tree has focus.
        Call the appropriate method to show the edit form,
        depending on the current index."""
        current = self.ui.treeView_object.currentIndex()
        current_type = current.data(Qt.UserRole)
        if current_type == 'object_class':
            self.show_edit_object_classes_form()
        elif current_type == 'object':
            self.show_edit_objects_form()
        elif current_type == 'relationship_class':
            self.show_edit_relationship_classes_form()
        elif current_type == 'relationship':
            self.show_edit_relationships_form()

    @busy_effect
    @Slot("bool", name="remove_object_tree_items")
    def remove_object_tree_items(self, checked=False):
        """Remove all selected items from the object treeview."""
        indexes = self.ui.treeView_object.selectionModel().selectedIndexes()
        if not indexes:
            return
        removed_items = {}
        for index in indexes:
            removed_type = index.data(Qt.UserRole)
            removed_item = index.data(Qt.UserRole + 1)
            removed_items.setdefault(removed_type, list()).append(removed_item)
        object_class_ids = set(x['id'] for x in removed_items.get('object_class', []))
        object_ids = set(x['id'] for x in removed_items.get('object', []))
        relationship_class_ids = set(x['id'] for x in removed_items.get('relationship_class', []))
        relationship_ids = set(x['id'] for x in removed_items.get('relationship', []))
        try:
            self.db_map.remove_items(
                object_class_ids=object_class_ids,
                object_ids=object_ids,
                relationship_class_ids=relationship_class_ids,
                relationship_ids=relationship_ids
            )
            self.object_tree_model.remove_items("object_class", object_class_ids)
            self.object_tree_model.remove_items("object", object_ids)
            self.object_tree_model.remove_items("relationship_class", relationship_class_ids)
            self.object_tree_model.remove_items("relationship", relationship_ids)
            # Parameter models
            self.object_parameter_value_model.remove_object_classes(removed_items.get('object_class', []))
            self.object_parameter_value_model.remove_objects(removed_items.get('object', []))
            self.object_parameter_definition_model.remove_object_classes(removed_items.get('object_class', []))
            self.relationship_parameter_value_model.remove_object_classes(removed_items.get('object_class', []))
            self.relationship_parameter_value_model.remove_objects(removed_items.get('object', []))
            self.relationship_parameter_value_model.remove_relationship_classes(
                removed_items.get('relationship_class', []))
            self.relationship_parameter_value_model.remove_relationships(removed_items.get('relationship', []))
            self.relationship_parameter_definition_model.remove_object_classes(removed_items.get('object_class', []))
            self.relationship_parameter_definition_model.remove_relationship_classes(
                removed_items.get('relationship_class', []))
            self.set_commit_rollback_actions_enabled(True)
            self.ui.actionExport.setEnabled(self.object_tree_model.root_item.hasChildren())
            self.msg.emit("Successfully removed items.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @Slot("QPoint", name="show_object_parameter_value_context_menu")
    def show_object_parameter_value_context_menu(self, pos):
        """Context menu for object parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_object_parameter_value.indexAt(pos)
        global_pos = self.ui.tableView_object_parameter_value.viewport().mapToGlobal(pos)
        remove_icon = self.ui.actionRemove_object_parameter_values.icon()
        self.object_parameter_value_context_menu = ParameterContextMenu(self, global_pos, index, remove_icon)
        option = self.object_parameter_value_context_menu.get_action()
        if option == "Remove selected":
            self.remove_object_parameter_values()
        elif option == "Copy":
            self.ui.tableView_object_parameter_value.copy()
        elif option == "Paste":
            self.ui.tableView_object_parameter_value.paste()
        self.object_parameter_value_context_menu.deleteLater()
        self.object_parameter_value_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_value_context_menu")
    def show_relationship_parameter_value_context_menu(self, pos):
        """Context menu for relationship parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_relationship_parameter_value.indexAt(pos)
        global_pos = self.ui.tableView_relationship_parameter_value.viewport().mapToGlobal(pos)
        remove_icon = self.ui.actionRemove_relationship_parameter_values.icon()
        self.relationship_parameter_value_context_menu = ParameterContextMenu(self, global_pos, index, remove_icon)
        option = self.relationship_parameter_value_context_menu.get_action()
        if option == "Remove selected":
            self.remove_relationship_parameter_values()
        elif option == "Copy":
            self.ui.tableView_relationship_parameter_value.copy()
        elif option == "Paste":
            self.ui.tableView_relationship_parameter_value.paste()
        self.relationship_parameter_value_context_menu.deleteLater()
        self.relationship_parameter_value_context_menu = None

    @Slot("QPoint", name="show_object_parameter_context_menu")
    def show_object_parameter_context_menu(self, pos):
        """Context menu for object parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_object_parameter_definition.indexAt(pos)
        global_pos = self.ui.tableView_object_parameter_definition.viewport().mapToGlobal(pos)
        remove_icon = self.ui.actionRemove_object_parameter_definitions.icon()
        self.object_parameter_context_menu = ParameterContextMenu(self, global_pos, index, remove_icon)
        option = self.object_parameter_context_menu.get_action()
        if option == "Remove selected":
            self.remove_object_parameter_definitions()
        elif option == "Copy":
            self.ui.tableView_object_parameter_definition.copy()
        elif option == "Paste":
            self.ui.tableView_object_parameter_definition.paste()
        self.object_parameter_context_menu.deleteLater()
        self.object_parameter_context_menu = None

    @Slot("QPoint", name="show_relationship_parameter_context_menu")
    def show_relationship_parameter_context_menu(self, pos):
        """Context menu for relationship parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        index = self.ui.tableView_relationship_parameter_definition.indexAt(pos)
        global_pos = self.ui.tableView_relationship_parameter_definition.viewport().mapToGlobal(pos)
        remove_icon = self.ui.actionRemove_relationship_parameter_definitions.icon()
        self.relationship_parameter_context_menu = ParameterContextMenu(self, global_pos, index, remove_icon)
        option = self.relationship_parameter_context_menu.get_action()
        if option == "Remove selected":
            self.remove_relationship_parameter_definitions()
        elif option == "Copy":
            self.ui.tableView_relationship_parameter_definition.copy()
        elif option == "Paste":
            self.ui.tableView_relationship_parameter_definition.paste()
        self.relationship_parameter_context_menu.deleteLater()
        self.relationship_parameter_context_menu = None

    @Slot(name="add_object_parameter_values")
    def add_object_parameter_values(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter value row if needed.
        """
        model = self.object_parameter_value_model
        index = self.ui.tableView_object_parameter_value.currentIndex()
        row = model.rowCount() - 1
        tree_selection = self.ui.treeView_object.selectionModel().selection()
        if not tree_selection.isEmpty():
            object_class_name_column = model.horizontal_header_labels().index('object_class_name')
            object_name_column = model.horizontal_header_labels().index('object_name')
            row_column_tuples = list()
            data = list()
            i = 0
            for tree_index in tree_selection.indexes():
                if tree_index.data(Qt.UserRole) == 'object_class':
                    object_class_name = tree_index.data(Qt.DisplayRole)
                    object_name = None
                elif tree_index.data(Qt.UserRole) == 'object':
                    object_class_name = tree_index.parent().data(Qt.DisplayRole)
                    object_name = tree_index.data(Qt.DisplayRole)
                else:
                    continue
                row_column_tuples.append((row + i, object_class_name_column))
                row_column_tuples.append((row + i, object_name_column))
                data.extend([object_class_name, object_name])
                i += 1
            if i > 0:
                model.insertRows(row, i)
                indexes = [model.index(row, column) for row, column in row_column_tuples]
                model.batch_set_data(indexes, data)
        self.ui.tabWidget_object_parameter.setCurrentIndex(0)
        model.update_filter()

    @Slot(name="add_relationship_parameter_values")
    def add_relationship_parameter_values(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter value row if needed.
        """
        model = self.relationship_parameter_value_model
        index = self.ui.tableView_relationship_parameter_value.currentIndex()
        row = model.rowCount() - 1
        tree_selection = self.ui.treeView_object.selectionModel().selection()
        if not tree_selection.isEmpty():
            relationship_class_name_column = model.horizontal_header_labels().index('relationship_class_name')
            object_name_list_column = model.horizontal_header_labels().index('object_name_list')
            row_column_tuples = list()
            data = list()
            i = 0
            for tree_index in tree_selection.indexes():
                if tree_index.data(Qt.UserRole) == 'relationship_class':
                    selected_object_class_name = tree_index.parent().parent().data(Qt.DisplayRole)
                    object_name = tree_index.parent().data(Qt.DisplayRole)
                    relationship_class_name = tree_index.data(Qt.DisplayRole)
                    object_class_name_list = tree_index.data(Qt.UserRole + 1)["object_class_name_list"].split(",")
                    object_name_list = list()
                    for object_class_name in object_class_name_list:
                        if object_class_name == selected_object_class_name:
                            object_name_list.append(object_name)
                        else:
                            object_name_list.append('')
                elif tree_index.data(Qt.UserRole) == 'relationship':
                    relationship_class_name = tree_index.parent().data(Qt.DisplayRole)
                    object_name_list = tree_index.data(Qt.UserRole + 1)["object_name_list"].split(",")
                else:
                    continue
                row_column_tuples.append((row + i, relationship_class_name_column))
                data.append(relationship_class_name)
                row_column_tuples.append((row + i, object_name_list_column))
                data.append(",".join(object_name_list))
                i += 1
            if i > 0:
                model.insertRows(row, i)
                indexes = [model.index(row, column) for row, column in row_column_tuples]
                model.batch_set_data(indexes, data)
        self.ui.tabWidget_relationship_parameter.setCurrentIndex(0)
        model.update_filter()

    @Slot(name="add_object_parameter_definitions")
    def add_object_parameter_definitions(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter value row if needed.
        """
        model = self.object_parameter_definition_model
        index = self.ui.tableView_object_parameter_definition.currentIndex()
        row = model.rowCount() - 1
        tree_selection = self.ui.treeView_object.selectionModel().selection()
        if not tree_selection.isEmpty():
            object_class_name_column = model.horizontal_header_labels().index('object_class_name')
            row_column_tuples = list()
            data = list()
            i = 0
            for tree_index in tree_selection.indexes():
                if tree_index.data(Qt.UserRole) == 'object_class':
                    object_class_name = tree_index.data(Qt.DisplayRole)
                elif tree_index.data(Qt.UserRole) == 'object':
                    object_class_name = tree_index.parent().data(Qt.DisplayRole)
                else:
                    continue
                row_column_tuples.append((row + i, object_class_name_column))
                data.append(object_class_name)
                i += 1
            if i > 0:
                model.insertRows(row, i)
                indexes = [model.index(row, column) for row, column in row_column_tuples]
                model.batch_set_data(indexes, data)
        self.ui.tabWidget_object_parameter.setCurrentIndex(1)
        model.update_filter()

    @Slot(name="add_relationship_parameter_definitions")
    def add_relationship_parameter_definitions(self):
        """Sweep object treeview selection.
        For each item in the selection, add a parameter row if needed.
        """
        model = self.relationship_parameter_definition_model
        index = self.ui.tableView_relationship_parameter_definition.currentIndex()
        row = model.rowCount() - 1
        tree_selection = self.ui.treeView_object.selectionModel().selection()
        if not tree_selection.isEmpty():
            relationship_class_name_column = model.horizontal_header_labels().index('relationship_class_name')
            row_column_tuples = list()
            data = list()
            i = 0
            for tree_index in tree_selection.indexes():
                if tree_index.data(Qt.UserRole) == 'relationship_class':
                    relationship_class_name = tree_index.data(Qt.DisplayRole)
                elif tree_index.data(Qt.UserRole) == 'relationship':
                    relationship_class_name = tree_index.parent().data(Qt.DisplayRole)
                else:
                    continue
                row_column_tuples.append((row + i, relationship_class_name_column))
                data.append(relationship_class_name)
                i += 1
            if i > 0:
                model.insertRows(row, i)
                indexes = [model.index(row, column) for row, column in row_column_tuples]
                model.batch_set_data(indexes, data)
        self.ui.tabWidget_relationship_parameter.setCurrentIndex(1)
        model.update_filter()

    @busy_effect
    @Slot(name="remove_object_parameter_values")
    def remove_object_parameter_values(self):
        """Remove selected rows from object parameter value table."""
        selection = self.ui.tableView_object_parameter_value.selectionModel().selection()
        row_dict = dict()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_dict[top] = bottom - top + 1
        model = self.object_parameter_value_model
        id_column = model.horizontal_header_labels().index("id")
        parameter_value_ids = set()
        for row, count in row_dict.items():
            parameter_value_ids.update(model.index(i, id_column).data() for i in range(row, row + count))
        try:
            self.db_map.remove_items(parameter_value_ids=parameter_value_ids)
            for row in reversed(sorted(row_dict)):
                count = row_dict[row]
                self.object_parameter_value_model.removeRows(row, count)
            self.set_commit_rollback_actions_enabled(True)
            self.msg.emit("Successfully removed parameter values.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    @Slot(name="remove_relationship_parameter_values")
    def remove_relationship_parameter_values(self):
        """Remove selected rows from relationship parameter value table."""
        selection = self.ui.tableView_relationship_parameter_value.selectionModel().selection()
        row_dict = dict()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_dict[top] = bottom - top + 1
        model = self.relationship_parameter_value_model
        id_column = model.horizontal_header_labels().index("id")
        parameter_value_ids = set()
        for row, count in row_dict.items():
            parameter_value_ids.update(model.index(i, id_column).data() for i in range(row, row + count))
        try:
            self.db_map.remove_items(parameter_value_ids=parameter_value_ids)
            for row in reversed(sorted(row_dict)):
                count = row_dict[row]
                self.relationship_parameter_value_model.removeRows(row, count)
            self.set_commit_rollback_actions_enabled(True)
            self.msg.emit("Successfully removed parameter values.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    @Slot("bool", name="remove_object_parameter_definitions")
    def remove_object_parameter_definitions(self, checked=False):
        """Remove selected rows from object parameter definition table."""
        selection = self.ui.tableView_object_parameter_definition.selectionModel().selection()
        row_dict = dict()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_dict[top] = bottom - top + 1
        model = self.object_parameter_definition_model
        parameter_ids = set()
        parameter_dict = dict()
        header = model.horizontal_header_labels()
        object_class_id_column = header.index("object_class_id")
        id_column = header.index("id")
        for row, count in row_dict.items():
            for i in range(row, row + count):
                object_class_id = model.index(i, object_class_id_column).data(Qt.DisplayRole)
                id_ = model.index(i, id_column).data(Qt.DisplayRole)
                parameter_ids.add(id_)
                parameter_dict.setdefault(object_class_id, set()).add(id_)
        try:
            self.db_map.remove_items(parameter_ids=parameter_ids)
            for row in reversed(sorted(row_dict)):
                count = row_dict[row]
                self.object_parameter_definition_model.removeRows(row, count)
            self.object_parameter_value_model.remove_parameters(parameter_dict)
            self.set_commit_rollback_actions_enabled(True)
            self.msg.emit("Successfully removed parameter definitions.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    @busy_effect
    @Slot("bool", name="remove_relationship_parameter_definitions")
    def remove_relationship_parameter_definitions(self, checked=False):
        """Remove selected rows from relationship parameter definition table."""
        selection = self.ui.tableView_relationship_parameter_definition.selectionModel().selection()
        row_dict = dict()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_dict[top] = bottom - top + 1
        model = self.relationship_parameter_definition_model
        parameter_ids = set()
        parameter_dict = dict()
        header = model.horizontal_header_labels()
        relationship_class_id_column = header.index("relationship_class_id")
        id_column = header.index("id")
        for row, count in row_dict.items():
            for i in range(row, row + count):
                relationship_class_id = model.index(i, relationship_class_id_column).data(Qt.DisplayRole)
                id_ = model.index(i, id_column).data(Qt.DisplayRole)
                parameter_ids.add(id_)
                parameter_dict.setdefault(relationship_class_id, set()).add(id_)
        try:
            self.db_map.remove_items(parameter_ids=parameter_ids)
            for row in reversed(sorted(row_dict)):
                count = row_dict[row]
                self.relationship_parameter_definition_model.removeRows(row, count)
            self.relationship_parameter_value_model.remove_parameters(parameter_dict)
            self.set_commit_rollback_actions_enabled(True)
            self.msg.emit("Successfully removed parameter definitions.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    def restore_ui(self):
        """Restore UI state from previous session."""
        super().restore_ui()
        splitter_tree_parameter_state = self.qsettings().value("treeViewWidget/splitterTreeParameterState")
        if splitter_tree_parameter_state:
            self.ui.splitter_tree_parameter.restoreState(splitter_tree_parameter_state)

    def close_editors(self):
        """Close any open editor in the parameter table views.
        Call this before closing the database mapping."""
        current = self.ui.tableView_object_parameter_definition.currentIndex()
        if self.ui.tableView_object_parameter_definition.isPersistentEditorOpen(current):
            self.ui.tableView_object_parameter_definition.closePersistentEditor(current)
        current = self.ui.tableView_object_parameter_value.currentIndex()
        if self.ui.tableView_object_parameter_value.isPersistentEditorOpen(current):
            self.ui.tableView_object_parameter_value.closePersistentEditor(current)
        current = self.ui.tableView_relationship_parameter_definition.currentIndex()
        if self.ui.tableView_relationship_parameter_definition.isPersistentEditorOpen(current):
            self.ui.tableView_relationship_parameter_definition.closePersistentEditor(current)
        current = self.ui.tableView_relationship_parameter_value.currentIndex()
        if self.ui.tableView_relationship_parameter_value.isPersistentEditorOpen(current):
            self.ui.tableView_relationship_parameter_value.closePersistentEditor(current)

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        super().closeEvent(event)
        self.qsettings().setValue(
            "{}/splitterTreeParameterState".format(self.settings_key),
            self.ui.splitter_tree_parameter.saveState())
        self.close_editors()


class GraphViewForm(DataStoreForm):
    """A widget to show the graph view.

    Attributes:
        owner (View or Data Store): View or DataStore instance
        db_map (DiffDatabaseMapping): The object relational database mapping
        database (str): The database name
        read_only (bool): Whether or not the form should be editable
    """
    def __init__(self, owner, db_map, database, read_only=False):
        """Initialize class."""
        tic = time.clock()
        super().__init__(owner, db_map, database, graph_view_form_ui())
        self.ui.graphicsView._graph_view_form = self
        self.read_only = read_only
        self._has_graph = False
        self._scene_bg = None
        self.font = QApplication.font()
        self.font.setPointSize(72)
        self.font_metric = QFontMetrics(self.font)
        self.extent = 6 * self.font.pointSize()
        self._spread = 3 * self.extent
        self.object_label_color = self.palette().color(QPalette.Normal, QPalette.Window)
        self.object_label_color.setAlphaF(.5)
        self.arc_label_color = self.palette().color(QPalette.Normal, QPalette.Window)
        self.arc_label_color.setAlphaF(.8)
        self.arc_color = self.palette().color(QPalette.Normal, QPalette.WindowText)
        self.arc_color.setAlphaF(.75)
        # Set flat object tree
        self.object_tree_model.is_flat = True
        # Data for ObjectItems
        self.object_ids = list()
        self.object_names = list()
        self.object_class_ids = list()
        self.object_class_names = list()
        # Data for ArcItems
        self.arc_object_id_lists = list()
        self.arc_relationship_class_ids = list()
        self.arc_object_class_name_lists = list()
        self.arc_label_object_name_lists = list()
        self.arc_label_object_class_name_lists = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        # Data for template ObjectItems and ArcItems (these are persisted across graph builds)
        self.heavy_positions = {}
        self.is_template = {}
        self.template_id_dims = {}
        self.arc_template_ids = {}
        # Data of relationship templates
        self.template_id = 1
        self.relationship_class_dict = {}  # template_id => relationship_class_name, relationship_class_id
        # Icon dicts
        self.object_class_list_model = ObjectClassListModel(self)
        self.relationship_class_list_model = RelationshipClassListModel(self)
        # Context menus
        self.object_item_context_menu = None
        self.graph_view_context_menu = None
        # Hidden and rejected items
        self.hidden_items = list()
        self.rejected_items = list()
        # Current item selection
        self.object_item_selection = list()
        self.arc_item_selection = list()
        # Zoom widget and action
        self.zoom_widget_action = None
        self.zoom_widget = None
        # Set up splitters
        area = self.dockWidgetArea(self.ui.dockWidget_parameter)
        self._handle_parameter_dock_location_changed(area)
        area = self.dockWidgetArea(self.ui.dockWidget_item_palette)
        self._handle_item_palette_dock_location_changed(area)
        # Initialize stuff
        self.init_models()
        self.init_views()
        self.setup_delegates()
        self.create_add_more_actions()
        self.setup_zoom_action()
        self.connect_signals()
        self.settings_key = "graphViewWidget" if not self.read_only else "graphViewWidgetReadOnly"
        self.restore_ui()
        self.add_toggle_view_actions()
        self.init_commit_rollback_actions()
        title = database + " (read only) " if read_only else database
        self.setWindowTitle("Data store graph view    -- {} --".format(title))
        toc = time.clock()
        self.msg.emit("Graph view form created in {} seconds\t".format(toc - tic))

    def show(self):
        """Show usage message together with the form."""
        super().show()
        self.show_usage_msg()

    def init_models(self):
        """Initialize models."""
        super().init_models()
        self.object_class_list_model.populate_list()
        self.relationship_class_list_model.populate_list()

    def init_object_tree_model(self):
        """Initialize object tree model."""
        self.object_tree_model.build_tree(self.database)

    def init_parameter_value_models(self):
        """Initialize parameter value models from source database."""
        self.object_parameter_value_model.has_empty_row = not self.read_only
        self.relationship_parameter_value_model.has_empty_row = not self.read_only
        super().init_parameter_value_models()

    def init_parameter_definition_models(self):
        """Initialize parameter (definition) models from source database."""
        self.object_parameter_definition_model.has_empty_row = not self.read_only
        self.relationship_parameter_definition_model.has_empty_row = not self.read_only
        super().init_parameter_definition_models()

    def init_views(self):
        super().init_views()
        self.ui.listView_object_class.setModel(self.object_class_list_model)
        self.ui.listView_relationship_class.setModel(self.relationship_class_list_model)

    def setup_zoom_action(self):
        """Setup zoom action in view menu."""
        self.zoom_widget = ZoomWidget(self)
        self.zoom_widget_action = QWidgetAction(self)
        self.zoom_widget_action.setDefaultWidget(self.zoom_widget)
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.zoom_widget_action)

    def create_add_more_actions(self):
        """Create and 'Add more' action and button for the Item Palette views."""
        # object class
        index = self.object_class_list_model.add_more_index
        action = QAction()
        icon = QIcon(":/icons/plus_object_icon.png")
        action.setIcon(icon)
        action.setText(index.data(Qt.DisplayRole))
        button = QToolButton()
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)
        button.setIconSize(QSize(32, 32))
        button.setFixedSize(64, 56)
        self.ui.listView_object_class.setIndexWidget(index, button)
        action.triggered.connect(self.show_add_object_classes_form)
        # relationship class
        index = self.relationship_class_list_model.add_more_index
        action = QAction()
        icon = QIcon(":/icons/plus_relationship_icon.png")
        action.setIcon(icon)
        action.setText(index.data(Qt.DisplayRole))
        button = QToolButton()
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)
        button.setIconSize(QSize(32, 32))
        button.setFixedSize(64, 56)
        self.ui.listView_relationship_class.setIndexWidget(index, button)
        action.triggered.connect(self.show_add_relationship_classes_form)

    def connect_signals(self):
        """Connect signals."""
        super().connect_signals()
        self.ui.graphicsView.item_dropped.connect(self._handle_item_dropped)
        self.ui.dockWidget_parameter.dockLocationChanged.connect(self._handle_parameter_dock_location_changed)
        self.ui.dockWidget_item_palette.dockLocationChanged.connect(self._handle_item_palette_dock_location_changed)
        self.ui.actionGraph_hide_selected.triggered.connect(self.hide_selected_items)
        self.ui.actionGraph_show_hidden.triggered.connect(self.show_hidden_items)
        self.ui.actionGraph_prune_selected.triggered.connect(self.prune_selected_items)
        self.ui.actionGraph_reinstate_pruned.triggered.connect(self.reinstate_pruned_items)
        self.ui.menuGraph.aboutToShow.connect(self._handle_menu_about_to_show)
        self.zoom_widget_action.hovered.connect(self._handle_zoom_widget_action_hovered)
        self.zoom_widget.minus_pressed.connect(self._handle_zoom_widget_minus_pressed)
        self.zoom_widget.plus_pressed.connect(self._handle_zoom_widget_plus_pressed)
        self.zoom_widget.reset_pressed.connect(self._handle_zoom_widget_reset_pressed)

    @Slot(name="_handle_zoom_widget_minus_pressed")
    def _handle_zoom_widget_minus_pressed(self):
        self.ui.graphicsView.zoom_out()

    @Slot(name="_handle_zoom_widget_plus_pressed")
    def _handle_zoom_widget_plus_pressed(self):
        self.ui.graphicsView.zoom_in()

    @Slot(name="_handle_zoom_widget_reset_pressed")
    def _handle_zoom_widget_reset_pressed(self):
        self.ui.graphicsView.reset_zoom()

    @Slot(name="_handle_zoom_widget_action_hovered")
    def _handle_zoom_widget_action_hovered(self):
        """Called when the zoom widget action is hovered. Hide the 'Dock widgets' submenu in case
        it's being shown. This is the default behavior for hovering 'normal' `QAction`s, but for some reason
        it's not the case for hovering `QWidgetAction`s."""
        self.ui.menuDock_Widgets.hide()

    @Slot(name="_handle_menu_about_to_show")
    def _handle_menu_about_to_show(self):
        """Called when a menu from the menubar is about to show."""
        self.ui.actionGraph_hide_selected.setEnabled(len(self.object_item_selection) > 0)
        self.ui.actionGraph_show_hidden.setEnabled(len(self.hidden_items) > 0)
        self.ui.actionGraph_prune_selected.setEnabled(len(self.object_item_selection) > 0)
        self.ui.actionGraph_reinstate_pruned.setEnabled(len(self.rejected_items) > 0)

    @Slot("Qt.DockWidgetArea", name="_handle_parameter_dock_location_changed")
    def _handle_parameter_dock_location_changed(self, area):
        """Called when the parameter dock widget location changes.
        Adjust splitter orientation accordingly."""
        if area & (Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea):
            self.ui.splitter_object_relationship_parameter.setOrientation(Qt.Vertical)
        else:
            self.ui.splitter_object_relationship_parameter.setOrientation(Qt.Horizontal)

    @Slot("Qt.DockWidgetArea", name="_handle_item_palette_dock_location_changed")
    def _handle_item_palette_dock_location_changed(self, area):
        """Called when the item palette dock widget location changes.
        Adjust splitter orientation accordingly."""
        if area & (Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea):
            self.ui.splitter_object_relationship_class.setOrientation(Qt.Vertical)
        else:
            self.ui.splitter_object_relationship_class.setOrientation(Qt.Horizontal)

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_object_tree.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_parameter.toggleViewAction())
        if not self.read_only:
            self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item_palette.toggleViewAction())
        else:
            self.ui.dockWidget_item_palette.hide()

    def init_commit_rollback_actions(self):
        if not self.read_only:
            self.set_commit_rollback_actions_enabled(False)
        else:
            self.ui.menuSession.removeAction(self.ui.actionCommit)
            self.ui.menuSession.removeAction(self.ui.actionRollback)

    @busy_effect
    @Slot("bool", name="build_graph")
    def build_graph(self, checked=True):
        """Initialize graph data and build graph."""
        tic = time.clock()
        self.init_graph_data()
        self._has_graph = self.make_graph()
        if self._has_graph:
            self.ui.graphicsView.scale_to_fit_scene()
            self.extend_scene_bg()
            toc = time.clock()
            self.msg.emit("Graph built in {} seconds\t".format(toc - tic))
        else:
            self.show_usage_msg()
        self.hidden_items = list()

    @Slot("QItemSelection", "QItemSelection", name="_handle_object_tree_selection_changed")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Build_graph."""
        self.build_graph()

    def init_graph_data(self):
        """Initialize graph data."""
        rejected_object_names = [x.object_name for x in self.rejected_items]
        self.object_ids = list()
        self.object_names = list()
        self.object_class_ids = list()
        self.object_class_names = list()
        root_item = self.object_tree_model.root_item
        index = self.object_tree_model.indexFromItem(root_item)
        is_root_selected = self.ui.treeView_object.selectionModel().isSelected(index)
        for i in range(root_item.rowCount()):
            object_class_item = root_item.child(i, 0)
            object_class_id = object_class_item.data(Qt.UserRole + 1)['id']
            object_class_name = object_class_item.data(Qt.UserRole + 1)['name']
            index = self.object_tree_model.indexFromItem(object_class_item)
            is_object_class_selected = self.ui.treeView_object.selectionModel().isSelected(index)
            # Fetch object class if needed
            if is_root_selected or is_object_class_selected:
                if self.object_tree_model.canFetchMore(index):
                    self.object_tree_model.fetchMore(index)
            for j in range(object_class_item.rowCount()):
                object_item = object_class_item.child(j, 0)
                object_id = object_item.data(Qt.UserRole + 1)["id"]
                object_name = object_item.data(Qt.UserRole + 1)["name"]
                if object_name in rejected_object_names:
                    continue
                index = self.object_tree_model.indexFromItem(object_item)
                is_object_selected = self.ui.treeView_object.selectionModel().isSelected(index)
                if is_root_selected or is_object_class_selected or is_object_selected:
                    self.object_ids.append(object_id)
                    self.object_names.append(object_name)
                    self.object_class_ids.append(object_class_id)
                    self.object_class_names.append(object_class_name)
        self.arc_object_id_lists = list()
        self.arc_relationship_class_ids = list()
        self.arc_object_class_name_lists = list()
        self.arc_label_object_name_lists = list()
        self.arc_label_object_class_name_lists = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        relationship_class_dict = {
            x.id: {
                "name": x.name,
                "object_class_name_list": x.object_class_name_list
            } for x in self.db_map.wide_relationship_class_list()
        }
        for relationship in self.db_map.wide_relationship_list():
            object_class_name_list = relationship_class_dict[relationship.class_id]["object_class_name_list"]
            split_object_class_name_list = object_class_name_list.split(",")
            object_id_list = relationship.object_id_list
            split_object_id_list = [int(x) for x in object_id_list.split(",")]
            split_object_name_list = relationship.object_name_list.split(",")
            for i in range(len(split_object_id_list)):
                src_object_id = split_object_id_list[i]
                try:
                    dst_object_id = split_object_id_list[i + 1]
                except IndexError:
                    dst_object_id = split_object_id_list[0]
                try:
                    src_ind = self.object_ids.index(src_object_id)
                    dst_ind = self.object_ids.index(dst_object_id)
                except ValueError:
                    continue
                self.src_ind_list.append(src_ind)
                self.dst_ind_list.append(dst_ind)
                src_object_name = self.object_names[src_ind]
                dst_object_name = self.object_names[dst_ind]
                self.arc_object_id_lists.append(object_id_list)
                self.arc_relationship_class_ids.append(relationship.class_id)
                self.arc_object_class_name_lists.append(object_class_name_list)
                # Find out label items
                arc_label_object_name_list = list()
                arc_label_object_class_name_list = list()
                for object_name, object_class_name in zip(split_object_name_list, split_object_class_name_list):
                    if object_name in (src_object_name, dst_object_name):
                        continue
                    arc_label_object_name_list.append(object_name)
                    arc_label_object_class_name_list.append(object_class_name)
                self.arc_label_object_name_lists.append(arc_label_object_name_list)
                self.arc_label_object_class_name_lists.append(arc_label_object_class_name_list)
        # Add template items hanging around
        scene = self.ui.graphicsView.scene()
        if not scene:
            return
        self.heavy_positions = {}
        template_object_items = [x for x in scene.items() if isinstance(x, ObjectItem) and x.template_id_dim]
        object_ind = len(self.object_ids)
        self.template_id_dims = {}
        self.is_template = {}
        object_ind_dict = {}  # Dict of object indexes added from this point
        object_ids_copy = self.object_ids.copy()  # Object ids added until this point
        for item in template_object_items:
            object_id = item.object_id
            object_name = item.object_name
            try:
                found_ind = object_ids_copy.index(object_id)
                # Object id is already in list; complete its template information and make it heavy
                self.template_id_dims[found_ind] = item.template_id_dim
                self.is_template[found_ind] = False
                self.heavy_positions[found_ind] = item.pos()
            except ValueError:
                # Object id is not in list; add it together with its template info, and make it heavy
                object_class_id = item.object_class_id
                object_class_name = item.object_class_name
                self.object_ids.append(object_id)
                self.object_names.append(object_name)
                self.object_class_ids.append(object_class_id)
                self.object_class_names.append(object_class_name)
                self.template_id_dims[object_ind] = item.template_id_dim
                self.is_template[object_ind] = item.is_template
                self.heavy_positions[object_ind] = item.pos()
                object_ind_dict[item] = object_ind
                object_ind += 1
        template_arc_items = [x for x in scene.items() if isinstance(x, ArcItem) and x.is_template]
        arc_ind = len(self.arc_label_object_name_lists)
        self.arc_template_ids = {}
        for item in template_arc_items:
            src_item = item.src_item
            dst_item = item.dst_item
            try:
                src_ind = object_ind_dict[src_item]
            except KeyError:
                src_object_id = src_item.object_id
                src_ind = self.object_ids.index(src_object_id)
            try:
                dst_ind = object_ind_dict[dst_item]
            except KeyError:
                dst_object_id = dst_item.object_id
                dst_ind = self.object_ids.index(dst_object_id)
            self.src_ind_list.append(src_ind)
            self.dst_ind_list.append(dst_ind)
            # NOTE: These arcs correspond to template arcs.
            relationship_class_id = item.relationship_class_id
            object_class_name_list = item.object_class_name_list
            self.arc_object_id_lists.append("")  # TODO: is this one filled when creating the relationship?
            self.arc_relationship_class_ids.append(relationship_class_id)
            self.arc_object_class_name_lists.append(object_class_name_list)
            # Label don't matter
            self.arc_label_object_name_lists.append("")
            self.arc_label_object_class_name_lists.append("")
            self.arc_template_ids[arc_ind] = item.template_id
            arc_ind += 1

    def shortest_path_matrix(self, object_name_list, src_ind_list, dst_ind_list, spread):
        """Return the shortest-path matrix."""
        N = len(object_name_list)
        if not N:
            return None
        dist = np.zeros((N, N))
        src_ind = arr(src_ind_list)
        dst_ind = arr(dst_ind_list)
        try:
            dist[src_ind, dst_ind] = dist[dst_ind, src_ind] = spread
        except IndexError:
            pass
        d = dijkstra(dist, directed=False)
        # Remove infinites and zeros
        d[d == np.inf] = spread * 3
        d[d == 0] = spread * 1e-6
        return d

    def sets(self, N):
        """Return sets of vertex pairs indices."""
        sets = []
        for n in range(1, N):
            pairs = np.zeros((N - n, 2), int)  # pairs on diagonal n
            pairs[:, 0] = np.arange(N - n)
            pairs[:, 1] = pairs[:, 0] + n
            mask = np.mod(range(N - n), 2 * n) < n
            s1 = pairs[mask]
            s2 = pairs[~mask]
            if len(s1) > 0:
                sets.append(s1)
            if len(s2) > 0:
                sets.append(s2)
        return sets

    def vertex_coordinates(self, matrix, heavy_positions={}, iterations=10, weight_exp=-2, initial_diameter=1000):
        """Return x and y coordinates for each vertex in the graph, computed using VSGD-MS."""
        N = len(matrix)
        if N == 1:
            return [0], [0]
        mask = np.ones((N, N)) == 1 - np.tril(np.ones((N, N)))  # Upper triangular except diagonal
        np.random.seed(0)
        layout = np.random.rand(N, 2) * initial_diameter - initial_diameter / 2  # Random layout with initial diameter
        heavy_ind_list = list()
        heavy_pos_list = list()
        for ind, pos in heavy_positions.items():
            heavy_ind_list.append(ind)
            heavy_pos_list.append([pos.x(), pos.y()])
        heavy_ind = arr(heavy_ind_list)
        heavy_pos = arr(heavy_pos_list)
        if heavy_ind.any():
            layout[heavy_ind, :] = heavy_pos
        weights = matrix ** weight_exp  # bus-pair weights (lower for distant buses)
        maxstep = 1 / np.min(weights[mask])
        minstep = 1 / np.max(weights[mask])
        lambda_ = np.log(minstep / maxstep) / (iterations - 1)  # exponential decay of allowed adjustment
        sets = self.sets(N)  # construct sets of bus pairs
        for iteration in range(iterations):
            step = maxstep * np.exp(lambda_ * iteration)  # how big adjustments are allowed?
            rand_order = np.random.permutation(N)  # we don't want to use the same pair order each iteration
            for p in sets:
                v1, v2 = rand_order[p[:, 0]], rand_order[p[:, 1]]  # arrays of vertex1 and vertex2
                # current distance (possibly accounting for system rescaling)
                dist = ((layout[v1, 0] - layout[v2, 0]) ** 2 + (layout[v1, 1] - layout[v2, 1]) ** 2) ** 0.5
                r = (matrix[v1, v2] - dist)[:, None] / 2 * (layout[v1] - layout[v2]) / dist[:, None]  # desired change
                dx1 = r * np.minimum(1, weights[v1, v2] * step)[:, None]
                dx2 = -dx1
                layout[v1, :] += dx1  # update position
                layout[v2, :] += dx2
                if heavy_ind.any():
                    layout[heavy_ind, :] = heavy_pos
        return layout[:, 0], layout[:, 1]

    def make_graph(self):
        """Make graph."""
        d = self.shortest_path_matrix(self.object_names, self.src_ind_list, self.dst_ind_list, self._spread)
        if d is None:
            return False
        scene = self.new_scene()
        x, y = self.vertex_coordinates(d, self.heavy_positions)
        object_items = list()
        for i in range(len(self.object_names)):
            object_id = self.object_ids[i]
            object_name = self.object_names[i]
            object_class_id = self.object_class_ids[i]
            object_class_name = self.object_class_names[i]
            object_item = ObjectItem(
                self, object_id, object_name, object_class_id, object_class_name,
                x[i], y[i], self.extent, label_font=self.font, label_color=self.object_label_color)
            try:
                template_id_dim = self.template_id_dims[i]
                object_item.template_id_dim = template_id_dim
                if self.is_template[i]:
                    object_item.make_template()
            except KeyError:
                pass
            scene.addItem(object_item)
            object_items.append(object_item)
        for k in range(len(self.src_ind_list)):
            i = self.src_ind_list[k]
            j = self.dst_ind_list[k]
            object_id_list = self.arc_object_id_lists[k]
            relationship_class_id = self.arc_relationship_class_ids[k]
            object_class_names = self.arc_object_class_name_lists[k]
            label_object_names = self.arc_label_object_name_lists[k]
            label_object_class_names = self.arc_label_object_class_name_lists[k]
            label_parts = self.relationship_graph(
                label_object_names, label_object_class_names, self.extent, self._spread / 2,
                label_font=self.font, label_color=Qt.transparent, # label_color=self.object_label_color
                relationship_class_id=relationship_class_id)
            arc_item = ArcItem(
                self, object_id_list, relationship_class_id, label_object_class_names, # object_class_names,
                object_items[i], object_items[j], .25 * self.extent, self.arc_color,
                token_color=self.object_label_color, label_color=self.arc_label_color, label_parts=label_parts)
            try:
                template_id = self.arc_template_ids[k]
                arc_item.template_id = template_id
                arc_item.make_template()
            except KeyError:
                pass
            scene.addItem(arc_item)
        return True

    def new_scene(self):
        """A new scene with a background."""
        old_scene = self.ui.graphicsView.scene()
        if old_scene:
            old_scene.deleteLater()
        self._scene_bg = QGraphicsRectItem()
        self._scene_bg.setPen(Qt.NoPen)
        self._scene_bg.setZValue(-100)
        scene = QGraphicsScene()
        self.ui.graphicsView.setScene(scene)
        scene.addItem(self._scene_bg)
        scene.changed.connect(self._handle_scene_changed)
        scene.selectionChanged.connect(self._handle_scene_selection_changed)
        return scene

    def extend_scene_bg(self):
        # Make scene background the size of the view
        view_rect = self.ui.graphicsView.viewport().rect()
        top_left = self.ui.graphicsView.mapToScene(view_rect.topLeft())
        bottom_right = self.ui.graphicsView.mapToScene(view_rect.bottomRight())
        rectf = QRectF(top_left, bottom_right)
        self._scene_bg.setRect(rectf)

    @Slot(name="_handle_scene_selection_changed")
    def _handle_scene_selection_changed(self):
        """Show parameters for selected items."""
        scene = self.ui.graphicsView.scene()  # TODO: should we use sender() here?
        selected_items = scene.selectedItems()
        self.object_item_selection = [x for x in selected_items if isinstance(x, ObjectItem)]
        self.arc_item_selection = [x for x in selected_items if isinstance(x, ArcItem)]
        self.selected_object_class_ids = set()
        self.selected_object_ids = dict()
        self.selected_relationship_class_ids = set()
        self.selected_object_id_lists = dict()
        for item in selected_items:
            if isinstance(item, ObjectItem):
                self.selected_object_class_ids.add(item.object_class_id)
                self.selected_object_ids.setdefault(item.object_class_id, set()).add(item.object_id)
            elif isinstance(item, ArcItem):
                self.selected_relationship_class_ids.add(item.relationship_class_id)
                self.selected_object_id_lists.setdefault(item.relationship_class_id, set()).add(item.object_id_list)
        if self.ui.tabWidget_object_parameter.currentIndex() == 0:
            self.object_parameter_value_model.update_filter()
        else:
            self.object_parameter_definition_model.update_filter()
        if self.ui.tabWidget_relationship_parameter.currentIndex() == 0:
            self.relationship_parameter_value_model.update_filter()
        else:
            self.relationship_parameter_definition_model.update_filter()

    @Slot("QList<QRectF>", name="_handle_scene_changed")
    def _handle_scene_changed(self, region):
        """Handle scene changed. Show usage message if no items other than the bg.
        """
        if len(self.ui.graphicsView.scene().items()) > 1:  # TODO: should we use sender() here?
            return
        self.show_usage_msg()

    def show_usage_msg(self):
        """Show usage instructions in new scene.
        """
        scene = self.new_scene()
        usage = """
            <html>
            <head>
            <style type="text/css">
            ol {
                margin-left: 80px;
                padding-left: 0px;
            }
            ul {
                margin-left: 40px;
                padding-left: 0px;
            }
            </style>
            </head>
            <h3>Usage:</h3>
            <ol>
            <li>Select items in <a href="Object tree">Object tree</a> to show objects here.
                <ul>
                <li>Hold down the 'Ctrl' key or just drag your mouse to add multiple items to the selection.</li>
                <li>Selected objects are vertices in the graph,
                while relationships between those objects are edges.
                </ul>
            </li>
            <li>Select items here to show their parameters in <a href="Parameter dock">Parameter dock</a>.
                <ul>
                <li>Hold down 'Ctrl' to add multiple items to the selection.</li>
                <li> Hold down 'Ctrl' and drag your mouse to perform a rubber band selection.</li>
                </ul>
            </li>
        """
        if not self.read_only:
            usage += """
                <li>Drag icons from <a href="Item palette">Item palette</a>
                and drop them here to create new items.</li>
            """
        usage += """
            </ol>
            </html>
        """
        usage_item = CustomTextItem(usage, self.font)
        usage_item.linkActivated.connect(self._handle_usage_link_activated)
        scene.addItem(usage_item)
        self._has_graph = False
        self.ui.graphicsView.scale_to_fit_scene()

    @Slot("QString", name="_handle_usage_link_activated")
    def _handle_usage_link_activated(self, link):
        if link == "Object tree":
            self.ui.dockWidget_object_tree.show()
        elif link == "Parameter dock":
            self.ui.dockWidget_parameter.show()
        elif link == "Item palette":
            self.ui.dockWidget_item_palette.show()

    @Slot("QPoint", "QString", name="_handle_item_dropped")
    def _handle_item_dropped(self, pos, text):
        if self._has_graph:
            scene = self.ui.graphicsView.scene()
        else:
            scene = self.new_scene()
        self.extend_scene_bg()
        scene_pos = self.ui.graphicsView.mapToScene(pos)
        data = eval(text)
        if data["type"] == "object_class":
            class_id = data["id"]
            class_name = data["name"]
            name = class_name
            object_item = ObjectItem(
                self, 0, name, class_id, class_name, scene_pos.x(), scene_pos.y(), self.extent,
                label_font=self.font, label_color=self.object_label_color)
            scene.addItem(object_item)
            object_item.make_template()
        elif data["type"] == "relationship_class":
            relationship_class_id = data["id"]
            object_class_id_list = [int(x) for x in data["object_class_id_list"].split(',')]
            object_class_name_list = data["object_class_name_list"].split(',')
            object_name_list = object_class_name_list.copy()
            fix_name_ambiguity(object_name_list)
            relationship_graph = self.relationship_graph(
                object_name_list, object_class_name_list, self.extent, self._spread,
                label_font=self.font, label_color=self.object_label_color,
                object_class_id_list=object_class_id_list, relationship_class_id=relationship_class_id)
            self.add_relationship_template(scene, scene_pos.x(), scene_pos.y(), *relationship_graph)
            self.relationship_class_dict[self.template_id] = {"id": data["id"], "name": data["name"]}
            self.template_id += 1
        self._has_graph = True

    def add_relationship_template(self, scene, x, y, object_items, arc_items, dimension_at_origin=None):
        """Add relationship parts into the scene to form a 'relationship template'."""
        for item in object_items + arc_items:
            scene.addItem(item)
        # Make template
        for dimension, object_item in enumerate(object_items):
            object_item.template_id_dim[self.template_id] = dimension
            object_item.make_template()
        for arc_item in arc_items:
            arc_item.template_id = self.template_id
            arc_item.make_template()
        # Move
        try:
            rectf = object_items[dimension_at_origin].sceneBoundingRect()
        except (IndexError, TypeError):
            rectf = QRectF()
            for object_item in object_items:
                rectf |= object_item.sceneBoundingRect()
        center = rectf.center()
        for object_item in object_items:
            object_item.moveBy(x - center.x(), y - center.y())
            object_item.move_related_items_by(QPointF(x, y) - center)

    @busy_effect
    def add_relationship(self, template_id, object_items):
        """Try and add relationship given a template id and a list of object items."""
        object_id_list = list()
        object_name_list = list()
        object_dimensions = [x.template_id_dim[template_id] for x in object_items]
        for dimension in sorted(object_dimensions):
            ind = object_dimensions.index(dimension)
            item = object_items[ind]
            object_name = item.object_name
            if not object_name:
                logging.debug("can't find name {}".format(object_name))
                return False
            object_ = self.db_map.single_object(name=object_name).one_or_none()
            if not object_:
                logging.debug("can't find object {}".format(object_name))
                return False
            object_id_list.append(object_.id)
            object_name_list.append(object_name)
        if len(object_id_list) < 2:
            logging.debug("too short {}".format(len(object_id_list)))
            return False
        name = self.relationship_class_dict[template_id]["name"] + "_" + "__".join(object_name_list)
        class_id = self.relationship_class_dict[template_id]["id"]
        wide_kwargs = {
            'name': name,
            'object_id_list': object_id_list,
            'class_id': class_id
        }
        try:
            wide_relationship = self.db_map.add_wide_relationships(wide_kwargs)[0]
            for item in object_items:
                del item.template_id_dim[template_id]
            items = self.ui.graphicsView.scene().items()
            arc_items = [x for x in items if isinstance(x, ArcItem) and x.template_id == template_id]
            for item in arc_items:
                item.remove_template()
                item.template_id = None
                item.object_id_list = ",".join([str(x) for x in object_id_list])
            self.set_commit_rollback_actions_enabled(True)
            msg = "Successfully added new relationship '{}'.".format(wide_relationship.name)
            self.msg.emit(msg)
            return True
        except SpineIntegrityError as e:
            self.msg_error.emit(e.msg)
            return False
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return False

    def relationship_graph(
            self, object_name_list, object_class_name_list,
            extent, spread, label_font, label_color,
            object_class_id_list=[], relationship_class_id=None):
        """Lists of object and arc items that form a relationship."""
        object_items = list()
        arc_items = list()
        src_ind_list = list(range(len(object_name_list)))
        dst_ind_list = src_ind_list[1:] + src_ind_list[:1]
        d = self.shortest_path_matrix(object_name_list, src_ind_list, dst_ind_list, spread)
        if d is None:
            return [], []
        x, y = self.vertex_coordinates(d)
        for i in range(len(object_name_list)):
            x_ = x[i]
            y_ = y[i]
            object_name = object_name_list[i]
            object_class_name = object_class_name_list[i]
            try:
                object_class_id = object_class_id_list[i]
            except IndexError:
                object_class_id = None
            object_item = ObjectItem(
                self, None, object_name, object_class_id, object_class_name, x_, y_, extent,
                label_font=label_font, label_color=label_color)
            object_items.append(object_item)
        for i in range(len(object_items)):
            src_item = object_items[i]
            try:
                dst_item = object_items[i + 1]
            except IndexError:
                dst_item = object_items[0]
            arc_item = ArcItem(
                self, None, relationship_class_id, None,
                src_item, dst_item, extent / 4, self.arc_color)
            arc_items.append(arc_item)
        return object_items, arc_items

    def add_object_classes(self, object_classes):
        """Insert new object classes."""
        super().add_object_classes(object_classes)
        for object_class in object_classes:
            self.object_class_list_model.add_object_class(object_class)

    def show_add_relationship_classes_form(self):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(self)
        dialog.show()

    def add_relationship_classes(self, wide_relationship_classes):
        """Insert new relationship classes."""
        dim_count_list = list()
        for wide_relationship_class in wide_relationship_classes:
            self.relationship_class_list_model.add_relationship_class(wide_relationship_class)
        self.set_commit_rollback_actions_enabled(True)
        relationship_class_name_list = "', '".join([x.name for x in wide_relationship_classes])
        msg = "Successfully added new relationship class(es) '{}'.".format(relationship_class_name_list)
        self.msg.emit(msg)

    def show_graph_view_context_menu(self, global_pos):
        """Show context menu for graphics view."""
        self.graph_view_context_menu = GraphViewContextMenu(self, global_pos)
        option = self.graph_view_context_menu.get_action()
        if option == "Hide selected items":
            self.hide_selected_items()
        elif option == "Show hidden items":
            self.show_hidden_items()
        elif option == "Prune selected items":
            self.prune_selected_items()
        elif option == "Reinstate pruned items":
            self.reinstate_pruned_items()
        else:
            pass
        self.graph_view_context_menu.deleteLater()
        self.graph_view_context_menu = None

    @Slot("bool", name="reinstate_pruned_items")
    def hide_selected_items(self, checked=False):
        """Hide selected items."""
        self.hidden_items.extend(self.object_item_selection)
        for item in self.object_item_selection:
            item.set_all_visible(False)

    @Slot("bool", name="reinstate_pruned_items")
    def show_hidden_items(self, checked=False):
        """Show hidden items."""
        scene = self.ui.graphicsView.scene()
        if not scene:
            return
        for item in self.hidden_items:
            item.set_all_visible(True)
            self.hidden_items = list()

    @Slot("bool", name="reinstate_pruned_items")
    def prune_selected_items(self, checked=False):
        """Prune selected items."""
        self.rejected_items.extend(self.object_item_selection)
        self.build_graph()

    @Slot("bool", name="reinstate_pruned_items")
    def reinstate_pruned_items(self, checked=False):
        """Reinstate pruned items."""
        self.rejected_items = list()
        self.build_graph()

    def show_object_item_context_menu(self, e, main_item):
        """Show context menu for object_item."""
        global_pos = e.screenPos()
        self.object_item_context_menu = ObjectItemContextMenu(self, global_pos, main_item)
        option = self.object_item_context_menu.get_action()
        if option == 'Hide':
            self.hide_selected_items()
        elif option == 'Prune':
            self.prune_selected_items()
        elif option in ('Set name', 'Rename'):
            main_item.edit_name()
        elif option == 'Remove':
            self.remove_graph_items()
        try:
            relationship_class = self.object_item_context_menu.relationship_class_dict[option]
            relationship_class_id = relationship_class["id"]
            relationship_class_name = relationship_class["name"]
            object_class_id_list = relationship_class["object_class_id_list"]
            object_class_name_list = relationship_class['object_class_name_list']
            object_name_list = relationship_class['object_name_list']
            dimension = relationship_class['dimension']
            object_items, arc_items = self.relationship_graph(
                object_name_list, object_class_name_list, self.extent, self._spread,
                label_font=self.font, label_color=self.object_label_color,
                object_class_id_list=object_class_id_list, relationship_class_id=relationship_class_id)
            scene = self.ui.graphicsView.scene()
            scene_pos = e.scenePos()
            self.add_relationship_template(
                scene, scene_pos.x(), scene_pos.y(), object_items, arc_items, dimension_at_origin=dimension)
            object_items[dimension].merge_item(main_item)
            self._has_graph = True
            self.relationship_class_dict[self.template_id] = {
                "id": relationship_class_id,
                "name": relationship_class_name
            }
            self.template_id += 1
        except KeyError:
            pass
        self.object_item_context_menu.deleteLater()
        self.object_item_context_menu = None

    @busy_effect
    @Slot("bool", name="remove_graph_items")
    def remove_graph_items(self, checked=False):
        """Remove all selected items in the graph."""
        if not self.object_item_selection:
            return
        removed_objects = list(
            dict(class_id=x.object_class_id, id=x.object_id) for x in self.object_item_selection if x.object_id
        )
        object_ids = set(x['id'] for x in removed_objects)
        try:
            self.db_map.remove_items(object_ids=object_ids)
            self.object_tree_model.remove_items("object", object_ids)
            # Parameter models
            self.object_parameter_value_model.remove_objects(removed_objects)
            self.relationship_parameter_value_model.remove_objects(removed_objects)
            self.set_commit_rollback_actions_enabled(True)
            for item in self.object_item_selection:
                item.wipe_out()
            self.msg.emit("Successfully removed items.")
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)

    def restore_ui(self):
        """Restore UI state from previous session."""
        super().restore_ui()
        window_state = self.qsettings().value("{0}/windowState".format(self.settings_key))
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        super().closeEvent(event)
        self.qsettings().setValue("{0}/windowState".format(self.settings_key), self.saveState(version=1))
        scene = self.ui.graphicsView.scene()
        if scene:
            scene.deleteLater()
