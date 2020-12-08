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
Custom QTableView classes that support copy-paste and the like.

:author: M. Marin (KTH)
:date:   18.5.2018
"""

from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import QAction, QTableView, QMenu
from ...widgets.report_plotting_failure import report_plotting_failure
from ...widgets.plot_widget import PlotWidget, _prepare_plot_in_window_menu
from ...plotting import plot_selection, PlottingError, ParameterTablePlottingHints, PivotTablePlottingHints
from .pivot_table_header_view import PivotTableHeaderView
from .tabular_view_header_widget import TabularViewHeaderWidget
from ...widgets.custom_qtableview import CopyPasteTableView, AutoFilterCopyPasteTableView
from .custom_delegates import (
    DatabaseNameDelegate,
    ParameterDefaultValueDelegate,
    TagListDelegate,
    ValueListDelegate,
    ParameterValueDelegate,
    ParameterNameDelegate,
    ObjectClassNameDelegate,
    ObjectNameDelegate,
    RelationshipClassNameDelegate,
    ObjectNameListDelegate,
    AlternativeNameDelegate,
)


class ParameterTableView(AutoFilterCopyPasteTableView):
    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self._menu = QMenu(self)
        self._spine_db_editor = None
        self.open_in_editor_action = None
        self.plot_action = None
        self.plot_separator = None

    @property
    def value_column_header(self):
        """Either "default value" or "value". Used to identifiy the value column for advanced editting and plotting.
        """
        raise NotImplementedError()

    def connect_spine_db_editor(self, spine_db_editor):
        """Connects a Spine db editor to work with this view.

        Args:
             spine_db_editor (SpineDBEditor)
        """
        self._spine_db_editor = spine_db_editor
        self.create_context_menu()
        self.create_delegates()

    def _make_delegate(self, column_name, delegate_class):
        """Creates a delegate for the given column and returns it.

        Args:
            column_name (str)
            delegate_class (ParameterDelegate)

        Returns:
            ParameterDelegate
        """
        column = self.model().header.index(column_name)
        delegate = delegate_class(self._spine_db_editor, self._spine_db_editor.db_mngr)
        self.setItemDelegateForColumn(column, delegate)
        delegate.data_committed.connect(self._spine_db_editor.set_parameter_data)
        return delegate

    def create_delegates(self):
        """Creates delegates for this view"""
        self._make_delegate("database", DatabaseNameDelegate)

    def open_in_editor(self):
        """Opens the current index in a parameter_value editor using the connected Spine db editor."""
        index = self.currentIndex()
        self._spine_db_editor.show_parameter_value_editor(index)

    @Slot(bool)
    def plot(self, checked=False):
        """Plots current index."""
        selection = self.selectedIndexes()
        try:
            hints = ParameterTablePlottingHints()
            plot_widget = plot_selection(self.model(), selection, hints)
        except PlottingError as error:
            report_plotting_failure(error, self._spine_db_editor)
        else:
            plot_widget.use_as_window(self.window(), self.value_column_header)
            plot_widget.show()

    @Slot(QAction)
    def plot_in_window(self, action):
        """Plots current index in the window given by action's name."""
        plot_window_name = action.text()
        plot_window = PlotWidget.plot_windows.get(plot_window_name)
        selection = self.selectedIndexes()
        try:
            hints = ParameterTablePlottingHints()
            plot_selection(self.model(), selection, hints, plot_window)
            plot_window.raise_()
        except PlottingError as error:
            report_plotting_failure(error, self._spine_db_editor)

    def create_context_menu(self):
        """Creates a context menu for this view."""
        self.open_in_editor_action = self._menu.addAction("Open in editor...", self.open_in_editor)
        self._menu.addSeparator()
        self.plot_action = self._menu.addAction("Plot", self.plot)
        self.plot_separator = self._menu.addSeparator()
        self._menu.addAction(self._spine_db_editor.ui.actionCopy)
        self._menu.addAction(self._spine_db_editor.ui.actionPaste)
        self._menu.addSeparator()
        self._menu.addAction("Filter by", self.filter_by_selection)
        self._menu.addAction("Filter excluding", self.filter_excluding_selection)
        self._menu.addSeparator()
        self._menu.addAction(self._spine_db_editor.ui.actionRemove_selected)

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        index = self.indexAt(event.pos())
        model = self.model()
        is_value = model.headerData(index.column(), Qt.Horizontal) == self.value_column_header
        self.open_in_editor_action.setVisible(is_value)
        self.plot_action.setVisible(is_value)
        if is_value:
            plot_in_window_menu = QMenu("Plot in window")
            plot_in_window_menu.triggered.connect(self.plot_in_window)
            _prepare_plot_in_window_menu(plot_in_window_menu)
            self._menu.insertMenu(self.plot_separator, plot_in_window_menu)
        self._menu.exec_(event.globalPos())
        if is_value:
            plot_in_window_menu.deleteLater()

    def _selected_rows_per_column(self):
        """Computes selected rows per column.

        Returns:
            dict: Mapping columns to selected rows in that column.
        """
        selection = self.selectionModel().selection()
        if not selection:
            return {}
        v_header = self.verticalHeader()
        h_header = self.horizontalHeader()
        rows_per_column = {}
        for rng in sorted(selection, key=lambda x: h_header.visualIndex(x.left())):
            for j in range(rng.left(), rng.right() + 1):
                if h_header.isSectionHidden(j):
                    continue
                rows = rows_per_column.setdefault(j, set())
                for i in range(rng.top(), rng.bottom() + 1):
                    if v_header.isSectionHidden(i):
                        continue
                    rows.add(i)
        return rows_per_column

    @Slot(bool)
    def filter_by_selection(self, checked=False):
        rows_per_column = self._selected_rows_per_column()
        self.model().filter_by(rows_per_column)

    @Slot(bool)
    def filter_excluding_selection(self, checked=False):
        rows_per_column = self._selected_rows_per_column()
        self.model().filter_excluding(rows_per_column)

    def remove_selected(self):
        """Removes selected indexes."""
        selection = self.selectionModel().selection()
        rows = list()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            rows += range(top, bottom + 1)
        # Get parameter data grouped by db_map
        db_map_typed_data = dict()
        model = self.model()
        for row in sorted(rows, reverse=True):
            db_map = model.sub_model_at_row(row).db_map
            if db_map is None:
                # It's an empty model, just remove the row
                _, sub_row = model._row_map[row]
                model.empty_model.removeRow(sub_row)
                continue
            id_ = model.item_at_row(row)
            db_map_typed_data.setdefault(db_map, {}).setdefault(model.item_type, []).append(id_)
        model.db_mngr.remove_items(db_map_typed_data)
        self.selectionModel().clearSelection()


class ObjectParameterTableMixin:
    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("object_class_name", ObjectClassNameDelegate)


class RelationshipParameterTableMixin:
    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("relationship_class_name", RelationshipClassNameDelegate)


class ParameterDefinitionTableView(ParameterTableView):
    @property
    def value_column_header(self):
        return "default_value"

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("parameter_tag_list", TagListDelegate)
        self._make_delegate("value_list_name", ValueListDelegate)
        delegate = self._make_delegate("default_value", ParameterDefaultValueDelegate)
        delegate.parameter_value_editor_requested.connect(self._spine_db_editor.show_parameter_value_editor)


class ParameterValueTableView(ParameterTableView):
    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self._show_value_metadata_action = None

    @property
    def value_column_header(self):
        return "value"

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("parameter_name", ParameterNameDelegate)
        self._make_delegate("alternative_name", AlternativeNameDelegate)
        delegate = self._make_delegate("value", ParameterValueDelegate)
        delegate.parameter_value_editor_requested.connect(self._spine_db_editor.show_parameter_value_editor)

    def create_context_menu(self):
        """Creates a context menu for this view."""
        super().create_context_menu()
        self._menu.addSeparator()
        self._show_value_metadata_action = self._menu.addAction(
            "Show parameter value metadata", self.show_value_metadata
        )

    def show_value_metadata(self):
        db_map_ids = {}
        for index in self.selectedIndexes():
            db_map, id_ = self.model().db_map_id(index)
            db_map_ids.setdefault(db_map, []).append(id_)
        self._spine_db_editor.show_db_map_parameter_value_metadata(db_map_ids)


class ObjectParameterDefinitionTableView(ObjectParameterTableMixin, ParameterDefinitionTableView):
    """A custom QTableView for the object parameter_definition pane in Spine db editor."""


class RelationshipParameterDefinitionTableView(RelationshipParameterTableMixin, ParameterDefinitionTableView):
    """A custom QTableView for the relationship parameter_definition pane in Spine db editor."""


class ObjectParameterValueTableView(ObjectParameterTableMixin, ParameterValueTableView):
    """A custom QTableView for the object parameter_value pane in Spine db editor."""

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("object_name", ObjectNameDelegate)


class RelationshipParameterValueTableView(RelationshipParameterTableMixin, ParameterValueTableView):
    """A custom QTableView for the relationship parameter_value pane in Spine db editor."""

    def create_delegates(self):
        super().create_delegates()
        delegate = self._make_delegate("object_name_list", ObjectNameListDelegate)
        delegate.object_name_list_editor_requested.connect(self._spine_db_editor.show_object_name_list_editor)


class PivotTableView(CopyPasteTableView):
    """Custom QTableView class with pivot capabilities.
    """

    _REMOVE_OBJECT = "Remove selected objects"
    _REMOVE_RELATIONSHIP = "Remove selected relationships"
    _REMOVE_PARAMETER = "Remove selected parameter definitions"
    _REMOVE_ALTERNATIVE = "Remove selected alternatives"
    _REMOVE_SCENARIO = "Remove selected scenarios"

    def __init__(self, parent=None):
        """Initialize the class."""
        super().__init__(parent)
        self._spine_db_editor = None
        self._menu = QMenu(self)
        self._selected_value_indexes = list()
        self._selected_entity_indexes = list()
        self._selected_parameter_indexes = list()
        self._selected_alternative_indexes = list()
        self._selected_scenario_indexes = list()
        self.open_in_editor_action = None
        self.plot_action = None
        self._plot_in_window_menu = None
        self.remove_values_action = None
        self.remove_objects_action = None
        self.remove_relationships_action = None
        self.remove_parameters_action = None
        self.remove_alternatives_action = None
        self.remove_scenarios_action = None

    @property
    def source_model(self):
        return self.model().sourceModel()

    @property
    def db_mngr(self):
        return self.source_model.db_mngr

    def connect_spine_db_editor(self, spine_db_editor):
        self._spine_db_editor = spine_db_editor
        self.create_context_menu()
        h_header = PivotTableHeaderView(Qt.Horizontal, "columns", self)
        h_header.setContextMenuPolicy(Qt.DefaultContextMenu)
        h_header.setResizeContentsPrecision(spine_db_editor.visible_rows)
        v_header = PivotTableHeaderView(Qt.Vertical, "rows", self)
        v_header.setContextMenuPolicy(Qt.NoContextMenu)
        v_header.setDefaultSectionSize(spine_db_editor.default_row_height)
        self.setHorizontalHeader(h_header)
        self.setVerticalHeader(v_header)

    def create_context_menu(self):
        self.open_in_editor_action = self._menu.addAction("Open in editor...", self.open_in_editor)
        self._menu.addSeparator()
        self.plot_action = self._menu.addAction("Plot", self.plot)
        self._plot_in_window_menu = self._menu.addMenu("Plot in window")
        self._plot_in_window_menu.triggered.connect(self._plot_in_window)
        self._menu.addSeparator()
        self.remove_values_action = self._menu.addAction("Remove selected parameter values", self.remove_values)
        self.remove_objects_action = self._menu.addAction(self._REMOVE_OBJECT, self.remove_objects)
        self.remove_relationships_action = self._menu.addAction(self._REMOVE_RELATIONSHIP, self.remove_relationships)
        self.remove_parameters_action = self._menu.addAction(self._REMOVE_PARAMETER, self.remove_parameters)
        self.remove_alternatives_action = self._menu.addAction(self._REMOVE_ALTERNATIVE, self.remove_alternatives)
        self.remove_scenarios_action = self._menu.addAction(self._REMOVE_SCENARIO, self.remove_scenarios)

    def remove_selected(self):
        self._find_selected_indexes()
        self.remove_values()
        if self._can_remove_relationships():
            self.remove_relationships()
        self.remove_objects()
        self.remove_parameters()
        self.remove_alternatives()
        self.remove_scenarios()

    def remove_values(self):
        row_mask = set()
        column_mask = set()
        for index in self._selected_value_indexes:
            row, column = self.source_model.map_to_pivot(index)
            row_mask.add(row)
            column_mask.add(column)
        data = self.source_model.model.get_pivoted_data(row_mask, column_mask)
        items = (item for row in data for item in row)
        db_map_typed_data = {}
        for item in items:
            if item is None:
                continue
            db_map, id_ = item
            db_map_typed_data.setdefault(db_map, {}).setdefault("parameter_value", set()).add(id_)
        self.db_mngr.remove_items(db_map_typed_data)

    def remove_objects(self):
        db_map_typed_data = {}
        for index in self._selected_entity_indexes:
            db_map, id_ = self.source_model._header_id(index)
            db_map_typed_data.setdefault(db_map, {}).setdefault("object", set()).add(id_)
        self.db_mngr.remove_items(db_map_typed_data)

    def remove_relationships(self):
        db_map_relationship_lookup = {
            db_map: {rel["object_id_list"]: rel["id"] for rel in rels}
            for db_map, rels in self._spine_db_editor._get_db_map_entities().items()
        }
        db_map_typed_data = {}
        for index in self._selected_entity_indexes:
            db_map, object_ids = self.source_model.db_map_object_ids(index)
            object_id_list = ",".join([str(id_) for id_ in object_ids])
            id_ = db_map_relationship_lookup.get(db_map, {}).get(object_id_list)
            if id_:
                db_map_typed_data.setdefault(db_map, {}).setdefault("relationship", set()).add(id_)
        self.db_mngr.remove_items(db_map_typed_data)

    def remove_parameters(self):
        db_map_typed_data = {}
        for index in self._selected_parameter_indexes:
            db_map, id_ = self.source_model._header_id(index)
            db_map_typed_data.setdefault(db_map, {}).setdefault("parameter_definition", set()).add(id_)
        self.db_mngr.remove_items(db_map_typed_data)

    def remove_alternatives(self):
        db_map_typed_data = {}
        for index in self._selected_alternative_indexes:
            db_map, id_ = self.source_model._header_id(index)
            db_map_typed_data.setdefault(db_map, {}).setdefault("alternative", set()).add(id_)
        self.db_mngr.remove_items(db_map_typed_data)

    def remove_scenarios(self):
        db_map_typed_data = {}
        for index in self._selected_scenario_indexes:
            db_map, id_ = self.source_model._header_id(index)
            db_map_typed_data.setdefault(db_map, {}).setdefault("scenario", set()).add(id_)
        self.db_mngr.remove_items(db_map_typed_data)

    def open_in_editor(self):
        """Opens the parameter_value editor for the first selected cell."""
        index = self._selected_value_indexes[0]
        self._spine_db_editor.show_parameter_value_editor(index)

    def plot(self):
        """Plots the selected cells in the pivot table."""
        selected_indexes = self.selectedIndexes()
        hints = PivotTablePlottingHints()
        try:
            plot_window = plot_selection(self.model(), selected_indexes, hints)
        except PlottingError as error:
            report_plotting_failure(error, self)
            return
        plotted_column_names = {
            hints.column_label(self.model(), index.column())
            for index in selected_indexes
            if hints.is_index_in_data(self.model(), index)
        }
        plot_window.use_as_window(self.parentWidget(), ", ".join(plotted_column_names))
        plot_window.show()

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        self._find_selected_indexes()
        self._update_actions_availability()
        pos = event.globalPos()
        self._menu.move(pos)
        _prepare_plot_in_window_menu(self._plot_in_window_menu)
        self._menu.show()

    def _find_selected_indexes(self):
        indexes = [self.model().mapToSource(ind) for ind in self.selectedIndexes()]
        self._selected_value_indexes = list()
        self._selected_entity_indexes = list()
        self._selected_parameter_indexes = list()
        self._selected_alternative_indexes = list()
        self._selected_scenario_indexes = list()
        for index in indexes:
            if self.source_model.index_in_data(index):
                self._selected_value_indexes.append(index)
            elif self.source_model.index_in_headers(index):
                top_left_id = self.source_model._top_left_id(index)
                header_type = self.source_model.top_left_headers[top_left_id].header_type
                if header_type == "parameter":
                    self._selected_parameter_indexes.append(index)
                elif header_type == "object":
                    self._selected_entity_indexes.append(index)
                elif header_type == "alternative":
                    self._selected_alternative_indexes.append(index)
                elif header_type == "scenario":
                    self._selected_scenario_indexes.append(index)

    def _update_actions_availability(self):
        self.open_in_editor_action.setEnabled(len(self._selected_value_indexes) == 1)
        self.plot_action.setEnabled(len(self._selected_value_indexes) > 0)
        self.remove_values_action.setEnabled(bool(self._selected_value_indexes))
        self.remove_objects_action.setEnabled(bool(self._selected_entity_indexes))
        self.remove_relationships_action.setEnabled(
            bool(self._selected_entity_indexes) and self._can_remove_relationships()
        )
        self.remove_parameters_action.setEnabled(bool(self._selected_parameter_indexes))
        self.remove_alternatives_action.setEnabled(bool(self._selected_alternative_indexes))
        self.remove_scenarios_action.setEnabled(bool(self._selected_scenario_indexes))

    def _can_remove_relationships(self):
        return (
            self.model().sourceModel().item_type == "parameter_value"
            and self._spine_db_editor.current_class_type == "relationship_class"
        )

    @Slot(QAction)
    def _plot_in_window(self, action):
        window_id = action.text()
        plot_window = PlotWidget.plot_windows.get(window_id)
        if plot_window is None:
            self.plot()
            return
        selected_indexes = self.selectedIndexes()
        hints = PivotTablePlottingHints()
        try:
            plot_selection(self.model(), selected_indexes, hints, plot_window)
            plot_window.raise_()
        except PlottingError as error:
            report_plotting_failure(error, self)


class FrozenTableView(QTableView):

    header_dropped = Signal(object, object)

    @property
    def area(self):
        return "frozen"

    def dragEnterEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dragMoveEvent(self, event):
        if isinstance(event.source(), TabularViewHeaderWidget):
            event.accept()

    def dropEvent(self, event):
        self.header_dropped.emit(event.source(), self)
