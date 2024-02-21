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
from tempfile import TemporaryDirectory
from PySide6.QtCore import QPoint
from spinetoolbox.spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor
from .spine_db_editor_test_base import DBEditorTestBase
from tests.mock_helpers import create_toolboxui_with_project, clean_up_toolbox, FakeDataStore


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
        multieditor.add_new_tab()
        self.assertEqual(1, multieditor.tab_widget.count())
        multieditor.make_context_menu(0)
        multieditor.show_plus_button_context_menu(QPoint(0, 0))
        # Add fake data stores to project
        self._toolbox.project()._project_items = {"a": FakeDataStore("a")}
        multieditor.show_plus_button_context_menu(QPoint(0, 0))
        multieditor._take_tab(0)
