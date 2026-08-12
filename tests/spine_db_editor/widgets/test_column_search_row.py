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

"""View-layer tests for the stacked tables' per-column regex search row.

Exercises ``_ColumnSearchBar`` and ``ColumnSearchRowMixin`` on real stacked views built by a
``DBEditorTestBase`` editor: live filtering, the active-cell highlight, geometry under the header, the
database-column editor hiding with its column, keyboard navigation and the Alt guard.

The column-filter debounce is flushed by calling ``model.refresh()`` directly (mirroring the model-layer
tests) so no wall-clock timer is relied upon.
"""

import unittest
from unittest import mock
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.helpers import SEARCH_FIELD_ACTIVE_STYLE
from tests.mock_helpers import fetch_model
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase


def _key_event(key, modifiers, text=""):
    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)


class TestColumnSearchRow(DBEditorTestBase):
    def _value_view_and_model(self):
        self.put_mock_dataset_in_db_mngr()
        view = self.spine_db_editor.ui.tableView_parameter_value
        model = view.model()
        fetch_model(model)
        while model.rowCount() < 6:
            QApplication.processEvents()
        return view, model

    @staticmethod
    def _column(model, header_name):
        return model.header.index(header_name)

    @staticmethod
    def _byname_values(model):
        column = model.header.index("entity byname")
        return [model.index(row, column).data(Qt.ItemDataRole.DisplayRole) for row in range(model.rowCount())]

    def test_search_bar_has_one_editor_per_column(self):
        view, model = self._value_view_and_model()
        self.assertEqual(len(view._search_bar.editors()), model.columnCount())

    def test_typing_filters_rows_live_and_clearing_restores(self):
        view, model = self._value_view_and_model()
        self.assertEqual(model.rowCount(), 6)
        column = self._column(model, "entity byname")
        editor = view._search_bar._editors[column]
        editor.setText("pluto")
        model.refresh()
        names = self._byname_values(model)
        self.assertTrue(names)
        self.assertTrue(all("pluto" in name for name in names))
        # pluto, nemo|pluto and pluto|nemo carry a "pluto" element.
        self.assertEqual(len(names), 3)
        editor.setText("")
        model.refresh()
        self.assertEqual(model.rowCount(), 6)

    def test_search_row_ands_with_header_auto_filter(self):
        view, model = self._value_view_and_model()
        # Simulate a header auto-filter keeping only the "dog" class rows (pluto, scooby).
        model.set_auto_filter("entity_class_name", {"dog"})
        model.refresh()
        self.assertEqual(sorted(self._byname_values(model)), ["pluto", "scooby"])
        # A column search for "scooby" must AND with it, leaving just scooby.
        column = self._column(model, "entity byname")
        view._search_bar._editors[column].setText("scooby")
        model.refresh()
        self.assertEqual(self._byname_values(model), ["scooby"])

    def test_active_editor_gets_highlight_style(self):
        view, model = self._value_view_and_model()
        column = self._column(model, "entity byname")
        editor = view._search_bar._editors[column]
        self.assertEqual(editor.styleSheet(), "")
        editor.setText("nemo")
        self.assertEqual(editor.styleSheet(), SEARCH_FIELD_ACTIVE_STYLE)
        editor.setText("")
        self.assertEqual(editor.styleSheet(), "")

    def test_geometry_puts_search_row_directly_under_header(self):
        view, _ = self._value_view_and_model()
        view.updateGeometries()
        header = view.horizontalHeader()
        bar = view._search_bar
        # No empty strip above the header: it starts at the frame edge.
        self.assertEqual(header.geometry().top(), view.frameWidth())
        # The search row is one data row tall and sits immediately below the header.
        self.assertEqual(bar.HEIGHT, view.verticalHeader().defaultSectionSize())
        self.assertEqual(bar.geometry().top(), header.geometry().bottom() + 1)

    def test_database_column_editor_hides_with_its_column(self):
        view, model = self._value_view_and_model()
        self.spine_db_editor.show()
        self.addCleanup(self.spine_db_editor.hide)
        QApplication.setActiveWindow(self.spine_db_editor)
        db_column = model.columnCount() - 1
        view.set_db_column_visibility(False)
        view.updateGeometries()
        self.assertIsNone(view._search_bar.editor_for_column(db_column))
        view.set_db_column_visibility(True)
        view.updateGeometries()
        self.assertIsNotNone(view._search_bar.editor_for_column(db_column))

    def test_down_from_editor_returns_to_top_data_row(self):
        view, model = self._value_view_and_model()
        column = self._column(model, "entity byname")
        view._search_bar._editors[column].go_down.emit()
        self.assertEqual(view.currentIndex().row(), 0)
        self.assertEqual(view.currentIndex().column(), column)

    def test_up_from_top_data_row_focuses_search_editor(self):
        view, model = self._value_view_and_model()
        column = self._column(model, "entity byname")
        view.setCurrentIndex(model.index(0, column))
        self.assertTrue(view._at_top_for_search_focus())
        with mock.patch.object(view, "_focus_search_editor") as focus:
            view.keyPressEvent(_key_event(Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier))
            focus.assert_called_once_with(column)

    def test_left_right_navigate_between_visible_editors(self):
        view, model = self._value_view_and_model()
        self.spine_db_editor.show()
        self.addCleanup(self.spine_db_editor.hide)
        QApplication.setActiveWindow(self.spine_db_editor)
        QApplication.processEvents()
        view.updateGeometries()
        class_column = self._column(model, "class")
        byname_column = self._column(model, "entity byname")
        first_column = 0  # The leftmost ("group") editor is the first visible one.
        class_editor = view._search_bar._editors[class_column]
        byname_editor = view._search_bar._editors[byname_column]
        first_editor = view._search_bar._editors[first_column]
        class_editor.setFocus()
        self.assertTrue(class_editor.hasFocus())
        # Right moves to the next visible editor.
        view._on_navigate_right(class_column)
        self.assertTrue(byname_editor.hasFocus())
        # Left moves back.
        view._on_navigate_left(byname_column)
        self.assertTrue(class_editor.hasFocus())
        # Left from the first visible editor is a no-op (there is no visible editor before it).
        first_editor.setFocus()
        self.assertTrue(first_editor.hasFocus())
        view._on_navigate_left(first_column)
        self.assertTrue(first_editor.hasFocus())

    def test_focus_search_editor_targets_column_or_first_visible(self):
        view, model = self._value_view_and_model()
        self.spine_db_editor.show()
        self.addCleanup(self.spine_db_editor.hide)
        QApplication.setActiveWindow(self.spine_db_editor)
        QApplication.processEvents()
        view.updateGeometries()
        byname_column = self._column(model, "entity byname")
        view._focus_search_editor(byname_column)
        self.assertTrue(view._search_bar._editors[byname_column].hasFocus())
        # The database column is hidden, so focusing it falls back to the first visible editor.
        view._focus_search_editor(model.columnCount() - 1)
        self.assertTrue(view._search_bar._editors[0].hasFocus())

    def test_activate_search_focus_moves_from_data_cell_into_row(self):
        view, model = self._value_view_and_model()
        column = self._column(model, "entity byname")
        view.setCurrentIndex(model.index(0, column))
        with (
            mock.patch("spinetoolbox.spine_db_editor.helpers.QApplication.focusWidget", return_value=view),
            mock.patch.object(view, "_focus_search_editor") as focus,
        ):
            view.activate_search_focus()
            focus.assert_called_once_with(column)

    def test_activate_search_focus_keeps_focus_when_field_focused(self):
        view, model = self._value_view_and_model()
        column = self._column(model, "entity byname")
        editor = view._search_bar._editors[column]
        with (
            mock.patch("spinetoolbox.spine_db_editor.helpers.QApplication.focusWidget", return_value=editor),
            mock.patch.object(view, "_focus_search_editor") as focus,
        ):
            view.activate_search_focus()
            focus.assert_not_called()

    def test_activate_search_focus_restores_last_used_from_elsewhere(self):
        view, model = self._value_view_and_model()
        column = self._column(model, "entity byname")
        # Record that a search field was focused last, then leave for the tree.
        view._on_search_editor_focused(column)
        with (
            mock.patch(
                "spinetoolbox.spine_db_editor.helpers.QApplication.focusWidget",
                return_value=self.spine_db_editor.ui.treeView_entity,
            ),
            mock.patch.object(view, "_focus_search_editor") as focus,
        ):
            view.activate_search_focus()
            focus.assert_called_once_with(column)

    def test_alt_key_is_swallowed_in_search_editor(self):
        view, model = self._value_view_and_model()
        column = self._column(model, "entity byname")
        editor = view._search_bar._editors[column]
        editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier, "2"))
        self.assertEqual(editor.text(), "")
        editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.NoModifier, "2"))
        self.assertEqual(editor.text(), "2")


if __name__ == "__main__":
    unittest.main()
