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
import sys
import unittest
from unittest import mock
from sqlalchemy.engine.url import make_url
from spinetoolbox.database_display_names import NameRegistry, suggest_display_name
from spinetoolbox.helpers import signal_waiter
from tests.mock_helpers import TestCaseWithQApplication


class TestNameRegistry(TestCaseWithQApplication):
    def test_display_name_for_unregistered_url(self):
        registry = NameRegistry()
        self.assertEqual(registry.display_name("mysql://db.example.com/best_database"), "best_database")
        sa_url = make_url("mysql://db.example.com/even_better_database")
        self.assertEqual(registry.display_name(sa_url), "even_better_database")

    def test_display_name_for_registered_url(self):
        registry = NameRegistry()
        url = "mysql://db.example.com/best_database"
        registry.register(url, "Best database")
        self.assertEqual(registry.display_name(url), "Best database")
        sa_url = make_url("mysql://db.example.com/even_better_database")
        registry.register(sa_url, "Even better database")
        self.assertEqual(registry.display_name(sa_url), "Even better database")

    def test_multiple_registered_names_gives_simple_database_name(self):
        registry = NameRegistry()
        url = "mysql://db.example.com/best_database"
        with signal_waiter(registry.display_name_changed, timeout=0.1) as waiter:
            registry.register(url, "Best database")
        self.assertEqual(waiter.args, (url, "Best database"))
        with signal_waiter(registry.display_name_changed, timeout=0.1) as waiter:
            registry.register(url, "Even better database")
        self.assertEqual(waiter.args, (url, "best_database"))
        self.assertEqual(registry.display_name(url), "best_database")

    def test_unregister(self):
        registry = NameRegistry()
        url = "mysql://db.example.com/best_database"
        with signal_waiter(registry.display_name_changed, timeout=0.1) as waiter:
            registry.register(url, "Best database")
        self.assertEqual(waiter.args, (url, "Best database"))
        self.assertEqual(registry.display_name(url), "Best database")
        with signal_waiter(registry.display_name_changed, timeout=0.1) as waiter:
            registry.unregister(url, "Best database")
        self.assertEqual(waiter.args, (url, "best_database"))
        self.assertEqual(registry.display_name(url), "best_database")

    def test_unregister_one_of_two_names(self):
        registry = NameRegistry()
        url = "mysql://db.example.com/best_database"
        registry.register(url, "Database 1")
        registry.register(url, "Database 2")
        self.assertEqual(registry.display_name(url), "best_database")
        with signal_waiter(registry.display_name_changed, timeout=0.1) as waiter:
            registry.unregister(url, "Database 1")
        self.assertEqual(waiter.args, (url, "Database 2"))
        self.assertEqual(registry.display_name(url), "Database 2")

    def test_unregister_one_of_three_names(self):
        registry = NameRegistry()
        url = "mysql://db.example.com/best_database"
        registry.register(url, "Database 1")
        registry.register(url, "Database 2")
        registry.register(url, "Database 3")
        self.assertEqual(registry.display_name(url), "best_database")
        with mock.patch.object(registry, "display_name_changed") as name_changed_signal:
            registry.unregister(url, "Database 3")
            name_changed_signal.emit.assert_not_called()
        self.assertEqual(registry.display_name(url), "best_database")


class TestSuggestDisplayName(unittest.TestCase):
    def test_mysql_url_returns_database_name(self):
        sa_url = make_url("mysql://db.example.com/my_lovely_db")
        self.assertEqual(suggest_display_name(sa_url), "my_lovely_db")

    def test_sqlite_url_returns_file_name_without_extension(self):
        path = r"c:\path\to\my_lovely_db.sqlite" if sys.platform == "win32" else "/path/to/my_lovely_db.sqlite"
        sa_url = make_url(r"sqlite:///" + path)
        self.assertEqual(suggest_display_name(sa_url), "my_lovely_db")

    def test_in_memory_sqlite_url_returns_random_hash(self):
        sa_url = make_url(r"sqlite://")
        name = suggest_display_name(sa_url)
        self.assertTrue(isinstance(name, str))
        self.assertTrue(bool(name))


if __name__ == "__main__":
    unittest.main()
