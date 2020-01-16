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
Offers a convenience function for time pattern and time series editor widgets.

:author: A. Soininen (VTT)
:date:   5.7.2019
"""

from PySide2.QtWidgets import QInputDialog, QMenu


def handle_table_context_menu(click_pos, table_view, model, parent_widget):
    """
    Shows a context menu for parameter value tables and handles the selection.

    Args:
        click_pos {QPoint): position from the context menu event
        table_view (QTableView): the table widget
        model (TimePatternModel, TimeSeriesModelFixedResolution, TimeSeriesModelVariableResolution): a model
        parent_widget (QWidget: context menu's parent widget
    """
    INSERT_SINGLE_AFTER = "Insert row after"
    INSERT_MULTI_AFTER = "Insert multiple rows after"
    INSERT_SINGLE_BEFORE = "Insert row before"
    INSERT_MULTI_BEFORE = "Insert multiple rows before"
    REMOVE = "Remove rows"
    column = table_view.columnAt(click_pos.x())
    row = table_view.rowAt(click_pos.y())
    if column < 0 or row < 0:
        return
    menu = QMenu(parent_widget)
    menu.addAction(INSERT_SINGLE_BEFORE)
    menu.addAction(INSERT_MULTI_BEFORE)
    menu.addSeparator()
    menu.addAction(INSERT_SINGLE_AFTER)
    menu.addAction(INSERT_MULTI_AFTER)
    menu.addSeparator()
    menu.addAction(REMOVE)
    global_pos = table_view.mapToGlobal(click_pos)
    action = menu.exec_(global_pos)
    if action is None:
        return
    action_text = action.text()
    selected_indexes = table_view.selectedIndexes()
    selected_rows = sorted([index.row() for index in selected_indexes])
    first_row = selected_rows[0]
    if action_text == INSERT_SINGLE_BEFORE:
        model.insertRows(first_row, 1)
    elif action_text == INSERT_MULTI_BEFORE:
        row_count, accepted = QInputDialog.getInt(
            parent_widget, "Enter number of rows", "Number of rows to insert", minValue=1
        )
        if accepted:
            model.insertRows(first_row, row_count)
    elif action_text == INSERT_SINGLE_AFTER:
        model.insertRows(first_row + 1, 1)
    elif action_text == INSERT_MULTI_AFTER:
        row_count, accepted = QInputDialog.getInt(
            parent_widget, "Enter number of rows", "Number of rows to insert", minValue=1
        )
        if accepted:
            model.insertRows(first_row + 1, row_count)
    elif action_text == REMOVE:
        _remove_rows(selected_rows, model)


def _remove_rows(selected_rows, model):
    """Packs consecutive rows into a single removeRows call."""

    class RowPack:
        def __init__(self, first_row, count):
            self.first_row = first_row
            self.count = count

    if len(selected_rows) == 1:
        packed_rows = [RowPack(selected_rows[0], 1)]
    else:
        packed_rows = [RowPack(selected_rows[0], 1)]
        row_count = 1
        for i in range(1, len(selected_rows)):
            if selected_rows[i] == selected_rows[i - 1] + 1:
                row_count += 1
            else:
                packed_rows[-1].count = row_count
                packed_rows.append(RowPack(selected_rows[i], 1))
                row_count = 1
        packed_rows[-1].count = row_count
    for row_pack in reversed(packed_rows):
        model.removeRows(row_pack.first_row, row_pack.count)
