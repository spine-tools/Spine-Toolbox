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

"""Unit tests for the indexed_value_table_context_menu module."""
import unittest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from spinedb_api import Array, Map, TimePattern, TimeSeriesFixedResolution, TimeSeriesVariableResolution
from spinetoolbox.widgets.array_editor import ArrayEditor
from spinetoolbox.widgets.indexed_value_table_context_menu import (
    ArrayTableContextMenu,
    IndexedValueTableContextMenu,
    MapTableContextMenu,
)
from spinetoolbox.widgets.map_editor import MapEditor
from spinetoolbox.widgets.time_pattern_editor import TimePatternEditor
from spinetoolbox.widgets.time_series_fixed_resolution_editor import TimeSeriesFixedResolutionEditor
from spinetoolbox.widgets.time_series_variable_resolution_editor import TimeSeriesVariableResolutionEditor


class TestArrayTableContextMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_insert_row_after(self):
        editor = ArrayEditor()
        editor.set_value(Array([-1.0]))
        table_view = editor._ui.array_table_view
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 1))
        menu = ArrayTableContextMenu(editor, table_view, rect.center())
        insert_action = _find_action(menu, "Insert row after")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 1).data(), str(-1.0))
        self.assertEqual(model.index(1, 1).data(), str(0.0))
        editor.deleteLater()

    def test_insert_row_before(self):
        editor = ArrayEditor()
        editor.set_value(Array([-1.0]))
        table_view = editor._ui.array_table_view
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 1))
        menu = ArrayTableContextMenu(editor, table_view, rect.center())
        insert_action = _find_action(menu, "Insert row before")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 1).data(), str(0.0))
        self.assertEqual(model.index(1, 1).data(), str(-1.0))
        editor.deleteLater()

    def test_remove_rows(self):
        editor = ArrayEditor()
        editor.set_value(Array([-1.0, -2.0]))
        table_view = editor._ui.array_table_view
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 1))
        menu = ArrayTableContextMenu(editor, table_view, rect.center())
        remove_action = _find_action(menu, "Remove rows")
        self.assertIsNotNone(remove_action)
        remove_action.trigger()
        self.assertEqual(model.rowCount(), 1 + 1)
        self.assertEqual(model.index(0, 1).data(), str(-2.0))
        editor.deleteLater()

    def test_show_value_editor(self):
        editor = ArrayEditor()
        editor.set_value(Array([-1.0]))
        table_view = editor._ui.array_table_view
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 1))
        editor.open_value_editor = MagicMock()
        menu = ArrayTableContextMenu(editor, table_view, rect.center())
        open_action = _find_action(menu, "Edit...")
        self.assertIsNotNone(open_action)
        open_action.trigger()
        editor.open_value_editor.assert_called_once_with(model.index(0, 1))
        editor.deleteLater()


class TestIndexedValueTableContextMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_insert_row_after_with_time_pattern_editor(self):
        editor = TimePatternEditor()
        editor.set_value(TimePattern(["D1-2"], [-1.1]))
        table_view = editor._ui.pattern_edit_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = IndexedValueTableContextMenu(table_view, rect.center())
        insert_action = _find_action(menu, "Insert row after")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "D1-2")
        self.assertEqual(model.index(0, 1).data(), str(-1.1))
        self.assertEqual(model.index(1, 0).data(), "")
        self.assertEqual(model.index(1, 1).data(), str(0.0))
        editor.deleteLater()

    def test_insert_row_after_with_time_series_fixed_resolution_editor(self):
        editor = TimeSeriesFixedResolutionEditor()
        editor.set_value(TimeSeriesFixedResolution("2020-11-11T14:25", "1D", [-1.1], False, False))
        table_view = editor._ui.time_series_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = IndexedValueTableContextMenu(table_view, rect.center())
        insert_action = _find_action(menu, "Insert row after")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "2020-11-11T14:25:00")
        self.assertEqual(model.index(0, 1).data(), str(-1.1))
        self.assertEqual(model.index(1, 0).data(), "2020-11-12T14:25:00")
        self.assertEqual(model.index(1, 1).data(), str(0.0))
        editor.deleteLater()

    def test_insert_row_after_with_time_series_variable_resolution_editor(self):
        editor = TimeSeriesVariableResolutionEditor()
        editor.set_value(TimeSeriesVariableResolution(["2020-11-11T14:25"], [-1.1], False, False))
        table_view = editor._ui.time_series_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = IndexedValueTableContextMenu(table_view, rect.center())
        insert_action = _find_action(menu, "Insert row after")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "2020-11-11T14:25:00")
        self.assertEqual(model.index(0, 1).data(), str(-1.1))
        self.assertEqual(model.index(1, 0).data(), "2020-11-11T15:25:00")
        self.assertEqual(model.index(1, 1).data(), str(0.0))
        editor.deleteLater()

    def test_insert_row_before_with_time_pattern_editor(self):
        editor = TimePatternEditor()
        editor.set_value(TimePattern(["D1-2"], [-1.1]))
        table_view = editor._ui.pattern_edit_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = IndexedValueTableContextMenu(table_view, rect.center())
        insert_action = _find_action(menu, "Insert row before")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), str(0.0))
        self.assertEqual(model.index(1, 0).data(), "D1-2")
        self.assertEqual(model.index(1, 1).data(), str(-1.1))
        editor.deleteLater()

    def test_insert_row_before_with_time_series_fixed_resolution_editor(self):
        editor = TimeSeriesFixedResolutionEditor()
        editor.set_value(TimeSeriesFixedResolution("2020-11-11T14:25", "1D", [-1.1], False, False))
        table_view = editor._ui.time_series_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = IndexedValueTableContextMenu(table_view, rect.center())
        insert_action = _find_action(menu, "Insert row before")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "2020-11-11T14:25:00")
        self.assertEqual(model.index(0, 1).data(), str(0.0))
        self.assertEqual(model.index(1, 0).data(), "2020-11-12T14:25:00")
        self.assertEqual(model.index(1, 1).data(), str(-1.1))
        editor.deleteLater()

    def test_insert_row_before_with_time_series_variable_resolution_editor(self):
        editor = TimeSeriesVariableResolutionEditor()
        editor.set_value(TimeSeriesVariableResolution(["2020-11-11T14:25"], [-1.1], False, False))
        table_view = editor._ui.time_series_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = IndexedValueTableContextMenu(table_view, rect.center())
        insert_action = _find_action(menu, "Insert row before")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "2020-11-11T13:25:00")
        self.assertEqual(model.index(0, 1).data(), str(0.0))
        self.assertEqual(model.index(1, 0).data(), "2020-11-11T14:25:00")
        self.assertEqual(model.index(1, 1).data(), str(-1.1))
        editor.deleteLater()

    def test_remove_rows_with_time_pattern_editor(self):
        editor = TimePatternEditor()
        editor.set_value(TimePattern(["D1-2", "D3-4"], [-1.1, -2.2]))
        table_view = editor._ui.pattern_edit_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = ArrayTableContextMenu(editor, table_view, rect.center())
        remove_action = _find_action(menu, "Remove rows")
        self.assertIsNotNone(remove_action)
        remove_action.trigger()
        self.assertEqual(model.rowCount(), 1 + 1)
        self.assertEqual(model.index(0, 0).data(), "D3-4")
        self.assertEqual(model.index(0, 1).data(), str(-2.2))
        editor.deleteLater()

    def test_remove_rows_with_time_series_fixed_resolution_editor(self):
        editor = TimeSeriesFixedResolutionEditor()
        editor.set_value(TimeSeriesFixedResolution("2020-11-11T14:25", "1D", [-1.1, -2.2], False, False))
        table_view = editor._ui.time_series_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = ArrayTableContextMenu(editor, table_view, rect.center())
        remove_action = _find_action(menu, "Remove rows")
        self.assertIsNotNone(remove_action)
        remove_action.trigger()
        self.assertEqual(model.rowCount(), 1 + 1)
        self.assertEqual(model.index(0, 0).data(), "2020-11-11T14:25:00")
        self.assertEqual(model.index(0, 1).data(), str(-2.2))
        editor.deleteLater()

    def test_remove_rows_with_time_series_variable_resolution_editor(self):
        editor = TimeSeriesVariableResolutionEditor()
        editor.set_value(
            TimeSeriesVariableResolution(["2020-11-11T14:25", "2020-11-12T14:25"], [-1.1, -2.2], False, False)
        )
        table_view = editor._ui.time_series_table
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = ArrayTableContextMenu(editor, table_view, rect.center())
        remove_action = _find_action(menu, "Remove rows")
        self.assertIsNotNone(remove_action)
        remove_action.trigger()
        self.assertEqual(model.rowCount(), 1 + 1)
        self.assertEqual(model.index(0, 0).data(), "2020-11-12T14:25:00")
        self.assertEqual(model.index(0, 1).data(), str(-2.2))
        editor.deleteLater()


class TestMapTableContextMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_insert_column_after(self):
        editor = MapEditor()
        editor.set_value(Map(["a"], [-1.0]))
        table_view = editor._ui.map_table_view
        table_view.selectColumn(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = MapTableContextMenu(editor, table_view, rect.center())
        insert_action = _find_action(menu, "Insert column after")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.columnCount(), 3 + 1)
        self.assertEqual(model.index(0, 0).data(), "a")
        self.assertEqual(model.index(0, 1).data(), "")
        self.assertEqual(model.index(0, 2).data(), str(-1.0))
        editor.deleteLater()

    def test_insert_column_before(self):
        editor = MapEditor()
        editor.set_value(Map(["a"], [-1.0]))
        table_view = editor._ui.map_table_view
        table_view.selectColumn(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = MapTableContextMenu(editor, table_view, rect.center())
        insert_action = _find_action(menu, "Insert column before")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.columnCount(), 3 + 1)
        self.assertEqual(model.index(0, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), "a")
        self.assertEqual(model.index(0, 2).data(), str(-1.0))
        editor.deleteLater()

    def test_insert_row_after(self):
        editor = MapEditor()
        editor.set_value(Map(["a"], [-1.0]))
        table_view = editor._ui.map_table_view
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = MapTableContextMenu(editor, table_view, rect.center())
        insert_action = _find_action(menu, "Insert row after")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "a")
        self.assertEqual(model.index(0, 1).data(), str(-1.0))
        self.assertEqual(model.index(1, 0).data(), "a")
        self.assertEqual(model.index(1, 1).data(), str(-1.0))
        editor.deleteLater()

    def test_insert_row_before(self):
        editor = MapEditor()
        editor.set_value(Map(["a"], [-1.0]))
        table_view = editor._ui.map_table_view
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = MapTableContextMenu(editor, table_view, rect.center())
        insert_action = _find_action(menu, "Insert row before")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 2 + 1)
        self.assertEqual(model.index(0, 0).data(), "")
        self.assertEqual(model.index(0, 1).data(), "")
        self.assertEqual(model.index(1, 0).data(), "a")
        self.assertEqual(model.index(1, 1).data(), str(-1.0))
        editor.deleteLater()

    def test_remove_columns(self):
        editor = MapEditor()
        editor.set_value(Map(["a"], [-1.0]))
        table_view = editor._ui.map_table_view
        table_view.selectColumn(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = MapTableContextMenu(editor, table_view, rect.center())
        insert_action = _find_action(menu, "Remove columns")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.columnCount(), 1 + 1)
        self.assertEqual(model.index(0, 0).data(), str(-1.0))
        editor.deleteLater()

    def test_remove_rows(self):
        editor = MapEditor()
        editor.set_value(Map(["a"], [-1.0]))
        table_view = editor._ui.map_table_view
        table_view.selectRow(0)
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        menu = MapTableContextMenu(editor, table_view, rect.center())
        insert_action = _find_action(menu, "Remove rows")
        self.assertIsNotNone(insert_action)
        insert_action.trigger()
        self.assertEqual(model.rowCount(), 1)
        editor.deleteLater()

    def test_show_value_editor(self):
        editor = MapEditor()
        editor.set_value(Map(["a"], [-1.0]))
        table_view = editor._ui.map_table_view
        model = table_view.model()
        rect = table_view.visualRect(model.index(0, 0))
        editor.open_value_editor = MagicMock()
        menu = MapTableContextMenu(editor, table_view, rect.center())
        open_action = _find_action(menu, "Edit...")
        self.assertIsNotNone(open_action)
        open_action.trigger()
        editor.open_value_editor.assert_called_once_with(model.index(0, 0))
        editor.deleteLater()


def _find_action(menu, text):
    """Returns ``QAction`` with given text or None if not found."""
    for action in menu.actions():
        if action.text() == text:
            return action
    return None


if __name__ == "__main__":
    unittest.main()
