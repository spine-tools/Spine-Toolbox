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

"""Unit tests for the shared search-row helpers and the tree level filter bar.

These cover the view-layer building blocks of the regex search feature in isolation:
``is_unmapped_alt``, ``SearchLineEdit``, ``SearchFocusMixin`` (via a tiny host) and ``TreeLevelFilterBar``.
"""

import unittest
from unittest import mock
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent, QKeyEvent
from PySide6.QtWidgets import QWidget
from spinetoolbox.spine_db_editor.helpers import (
    SEARCH_FIELD_ACTIVE_STYLE,
    SearchFocusMixin,
    SearchLineEdit,
    is_unmapped_alt,
)
from spinetoolbox.spine_db_editor.widgets.tree_filter_bar import TreeLevelFilterBar
from tests.mock_helpers import TestCaseWithQApplication, q_object


def _key_event(key, modifiers, text=""):
    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers, text)


class TestIsUnmappedAlt(TestCaseWithQApplication):
    def test_truth_table(self):
        # Plain Alt -> should be swallowed.
        self.assertTrue(is_unmapped_alt(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier, "2")))
        # AltGr on X11 arrives as Ctrl+Alt -> must be let through.
        self.assertFalse(
            is_unmapped_alt(
                _key_event(
                    Qt.Key.Key_2,
                    Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.ControlModifier,
                    "2",
                )
            )
        )
        # A plain key without Alt -> let through.
        self.assertFalse(is_unmapped_alt(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.NoModifier, "2")))
        # Ctrl only -> let through.
        self.assertFalse(is_unmapped_alt(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.ControlModifier, "2")))


class TestSearchLineEdit(TestCaseWithQApplication):
    def test_focus_in_emits_focused(self):
        with q_object(QWidget()) as parent:
            editor = SearchLineEdit(parent)
            calls = []
            editor.focused.connect(lambda: calls.append(True))
            editor.focusInEvent(QFocusEvent(QEvent.Type.FocusIn, Qt.FocusReason.OtherFocusReason))
            self.assertEqual(calls, [True])

    def test_down_arrow_emits_go_down(self):
        with q_object(QWidget()) as parent:
            editor = SearchLineEdit(parent)
            down = []
            editor.go_down.connect(lambda: down.append(True))
            editor.keyPressEvent(_key_event(Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier))
            self.assertEqual(down, [True])

    def test_arrows_navigate_only_while_empty(self):
        with q_object(QWidget()) as parent:
            editor = SearchLineEdit(parent)
            left = []
            right = []
            editor.go_left.connect(lambda: left.append(True))
            editor.go_right.connect(lambda: right.append(True))
            # Empty: Left/Right navigate between fields.
            editor.keyPressEvent(_key_event(Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier))
            editor.keyPressEvent(_key_event(Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier))
            self.assertEqual(left, [True])
            self.assertEqual(right, [True])
            # Non-empty: arrows move the text cursor instead, so no navigation.
            editor.setText("abc")
            editor.keyPressEvent(_key_event(Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier))
            editor.keyPressEvent(_key_event(Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier))
            self.assertEqual(left, [True])
            self.assertEqual(right, [True])

    def test_alt_key_is_swallowed_but_plain_key_is_typed(self):
        with q_object(QWidget()) as parent:
            editor = SearchLineEdit(parent)
            editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.AltModifier, "2"))
            self.assertEqual(editor.text(), "")
            editor.keyPressEvent(_key_event(Qt.Key.Key_2, Qt.KeyboardModifier.NoModifier, "2"))
            self.assertEqual(editor.text(), "2")


class _FocusHost(SearchFocusMixin, QWidget):
    """A minimal concrete host exercising the SearchFocusMixin choreography deterministically."""

    def __init__(self):
        super().__init__()
        self.e1 = SearchLineEdit(self)
        self.e2 = SearchLineEdit(self)
        self._ready = True
        self._top = True
        self.focused_from_view = 0
        self.restored = 0
        self.set_focus_calls = 0

    def setFocus(self, *args):  # noqa: N802 - Qt override
        self.set_focus_calls += 1

    def _search_focus_ready(self):
        return self._ready

    def _search_row_editor_widgets(self):
        return [self.e1, self.e2]

    def _focus_search_row_from_view(self):
        self.focused_from_view += 1

    def _restore_search_row_focus(self):
        self.restored += 1

    def _at_top_for_search_focus(self):
        return self._top


class TestSearchFocusMixin(TestCaseWithQApplication):
    def _host(self):
        host = _FocusHost()
        self.addCleanup(host.deleteLater)
        return host

    def test_focus_in_clears_last_flag(self):
        host = self._host()
        host._regex_row_was_last = True
        host.focusInEvent(QFocusEvent(QEvent.Type.FocusIn, Qt.FocusReason.OtherFocusReason))
        self.assertFalse(host._regex_row_was_last)

    def test_up_at_top_jumps_into_search_row(self):
        host = self._host()
        host._top = True
        host.keyPressEvent(_key_event(Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier))
        self.assertEqual(host.focused_from_view, 1)

    def test_up_not_at_top_is_forwarded(self):
        host = self._host()
        host._top = False
        host.keyPressEvent(_key_event(Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier))
        self.assertEqual(host.focused_from_view, 0)

    def test_note_search_row_focused_sets_flag(self):
        host = self._host()
        host._note_search_row_focused("payload_ignored")
        self.assertTrue(host._regex_row_was_last)

    def test_activate_not_ready_focuses_view(self):
        host = self._host()
        host._ready = False
        host.activate_search_focus()
        self.assertEqual(host.set_focus_calls, 1)
        self.assertEqual(host.focused_from_view, 0)

    def test_activate_when_field_focused_keeps_it(self):
        host = self._host()
        with mock.patch("spinetoolbox.spine_db_editor.helpers.QApplication.focusWidget", return_value=host.e1):
            host.activate_search_focus()
        self.assertEqual(host.focused_from_view, 0)
        self.assertEqual(host.restored, 0)
        self.assertEqual(host.set_focus_calls, 0)

    def test_activate_from_view_moves_into_row(self):
        host = self._host()
        with mock.patch("spinetoolbox.spine_db_editor.helpers.QApplication.focusWidget", return_value=host):
            host.activate_search_focus()
        self.assertEqual(host.focused_from_view, 1)

    def test_activate_from_elsewhere_restores_last_field(self):
        host = self._host()
        host._regex_row_was_last = True
        with mock.patch("spinetoolbox.spine_db_editor.helpers.QApplication.focusWidget", return_value=QWidget()):
            host.activate_search_focus()
        self.assertEqual(host.restored, 1)

    def test_activate_from_elsewhere_without_history_focuses_view(self):
        host = self._host()
        host._regex_row_was_last = False
        with mock.patch("spinetoolbox.spine_db_editor.helpers.QApplication.focusWidget", return_value=QWidget()):
            host.activate_search_focus()
        self.assertEqual(host.set_focus_calls, 1)
        self.assertEqual(host.restored, 0)

    def test_default_hooks(self):
        class _Bare(SearchFocusMixin):
            pass

        bare = _Bare()
        self.assertTrue(bare._search_focus_ready())
        for hook in (
            bare._search_row_editor_widgets,
            bare._focus_search_row_from_view,
            bare._restore_search_row_focus,
            bare._at_top_for_search_focus,
        ):
            with self.assertRaises(NotImplementedError):
                hook()


class TestTreeLevelFilterBar(TestCaseWithQApplication):
    def _bar(self, levels=(("entity_class", "class…"), ("entity", "entity…"))):
        bar = TreeLevelFilterBar(list(levels))
        self.addCleanup(bar.deleteLater)
        return bar

    def test_one_editor_per_level_with_placeholders(self):
        bar = self._bar()
        editors = bar.editors()
        self.assertEqual(len(editors), 2)
        self.assertEqual(editors[0].placeholderText(), "class…")
        self.assertEqual(editors[1].placeholderText(), "entity…")

    def test_typing_emits_filter_edited_and_highlights(self):
        bar = self._bar()
        edits = []
        bar.filter_edited.connect(lambda it, text: edits.append((it, text)))
        bar._editors["entity_class"].setText("dog")
        self.assertEqual(edits, [("entity_class", "dog")])
        self.assertEqual(bar._editors["entity_class"].styleSheet(), SEARCH_FIELD_ACTIVE_STYLE)
        bar._editors["entity_class"].setText("")
        self.assertEqual(edits[-1], ("entity_class", ""))
        self.assertEqual(bar._editors["entity_class"].styleSheet(), "")

    def test_lower_filter_active_changes_only_for_lower_levels(self):
        bar = self._bar()
        states = []
        bar.lower_filter_active_changed.connect(states.append)
        # Top level typing must not toggle the lower-filter state.
        bar._editors["entity_class"].setText("dog")
        self.assertEqual(states, [])
        # A cell below the top level toggles it on, then off.
        bar._editors["entity"].setText("nemo")
        self.assertEqual(states, [True])
        bar._editors["entity"].setText("")
        self.assertEqual(states, [True, False])

    def test_editor_focus_records_last_used_and_emits(self):
        bar = self._bar()
        focused = []
        bar.editor_focused.connect(focused.append)
        bar._editors["entity"].focused.emit()
        self.assertEqual(focused, ["entity"])
        self.assertEqual(bar._last_used_item_type, "entity")

    def test_navigate_moves_within_bounds(self):
        bar = self._bar()
        with mock.patch.object(bar, "_focus_editor") as focus:
            bar._navigate("entity_class", 1)
            focus.assert_called_once_with("entity")
            focus.reset_mock()
            # No wrapping past the last cell.
            bar._navigate("entity", 1)
            focus.assert_not_called()
            # No wrapping before the first cell.
            bar._navigate("entity_class", -1)
            focus.assert_not_called()

    def test_focus_helpers_run(self):
        bar = self._bar()
        bar.focus_first_cell()
        bar._editors["entity"].focused.emit()  # marks entity as last used
        bar.focus_last_used_cell()
        # focus_last_used_cell falls back to the first cell when nothing was used yet.
        fresh = self._bar()
        fresh._last_used_item_type = None
        fresh.focus_last_used_cell()

    def test_clear_all_resets_text_and_lower_state(self):
        bar = self._bar()
        states = []
        edits = []
        bar._editors["entity"].setText("nemo")
        bar.lower_filter_active_changed.connect(states.append)
        bar.filter_edited.connect(lambda it, text: edits.append((it, text)))
        bar.clear_all()
        self.assertEqual(bar._editors["entity"].text(), "")
        self.assertEqual(bar._editors["entity"].styleSheet(), "")
        # clear_all must not re-emit filter_edited but must announce the lower-level clear.
        self.assertEqual(edits, [])
        self.assertEqual(states, [False])


if __name__ == "__main__":
    unittest.main()
