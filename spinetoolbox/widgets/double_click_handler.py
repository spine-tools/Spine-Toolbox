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
Contains the TreeViewForm class.

:author: A. Soininen (VTT)
:date:   17.7.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTableView
from spinedb_api import from_database, DateTime, Duration, ParameterValueFormatError, TimePattern, TimeSeries
from widgets.parameter_value_editor import ParameterValueEditor

# NOTE: Both `overwrite_table_double_click_handlers` and `OpenEditorOrDefaultDelegate`
# are not used at the moment. The reason is I want to show the `ParameterValueEditor`
# not only on double click, but everytime the cell is *edited* (edit triggers include double click *and* key press).
# So now I've hooked the `ParameterValueEditor` to the `edit` slot of the concerned tables.
# It's not too big of a change, so we can fall back to this if I'm wrong.
# Otherwise, if you believe I'm right we can just remove this.


def overwrite_table_double_click_handlers(form):
    """
    Sets new double click event handlers for the table views.

    The new handler opens a ParameterValueEditor if the table cell contains a 'complicated' value,
    otherwise the default editor delegate is used.

    Args:
        form (GraphViewForm, TreeViewForm): a form in which to change the mouse event handlers.
    """
    form.ui.tableView_object_parameter_value.mouseDoubleClickEvent = OpenEditorOrDefaultDelegate(
        form, form.ui.tableView_object_parameter_value, "value"
    )
    form.ui.tableView_object_parameter_definition.mouseDoubleClickEvent = OpenEditorOrDefaultDelegate(
        form, form.ui.tableView_object_parameter_definition, "default_value"
    )
    form.ui.tableView_relationship_parameter_value.mouseDoubleClickEvent = OpenEditorOrDefaultDelegate(
        form, form.ui.tableView_relationship_parameter_value, "value"
    )
    form.ui.tableView_relationship_parameter_definition.mouseDoubleClickEvent = OpenEditorOrDefaultDelegate(
        form, form.ui.tableView_relationship_parameter_definition, "default_value"
    )


class OpenEditorOrDefaultDelegate:
    """
    A functor to replace the double click event handler of a table view.

    This is meant to be used as a replacement for the default double click handler
    in the (relationship) parameter value/definition tables.
    By default, a double click opens an editor widget if the table cell is editable.
    If the cell contains some 'complex' parameter value, however,
    we open the parameter value editor window instead.

    Args:
        parent_view (TreeViewForm, GraphViewForm): a reference to the parent window
        table_view (QTableView): a reference to the table view
        value_column_header (str): name of the value or default value column, for identification
    """

    def __init__(self, parent_view, table_view, value_column_header):
        self._parent_view = parent_view
        self._table_view = table_view
        self._column_header = value_column_header

    def __call__(self, event):
        """Handles a double click QMouseEvent event on a QTableView."""
        index = self._table_view.indexAt(event.pos())
        model = index.model()
        flags = model.flags(index)
        editable = (flags & Qt.ItemIsEditable) == Qt.ItemIsEditable
        is_value = model.headerData(index.column(), Qt.Horizontal) == self._column_header
        if editable and is_value:
            try:
                value = from_database(index.data(role=Qt.EditRole))
            except ParameterValueFormatError:
                value = None
            if isinstance(value, (DateTime, Duration, TimePattern, TimeSeries)) or value is None:
                self._table_view.doubleClicked.emit(index)
                editor = ParameterValueEditor(index, value=value, parent_widget=self._parent_view)
                editor.show()
                return
        # pylint: disable=bad-super-call
        super(QTableView, self._table_view).mouseDoubleClickEvent(event)


class OpenEditorOrDefaultDelegateForPivotTable:
    """
    A functor to replace the double click event handler of a table view.

    This is meant to be used as a replacement for the default double click handler
    in the (relationship) parameter value/definition tables.
    By default, a double click opens an editor widget if the table cell is editable.
    If the cell contains some 'complex' parameter value, however,
    we open the parameter value editor window instead.

    Args:
        parent_view (TreeViewForm, GraphViewForm): a reference to the parent window
        table_view (QTableView): a reference to the table view
        pivot_model (PivotTableModel)
    """

    def __init__(self, parent_view, table_view, pivot_model):
        self._parent_view = parent_view
        self._pivot_model = pivot_model
        self._table_view = table_view

    def __call__(self, event):
        """Handles a double click QMouseEvent event on a QTableView."""
        index = self._table_view.indexAt(event.pos())
        flags = self._pivot_model.flags(index)
        editable = (flags & Qt.ItemIsEditable) == Qt.ItemIsEditable
        is_value = self._pivot_model.index_in_data(index)
        if editable and is_value:
            try:
                value = from_database(index.data(role=Qt.EditRole))
            except ParameterValueFormatError:
                value = None
            if isinstance(value, (DateTime, Duration, TimePattern, TimeSeries)) or value is None:
                self._table_view.doubleClicked.emit(index)
                editor = ParameterValueEditor(index, value=value, parent_widget=self._parent_view)
                editor.show()
                return
        # pylint: disable=bad-super-call
        super(QTableView, self._table_view).mouseDoubleClickEvent(event)
