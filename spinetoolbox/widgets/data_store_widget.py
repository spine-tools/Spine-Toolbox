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
    ObjectParameterValueDelegate,
    ObjectParameterDefinitionDelegate,
    RelationshipParameterValueDelegate,
    RelationshipParameterDefinitionDelegate,
)
from .custom_qdialog import (
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
from ..widgets.parameter_value_editor import ParameterValueEditor
from ..widgets.toolbars import ParameterTagToolBar
from ..mvcmodels.compound_parameter_models import (
    CompoundObjectParameterDefinitionModel,
    CompoundObjectParameterValueModel,
    CompoundRelationshipParameterDefinitionModel,
    CompoundRelationshipParameterValueModel,
)
from ..mvcmodels.parameter_value_list_model import ParameterValueListModel
from ..spine_db_manager import SpineDBManager
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
        keyed_db_maps = {db_map.codename: db_map for db_map in db_maps}
        self.db_maps = db_maps
        self.keyed_db_maps = keyed_db_maps
        self.db_mngr = SpineDBManager(*db_maps)
        # Selected ids
        self.selected_object_class_ids = dict()
        self.selected_object_ids = dict()
        self.selected_relationship_class_ids = dict()
        self.selected_object_id_lists = dict()
        self.selected_parameter_tag_ids = dict()
        self.selected_obj_parameter_definition_ids = dict()
        self.selected_rel_parameter_definition_ids = dict()
        # Parameter tag toolbar
        self.parameter_tag_toolbar = ParameterTagToolBar(self, db_maps)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)
        # Models
        self.object_parameter_value_model = CompoundObjectParameterValueModel(self, self.db_mngr)
        self.relationship_parameter_value_model = CompoundRelationshipParameterValueModel(self, self.db_mngr)
        self.object_parameter_definition_model = CompoundObjectParameterDefinitionModel(self, self.db_mngr)
        self.relationship_parameter_definition_model = CompoundRelationshipParameterDefinitionModel(self, self.db_mngr)
        self.parameter_value_list_model = ParameterValueListModel(self, keyed_db_maps)
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
        # Parameter tables delegates
        for table_view in (
            self.ui.tableView_object_parameter_definition,
            self.ui.tableView_relationship_parameter_definition,
            self.ui.tableView_object_parameter_value,
            self.ui.tableView_relationship_parameter_value,
        ):
            # pylint: disable=cell-var-from-loop
            table_view.itemDelegate().data_committed.connect(self.set_parameter_data)
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

        # DB manager
        # Added
        self.db_mngr.object_classes_added.connect(self.receive_object_classes_added)
        self.db_mngr.objects_added.connect(self.receive_objects_added)
        self.db_mngr.relationship_classes_added.connect(self.receive_relationship_classes_added)
        self.db_mngr.relationships_added.connect(self.receive_relationships_added)
        # Updated
        self.db_mngr.object_classes_updated.connect(self.receive_object_classes_updated)
        self.db_mngr.objects_updated.connect(self.receive_objects_updated)
        self.db_mngr.relationship_classes_updated.connect(self.receive_relationship_classes_updated)
        self.db_mngr.relationships_updated.connect(self.receive_relationships_updated)
        self.db_mngr.parameter_definitions_updated.connect(self.receive_parameter_definitions_updated)
        self.db_mngr.parameter_values_updated.connect(self.receive_parameter_values_updated)
        # Removed
        self.db_mngr.object_classes_removed.connect(self.receive_object_classes_removed)
        self.db_mngr.objects_removed.connect(self.receive_objects_removed)
        self.db_mngr.relationship_classes_removed.connect(self.receive_relationship_classes_removed)
        self.db_mngr.relationships_removed.connect(self.receive_relationships_removed)
        self.db_mngr.parameter_definitions_removed.connect(self.receive_parameter_definitions_removed)
        self.db_mngr.parameter_values_removed.connect(self.receive_parameter_values_removed)
        # Error
        self.db_mngr.msg_error.connect(self.add_db_mngr_error_msg)

    @Slot("QVariant", name="add_message")
    def add_db_mngr_error_msg(self, db_map_error_log):
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
            # No tags selected
            self.selected_obj_parameter_definition_ids = {}
            self.selected_rel_parameter_definition_ids = {}
        else:
            # At least one tag selected: init dict like below so in case no parameter has the tag,
            # all of them are filtered
            self.selected_obj_parameter_definition_ids = {(None, None): None}
            self.selected_rel_parameter_definition_ids = {(None, None): None}
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

    @property
    def all_selected_object_class_ids(self):
        """Return object class ids selected in object tree *and* parameter tag toolbar."""
        tree_object_class_ids = self.selected_object_class_ids
        tag_object_class_ids = dict()
        for db_map, id_ in self.selected_obj_parameter_definition_ids.keys():
            tag_object_class_ids.setdefault(db_map, set()).add(id_)
        if not tag_object_class_ids:
            return tree_object_class_ids
        if not tree_object_class_ids:
            return tag_object_class_ids
        return {
            key: value.intersection(tag_object_class_ids.get(key, {})) for key, value in tree_object_class_ids.items()
        }

    @property
    def all_selected_relationship_class_ids(self):
        """Return relationship class ids selected in relationship tree *and* parameter tag toolbar."""
        tree_relationship_class_ids = self.selected_relationship_class_ids
        tag_relationship_class_ids = dict()
        for db_map, id_ in self.selected_rel_parameter_definition_ids.keys():
            tag_relationship_class_ids.setdefault(db_map, set()).add(id_)
        if not tag_relationship_class_ids:
            return tree_relationship_class_ids
        if not tree_relationship_class_ids:
            return tag_relationship_class_ids
        return {
            key: value.intersection(tag_relationship_class_ids.get(key, {}))
            for key, value in tree_relationship_class_ids.items()
        }

    def set_default_parameter_data(self, index=None):
        """Set default rows for parameter models according to selection in object or relationship tree."""
        return
        if index is None:
            default_data = dict(database=next(iter(self.db_maps)).codename)
        else:
            default_data = index.internalPointer().default_parameter_data()
        for model in (
            self.object_parameter_definition_model,
            self.object_parameter_value_model,
            self.relationship_parameter_definition_model,
            self.relationship_parameter_value_model,
        ):
            model.empty_model.set_default_row(**default_data)
            model.empty_model.set_rows_to_default(model.empty_model.rowCount() - 1)

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
        dialog = AddObjectClassesDialog(self, self.db_mngr.icon_mngr, self.db_maps)
        dialog.data_committed.connect(self.db_mngr.add_object_classes)
        dialog.show()

    @Slot("bool", "str", name="show_add_objects_form")
    def show_add_objects_form(self, checked=False, class_name=""):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, self.db_maps, class_name=class_name)
        dialog.data_committed.connect(self.db_mngr.add_objects)
        dialog.show()

    @Slot("bool", "str", name="show_add_relationship_classes_form")
    def show_add_relationship_classes_form(self, checked=False, object_class_one_name=None):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(self, self.db_maps, object_class_one_name=object_class_one_name)
        dialog.data_committed.connect(self.db_mngr.add_relationship_classes)
        dialog.show()

    @Slot("bool", "tuple", "str", "str", name="show_add_relationships_form")
    def show_add_relationships_form(
        self, checked=False, relationship_class_key=(), object_class_name="", object_name=""
    ):
        """Show dialog to let user select preferences for new relationships."""
        dialog = AddRelationshipsDialog(
            self,
            self.db_maps,
            relationship_class_key=relationship_class_key,
            object_class_name=object_class_name,
            object_name=object_name,
        )
        dialog.data_committed.connect(self.db_mngr.add_relationships)
        dialog.show()

    @Slot("bool", name="show_edit_object_classes_form")
    def show_edit_object_classes_form(self, checked=False):
        selected = {ind.internalPointer() for ind in self.object_tree_model.selected_object_class_indexes}
        dialog = EditObjectClassesDialog(self, self.db_mngr.icon_mngr, selected)
        dialog.data_committed.connect(self.db_mngr.update_object_classes)
        dialog.show()

    @Slot("bool", name="show_edit_objects_form")
    def show_edit_objects_form(self, checked=False):
        selected = {ind.internalPointer() for ind in self.object_tree_model.selected_object_indexes}
        dialog = EditObjectsDialog(self, selected)
        dialog.data_committed.connect(self.db_mngr.update_objects)
        dialog.show()

    @Slot("bool", name="show_edit_relationship_classes_form")
    def show_edit_relationship_classes_form(self, checked=False):
        selected = {
            ind.internalPointer()
            for ind in self.object_tree_model.selected_relationship_class_indexes.keys()
            | self.relationship_tree_model.selected_relationship_class_indexes.keys()
        }
        dialog = EditRelationshipClassesDialog(self, selected)
        dialog.data_committed.connect(self.db_mngr.update_relationship_classes)
        dialog.show()

    @Slot("bool", name="show_edit_relationships_form")
    def show_edit_relationships_form(self, checked=False):
        # TODO: this...
        # NOTE: Only edits relationships that are in the same class
        selected = {
            ind.internalPointer()
            for ind in self.object_tree_model.selected_relationship_indexes.keys()
            | self.relationship_tree_model.selected_relationship_indexes.keys()
        }
        first_item = next(iter(selected))
        relationship_class_key = first_item.parent.display_id
        selected = {item for item in selected if item.parent.display_id == relationship_class_key}
        dialog = EditRelationshipsDialog(self, selected, relationship_class_key)
        dialog.data_committed.connect(self.db_mngr.update_relationships)
        dialog.show()

    def receive_items_changed(self, action, item_type, db_map_data, name_key=None):
        """Enables or disables actions and informs the user about what just happened."""
        if name_key is None:
            name_key = "name"
        # NOTE: The following line assumes this slot is called *after* removing items from object tree model
        self.ui.actionExport.setEnabled(self.object_tree_model.root_item.has_children())
        names = {item[name_key] for db_map, data in db_map_data.items() for item in data if name_key in item}
        self.commit_available.emit(True)
        names = ", ".join(names) if names else ""
        msg = f"Item(s) {names} of type {item_type} successfully {action}."
        self.msg.emit(msg)

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
        self.receive_items_changed("removed", "parameter definition", db_map_data, name_key="parameter_name")

    @Slot("QVariant", name="receive_parameter_values_removed")
    def receive_parameter_values_removed(self, db_map_data):
        self.receive_items_changed("removed", "parameter value", db_map_data)

    # TODO: all this with the manager
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
        db_map_data = dict()
        for db_map, items in parameter_value_list_d.items():
            updated, error_log = db_map.update_wide_parameter_value_lists(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not updated.count():
                continue
            db_map_data[db_map] = [x._asdict() for x in updated]
        updated_names = {x["name"] for updated in db_map_data.values() for x in updated}
        if not updated_names:
            return False
        self.object_parameter_definition_model.rename_parameter_value_lists(db_map_data)
        self.relationship_parameter_definition_model.rename_parameter_value_lists(db_map_data)
        self.commit_available.emit(True)
        msg = "Successfully updated parameter value list(s) '{}'.".format("', '".join(updated_names))
        self.msg.emit(msg)
        return True

    @Slot("bool", name="show_manage_parameter_tags_form")
    def show_manage_parameter_tags_form(self, checked=False):
        dialog = ManageParameterTagsDialog(self, self.db_maps)
        dialog.show()

    @busy_effect
    def add_parameter_tags(self, parameter_tag_d):
        """Add parameter tags."""
        db_map_parameter_tags = dict()
        for db_map, items in parameter_tag_d.items():
            added, error_log = db_map.add_parameter_tags(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not added.count():
                continue
            db_map_parameter_tags[db_map] = added
        added_tags = {x.tag for added in db_map_parameter_tags.values() for x in added}
        if not added_tags:
            return False
        self.parameter_tag_toolbar.add_tag_actions(db_map_parameter_tags)
        self.commit_available.emit(True)
        msg = "Successfully added new parameter tag(s) '{}'.".format("', '".join(added_tags))
        self.msg.emit(msg)
        return True

    @busy_effect
    def update_parameter_tags(self, parameter_tag_d):
        """Update parameter tags."""
        # TODO: update parameter value tables??
        db_map_parameter_tags = dict()
        for db_map, items in parameter_tag_d.items():
            updated, error_log = db_map.update_parameter_tags(*items)
            if error_log:
                self.msg_error.emit(format_string_list(error_log))
            if not updated.count():
                continue
            db_map_parameter_tags[db_map] = [x._asdict() for x in updated]
        updated_tags = {x["tag"] for updated in db_map_parameter_tags.values() for x in updated}
        if not updated_tags:
            return False
        self.object_parameter_definition_model.rename_parameter_tags(db_map_parameter_tags)
        self.relationship_parameter_definition_model.rename_parameter_tags(db_map_parameter_tags)
        self.parameter_tag_toolbar.update_tag_actions(db_map_parameter_tags)
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
            removed += len(ids)
        if not removed:
            return False
        self.parameter_tag_toolbar.remove_tag_actions(parameter_tag_d)
        self.object_parameter_definition_model.remove_parameter_tags(parameter_tag_d)
        self.relationship_parameter_definition_model.remove_parameter_tags(parameter_tag_d)
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

    @Slot("QModelIndex", "QVariant", name="set_parameter_data")
    def set_parameter_data(self, index, new_value):  # pylint: disable=no-self-use
        """Update (object or relationship) parameter value with newly edited data."""
        if new_value is None:
            return False
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
        event.accept()
