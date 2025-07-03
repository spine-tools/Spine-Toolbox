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
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QTableView, QTableWidget
from spinetoolbox.spine_db_editor.empty_table_size_hint_provider import EmptyTableSizeHintProvider, SizeHintProvided


class TestEmptyTableSizeHintProvider:
    def test_no_rows_in_models(self, parent_widget):
        top_table = QTableWidget(0, 0, parent_widget)
        bottom_table = QTableWidget(0, 0, parent_widget)
        size_provider = EmptyTableSizeHintProvider(top_table, bottom_table)
        original_hint = QSize(23, 23)
        hint = size_provider.size_hint_for_bottom_table(original_hint)
        expected_base_height = (
            parent_widget.height()
            - top_table.horizontalHeader().height()
            - top_table.contentsMargins().top()
            - top_table.contentsMargins().bottom()
        )
        assert hint.height() == expected_base_height
        assert hint.width() == 23

    def test_bottom_table_shrinks_when_rows_added_to_top_table(self, parent_widget):
        top_table = QTableWidget(0, 0, parent_widget)
        bottom_table = QTableWidget(0, 0, parent_widget)
        size_provider = EmptyTableSizeHintProvider(top_table, bottom_table)
        top_table.insertColumn(0)
        top_table.insertRow(0)
        original_hint = QSize(23, 23)
        hint = size_provider.size_hint_for_bottom_table(original_hint)
        expected_base_height = (
            parent_widget.height()
            - top_table.horizontalHeader().height()
            - top_table.contentsMargins().top()
            - top_table.contentsMargins().bottom()
        )
        assert hint.height() == expected_base_height - top_table.rowHeight(0)
        assert hint.width() == 23

    def test_bottom_table_grows_when_rows_removed_from_top_table(self, parent_widget):
        top_table = QTableWidget(0, 0, parent_widget)
        top_table.insertColumn(0)
        top_table.insertRow(0)
        bottom_table = QTableWidget(0, 0, parent_widget)
        size_provider = EmptyTableSizeHintProvider(top_table, bottom_table)
        top_table.removeRow(0)
        original_hint = QSize(23, 23)
        hint = size_provider.size_hint_for_bottom_table(original_hint)
        expected_base_height = (
            parent_widget.height()
            - top_table.horizontalHeader().height()
            - top_table.contentsMargins().top()
            - top_table.contentsMargins().bottom()
        )
        assert hint.height() == expected_base_height
        assert hint.width() == 23

    def test_bottom_table_grows_when_rows_added_to_it(self, parent_widget):
        top_table = QTableWidget(0, 0, parent_widget)
        top_table.insertColumn(0)
        while sum(top_table.rowHeight(row) for row in range(top_table.rowCount())) < parent_widget.height():
            top_table.insertRow(0)
        bottom_table = QTableWidget(0, 0, parent_widget)
        bottom_table.insertColumn(0)
        size_provider = EmptyTableSizeHintProvider(top_table, bottom_table)
        original_hint = QSize(23, 23)
        hint = size_provider.size_hint_for_bottom_table(original_hint)
        expected_base_height = (
            bottom_table.horizontalHeader().height()
            + bottom_table.contentsMargins().top()
            + bottom_table.contentsMargins().bottom()
        )
        assert hint.height() == expected_base_height
        assert hint.width() == 23
        bottom_table.insertRow(0)
        original_hint = QSize(23, 23)
        hint = size_provider.size_hint_for_bottom_table(original_hint)
        expected_base_height = (
            bottom_table.horizontalHeader().height()
            + bottom_table.contentsMargins().top()
            + bottom_table.contentsMargins().bottom()
        )
        assert hint.height() == expected_base_height + bottom_table.rowHeight(0)
        assert hint.width() == 23


class SizeHintProvidedTableView(SizeHintProvided, QTableView):
    pass


class MockSizeHintProvider:
    @staticmethod
    def size_hint_for_bottom_table(_):
        return QSize(23, 32)


class TestSizeHintProvided:
    def test_size_hint_comes_from_provider(self, parent_widget):
        table_view = SizeHintProvidedTableView(parent_widget)
        comparison_table = QTableView(parent_widget)
        assert table_view.sizeHint() == comparison_table.sizeHint()
        table_view.set_size_hint_provider(MockSizeHintProvider())
        assert table_view.sizeHint() == MockSizeHintProvider.size_hint_for_bottom_table(QSize())
