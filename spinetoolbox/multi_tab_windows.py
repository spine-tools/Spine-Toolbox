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

"""Contains functionality to keep track on open MultiTabWindow instances."""
from spinetoolbox.widgets.multi_tab_window import MultiTabWindow


class MultiTabWindowRegistry:
    """Registry that holds multi tab windows."""

    def __init__(self):
        self._multi_tab_windows: list[MultiTabWindow] = []

    def has_windows(self):
        """Tests if there are any windows registered.

        Returns:
            bool: True if editor windows exist, False otherwise
        """
        return bool(self._multi_tab_windows)

    def windows(self):
        """Returns a list of multi tab windows.

        Returns:
            list of MultiTabWindow: windows
        """
        return list(self._multi_tab_windows)

    def tabs(self):
        """Returns a list of tabs across all windows.

        Returns:
            list of QWidget: tab widgets
        """
        return [
            window.tab_widget.widget(k) for window in self._multi_tab_windows for k in range(window.tab_widget.count())
        ]

    def register_window(self, window):
        """Registers a new multi tab window.

        Args:
            window (MultiTabWindow): window to register
        """
        self._multi_tab_windows.append(window)

    def unregister_window(self, window):
        """Removes multi tab window from the registry.

        Args:
            window (MultiTabWindow): window to unregister
        """
        self._multi_tab_windows.remove(window)

    def get_some_window(self):
        """Returns a random multi tab window or None if none is available.

        Returns:
            MultiTabWindow: editor window
        """
        return self._multi_tab_windows[0] if self._multi_tab_windows else None
