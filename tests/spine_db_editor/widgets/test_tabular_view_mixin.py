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

"""Unit tests for ``tabular_view_mixin`` module."""
import itertools
import unittest
from unittest.mock import patch
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QApplication
from spinedb_api import Map
from tests.mock_helpers import fetch_model
from tests.spine_db_editor.helpers import TestBase


class TestPivotHeaderDraggingAndDropping(TestBase):
    def _add_entity_class_data(self):
        data = {
            "entity_classes": (("class1",),),
            "parameter_definitions": (("class1", "parameter1"), ("class1", "parameter2")),
            "entities": (("class1", "object1"), ("class1", "object2")),
            "parameter_values": (
                ("class1", "object1", "parameter1", 1.0),
                ("class1", "object2", "parameter1", 3.0),
                ("class1", "object1", "parameter2", 5.0),
                ("class1", "object2", "parameter2", 7.0),
            ),
        }
        self._db_mngr.import_data({self._db_map: data})

    def _add_entity_class_data_with_indexes_values(self):
        data = {
            "entity_classes": (("class1",),),
            "parameter_definitions": (("class1", "parameter1"),),
            "entities": (("class1", "object1"), ("class1", "object2")),
            "parameter_values": (
                (
                    "class1",
                    "object1",
                    "parameter1",
                    Map(["k1", "k2"], [Map(["q1", "q2"], [11.0, 111.0]), Map(["q1", "q2"], [22.0, 222.0])]),
                ),
                (
                    "class1",
                    "object2",
                    "parameter1",
                    Map(["k1", "k2"], [Map(["q1", "q2"], [-11.0, -111.0]), Map(["q1", "q2"], [-22.0, -222.0])]),
                ),
            ),
        }
        self._db_mngr.import_data({self._db_map: data})

    def _start(self):
        get_item_exceptions = []

        def guarded_get_item(db_map, item_type, id_):
            try:
                return db_map.get_item(item_type, id=id_)
            except Exception as error:
                get_item_exceptions.append(error)
                return None

        with patch.object(self._db_mngr, "get_item") as get_item:
            get_item.side_effect = guarded_get_item
            object_class_index = self._db_editor.entity_tree_model.index(0, 0)
            fetch_model(self._db_editor.entity_tree_model)
            index = self._db_editor.entity_tree_model.index(0, 0, object_class_index)
            self._db_editor._update_class_attributes(index)
            with patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as mock_is_visible:
                mock_is_visible.return_value = True
                self._db_editor.do_reload_pivot_table()
            pivot_model = self._db_editor.pivot_table_model
            pivot_model.beginResetModel()
            pivot_model.endResetModel()
            QApplication.processEvents()
            self.assertEqual(get_item_exceptions, [])

    def _change_pivot_input_type(self, input_type):
        for action in self._db_editor.pivot_action_group.actions():
            if action.text() == input_type:
                with patch.object(self._db_editor.ui.dockWidget_pivot_table, "isVisible") as mock_is_visible:
                    mock_is_visible.return_value = True
                    action.trigger()
                break
        else:
            raise RuntimeError(f"Unknown input type '{input_type}'.")

    def test_drag_and_drop_database_from_frozen_table(self):
        self._add_entity_class_data()
        self._start()
        original_frozen_columns = tuple(self._db_editor.pivot_table_model.model.pivot_frozen)
        frozen_table_header_widget = self._get_header_widget(self._db_editor.ui.frozen_table, "database")
        self._drag_and_drop_header(frozen_table_header_widget, frozen_table_header_widget)
        self.assertEqual(self._db_editor.pivot_table_model.model.pivot_frozen, original_frozen_columns)

    def test_purging_data_in_value_mode(self):
        self._add_entity_class_data()
        self._start()
        pivot_model = self._db_editor.pivot_table_model
        self.assertEqual(pivot_model.rowCount(), 5)
        self._db_mngr.purge_items({self._db_map: ["alternative", "entity_class"]})
        self.assertEqual(pivot_model.rowCount(), 0)
        self.assertEqual(self._db_editor.frozen_table_model.rowCount(), 1)

    def test_purging_data_in_value_mode_when_entity_class_is_frozen(self):
        self._add_entity_class_data()
        self._start()
        database_header_widget = self._get_header_widget(self._db_editor.ui.frozen_table, "database")
        class_header_widget = self._get_header_widget(self._db_editor.ui.pivot_table, "class1")
        self._drag_and_drop_header(database_header_widget, class_header_widget)
        self._select_frozen_row(1)
        expected = [["alternative"], ["Base"]]
        self._assert_model_data_equals(self._db_editor.frozen_table_model, expected)
        expected = [
            [None, "parameter", "parameter1", "parameter2", None],
            ["database", "class1", None, None, None],
            ["TestPivotHeaderDraggingAndDropping_db", "object1", "1.0", "5.0", None],
            ["TestPivotHeaderDraggingAndDropping_db", "object2", "3.0", "7.0", None],
            ["TestPivotHeaderDraggingAndDropping_db", None, None, None, None],
        ]
        self._assert_model_data_equals(self._db_editor.pivot_table_model, expected)
        frozen_model = self._db_editor.frozen_table_model
        QApplication.processEvents()
        for frozen_column in range(self._db_editor.frozen_table_model.columnCount()):
            frozen_index = self._db_editor.frozen_table_model.index(0, frozen_column)
            if frozen_index.data() == "alternative":
                break
        else:
            raise RuntimeError("No 'alternative' column found in frozen table")
        alternative_header_widget = self._db_editor.ui.frozen_table.indexWidget(frozen_index)
        self._db_editor.handle_header_dropped(class_header_widget, alternative_header_widget)
        QApplication.processEvents()
        expected = [["class1", "alternative"], ["object1", "Base"], ["object2", "Base"]]
        self._assert_model_data_equals(frozen_model, expected)
        self._select_frozen_row(1)
        pivot_model = self._db_editor.pivot_table_model
        while pivot_model.rowCount() != 4:
            QApplication.processEvents()
        expected = [
            ["parameter", "parameter1", "parameter2", None],
            ["database", None, None, None],
            ["TestPivotHeaderDraggingAndDropping_db", "1.0", "5.0", None],
            ["TestPivotHeaderDraggingAndDropping_db", None, None, None],
        ]
        self._assert_model_data_equals(pivot_model, expected)
        self._db_mngr.purge_items({self._db_map: ["entity_class"]})
        self.assertEqual(pivot_model.rowCount(), 0)

    def test_purging_entity_classes_in_index_mode_does_not_crash_pivot_filter_menu(self):
        self._add_entity_class_data_with_indexes_values()
        self._start()
        self._change_pivot_input_type(self._db_editor._INDEX_EXPANSION)
        for filter_menu in self._db_editor.filter_menus.values():
            filter_menu._filter._filter_model.canFetchMore(None)
            filter_menu._filter._filter_model.fetchMore(None)
        while self._db_editor.pivot_table_model.rowCount() != 6:
            QApplication.processEvents()
        expected = [
            [None, "parameter", "parameter1"],
            ["class1", "index", None],
            ["object1", "k1", "Map"],
            ["object1", "k2", "Map"],
            ["object2", "k1", "Map"],
            ["object2", "k2", "Map"],
        ]
        self._assert_model_data_equals(self._db_editor.pivot_table_model, expected)
        self._db_mngr.purge_items({self._db_map: ["entity_class"]})
        self.assertEqual(self._db_editor.pivot_table_model.rowCount(), 0)
        for filter_menu in self._db_editor.filter_menus.values():
            self.assertEqual(filter_menu._menu_data, {})

    @staticmethod
    def _get_header_widget(table_view, name):
        model = table_view.model()
        for row, column in itertools.product(range(model.rowCount()), range(model.columnCount())):
            source_index = model.index(row, column)
            if source_index.data() == name:
                break
        else:
            raise RuntimeError(f"No '{name}' column found in {type(model).__name__}.")
        return table_view.indexWidget(source_index)

    def _drag_and_drop_header(self, source_header_widget, target_header_widget):
        self._db_editor.handle_header_dropped(source_header_widget, target_header_widget)
        QApplication.processEvents()

    def _select_frozen_row(self, row):
        model = self._db_editor.frozen_table_model
        self.assertGreater(row, 0)
        self.assertLess(row, model.rowCount())
        selected = model.index(row, 0)
        self._db_editor.ui.frozen_table.selectionModel().setCurrentIndex(
            selected, QItemSelectionModel.SelectionFlags.ClearAndSelect
        )
        QApplication.processEvents()
        self.assertEqual(model._selected_row, row)

    def _assert_model_data_equals(self, model, expected):
        row_count = model.rowCount()
        column_count = model.columnCount()
        self.assertEqual(row_count, len(expected))
        self.assertEqual(column_count, len(expected[0]))
        for row, column in itertools.product(range(row_count), range(column_count)):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])


if __name__ == "__main__":
    unittest.main()
