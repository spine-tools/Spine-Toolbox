######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains unit tests for the SpineDBEditorBase class.

:author: A. Soininen
:date:   16.3.2020
"""

import unittest
from unittest import mock
from PySide2.QtWidgets import QApplication
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditorBase


class TestSpineDBEditorBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Builds a SpineDBEditorBase object."""
        with mock.patch("spinetoolbox.spine_db_worker.DiffDatabaseMapping") as mock_DiffDBMapping, mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"
        ), mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwards: 0
            self.db_mngr = SpineDBManager(mock_settings, None)
            self.db_mngr.fetch_db_maps_for_listener = lambda *args: None

            def DiffDBMapping_side_effect(url, codename=None, upgrade=False, create=False):
                mock_db_map = mock.MagicMock()
                mock_db_map.codename = codename
                mock_db_map.db_url = url
                return mock_db_map

            mock_DiffDBMapping.side_effect = DiffDBMapping_side_effect
            self.db_editor = SpineDBEditorBase(self.db_mngr)

    def tearDown(self):
        """Frees resources after each test."""
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self.db_editor.close()
        self.db_editor.deleteLater()
        self.db_editor = None

    def test_save_window_state(self):
        self.db_editor.save_window_state()
        self.db_editor.qsettings.beginGroup.assert_has_calls([mock.call("spineDBEditor"), mock.call("")])
        self.db_editor.qsettings.endGroup.assert_has_calls([mock.call(), mock.call()])
        qsettings_save_calls = self.db_editor.qsettings.setValue.call_args_list
        self.assertEqual(len(qsettings_save_calls), 1)
        saved_dict = {saved[0][0]: saved[0][1] for saved in qsettings_save_calls}
        self.assertIn("windowState", saved_dict)


if __name__ == '__main__':
    unittest.main()
