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

"""Unit tests for ``custom_menus`` module."""
import unittest
from unittest import mock
from PySide6.QtWidgets import QWidget
from spinetoolbox.database_display_names import NameRegistry
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.widgets.custom_menus import TabularViewDatabaseNameFilterMenu
from tests.mock_helpers import TestCaseWithQApplication


class TestTabularViewCodenameFilterMenu(TestCaseWithQApplication):
    def setUp(self):
        self._parent = QWidget()

    def tearDown(self):
        self._parent.deleteLater()

    def test_init_fills_filter_list_with_database_codenames(self):
        db_map1 = mock.MagicMock()
        db_map1.sa_url = "sqlite://a"
        db_map2 = mock.MagicMock()
        db_map2.sa_url = "sqlite://b"
        db_maps = [db_map1, db_map2]
        name_registry = NameRegistry()
        name_registry.register(db_map1.sa_url, "db map 1")
        name_registry.register(db_map2.sa_url, "db map 2")
        menu = TabularViewDatabaseNameFilterMenu(self._parent, db_maps, "database", name_registry)
        self.assertIs(menu.anchor, self._parent)
        filter_list_model = menu._filter._filter_model
        filter_rows = []
        for row in range(filter_list_model.rowCount()):
            filter_rows.append(filter_list_model.index(row, 0).data())
        self.assertEqual(filter_rows, ["(Select all)", "(Empty)", "db map 1", "db map 2"])

    def test_filter_changed_signal_is_emitted_correctly(self):
        db_map1 = mock.MagicMock()
        db_map1.sa_url = "sqlite://a"
        db_map2 = mock.MagicMock()
        db_map2.sa_url = "sqlite://b"
        db_maps = [db_map1, db_map2]
        name_registry = NameRegistry()
        name_registry.register(db_map1.sa_url, "db map 1")
        name_registry.register(db_map2.sa_url, "db map 2")
        menu = TabularViewDatabaseNameFilterMenu(self._parent, db_maps, "database", name_registry)
        with signal_waiter(menu.filterChanged, timeout=0.1) as waiter:
            menu._clear_filter()
            waiter.wait()
            self.assertEqual(waiter.args, ("database", {None, "db map 1", "db map 2"}, False))


if __name__ == "__main__":
    unittest.main()
