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

"""Unit tests for the ``url_toolbar`` module."""

from unittest import mock
from PySide6.QtWidgets import QApplication, QWidget
from spinetoolbox.spine_db_editor.widgets.url_toolbar import UrlToolBar
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase


class TestURLToolbar(DBEditorTestBase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_url_toolbar(self):
        self.mock_toolbox = QWidget()
        self.db_mngr.setParent(self.mock_toolbox)
        tb = UrlToolBar(self.spine_db_editor)
        tb.add_urls_to_history(self.db_mngr.db_urls)
        self.assertEqual({"sqlite://"}, tb.get_previous_urls())
        self.assertEqual({"sqlite://"}, tb.get_next_urls())
        with mock.patch("spinetoolbox.spine_db_editor.widgets.url_toolbar._UrlFilterDialog.show") as mock_show_dialog:
            mock_show_dialog.show.return_value = True
            tb._show_filter_menu()
            mock_show_dialog.assert_called()
        self.mock_toolbox.deleteLater()
