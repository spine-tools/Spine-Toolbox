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

"""Unit tests for SpineDBEditor classes."""

from unittest.mock import patch
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication
from spinetoolbox.helpers import normcase_database_url_path
from spinetoolbox.multi_tab_windows import MultiTabWindowRegistry
from spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor, open_db_editor
from tests.mock_helpers import FakeDataStore


class TestMultiSpineDBEditor:
    def test_multi_spine_db_editor(self, db_mngr, spine_toolbox_with_project):
        toolbox = spine_toolbox_with_project
        db_mngr.setParent(toolbox)
        multieditor = MultiSpineDBEditor(db_mngr)
        multieditor.add_new_tab([])
        assert multieditor.tab_widget.count() == 1
        multieditor.make_context_menu(0)
        multieditor.show_plus_button_context_menu(QPoint(0, 0))
        # Add fake data stores to project
        toolbox.project()._project_items = {"a": FakeDataStore("a")}
        multieditor.show_plus_button_context_menu(QPoint(0, 0))
        multieditor._take_tab(0)


class TestOpenDBEditor:
    @staticmethod
    def _close_windows(db_editor_registry):
        for editor in db_editor_registry.windows():
            QApplication.processEvents()
            editor.close()
        assert not db_editor_registry.has_windows()

    def test_open_db_editor(self, db_map_generator, db_mngr):
        db_map = db_map_generator()
        db_editor_registry = MultiTabWindowRegistry()
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show") as mock_show,
        ):
            assert not db_editor_registry.has_windows()
            open_db_editor([db_map.db_url], db_mngr, reuse_existing_editor=True)
            mock_show.assert_called_once()
            assert len(db_editor_registry.windows()) == 1
            open_db_editor([db_map.db_url], db_mngr, reuse_existing_editor=True)
            assert len(db_editor_registry.windows()) == 1
            editor = db_editor_registry.windows()[0]
            assert editor.tab_widget.count() == 1
            self._close_windows(db_editor_registry)

    def test_open_db_replaces_db_in_place_when_a_db_is_already_open(self, db_map_generator, db_mngr):
        """File > Open on a tab that already has a database replaces it in place (no new tab)."""
        db_map1 = db_map_generator()
        db_map2 = db_map_generator()
        db_editor_registry = MultiTabWindowRegistry()
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show"),
            patch("spinetoolbox.spine_db_manager.QMessageBox"),
        ):
            window = MultiSpineDBEditor(db_mngr, [db_map1.db_url])
            assert window.tab_widget.count() == 1
            first_tab = window.tab_widget.widget(0)
            assert first_tab.db_urls == [normcase_database_url_path(db_map1.db_url)]
            file_path = db_map2.db_url.replace("sqlite:///", "", 1)
            with patch(
                "spinetoolbox.spine_db_editor.widgets.spine_db_editor.get_open_file_name_in_last_dir",
                return_value=(file_path, ""),
            ):
                first_tab.open_db_file()
            QApplication.processEvents()
            # No new tab; the same tab now holds the second database (replaced in place).
            assert window.tab_widget.count() == 1
            assert window.tab_widget.widget(0) is first_tab
            assert first_tab.db_urls == [normcase_database_url_path(db_map2.db_url)]
            self._close_windows(db_editor_registry)

    def test_open_in_new_tab_opens_a_second_tab(self, db_map_generator, db_mngr):
        """File > Open in new tab on a tab that already has a database opens a NEW tab."""
        db_map1 = db_map_generator()
        db_map2 = db_map_generator()
        db_editor_registry = MultiTabWindowRegistry()
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show"),
        ):
            window = MultiSpineDBEditor(db_mngr, [db_map1.db_url])
            assert window.tab_widget.count() == 1
            first_tab = window.tab_widget.widget(0)
            file_path = db_map2.db_url.replace("sqlite:///", "", 1)
            with patch(
                "spinetoolbox.spine_db_editor.widgets.spine_db_editor.get_open_file_name_in_last_dir",
                return_value=(file_path, ""),
            ):
                first_tab.open_db_file_in_new_tab()
            # A new tab was added; the original tab still holds the first database.
            assert window.tab_widget.count() == 2
            assert window.tab_widget.widget(0).db_urls == [normcase_database_url_path(db_map1.db_url)]
            assert window.tab_widget.widget(1).db_urls == [normcase_database_url_path(db_map2.db_url)]
            self._close_windows(db_editor_registry)

    def test_open_in_new_tab_same_db_raises_existing_tab_instead_of_adding(self, db_map_generator, db_mngr):
        """Opening in a new tab a URL already open selects that tab rather than adding a duplicate."""
        db_map1 = db_map_generator()
        db_map2 = db_map_generator()
        db_editor_registry = MultiTabWindowRegistry()
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show"),
        ):
            window = MultiSpineDBEditor(db_mngr, [db_map1.db_url])
            window.add_new_tab([db_map2.db_url])
            assert window.tab_widget.count() == 2
            window.tab_widget.setCurrentIndex(1)
            # Re-open db1, which is already open in the first tab.
            first_tab = window.tab_widget.widget(0)
            file_path = db_map1.db_url.replace("sqlite:///", "", 1)
            with patch(
                "spinetoolbox.spine_db_editor.widgets.spine_db_editor.get_open_file_name_in_last_dir",
                return_value=(file_path, ""),
            ):
                window.tab_widget.widget(1).open_db_file_in_new_tab()
            # No new tab; the existing db1 tab is selected instead.
            assert window.tab_widget.count() == 2
            assert window.tab_widget.currentWidget() is first_tab
            self._close_windows(db_editor_registry)

    def test_closing_last_tab_keeps_window_open_with_no_tabs(self, db_map_generator, db_mngr):
        """Closing the last tab leaves the MultiSpineDBEditor open (empty), instead of closing the window."""
        db_map = db_map_generator()
        db_editor_registry = MultiTabWindowRegistry()
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show"),
            patch("spinetoolbox.spine_db_manager.QMessageBox"),
        ):
            window = MultiSpineDBEditor(db_mngr, [db_map.db_url])
            assert window.tab_widget.count() == 1
            window._close_tab(0)
            # The window is still open (registered) with no tabs, ready to open a new db via "+".
            assert window.tab_widget.count() == 0
            assert window in db_editor_registry.windows()
            # The "+" button still works on the empty window.
            window.add_new_tab([db_map.db_url])
            assert window.tab_widget.count() == 1
            self._close_windows(db_editor_registry)

    def test_replace_path_still_replaces_db_in_place(self, db_map_generator, db_mngr):
        """Regression guard for deliverable 1: load_db_urls([url]) still replaces the db in place.

        The reload/refresh flows and the "add a db" action rely on load_db_urls tearing down the old db
        maps and loading the given ones into the same editor. This asserts that path is not a no-op.
        """
        db_map1 = db_map_generator()
        db_map2 = db_map_generator()
        db_editor_registry = MultiTabWindowRegistry()
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show"),
            patch("spinetoolbox.spine_db_manager.QMessageBox"),
        ):
            window = MultiSpineDBEditor(db_mngr, [db_map1.db_url])
            tab = window.tab_widget.widget(0)
            assert tab.db_urls == [normcase_database_url_path(db_map1.db_url)]
            assert tab.load_db_urls([db_map2.db_url]) is True
            QApplication.processEvents()
            # Same tab, but now holding the second database (replaced, not a no-op, no extra tab).
            assert window.tab_widget.count() == 1
            assert tab.db_urls == [normcase_database_url_path(db_map2.db_url)]
            self._close_windows(db_editor_registry)

    def test_open_db_in_tab_when_editor_has_an_empty_tab(self, db_map_generator, db_mngr):
        db_map = db_map_generator()
        db_editor_registry = MultiTabWindowRegistry()
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show"),
        ):
            assert not db_editor_registry.has_windows()
            window = MultiSpineDBEditor(db_mngr, [])
            assert window.tab_widget.count() == 1
            tab = window.tab_widget.widget(0)
            assert tab.db_urls == []
            open_db_editor([db_map.db_url], db_mngr, reuse_existing_editor=True)
            assert window.tab_widget.count() == 2
            tab = window.tab_widget.widget(1)
            assert tab.db_urls == [normcase_database_url_path(db_map.db_url)]
            self._close_windows(db_editor_registry)
