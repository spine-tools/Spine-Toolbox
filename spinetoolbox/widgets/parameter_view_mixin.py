######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the ParameterViewMixin class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QHeaderView
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
from .custom_menus import EditableParameterValueContextMenu, ParameterContextMenu
from .report_plotting_failure import report_plotting_failure
from ..mvcmodels.compound_parameter_models import (
    CompoundObjectParameterDefinitionModel,
    CompoundObjectParameterValueModel,
    CompoundRelationshipParameterDefinitionModel,
    CompoundRelationshipParameterValueModel,
)
from ..widgets.parameter_value_editor import ParameterValueEditor
from ..widgets.plot_widget import PlotWidget
from ..widgets.object_name_list_editor import ObjectNameListEditor
from ..plotting import plot_selection, PlottingError, ParameterTablePlottingHints
from ..helpers import busy_effect


class ParameterViewMixin:
    """
    Provides stacked parameter tables for the data store form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        self.ui.treeView_parameter_value_list.setModel(self.parameter_value_list_model)
        self.ui.tableView_object_parameter_value.setModel(self.object_parameter_value_model)
        self.ui.tableView_relationship_parameter_value.setModel(self.relationship_parameter_value_model)
        self.ui.tableView_object_parameter_definition.setModel(self.object_parameter_definition_model)
        self.ui.tableView_relationship_parameter_definition.setModel(self.relationship_parameter_definition_model)
        # Others
        views = [
            self.ui.tableView_object_parameter_definition,
            self.ui.tableView_object_parameter_value,
            self.ui.tableView_relationship_parameter_definition,
            self.ui.tableView_relationship_parameter_value,
        ]
        self._focusable_childs += views
        for view in views:
            view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            view.verticalHeader().setDefaultSectionSize(self.default_row_height)
            view.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
            view.horizontalHeader().setSectionsMovable(True)
        self.setup_delegates()

    def add_menu_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_object_parameter_value.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_object_parameter_definition.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_relationship_parameter_value.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_relationship_parameter_definition.toggleViewAction())

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
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
        self.object_parameter_definition_model.remove_selection_requested.connect(
            self.remove_object_parameter_definitions
        )
        self.object_parameter_value_model.remove_selection_requested.connect(self.remove_object_parameter_values)
        self.relationship_parameter_definition_model.remove_selection_requested.connect(
            self.remove_relationship_parameter_definitions
        )
        self.relationship_parameter_value_model.remove_selection_requested.connect(
            self.remove_relationship_parameter_values
        )
        # Parameter tables selection changes
        self.ui.tableView_object_parameter_definition.selectionModel().selectionChanged.connect(
            self._handle_object_parameter_definition_selection_changed
        )
        self.ui.tableView_object_parameter_value.selectionModel().selectionChanged.connect(
            self._handle_object_parameter_value_selection_changed
        )
        self.ui.tableView_relationship_parameter_definition.selectionModel().selectionChanged.connect(
            self._handle_relationship_parameter_definition_selection_changed
        )
        self.ui.tableView_relationship_parameter_value.selectionModel().selectionChanged.connect(
            self._handle_relationship_parameter_value_selection_changed
        )
        # Parameter tables context menu requested
        self.ui.tableView_object_parameter_definition.customContextMenuRequested.connect(
            self.show_object_parameter_definition_context_menu
        )
        self.ui.tableView_object_parameter_value.customContextMenuRequested.connect(
            self.show_object_parameter_value_context_menu
        )
        self.ui.tableView_relationship_parameter_definition.customContextMenuRequested.connect(
            self.show_relationship_parameter_definition_context_menu
        )
        self.ui.tableView_relationship_parameter_value.customContextMenuRequested.connect(
            self.show_relationship_parameter_value_context_menu
        )

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.object_parameter_value_model.init_model()
        self.object_parameter_definition_model.init_model()
        self.relationship_parameter_value_model.init_model()
        self.relationship_parameter_definition_model.init_model()
        self.set_default_parameter_data()
        self.ui.tableView_object_parameter_value.resizeColumnsToContents()
        self.ui.tableView_object_parameter_definition.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_value.resizeColumnsToContents()
        self.ui.tableView_relationship_parameter_definition.resizeColumnsToContents()

    def _setup_delegate(self, table_view, column, delegate_class):
        """Returns a custom delegate for a given view."""
        delegate = delegate_class(self, self.db_mngr)
        table_view.setItemDelegateForColumn(column, delegate)
        delegate.data_committed.connect(self.set_parameter_data)
        return delegate

    def setup_delegates(self):
        """Sets delegates for tables."""
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
            delegate.parameter_value_editor_requested.connect(self.show_parameter_value_editor)
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
        delegate.parameter_value_editor_requested.connect(self.show_parameter_value_editor)
        self._setup_delegate(table_view, h("parameter_name"), ObjectParameterNameDelegate)
        self._setup_delegate(table_view, h("object_name"), ObjectNameDelegate)
        # Relationship parameter value
        table_view = self.ui.tableView_relationship_parameter_value
        h = table_view.model().header.index
        delegate = self._setup_delegate(table_view, h("value"), RelationshipParameterValueDelegate)
        delegate.parameter_value_editor_requested.connect(self.show_parameter_value_editor)
        self._setup_delegate(table_view, h("parameter_name"), RelationshipParameterNameDelegate)
        delegate = self._setup_delegate(table_view, h("object_name_list"), ObjectNameListDelegate)
        delegate.object_name_list_editor_requested.connect(self.show_object_name_list_editor)

    @Slot("QModelIndex", "QVariant")
    def set_parameter_data(self, index, new_value):  # pylint: disable=no-self-use
        """Updates (object or relationship) parameter definition or value with newly edited data."""
        index.model().setData(index, new_value)

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

    @busy_effect
    @Slot("QModelIndex", str, object)
    def show_parameter_value_editor(self, index, value_name="", value=None):
        """Shows the parameter value editor for the given index of given table view.
        """
        editor = ParameterValueEditor(index, value_name=value_name, value=value, parent_widget=self)
        editor.show()

    # TODO: nothing connected to these two below

    @Slot(int)
    def _handle_object_parameter_tab_changed(self, index):
        """Updates filter."""
        if index == 0:
            self.object_parameter_value_model.update_main_filter()
        else:
            self.object_parameter_definition_model.update_main_filter()

    @Slot(int)
    def _handle_relationship_parameter_tab_changed(self, index):
        """Updates filter."""
        if index == 0:
            self.relationship_parameter_value_model.update_main_filter()
        else:
            self.relationship_parameter_definition_model.update_main_filter()

    @Slot(bool)
    def _handle_object_parameter_value_visibility_changed(self, visible):
        if visible:
            self.object_parameter_value_model.update_main_filter()

    @Slot(bool)
    def _handle_object_parameter_definition_visibility_changed(self, visible):
        if visible:
            self.object_parameter_definition_model.update_main_filter()

    @Slot(bool)
    def _handle_relationship_parameter_value_visibility_changed(self, visible):
        if visible:
            self.relationship_parameter_value_model.update_main_filter()

    @Slot(bool)
    def _handle_relationship_parameter_definition_visibility_changed(self, visible):
        if visible:
            self.relationship_parameter_definition_model.update_main_filter()

    @Slot("QItemSelection", "QItemSelection")
    def _handle_object_parameter_definition_selection_changed(self, selected, deselected):
        """Enables/disables the option to remove rows."""
        self._accept_selection(self.ui.tableView_object_parameter_definition)

    @Slot("QItemSelection", "QItemSelection")
    def _handle_object_parameter_value_selection_changed(self, selected, deselected):
        """Enables/disables the option to remove rows."""
        self._accept_selection(self.ui.tableView_object_parameter_value)

    @Slot("QItemSelection", "QItemSelection")
    def _handle_relationship_parameter_definition_selection_changed(self, selected, deselected):
        """Enables/disables the option to remove rows."""
        self._accept_selection(self.ui.tableView_relationship_parameter_definition)

    @Slot("QItemSelection", "QItemSelection")
    def _handle_relationship_parameter_value_selection_changed(self, selected, deselected):
        """Enables/disables the option to remove rows."""
        self._accept_selection(self.ui.tableView_relationship_parameter_value)

    def set_default_parameter_data(self, index=None):
        """Sets default rows for parameter models according to given index.

        Args:
            index (QModelIndex): and index of the object or relationship tree
        """
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
        """Updates filters."""
        if self.ui.dockWidget_object_parameter_value.isVisible():
            self.object_parameter_value_model.update_main_filter()
        if self.ui.dockWidget_object_parameter_definition.isVisible():
            self.object_parameter_definition_model.update_main_filter()
        if self.ui.dockWidget_relationship_parameter_value.isVisible():
            self.relationship_parameter_value_model.update_main_filter()
        if self.ui.dockWidget_relationship_parameter_definition.isVisible():
            self.relationship_parameter_definition_model.update_main_filter()

    @Slot("QPoint")
    def show_object_parameter_value_context_menu(self, pos):
        """Shows the context menu for object parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        self._show_parameter_context_menu(pos, self.ui.tableView_object_parameter_value, "value")

    @Slot("QPoint")
    def show_relationship_parameter_value_context_menu(self, pos):
        """Shows the context menu for relationship parameter value table view.

        Args:
            pos (QPoint): Mouse position
        """
        self._show_parameter_context_menu(pos, self.ui.tableView_relationship_parameter_value, "value")

    @Slot("QPoint")
    def show_object_parameter_definition_context_menu(self, pos):
        """Shows the context menu for object parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        self._show_parameter_context_menu(pos, self.ui.tableView_object_parameter_definition, "default_value")

    @Slot("QPoint")
    def show_relationship_parameter_definition_context_menu(self, pos):
        """Shows the context menu for relationship parameter table view.

        Args:
            pos (QPoint): Mouse position
        """
        self._show_parameter_context_menu(pos, self.ui.tableView_relationship_parameter_definition, "default_value")

    def _show_parameter_context_menu(self, position, table_view, value_column_header):
        """
        Shows the context menu for the given parameter table.

        Args:
            position (QPoint): local mouse position in the table view
            table_view (QTableView): the table view where the context menu was triggered
            value_column_header (str): column header for editable/plottable values
        """
        index = table_view.indexAt(position)
        global_pos = table_view.mapToGlobal(position)
        model = table_view.model()
        flags = model.flags(index)
        editable = (flags & Qt.ItemIsEditable) == Qt.ItemIsEditable
        is_value = model.headerData(index.column(), Qt.Horizontal) == value_column_header
        if editable and is_value:
            menu = EditableParameterValueContextMenu(self, global_pos, index)
        else:
            menu = ParameterContextMenu(self, global_pos, index)
        option = menu.get_action()
        if option == "Open in editor...":
            value_name = model.value_name(index)
            self.show_parameter_value_editor(index, value_name=value_name)
        elif option == "Plot":
            selection = table_view.selectedIndexes()
            try:
                hints = ParameterTablePlottingHints()
                plot_widget = plot_selection(model, selection, hints)
            except PlottingError as error:
                report_plotting_failure(error, self)
            else:
                plot_widget.use_as_window(table_view.window(), value_column_header)
                plot_widget.show()
        elif option == "Plot in window":
            plot_window_name = menu.plot_in_window_option
            plot_window = PlotWidget.plot_windows.get(plot_window_name)
            selection = table_view.selectedIndexes()
            try:
                hints = ParameterTablePlottingHints()
                plot_selection(model, selection, hints, plot_window)
            except PlottingError as error:
                report_plotting_failure(error, self)
        elif option == "Remove selection":
            model.remove_selection_requested.emit()
        elif option == "Copy":
            table_view.copy()
        elif option == "Paste":
            table_view.paste()
        menu.deleteLater()

    @Slot()
    def remove_object_parameter_values(self):
        """Removes selected rows from object parameter value table."""
        self._remove_parameter_data(self.ui.tableView_object_parameter_value, "parameter value")

    @Slot()
    def remove_relationship_parameter_values(self):
        """Removes selected rows from relationship parameter value table."""
        self._remove_parameter_data(self.ui.tableView_relationship_parameter_value, "parameter value")

    @Slot()
    def remove_object_parameter_definitions(self):
        """Removes selected rows from object parameter definition table."""
        self._remove_parameter_data(self.ui.tableView_object_parameter_definition, "parameter definition")

    @Slot()
    def remove_relationship_parameter_definitions(self):
        """Removes selected rows from relationship parameter definition table."""
        self._remove_parameter_data(self.ui.tableView_relationship_parameter_definition, "parameter definition")

    def _remove_parameter_data(self, table_view, item_type):
        """
        Removes selected rows from parameter table.

        Args:
            table_view (QTableView): remove selection from this view
            item_type (str)
        """
        selection = table_view.selectionModel().selection()
        rows = list()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            rows += range(top, bottom + 1)
        # Get parameter data grouped by db_map
        db_map_typed_data = dict()
        model = table_view.model()
        for row in sorted(rows, reverse=True):
            try:
                db_map = model.sub_model_at_row(row).db_map
            except AttributeError:
                # It's an empty model, just remove the row
                _, sub_row = model._row_map[row]
                model.empty_model.removeRow(sub_row)
            else:
                id_ = model.item_at_row(row)
                item = model.db_mngr.get_item(db_map, item_type, id_)
                db_map_typed_data.setdefault(db_map, {}).setdefault(item_type, []).append(item)
        self.db_mngr.remove_items(db_map_typed_data)
        table_view.selectionModel().clearSelection()

    def restore_ui(self):
        """Restores UI state from previous session."""
        super().restore_ui()
        self.qsettings.beginGroup(self.settings_group)
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

    def save_window_state(self):
        """Saves window state parameters (size, position, state) via QSettings."""
        super().save_window_state()
        self.qsettings.beginGroup(self.settings_group)
        h = self.ui.tableView_object_parameter_definition.horizontalHeader()
        self.qsettings.setValue("objParDefHeaderState", h.saveState())
        h = self.ui.tableView_object_parameter_value.horizontalHeader()
        self.qsettings.setValue("objParValHeaderState", h.saveState())
        h = self.ui.tableView_relationship_parameter_definition.horizontalHeader()
        self.qsettings.setValue("relParDefHeaderState", h.saveState())
        h = self.ui.tableView_relationship_parameter_value.horizontalHeader()
        self.qsettings.setValue("relParValHeaderState", h.saveState())
        self.qsettings.endGroup()

    def receive_parameter_definitions_added(self, db_map_data):
        super().receive_parameter_definitions_added(db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_added(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_added(db_map_data)

    def receive_parameter_values_added(self, db_map_data):
        super().receive_parameter_values_added(db_map_data)
        self.object_parameter_value_model.receive_parameter_data_added(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_added(db_map_data)

    def receive_parameter_definitions_updated(self, db_map_data):
        super().receive_parameter_definitions_updated(db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_updated(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_updated(db_map_data)

    def receive_parameter_values_updated(self, db_map_data):
        super().receive_parameter_values_updated(db_map_data)
        self.object_parameter_value_model.receive_parameter_data_updated(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_updated(db_map_data)

    def receive_parameter_definition_tags_set(self, db_map_data):
        super().receive_parameter_definition_tags_set(db_map_data)
        self.object_parameter_definition_model.receive_parameter_definition_tags_set(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_definition_tags_set(db_map_data)

    def receive_object_classes_removed(self, db_map_data):
        super().receive_object_classes_removed(db_map_data)
        self.object_parameter_definition_model.receive_entity_classes_removed(db_map_data)
        self.object_parameter_value_model.receive_entity_classes_removed(db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        super().receive_relationship_classes_removed(db_map_data)
        self.relationship_parameter_definition_model.receive_entity_classes_removed(db_map_data)
        self.relationship_parameter_value_model.receive_entity_classes_removed(db_map_data)

    def receive_parameter_definitions_removed(self, db_map_data):
        super().receive_parameter_definitions_removed(db_map_data)
        self.object_parameter_definition_model.receive_parameter_data_removed(db_map_data)
        self.relationship_parameter_definition_model.receive_parameter_data_removed(db_map_data)

    def receive_parameter_values_removed(self, db_map_data):
        super().receive_parameter_values_removed(db_map_data)
        self.object_parameter_value_model.receive_parameter_data_removed(db_map_data)
        self.relationship_parameter_value_model.receive_parameter_data_removed(db_map_data)
