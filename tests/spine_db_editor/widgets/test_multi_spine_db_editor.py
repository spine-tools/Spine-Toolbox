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
