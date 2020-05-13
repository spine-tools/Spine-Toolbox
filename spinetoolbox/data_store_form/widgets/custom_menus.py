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
Classes for custom context menus and pop-up menus.

:author: M. Marin (KTH)
:date:   13.5.2020
"""

from PySide2.QtWidgets import QMenu, QWidgetAction
from PySide2.QtGui import QIcon
from PySide2.QtCore import QEvent, QPoint, Signal, Slot
from ...helpers import fix_name_ambiguity
from ...plotting import plot_pivot_column, plot_selection, PlottingError, PivotTablePlottingHints
from .custom_qwidgets import LazyFilterWidget, DataToValueFilterWidget
from ...widgets.plot_widget import PlotWidget
from ...widgets.report_plotting_failure import report_plotting_failure
from ...widgets.custom_menus import CustomContextMenu, FilterMenuBase


class EntityTreeContextMenu(CustomContextMenu):
    """Context menu class for object tree items in tree view form."""

    def __init__(self, parent, position, index):
        """
        Args:
            parent (QWidget): Parent for menu widget
            position (QPoint): Position on screen
            index (QModelIndex): Index of item that requested the context-menu
        """
        super().__init__(parent, position)
        if not index.isValid():
            return
        item = index.model().item_from_index(index)
        self.add_action("Copy text", QIcon(":/icons/menu_icons/copy.svg"))
        self.addSeparator()
        for action_block in item.context_menu_actions:
            for text, icon in action_block.items():
                self.add_action(text, icon)
            self.addSeparator()
        if item.has_children():
            self.addSeparator()
            self.add_action("Fully expand", QIcon(":/icons/menu_icons/angle-double-right.svg"))
            self.add_action("Fully collapse", QIcon(":/icons/menu_icons/angle-double-left.svg"))
        self.addSeparator()
        self.add_action("Export selection", QIcon(":/icons/project_item_icons/database-export.svg"))


class ParameterContextMenu(CustomContextMenu):
    """Context menu class for object (relationship) parameter items in tree views."""

    def __init__(self, parent, position, index):
        """
        Args:
            parent (QWidget): Parent for menu widget
            position (QPoint): Position on screen
            index (QModelIndex): Index of item that requested the context-menu
        """
        super().__init__(parent, position)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        paste_icon = self._parent.ui.actionPaste.icon()
        remove_icon = QIcon(":/icons/menu_icons/cog_minus.svg")
        self.add_action("Copy", copy_icon)
        self.add_action("Paste", paste_icon)
        self.addSeparator()
        self.add_action("Remove selection", remove_icon)


class EditableParameterValueContextMenu(CustomContextMenu):
    """Context menu class for object (relationship) parameter value items in tree views."""

    def __init__(self, parent, position, index):
        """
        Args:
            parent (QWidget): Parent for menu widget
            position (QPoint): Position on screen
            index (QModelIndex): Index of item that requested the context-menu
        """
        super().__init__(parent, position)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        paste_icon = self._parent.ui.actionPaste.icon()
        remove_icon = QIcon(":/icons/menu_icons/cog_minus.svg")
        self.add_action("Open in editor...")
        self.addSeparator()
        self.add_action("Plot")
        plot_in_window_menu = QMenu("Plot in window")
        _prepare_plot_in_window_menu(plot_in_window_menu)
        plot_in_window_menu.triggered.connect(self._plot_in_window)
        self.plot_in_window_option = None
        self.addMenu(plot_in_window_menu)
        self.addSeparator()
        self.add_action("Copy", copy_icon)
        self.add_action("Paste", paste_icon)
        self.addSeparator()
        self.add_action("Remove selection", remove_icon)

    @Slot("QAction")
    def _plot_in_window(self, action):
        """Sets the option attributes ready for plotting in an existing window."""
        self.option = "Plot in window"
        self.plot_in_window_option = action.text()


class ParameterValueListContextMenu(CustomContextMenu):
    """Context menu class for parameter enum view in tree view form."""

    def __init__(self, parent, position, index):
        """
        Args:
            parent (QWidget): Parent for menu widget
            position (QPoint): Position on screen
            index (QModelIndex): Index of item that requested the context-menu
        """
        super().__init__(parent, position)
        if not index.isValid():
            return
        copy_icon = self._parent.ui.actionCopy.icon()
        remove_icon = QIcon(":/icons/minus.png")
        self.add_action("Copy", copy_icon)
        self.addSeparator()
        self.add_action("Remove selection", remove_icon)


class GraphViewContextMenu(QMenu):
    """Context menu class for qgraphics view in graph view."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
        """
        super().__init__(parent)
        parent._handle_menu_graph_about_to_show()
        self.addAction(parent.ui.actionSave_positions)
        self.addAction(parent.ui.actionClear_positions)
        self.addSeparator()
        self.addAction(parent.ui.actionHide_selected)
        self.addAction(parent.ui.actionShow_hidden)
        self.addSeparator()
        self.addAction(parent.ui.actionPrune_selected_entities)
        self.addAction(parent.ui.actionPrune_selected_classes)
        self.addMenu(parent.ui.menuRestore_pruned)
        self.addAction(parent.ui.actionRestore_all_pruned)


class EntityItemContextMenu(CustomContextMenu):
    """Context menu class for entity graphic items in graph view."""

    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.selection_count = len(parent.entity_item_selection)
        parent._handle_menu_graph_about_to_show()
        self.addAction(parent.ui.actionHide_selected)
        self.addAction(parent.ui.actionPrune_selected_entities)
        self.addAction(parent.ui.actionPrune_selected_classes)


class ObjectItemContextMenu(EntityItemContextMenu):
    def __init__(self, parent, position, graphics_item):
        """
        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
            graphics_item (spinetoolbox.widgets.graph_view_graphics_items.ObjectItem): item that requested the menu
        """
        super().__init__(parent, position)
        self.relationship_class_dict = dict()
        self.addSeparator()
        if graphics_item.is_wip:
            self.add_action("Set name", enabled=self.selection_count == 1)
        else:
            self.add_action("Rename", enabled=self.selection_count == 1)
        self.add_action("Remove")
        if graphics_item.is_wip or self.selection_count > 1:
            return
        self.addSeparator()
        for relationship_class in parent.db_mngr.get_items(parent.db_map, "relationship class"):
            object_class_names = relationship_class["object_class_name_list"].split(",")
            fixed_object_class_names = fix_name_ambiguity(object_class_names)
            for i, object_class_name in enumerate(object_class_names):
                if object_class_name != graphics_item.entity_class_name:
                    continue
                option = "Add '{}' relationship".format(relationship_class['name'])
                if object_class_name != fixed_object_class_names[i]:
                    option += f" as dimension {i}"
                self.add_action(option)
                self.relationship_class_dict[option] = {'id': relationship_class["id"], 'dimension': i}


class RelationshipItemContextMenu(EntityItemContextMenu):
    def __init__(self, parent, position):
        """
        Args:
            parent (QWidget): Parent for menu widget (GraphViewForm)
            position (QPoint): Position on screen
        """
        super().__init__(parent, position)
        self.addSeparator()
        self.add_action("Remove")


class ParameterViewFilterMenu(FilterMenuBase):

    filterChanged = Signal(set, bool)

    def __init__(self, parent, source_model, show_empty=True):
        """
        Args:
            parent (DataStoreForm)
            source_model (CompoundParameterModel): a model to lazily get data from
        """
        super().__init__(parent)
        self._filter = LazyFilterWidget(self, source_model, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.connect_signals()
        self.aboutToShow.connect(self._filter.set_model)

    def emit_filter_changed(self, valid_values):
        self.filterChanged.emit(valid_values, self._filter.has_filter())


class TabularViewFilterMenu(FilterMenuBase):
    """Filter menu to use together with FilterWidget in TabularViewMixin."""

    filterChanged = Signal(int, set, bool)

    def __init__(self, parent, identifier, data_to_value, show_empty=True):
        """
        Args:
            parent (DataStoreForm)
            identifier (int): index identifier
            data_to_value (method): a method to translate item data to a value for display role
        """
        super().__init__(parent)
        self.identifier = identifier
        self._filter = DataToValueFilterWidget(self, data_to_value, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.anchor = parent
        self.connect_signals()

    def emit_filter_changed(self, valid_values):
        self.filterChanged.emit(self.identifier, valid_values, self._filter.has_filter())

    def event(self, event):
        if event.type() == QEvent.Show and self.anchor is not None:
            if self.anchor.area == "rows":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(0, self.anchor.height())
            elif self.anchor.area == "columns":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(self.anchor.width(), 0)
            self.move(pos)
        return super().event(event)


class PivotTableModelMenu(QMenu):

    _DELETE_OBJECT = "Remove selected objects"
    _DELETE_RELATIONSHIP = "Remove selected relationships"
    _DELETE_PARAMETER = "Remove selected parameter definitions"

    def __init__(self, parent):
        """
        Args:
            parent (TabularViewMixin): a parent widget
        """
        super().__init__(parent)
        self.db_mngr = parent.db_mngr
        self.db_map = parent.db_map
        self._table = parent.ui.pivot_table
        self._proxy = self._table.model()
        self._source = self._proxy.sourceModel()
        self._selected_value_indexes = list()
        self._selected_entity_indexes = list()
        self._selected_parameter_indexes = list()
        # add actions
        self.open_value_editor_action = self.addAction("Open in editor...")
        self.addSeparator()
        self.plot_action = self.addAction("Plot")
        self._plot_in_window_menu = QMenu("Plot in window")
        self._plot_in_window_menu.triggered.connect(self._plot_in_window)
        self.addMenu(self._plot_in_window_menu)
        self.addSeparator()
        self.delete_values_action = self.addAction("Delete selected values")
        self.delete_object_action = self.addAction(self._DELETE_OBJECT)
        self.delete_relationship_action = self.addAction(self._DELETE_RELATIONSHIP)
        self.delete_parameter_action = self.addAction(self._DELETE_PARAMETER)
        # connect signals
        self.open_value_editor_action.triggered.connect(self.open_value_editor)
        self.plot_action.triggered.connect(self.plot)
        self.delete_values_action.triggered.connect(self.delete_values)
        self.delete_object_action.triggered.connect(self.delete_objects)
        self.delete_relationship_action.triggered.connect(self.delete_relationships)
        self.delete_parameter_action.triggered.connect(self.delete_parameters)

    def delete_values(self):
        row_mask = set()
        column_mask = set()
        for index in self._selected_value_indexes:
            row, column = self._source.map_to_pivot(index)
            row_mask.add(row)
            column_mask.add(column)
        data = self._source.model.get_pivoted_data(row_mask, column_mask)
        ids = {item for row in data for item in row if item is not None}
        parameter_values = [self.db_mngr.get_item(self.db_map, "parameter value", id_) for id_ in ids]
        db_map_typed_data = {self.parent().db_map: {"parameter value": parameter_values}}
        self.db_mngr.remove_items(db_map_typed_data)

    def delete_objects(self):
        ids = {self._source._header_id(index) for index in self._selected_entity_indexes}
        objects = [self.db_mngr.get_item(self.db_map, "object", id_) for id_ in ids]
        db_map_typed_data = {self.parent().db_map: {"object": objects}}
        self.db_mngr.remove_items(db_map_typed_data)

    def delete_relationships(self):
        relationships = []
        for index in self._selected_entity_indexes:
            header_ids = self._source._header_ids(index)
            objects_ids = header_ids[:-1]
            relationships.append(self._source._get_relationship(objects_ids))
        db_map_typed_data = {self.parent().db_map: {"relationship": relationships}}
        self.db_mngr.remove_items(db_map_typed_data)

    def delete_parameters(self):
        ids = {self._source._header_id(index) for index in self._selected_parameter_indexes}
        parameters = [self.db_mngr.get_item(self.db_map, "parameter definition", id_) for id_ in ids]
        db_map_typed_data = {self.parent().db_map: {"parameter definition": parameters}}
        self.db_mngr.remove_items(db_map_typed_data)

    def open_value_editor(self):
        """Opens the parameter value editor for the first selected cell."""
        index = self._selected_value_indexes[0]
        self.parent().show_parameter_value_editor(index)

    def plot(self):
        """Plots the selected cells in the pivot table."""
        selected_indexes = self._table.selectedIndexes()
        hints = PivotTablePlottingHints()
        try:
            plot_window = plot_selection(self._proxy, selected_indexes, hints)
        except PlottingError as error:
            report_plotting_failure(error, self)
            return
        plotted_column_names = {
            hints.column_label(self._proxy, index.column())
            for index in selected_indexes
            if hints.is_index_in_data(self._proxy, index)
        }
        plot_window.use_as_window(self.parentWidget(), ", ".join(plotted_column_names))
        plot_window.show()

    def request_menu(self, QPos=None):
        """Shows the context menu on the screen."""
        self._find_selected_indexes()
        self._update_actions_enable()
        self._update_actions_text()
        pos = self._table.viewport().mapToGlobal(QPos)
        self.move(pos)
        _prepare_plot_in_window_menu(self._plot_in_window_menu)
        self.show()

    def _find_selected_indexes(self):
        indexes = [self._proxy.mapToSource(ind) for ind in self._table.selectedIndexes()]
        self._selected_value_indexes = list()
        self._selected_entity_indexes = list()
        self._selected_parameter_indexes = list()
        for index in indexes:
            if self._source.index_in_data(index):
                self._selected_value_indexes.append(index)
            elif self._source.index_in_headers(index):
                if self._source._top_left_id(index) == -1:
                    self._selected_parameter_indexes.append(index)
                else:
                    self._selected_entity_indexes.append(index)

    def _update_actions_enable(self):
        self.open_value_editor_action.setEnabled(len(self._selected_value_indexes) == 1)
        self.plot_action.setEnabled(len(self._selected_value_indexes) > 0)
        self.delete_values_action.setEnabled(bool(self._selected_value_indexes))
        self.delete_object_action.setEnabled(bool(self._selected_entity_indexes))
        self.delete_relationship_action.setEnabled(
            bool(self._selected_entity_indexes) and self.parent().current_class_type == "relationship class"
        )
        self.delete_parameter_action.setEnabled(bool(self._selected_parameter_indexes))

    def _update_actions_text(self):
        self.delete_object_action.setText(self._DELETE_OBJECT)
        self.delete_relationship_action.setText(self._DELETE_RELATIONSHIP)
        self.delete_parameter_action.setText(self._DELETE_PARAMETER)
        if len(self._selected_entity_indexes) == 1:
            index = self._selected_entity_indexes[0]
            object_name = self._source.header_name(index)
            self.delete_object_action.setText("Remove object: {}".format(object_name))
            if self.delete_relationship_action.isEnabled():
                object_names, _ = self._source.header_names(index)
                relationship_name = self.db_mngr._GROUP_SEP.join(object_names)
                self.delete_relationship_action.setText("Remove relationship: {}".format(relationship_name))
        if len(self._selected_parameter_indexes) == 1:
            index = self._selected_parameter_indexes[0]
            parameter_name = self._source.header_name(index)
            self.delete_parameter_action.setText("Remove parameter definition: {}".format(parameter_name))

    @Slot("QAction")
    def _plot_in_window(self, action):
        window_id = action.text()
        plot_window = PlotWidget.plot_windows.get(window_id)
        if plot_window is None:
            self.plot()
            return
        selected_indexes = self._table.selectedIndexes()
        hints = PivotTablePlottingHints()
        try:
            plot_selection(self._proxy, selected_indexes, hints, plot_window)
        except PlottingError as error:
            report_plotting_failure(error, self)
            return


class PivotTableHorizontalHeaderMenu(QMenu):
    """
    A context menu for the horizontal header of a pivot table.
    """

    def __init__(self, proxy_model, parent=None):
        """
        Args:
             proxy_model (PivotTableSortFilterProxy): a proxy model
             parent (QWidget): a parent widget
        """
        super().__init__(parent)
        self._proxy_model = proxy_model
        self._model_index = None
        self._plot_action = self.addAction("Plot single column")
        self._plot_action.triggered.connect(self._plot_column)
        self._add_to_plot_menu = self.addMenu("Plot in window")
        self._add_to_plot_menu.triggered.connect(self._add_column_to_plot)
        self._set_as_X_action = self.addAction("Use as X")
        self._set_as_X_action.setCheckable(True)
        self._set_as_X_action.triggered.connect(self._set_x_flag)

    @Slot("QPoint")
    def request_menu(self, pos):
        """Shows the context menu on the screen."""
        self.move(self.parent().mapToGlobal(pos))
        self._model_index = self.parent().indexAt(pos)
        source_index = self._proxy_model.mapToSource(self._model_index)
        if self._proxy_model.sourceModel().column_is_index_column(self._model_index.column()):
            self._plot_action.setEnabled(False)
            self._set_as_X_action.setEnabled(True)
            self._set_as_X_action.setChecked(source_index.column() == self._proxy_model.sourceModel().plot_x_column)
        elif self._model_index.column() < self._proxy_model.sourceModel().headerColumnCount():
            self._plot_action.setEnabled(False)
            self._set_as_X_action.setEnabled(False)
            self._set_as_X_action.setChecked(False)
        else:
            self._plot_action.setEnabled(True)
            self._set_as_X_action.setEnabled(True)
            self._set_as_X_action.setChecked(source_index.column() == self._proxy_model.sourceModel().plot_x_column)
        _prepare_plot_in_window_menu(self._add_to_plot_menu)
        self.show()

    @Slot("QAction")
    def _add_column_to_plot(self, action):
        """Adds a single column to existing plot window."""
        window_id = action.text()
        plot_window = PlotWidget.plot_windows.get(window_id)
        if plot_window is None:
            self._plot_column()
            return
        try:
            support = PivotTablePlottingHints()
            plot_pivot_column(self._proxy_model, self._model_index.column(), support, plot_window)
        except PlottingError as error:
            report_plotting_failure(error, self)

    @Slot()
    def _plot_column(self):
        """Plots a single column not the selection."""
        try:
            support = PivotTablePlottingHints()
            plot_window = plot_pivot_column(self._proxy_model, self._model_index.column(), support)
        except PlottingError as error:
            report_plotting_failure(error, self)
            return
        plot_window.use_as_window(
            self.parentWidget(), support.column_label(self._proxy_model, self._model_index.column())
        )
        plot_window.show()

    @Slot()
    def _set_x_flag(self):
        """Sets the X flag for a column."""
        index = self._proxy_model.mapToSource(self._model_index)
        self._proxy_model.sourceModel().set_plot_x_column(index.column(), self._set_as_X_action.isChecked())


def _prepare_plot_in_window_menu(menu):
    """Fills a given menu with available plot window names."""
    menu.clear()
    plot_windows = PlotWidget.plot_windows
    if not plot_windows:
        menu.setEnabled(False)
        return
    menu.setEnabled(True)
    window_names = list(plot_windows.keys())
    for name in sorted(window_names):
        menu.addAction(name)
