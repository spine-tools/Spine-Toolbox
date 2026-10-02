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

from unittest import mock
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
import pytest
from spinetoolbox.spine_db_editor.widgets.search_bar_base import SEARCH_FIELD_ACTIVE_STYLE
from tests.mock_helpers import fetch_model

FOCUS_WIDGET = "spinetoolbox.spine_db_editor.widgets.search_bar_base.QApplication.focusWidget"


def _key_event(key, modifiers, text=""):
    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)


@pytest.fixture
def parameter_value_view(db_editor):
    yield db_editor.ui.tableView_parameter_value


@pytest.fixture
def parameter_value_model(parameter_value_view, dog_fish_db_map):
    model = parameter_value_view.model()
    fetch_model(model)
    while model.rowCount() < 6:
        QApplication.processEvents()
    yield model


def _column(model, header_name):
    return model.header.index(header_name)


def _byname_values(model):
    column = model.header.index("entity byname")
    return [model.index(row, column).data(Qt.ItemDataRole.DisplayRole) for row in range(model.rowCount())]


def test_search_bar_has_one_editor_per_column(parameter_value_view, parameter_value_model):
    assert len(parameter_value_view.search_bar.editors()) == parameter_value_model.columnCount()


def test_typing_filters_rows_live_and_clearing_restores(parameter_value_view, parameter_value_model):
    assert parameter_value_model.rowCount() == 6
    column = _column(parameter_value_model, "entity byname")
    editor = parameter_value_view.search_bar._editors[column]
    editor.setText("pluto")
    parameter_value_model.refresh()
    names = _byname_values(parameter_value_model)
    assert names
    assert all("pluto" in name for name in names)
    # pluto, nemo|pluto and pluto|nemo carry a "pluto" element.
    assert len(names) == 3
    editor.setText("")
    parameter_value_model.refresh()
    assert parameter_value_model.rowCount() == 6


def test_search_row_ands_with_header_auto_filter(parameter_value_view, parameter_value_model):
    parameter_value_model.set_auto_filter("entity_class_name", {"dog"})
    parameter_value_model.refresh()
    assert sorted(_byname_values(parameter_value_model)) == ["pluto", "scooby"]
    column = _column(parameter_value_model, "entity byname")
    parameter_value_view.search_bar._editors[column].setText("scooby")
    parameter_value_model.refresh()
    assert _byname_values(parameter_value_model) == ["scooby"]


def test_active_editor_gets_highlight_style(parameter_value_view, parameter_value_model):
    column = _column(parameter_value_model, "entity byname")
    editor = parameter_value_view.search_bar._editors[column]
    assert editor.styleSheet() == ""
    editor.setText("nemo")
    assert editor.styleSheet() == SEARCH_FIELD_ACTIVE_STYLE
    editor.setText("")
    assert editor.styleSheet() == ""


def test_geometry_puts_search_row_directly_under_header(parameter_value_view):
    parameter_value_view.updateGeometries()
    header = parameter_value_view.horizontalHeader()
    bar = parameter_value_view.search_bar
    # No empty strip above the header: it starts at the frame edge.
    assert header.geometry().top() == parameter_value_view.frameWidth()
    # The search row is one data row tall and sits immediately below the header.
    assert bar.HEIGHT == parameter_value_view.verticalHeader().defaultSectionSize()
    assert bar.geometry().top() == header.geometry().bottom() + 1


def test_database_column_editor_hides_with_its_column(parameter_value_view, parameter_value_model, monkeypatch):
    db_column = parameter_value_model.columnCount() - 1
    editor = parameter_value_view.search_bar._editors[db_column]
    monkeypatch.setattr(editor, "isVisible", lambda: False)
    assert parameter_value_view.search_bar.editor_for_column(db_column) is None
    monkeypatch.setattr(editor, "isVisible", lambda: True)
    assert parameter_value_view.search_bar.editor_for_column(db_column) is not None


def test_down_from_editor_returns_to_top_data_row(parameter_value_view, parameter_value_model):
    column = _column(parameter_value_model, "entity byname")
    parameter_value_view.search_bar._editors[column].go_down.emit()
    assert parameter_value_view.currentIndex().row() == 0
    assert parameter_value_view.currentIndex().column() == column


def test_up_from_top_data_row_focuses_search_editor(parameter_value_view, parameter_value_model):
    column = _column(parameter_value_model, "entity byname")
    parameter_value_view.setCurrentIndex(parameter_value_model.index(0, column))
    assert parameter_value_view._at_top_for_search_focus()
    with mock.patch.object(parameter_value_view, "_focus_search_editor") as focus:
        parameter_value_view.keyPressEvent(_key_event(Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier))
        focus.assert_called_once_with(column)


class FocusMethod:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1


def test_left_right_navigate_between_visible_editors(parameter_value_view, parameter_value_model, monkeypatch):
    class_column = _column(parameter_value_model, "class")
    byname_column = _column(parameter_value_model, "entity byname")
    first_column = 0
    class_editor = parameter_value_view.search_bar._editors[class_column]
    byname_editor = parameter_value_view.search_bar._editors[byname_column]
    first_editor = parameter_value_view.search_bar._editors[first_column]
    for editor in (first_editor, class_editor, byname_editor):
        monkeypatch.setattr(editor, "isVisible", lambda: True)
        monkeypatch.setattr(editor, "setFocus", FocusMethod())
    parameter_value_view._on_navigate_right(class_column)
    assert byname_editor.setFocus.calls == 1
    parameter_value_view._on_navigate_left(byname_column)
    assert class_editor.setFocus.calls == 1
    parameter_value_view._on_navigate_left(first_column)
    assert first_editor.setFocus.calls == 0


def test_focus_search_editor_targets_column_or_first_visible(parameter_value_view, parameter_value_model, monkeypatch):
    parameter_value_view.updateGeometries()
    byname_column = _column(parameter_value_model, "entity byname")
    byname_editor = parameter_value_view.search_bar._editors[byname_column]
    monkeypatch.setattr(byname_editor, "isVisible", lambda: True)
    monkeypatch.setattr(byname_editor, "setFocus", FocusMethod())
    parameter_value_view._focus_search_editor(byname_column)
    assert byname_editor.setFocus.calls == 1
    # The database column is hidden, so focusing it falls back to the first visible editor.
    db_column = parameter_value_model.columnCount() - 1
    db_editor = parameter_value_view.search_bar._editors[db_column]
    monkeypatch.setattr(db_editor, "isVisible", lambda: False)
    monkeypatch.setattr(db_editor, "setFocus", FocusMethod())
    first_editor = parameter_value_view.search_bar._editors[0]
    monkeypatch.setattr(first_editor, "isVisible", lambda: True)
    monkeypatch.setattr(first_editor, "setFocus", FocusMethod())
    parameter_value_view._focus_search_editor(db_column)
    assert db_editor.setFocus.calls == 0
    assert first_editor.setFocus.calls == 1


def test_activate_search_focus_moves_from_data_cell_into_row(parameter_value_view, parameter_value_model):
    column = _column(parameter_value_model, "entity byname")
    parameter_value_view.setCurrentIndex(parameter_value_model.index(0, column))
    with (
        mock.patch(FOCUS_WIDGET, return_value=parameter_value_view),
        mock.patch.object(parameter_value_view, "_focus_search_editor") as focus,
    ):
        parameter_value_view.activate_search_focus()
        focus.assert_called_once_with(column)


def test_activate_search_focus_keeps_focus_when_field_focused(parameter_value_view, parameter_value_model):
    column = _column(parameter_value_model, "entity byname")
    editor = parameter_value_view.search_bar._editors[column]
    with (
        mock.patch(FOCUS_WIDGET, return_value=editor),
        mock.patch.object(parameter_value_view, "_focus_search_editor") as focus,
    ):
        parameter_value_view.activate_search_focus()
        focus.assert_not_called()


def test_activate_search_focus_restores_last_used_from_elsewhere(
    db_editor, parameter_value_view, parameter_value_model
):
    column = _column(parameter_value_model, "entity byname")
    # Record that a search field was focused last, then leave for the tree.
    parameter_value_view._on_search_editor_focused(column)
    with (
        mock.patch(FOCUS_WIDGET, return_value=db_editor.ui.treeView_entity),
        mock.patch.object(parameter_value_view, "_focus_search_editor") as focus,
    ):
        parameter_value_view.activate_search_focus()
        focus.assert_called_once_with(column)


def test_alt_key_is_swallowed_in_search_editor(parameter_value_view, parameter_value_model):
    column = _column(parameter_value_model, "entity byname")
    editor = parameter_value_view.search_bar._editors[column]
    editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier, "2"))
    assert editor.text() == ""
    editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.NoModifier, "2"))
    assert editor.text() == "2"
