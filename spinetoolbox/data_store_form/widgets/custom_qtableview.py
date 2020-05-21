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
from PySide2.QtWidgets import QTableView, QAbstractItemView, QMenu
from ...widgets.report_plotting_failure import report_plotting_failure
from ...widgets.plot_widget import PlotWidget, _prepare_plot_in_window_menu
from ...plotting import plot_selection, PlottingError, ParameterTablePlottingHints
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
    PivotTableDelegate,
)


class ParameterTableView(AutoFilterCopyPasteTableView):
    def __init__(self, parent):
        """Initialize the view."""
        super().__init__(parent=parent)
        self._menu = QMenu(self)
        self._data_store_form = None
        self.open_in_editor_action = None
        self.plot_action = None
        self.plot_separator = None

    @property
    def value_column_header(self):
        raise NotImplementedError()

    def connect_data_store_form(self, data_store_form):
        self._data_store_form = data_store_form
        self.create_context_menu()
        self.create_delegates()

    def _make_delegate(self, column_name, delegate_class):
        """Returns a custom delegate for a given view."""
        column = self.model().header.index(column_name)
        delegate = delegate_class(self._data_store_form, self._data_store_form.db_mngr)
        self.setItemDelegateForColumn(column, delegate)
        delegate.data_committed.connect(self._data_store_form.set_parameter_data)
        return delegate

    def create_delegates(self):
        self._make_delegate("database", DatabaseNameDelegate)

    def open_in_editor(self):
        index = self.currentIndex()
        self._data_store_form.show_parameter_value_editor(index)

    @Slot(bool)
    def plot(self, checked=False):
        selection = self.selectedIndexes()
        try:
            hints = ParameterTablePlottingHints()
            plot_widget = plot_selection(self.model(), selection, hints)
        except PlottingError as error:
            report_plotting_failure(error, self._data_store_form)
        else:
            plot_widget.use_as_window(self.window(), self.value_column_header)
            plot_widget.show()

    @Slot("QAction")
    def plot_in_window(self, action):
        """Plots in window given by the action's name."""
        plot_window_name = action.text()
        plot_window = PlotWidget.plot_windows.get(plot_window_name)
        selection = self.selectedIndexes()
        try:
            hints = ParameterTablePlottingHints()
            plot_selection(self.model(), selection, hints, plot_window)
            plot_window.raise_()
        except PlottingError as error:
            report_plotting_failure(error, self._data_store_form)

    def create_context_menu(self):
        self.open_in_editor_action = self._menu.addAction("Open in editor...", self.open_in_editor)
        self._menu.addSeparator()
        self.plot_action = self._menu.addAction("Plot", self.plot)
        self.plot_separator = self._menu.addSeparator()
        self._menu.addAction(self._data_store_form.ui.actionCopy)
        self._menu.addAction(self._data_store_form.ui.actionPaste)
        self._menu.addSeparator()
        self._menu.addAction(self._data_store_form.ui.actionRemove_selected)

    def contextMenuEvent(self, event):
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
            try:
                db_map = model.sub_model_at_row(row).db_map
            except AttributeError:
                # It's an empty model, just remove the row
                _, sub_row = model._row_map[row]
                model.empty_model.removeRow(sub_row)
            else:
                id_ = model.item_at_row(row)
                item = model.db_mngr.get_item(db_map, model.item_type, id_)
                db_map_typed_data.setdefault(db_map, {}).setdefault(model.item_type, []).append(item)
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
        delegate.parameter_value_editor_requested.connect(self._data_store_form.show_parameter_value_editor)


class ParameterValueTableView(ParameterTableView):
    @property
    def value_column_header(self):
        return "value"

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("parameter_name", ParameterNameDelegate)
        delegate = self._make_delegate("value", ParameterValueDelegate)
        delegate.parameter_value_editor_requested.connect(self._data_store_form.show_parameter_value_editor)


class ObjectParameterDefinitionTableView(ObjectParameterTableMixin, ParameterDefinitionTableView):
    """A custom QTableView for the object parameter definition pane in Data Store Form."""


class RelationshipParameterDefinitionTableView(RelationshipParameterTableMixin, ParameterDefinitionTableView):
    """A custom QTableView for the relationship parameter definition pane in Data Store Form."""


class ObjectParameterValueTableView(ObjectParameterTableMixin, ParameterValueTableView):
    """A custom QTableView for the object parameter value pane in Data Store Form."""

    def create_delegates(self):
        super().create_delegates()
        self._make_delegate("object_name", ObjectNameDelegate)


class RelationshipParameterValueTableView(RelationshipParameterTableMixin, ParameterValueTableView):
    """A custom QTableView for the relationship parameter value pane in Data Store Form."""

    def create_delegates(self):
        super().create_delegates()
        delegate = self._make_delegate("object_name_list", ObjectNameListDelegate)
        delegate.object_name_list_editor_requested.connect(self._data_store_form.show_object_name_list_editor)


class PivotTableView(CopyPasteTableView):
    """Custom QTableView class with pivot capabilities.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent=None):
        """Initialize the class."""
        super().__init__(parent)
        h_header = PivotTableHeaderView(Qt.Horizontal, "columns", self)
        v_header = PivotTableHeaderView(Qt.Vertical, "rows", self)
        self.setHorizontalHeader(h_header)
        self.setVerticalHeader(v_header)
        h_header.setContextMenuPolicy(Qt.CustomContextMenu)

    def setup_delegates(self, data_store_form):
        delegate = PivotTableDelegate(data_store_form)
        self.setItemDelegate(delegate)
        delegate.parameter_value_editor_requested.connect(data_store_form.show_parameter_value_editor)
        delegate.data_committed.connect(data_store_form._set_model_data)


class FrozenTableView(QTableView):

    header_dropped = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setAcceptDrops(True)

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
