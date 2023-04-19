######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""

from dataclasses import replace
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QModelIndex, QPoint, QItemSelection, QItemSelectionModel
from PySide6.QtWidgets import QTableView, QMenu, QWidget
from PySide6.QtGui import QKeySequence, QAction
from .scenario_generator import ScenarioGenerator
from ..mvcmodels.pivot_table_models import (
    ParameterValuePivotTableModel,
    RelationshipPivotTableModel,
    IndexExpansionPivotTableModel,
    ScenarioAlternativePivotTableModel,
)
from ..mvcmodels.metadata_table_model_base import Column as MetadataColumn
from ...widgets.report_plotting_failure import report_plotting_failure
from ...widgets.plot_widget import PlotWidget, prepare_plot_in_window_menu
from ...widgets.custom_qtableview import CopyPasteTableView, AutoFilterCopyPasteTableView
from ...widgets.custom_qwidgets import TitleWidgetAction, ResizingViewMixin
from ...plotting import (
    PlottingError,
    ParameterTableHeaderSection,
    plot_parameter_table_selection,
    plot_pivot_table_selection,
)
from ...helpers import preferred_row_height, rows_to_row_count_tuples, DB_ITEM_SEPARATOR
from .pivot_table_header_view import (
    PivotTableHeaderView,
    ParameterValuePivotHeaderView,
    ScenarioAlternativePivotHeaderView,
)
from .tabular_view_header_widget import TabularViewHeaderWidget
from .custom_delegates import (
    DatabaseNameDelegate,
    ParameterDefaultValueDelegate,
    ValueListDelegate,
    ParameterValueDelegate,
    ParameterNameDelegate,
    ObjectClassNameDelegate,
    ObjectNameDelegate,
    RelationshipClassNameDelegate,
    ObjectNameListDelegate,
    AlternativeNameDelegate,
    ItemMetadataDelegate,
)


@Slot(QModelIndex, object)
def _set_parameter_data(index, new_value):
    """Updates (object or relationship) parameter_definition or value with newly edited data."""
    index.model().setData(index, new_value)


class ParameterTableView(ResizingViewMixin, AutoFilterCopyPasteTableView):
    value_column_header: str = NotImplemented
    """Either "default value" or "value". Used to identify the value column for advanced editing and plotting."""

    def __init__(self, parent):
        """
        Args:
            parent (QObject): parent object
        """
        super().__init__(parent=parent)
        self._menu = QMenu(self)
        self._spine_db_editor = None
        self._open_in_editor_action = None
        self._plot_action = None
        self._plot_separator = None
        self.pinned_values = []

    def connect_spine_db_editor(self, spine_db_editor):
        """Connects a Spine db editor to work with this view.

        Args:
             spine_db_editor (SpineDBEditor)
        """
        self._spine_db_editor = spine_db_editor
        self.set_external_copy_and_paste_actions(spine_db_editor.ui.actionCopy, spine_db_editor.ui.actionPaste)
        self.populate_context_menu()
        self.create_delegates()
        self.selectionModel().selectionChanged.connect(self._refresh_copy_paste_actions)

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
        delegate.data_committed.connect(_set_parameter_data)
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
            plot_widget = self._plot_selection(selection)
        except PlottingError as error:
            report_plotting_failure(error, self._spine_db_editor)
        else:
            plot_widget.use_as_window(self.window(), self.value_column_header)
            plot_widget.show()

    def _plot_selection(self, selection, plot_widget=None):
        """Adds selected indexes to existing plot or creates a new plot window.

        Args:
            selection (Iterable of QModelIndex): a list of QModelIndex objects for plotting
            plot_widget (PlotWidget, optional): an existing plot widget to draw into or None to create a new widget

        Returns:
            PlotWidget: a PlotWidget object
        """
        raise NotImplementedError()

    @Slot(QAction)
    def plot_in_window(self, action):
        """Plots current index in the window given by action's name."""
        plot_window_name = action.text()
        plot_window = PlotWidget.plot_windows.get(plot_window_name)
        selection = self.selectedIndexes()
        try:
            self._plot_selection(selection, plot_window)
            plot_window.raise_()
        except PlottingError as error:
            report_plotting_failure(error, self._spine_db_editor)

    def populate_context_menu(self):
        """Creates a context menu for this view."""
        self._open_in_editor_action = self._menu.addAction("Edit...", self.open_in_editor)
        self._menu.addSeparator()
        self._plot_action = self._menu.addAction("Plot...", self.plot)
        self._plot_separator = self._menu.addSeparator()
        self._menu.addAction(self._spine_db_editor.ui.actionCopy)
        self._menu.addAction(self._spine_db_editor.ui.actionPaste)
        self._menu.addSeparator()
        remove_rows_action = self._menu.addAction("Remove row(s)", self.remove_selected)
        self._menu.addSeparator()
        self._menu.addAction("Filter by", self.filter_by_selection)
        self._menu.addAction("Filter excluding", self.filter_excluding_selection)
        self._menu.addSeparator()
        self._menu.addAction("Clear all filters", self._spine_db_editor.clear_all_filters)
        self._menu.addSeparator()
        # Shortcuts
        remove_rows_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_Delete))
        remove_rows_action.setShortcutContext(Qt.WidgetShortcut)
        self.addAction(remove_rows_action)

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        index = self.indexAt(event.pos())
        if not index.isValid():
            return
        model = self.model()
        is_value = model.headerData(index.column(), Qt.Orientation.Horizontal) == self.value_column_header
        self._open_in_editor_action.setEnabled(is_value)
        self._plot_action.setEnabled(is_value)
        if is_value:
            plot_in_window_menu = QMenu("Plot in window")
            plot_in_window_menu.triggered.connect(self.plot_in_window)
            prepare_plot_in_window_menu(plot_in_window_menu)
            self._menu.insertMenu(self._plot_separator, plot_in_window_menu)
        self._menu.exec(event.globalPos())
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
            current = selection.takeAt(0)
            top = current.top()
            bottom = current.bottom()
            rows += range(top, bottom + 1)
        # Get parameter data grouped by db_map
        db_map_typed_data = dict()
        model = self.model()
        empty_model = model.empty_model
        for row in sorted(rows, reverse=True):
            sub_model = model.sub_model_at_row(row)
            if sub_model is empty_model:
                sub_row = model.sub_model_row(row)
                sub_model.removeRow(sub_row)
                continue
            db_map = sub_model.db_map
            id_ = model.item_at_row(row)
            db_map_typed_data.setdefault(db_map, {}).setdefault(model.item_type, []).append(id_)
        model.db_mngr.remove_items(db_map_typed_data)
        self.selectionModel().clearSelection()

    def _do_resize(self):
        self.resizeColumnsToContents()

    @Slot(QModelIndex, QModelIndex)
    def _refresh_copy_paste_actions(self, _, __):
        """Enables or disables copy and paste actions."""
        self._spine_db_editor.refresh_copy_paste_actions()


class ObjectParameterTableMixin:
    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("object_class_name", ObjectClassNameDelegate)


class RelationshipParameterTableMixin:
    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("relationship_class_name", RelationshipClassNameDelegate)


class ParameterDefinitionTableView(ParameterTableView):
    value_column_header = "default_value"

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("value_list_name", ValueListDelegate)
        delegate = self._make_delegate("default_value", ParameterDefaultValueDelegate)
        delegate.parameter_value_editor_requested.connect(self._spine_db_editor.show_parameter_value_editor)

    def _plot_selection(self, selection, plot_widget=None):
        """See base class"""
        raise NotImplementedError()


class ParameterValueTableView(ParameterTableView):
    value_column_header = "value"

    def connect_spine_db_editor(self, spine_db_editor):
        super().connect_spine_db_editor(spine_db_editor)
        self.selectionModel().selectionChanged.connect(self._update_pinned_values)

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("parameter_name", ParameterNameDelegate)
        self._make_delegate("alternative_name", AlternativeNameDelegate)
        delegate = self._make_delegate("value", ParameterValueDelegate)
        delegate.parameter_value_editor_requested.connect(self._spine_db_editor.show_parameter_value_editor)

    def _update_pinned_values(self, _selected, _deselected):
        row_pinned_value_iter = ((index.row(), self._make_pinned_value(index)) for index in self.selectedIndexes())
        self.pinned_values = list(
            {row: pinned_value for row, pinned_value in row_pinned_value_iter if pinned_value is not None}.values()
        )
        self._spine_db_editor.emit_pinned_values_updated()

    @property
    def _pk_fields(self):
        raise NotImplementedError()

    def _make_pinned_value(self, index):
        db_map, _ = self.model().db_map_id(index)
        if db_map is None:
            return None
        db_item = self.model().db_item(index)
        if db_item is None:
            return None
        return (db_map.db_url, {f: db_item[f] for f in self._pk_fields})

    def _plot_selection(self, selection, plot_widget=None):
        """See base class"""
        raise NotImplementedError()


class ObjectParameterDefinitionTableView(ObjectParameterTableMixin, ParameterDefinitionTableView):
    """A custom QTableView for the object parameter_definition pane in Spine db editor."""

    def _plot_selection(self, selection, plot_widget=None):
        """See base class"""
        header_sections = [
            ParameterTableHeaderSection(label) for label in ("database", "object_class_name", "parameter_name")
        ]
        return plot_parameter_table_selection(
            self.model(), selection, header_sections, self.value_column_header, plot_widget
        )


class RelationshipParameterDefinitionTableView(RelationshipParameterTableMixin, ParameterDefinitionTableView):
    """A custom QTableView for the relationship parameter_definition pane in Spine db editor."""

    def _plot_selection(self, selection, plot_widget=None):
        """See base class"""
        header_sections = [
            ParameterTableHeaderSection(label)
            for label in ("database", "relationship_class_name", "object_class_name_list", "parameter_name")
        ]
        for i, section in enumerate(header_sections):
            if section.label == "object_class_name_list":
                header_sections[i] = replace(section, separator=DB_ITEM_SEPARATOR)
                break
        return plot_parameter_table_selection(
            self.model(), selection, header_sections, self.value_column_header, plot_widget
        )


class ObjectParameterValueTableView(ObjectParameterTableMixin, ParameterValueTableView):
    """A custom QTableView for the object parameter_value pane in Spine db editor."""

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("object_name", ObjectNameDelegate)

    @property
    def _pk_fields(self):
        return "object_class_name", "object_name", "parameter_name", "alternative_name"

    def _plot_selection(self, selection, plot_widget=None):
        """See base class."""
        header_sections = [ParameterTableHeaderSection(label) for label in ("database",) + self._pk_fields]
        return plot_parameter_table_selection(
            self.model(), selection, header_sections, self.value_column_header, plot_widget
        )


class RelationshipParameterValueTableView(RelationshipParameterTableMixin, ParameterValueTableView):
    """A custom QTableView for the relationship parameter_value pane in Spine db editor."""

    def create_delegates(self):
        super().create_delegates()
        delegate = self._make_delegate("object_name_list", ObjectNameListDelegate)
        delegate.object_name_list_editor_requested.connect(self._spine_db_editor.show_object_name_list_editor)

    @property
    def _pk_fields(self):
        return "relationship_class_name", "object_name_list", "parameter_name", "alternative_name"

    def _plot_selection(self, selection, plot_widget=None):
        """See base class."""
        header_sections = [ParameterTableHeaderSection(label) for label in ("database",) + self._pk_fields]
        for i, section in enumerate(header_sections):
            if section.label == "object_name_list":
                header_sections[i] = replace(section, separator=DB_ITEM_SEPARATOR)
                break
        return plot_parameter_table_selection(
            self.model(), selection, header_sections, self.value_column_header, plot_widget
        )


class PivotTableView(ResizingViewMixin, CopyPasteTableView):
    """Custom QTableView class with pivot capabilities.

    Uses 'contexts' to provide different UI elements (table headers, context menus,...) depending on what
    data the pivot table currently contains.
    """

    header_changed = Signal()

    class _ContextBase:
        """Base class for pivot table view's contexts."""

        _REMOVE_OBJECT = "Remove objects"
        _REMOVE_RELATIONSHIP = "Remove relationships"
        _REMOVE_PARAMETER = "Remove parameter definitions"
        _REMOVE_ALTERNATIVE = "Remove alternatives"
        _REMOVE_SCENARIO = "Remove scenarios"
        _DUPLICATE_SCENARIO = "Duplicate scenario"

        def __init__(self, view, db_editor, horizontal_header, vertical_header):
            """
            Args:
                view (PivotTableView): parent view
                db_editor (SpineDBEditor): database editor
                horizontal_header (QHeaderView): horizontal header
                vertical_header (QHeaderView): vertical header
            """
            self._view = view
            self._db_editor = db_editor
            self._selected_alternative_indexes = list()
            self._header_selection_lists = {"alternative": self._selected_alternative_indexes}
            self._remove_alternatives_action = None
            self._menu = QMenu(self._view)
            self.populate_context_menu()
            horizontal_header.setResizeContentsPrecision(self._db_editor.visible_rows)
            vertical_header.setDefaultSectionSize(preferred_row_height(self._view))
            self._view.setHorizontalHeader(horizontal_header)
            self._view.setVerticalHeader(vertical_header)
            self._view.header_changed.emit()

        def _clear_selection_lists(self):
            """Clears cached selected index lists."""
            self._selected_alternative_indexes.clear()

        def populate_context_menu(self):
            """Generates context menu."""
            raise NotImplementedError()

        def _refresh_selected_indexes(self):
            """Caches selected index lists."""
            self._clear_selection_lists()
            for index in map(self._view.model().mapToSource, self._view.selectedIndexes()):
                self._to_selection_lists(index)

        def remove_alternatives(self):
            """Removes selected alternatives from the database."""
            db_map_typed_data = {}
            source_model = self._view.source_model
            for index in self._selected_alternative_indexes:
                db_map, id_ = source_model._header_id(index)
                db_map_typed_data.setdefault(db_map, {}).setdefault("alternative", set()).add(id_)
            self._db_editor.db_mngr.remove_items(db_map_typed_data)

        @Slot(QPoint)
        def show_context_menu(self, position):
            """Shows the context menu."""
            self._refresh_selected_indexes()
            self._update_actions_availability()
            self._menu.exec(position)

        def _to_selection_lists(self, index):
            """Caches given index to corresponding selected index list.

            Args:
                index (QModelIndex): index to cache
            """
            if self._view.source_model.index_in_headers(index):
                top_left_id = self._view.source_model.top_left_id(index)
                header_type = self._view.source_model.top_left_headers[top_left_id].header_type
                try:
                    self._header_selection_lists[header_type].append(index)
                except KeyError:
                    pass

        def _update_actions_availability(self):
            """Enables/disables context menu entries before the menu is shown."""
            raise NotImplementedError()

    class _EntityContextBase(_ContextBase):
        """Base class for contexts that contain entities and entity classes."""

        def __init__(self, view, db_editor, horizontal_header, vertical_header):
            """
            Args:
                view (PivotTableView): parent view
                db_editor (SpineDBEditor): database editor
                horizontal_header (QHeaderView): horizontal header
                vertical_header (QHeaderView): vertical header
            """
            self._selected_entity_indexes = list()
            super().__init__(view, db_editor, horizontal_header, vertical_header)
            self._header_selection_lists["object"] = self._selected_entity_indexes

        def _can_remove_relationships(self):
            """Checks if it makes sense to remove selected relationships from the database.

            Returns:
                bool: True if relationships can be removed, False otherwise
            """
            return (
                self._view.source_model.item_type == "parameter_value"
                and self._db_editor.current_class_type == "relationship_class"
            )

        def _clear_selection_lists(self):
            """See base class."""
            self._selected_entity_indexes.clear()
            super()._clear_selection_lists()

        def populate_context_menu(self):
            """See base class."""
            raise NotImplementedError()

        def remove_objects(self):
            """Removes selected objects from the database."""
            db_map_typed_data = {}
            source_model = self._view.source_model
            for index in self._selected_entity_indexes:
                db_map, id_ = source_model._header_id(index)
                db_map_typed_data.setdefault(db_map, {}).setdefault("object", set()).add(id_)
            self._db_editor.db_mngr.remove_items(db_map_typed_data)

        def remove_relationships(self):
            """Removes selected relationships from the database."""
            db_map_relationship_lookup = {
                db_map: {rel["object_id_list"]: rel["id"] for rel in rels}
                for db_map, rels in self._db_editor._get_db_map_entities().items()
            }
            db_map_typed_data = {}
            source_model = self._view.source_model
            for index in self._selected_entity_indexes:
                db_map, object_ids = source_model.db_map_object_ids(index)
                object_id_list = ",".join([str(id_) for id_ in object_ids])
                id_ = db_map_relationship_lookup.get(db_map, {}).get(object_id_list)
                if id_:
                    db_map_typed_data.setdefault(db_map, {}).setdefault("relationship", set()).add(id_)
            self._db_editor.db_mngr.remove_items(db_map_typed_data)

        def _update_actions_availability(self):
            """See base class."""
            raise NotImplementedError()

    class _ParameterValueContext(_EntityContextBase):
        """Context for showing parameter values in the pivot table."""

        def __init__(self, view, db_editor):
            """
            Args:
                view (PivotTableView): parent view
                db_editor (SpineDBEditor): database editor
            """
            self._selected_parameter_indexes = list()
            self._selected_value_indexes = list()
            self._open_in_editor_action = None
            self._remove_values_action = None
            self._remove_parameters_action = None
            self._remove_objects_action = None
            self._remove_relationships_action = None
            self._plot_action = None
            self._plot_in_window_menu = None
            horizontal_header = ParameterValuePivotHeaderView(Qt.Orientation.Horizontal, "columns", view)
            vertical_header = ParameterValuePivotHeaderView(Qt.Orientation.Vertical, "rows", view)
            super().__init__(view, db_editor, horizontal_header, vertical_header)
            self._header_selection_lists["parameter"] = self._selected_parameter_indexes

        def _clear_selection_lists(self):
            """See base class."""
            self._selected_parameter_indexes.clear()
            self._selected_value_indexes.clear()
            super()._clear_selection_lists()

        def populate_context_menu(self):
            """See base class."""
            self._open_in_editor_action = self._menu.addAction("Edit...", self.open_in_editor)
            self._menu.addSeparator()
            self._plot_action = self._menu.addAction("Plot", self.plot)
            self._plot_in_window_menu = self._menu.addMenu("Plot in window")
            self._plot_in_window_menu.triggered.connect(self._plot_in_window)
            self._menu.addSeparator()
            self._menu.addAction(self._view.copy_action)
            self._menu.addAction(self._view.paste_action)
            self._menu.addSeparator()
            self._remove_values_action = self._menu.addAction("Remove parameter values", self.remove_values)
            self._remove_objects_action = self._menu.addAction(self._REMOVE_OBJECT, self.remove_objects)
            self._remove_relationships_action = self._menu.addAction(
                self._REMOVE_RELATIONSHIP, self.remove_relationships
            )
            self._remove_parameters_action = self._menu.addAction(self._REMOVE_PARAMETER, self.remove_parameters)
            self._remove_alternatives_action = self._menu.addAction(self._REMOVE_ALTERNATIVE, self.remove_alternatives)

        def open_in_editor(self):
            """Opens the parameter value editor for the first selected cell."""
            index = self._selected_value_indexes[0]
            self._db_editor.show_parameter_value_editor(index)

        def plot(self):
            """Plots the selected cells."""
            selected_indexes = self._view.selectedIndexes()
            model = self._view.model()
            try:
                plot_window = plot_pivot_table_selection(model, selected_indexes)
            except PlottingError as error:
                report_plotting_failure(error, self._view)
                return
            source_model = model.sourceModel()
            plotted_column_names = {
                source_model.column_name(index.column())
                for index in selected_indexes
                if source_model.index_in_data(model.mapToSource(index))
                or source_model.column_is_index_column(model.mapToSource(index).column())
            }
            plot_window.use_as_window(self._view, ", ".join(plotted_column_names))
            plot_window.show()

        @Slot(QAction)
        def _plot_in_window(self, action):
            """Plots the selected cells in an existing window."""
            window_id = action.text()
            plot_window = PlotWidget.plot_windows.get(window_id)
            if plot_window is None:
                self.plot()
                return
            selected_indexes = self._view.selectedIndexes()
            try:
                plot_pivot_table_selection(self._view.model(), selected_indexes, plot_window)
                plot_window.raise_()
            except PlottingError as error:
                report_plotting_failure(error, self._view)

        def remove_parameters(self):
            """Removes selected parameter definitions from the database."""
            db_map_typed_data = {}
            source_model = self._view.source_model
            for index in self._selected_parameter_indexes:
                db_map, id_ = source_model._header_id(index)
                db_map_typed_data.setdefault(db_map, {}).setdefault("parameter_definition", set()).add(id_)
            self._db_editor.db_mngr.remove_items(db_map_typed_data)

        def remove_values(self):
            """Removes selected parameter values from the database."""
            row_mask = set()
            column_mask = set()
            source_model = self._view.source_model
            for index in self._selected_value_indexes:
                row, column = source_model.map_to_pivot(index)
                row_mask.add(row)
                column_mask.add(column)
            data = source_model.model.get_pivoted_data(row_mask, column_mask)
            items = (item for row in data for item in row)
            db_map_typed_data = {}
            for item in items:
                if item is None:
                    continue
                db_map, id_ = item
                db_map_typed_data.setdefault(db_map, {}).setdefault("parameter_value", set()).add(id_)
            self._db_editor.db_mngr.remove_items(db_map_typed_data)

        @Slot(QPoint)
        def show_context_menu(self, position):
            prepare_plot_in_window_menu(self._plot_in_window_menu)
            super().show_context_menu(position)

        def _to_selection_lists(self, index):
            """See base class."""
            if self._view.source_model.index_in_data(index):
                self._selected_value_indexes.append(index)
            else:
                super()._to_selection_lists(index)

        def _update_actions_availability(self):
            """See base class."""
            self._open_in_editor_action.setEnabled(len(self._selected_value_indexes) == 1)
            self._plot_action.setEnabled(bool(self._selected_value_indexes))
            self._remove_values_action.setEnabled(bool(self._selected_value_indexes))
            self._remove_parameters_action.setEnabled(bool(self._selected_parameter_indexes))
            self._remove_objects_action.setEnabled(bool(self._selected_entity_indexes))
            self._remove_relationships_action.setEnabled(
                bool(self._selected_entity_indexes) and self._can_remove_relationships()
            )
            self._remove_alternatives_action.setEnabled(bool(self._selected_alternative_indexes))

    class _IndexExpansionContext(_ParameterValueContext):
        """Context for expanded parameter values"""

    class _RelationshipContext(_EntityContextBase):
        """Context for presenting relationships in the pivot table."""

        def __init__(self, view, db_editor):
            """
            Args:
                view (PivotTableView): parent view
                db_editor (SpineDBEditor): database editor
            """
            self._remove_objects_action = None
            horizontal_header = PivotTableHeaderView(Qt.Orientation.Horizontal, "columns", view)
            vertical_header = PivotTableHeaderView(Qt.Orientation.Vertical, "rows", view)
            super().__init__(view, db_editor, horizontal_header, vertical_header)

        def populate_context_menu(self):
            """See base class."""
            self._menu.addAction(self._view.copy_action)
            self._menu.addAction(self._view.paste_action)
            self._menu.addSeparator()
            self._remove_objects_action = self._menu.addAction(self._REMOVE_OBJECT, self.remove_objects)

        def _update_actions_availability(self):
            """See base class."""
            self._remove_objects_action.setEnabled(bool(self._selected_entity_indexes))

    class _ScenarioAlternativeContext(_ContextBase):
        """Context for presenting scenarios and alternatives"""

        def __init__(self, view, db_editor):
            """
            Args:
                view (PivotTableView): parent view
                db_editor (SpineDBEditor): database editor
            """
            self._selected_scenario_indexes = list()
            self._selected_scenario_alternative_indexes = list()
            self._generate_scenarios_action = None
            self._toggle_alternatives_checked = QAction("Check/uncheck selected")
            self._toggle_alternatives_checked.triggered.connect(self._toggle_checked_state)
            self._remove_scenarios_action = None
            self._duplicate_scenario_action = None
            horizontal_header = ScenarioAlternativePivotHeaderView(Qt.Orientation.Horizontal, "columns", view)
            horizontal_header.context_menu_requested.connect(self.show_context_menu)
            vertical_header = ScenarioAlternativePivotHeaderView(Qt.Orientation.Vertical, "rows", view)
            vertical_header.context_menu_requested.connect(self.show_context_menu)
            super().__init__(view, db_editor, horizontal_header, vertical_header)
            self._header_selection_lists["scenario"] = self._selected_scenario_indexes

        def _clear_selection_lists(self):
            """See base class."""
            self._selected_scenario_indexes.clear()
            self._selected_scenario_alternative_indexes.clear()
            super()._clear_selection_lists()

        def populate_context_menu(self):
            """See base class."""
            self._generate_scenarios_action = self._menu.addAction(
                "Generate scenarios...", self._open_scenario_generator
            )
            self._menu.addSeparator()
            self._menu.addAction(self._toggle_alternatives_checked)
            self._menu.addSeparator()
            self._menu.addAction(self._view.copy_action)
            self._menu.addAction(self._view.paste_action)
            self._menu.addSeparator()
            self._remove_alternatives_action = self._menu.addAction(self._REMOVE_ALTERNATIVE, self.remove_alternatives)
            self._remove_scenarios_action = self._menu.addAction(self._REMOVE_SCENARIO, self.remove_scenarios)
            self._duplicate_scenario_action = self._menu.addAction(self._DUPLICATE_SCENARIO, self.duplicate_scenario)

        def remove_scenarios(self):
            """Removes selected scenarios from the database."""
            db_map_typed_data = {}
            source_model = self._view.source_model
            for index in self._selected_scenario_indexes:
                db_map, id_ = source_model._header_id(index)
                db_map_typed_data.setdefault(db_map, {}).setdefault("scenario", set()).add(id_)
            self._db_editor.db_mngr.remove_items(db_map_typed_data)

        def duplicate_scenario(self):
            """Duplicates current scenario in the database."""
            index = self._selected_scenario_indexes[0]
            db_map, scen_id = self._view.source_model._header_id(index)
            self._db_editor.duplicate_scenario(db_map, scen_id)

        def _to_selection_lists(self, index):
            """See base class."""
            if self._view.source_model.index_in_data(index):
                self._selected_scenario_alternative_indexes.append(index)
            else:
                super()._to_selection_lists(index)

        def _update_actions_availability(self):
            """See base class."""
            self._generate_scenarios_action.setEnabled(bool(self._selected_alternative_indexes))
            self._remove_alternatives_action.setEnabled(bool(self._selected_alternative_indexes))
            self._remove_scenarios_action.setEnabled(bool(self._selected_scenario_indexes))
            self._duplicate_scenario_action.setEnabled(len(self._selected_scenario_indexes) == 1)

        def _open_scenario_generator(self):
            """Opens the scenario generator dialog."""
            source_model = self._view.source_model
            db_mngr = self._db_editor.db_mngr
            chosen_db_map = None
            alternatives = list()
            for index in self._selected_alternative_indexes:
                header_id = source_model._header_id(index)
                db_map, id_ = header_id
                if chosen_db_map is None:
                    chosen_db_map = db_map
                elif db_map is not chosen_db_map:
                    continue
                item = db_mngr.get_item(db_map, "alternative", id_)
                alternatives.append(item)
            generator = ScenarioGenerator(self._view, chosen_db_map, alternatives, self._db_editor)
            generator.show()

        @Slot()
        def _toggle_checked_state(self):
            """Toggles the checked state of selected alternatives."""
            source_model = self._view.source_model
            selected = [source_model.data(index) for index in self._selected_scenario_alternative_indexes]
            checked = len(selected) * [not all(selected)]
            source_model.batch_set_data(self._selected_scenario_alternative_indexes, checked)

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget, optional): parent widget
        """
        super().__init__(parent)
        self.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        # NOTE: order of creation of header tables is important for them to stack properly
        self._left_header_table = CopyPasteTableView(self)
        self._top_header_table = CopyPasteTableView(self)
        self._top_left_header_table = CopyPasteTableView(self)
        self._left_header_table.setObjectName("left")
        self._top_header_table.setObjectName("top")
        self._top_left_header_table.setObjectName("top-left")
        self._spine_db_editor = None
        self._context = None
        self._fetch_more_timer = QTimer(self)
        self._fetch_more_timer.setSingleShot(True)
        self._fetch_more_timer.setInterval(100)
        self._fetch_more_timer.timeout.connect(self._fetch_more_visible)
        self._left_header_table.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self._left_header_table.verticalScrollBar().setValue)
        self._top_header_table.horizontalScrollBar().valueChanged.connect(self.horizontalScrollBar().setValue)
        self.horizontalScrollBar().valueChanged.connect(self._top_header_table.horizontalScrollBar().setValue)
        # NOTE: order of the iteration below is important for calls to stackUnder
        for header_table in (self._top_left_header_table, self._top_header_table, self._left_header_table):
            header_table.setFocusPolicy(Qt.NoFocus)
            header_table.setStyleSheet(self.styleSheet())
            header_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            header_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            header_table.show()
            header_table.verticalHeader().hide()
            header_table.horizontalHeader().hide()
            header_table.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
            header_table.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
            header_table.setStyleSheet("QTableView { border: none;}")
            self.viewport().stackUnder(header_table)
        for header_table in (self._top_header_table, self._left_header_table):
            header_table.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _do_resize(self):
        self.resizeColumnsToContents()

    @property
    def source_model(self):
        return self.model().sourceModel()

    @property
    def db_mngr(self):
        return self.source_model.db_mngr

    def connect_spine_db_editor(self, spine_db_editor):
        self._spine_db_editor = spine_db_editor
        self.set_external_copy_and_paste_actions(spine_db_editor.ui.actionCopy, spine_db_editor.ui.actionPaste)
        self._spine_db_editor.pivot_table_proxy.sourceModelChanged.connect(self._change_context)
        self.selectionModel().selectionChanged.connect(self._refresh_copy_paste_actions)

    @Slot()
    def _change_context(self):
        """Changes the UI engine according to pivot model type."""
        model = self._spine_db_editor.pivot_table_proxy.sourceModel()
        if isinstance(model, ParameterValuePivotTableModel):
            self._context = self._ParameterValueContext(self, self._spine_db_editor)
        elif isinstance(model, RelationshipPivotTableModel):
            self._context = self._RelationshipContext(self, self._spine_db_editor)
        elif isinstance(model, IndexExpansionPivotTableModel):
            self._context = self._IndexExpansionContext(self, self._spine_db_editor)
        elif isinstance(model, ScenarioAlternativePivotTableModel):
            self._context = self._ScenarioAlternativeContext(self, self._spine_db_editor)
        else:
            raise RuntimeError(f"Unknown pivot table model: {type(model).__name__}")

    def contextMenuEvent(self, event):
        """Shows context menu.

        Args:
            event (QContextMenuEvent)
        """
        index = self.indexAt(event.pos())
        index = self.model().mapToSource(index)
        if not index.isValid() or self.source_model.index_within_top_left(index):
            pivot_menu = QMenu(self)
            title = TitleWidgetAction("Pivot", self._spine_db_editor)
            pivot_menu.addAction(title)
            pivot_menu.addActions(self._spine_db_editor.pivot_action_group.actions())
            pivot_menu.exec(event.globalPos())
            return
        self._context.show_context_menu(event.globalPos())

    def setModel(self, model):
        old_model = self.model()
        if old_model:
            old_model.model_data_changed.disconnect(self._fetch_more_timer.start)
            old_model.model_data_changed.disconnect(self._update_header_tables)
            old_model.modelReset.disconnect(self._update_header_tables)
            self.selectionModel().selectionChanged.disconnect(self._synch_selection_with_header_tables)
        super().setModel(model)
        for header_table in (self._left_header_table, self._top_header_table, self._top_left_header_table):
            header_table.setModel(model)
        model.model_data_changed.connect(self._fetch_more_timer.start)
        model.model_data_changed.connect(self._update_header_tables)
        model.modelReset.connect(self._update_header_tables)
        self.selectionModel().selectionChanged.connect(self._synch_selection_with_header_tables)

    @Slot(QItemSelection, QItemSelection)
    def _synch_selection_with_header_tables(self, selected, deselected):
        for header_table in (self._left_header_table, self._top_header_table):
            header_table.selectionModel().select(selected, QItemSelectionModel.Select)
            header_table.selectionModel().select(deselected, QItemSelectionModel.Deselect)

    def setIndexWidget(self, proxy_index, widget):
        self._top_left_header_table.setIndexWidget(proxy_index, widget)

    def setHorizontalHeader(self, horizontal_header):
        super().setHorizontalHeader(horizontal_header)
        horizontal_header.sectionResized.connect(self._update_section_width)
        for header_table in (self._left_header_table, self._top_header_table, self._top_left_header_table):
            header_table.horizontalHeader().setResizeContentsPrecision(horizontal_header.resizeContentsPrecision())

    def setVerticalHeader(self, vertical_header):
        super().setVerticalHeader(vertical_header)
        vertical_header.sectionResized.connect(self._update_section_height)
        for header_table in (self._left_header_table, self._top_header_table, self._top_left_header_table):
            header_table.verticalHeader().setDefaultSectionSize(vertical_header.defaultSectionSize())

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._update_header_tables_geometry()

    def _fetch_more_visible(self):
        model = self.model()
        scrollbar = self.verticalScrollBar()
        scrollbar_at_max = scrollbar.value() == scrollbar.maximum()
        if scrollbar_at_max and model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())

    def _update_header_tables(self):
        # Top
        for header_table in (self._top_header_table, self._top_left_header_table):
            for i in range(0, self.source_model.headerRowCount()):
                header_table.setRowHeight(i, self.rowHeight(i))
                header_table.setRowHidden(i, False)
            for i in range(self.source_model.headerRowCount(), self.source_model.rowCount()):
                header_table.setRowHidden(i, True)
        # Left
        for header_table in (self._left_header_table, self._top_left_header_table):
            for j in range(0, self.source_model.headerColumnCount()):
                header_table.setColumnWidth(j, self.columnWidth(j))
                header_table.setColumnHidden(j, False)
            for j in range(self.source_model.headerColumnCount(), self.source_model.columnCount()):
                header_table.setColumnHidden(j, True)
        self._update_header_tables_geometry()

    @Slot(int, int, int)
    def _update_section_width(self, logical_index, _old_size, new_size):
        for header_table in (self._left_header_table, self._top_header_table, self._top_left_header_table):
            header_table.setColumnWidth(logical_index, new_size)
        self._update_header_tables_geometry()

    @Slot(int, int, int)
    def _update_section_height(self, logical_index, _old_size, new_size):
        for header_table in (self._left_header_table, self._top_header_table, self._top_left_header_table):
            header_table.setRowHeight(logical_index, new_size)
        self._update_header_tables_geometry()

    def _update_header_tables_geometry(self):
        if not self.source_model:
            return
        x = self.verticalHeader().width() + self.frameWidth()
        y = self.horizontalHeader().height() + self.frameWidth()
        header_w = sum(self.columnWidth(j) for j in range(0, self.source_model.headerColumnCount()))
        header_h = sum(self.rowHeight(i) for i in range(0, self.source_model.headerRowCount()))
        total_w = self.viewport().width()
        total_h = self.viewport().height()
        self._left_header_table.setGeometry(x, y, header_w, total_h)
        self._top_header_table.setGeometry(x, y, total_w, header_h)
        self._top_left_header_table.setGeometry(x, y, header_w, header_h)

    @Slot(QModelIndex, QModelIndex)
    def _refresh_copy_paste_actions(self, _, __):
        self._spine_db_editor.refresh_copy_paste_actions()


class FrozenTableView(QTableView):
    header_dropped = Signal(QWidget, QWidget)

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


class MetadataTableViewBase(CopyPasteTableView):
    """Base for metadata and item metadata table views."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget, optional): parent widget
        """
        super().__init__(parent)
        self.verticalHeader().setDefaultSectionSize(preferred_row_height(self))
        self._menu = QMenu(self)
        self._db_editor = None

    def connect_spine_db_editor(self, db_editor):
        """Finishes view's initialization.

        Args:
             db_editor (SpineDBEditor): database editor instance
        """
        self._db_editor = db_editor
        self.set_external_copy_and_paste_actions(db_editor.ui.actionCopy, db_editor.ui.actionPaste)
        self._populate_context_menu()
        self._enable_delegates(db_editor)
        self.selectionModel().selectionChanged.connect(self._refresh_copy_paste_actions)

    def contextMenuEvent(self, event):
        menu_position = event.globalPos()
        self._menu.exec(menu_position)

    def _remove_selected(self):
        """Removes selected rows from view's model."""
        selected = self.selectionModel().selectedIndexes()
        if len(selected) == 1:
            self.model().removeRow(selected[0].row())
            return
        spans = rows_to_row_count_tuples(i.row() for i in selected)
        for span in spans:
            self.model().removeRows(span[0], span[1])

    def _enable_delegates(self, db_editor):
        """Creates delegates for this view

        Args:
            db_editor (SpineDBEditor): database editor
        """

    def _populate_context_menu(self):
        """Fills context menu with actions."""
        self._menu.addAction(self.copy_action)
        self._menu.addAction(self.paste_action)
        self._menu.addSeparator()
        self._menu.addAction("Remove row(s)", self._remove_selected)

    @Slot(QModelIndex, str)
    def _set_model_data(self, index, value):
        """Sets model data.

        Args:
            index (QModelIndex): model index to set
            value (str): value
        """
        self.model().setData(index, value)

    @Slot(QModelIndex, QModelIndex)
    def _refresh_copy_paste_actions(self):
        self._db_editor.refresh_copy_paste_actions()


class MetadataTableView(MetadataTableViewBase):
    """Table view for metadata."""

    def _enable_delegates(self, db_editor):
        """See base class."""
        delegate = DatabaseNameDelegate(self, db_editor.db_mngr)
        self.setItemDelegateForColumn(MetadataColumn.DB_MAP, delegate)
        delegate.data_committed.connect(self._set_model_data)


class ItemMetadataTableView(MetadataTableViewBase):
    """Table view for entity and parameter value metadata."""

    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent)
        self._item_metadata_model = None
        self._metadata_model = None

    def set_models(self, item_metadata_model, metadata_model):
        """Sets models.

        Args:
            item_metadata_model (ItemMetadataModel): item metadata model
            metadata_model (MetadataTableModel): metadata model
        """
        self._item_metadata_model = item_metadata_model
        self._metadata_model = metadata_model

    def _enable_delegates(self, db_editor):
        """See base class"""
        name_column_delegate = ItemMetadataDelegate(
            self._item_metadata_model, self._metadata_model, MetadataColumn.NAME, self
        )
        self.setItemDelegateForColumn(MetadataColumn.NAME, name_column_delegate)
        value_column_delegate = ItemMetadataDelegate(
            self._item_metadata_model, self._metadata_model, MetadataColumn.VALUE, self
        )
        self.setItemDelegateForColumn(MetadataColumn.VALUE, value_column_delegate)
        database_column_delegate = DatabaseNameDelegate(self, db_editor.db_mngr)
        self.setItemDelegateForColumn(MetadataColumn.DB_MAP, database_column_delegate)
        database_column_delegate.data_committed.connect(self._set_model_data)
