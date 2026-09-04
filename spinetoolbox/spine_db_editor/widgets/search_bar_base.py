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

"""Shared search-row widgets and focus choreography for the Spine Database editor."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QLineEdit

# A search field that holds a pattern is highlighted so it stands out in both light and dark themes.
# Explicit colors override the theme deliberately. The border forces Qt off the native macOS
# text field, which otherwise ignores the background and leaves white text on a white field.
SEARCH_FIELD_ACTIVE_STYLE = "QLineEdit { background-color: #8b0000; color: white; border: 1px solid #8b0000; }"


def is_unmapped_alt(event) -> bool:
    """Tells whether a key event carries an unmapped Alt shortcut that should be swallowed.

    Alt+<key> combinations are reserved for window shortcuts (e.g. Alt+1/3/4/... focus docks).
    Mapped ones fire as QShortcuts on the main window before a widget's key handler runs; unmapped
    combos like Alt+2 must be swallowed so their character is not typed into a line edit. AltGr
    composed input arrives as Ctrl+Alt on X11, so it is let through when Ctrl is also held.

    Args:
        event: the key press event to inspect

    Returns:
        True if Alt is set and Ctrl is not, False otherwise
    """
    modifiers = event.modifiers()
    return bool(modifiers & Qt.KeyboardModifier.AltModifier) and not modifiers & Qt.KeyboardModifier.ControlModifier


class SearchLineEdit(QLineEdit):
    """A search field that reports focus and directional navigation to its owner.

    Shared by the stacked tables' column search row and the trees' per-level filter bar so both
    provide the same keyboard behavior: while the field is empty the Left/Right arrows navigate
    between neighboring fields, and Down leaves the search row for the data below.
    """

    focused = Signal()
    go_down = Signal()
    go_left = Signal()
    go_right = Signal()

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self.focused.emit()

    def keyPressEvent(self, event) -> None:
        if is_unmapped_alt(event):
            event.ignore()
            return
        modifiers = event.modifiers()
        if modifiers == Qt.KeyboardModifier.NoModifier:
            if event.key() == Qt.Key.Key_Down:
                self.go_down.emit()
                return
            # While the editor is empty, arrows navigate between cells like the table's value cells;
            # once typing has started, they move the text cursor as usual.
            if not self.text():
                if event.key() == Qt.Key.Key_Left:
                    self.go_left.emit()
                    return
                if event.key() == Qt.Key.Key_Right:
                    self.go_right.emit()
                    return
        super().keyPressEvent(event)


class SearchFocusMixin:
    """Shared keyboard-focus choreography between a view and its regex search row.

    Both the stacked tables' per-column search row and the trees' per-level filter bar sit directly
    above their view and behave the same way: the view's Alt+N shortcut toggles focus into the search
    row, the Up arrow on the view's topmost row/item jumps into the search row, and the mixin tracks
    whether a search field or the view itself was focused last so the shortcut can restore the right
    one.

    Subclasses supply the parts that genuinely differ through small hooks:
    :meth:`_search_row_editor_widgets`, :meth:`_focus_search_row_from_view`,
    :meth:`_restore_search_row_focus` and :meth:`_at_top_for_search_focus`, plus the optional
    :meth:`_search_focus_ready` guard for views whose search row may not exist yet.
    """

    _regex_row_was_last = False  # Whether a search field was the last focused element here.

    def focusInEvent(self, event) -> None:
        """Records that the view (not a search field) is now the focused element here."""
        super().focusInEvent(event)
        self._regex_row_was_last = False

    def keyPressEvent(self, event) -> None:
        """Jumps into the search row when the Up arrow leaves the view's topmost row/item."""
        if (
            event.key() == Qt.Key.Key_Up
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
            and self._at_top_for_search_focus()
        ):
            self._focus_search_row_from_view()
            return
        super().keyPressEvent(event)

    def activate_search_focus(self) -> None:
        """Focus behavior for this view's Alt+N shortcut.

        When focus is elsewhere, restores the last focused element here (the view or a search
        field). When the view already has focus, moves into the search row. When a search field
        already has focus, keeps it.
        """
        if not self._search_focus_ready():
            self.setFocus()
            return
        focused = QApplication.focusWidget()
        if focused in self._search_row_editor_widgets():
            return
        if focused is self:
            self._focus_search_row_from_view()
            return
        if self._regex_row_was_last:
            self._restore_search_row_focus()
        else:
            self.setFocus()

    def _note_search_row_focused(self, *_args) -> None:
        """Records that a search field is now the last focused element here.

        Accepts and ignores extra arguments so it can be connected directly to focus signals that
        carry a payload (e.g. the focused column or item type).
        """
        self._regex_row_was_last = True

    # Hooks implemented by subclasses.

    def _search_focus_ready(self) -> bool:
        """Tells whether the search row exists and can take focus."""
        return True

    def _search_row_editor_widgets(self):
        """Returns the search-field widgets, used to detect whether one already has focus."""
        raise NotImplementedError()

    def _focus_search_row_from_view(self) -> None:
        """Moves focus from the focused view into the search row."""
        raise NotImplementedError()

    def _restore_search_row_focus(self) -> None:
        """Focuses the search field that was last used here."""
        raise NotImplementedError()

    def _at_top_for_search_focus(self) -> bool:
        """Tells whether the view is positioned so that Up should jump into the search row."""
        raise NotImplementedError()
