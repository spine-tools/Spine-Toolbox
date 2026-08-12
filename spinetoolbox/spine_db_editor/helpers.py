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

"""Helpers and utilities for Spine Database editor."""

import locale
from typing import Any, Optional, Union
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLineEdit
from spinedb_api.helpers import string_to_bool as base_string_to_bool
from spinetoolbox.helpers import DB_ITEM_SEPARATOR

# A search field that holds a pattern is highlighted so it stands out in both light and dark themes.
# Explicit colors override the theme deliberately.
SEARCH_FIELD_ACTIVE_STYLE = "QLineEdit { background: #8b0000; color: white; }"


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
        modifiers = event.modifiers()
        # Alt+<key> combinations are reserved for window shortcuts (e.g. Alt+1/3/4/... focus docks).
        # Mapped ones fire as QShortcuts on the main window before this handler runs; unmapped combos
        # like Alt+2 must be swallowed here so their character is not typed into the search field.
        # AltGr composed input arrives as Ctrl+Alt on X11, so let it through when Ctrl is also held.
        if modifiers & Qt.KeyboardModifier.AltModifier and not modifiers & Qt.KeyboardModifier.ControlModifier:
            event.ignore()
            return
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


def string_to_display_icon(x: str) -> Optional[int]:
    """Converts a 'foreign' string (from e.g. Excel) to entity class display icon.

    Args:
        x: string to convert

    Returns:
        display icon or None if conversion failed
    """
    try:
        return int(x)
    except ValueError:
        return None


TRUE_STRING = "true"
FALSE_STRING = "false"


def string_to_bool(x: Union[str, bytes]) -> bool:
    """Converts a 'foreign' string (from e.g. Excel) to boolean.

    Args:
        string to convert

    Returns:
        boolean value
    """
    if isinstance(x, bytes):
        x = x.decode()
    try:
        return base_string_to_bool(x)
    except ValueError:
        return False


def bool_to_string(x: bool) -> str:
    return TRUE_STRING if x else FALSE_STRING


def optional_to_string(x: Optional[Any]) -> Optional[str]:
    return str(x) if x is not None else None


def group_to_string(group: Union[str, tuple[str, ...]]) -> Optional[str]:
    if not group:
        return None
    if isinstance(group, str):
        return group
    return DB_ITEM_SEPARATOR.join(group)


def string_to_group(string: Optional[str]) -> Union[str, tuple[str, ...]]:
    if not string:
        return ()
    separator = DB_ITEM_SEPARATOR if DB_ITEM_SEPARATOR in string else ","
    return tuple(stripped for t in string.split(separator) if (stripped := t.strip()))


def parameter_value_to_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    try:
        number = float(value)
        return locale.str(number)
    except ValueError:
        return str(value)


def string_to_parameter_value(str_value: str) -> Any:
    try:
        return float(str_value)
    except ValueError:
        try:
            return locale.atof(str_value)
        except ValueError:
            pass
    if str_value == TRUE_STRING:
        return True
    if str_value == FALSE_STRING:
        return False
    return str_value


def input_string_to_int(str_value: str) -> int:
    try:
        x = float(str_value)
    except ValueError:
        x = locale.atof(str_value)
    return int(round(x))


GRAPH_OVERLAY_COLOR = QColor(210, 210, 210, 211)
