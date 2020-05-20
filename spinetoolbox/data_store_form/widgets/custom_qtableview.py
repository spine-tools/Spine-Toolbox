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

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QTableView, QAbstractItemView
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

    def _make_delegate(self, data_store_form, column_name, delegate_class):
        """Returns a custom delegate for a given view."""
        column = self.model().header.index(column_name)
        delegate = delegate_class(data_store_form, data_store_form.db_mngr)
        self.setItemDelegateForColumn(column, delegate)
        delegate.data_committed.connect(data_store_form.set_parameter_data)
        return delegate

    def setup_delegates(self, data_store_form):
        self._make_delegate(data_store_form, "database", DatabaseNameDelegate)


class ObjectParameterTableMixin:
    def setup_delegates(self, data_store_form):
        super().setup_delegates(data_store_form)
        self._make_delegate(data_store_form, "object_class_name", ObjectClassNameDelegate)


class RelationshipParameterTableMixin:
    def setup_delegates(self, data_store_form):
        super().setup_delegates(data_store_form)
        self._make_delegate(data_store_form, "relationship_class_name", RelationshipClassNameDelegate)


class ParameterDefinitionTableView(ParameterTableView):
    def setup_delegates(self, data_store_form):
        super().setup_delegates(data_store_form)
        self._make_delegate(data_store_form, "parameter_tag_list", TagListDelegate)
        self._make_delegate(data_store_form, "value_list_name", ValueListDelegate)
        delegate = self._make_delegate(data_store_form, "default_value", ParameterDefaultValueDelegate)
        delegate.parameter_value_editor_requested.connect(data_store_form.show_parameter_value_editor)


class ParameterValueTableView(ParameterTableView):
    def setup_delegates(self, data_store_form):
        super().setup_delegates(data_store_form)
        self._make_delegate(data_store_form, "parameter_name", ParameterNameDelegate)
        delegate = self._make_delegate(data_store_form, "value", ParameterValueDelegate)
        delegate.parameter_value_editor_requested.connect(data_store_form.show_parameter_value_editor)


class ObjectParameterDefinitionTableView(ObjectParameterTableMixin, ParameterDefinitionTableView):
    pass


class RelationshipParameterDefinitionTableView(RelationshipParameterTableMixin, ParameterDefinitionTableView):
    pass


class ObjectParameterValueTableView(ObjectParameterTableMixin, ParameterValueTableView):
    def setup_delegates(self, data_store_form):
        super().setup_delegates(data_store_form)
        self._make_delegate(data_store_form, "object_name", ObjectNameDelegate)


class RelationshipParameterValueTableView(RelationshipParameterTableMixin, ParameterValueTableView):
    def setup_delegates(self, data_store_form):
        super().setup_delegates(data_store_form)
        delegate = self._make_delegate(data_store_form, "object_name_list", ObjectNameListDelegate)
        delegate.object_name_list_editor_requested.connect(data_store_form.show_object_name_list_editor)


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
