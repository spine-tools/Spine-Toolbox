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

from unittest import mock
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
import pytest
from spinetoolbox.spine_db_editor.widgets.search_bar_base import SEARCH_FIELD_ACTIVE_STYLE
from tests.mock_helpers import fetch_model
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase

FOCUS_WIDGET = "spinetoolbox.spine_db_editor.widgets.search_bar_base.QApplication.focusWidget"


def _key_event(key, modifiers, text=""):
    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)


@pytest.fixture
def editor_env(application):
    env = DBEditorTestBase()
    env.setUp()
    try:
        yield env
    finally:
        env.tearDown()
        env.doCleanups()


def _value_view_and_model(env):
    env.put_mock_dataset_in_db_mngr()
    view = env.spine_db_editor.ui.tableView_parameter_value
    model = view.model()
    fetch_model(model)
    while model.rowCount() < 6:
        QApplication.processEvents()
    return view, model


def _column(model, header_name):
    return model.header.index(header_name)


def _byname_values(model):
    column = model.header.index("entity byname")
    return [model.index(row, column).data(Qt.ItemDataRole.DisplayRole) for row in range(model.rowCount())]


def test_search_bar_has_one_editor_per_column(editor_env):
    view, model = _value_view_and_model(editor_env)
    assert len(view.search_bar.editors()) == model.columnCount()


def test_typing_filters_rows_live_and_clearing_restores(editor_env):
    view, model = _value_view_and_model(editor_env)
    assert model.rowCount() == 6
    column = _column(model, "entity byname")
    editor = view.search_bar._editors[column]
    editor.setText("pluto")
    model.refresh()
    names = _byname_values(model)
    assert names
    assert all("pluto" in name for name in names)
    # pluto, nemo|pluto and pluto|nemo carry a "pluto" element.
    assert len(names) == 3
    editor.setText("")
    model.refresh()
    assert model.rowCount() == 6


def test_search_row_ands_with_header_auto_filter(editor_env):
    view, model = _value_view_and_model(editor_env)
    # Simulate a header auto-filter keeping only the "dog" class rows (pluto, scooby).
    model.set_auto_filter("entity_class_name", {"dog"})
    model.refresh()
    assert sorted(_byname_values(model)) == ["pluto", "scooby"]
    # A column search for "scooby" must AND with it, leaving just scooby.
    column = _column(model, "entity byname")
    view.search_bar._editors[column].setText("scooby")
    model.refresh()
    assert _byname_values(model) == ["scooby"]


def test_active_editor_gets_highlight_style(editor_env):
    view, model = _value_view_and_model(editor_env)
    column = _column(model, "entity byname")
    editor = view.search_bar._editors[column]
    assert editor.styleSheet() == ""
    editor.setText("nemo")
    assert editor.styleSheet() == SEARCH_FIELD_ACTIVE_STYLE
    editor.setText("")
    assert editor.styleSheet() == ""


def test_geometry_puts_search_row_directly_under_header(editor_env):
    view, _ = _value_view_and_model(editor_env)
    view.updateGeometries()
    header = view.horizontalHeader()
    bar = view.search_bar
    # No empty strip above the header: it starts at the frame edge.
    assert header.geometry().top() == view.frameWidth()
    # The search row is one data row tall and sits immediately below the header.
    assert bar.HEIGHT == view.verticalHeader().defaultSectionSize()
    assert bar.geometry().top() == header.geometry().bottom() + 1


def test_database_column_editor_hides_with_its_column(editor_env):
    view, model = _value_view_and_model(editor_env)
    editor_env.spine_db_editor.show()
    editor_env.addCleanup(editor_env.spine_db_editor.hide)
    editor_env.spine_db_editor.activateWindow()
    db_column = model.columnCount() - 1
    view.set_db_column_visibility(False)
    view.updateGeometries()
    assert view.search_bar.editor_for_column(db_column) is None
    view.set_db_column_visibility(True)
    view.updateGeometries()
    assert view.search_bar.editor_for_column(db_column) is not None


def test_down_from_editor_returns_to_top_data_row(editor_env):
    view, model = _value_view_and_model(editor_env)
    column = _column(model, "entity byname")
    view.search_bar._editors[column].go_down.emit()
    assert view.currentIndex().row() == 0
    assert view.currentIndex().column() == column


def test_up_from_top_data_row_focuses_search_editor(editor_env):
    view, model = _value_view_and_model(editor_env)
    column = _column(model, "entity byname")
    view.setCurrentIndex(model.index(0, column))
    assert view._at_top_for_search_focus()
    with mock.patch.object(view, "_focus_search_editor") as focus:
        view.keyPressEvent(_key_event(Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier))
        focus.assert_called_once_with(column)


def test_left_right_navigate_between_visible_editors(editor_env):
    view, model = _value_view_and_model(editor_env)
    editor_env.spine_db_editor.show()
    editor_env.addCleanup(editor_env.spine_db_editor.hide)
    editor_env.spine_db_editor.activateWindow()
    QApplication.processEvents()
    view.updateGeometries()
    class_column = _column(model, "class")
    byname_column = _column(model, "entity byname")
    first_column = 0  # The leftmost ("group") editor is the first visible one.
    class_editor = view.search_bar._editors[class_column]
    byname_editor = view.search_bar._editors[byname_column]
    first_editor = view.search_bar._editors[first_column]
    class_editor.setFocus()
    assert class_editor.hasFocus()
    # Right moves to the next visible editor.
    view._on_navigate_right(class_column)
    assert byname_editor.hasFocus()
    # Left moves back.
    view._on_navigate_left(byname_column)
    assert class_editor.hasFocus()
    # Left from the first visible editor is a no-op (there is no visible editor before it).
    first_editor.setFocus()
    assert first_editor.hasFocus()
    view._on_navigate_left(first_column)
    assert first_editor.hasFocus()


def test_focus_search_editor_targets_column_or_first_visible(editor_env):
    view, model = _value_view_and_model(editor_env)
    editor_env.spine_db_editor.show()
    editor_env.addCleanup(editor_env.spine_db_editor.hide)
    editor_env.spine_db_editor.activateWindow()
    QApplication.processEvents()
    view.updateGeometries()
    byname_column = _column(model, "entity byname")
    view._focus_search_editor(byname_column)
    assert view.search_bar._editors[byname_column].hasFocus()
    # The database column is hidden, so focusing it falls back to the first visible editor.
    view._focus_search_editor(model.columnCount() - 1)
    assert view.search_bar._editors[0].hasFocus()


def test_activate_search_focus_moves_from_data_cell_into_row(editor_env):
    view, model = _value_view_and_model(editor_env)
    column = _column(model, "entity byname")
    view.setCurrentIndex(model.index(0, column))
    with (
        mock.patch(FOCUS_WIDGET, return_value=view),
        mock.patch.object(view, "_focus_search_editor") as focus,
    ):
        view.activate_search_focus()
        focus.assert_called_once_with(column)


def test_activate_search_focus_keeps_focus_when_field_focused(editor_env):
    view, model = _value_view_and_model(editor_env)
    column = _column(model, "entity byname")
    editor = view.search_bar._editors[column]
    with (
        mock.patch(FOCUS_WIDGET, return_value=editor),
        mock.patch.object(view, "_focus_search_editor") as focus,
    ):
        view.activate_search_focus()
        focus.assert_not_called()


def test_activate_search_focus_restores_last_used_from_elsewhere(editor_env):
    view, model = _value_view_and_model(editor_env)
    column = _column(model, "entity byname")
    # Record that a search field was focused last, then leave for the tree.
    view._on_search_editor_focused(column)
    with (
        mock.patch(FOCUS_WIDGET, return_value=editor_env.spine_db_editor.ui.treeView_entity),
        mock.patch.object(view, "_focus_search_editor") as focus,
    ):
        view.activate_search_focus()
        focus.assert_called_once_with(column)


def test_alt_key_is_swallowed_in_search_editor(editor_env):
    view, model = _value_view_and_model(editor_env)
    column = _column(model, "entity byname")
    editor = view.search_bar._editors[column]
    editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier, "2"))
    assert editor.text() == ""
    editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.NoModifier, "2"))
    assert editor.text() == "2"
