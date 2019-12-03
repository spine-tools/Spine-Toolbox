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

from PySide2.QtWidgets import QMainWindow, QHeaderView, QErrorMessage
from PySide2.QtCore import Qt, Signal, Slot, QSettings
from PySide2.QtGui import QFont, QFontMetrics, QGuiApplication, QIcon
from ..config import MAINWINDOW_SS
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
from .object_name_list_editor import ObjectNameListEditor
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
from ..widgets.parameter_value_editor import ParameterValueEditor
from ..widgets.toolbars import ParameterTagToolBar
from ..mvcmodels.entity_tree_models import ObjectTreeModel
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
    """A widget to show and edit Spine dbs.
    """

    msg = Signal(str)
    msg_error = Signal(str)

    def __init__(self, db_mngr, ui, *db_urls):
        """Initializes form.

        Args:
            db_mngr (SpineDBManager): The manager to use
            ui: UI definition of the form that is initialized
            *db_urls (tuple): Database url, codename.
        """
        super().__init__(flags=Qt.Window)
        self.db_urls = list(db_urls)
        self.db_url = self.db_urls[0]
        self.db_mngr = db_mngr
        self.db_maps = [
            self.db_mngr.get_db_map_for_listener(self, url, codename=codename) for url, codename in self.db_urls
        ]
        self.db_map = self.db_maps[0]
        # Setup UI from Qt Designer file
        self.ui = ui
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStyleSheet(MAINWINDOW_SS)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Class attributes
        self.err_msg = QErrorMessage(self)
        self.err_msg.setWindowTitle("Error")
        # Selected ids
        self.selected_ent_cls_ids = {"object class": {}, "relationship class": {}}
        self.selected_ent_ids = {"object": {}, "relationship": {}}
        self.selected_param_def_ids = {"object class": {}, "relationship class": {}}
        self.selected_parameter_tag_ids = dict()
        # Parameter tag toolbar
        self.parameter_tag_toolbar = ParameterTagToolBar(self, self.db_mngr, *self.db_maps)
        self.addToolBar(Qt.TopToolBarArea, self.parameter_tag_toolbar)
        # Models
        self.object_tree_model = ObjectTreeModel(self, self.db_mngr, *self.db_maps)
        self.object_parameter_value_model = CompoundObjectParameterValueModel(self, self.db_mngr, *self.db_maps)
        self.relationship_parameter_value_model = CompoundRelationshipParameterValueModel(
            self, self.db_mngr, *self.db_maps
        )
        self.object_parameter_definition_model = CompoundObjectParameterDefinitionModel(
            self, self.db_mngr, *self.db_maps
        )
        self.relationship_parameter_definition_model = CompoundRelationshipParameterDefinitionModel(
            self, self.db_mngr, *self.db_maps
        )
        self.parameter_value_list_model = ParameterValueListModel(self, self.db_mngr, *self.db_maps)
        # Setup views
        self.ui.treeView_object.setModel(self.object_tree_model)
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
        self.msg_error.connect(self.err_msg.showMessage)
        # Menu actions
        self.ui.menuSession.aboutToShow.connect(self._handle_menu_session_about_to_show)
        self.ui.actionCommit.triggered.connect(self.commit_session)
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

    @Slot(str)
    def add_message(self, msg):
        """Append regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        self.ui.statusbar.add_notification(msg)

    @Slot("QItemSelection", "QItemSelection")
    def _handle_object_tree_selection_changed(self, selected, deselected):
        """Called when the object tree selection changes.
        Set default rows and apply filters on parameter models."""
        for index in deselected.indexes():
            self.object_tree_model.deselect_index(index)
        for index in selected.indexes():
            self.object_tree_model.select_index(index)

    @Slot("bool")
    def _handle_object_parameter_value_visibility_changed(self, visible):
        if visible:
            self.object_parameter_value_model.update_main_filter()

    @Slot("bool")
    def _handle_object_parameter_definition_visibility_changed(self, visible):
        if visible:
            self.object_parameter_definition_model.update_main_filter()

    @Slot("bool")
    def _handle_relationship_parameter_value_visibility_changed(self, visible):
        if visible:
            self.relationship_parameter_value_model.update_main_filter()

    @Slot("bool")
    def _handle_relationship_parameter_definition_visibility_changed(self, visible):
        if visible:
            self.relationship_parameter_definition_model.update_main_filter()

    @Slot("QVariant", "bool")
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
        selected_param_defs = self.db_mngr.find_cascading_parameter_definitions_by_tag(self.selected_parameter_tag_ids)
        if any(v for v in self.selected_parameter_tag_ids.values()) and not any(
            v for v in selected_param_defs.values()
        ):
            # There are tags selected but no matching parameter definitions ~> we need to reject them all
            self.selected_param_def_ids["object class"] = None
            self.selected_param_def_ids["relationship class"] = None
        else:
            self.selected_param_def_ids["object class"] = {}
            self.selected_param_def_ids["relationship class"] = {}
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

    @Slot()
    def _handle_menu_session_about_to_show(self):
        on = any(db_map.has_pending_changes() for db_map in self.db_maps)
        self.ui.actionCommit.setEnabled(on)
        self.ui.actionRollback.setEnabled(on)

    @Slot("bool")
    def commit_session(self, checked=False):
        """Commits session."""
        self.db_mngr.commit_session(*self.db_maps)

    @Slot("bool")
    def rollback_session(self, checked=False):
        self.db_mngr.rollback_session(*self.db_maps)

    def receive_session_committed(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        db_names = ", ".join([x.codename for x in db_maps])
        msg = f"All changes in {db_names} committed successfully."
        self.msg.emit(msg)

    def receive_session_rolled_back(self, db_maps):
        db_maps = set(self.db_maps) & set(db_maps)
        if not db_maps:
            return
        self.init_models()
        db_names = ", ".join([x.codename for x in db_maps])
        msg = f"All changes in {db_names} rolled back successfully."
        self.msg.emit(msg)

    @Slot("bool", name="refresh_session")
    def refresh_session(self, checked=False):
        self.init_models()
        msg = "Session refreshed."
        self.msg.emit(msg)

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
        delegate = self._setup_delegate(table_view, h("object_name_list"), ObjectNameListDelegate)
        delegate.object_name_list_editor_requested.connect(self.show_object_name_list_editor)

    @Slot("QModelIndex", int, "QVariant")
    def show_object_name_list_editor(self, index, rel_cls_id, db_map):
        """Shows the object names list editor.

        Args:
            index (QModelIndex)
            rel_cls_id (int)
            db_map (DiffDatabaseMapping)
        """
        relationship_class = self.db_mngr.get_item(db_map, "relationship class", rel_cls_id)
        object_class_id_list = relationship_class.get("object_class_id_list")
        object_class_names = []
        object_names_lists = []
        for id_ in object_class_id_list.split(","):
            id_ = int(id_)
            object_class_name = self.db_mngr.get_item(db_map, "object class", id_).get("name")
            object_names_list = [x["name"] for x in self.db_mngr.get_objects(db_map, class_id=id_)]
            object_class_names.append(object_class_name)
            object_names_lists.append(object_names_list)
        object_name_list = index.data(Qt.EditRole)
        try:
            current_object_names = object_name_list.split(",")
        except AttributeError:
            # Gibberish
            current_object_names = []
        editor = ObjectNameListEditor(self, index, object_class_names, object_names_lists, current_object_names)
        editor.show()

    @staticmethod
    def _db_map_items(indexes):
        """Groups items from given tree indexes by db map.

        Returns:
            dict: lists of dictionary items keyed by DiffDatabaseMapping
        """
        d = dict()
        for index in indexes:
            item = index.model().item_from_index(index)
            for db_map in item.db_maps:
                d.setdefault(db_map, []).append(item.db_map_data(db_map))
        return d

    @staticmethod
    def _db_map_class_id_data(db_map_data):
        """Returns a new dictionary where the class id is also part of the key.

        Returns:
            dict: lists of dictionary items keyed by tuple (DiffDatabaseMapping, integer class id)
        """
        d = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                d.setdefault((db_map, item["class_id"]), set()).add(item["id"])
        return d

    @staticmethod
    def _extend_merge(left, right):
        """Returns a new dictionary by uniting left and right.

        Returns:
            dict: lists of dictionary items keyed by DiffDatabaseMapping
        """
        result = left.copy()
        for key, data in right.items():
            result.setdefault(key, []).extend(data)
        return result

    def selected_entity_class_ids(self, entity_class_type):
        """Return object class ids selected in object tree *and* parameter tag toolbar."""
        if self.selected_param_def_ids[entity_class_type] is None:
            return None
        tree_class_ids = self.selected_ent_cls_ids[entity_class_type]
        tag_class_ids = dict()
        for db_map, class_id in self.selected_param_def_ids[entity_class_type]:
            tag_class_ids.setdefault(db_map, set()).add(class_id)
        result = dict()
        for db_map in tree_class_ids.keys() | tag_class_ids.keys():
            tree_cls_ids = tree_class_ids.get(db_map, set())
            tag_cls_ids = tag_class_ids.get(db_map, set())
            if tree_cls_ids == set():
                result[db_map] = tag_cls_ids
            elif tag_cls_ids == set():
                result[db_map] = tree_cls_ids
            else:
                result[db_map] = tree_cls_ids & tag_cls_ids
        return result

    def set_default_parameter_data(self, index=None):
        """Set default rows for parameter models according to selection in object or relationship tree."""
        if index is None or not index.isValid():
            default_data = dict(database=next(iter(self.db_maps)).codename)
        else:
            default_data = index.model().item_from_index(index).default_parameter_data()
        self.set_and_apply_default_rows(self.object_parameter_definition_model, default_data)
        self.set_and_apply_default_rows(self.object_parameter_value_model, default_data)
        self.set_and_apply_default_rows(self.relationship_parameter_definition_model, default_data)
        self.set_and_apply_default_rows(self.relationship_parameter_value_model, default_data)

    @staticmethod
    def set_and_apply_default_rows(model, default_data):
        model.empty_model.set_default_row(**default_data)
        model.empty_model.set_rows_to_default(model.empty_model.rowCount() - 1)

    def update_filter(self):
        """Update filter on parameter models."""
        if self.ui.dockWidget_object_parameter_value.isVisible():
            self.object_parameter_value_model.update_main_filter()
        if self.ui.dockWidget_object_parameter_definition.isVisible():
            self.object_parameter_definition_model.update_main_filter()
        if self.ui.dockWidget_relationship_parameter_value.isVisible():
            self.relationship_parameter_value_model.update_main_filter()
        if self.ui.dockWidget_relationship_parameter_definition.isVisible():
            self.relationship_parameter_definition_model.update_main_filter()

    @Slot("bool")
    def show_add_object_classes_form(self, checked=False):
        """Show dialog to let user select preferences for new object classes."""
        dialog = AddObjectClassesDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    @Slot("bool")
    def show_add_objects_form(self, checked=False, class_name=""):
        """Show dialog to let user select preferences for new objects."""
        dialog = AddObjectsDialog(self, self.db_mngr, *self.db_maps, class_name=class_name)
        dialog.show()

    @Slot("bool")
    def show_add_relationship_classes_form(self, checked=False, object_class_one_name=None):
        """Show dialog to let user select preferences for new relationship class."""
        dialog = AddRelationshipClassesDialog(
            self, self.db_mngr, *self.db_maps, object_class_one_name=object_class_one_name
        )
        dialog.show()

    @Slot("bool")
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

    @Slot("bool")
    def show_edit_object_classes_form(self, checked=False):
        selected = {ind.internalPointer() for ind in self.object_tree_model.selected_object_class_indexes}
        dialog = EditObjectClassesDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool")
    def show_edit_objects_form(self, checked=False):
        selected = {ind.internalPointer() for ind in self.object_tree_model.selected_object_indexes}
        dialog = EditObjectsDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool")
    def show_edit_relationship_classes_form(self, checked=False):
        selected = {
            ind.internalPointer()
            for ind in self.object_tree_model.selected_relationship_class_indexes.keys()
            | self.relationship_tree_model.selected_relationship_class_indexes.keys()
        }
        dialog = EditRelationshipClassesDialog(self, self.db_mngr, selected)
        dialog.show()

    @Slot("bool")
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

    @Slot("bool")
    def show_manage_parameter_tags_form(self, checked=False):
        dialog = ManageParameterTagsDialog(self, self.db_mngr, *self.db_maps)
        dialog.show()

    def notify_items_changed(self, action, item_type, db_map_data):
        """Enables or disables actions and informs the user about what just happened."""
        msg = f"Successfully {action}"
        name_keys = {
            "parameter tag": "tag",
            "parameter value": None,
            "parameter definition": "parameter_name",
            "relationship": "object_name_list",
        }
        name_key = name_keys.get(item_type, "name")
        if name_key:
            names = {item[name_key] for data in db_map_data.values() for item in data}
            msg += f" the following {item_type} item(s):" + format_string_list(names)
        else:
            count = sum(len(data) for data in db_map_data.values())
            msg += f" {count} {item_type} item(s)"
        msg += "<br />"
        self.msg.emit(msg)

    def receive_object_classes_added(self, db_map_data):
        self.notify_items_changed("added", "object class", db_map_data)
        self.object_tree_model.add_object_classes(db_map_data)

    def receive_objects_added(self, db_map_data):
        self.notify_items_changed("added", "object", db_map_data)
        self.object_tree_model.add_objects(db_map_data)

    def receive_relationship_classes_added(self, db_map_data):
        self.notify_items_changed("added", "relationship class", db_map_data)
        self.object_tree_model.add_relationship_classes(db_map_data)

    def receive_relationships_added(self, db_map_data):
        self.notify_items_changed("added", "relationship", db_map_data)
        self.object_tree_model.add_relationships(db_map_data)
        self.relationship_parameter_value_model.receive_relationships_added(db_map_data)

    def receive_parameter_definitions_added(self, db_map_data):
        self.notify_items_changed("added", "parameter definition", db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_added(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_added(db_map_data)

    def receive_parameter_values_added(self, db_map_data):
        self.notify_items_changed("added", "parameter value", db_map_data)
        self.object_parameter_value_model.receive_parameter_data_added(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_added(db_map_data)

    def receive_parameter_value_lists_added(self, db_map_data):
        self.notify_items_changed("added", "parameter value list", db_map_data)
        self.parameter_value_list_model.receive_parameter_value_lists_added(db_map_data)

    def receive_parameter_tags_added(self, db_map_data):
        self.notify_items_changed("added", "parameter tag", db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_added(db_map_data)

    def receive_object_classes_updated(self, db_map_data):
        self.notify_items_changed("updated", "object class", db_map_data)
        self.object_tree_model.update_object_classes(db_map_data)

    def receive_objects_updated(self, db_map_data):
        self.notify_items_changed("updated", "object", db_map_data)
        self.object_tree_model.update_objects(db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        self.notify_items_changed("updated", "relationship class", db_map_data)
        self.object_tree_model.update_relationship_classes(db_map_data)

    def receive_relationships_updated(self, db_map_data):
        self.notify_items_changed("updated", "relationship", db_map_data)
        self.object_tree_model.update_relationships(db_map_data)

    def receive_parameter_definitions_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter definition", db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_updated(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_updated(db_map_data)

    def receive_parameter_values_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter value", db_map_data)
        self.object_parameter_value_model.receive_parameter_data_updated(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_updated(db_map_data)

    def receive_parameter_value_lists_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter value list", db_map_data)
        self.parameter_value_list_model.receive_parameter_value_lists_updated(db_map_data)

    def receive_parameter_tags_updated(self, db_map_data):
        self.notify_items_changed("updated", "parameter tag", db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_updated(db_map_data)

    def receive_object_classes_removed(self, db_map_data):
        self.notify_items_changed("removed", "object class", db_map_data)
        self.object_tree_model.remove_object_classes(db_map_data)
        self.object_parameter_definition_model.receive_entity_classes_removed(db_map_data)
        self.object_parameter_value_model.receive_entity_classes_removed(db_map_data)

    def receive_objects_removed(self, db_map_data):
        self.notify_items_changed("removed", "object", db_map_data)
        self.object_tree_model.remove_objects(db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        self.notify_items_changed("removed", "relationship class", db_map_data)
        self.object_tree_model.remove_relationship_classes(db_map_data)
        self.relationship_parameter_definition_model.receive_entity_classes_removed(db_map_data)
        self.relationship_parameter_value_model.receive_entity_classes_removed(db_map_data)

    def receive_relationships_removed(self, db_map_data):
        self.notify_items_changed("removed", "relationship", db_map_data)
        self.object_tree_model.remove_relationships(db_map_data)

    def receive_parameter_definitions_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter definition", db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_removed(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_removed(db_map_data)

    def receive_parameter_values_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter value", db_map_data)
        self.object_parameter_value_model.receive_parameter_data_removed(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_removed(db_map_data)

    def receive_parameter_value_lists_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter value list", db_map_data)
        self.parameter_value_list_model.receive_parameter_value_lists_removed(db_map_data)

    def receive_parameter_tags_removed(self, db_map_data):
        self.notify_items_changed("removed", "parameter tag", db_map_data)
        self.parameter_tag_toolbar.receive_parameter_tags_removed(db_map_data)

    @busy_effect
    def show_parameter_value_editor(self, index, table_view, value=None):
        """Shows the parameter value editor for the given index of given table view.
        """
        value_name = tree_graph_view_parameter_value_name(index, table_view)
        editor = ParameterValueEditor(index, value_name=value_name, value=value, parent_widget=self)
        editor.show()

    @Slot("QModelIndex", "QVariant")
    def set_parameter_data(self, index, new_value):  # pylint: disable=no-self-use
        """Update (object or relationship) parameter definition or value with newly edited data."""
        index.model().setData(index, new_value)

    def restore_ui(self):
        """Restore UI state from previous session."""
        self.qsettings.beginGroup(self.settings_group)
        window_size = self.qsettings.value("windowSize")
        window_pos = self.qsettings.value("windowPosition")
        window_state = self.qsettings.value("windowState")
        window_maximized = self.qsettings.value("windowMaximized", defaultValue='false')
        n_screens = self.qsettings.value("n_screens", defaultValue=1)
        header_states = (
            self.qsettings.value("objParDefHeaderState"),
            self.qsettings.value("objParValHeaderState"),
            self.qsettings.value("relParDefHeaderState"),
            self.qsettings.value("relParValHeaderState"),
        )
        self.qsettings.endGroup()
        views = (
            self.ui.tableView_object_parameter_definition.horizontalHeader(),
            self.ui.tableView_object_parameter_value.horizontalHeader(),
            self.ui.tableView_relationship_parameter_definition.horizontalHeader(),
            self.ui.tableView_relationship_parameter_value.horizontalHeader(),
        )
        for view, state in zip(views, header_states):
            if state:
                curr_state = view.saveState()
                view.restoreState(state)
                if view.count() != view.model().columnCount():
                    # This can happen when switching to a version where the model has a different header
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
        self.qsettings.beginGroup(self.settings_group)
        self.qsettings.setValue("windowSize", self.size())
        self.qsettings.setValue("windowPosition", self.pos())
        self.qsettings.setValue("windowState", self.saveState(version=1))
        h = self.ui.tableView_object_parameter_definition.horizontalHeader()
        self.qsettings.setValue("objParDefHeaderState", h.saveState())
        h = self.ui.tableView_object_parameter_value.horizontalHeader()
        self.qsettings.setValue("objParValHeaderState", h.saveState())
        h = self.ui.tableView_relationship_parameter_definition.horizontalHeader()
        self.qsettings.setValue("relParDefHeaderState", h.saveState())
        h = self.ui.tableView_relationship_parameter_value.horizontalHeader()
        self.qsettings.setValue("relParValHeaderState", h.saveState())
        self.qsettings.setValue("windowMaximized", self.windowState() == Qt.WindowMaximized)
        self.qsettings.endGroup()

    def closeEvent(self, event):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event
        """
        for db_map in self.db_maps:
            if not self.db_mngr.remove_db_map_listener(db_map, self):
                event.ignore()
                return
        # Save UI form state
        self.save_window_state()
        event.accept()
