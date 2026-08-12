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

"""A per-level regex filter bar placed above a tree view."""

from typing import Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget
from ..helpers import SEARCH_FIELD_ACTIVE_STYLE, SearchLineEdit


class TreeLevelFilterBar(QWidget):
    """A horizontal row of regex search fields, one per tree level, sitting above a tree view."""

    filter_edited = Signal(str, str)
    """Emitted as (item_type, text) whenever a level's editor text changes."""
    editor_focused = Signal(str)
    """Emitted with the item type when one of the search fields gains keyboard focus."""
    navigate_to_tree = Signal()
    """Emitted when the user presses Down to leave the filter row for the tree below."""
    lower_filter_active_changed = Signal(bool)
    """Emitted with the new state whenever any cell below the top level toggles between empty and non-empty.

    The view uses the rising edge to capture the tree's expansion state *before* the model hides anything,
    so it can be restored faithfully once the lower-level filters are cleared again.
    """

    def __init__(self, levels: list[tuple[str, str]], parent=None):
        """
        Args:
            levels: (item_type, placeholder) pairs ordered top to bottom
            parent: parent widget
        """
        super().__init__(parent)
        self._editors: dict[str, SearchLineEdit] = {}
        self._order: list[str] = []
        self._last_used_item_type: Optional[str] = None
        self._lower_active = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for item_type, placeholder in levels:
            editor = SearchLineEdit(self)
            editor.setPlaceholderText(placeholder)
            editor.setClearButtonEnabled(True)
            editor.textChanged.connect(lambda text, it=item_type: self._handle_text_changed(it, text))
            editor.focused.connect(lambda it=item_type: self._on_editor_focused(it))
            editor.go_down.connect(self.navigate_to_tree)
            editor.go_left.connect(lambda it=item_type: self._navigate(it, -1))
            editor.go_right.connect(lambda it=item_type: self._navigate(it, 1))
            self._editors[item_type] = editor
            self._order.append(item_type)
            layout.addWidget(editor)
        if self._order:
            self._last_used_item_type = self._order[0]

    def editors(self) -> list[SearchLineEdit]:
        """Returns the search field widgets."""
        return list(self._editors.values())

    def _handle_text_changed(self, item_type: str, text: str) -> None:
        """Highlights an editor that holds a pattern and forwards the change.

        Args:
            item_type: the level's item type
            text: current editor text
        """
        self._editors[item_type].setStyleSheet(SEARCH_FIELD_ACTIVE_STYLE if text else "")
        self.filter_edited.emit(item_type, text)
        self._update_lower_active()

    def _lower_filter_active(self) -> bool:
        """Returns whether any cell below the top level currently holds text."""
        return any(self._editors[it].text() for it in self._order[1:])

    def _update_lower_active(self) -> None:
        """Emits :attr:`lower_filter_active_changed` when the lower-level cells toggle empty/non-empty."""
        active = self._lower_filter_active()
        if active != self._lower_active:
            self._lower_active = active
            self.lower_filter_active_changed.emit(active)

    def _on_editor_focused(self, item_type: str) -> None:
        """Records the last focused field and forwards the focus event.

        Args:
            item_type: the focused level's item type
        """
        self._last_used_item_type = item_type
        self.editor_focused.emit(item_type)

    def _navigate(self, item_type: str, step: int) -> None:
        """Moves focus to the neighboring field in layout order without wrapping.

        Args:
            item_type: the currently focused level's item type
            step: -1 to move to the previous field, +1 for the next
        """
        index = self._order.index(item_type) + step
        if 0 <= index < len(self._order):
            self._focus_editor(self._order[index])

    def _focus_editor(self, item_type: str) -> None:
        """Gives keyboard focus to a level's search field and selects its text.

        Args:
            item_type: the level's item type
        """
        editor = self._editors[item_type]
        editor.setFocus()
        editor.selectAll()

    def focus_first_cell(self) -> None:
        """Focuses the first (leftmost) search field."""
        if self._order:
            self._focus_editor(self._order[0])

    def focus_last_used_cell(self) -> None:
        """Focuses the search field that last had focus, or the first one otherwise."""
        item_type = self._last_used_item_type or (self._order[0] if self._order else None)
        if item_type is not None:
            self._focus_editor(item_type)

    def clear_all(self) -> None:
        """Clears the text and highlight of every editor without emitting filter_edited.

        Still emits :attr:`lower_filter_active_changed` if a lower-level cell was cleared, so the view can
        restore the tree's pre-filter expansion.
        """
        for editor in self._editors.values():
            editor.blockSignals(True)
            editor.setText("")
            editor.setStyleSheet("")
            editor.blockSignals(False)
        self._update_lower_active()
