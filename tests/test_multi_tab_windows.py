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
import unittest
from unittest import mock
from spinetoolbox.multi_tab_windows import MultiTabWindowRegistry


class TestMultiTabWindowRegistry(unittest.TestCase):
    def test_initialization(self):
        registry = MultiTabWindowRegistry()
        self.assertFalse(registry.has_windows())
        self.assertEqual(registry.windows(), [])
        self.assertEqual(registry.tabs(), [])
        self.assertIsNone(registry.get_some_window())

    def test_register_window(self):
        registry = MultiTabWindowRegistry()
        window = mock.MagicMock()
        registry.register_window(window)
        self.assertEqual(registry.windows(), [window])

    def test_unregister_window(self):
        registry = MultiTabWindowRegistry()
        window = mock.MagicMock()
        registry.register_window(window)
        self.assertTrue(registry.has_windows())
        registry.unregister_window(window)
        self.assertEqual(registry.windows(), [])

    def test_get_some_window(self):
        registry = MultiTabWindowRegistry()
        window = mock.MagicMock()
        registry.register_window(window)
        self.assertIs(registry.get_some_window(), window)

    def test_tabs(self):
        registry = MultiTabWindowRegistry()
        window = mock.MagicMock()
        window.tab_widget.count.return_value = 1
        tab = mock.MagicMock()
        window.tab_widget.widget.return_value = tab
        registry.register_window(window)
        self.assertEqual(registry.tabs(), [tab])


if __name__ == "__main__":
    unittest.main()
