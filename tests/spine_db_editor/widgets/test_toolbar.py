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

"""Unit tests for the ``toolbar`` module."""
from tempfile import TemporaryDirectory
from unittest import mock
from spinetoolbox.spine_db_editor.widgets.toolbar import DBEditorToolBar
from tests.mock_helpers import clean_up_toolbox, create_toolboxui_with_project
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase


class TestDBEditorToolBar(DBEditorTestBase):
    def setUp(self):
        super().setUp()
        self._temp_dir = TemporaryDirectory()
        self._toolbox = create_toolboxui_with_project(self._temp_dir.name)

    def tearDown(self):
        super().tearDown()
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_toolbar(self):
        self.db_mngr.setParent(self._toolbox)
        tb = DBEditorToolBar(self.spine_db_editor)
        self.assertEqual([{"database": "sqlite://"}], self.spine_db_editor._history)
        with mock.patch("spinetoolbox.spine_db_editor.widgets.toolbar._URLDialog.show") as mock_show_dialog:
            mock_show_dialog.show.return_value = True
            tb._show_url_codename_widget()
            mock_show_dialog.assert_called()
