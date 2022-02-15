######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

from PySide2.QtCore import Qt, Signal, Slot, QTimer, QModelIndex, QPoint
from PySide2.QtWidgets import QAction, QTableView, QMenu
from PySide2.QtGui import QKeySequence

from .scenario_generator import ScenarioGenerator
from ..mvcmodels.pivot_table_models import (
    ParameterValuePivotTableModel,
    RelationshipPivotTableModel,
    IndexExpansionPivotTableModel,
    ScenarioAlternativePivotTableModel,
)
from ..mvcmodels.metadata_table_model import Column as MetadataColumn
from ...widgets.report_plotting_failure import report_plotting_failure
from ...widgets.plot_widget import PlotWidget, _prepare_plot_in_window_menu
from ...widgets.custom_qtableview import CopyPasteTableView, AutoFilterCopyPasteTableView
from ...widgets.custom_qwidgets import TitleWidgetAction
from ...plotting import plot_selection, PlottingError, ParameterTablePlottingHints, PivotTablePlottingHints
from ...helpers import preferred_row_height, rows_to_row_count_tuples
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
)


@Slot(QModelIndex, object)
def _set_parameter_data(index, new_value):
    """Updates (object or relationship) parameter_definition or value with newly edited data."""
    index.model().setData(index, new_value)


class ParameterTableView(AutoFilterCopyPasteTableView):
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

    @property
    def value_column_header(self):
        """Either "default value" or "value". Used to identify the value column for advanced editing and plotting."""
        raise NotImplementedError()

    def connect_spine_db_editor(self, spine_db_editor):
        """Connects a Spine db editor to work with this view.

        Args:
             spine_db_editor (SpineDBEditor)
        """
        self._spine_db_editor = spine_db_editor
        self.populate_context_menu()
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
        self._menu.aboutToShow.connect(self._spine_db_editor.refresh_copy_paste_actions)
        # Shortcuts
        remove_rows_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Delete))
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
        is_value = model.headerData(index.column(), Qt.Horizontal) == self.value_column_header
        self._open_in_editor_action.setEnabled(is_value)
        self._plot_action.setEnabled(is_value)
        if is_value:
            plot_in_window_menu = QMenu("Plot in window")
            plot_in_window_menu.triggered.connect(self.plot_in_window)
            _prepare_plot_in_window_menu(plot_in_window_menu)
            self._menu.insertMenu(self._plot_separator, plot_in_window_menu)
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

    def connect_spine_db_editor(self, spine_db_editor):
        super().connect_spine_db_editor(spine_db_editor)
        self.selectionModel().selectionChanged.connect(self._update_pinned_values)

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("parameter_name", ParameterNameDelegate)
        self._make_delegate("alternative_name", AlternativeNameDelegate)
        delegate = self._make_delegate("value", ParameterValueDelegate)
        delegate.parameter_value_editor_requested.connect(self._spine_db_editor.show_parameter_value_editor)

    def populate_context_menu(self):
        """Creates a context menu for this view."""
        super().populate_context_menu()
        self._menu.addSeparator()
        self._show_value_metadata_action = self._menu.addAction("View metadata", self.show_value_metadata)

    def show_value_metadata(self):
        db_map_ids = {}
        for index in self.selectedIndexes():
            db_map, id_ = self.model().db_map_id(index)
            db_map_ids.setdefault(db_map, []).append(id_)
        self._spine_db_editor.show_db_map_parameter_value_metadata(db_map_ids)

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
        return (db_map.db_url, {f: db_item[f] for f in self._pk_fields})


class ObjectParameterDefinitionTableView(ObjectParameterTableMixin, ParameterDefinitionTableView):
    """A custom QTableView for the object parameter_definition pane in Spine db editor."""


class RelationshipParameterDefinitionTableView(RelationshipParameterTableMixin, ParameterDefinitionTableView):
    """A custom QTableView for the relationship parameter_definition pane in Spine db editor."""


class ObjectParameterValueTableView(ObjectParameterTableMixin, ParameterValueTableView):
    """A custom QTableView for the object parameter_value pane in Spine db editor."""

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("object_name", ObjectNameDelegate)

    @property
    def _pk_fields(self):
        return ("object_class_name", "object_name", "parameter_name", "alternative_name")


class RelationshipParameterValueTableView(RelationshipParameterTableMixin, ParameterValueTableView):
    """A custom QTableView for the relationship parameter_value pane in Spine db editor."""

    def create_delegates(self):
        super().create_delegates()
        delegate = self._make_delegate("object_name_list", ObjectNameListDelegate)
        delegate.object_name_list_editor_requested.connect(self._spine_db_editor.show_object_name_list_editor)

    @property
    def _pk_fields(self):
        return ("relationship_class_name", "object_name_list", "parameter_name", "alternative_name")


class PivotTableView(CopyPasteTableView):
    """Custom QTableView class with pivot capabilities.

    Uses 'contexts' to provide different UI elements (table headers, context menus,...) depending on what
    data the pivot table currently contains.
    """

    header_changed = Signal()

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget, optional): parent widget
        """
        super().__init__(parent)
        self._spine_db_editor = None
        self._context = None
        self._fetch_more_timer = QTimer(self)
        self._fetch_more_timer.setSingleShot(True)
        self._fetch_more_timer.setInterval(100)
        self._fetch_more_timer.timeout.connect(self._fetch_more_visible)

    class _ContextBase:
        """Base class for pivot table view's contexts."""

        _REMOVE_OBJECT = "Remove objects"
        _REMOVE_RELATIONSHIP = "Remove relationships"
        _REMOVE_PARAMETER = "Remove parameter definitions"
        _REMOVE_ALTERNATIVE = "Remove alternatives"
        _REMOVE_SCENARIO = "Remove scenarios"

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
            source_model = self._view.source_model
            for index in map(self._view.model().mapToSource, self._view.selectedIndexes()):
                self._to_selection_lists(index, source_model)

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
            self._menu.exec_(position)

        def _to_selection_lists(self, index, source_model):
            """Caches given index to corresponding selected index list.

            Args:
                index (QModelIndex): index to cache
                source_model (PivotTableModelBase): underlying model
            """
            if source_model.index_in_headers(index):
                top_left_id = source_model.top_left_id(index)
                header_type = source_model.top_left_headers[top_left_id].header_type
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
            horizontal_header = ParameterValuePivotHeaderView(Qt.Horizontal, "columns", view)
            vertical_header = ParameterValuePivotHeaderView(Qt.Vertical, "rows", view)
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
            self._menu.addAction(self._db_editor.ui.actionCopy)
            self._menu.addAction(self._db_editor.ui.actionPaste)
            self._menu.addSeparator()
            self._remove_values_action = self._menu.addAction("Remove parameter values", self.remove_values)
            self._remove_objects_action = self._menu.addAction(self._REMOVE_OBJECT, self.remove_objects)
            self._remove_relationships_action = self._menu.addAction(
                self._REMOVE_RELATIONSHIP, self.remove_relationships
            )
            self._remove_parameters_action = self._menu.addAction(self._REMOVE_PARAMETER, self.remove_parameters)
            self._remove_alternatives_action = self._menu.addAction(self._REMOVE_ALTERNATIVE, self.remove_alternatives)
            self._menu.aboutToShow.connect(self._db_editor.refresh_copy_paste_actions)

        def open_in_editor(self):
            """Opens the parameter value editor for the first selected cell."""
            index = self._selected_value_indexes[0]
            self._db_editor.show_parameter_value_editor(index)

        def plot(self):
            """Plots the selected cells."""
            selected_indexes = self._view.selectedIndexes()
            hints = PivotTablePlottingHints()
            model = self._view.model()
            try:
                plot_window = plot_selection(model, selected_indexes, hints)
            except PlottingError as error:
                report_plotting_failure(error, self)
                return
            plotted_column_names = {
                hints.column_label(model, index.column())
                for index in selected_indexes
                if hints.is_index_in_data(model, index)
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
            hints = PivotTablePlottingHints()
            try:
                plot_selection(self._view.model(), selected_indexes, hints, plot_window)
                plot_window.raise_()
            except PlottingError as error:
                report_plotting_failure(error, self)

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

        def _show_context_menu(self, position):
            """See base class."""
            _prepare_plot_in_window_menu(self._plot_in_window_menu)
            super().show_context_menu(position)

        def _to_selection_lists(self, index, source_model):
            """See base class."""
            if source_model.index_in_data(index):
                self._selected_value_indexes.append(index)
            else:
                super()._to_selection_lists(index, source_model)

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
            horizontal_header = PivotTableHeaderView(Qt.Horizontal, "columns", view)
            vertical_header = PivotTableHeaderView(Qt.Vertical, "rows", view)
            super().__init__(view, db_editor, horizontal_header, vertical_header)

        def populate_context_menu(self):
            """See base class."""
            self._menu.addAction(self._db_editor.ui.actionCopy)
            self._menu.addAction(self._db_editor.ui.actionPaste)
            self._menu.addSeparator()
            self._remove_objects_action = self._menu.addAction(self._REMOVE_OBJECT, self.remove_objects)
            self._menu.aboutToShow.connect(self._db_editor.refresh_copy_paste_actions)

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
            horizontal_header = ScenarioAlternativePivotHeaderView(Qt.Horizontal, "columns", view)
            horizontal_header.context_menu_requested.connect(self.show_context_menu)
            vertical_header = ScenarioAlternativePivotHeaderView(Qt.Vertical, "rows", view)
            vertical_header.context_menu_requested.connect(self.show_context_menu)
            super().__init__(view, db_editor, horizontal_header, vertical_header)
            self._header_selection_lists["scenario"] = self._selected_scenario_indexes

        def _clear_selection_lists(self):
            """See base class."""
            self._selected_scenario_indexes = list()
            self._selected_scenario_alternative_indexes = list()
            super()._clear_selection_lists()

        def populate_context_menu(self):
            """See base class."""
            self._generate_scenarios_action = self._menu.addAction(
                "Generate scenarios...", self._open_scenario_generator
            )
            self._menu.addSeparator()
            self._menu.addAction(self._toggle_alternatives_checked)
            self._menu.addSeparator()
            self._menu.addAction(self._db_editor.ui.actionCopy)
            self._menu.addAction(self._db_editor.ui.actionPaste)
            self._menu.addSeparator()
            self._remove_alternatives_action = self._menu.addAction(self._REMOVE_ALTERNATIVE, self.remove_alternatives)
            self._remove_scenarios_action = self._menu.addAction(self._REMOVE_SCENARIO, self.remove_scenarios)
            self._menu.aboutToShow.connect(self._db_editor.refresh_copy_paste_actions)

        def remove_scenarios(self):
            """Removes selected scenarios from the database."""
            db_map_typed_data = {}
            source_model = self._view.source_model
            for index in self._selected_scenario_indexes:
                db_map, id_ = source_model._header_id(index)
                db_map_typed_data.setdefault(db_map, {}).setdefault("scenario", set()).add(id_)
            self._db_editor.db_mngr.remove_items(db_map_typed_data)

        def _to_selection_lists(self, index, source_model):
            """See base class."""
            if source_model.index_in_data(index):
                self._selected_scenario_alternative_indexes.append(index)
            else:
                super()._to_selection_lists(index, source_model)

        def _update_actions_availability(self):
            """See base class."""
            self._generate_scenarios_action.setEnabled(bool(self._selected_alternative_indexes))
            self._remove_alternatives_action.setEnabled(bool(self._selected_alternative_indexes))
            self._remove_scenarios_action.setEnabled(bool(self._selected_scenario_indexes))

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

    @property
    def source_model(self):
        return self.model().sourceModel()

    @property
    def db_mngr(self):
        return self.source_model.db_mngr

    def connect_spine_db_editor(self, spine_db_editor):
        self._spine_db_editor = spine_db_editor
        self._spine_db_editor.pivot_table_proxy.sourceModelChanged.connect(self._change_context)

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
            pivot_menu.exec_(event.globalPos())
            return
        self._context.show_context_menu(event.globalPos())

    def setModel(self, model):
        old_model = self.model()
        if old_model:
            old_model.model_data_changed.disconnect(self._fetch_more_timer.start)
        super().setModel(model)
        model.model_data_changed.connect(self._fetch_more_timer.start)

    def _fetch_more_visible(self):
        model = self.model()
        scrollbar = self.verticalScrollBar()
        scrollbar_at_max = scrollbar.value() == scrollbar.maximum()
        if scrollbar_at_max and model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())


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


class MetadataTableView(CopyPasteTableView):
    def __init__(self, parent):
        super().__init__(parent)
        self.verticalHeader().setDefaultSectionSize(preferred_row_height(self))
        self._menu = QMenu(self)

    def connect_spine_db_editor(self, db_editor):
        """Finishes view's initialization.

        Args:
             db_editor (SpineDBEditor): database editor instance
        """
        self._populate_context_menu(db_editor)
        self._enable_delegates(db_editor)

    def contextMenuEvent(self, event):
        menu_position = event.globalPos()
        self._menu.exec_(menu_position)

    def _remove_selected(self):
        selected = self.selectionModel().selectedIndexes()
        if len(selected) == 1:
            self.model().removeRow(selected[0].row())
            return
        spans = rows_to_row_count_tuples(i.row() for i in selected)
        for span in spans:
            self.model().removeRows(span[0], span[1])

    def _enable_delegates(self, db_editor):
        """Creates delegates for this view"""
        delegate = DatabaseNameDelegate(self, db_editor.db_mngr)
        self.setItemDelegateForColumn(MetadataColumn.DB_MAP, delegate)
        delegate.data_committed.connect(self._set_model_data)

    def _populate_context_menu(self, db_editor):
        self._menu.addAction(db_editor.ui.actionCopy)
        self._menu.addAction(db_editor.ui.actionPaste)
        self._menu.addSeparator()
        self._menu.addAction("Remove row(s)", self._remove_selected)

    @Slot(QModelIndex, str)
    def _set_model_data(self, index, value):
        self.model().setData(index, value)


class ItemMetadataTableView(CopyPasteTableView):
    pass
