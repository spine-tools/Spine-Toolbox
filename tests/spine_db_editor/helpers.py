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

"""Helper utilities for Database editor's tests."""
from unittest import mock
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from tests.mock_helpers import TestCaseWithQApplication, MockSpineDBManager


class TestBase(TestCaseWithQApplication):
    """Base class for Database editor's table and tree view tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.db_codename = cls.__name__ + "_db"

    def setUp(self):
        self._common_setup("sqlite://", create=True)

    def tearDown(self):
        self._common_tear_down()

    def _common_setup(self, url, create):
        with (
            mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"),
            mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"),
        ):
            mock_settings = mock.MagicMock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = MockSpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._db_map = self._db_mngr.get_db_map(url, logger, create=create)
            self._db_mngr.name_registry.register(url, self.db_codename)
            self._db_editor = SpineDBEditor(self._db_mngr, [url])
        QApplication.processEvents()

    def _common_tear_down(self):
        with (
            mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"),
            mock.patch("spinetoolbox.spine_db_manager.QMessageBox"),
        ):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._db_editor = None  # pylint: disable=attribute-defined-outside-init

    def _commit_changes_to_database(self, commit_message):
        with mock.patch.object(self._db_editor, "_get_commit_msg") as commit_msg:
            commit_msg.return_value = commit_message
            self._db_editor.ui.actionCommit.trigger()
