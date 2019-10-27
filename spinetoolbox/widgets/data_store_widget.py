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
from ..config import MAINWINDOW_SS, STATUSBAR_SS
from .custom_delegates import (
    DatabaseNameDelegate,
    ParameterDefaultValueDelegate,
    TagListDelegate,
    ValueListDelegate,
    ObjectParameterValueDelegate,
    ObjectParameterNameDelegate,
    ObjectClassNameDelegate,
    ObjectNameDelegate,
    RelationshipParameterValueDelegate,
    RelationshipParameterNameDelegate,
    RelationshipClassNameDelegate,
    ObjectNameListDelegate,
)
from .add_db_items_dialogs import (
    AddObjectClassesDialog,
    AddObjectsDialog,
    AddRelationshipClassesDialog,
    AddRelationshipsDialog,
)
from .edit_db_items_dialogs import (
    EditObjectClassesDialog,
    EditObjectsDialog,
    EditRelationshipClassesDialog,
    EditRelationshipsDialog,
    ManageParameterTagsDialog,
)
from .manage_db_items_dialog import CommitDialog
from ..widgets.parameter_value_editor import ParameterValueEditor
from ..widgets.toolbars import ParameterTagToolBar
from ..widgets.custom_qwidgets import NotificationIcon
from ..mvcmodels.compound_parameter_models import (
    CompoundObjectParameterDefinitionModel,
    CompoundObjectParameterValueModel,
    CompoundRelationshipParameterDefinitionModel,
    CompoundRelationshipParameterValueModel,
)
from ..mvcmodels.parameter_value_list_model import ParameterValueListModel
from ..helpers import busy_effect, format_string_list
from ..plotting import tree_graph_view_parameter_value_name


class DataStoreForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        project (SpineToolboxProject): The project instance that owns this form
        ui: UI definition of the form that is initialized
        db_maps (iter): DiffDatabaseMapping instances
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
        self.db_maps = db_maps
        self.db_mngr = project.db_mngr
        self.db_mngr.add_db_maps(*db_maps)
        # Selected ids
        self.selected_ent_cls_ids = {"object class": {}, "relationship class": {}}
        self.selected_ent_ids = {"object": {}, "relationship": {}}
        self.selected_param_def_ids = {"object class": {}, "relationship class": {}}
        self.selected_parameter_tag_ids = dict()
        # Parameter tag toolbar
        self.parameter_tag_toolbar = ParameterTagToolBar(self, self.db_mngr, *db_maps)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)
        # Models
        self.object_parameter_value_model = CompoundObjectParameterValueModel(self, self.db_mngr, *db_maps)
        self.relationship_parameter_value_model = CompoundRelationshipParameterValueModel(self, self.db_mngr, *db_maps)
        self.object_parameter_definition_model = CompoundObjectParameterDefinitionModel(self, self.db_mngr, *db_maps)
        self.relationship_parameter_definition_model = CompoundRelationshipParameterDefinitionModel(
            self, self.db_mngr, *db_maps
        )
        self.parameter_value_list_model = ParameterValueListModel(self, self.db_mngr, *db_maps)
        # Setup views
        self.ui.tableView_object_parameter_value.setModel(self.object_parameter_value_model)
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_model)
        self.ui.tableView_object_parameter_definition.setModel(self.object_parameter_definition_model)
        self.ui.tableView_relationship_parameter_definition.setModel(self.relationship_parameter_definition_model)
        self.ui.treeView_parameter_value_list.setModel(self.parameter_value_list_model)
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        visible_rows = int(max_screen_height / self.default_row_height)
        for view in (
            self.ui.tableView_object_parameter_value,
            self.ui.tableView_relationship_parameter_value,
            self.ui.tableView_object_parameter_definition,
            self.ui.tableView_relationship_parameter_definition,
        ):
            view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            view.verticalHeader().setDefaultSectionSize(self.default_row_height)
            view.horizontalHeader().setResizeContentsPrecision(visible_rows)
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
        self.ui.actionCommit.triggered.connect(self._prompt_and_commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)
        self.ui.actionClose.triggered.connect(self.close)
        # Object tree
        self.ui.treeView_object.selectionModel().selectionChanged.connect(self._handle_object_tree_selection_changed)
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
        # DB manager
        # Added
        self.db_mngr.object_classes_added.connect(self.receive_object_classes_added)
        self.db_mngr.objects_added.connect(self.receive_objects_added)
        self.db_mngr.relationship_classes_added.connect(self.receive_relationship_classes_added)
        self.db_mngr.relationships_added.connect(self.receive_relationships_added)
        self.db_mngr.parameter_definitions_added.connect(self.receive_parameter_definitions_added)
        self.db_mngr.parameter_values_added.connect(self.receive_parameter_values_added)
        self.db_mngr.parameter_value_lists_added.connect(self.receive_parameter_value_lists_added)
        # Updated
        self.db_mngr.object_classes_updated.connect(self.receive_object_classes_updated)
        self.db_mngr.objects_updated.connect(self.receive_objects_updated)
        self.db_mngr.relationship_classes_updated.connect(self.receive_relationship_classes_updated)
        self.db_mngr.relationships_updated.connect(self.receive_relationships_updated)
        self.db_mngr.parameter_definitions_updated.connect(self.receive_parameter_definitions_updated)
        self.db_mngr.parameter_values_updated.connect(self.receive_parameter_values_updated)
        self.db_mngr.parameter_value_lists_updated.connect(self.receive_parameter_value_lists_updated)
        # Removed
        self.db_mngr.object_classes_removed.connect(self.receive_object_classes_removed)
        self.db_mngr.objects_removed.connect(self.receive_objects_removed)
        self.db_mngr.relationship_classes_removed.connect(self.receive_relationship_classes_removed)
        self.db_mngr.relationships_removed.connect(self.receive_relationships_removed)
        self.db_mngr.parameter_definitions_removed.connect(self.receive_parameter_definitions_removed)
        self.db_mngr.parameter_values_removed.connect(self.receive_parameter_values_removed)
        self.db_mngr.parameter_value_lists_removed.connect(self.receive_parameter_value_lists_removed)
        # Error
        self.db_mngr.msg_error.connect(self.receive_db_mngr_error_msg)

    @Slot("QVariant", name="receive_db_mngr_error_msg")
    def receive_db_mngr_error_msg(self, db_map_error_log):
        msg = ""
        for db_map, error_log in db_map_error_log.items():
            database = "From " + db_map.codename + ":"
            formatted_log = format_string_list(error_log)
            msg += format_string_list([database, formatted_log])
        self.msg_error.emit(msg)

    def qsettings(self):
        """Returns the QSettings instance from ToolboxUI."""
        return self._project._toolbox._qsettings

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Append regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        icon = NotificationIcon(msg)
        icon.pressed.connect(lambda icon=icon: self.ui.statusbar.removeWidget(icon))
        self.ui.statusbar.insertWidget(0, icon)

    @Slot(str, name="add_error_message")
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show in QErrorMessage
        """
        self.err_msg.showMessage(msg)

    @Slot("QItemSelection", "QItemSelection", name="_handle_object_tree_selection_changed")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Called when the object tree selection changes.
        Set default rows and apply filters on parameter models."""
        for index in deselected.indexes():
            self.object_tree_model.deselect_index(index)
        for index in selected.indexes():
            self.object_tree_model.select_index(index)

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
            # No tags selected
            self.selected_param_def_ids["object class"] = {}
            self.selected_param_def_ids["relationship class"] = {}
        else:
            # At least one tag selected: init dict like below so in case no parameter has the tag,
            # all of them are filtered
            self.selected_param_def_ids["object class"] = {(None, 0): set()}
            self.selected_param_def_ids["relationship class"] = {(None, 0): set()}
            # Find selected parameter definitions
            selected_param_defs = self.db_mngr.find_cascading_parameter_definitions_by_tag(
                self.selected_parameter_tag_ids
            )
            for db_map, param_defs in selected_param_defs.items():
                for param_def in param_defs:
                    if "object_class_id" in param_def:
                        self.selected_param_def_ids["object class"].setdefault(
                            (db_map, param_def["object_class_id"]), set()
                        ).add(param_def["id"])
                    elif "relationship_class_id" in param_def:
                        self.selected_param_def_ids["relationship class"].setdefault(
                            (db_map, param_def["relationship_class_id"]), set()
                        ).add(param_def["id"])
        self.update_filter()

    @Slot("bool", name="_handle_commit_available")
    def _handle_commit_available(self, on):
        self.ui.actionCommit.setEnabled(on)
        self.ui.actionRollback.setEnabled(on)

    @Slot("bool", name="_prompt_and_commit_session")
    def _prompt_and_commit_session(self, checked=False):
        """Query user for a commit message and commit changes to source database returning False if cancelled."""
        if not any(db_map.has_pending_changes() for db_map in self.db_maps):
            self.msg.emit("Nothing to commit yet.")
            return
        db_names = [x.codename for x in self.db_maps]
        dialog = CommitDialog(self, *db_names)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return False
        self.commit_session(dialog.commit_msg)
        return True

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
        self.init_parameter_value_list_model()
        self.init_parameter_tag_toolbar()
        self.set_default_parameter_data()

    def init_object_tree_model(self):
        """Initialize object tree model."""
        self.object_tree_model.build_tree()
        self.ui.treeView_object.expand(self.object_tree_model.root_index)
        self.ui.treeView_object.resizeColumnToContents(0)

    def init_parameter_value_models(self):
        """Initialize parameter value models."""
        self.object_parameter_value_model.init_model()
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()
        self.relationship_parameter_value_model.init_model()
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()

    def init_parameter_definition_models(self):
        """Initialize parameter (definition) models."""
        self.object_parameter_definition_model.init_model()
        self.ui.tableView_object_parameter_definition.resizeColumnsToContents()
        self.relationship_parameter_definition_model.init_model()
        self.ui.tableView_relationship_parameter_definition.resizeColumnsToContents()

    def init_parameter_value_list_model(self):
        """Initialize parameter value_list models."""
        self.parameter_value_list_model.build_tree()
        for item in self.parameter_value_list_model.visit_all():
            index = self.parameter_value_list_model.index_from_item(item)
            self.ui.treeView_parameter_value_list.expand(index)
        self.ui.treeView_parameter_value_list.resizeColumnToContents(0)
        self.ui.treeView_parameter_value_list.header().hide()

    def init_parameter_tag_toolbar(self):
        """Initialize parameter tag toolbar."""
        self.parameter_tag_toolbar.init_toolbar()

    def _setup_delegate(self, table_view, column, delegate_class):
        """Convenience method to setup a delegate for a view."""
        delegate = delegate_class(self, self.db_mngr)
        table_view.setItemDelegateForColumn(column, delegate)
        delegate.data_committed.connect(self.set_parameter_data)
        return delegate

    def setup_delegates(self):
        """Set delegates for tables."""
        # Parameter definitions
        for table_view in (
            self.ui.tableView_object_parameter_definition,
            self.ui.tableView_relationship_parameter_definition,
        ):
            h = table_view.model().header.index
            self._setup_delegate(table_view, h("database"), DatabaseNameDelegate)
            self._setup_delegate(table_view, h("parameter_tag_list"), TagListDelegate)
            self._setup_delegate(table_view, h("value_list_name"), ValueListDelegate)
            delegate = self._setup_delegate(table_view, h("default_value"), ParameterDefaultValueDelegate)
            delegate.parameter_value_editor_requested.connect(
                lambda index, value, table_view=table_view: self.show_parameter_value_editor(
                    index, table_view, value=value
                )
            )
        # Parameter values
        for table_view in (self.ui.tableView_object_parameter_value, self.ui.tableView_relationship_parameter_value):
            h = table_view.model().header.index
            self._setup_delegate(table_view, h("database"), DatabaseNameDelegate)
        # Object parameters
        for table_view in (self.ui.tableView_object_parameter_value, self.ui.tableView_object_parameter_definition):
            h = table_view.model().header.index
            self._setup_delegate(table_view, h("object_class_name"), ObjectClassNameDelegate)
        # Relationship parameters
        for table_view in (
            self.ui.tableView_relationship_parameter_value,
            self.ui.tableView_relationship_parameter_definition,
        ):
            h = table_view.model().header.index
            self._setup_delegate(table_view, h("relationship_class_name"), RelationshipClassNameDelegate)
        # Object parameter value
        table_view = self.ui.tableView_object_parameter_value
        h = table_view.model().header.index
        delegate = self._setup_delegate(table_view, h("value"), ObjectParameterValueDelegate)
        delegate.parameter_value_editor_requested.connect(
            lambda index, value, table_view=table_view: self.show_parameter_value_editor(index, table_view, value=value)
        )
        self._setup_delegate(table_view, h("parameter_name"), ObjectParameterNameDelegate)
        self._setup_delegate(table_view, h("object_name"), ObjectNameDelegate)
        # Relationship parameter value
        table_view = self.ui.tableView_relationship_parameter_value
        h = table_view.model().header.index
        delegate = self._setup_delegate(table_view, h("value"), RelationshipParameterValueDelegate)
        delegate.parameter_value_editor_requested.connect(
            lambda index, value, table_view=table_view: self.show_parameter_value_editor(index, table_view, value=value)
        )
        self._setup_delegate(table_view, h("parameter_name"), RelationshipParameterNameDelegate)
        self._setup_delegate(table_view, h("object_name_list"), ObjectNameListDelegate)

    def selected_entity_class_ids(self, entity_class_type):
        """Return object class ids selected in object tree *and* parameter tag toolbar."""
        tree_class_ids = self.selected_ent_cls_ids[entity_class_type]
        tag_class_ids = dict()
        for db_map, class_id in self.selected_param_def_ids[entity_class_type]:
            tag_class_ids.setdefault(db_map, set()).add(class_id)
        if not tag_class_ids:
            return tree_class_ids
        if not tree_class_ids:
            return tag_class_ids
        return {
            db_map: class_ids.intersection(tag_class_ids.get(db_map, {}))
            for db_map, class_ids in tree_class_ids.items()
        }

    def set_default_parameter_data(self, index=None):
        """Set default rows for parameter models according to selection in object or relationship tree."""
        if index is None or not index.isValid():
            default_data = dict(database=next(iter(self.db_maps)).codename)
        else:
            default_data = index.model().item_from_index(index).default_parameter_data()
        for model in (
            self.object_parameter_definition_model,
            self.object_parameter_value_model,
            self.relationship_parameter_definition_model,
            self.relationship_parameter_value_model,
        ):
            model.empty_model.set_default_row(**default_data)
            model.empty_model.set_rows_to_default(model.empty_model.rowCount() - 1)

    def update_filter(self):
        """Update filter on parameter models."""
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
        dialog = AddObjectClassesDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    @Slot("bool", "str", name="show_add_objects_form")
    def show_add_objects_form(self, checked=False, class_name=""):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, self.db_mngr, *self.db_maps, class_name=class_name)
        dialog.show()

    @Slot("bool", "str", name="show_add_relationship_classes_form")
    def show_add_relationship_classes_form(self, checked=False, object_class_one_name=None):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(
            self, self.db_mngr, *self.db_maps, object_class_one_name=object_class_one_name
        )
        dialog.show()

    @Slot("bool", "tuple", "str", "str", name="show_add_relationships_form")
    def show_add_relationships_form(
        self, checked=False, relationship_class_key=(), object_class_name="", object_name=""
    ):
        """Show dialog to let user select preferences for new relationships."""
        dialog = AddRelationshipsDialog(
            self,
            self.db_mngr,
            *self.db_maps,
            relationship_class_key=relationship_class_key,
            object_class_name=object_class_name,
            object_name=object_name,
        )
        dialog.show()

    @Slot("bool", name="show_edit_object_classes_form")
    def show_edit_object_classes_form(self, checked=False):
        selected = {ind.internalPointer() for ind in self.object_tree_model.selected_object_class_indexes}
        dialog = EditObjectClassesDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool", name="show_edit_objects_form")
    def show_edit_objects_form(self, checked=False):
        selected = {ind.internalPointer() for ind in self.object_tree_model.selected_object_indexes}
        dialog = EditObjectsDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool", name="show_edit_relationship_classes_form")
    def show_edit_relationship_classes_form(self, checked=False):
        selected = {
            ind.internalPointer()
            for ind in self.object_tree_model.selected_relationship_class_indexes.keys()
            | self.relationship_tree_model.selected_relationship_class_indexes.keys()
        }
        dialog = EditRelationshipClassesDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool", name="show_edit_relationships_form")
    def show_edit_relationships_form(self, checked=False):
        # NOTE: Only edits relationships that are in the same class
        selected = {
            ind.internalPointer()
            for ind in self.object_tree_model.selected_relationship_indexes.keys()
            | self.relationship_tree_model.selected_relationship_indexes.keys()
        }
        first_item = next(iter(selected))
        relationship_class_key = first_item.parent_item.display_id
        selected = {item for item in selected if item.parent_item.display_id == relationship_class_key}
        dialog = EditRelationshipsDialog(self, self.db_mngr, selected, relationship_class_key)
        dialog.show()

    @Slot("bool", name="show_manage_parameter_tags_form")
    def show_manage_parameter_tags_form(self, checked=False):
        dialog = ManageParameterTagsDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    def receive_items_changed(self, action, item_type, db_map_data):
        """Enables or disables actions and informs the user about what just happened."""
        msg = f"<html> Successfully {action} {item_type} item(s)"
        name_keys = {"parameter definition": "parameter_name", "parameter tag": "tag", "parameter value": None}
        name_key = name_keys.get(item_type, "name")
        if name_key:
            names = {item[name_key] for db_map, data in db_map_data.items() for item in data}
            msg += ":" + format_string_list(names)
        msg += "</html>"
        self.msg.emit(msg)
        self.commit_available.emit(True)

    @Slot("QVariant", name="receive_object_classes_added")
    def receive_object_classes_added(self, db_map_data):
        self.receive_items_changed("added", "object class", db_map_data)

    @Slot("QVariant", name="receive_objects_added")
    def receive_objects_added(self, db_map_data):
        self.receive_items_changed("added", "object", db_map_data)

    @Slot("QVariant", name="receive_relationship_classes_added")
    def receive_relationship_classes_added(self, db_map_data):
        self.receive_items_changed("added", "relationship class", db_map_data)

    @Slot("QVariant", name="receive_relationships_added")
    def receive_relationships_added(self, db_map_data):
        self.receive_items_changed("added", "relationship", db_map_data)

    @Slot("QVariant", name="receive_parameter_definitions_added")
    def receive_parameter_definitions_added(self, db_map_data):
        self.receive_items_changed("added", "parameter definition", db_map_data)

    @Slot("QVariant", name="receive_parameter_values_added")
    def receive_parameter_values_added(self, db_map_data):
        self.receive_items_changed("added", "parameter value", db_map_data)

    @Slot("QVariant", name="receive_parameter_value_lists_added")
    def receive_parameter_value_lists_added(self, db_map_data):
        self.receive_items_changed("added", "parameter value list", db_map_data)

    @Slot("QVariant", name="receive_parameter_tags_added")
    def receive_parameter_tags_added(self, db_map_data):
        self.receive_items_changed("added", "parameter tag", db_map_data)

    @Slot("QVariant", name="receive_object_classes_updated")
    def receive_object_classes_updated(self, db_map_data):
        self.receive_items_changed("updated", "object class", db_map_data)

    @Slot("QVariant", name="receive_objects_updated")
    def receive_objects_updated(self, db_map_data):
        self.receive_items_changed("updated", "object", db_map_data)

    @Slot("QVariant", name="receive_relationship_classes_updated")
    def receive_relationship_classes_updated(self, db_map_data):
        self.receive_items_changed("updated", "relationship class", db_map_data)

    @Slot("QVariant", name="receive_relationships_updated")
    def receive_relationships_updated(self, db_map_data):
        self.receive_items_changed("updated", "relationship", db_map_data)

    @Slot("QVariant", name="receive_parameter_definitions_updated")
    def receive_parameter_definitions_updated(self, db_map_data):
        self.receive_items_changed("updated", "parameter definition", db_map_data)

    @Slot("QVariant", name="receive_parameter_values_updated")
    def receive_parameter_values_updated(self, db_map_data):
        self.receive_items_changed("updated", "parameter value", db_map_data)

    @Slot("QVariant", name="receive_parameter_value_lists_updated")
    def receive_parameter_value_lists_updated(self, db_map_data):
        self.receive_items_changed("updated", "parameter value list", db_map_data)

    @Slot("QVariant", name="receive_parameter_tags_updated")
    def receive_parameter_tags_updated(self, db_map_data):
        self.receive_items_changed("updated", "parameter tag", db_map_data)

    @Slot("QVariant", name="receive_object_classes_removed")
    def receive_object_classes_removed(self, db_map_data):
        self.receive_items_changed("removed", "object class", db_map_data)

    @Slot("QVariant", name="receive_objects_removed")
    def receive_objects_removed(self, db_map_data):
        self.receive_items_changed("removed", "object", db_map_data)

    @Slot("QVariant", name="receive_relationship_classes_removed")
    def receive_relationship_classes_removed(self, db_map_data):
        self.receive_items_changed("removed", "relationship class", db_map_data)

    @Slot("QVariant", name="receive_relationships_removed")
    def receive_relationships_removed(self, db_map_data):
        self.receive_items_changed("removed", "relationship", db_map_data)

    @Slot("QVariant", name="receive_parameter_definitions_removed")
    def receive_parameter_definitions_removed(self, db_map_data):
        self.receive_items_changed("removed", "parameter definition", db_map_data)

    @Slot("QVariant", name="receive_parameter_values_removed")
    def receive_parameter_values_removed(self, db_map_data):
        self.receive_items_changed("removed", "parameter value", db_map_data)

    @Slot("QVariant", name="receive_parameter_value_lists_removed")
    def receive_parameter_value_lists_removed(self, db_map_data):
        self.receive_items_changed("removed", "parameter value list", db_map_data)

    @Slot("QVariant", name="receive_parameter_tags_removed")
    def receive_parameter_tags_removed(self, db_map_data):
        self.receive_items_changed("removed", "parameter tag", db_map_data)

    @busy_effect
    def show_parameter_value_editor(self, index, table_view, value=None):
        """Shows the parameter value editor for the given index of given table view.
        """
        value_name = tree_graph_view_parameter_value_name(index, table_view)
        editor = ParameterValueEditor(index, value_name=value_name, value=value, parent_widget=self)
        editor.show()

    @Slot("QModelIndex", "QVariant", name="set_parameter_data")
    def set_parameter_data(self, index, new_value):  # pylint: disable=no-self-use
        """Update (object or relationship) parameter definition or value with newly edited data."""
        return index.model().setData(index, new_value)

    def _prompt_close_and_commit(self):
        """Prompts user for window closing and commits if requested returning True if window should close."""
        qsettings = self.qsettings()
        commit_at_exit = int(qsettings.value("appSettings/commitAtExit", defaultValue="1"))
        if commit_at_exit == 0:
            # Don't commit session and don't show message box
            return True
        if commit_at_exit == 1:  # Default
            # Show message box
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Commit Pending Changes")
            msg.setText("The current session has uncommitted changes. Do you want to commit them now?")
            msg.setInformativeText("WARNING: If you choose not to commit, all changes will be lost.")
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg.button(QMessageBox.Save).setText("Commit And Close ")
            msg.button(QMessageBox.Discard).setText("Discard Changes And Close")
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()
            if answer == QMessageBox.Cancel:
                return False
            chk = chkbox.checkState()
            if answer == QMessageBox.Save:
                committed = self._prompt_and_commit_session()
                if not committed:
                    return False
                if chk == 2:
                    # Save preference
                    qsettings.setValue("appSettings/commitAtExit", "2")
            else:
                if chk == 2:
                    # Save preference
                    qsettings.setValue("appSettings/commitAtExit", "0")
        elif commit_at_exit == 2:
            # Commit session and don't show message box
            committed = self._prompt_and_commit_session()
            if not committed:
                return False
        else:
            qsettings.setValue("appSettings/commitAtExit", "1")
        return True

    def restore_ui(self):
        """Restore UI state from previous session."""
        qsettings = self.qsettings()
        qsettings.beginGroup(self.settings_group)
        window_size = qsettings.value("windowSize")
        window_pos = qsettings.value("windowPosition")
        window_state = qsettings.value("windowState")
        window_maximized = qsettings.value("windowMaximized", defaultValue='false')
        n_screens = qsettings.value("n_screens", defaultValue=1)
        header_states = (
            qsettings.value("objParDefHeaderState"),
            qsettings.value("objParValHeaderState"),
            qsettings.value("relParDefHeaderState"),
            qsettings.value("relParValHeaderState"),
        )
        qsettings.endGroup()
        views = (
            self.ui.tableView_object_parameter_definition.horizontalHeader(),
            self.ui.tableView_object_parameter_value.horizontalHeader(),
            self.ui.tableView_relationship_parameter_definition.horizontalHeader(),
            self.ui.tableView_relationship_parameter_value.horizontalHeader(),
        )
        models = (
            self.object_parameter_definition_model,
            self.object_parameter_value_model,
            self.relationship_parameter_definition_model,
            self.relationship_parameter_value_model,
        )
        for view, model, state in zip(views, models, header_states):
            if state:
                curr_state = view.saveState()
                view.restoreState(state)
                if view.count() != model.columnCount():
                    # This can happen the first time the user switches to this version,
                    # because of hidden columns in past versions
                    view.restoreState(curr_state)
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

    def save_window_state(self):
        """Save window state parameters (size, position, state) via QSettings."""
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

    def closeEvent(self, event):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event
        """
        if any(db_map.has_pending_changes() for db_map in self.db_maps):
            want_to_close = self._prompt_close_and_commit()
            if not want_to_close:
                event.ignore()
                return
        # Save UI form state
        self.save_window_state()
        for db_map in self.db_maps:
            db_map.connection.close()
        event.accept()
