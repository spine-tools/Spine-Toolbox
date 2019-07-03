######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the DataStoreForm class, parent class of TreeViewForm and GraphViewForm.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

from PySide2.QtWidgets import QMainWindow, QHeaderView, QDialog, QMessageBox, QCheckBox, QErrorMessage
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon
from config import MAINWINDOW_SS, STATUSBAR_SS
from spinedb_api import SpineDBAPIError
from widgets.custom_delegates import (
    ObjectParameterValueDelegate,
    ObjectParameterDefinitionDelegate,
    RelationshipParameterValueDelegate,
    RelationshipParameterDefinitionDelegate,
)
from widgets.custom_qdialog import (
    AddObjectClassesDialog,
    AddObjectsDialog,
    AddRelationshipClassesDialog,
    AddRelationshipsDialog,
    EditObjectClassesDialog,
    EditObjectsDialog,
    EditRelationshipClassesDialog,
    EditRelationshipsDialog,
    ManageParameterTagsDialog,
    CommitDialog,
)
from widgets.toolbars import ParameterTagToolBar
from treeview_models import (
    ObjectParameterDefinitionModel,
    ObjectParameterValueModel,
    RelationshipParameterDefinitionModel,
    RelationshipParameterValueModel,
    ParameterValueListModel,
)
from spinedb_api import copy_database
from helpers import busy_effect, format_string_list, IconManager


class DataStoreForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        project (SpineToolboxProject): The project instance that owns this form
        db_map (DiffDatabaseMapping): The object relational database mapping
        database (str): The database name
        ui: UI definition of the form that is initialized
    """

    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")
    commit_available = Signal("bool", name="commit_available")

    def __init__(self, project, ui, *db_maps):
        """Initialize class."""
        super().__init__(flags=Qt.Window)
        self._project = project
        # Setup UI from Qt Designer file
        self.ui = ui
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        # Set up status bar and apply style sheet
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        self.setStyleSheet(MAINWINDOW_SS)
        # Class attributes
        self.err_msg = QErrorMessage(self)
        # DB
        self.db_map = db_maps[0]
        self.db_maps = db_maps
        self.database = self.db_map.sa_url.database
        self.databases = [x.sa_url.database for x in self.db_maps]
        self.icon_mngr = IconManager()
        self.icon_mngr.setup_object_pixmaps(self.db_maps[0].object_class_list())
        # Object tree selected indexes
        self.selected_obj_tree_indexes = {}
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
        self.parameter_value_list_model = ParameterValueListModel(self)
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        # Parameter tag stuff
        self.parameter_tag_toolbar = ParameterTagToolBar(self, self.db_maps[0])
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)
        self.selected_parameter_tag_ids = set()
        self.selected_obj_parameter_definition_ids = dict()
        self.selected_rel_parameter_definition_ids = dict()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_object_parameter_value.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_object_parameter_definition.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_relationship_parameter_value.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_relationship_parameter_definition.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_parameter_value_list.toggleViewAction())
        self.ui.menuToolbars.addAction(self.parameter_tag_toolbar.toggleViewAction())

    def connect_signals(self):
        """Connect signals to slots."""
        # Message signals
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        self.commit_available.connect(self._handle_commit_available)
        # Menu actions
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)
        self.ui.actionClose.triggered.connect(self.close)
        # Object tree
        self.ui.treeView_object.selectionModel().selectionChanged.connect(self._handle_object_tree_selection_changed)
        # Parameter tables delegate commit data
        self.ui.tableView_object_parameter_definition.itemDelegate().data_committed.connect(
            self.set_parameter_definition_data
        )
        self.ui.tableView_object_parameter_value.itemDelegate().data_committed.connect(self.set_parameter_value_data)
        self.ui.tableView_relationship_parameter_definition.itemDelegate().data_committed.connect(
            self.set_parameter_definition_data
        )
        self.ui.tableView_relationship_parameter_value.itemDelegate().data_committed.connect(
            self.set_parameter_value_data
        )
        # Parameter tags
        self.parameter_tag_toolbar.manage_tags_action_triggered.connect(self.show_manage_parameter_tags_form)
        self.parameter_tag_toolbar.tag_button_toggled.connect(self._handle_tag_button_toggled)
        # Dock widgets visibility
        self.ui.dockWidget_object_parameter_value.visibilityChanged.connect(
            self._handle_object_parameter_value_visibility_changed
        )
        self.ui.dockWidget_object_parameter_definition.visibilityChanged.connect(
            self._handle_object_parameter_definition_visibility_changed
        )
        self.ui.dockWidget_relationship_parameter_value.visibilityChanged.connect(
            self._handle_relationship_parameter_value_visibility_changed
        )
        self.ui.dockWidget_relationship_parameter_definition.visibilityChanged.connect(
            self._handle_relationship_parameter_definition_visibility_changed
        )
        self.ui.actionRestore_Dock_Widgets.triggered.connect(self.restore_dock_widgets)

    def qsettings(self):
        """Returns the QSettings instance from ToolboxUI."""
        return self._project._toolbox._qsettings

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

    @Slot("bool", name="_handle_object_parameter_value_visibility_changed")
    def _handle_object_parameter_value_visibility_changed(self, visible):
        if visible:
            self.object_parameter_value_model.update_filter()

    @Slot("bool", name="_handle_object_parameter_definition_visibility_changed")
    def _handle_object_parameter_definition_visibility_changed(self, visible):
        if visible:
            self.object_parameter_definition_model.update_filter()

    @Slot("bool", name="_handle_relationship_parameter_value_visibility_changed")
    def _handle_relationship_parameter_value_visibility_changed(self, visible):
        if visible:
            self.relationship_parameter_value_model.update_filter()

    @Slot("bool", name="_handle_relationship_parameter_definition_visibility_changed")
    def _handle_relationship_parameter_definition_visibility_changed(self, visible):
        if visible:
            self.relationship_parameter_definition_model.update_filter()

    @Slot("int", "bool", name="_handle_tag_button_toggled")
    def _handle_tag_button_toggled(self, id, checked):
        """Called when a parameter tag button is toggled.
        Compute selected parameter definiton ids per object class ids.
        Then update set of selected object class ids. Finally, update filter.
        """
        if checked:
            self.selected_parameter_tag_ids.add(id)
        else:
            self.selected_parameter_tag_ids.remove(id)
        parameter_definition_id_list = set()
        for item in self.db_map.wide_parameter_tag_definition_list():
            tag_id = item.parameter_tag_id if item.parameter_tag_id else 0
            if tag_id not in self.selected_parameter_tag_ids:
                continue
            parameter_definition_id_list.update({int(x) for x in item.parameter_definition_id_list.split(",")})
        self.selected_obj_parameter_definition_ids = {
            x.object_class_id: {int(y) for y in x.parameter_definition_id_list.split(",")}
            for x in self.db_map.wide_object_parameter_definition_list(
                parameter_definition_id_list=parameter_definition_id_list
            )
        }
        self.selected_rel_parameter_definition_ids = {
            x.relationship_class_id: {int(y) for y in x.parameter_definition_id_list.split(",")}
            for x in self.db_map.wide_relationship_parameter_definition_list(
                parameter_definition_id_list=parameter_definition_id_list
            )
        }
        self.do_update_filter()

    @Slot("bool", name="_handle_commit_available")
    def _handle_commit_available(self, on):
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
            self.commit_available.emit(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes committed successfully."
        self.msg.emit(msg)

    @Slot("bool", name="rollback_session")
    def rollback_session(self, checked=False):
        try:
            self.db_map.rollback_session()
            self.commit_available.emit(False)
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

    def init_models(self):
        """Initialize models."""
        self.init_object_tree_model()
        self.init_parameter_value_models()
        self.init_parameter_definition_models()
        self.init_parameter_value_list_model()

    def init_parameter_value_models(self):
        """Initialize parameter value models from source database."""
        self.object_parameter_value_model.reset_model()
        self.relationship_parameter_value_model.reset_model()

    def init_parameter_definition_models(self):
        """Initialize parameter (definition) models from source database."""
        self.object_parameter_definition_model.reset_model()
        self.relationship_parameter_definition_model.reset_model()

    def init_parameter_value_list_model(self):
        """Initialize parameter value_list models from source database."""
        self.parameter_value_list_model.build_tree()

    def init_views(self):
        """Initialize model views."""
        self.init_object_tree_view()
        self.init_object_parameter_value_view()
        self.init_relationship_parameter_value_view()
        self.init_object_parameter_definition_view()
        self.init_relationship_parameter_definition_view()
        self.init_parameter_value_list_view()

    def init_object_tree_view(self):
        """Init object tree view."""
        self.ui.treeView_object.setModel(self.object_tree_model)
        # self.ui.treeView_object.header().hide()
        for i in range(self.object_tree_model.rowCount()):
            self.ui.treeView_object.expand(self.object_tree_model.index(i, 0))
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
        self.ui.tableView_object_parameter_value.horizontalHeader().setSectionsMovable(True)

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
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_value.horizontalHeader().setSectionsMovable(True)

    def init_object_parameter_definition_view(self):
        """Init object parameter definition view."""
        self.ui.tableView_object_parameter_definition.setModel(self.object_parameter_definition_model)
        h = self.object_parameter_definition_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('object_class_id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('parameter_tag_id_list'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('value_list_id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView_object_parameter_definition.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_object_parameter_definition.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_object_parameter_definition.resizeColumnsToContents()
        self.ui.tableView_object_parameter_definition.horizontalHeader().setSectionsMovable(True)

    def init_relationship_parameter_definition_view(self):
        """Init relationship parameter definition view."""
        self.ui.tableView_relationship_parameter_definition.setModel(self.relationship_parameter_definition_model)
        h = self.relationship_parameter_definition_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('relationship_class_id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('object_class_id_list'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('parameter_tag_id_list'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('value_list_id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.ui.tableView_relationship_parameter_definition.verticalHeader().setDefaultSectionSize(
            self.default_row_height
        )
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().setResizeContentsPrecision(
            self.visible_rows
        )
        self.ui.tableView_relationship_parameter_definition.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().setSectionsMovable(True)

    def init_parameter_value_list_view(self):
        self.ui.treeView_parameter_value_list.setModel(self.parameter_value_list_model)
        for i in range(self.parameter_value_list_model.rowCount()):
            index = self.parameter_value_list_model.index(i, 0)
            self.ui.treeView_parameter_value_list.expand(index)
        self.ui.treeView_parameter_value_list.resizeColumnToContents(0)
        self.ui.treeView_parameter_value_list.header().hide()

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

    def all_selected_object_class_ids(self):
        """Return object class ids selected in object tree *and* parameter tag toolbar."""
        tree_object_class_ids = self.selected_object_class_ids
        tag_object_class_ids = set(self.selected_obj_parameter_definition_ids.keys())
        if not tag_object_class_ids:
            return tree_object_class_ids
        elif not tree_object_class_ids:
            return tag_object_class_ids
        else:
            intersection = tree_object_class_ids.intersection(tag_object_class_ids)
            if intersection:
                return intersection
            else:
                return {None}

    def all_selected_relationship_class_ids(self):
        """Return relationship class ids selected in relationship tree *and* parameter tag toolbar."""
        tree_relationship_class_ids = self.selected_relationship_class_ids
        tag_relationship_class_ids = set(self.selected_rel_parameter_definition_ids.keys())
        if not tag_relationship_class_ids:
            return tree_relationship_class_ids
        elif not tree_relationship_class_ids:
            return tag_relationship_class_ids
        else:
            intersection = tree_relationship_class_ids.intersection(tag_relationship_class_ids)
            if intersection:
                return intersection
            else:
                return {None}

    def do_update_filter(self):
        """Apply filter on visible views."""
        if self.ui.dockWidget_object_parameter_value.isVisible():
            self.object_parameter_value_model.update_filter()
        if self.ui.dockWidget_object_parameter_definition.isVisible():
            self.object_parameter_definition_model.update_filter()
        if self.ui.dockWidget_relationship_parameter_value.isVisible():
            self.relationship_parameter_value_model.update_filter()
        if self.ui.dockWidget_relationship_parameter_definition.isVisible():
            self.relationship_parameter_definition_model.update_filter()

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
        self, checked=False, relationship_class_id=None, object_id=None, object_class_id=None
    ):
        """Show dialog to let user select preferences for new relationships."""
        dialog = AddRelationshipsDialog(
            self, relationship_class_id=relationship_class_id, object_id=object_id, object_class_id=object_class_id
        )
        dialog.show()

    def add_object_classes(self, object_classes):
        """Insert new object classes."""
        if not object_classes.count():
            return False
        self.icon_mngr.setup_object_pixmaps(object_classes)
        self.object_tree_model.add_object_classes(object_classes)
        if self.selected_object_class_ids:
            # Recompute self.selected_obj_tree_indexes['object_class']
            # since some new classes might have been inserted above those indexes
            # NOTE: This is only needed for object classes, since all other items are inserted at the bottom
            self.selected_obj_tree_indexes['object_class'] = sel_obj_cls_indexes = {}
            root_index = self.object_tree_model.indexFromItem(self.object_tree_model.root_item)
            for i in range(self.object_tree_model.root_item.rowCount()):
                obj_cls_index = self.object_tree_model.index(i, 0, root_index)
                if obj_cls_index.data(Qt.UserRole + 1)['id'] in self.selected_object_class_ids:
                    sel_obj_cls_indexes[obj_cls_index] = None
        self.commit_available.emit(True)
        msg = "Successfully added new object class(es) '{}'.".format("', '".join([x.name for x in object_classes]))
        self.msg.emit(msg)
        return True

    def add_objects(self, objects):
        """Insert new objects."""
        if not objects.count():
            return False
        self.object_tree_model.add_objects(objects)
        self.commit_available.emit(True)
        msg = "Successfully added new object(s) '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)
        return True

    def add_relationship_classes(self, relationship_classes):
        """Insert new relationship classes."""
        if not relationship_classes.count():
            return False
        self.object_tree_model.add_relationship_classes(relationship_classes)
        self.relationship_parameter_definition_model.add_object_class_id_lists(relationship_classes)
        self.relationship_parameter_value_model.add_object_class_id_lists(relationship_classes)
        self.commit_available.emit(True)
        relationship_class_name_list = "', '".join([x.name for x in relationship_classes])
        msg = "Successfully added new relationship class(es) '{}'.".format(relationship_class_name_list)
        self.msg.emit(msg)
        return True

    def add_relationships(self, relationships):
        """Insert new relationships."""
        if not relationships.count():
            return False
        self.object_tree_model.add_relationships(relationships)
        self.commit_available.emit(True)
        relationship_name_list = "', '".join([x.name for x in relationships])
        msg = "Successfully added new relationship(s) '{}'.".format(relationship_name_list)
        self.msg.emit(msg)
        return True

    @Slot("bool", name="show_edit_object_classes_form")
    def show_edit_object_classes_form(self, checked=False):
        try:
            indexes = self.selected_obj_tree_indexes['object_class']
        except KeyError:
            return
        kwargs_list = [ind.data(Qt.UserRole + 1) for ind in indexes]
        dialog = EditObjectClassesDialog(self, kwargs_list)
        dialog.show()

    @Slot("bool", name="show_edit_objects_form")
    def show_edit_objects_form(self, checked=False):
        try:
            indexes = self.selected_obj_tree_indexes['object']
        except KeyError:
            return
        kwargs_list = [ind.data(Qt.UserRole + 1) for ind in indexes]
        dialog = EditObjectsDialog(self, kwargs_list)
        dialog.show()

    @Slot("bool", name="show_edit_relationship_classes_form")
    def show_edit_relationship_classes_form(self, checked=False):
        if self.widget_with_selection == self.ui.treeView_object:
            indexes = self.selected_obj_tree_indexes.get('relationship_class')
        elif self.widget_with_selection == self.ui.treeView_relationship:
            indexes = self.selected_rel_tree_indexes.get('relationship_class')
        else:
            return
        if not indexes:
            return
        kwargs_list = [ind.data(Qt.UserRole + 1) for ind in indexes]
        dialog = EditRelationshipClassesDialog(self, kwargs_list)
        dialog.show()

    @Slot("bool", name="show_edit_relationships_form")
    def show_edit_relationships_form(self, checked=False):
        # NOTE: Only edit relationships of the same class as the one in current index, for now...
        if self.widget_with_selection == self.ui.treeView_object:
            current = self.ui.treeView_object.currentIndex()
            if current.data(Qt.UserRole) != "relationship":
                return
            class_id = current.data(Qt.UserRole + 1)['class_id']
            wide_relationship_class = current.parent().data(Qt.UserRole + 1)
            indexes = self.selected_obj_tree_indexes.get('relationship')
        elif self.widget_with_selection == self.ui.treeView_relationship:
            current = self.ui.treeView_relationship.currentIndex()
            if current.data(Qt.UserRole) != "relationship":
                return
            class_id = current.data(Qt.UserRole + 1)['class_id']
            wide_relationship_class = current.parent().data(Qt.UserRole + 1)
            indexes = self.selected_rel_tree_indexes.get('relationship')
        kwargs_list = list()
        for index in indexes:
            if index.data(Qt.UserRole + 1)['class_id'] != class_id:
                continue
            kwargs_list.append(index.data(Qt.UserRole + 1))
        dialog = EditRelationshipsDialog(self, kwargs_list, wide_relationship_class)
        dialog.show()

    @busy_effect
    def update_object_classes(self, object_classes):
        """Update object classes."""
        if not object_classes.count():
            return False
        self.icon_mngr.setup_object_pixmaps(object_classes)
        self.object_tree_model.update_object_classes(object_classes)
        self.object_parameter_value_model.rename_object_classes(object_classes)
        self.object_parameter_definition_model.rename_object_classes(object_classes)
        self.relationship_parameter_value_model.rename_object_classes(object_classes)
        self.relationship_parameter_definition_model.rename_object_classes(object_classes)
        self.commit_available.emit(True)
        msg = "Successfully updated object classes '{}'.".format("', '".join([x.name for x in object_classes]))
        self.msg.emit(msg)
        return True

    @busy_effect
    def update_objects(self, objects):
        """Update objects."""
        if not objects.count():
            return False
        self.object_tree_model.update_objects(objects)
        self.object_parameter_value_model.rename_objects(objects)
        self.relationship_parameter_value_model.rename_objects(objects)
        self.commit_available.emit(True)
        msg = "Successfully updated objects '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)
        return True

    @busy_effect
    def update_relationship_classes(self, wide_relationship_classes):
        """Update relationship classes."""
        if not wide_relationship_classes.count():
            return False
        self.object_tree_model.update_relationship_classes(wide_relationship_classes)
        self.relationship_parameter_value_model.rename_relationship_classes(wide_relationship_classes)
        self.relationship_parameter_definition_model.rename_relationship_classes(wide_relationship_classes)
        self.commit_available.emit(True)
        relationship_class_name_list = "', '".join([x.name for x in wide_relationship_classes])
        msg = "Successfully updated relationship classes '{}'.".format(relationship_class_name_list)
        self.msg.emit(msg)
        return True

    @busy_effect
    def update_relationships(self, wide_relationships):
        """Update relationships."""
        if not wide_relationships.count():
            return False
        self.object_tree_model.update_relationships(wide_relationships)
        self.commit_available.emit(True)
        relationship_name_list = "', '".join([x.name for x in wide_relationships])
        msg = "Successfully updated relationships '{}'.".format(relationship_name_list)
        self.msg.emit(msg)
        return True

    def add_parameter_value_lists(self, *to_add):
        if not any(to_add):
            return False
        parents = []
        for item in to_add:
            parents.append(item.pop("parent"))
        try:
            value_lists, error_log = self.db_map.add_wide_parameter_value_lists(*to_add)
            if value_lists.count():
                self.commit_available.emit(True)
                self.msg.emit("Successfully added new parameter value list(s).")
            for k, value_list in enumerate(value_lists):
                parents[k].internalPointer().id = value_list.id
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            return True
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return False

    def update_parameter_value_lists(self, *to_update):
        if not any(to_update):
            return False
        try:
            value_lists, error_log = self.db_map.update_wide_parameter_value_lists(*to_update)
            if value_lists.count():
                self.object_parameter_definition_model.rename_parameter_value_lists(value_lists)
                self.relationship_parameter_definition_model.rename_parameter_value_lists(value_lists)
                self.commit_available.emit(True)
                self.msg.emit("Successfully updated parameter value list(s).")
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            return True
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return False

    @Slot("bool", name="show_manage_parameter_tags_form")
    def show_manage_parameter_tags_form(self, checked=False):
        dialog = ManageParameterTagsDialog(self)
        dialog.show()

    @busy_effect
    def add_parameter_tags(self, parameter_tags):
        """Add parameter tags."""
        self.parameter_tag_toolbar.add_tag_actions(parameter_tags)
        self.commit_available.emit(True)
        msg = "Successfully added parameter tags '{}'.".format([x.tag for x in parameter_tags])
        self.msg.emit(msg)
        return True

    @busy_effect
    def update_parameter_tags(self, parameter_tags):
        """Update parameter tags."""
        # TODO: update parameter value tables??
        self.object_parameter_definition_model.rename_parameter_tags(parameter_tags)
        self.relationship_parameter_definition_model.rename_parameter_tags(parameter_tags)
        self.parameter_tag_toolbar.update_tag_actions(parameter_tags)
        self.commit_available.emit(True)
        msg = "Successfully updated parameter tags '{}'.".format([x.tag for x in parameter_tags])
        self.msg.emit(msg)
        return True

    @busy_effect
    def remove_parameter_tags(self, parameter_tag_ids):
        """Remove parameter tags."""
        # TODO: remove from parameter value tables??
        if not parameter_tag_ids:
            return False
        self.object_parameter_definition_model.remove_parameter_tags(parameter_tag_ids)
        self.relationship_parameter_definition_model.remove_parameter_tags(parameter_tag_ids)
        self.parameter_tag_toolbar.remove_tag_actions(parameter_tag_ids)
        self.commit_available.emit(True)
        msg = "Successfully removed parameter tags."
        self.msg.emit(msg)
        return True

    @Slot("QModelIndex", "QVariant", name="set_parameter_value_data")
    def set_parameter_value_data(self, index, new_value):
        """Update (object or relationship) parameter value with newly edited data."""
        if new_value is None:
            return False
        index.model().setData(index, new_value)
        return True

    @Slot("QModelIndex", "QVariant", name="set_parameter_definition_data")
    def set_parameter_definition_data(self, index, new_value):
        """Update (object or relationship) parameter definition with newly edited data.
        If the parameter name changed, update it in (object or relationship) parameter value.
        """
        if new_value is None:
            return False
        header = index.model().horizontal_header_labels()
        if index.model().setData(index, new_value) and header[index.column()] == 'parameter_name':
            parameter_id_column = header.index('id')
            parameter_id = index.sibling(index.row(), parameter_id_column).data(Qt.DisplayRole)
            if 'object_class_id' in header:
                object_class_id_column = header.index('object_class_id')
                object_class_id = index.sibling(index.row(), object_class_id_column).data(Qt.DisplayRole)
                self.object_parameter_value_model.rename_parameter(parameter_id, object_class_id, new_value)
            elif 'relationship_class_id' in header:
                relationship_class_id_column = header.index('relationship_class_id')
                relationship_class_id = index.sibling(index.row(), relationship_class_id_column).data(Qt.DisplayRole)
                self.relationship_parameter_value_model.rename_parameter(parameter_id, relationship_class_id, new_value)
        return True

    def show_commit_session_prompt(self):
        """Shows the commit session message box."""
        qsettings = self.qsettings()
        commit_at_exit = int(qsettings.value("appSettings/commitAtExit", defaultValue="1"))
        if commit_at_exit == 0:
            # Don't commit session and don't show message box
            return
        elif commit_at_exit == 1:  # Default
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
                    # Save preference
                    qsettings.setValue("appSettings/commitAtExit", "2")
            else:
                if chk == 2:
                    # Save preference
                    qsettings.setValue("appSettings/commitAtExit", "0")
        elif commit_at_exit == 2:
            # Commit session and don't show message box
            self.show_commit_session_dialog()
        else:
            qsettings.setValue("appSettings/commitAtExit", "1")
        return

    def restore_ui(self):
        """Restore UI state from previous session."""
        qsettings = self.qsettings()
        qsettings.beginGroup(self.settings_group)
        window_size = qsettings.value("windowSize")
        window_pos = qsettings.value("windowPosition")
        window_state = qsettings.value("windowState")
        window_maximized = qsettings.value("windowMaximized", defaultValue='false')
        n_screens = qsettings.value("n_screens", defaultValue=1)
        opd_h_state = qsettings.value("objParDefHeaderState")
        opv_h_state = qsettings.value("objParValHeaderState")
        rpd_h_state = qsettings.value("relParDefHeaderState")
        rpv_h_state = qsettings.value("relParValHeaderState")
        qsettings.endGroup()
        if opd_h_state:
            self.ui.tableView_object_parameter_definition.horizontalHeader().restoreState(opd_h_state)
        if opv_h_state:
            self.ui.tableView_object_parameter_value.horizontalHeader().restoreState(opv_h_state)
        if rpd_h_state:
            self.ui.tableView_relationship_parameter_definition.horizontalHeader().restoreState(rpd_h_state)
        if rpv_h_state:
            self.ui.tableView_relationship_parameter_value.horizontalHeader().restoreState(rpv_h_state)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
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
        qsettings = self.qsettings()
        qsettings.beginGroup(self.settings_group)
        qsettings.setValue("windowSize", self.size())
        qsettings.setValue("windowPosition", self.pos())
        qsettings.setValue("windowState", self.saveState(version=1))
        h = self.ui.tableView_object_parameter_definition.horizontalHeader()
        qsettings.setValue("objParDefHeaderState", h.saveState())
        h = self.ui.tableView_object_parameter_value.horizontalHeader()
        qsettings.setValue("objParValHeaderState", h.saveState())
        h = self.ui.tableView_relationship_parameter_definition.horizontalHeader()
        qsettings.setValue("relParDefHeaderState", h.saveState())
        h = self.ui.tableView_relationship_parameter_value.horizontalHeader()
        qsettings.setValue("relParValHeaderState", h.saveState())
        if self.windowState() == Qt.WindowMaximized:
            qsettings.setValue("windowMaximized", True)
        else:
            qsettings.setValue("windowMaximized", False)
        qsettings.endGroup()
        if self.db_map.has_pending_changes():
            self.show_commit_session_prompt()
        if event:
            event.accept()
