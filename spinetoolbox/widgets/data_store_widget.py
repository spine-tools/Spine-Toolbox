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
from spinedb_api import SpineDBAPIError
from config import MAINWINDOW_SS, STATUSBAR_SS
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
from widgets.parameter_value_editor import ParameterValueEditor
from widgets.toolbars import ParameterTagToolBar
from treeview_models import (
    ObjectParameterDefinitionModel,
    ObjectParameterValueModel,
    RelationshipParameterDefinitionModel,
    RelationshipParameterValueModel,
    ParameterValueListModel,
)
from helpers import busy_effect, format_string_list, IconManager
from plotting import tree_graph_view_parameter_value_name


class DataStoreForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        project (SpineToolboxProject): The project instance that owns this form
        ui: UI definition of the form that is initialized
        db_maps (dict): named DiffDatabaseMapping instances
    """

    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")
    commit_available = Signal("bool", name="commit_available")

    def __init__(self, project, ui, db_maps):
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
        self.db_names = list(db_maps.keys())
        self.db_maps = list(db_maps.values())
        self.db_name_to_map = dict(zip(self.db_names, self.db_maps))
        self.db_map_to_name = dict(zip(self.db_maps, self.db_names))
        self.icon_mngr = IconManager()
        for db_map in self.db_maps:
            self.icon_mngr.setup_object_pixmaps(db_map.object_class_list())
        # Object tree selected indexes
        self.selected_obj_tree_indexes = {}
        self.selected_object_class_ids = set()
        self.selected_object_ids = dict()
        self.selected_relationship_class_ids = set()
        self.selected_object_id_lists = dict()
        # Parameter tag stuff
        self.parameter_tag_toolbar = ParameterTagToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)
        self.selected_parameter_tag_ids = dict()
        self.selected_obj_parameter_definition_ids = dict()
        self.selected_rel_parameter_definition_ids = dict()
        # Models
        self.object_parameter_value_model = ObjectParameterValueModel(self)
        self.relationship_parameter_value_model = RelationshipParameterValueModel(self)
        self.object_parameter_definition_model = ObjectParameterDefinitionModel(self)
        self.relationship_parameter_definition_model = RelationshipParameterDefinitionModel(self)
        self.parameter_value_list_model = ParameterValueListModel(self)
        # Setup views
        self.ui.tableView_object_parameter_value.setModel(self.object_parameter_value_model)
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_model)
        self.ui.tableView_object_parameter_definition.setModel(self.object_parameter_definition_model)
        self.ui.tableView_relationship_parameter_definition.setModel(self.relationship_parameter_definition_model)
        self.ui.treeView_parameter_value_list.setModel(self.parameter_value_list_model)
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        for view in (
            self.ui.tableView_object_parameter_value,
            self.ui.tableView_relationship_parameter_value,
            self.ui.tableView_object_parameter_definition,
            self.ui.tableView_relationship_parameter_definition,
        ):
            view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            view.verticalHeader().setDefaultSectionSize(self.default_row_height)
            view.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
            view.horizontalHeader().setSectionsMovable(True)
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
        # Parameter tables delegates
        for table_view in (
            self.ui.tableView_object_parameter_definition,
            self.ui.tableView_relationship_parameter_definition,
        ):
            # pylint: disable=cell-var-from-loop
            table_view.itemDelegate().data_committed.connect(self.set_parameter_definition_data)
            table_view.itemDelegate().parameter_value_editor_requested.connect(
                lambda index, value: self.show_parameter_value_editor(index, table_view, value=value)
            )
        for table_view in (self.ui.tableView_object_parameter_value, self.ui.tableView_relationship_parameter_value):
            table_view.itemDelegate().data_committed.connect(self.set_parameter_value_data)
            table_view.itemDelegate().parameter_value_editor_requested.connect(
                lambda index, value: self.show_parameter_value_editor(index, table_view, value=value)
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

    @Slot("QVariant", "bool", name="_handle_tag_button_toggled")
    def _handle_tag_button_toggled(self, db_map_ids, checked):
        """Called when a parameter tag button is toggled.
        Compute selected parameter definition ids per object class ids.
        Then update set of selected object class ids. Finally, update filter.
        """
        for db_map, id_ in db_map_ids:
            if checked:
                self.selected_parameter_tag_ids.setdefault(db_map, set()).add(id_)
            else:
                self.selected_parameter_tag_ids[db_map].remove(id_)
        if not any(v for v in self.selected_parameter_tag_ids.values()):
            # No tags selected: set empty dict so them all pass
            self.selected_obj_parameter_definition_ids = {}
            self.selected_rel_parameter_definition_ids = {}
        else:
            # At least one tag selected: set non-empty dict so not all of them pass
            self.selected_obj_parameter_definition_ids = {None: None}
            self.selected_rel_parameter_definition_ids = {None: None}
            for db_map, tag_ids in self.selected_parameter_tag_ids.items():
                parameter_definition_id_list = set()
                for item in db_map.wide_parameter_tag_definition_list():
                    tag_id = item.parameter_tag_id if item.parameter_tag_id else 0
                    if tag_id not in tag_ids:
                        continue
                    parameter_definition_id_list.update({int(x) for x in item.parameter_definition_id_list.split(",")})
                self.selected_obj_parameter_definition_ids.update(
                    {
                        (db_map, x.object_class_id): {int(y) for y in x.parameter_definition_id_list.split(",")}
                        for x in db_map.wide_object_parameter_definition_list(
                            parameter_definition_id_list=parameter_definition_id_list
                        )
                    }
                )
                self.selected_rel_parameter_definition_ids.update(
                    {
                        (db_map, x.relationship_class_id): {int(y) for y in x.parameter_definition_id_list.split(",")}
                        for x in db_map.wide_relationship_parameter_definition_list(
                            parameter_definition_id_list=parameter_definition_id_list
                        )
                    }
                )
        self.do_update_filter()

    @Slot("bool", name="_handle_commit_available")
    def _handle_commit_available(self, on):
        self.ui.actionCommit.setEnabled(on)
        self.ui.actionRollback.setEnabled(on)

    @Slot("bool", name="show_commit_session_dialog")
    def show_commit_session_dialog(self, checked=False):
        """Query user for a commit message and commit changes to source database."""
        if not any(db_map.has_pending_changes() for db_map in self.db_maps):
            self.msg.emit("Nothing to commit yet.")
            return
        dialog = CommitDialog(self, *self.db_names)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        self.commit_session(dialog.commit_msg)

    @busy_effect
    def commit_session(self, commit_msg):
        try:
            for db_map in self.db_maps:
                db_map.commit_session(commit_msg)
            self.commit_available.emit(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes committed successfully."
        self.msg.emit(msg)

    @Slot("bool", name="rollback_session")
    def rollback_session(self, checked=False):
        try:
            for db_map in self.db_maps:
                db_map.rollback_session()
            self.commit_available.emit(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        self.init_models()
        msg = "All changes since last commit rolled back successfully."
        self.msg.emit(msg)

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
        self.set_default_parameter_rows()
        self.init_parameter_value_list_model()
        self.init_parameter_tag_toolbar()

    def init_object_tree_model(self):
        """Initialize object tree model."""
        self.object_tree_model.build_tree()
        self.ui.treeView_object.expand(self.object_tree_model.indexFromItem(self.object_tree_model.root_item))
        self.ui.treeView_object.resizeColumnToContents(0)

    def init_parameter_value_models(self):
        """Initialize parameter value models from source database."""
        self.object_parameter_value_model.reset_model()
        h = self.object_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('object_class_id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('object_id'))
        self.ui.tableView_object_parameter_value.horizontalHeader().hideSection(h('parameter_id'))
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()
        self.relationship_parameter_value_model.reset_model()
        h = self.relationship_parameter_value_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('relationship_class_id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_class_id_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_class_name_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('relationship_id'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('object_id_list'))
        self.ui.tableView_relationship_parameter_value.horizontalHeader().hideSection(h('parameter_id'))
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_parameter_definition_models(self):
        """Initialize parameter (definition) models from source database."""
        self.object_parameter_definition_model.reset_model()
        h = self.object_parameter_definition_model.horizontal_header_labels().index
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('object_class_id'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('parameter_tag_id_list'))
        self.ui.tableView_object_parameter_definition.horizontalHeader().hideSection(h('value_list_id'))
        self.ui.tableView_object_parameter_definition.resizeColumnsToContents()
        self.relationship_parameter_definition_model.reset_model()
        h = self.relationship_parameter_definition_model.horizontal_header_labels().index
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('relationship_class_id'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('object_class_id_list'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('parameter_tag_id_list'))
        self.ui.tableView_relationship_parameter_definition.horizontalHeader().hideSection(h('value_list_id'))
        self.ui.tableView_relationship_parameter_definition.resizeColumnsToContents()

    def init_parameter_value_list_model(self):
        """Initialize parameter value_list models from source database."""
        self.parameter_value_list_model.build_tree()
        for i in range(self.parameter_value_list_model.rowCount()):
            db_index = self.parameter_value_list_model.index(i, 0)
            self.ui.treeView_parameter_value_list.expand(db_index)
            for j in range(self.parameter_value_list_model.rowCount(db_index)):
                list_index = self.parameter_value_list_model.index(j, 0, db_index)
                self.ui.treeView_parameter_value_list.expand(list_index)
        self.ui.treeView_parameter_value_list.resizeColumnToContents(0)
        self.ui.treeView_parameter_value_list.header().hide()

    def init_parameter_tag_toolbar(self):
        """Initialize parameter tag toolbar."""
        self.parameter_tag_toolbar.init_toolbar()

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
        if not tree_object_class_ids:
            return tag_object_class_ids
        intersection = tree_object_class_ids.intersection(tag_object_class_ids)
        if intersection:
            return intersection
        return {None}

    def all_selected_relationship_class_ids(self):
        """Return relationship class ids selected in relationship tree *and* parameter tag toolbar."""
        tree_relationship_class_ids = self.selected_relationship_class_ids
        tag_relationship_class_ids = set(self.selected_rel_parameter_definition_ids.keys())
        if not tag_relationship_class_ids:
            return tree_relationship_class_ids
        if not tree_relationship_class_ids:
            return tag_relationship_class_ids
        intersection = tree_relationship_class_ids.intersection(tag_relationship_class_ids)
        if intersection:
            return intersection
        return {None}

    def set_default_parameter_rows(self, index=None):
        """Set default rows for parameter models according to selection in object or relationship tree."""
        if index is None or index.data(Qt.UserRole) == 'root':
            db_name = self.db_names[0]
            default_row = dict(database=db_name)
            for model in (
                self.object_parameter_definition_model,
                self.object_parameter_value_model,
                self.relationship_parameter_definition_model,
                self.relationship_parameter_value_model,
            ):
                model = model.empty_row_model
                model.set_default_row(**default_row)
                model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            return
        item_type = index.data(Qt.UserRole)
        db_map_dict = index.data(Qt.UserRole + 1)
        db_map = list(db_map_dict.keys())[0]
        db_name = self.db_map_to_name[db_map]
        item = db_map_dict[db_map]
        if item_type == 'object_class':
            default_row = dict(object_class_id=item['id'], object_class_name=item['name'], database=db_name)
            for model in (self.object_parameter_definition_model, self.object_parameter_value_model):
                model = model.empty_row_model
                model.set_default_row(**default_row)
                model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'object':
            parent_index = index.parent()
            parent_db_map_dict = parent_index.data(Qt.UserRole + 1)
            parent_item = parent_db_map_dict[db_map]
            default_row = dict(
                object_class_id=parent_item['id'], object_class_name=parent_item['name'], database=db_name
            )
            model = self.object_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            default_row.update(dict(object_id=item['id'], object_name=item['name']))
            model = self.object_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'relationship_class':
            default_row = dict(
                relationship_class_id=item['id'],
                relationship_class_name=item['name'],
                object_class_id_list=item['object_class_id_list'],
                object_class_name_list=item['object_class_name_list'],
                database=db_name,
            )
            for model in (self.relationship_parameter_definition_model, self.relationship_parameter_value_model):
                model = model.empty_row_model
                model.set_default_row(**default_row)
                model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
        elif item_type == 'relationship':
            parent_index = index.parent()
            parent_db_map_dict = parent_index.data(Qt.UserRole + 1)
            parent_item = parent_db_map_dict[db_map]
            default_row = dict(
                relationship_class_id=parent_item['id'],
                relationship_class_name=parent_item['name'],
                object_class_id_list=parent_item['object_class_id_list'],
                object_class_name_list=parent_item['object_class_name_list'],
                database=db_name,
            )
            model = self.relationship_parameter_definition_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)
            default_row.update(
                dict(
                    relationship_id=item['id'],
                    object_id_list=item['object_id_list'],
                    object_name_list=item['object_name_list'],
                )
            )
            model = self.relationship_parameter_value_model.empty_row_model
            model.set_default_row(**default_row)
            model.set_rows_to_default(model.rowCount() - 1, model.rowCount() - 1)

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

    @Slot("bool", "str", name="show_add_objects_form")
    def show_add_objects_form(self, checked=False, class_name=""):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, class_name=class_name)
        dialog.show()

    @Slot("bool", "str", name="show_add_relationship_classes_form")
    def show_add_relationship_classes_form(self, checked=False, object_class_one_name=None):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(self, object_class_one_name=object_class_one_name)
        dialog.show()

    @Slot("bool", "tuple", "str", "str", name="show_add_relationships_form")
    def show_add_relationships_form(
        self, checked=False, relationship_class_key=(), object_class_name="", object_name=""
    ):
        """Show dialog to let user select preferences for new relationships."""
        dialog = AddRelationshipsDialog(
            self,
            relationship_class_key=relationship_class_key,
            object_class_name=object_class_name,
            object_name=object_name,
        )
        dialog.show()

    def add_object_classes(self, object_class_d):
        """Insert new object classes."""
        added_names = set()
        for db_map, items in object_class_d.items():
            added, error_log = db_map.add_object_classes(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not added.count():
                continue
            self.icon_mngr.setup_object_pixmaps(added)
            self.add_object_classses_to_models(db_map, added)
            added_names.update(x.name for x in added)
        if not added_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully added new object class(es) '{}'.".format("', '".join(added_names))
        self.msg.emit(msg)
        if self.selected_object_class_ids:
            # Recompute self.selected_obj_tree_indexes['object_class']
            # since some new classes might have been inserted above those indexes
            # NOTE: This is only needed for object classes, since all other items are inserted at the bottom
            self.selected_obj_tree_indexes['object_class'] = {}
            is_selected = self.ui.treeView_object.selectionModel().isSelected
            root_index = self.object_tree_model.indexFromItem(self.object_tree_model.root_item)
            for i in range(self.object_tree_model.root_item.rowCount()):
                obj_cls_index = self.object_tree_model.index(i, 0, root_index)
                if is_selected(obj_cls_index):
                    self.selected_obj_tree_indexes['object_class'][obj_cls_index] = None
        return True

    def add_object_classses_to_models(self, db_map, added):
        self.object_tree_model.add_object_classes(db_map, added)

    def add_objects(self, object_d):
        """Insert new objects."""
        added_names = set()
        for db_map, items in object_d.items():
            added, error_log = db_map.add_objects(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not added.count():
                continue
            self.object_tree_model.add_objects(db_map, added)
            added_names.update(x.name for x in added)
        if not added_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully added new object(s) '{}'.".format("', '".join(added_names))
        self.msg.emit(msg)
        return True

    def add_relationship_classes(self, rel_cls_d):
        """Insert new relationship classes."""
        added_names = set()
        for db_map, items in rel_cls_d.items():
            added, error_log = db_map.add_wide_relationship_classes(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not added.count():
                continue
            self.add_relationship_classes_to_models(db_map, added)
            added_names.update(x.name for x in added)
        if not added_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully added new relationship class(es) '{}'.".format("', '".join(added_names))
        self.msg.emit(msg)
        return True

    def add_relationship_classes_to_models(self, db_map, added):
        self.object_tree_model.add_relationship_classes(db_map, added)
        self.relationship_parameter_definition_model.add_object_class_id_lists(db_map, added)
        self.relationship_parameter_value_model.add_object_class_id_lists(db_map, added)

    def add_relationships(self, relationship_d):
        """Insert new relationships."""
        added_names = set()
        for db_map, items in relationship_d.items():
            added, error_log = db_map.add_wide_relationships(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            added_names.update(x.name for x in added)
            if not added.count():
                continue
            self.add_relationships_to_models(db_map, added)
        if not added_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully added new relationship(s) '{}'.".format("', '".join(added_names))
        self.msg.emit(msg)
        return True

    def add_relationships_to_models(self, db_map, added):
        self.object_tree_model.add_relationships(db_map, added)

    @Slot("bool", name="show_edit_object_classes_form")
    def show_edit_object_classes_form(self, checked=False):
        indexes = self.selected_obj_tree_indexes.get('object_class')
        if not indexes:
            return
        db_map_dicts = [ind.data(Qt.UserRole + 1) for ind in indexes]
        dialog = EditObjectClassesDialog(self, db_map_dicts)
        dialog.show()

    @Slot("bool", name="show_edit_objects_form")
    def show_edit_objects_form(self, checked=False):
        indexes = self.selected_obj_tree_indexes.get('object')
        if not indexes:
            return
        db_map_dicts = [ind.data(Qt.UserRole + 1) for ind in indexes]
        dialog = EditObjectsDialog(self, db_map_dicts)
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
        db_map_dicts = [ind.data(Qt.UserRole + 1) for ind in indexes]
        dialog = EditRelationshipClassesDialog(self, db_map_dicts)
        dialog.show()

    @Slot("bool", name="show_edit_relationships_form")
    def show_edit_relationships_form(self, checked=False):
        # NOTE: Only edit relationships of the same class as the one in current index, for now...
        if self.widget_with_selection == self.ui.treeView_object:
            current = self.ui.treeView_object.currentIndex()
            if current.data(Qt.UserRole) != "relationship":
                return
            indexes = self.selected_obj_tree_indexes.get('relationship')
        elif self.widget_with_selection == self.ui.treeView_relationship:
            current = self.ui.treeView_relationship.currentIndex()
            if current.data(Qt.UserRole) != "relationship":
                return
            indexes = self.selected_rel_tree_indexes.get('relationship')
        ref_class_key = (current.parent().data(Qt.DisplayRole), current.parent().data(Qt.ToolTipRole))
        db_map_dicts = []
        for index in indexes:
            class_key = (index.parent().data(Qt.DisplayRole), index.parent().data(Qt.ToolTipRole))
            if class_key == ref_class_key:
                db_map_dicts.append(index.data(Qt.UserRole + 1))
        dialog = EditRelationshipsDialog(self, db_map_dicts, ref_class_key)
        dialog.show()

    @busy_effect
    def update_object_classes(self, object_class_d):
        """Update object classes."""
        updated_names = set()
        for db_map, items in object_class_d.items():
            updated, error_log = db_map.update_object_classes(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not updated.count():
                continue
            self.icon_mngr.setup_object_pixmaps(updated)
            self.update_object_classes_in_models(db_map, updated)
            updated_names.update(x.name for x in updated)
        if not updated_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully updated object class(es) '{}'.".format("', '".join(updated_names))
        self.msg.emit(msg)
        return True

    def update_object_classes_in_models(self, db_map, updated):
        self.object_tree_model.update_object_classes(db_map, updated)
        self.object_parameter_value_model.rename_object_classes(db_map, updated)
        self.object_parameter_definition_model.rename_object_classes(db_map, updated)
        self.relationship_parameter_value_model.rename_object_classes(db_map, updated)
        self.relationship_parameter_definition_model.rename_object_classes(db_map, updated)

    @busy_effect
    def update_objects(self, object_d):
        """Update objects."""
        updated_names = set()
        for db_map, items in object_d.items():
            updated, error_log = db_map.update_objects(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not updated.count():
                continue
            self.update_objects_in_models(db_map, updated)
            updated_names.update(x.name for x in updated)
        if not updated_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully updated object(s) '{}'.".format("', '".join(updated_names))
        self.msg.emit(msg)
        return True

    def update_objects_in_models(self, db_map, updated):
        self.object_tree_model.update_objects(db_map, updated)
        self.object_parameter_value_model.rename_objects(db_map, updated)
        self.relationship_parameter_value_model.rename_objects(db_map, updated)

    @busy_effect
    def update_relationship_classes(self, rel_cls_d):
        """Update relationship classes."""
        updated_names = set()
        for db_map, items in rel_cls_d.items():
            updated, error_log = db_map.update_wide_relationship_classes(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not updated.count():
                continue
            self.update_relationship_classes_in_models(db_map, updated)
            updated_names.update(x.name for x in updated)
        if not updated_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully updated relationship class(es) '{}'.".format("', '".join(updated_names))
        self.msg.emit(msg)
        return True

    def update_relationship_classes_in_models(self, db_map, updated):
        self.object_tree_model.update_relationship_classes(db_map, updated)
        self.relationship_parameter_value_model.rename_relationship_classes(db_map, updated)
        self.relationship_parameter_definition_model.rename_relationship_classes(db_map, updated)

    @busy_effect
    def update_relationships(self, relationship_d):
        """Update relationships."""
        updated_names = set()
        for db_map, items in relationship_d.items():
            updated, error_log = db_map.update_wide_relationships(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not updated.count():
                continue
            self.update_relationships_in_models(db_map, updated)
            updated_names.update(x.name for x in updated)
        if not updated_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully updated relationship(s) '{}'.".format("', '".join(updated_names))
        self.msg.emit(msg)
        return True

    def update_relationships_in_models(self, db_map, updated):
        self.object_tree_model.update_relationships(db_map, updated)

    def add_parameter_value_lists(self, parameter_value_list_d):
        added_names = set()
        for db_map, items in parameter_value_list_d.items():
            parents = []
            for item in items:
                parents.append(item.pop("parent"))
            added, error_log = db_map.add_wide_parameter_value_lists(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not added.count():
                continue
            for k, item in enumerate(added):
                parents[k].internalPointer().id = item.id
            added_names.update(x.name for x in added)
        if not added_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully added new parameter value list(s) '{}'.".format("', '".join(added_names))
        self.msg.emit(msg)
        return True

    def update_parameter_value_lists(self, parameter_value_list_d):
        updated_names = set()
        for db_map, items in parameter_value_list_d.items():
            updated, error_log = db_map.update_wide_parameter_value_lists(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not updated.count():
                continue
            self.object_parameter_definition_model.rename_parameter_value_lists(db_map, updated)
            self.relationship_parameter_definition_model.rename_parameter_value_lists(db_map, updated)
            updated_names.update(x.name for x in updated)
        if not updated_names:
            return False
        self.commit_available.emit(True)
        msg = "Successfully updated parameter value list(s) '{}'.".format("', '".join(updated_names))
        self.msg.emit(msg)
        return True

    @Slot("bool", name="show_manage_parameter_tags_form")
    def show_manage_parameter_tags_form(self, checked=False):
        dialog = ManageParameterTagsDialog(self)
        dialog.show()

    @busy_effect
    def add_parameter_tags(self, parameter_tag_d):
        """Add parameter tags."""
        added_tags = set()
        for db_map, items in parameter_tag_d.items():
            added, error_log = db_map.add_parameter_tags(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            added_tags.update(x.tag for x in added)
            if not added.count():
                continue
            self.parameter_tag_toolbar.add_tag_actions(db_map, added)
        if not added_tags:
            return False
        self.commit_available.emit(True)
        msg = "Successfully added new parameter tag(s) '{}'.".format("', '".join(added_tags))
        self.msg.emit(msg)
        return True

    @busy_effect
    def update_parameter_tags(self, parameter_tag_d):
        """Update parameter tags."""
        # TODO: update parameter value tables??
        updated_tags = set()
        for db_map, items in parameter_tag_d.items():
            updated, error_log = db_map.update_parameter_tags(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not updated.count():
                continue
            self.object_parameter_definition_model.rename_parameter_tags(db_map, updated)
            self.relationship_parameter_definition_model.rename_parameter_tags(db_map, updated)
            self.parameter_tag_toolbar.update_tag_actions(db_map, updated)
            updated_tags.update(x.tag for x in updated)
        if not updated_tags:
            return False
        self.commit_available.emit(True)
        msg = "Successfully updated parameter tag(s) '{}'.".format("', '".join(updated_tags))
        self.msg.emit(msg)
        return True

    @busy_effect
    def remove_parameter_tags(self, parameter_tag_d):
        """Remove parameter tags."""
        # TODO: remove from parameter value tables??
        removed = 0
        for db_map, ids in parameter_tag_d.items():
            try:
                db_map.remove_items(parameter_tag_ids=ids)
            except SpineDBAPIError as e:
                self.msg_error.emit(e.msg)
                continue
            self.object_parameter_definition_model.remove_parameter_tags(db_map, ids)
            self.relationship_parameter_definition_model.remove_parameter_tags(db_map, ids)
            self.parameter_tag_toolbar.remove_tag_actions(db_map, ids)
            removed += len(ids)
        if not removed:
            return False
        self.commit_available.emit(True)
        msg = "Successfully removed {} parameter tag(s).".format(removed)
        self.msg.emit(msg)
        return True

    def show_parameter_value_editor(self, index, table_view, value=None):
        """Shows the parameter value editor for the given index of given table view.
        """
        value_name = tree_graph_view_parameter_value_name(index, table_view)
        editor = ParameterValueEditor(index, value_name=value_name, value=value, parent_widget=self)
        editor.show()

    @Slot("QModelIndex", "QVariant", name="set_parameter_value_data")
    def set_parameter_value_data(self, index, new_value):  # pylint: disable=no-self-use
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
        db_column = header.index('database')
        db_name = index.sibling(index.row(), db_column).data(Qt.DisplayRole)
        db_map = self.db_name_to_map.get(db_name)
        if index.model().setData(index, new_value) and header[index.column()] == 'parameter_name' and db_map:
            parameter_id_column = header.index('id')
            parameter_id = index.sibling(index.row(), parameter_id_column).data(Qt.DisplayRole)
            if 'object_class_id' in header:
                object_class_id_column = header.index('object_class_id')
                object_class_id = index.sibling(index.row(), object_class_id_column).data(Qt.DisplayRole)
                parameter = dict(id=parameter_id, object_class_id=object_class_id, name=new_value)
                self.object_parameter_value_model.rename_parameter(db_map, parameter)
            elif 'relationship_class_id' in header:
                relationship_class_id_column = header.index('relationship_class_id')
                relationship_class_id = index.sibling(index.row(), relationship_class_id_column).data(Qt.DisplayRole)
                parameter = dict(id=parameter_id, relationship_class_id=relationship_class_id, name=new_value)
                self.relationship_parameter_value_model.rename_parameter(db_map, parameter)
        return True

    def show_commit_session_prompt(self):
        """Shows the commit session message box."""
        qsettings = self.qsettings()
        commit_at_exit = int(qsettings.value("appSettings/commitAtExit", defaultValue="1"))
        if commit_at_exit == 0:
            # Don't commit session and don't show message box
            return
        if commit_at_exit == 1:  # Default
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
        if any(db_map.has_pending_changes() for db_map in self.db_maps):
            self.show_commit_session_prompt()
        if event:
            event.accept()
