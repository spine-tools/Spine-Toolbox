######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
from typing import Optional
from PySide6.QtCore import QAbstractItemModel, QModelIndex, QPersistentModelIndex, QSize
from PySide6.QtWidgets import QTableView


class EmptyTableSizeHintProvider:
    """Finds suitable height for the empty table depending on how many rows the compound table contains."""

    def __init__(self, top_table: QTableView, bottom_table: QTableView):
        self._top_table = top_table
        self._top_total_height = calculate_table_height(self._top_table)
        top_model = self._top_table.model()
        top_model.rowsInserted.connect(self._top_rows_changed)
        top_model.rowsRemoved.connect(self._top_rows_changed)
        top_model.modelReset.connect(self._update_top_total_height)
        top_model.layoutChanged.connect(self._top_layout_changed)
        self._bottom_table = bottom_table

    def _top_rows_changed(self, parent: QModelIndex, first: int, last: int) -> None:
        self._update_top_total_height()

    def _top_layout_changed(
        self, parents: list[QPersistentModelIndex], hint: QAbstractItemModel.LayoutChangeHint
    ) -> None:
        self._update_top_total_height()

    def _update_top_total_height(self) -> None:
        top_total_height = calculate_table_height(self._top_table)
        if top_total_height != self._top_total_height:
            self._top_total_height = top_total_height
            self._bottom_table.updateGeometry()

    def size_hint_for_bottom_table(self, bottoms_own_hint: QSize) -> QSize:
        container_height = self._top_table.parent().height()
        bottom_total_height = calculate_table_height(self._bottom_table)
        bottoms_own_hint.setHeight(max(container_height - self._top_total_height, bottom_total_height))
        return bottoms_own_hint


class SizeHintProvided:
    """A mixin that uses the size hint provided by StackedTableDivision."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._size_hint_provider: Optional[EmptyTableSizeHintProvider] = None

    def set_size_hint_provider(self, provider: EmptyTableSizeHintProvider) -> None:
        self._size_hint_provider = provider

    def sizeHint(self, /):
        own_hint = super().sizeHint()
        if self._size_hint_provider is not None:
            return self._size_hint_provider.size_hint_for_bottom_table(own_hint)
        return own_hint


def calculate_table_height(table: QTableView) -> int:
    row_count = table.model().rowCount()
    row_height = table.rowHeight(0) if row_count != 0 else 0
    contents_margins = table.contentsMargins()
    return (
        row_count * row_height + table.horizontalHeader().height() + contents_margins.top() + contents_margins.bottom()
    )
