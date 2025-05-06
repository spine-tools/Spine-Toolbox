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
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QPoint, QSettings
from PySide6.QtWidgets import QApplication
from spinetoolbox.multi_tab_windows import MultiTabWindowRegistry
from spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor, open_db_editor
from spinetoolbox.spine_db_manager import SpineDBManager
from tests.mock_helpers import FakeDataStore, TestCaseWithQApplication, clean_up_toolbox, create_toolboxui_with_project
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase


class TestMultiSpineDBEditor(DBEditorTestBase):
    def setUp(self):
        super().setUp()
        self._temp_dir = TemporaryDirectory()
        self._toolbox = create_toolboxui_with_project(self._temp_dir.name)

    def tearDown(self):
        super().tearDown()
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_multi_spine_db_editor(self):
        self.db_mngr.setParent(self._toolbox)
        multieditor = MultiSpineDBEditor(self.db_mngr)
        multieditor.add_new_tab([])
        self.assertEqual(1, multieditor.tab_widget.count())
        multieditor.make_context_menu(0)
        multieditor.show_plus_button_context_menu(QPoint(0, 0))
        # Add fake data stores to project
        self._toolbox.project()._project_items = {"a": FakeDataStore("a")}
        multieditor.show_plus_button_context_menu(QPoint(0, 0))
        multieditor._take_tab(0)


class TestOpenDBEditor(TestCaseWithQApplication):
    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        db_path = Path(self._temp_dir.name, "db.sqlite")
        self._db_url = "sqlite:///" + str(db_path)
        self._db_mngr = SpineDBManager(QSettings(), None)
        self._logger = MagicMock()
        self._db_editor_registry = MultiTabWindowRegistry()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()
        # Database connection may still be open. Retry cleanup until it succeeds.
        running = True
        while running:
            QApplication.processEvents()
            try:
                self._temp_dir.cleanup()
            except NotADirectoryError:
                pass
            else:
                running = False

    def _close_windows(self):
        for editor in self._db_editor_registry.windows():
            QApplication.processEvents()
            editor.close()
        self.assertFalse(self._db_editor_registry.has_windows())

    def test_open_db_editor(self):
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                self._db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show") as mock_show,
        ):
            self.assertFalse(self._db_editor_registry.has_windows())
            open_db_editor([self._db_url], self._db_mngr, reuse_existing_editor=True)
            mock_show.assert_called_once()
            self.assertEqual(len(self._db_editor_registry.windows()), 1)
            open_db_editor([self._db_url], self._db_mngr, reuse_existing_editor=True)
            self.assertEqual(len(self._db_editor_registry.windows()), 1)
            editor = self._db_editor_registry.windows()[0]
            self.assertEqual(editor.tab_widget.count(), 1)
            self._close_windows()

    def test_open_db_in_tab_when_editor_has_an_empty_tab(self):
        with (
            patch(
                "spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.db_editor_registry",
                self._db_editor_registry,
            ),
            patch("spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor.MultiSpineDBEditor.show") as mock_show,
        ):
            self.assertFalse(self._db_editor_registry.has_windows())
            window = MultiSpineDBEditor(self._db_mngr, [])
            self.assertEqual(window.tab_widget.count(), 1)
            tab = window.tab_widget.widget(0)
            self.assertEqual(tab.db_urls, [])
            open_db_editor([self._db_url], self._db_mngr, reuse_existing_editor=True)
            self.assertEqual(window.tab_widget.count(), 2)
            tab = window.tab_widget.widget(1)
            self.assertEqual(tab.db_urls, [self._db_url])
            self._close_windows()
