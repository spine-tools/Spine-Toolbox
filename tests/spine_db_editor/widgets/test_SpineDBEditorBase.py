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

"""Contains unit tests for the SpineDBEditorBase class."""
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditorBase
from tests.mock_helpers import TestSpineDBManager


class TestSpineDBEditorBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Builds a SpineDBEditorBase object."""
        with mock.patch("spinetoolbox.spine_db_worker.DatabaseMapping") as mock_DiffDBMapping, mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"
        ), mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwards: 0
            self.db_mngr = TestSpineDBManager(mock_settings, None)

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
            self.db_editor._parameter_models = []
            self.db_editor.close()
        self.db_mngr.close_all_sessions()
        self.db_mngr.clean_up()
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

    def test_import_file_recognizes_excel(self):
        with mock.patch.object(self.db_editor, "qsettings"), mock.patch.object(
            self.db_editor, "import_from_excel"
        ) as mock_import_from_excel, mock.patch("spinetoolbox.helpers.QFileDialog") as mock_file_dialog:
            mock_file_dialog.getOpenFileName.return_value = "my_excel_file.xlsx", "Excel files (*.xlsx)"
            self.db_editor.import_file()
            mock_import_from_excel.assert_called_once_with("my_excel_file.xlsx")

    def test_import_file_recognizes_sqlite(self):
        with mock.patch.object(self.db_editor, "qsettings"), mock.patch.object(
            self.db_editor, "import_from_sqlite"
        ) as mock_import_from_sqlite, mock.patch("spinetoolbox.helpers.QFileDialog") as mock_file_dialog:
            mock_file_dialog.getOpenFileName.return_value = "my_sqlite_file.sqlite", "SQLite files (*.sqlite)"
            self.db_editor.import_file()
            mock_import_from_sqlite.assert_called_once_with("my_sqlite_file.sqlite")

    def test_import_file_recognizes_json(self):
        with mock.patch.object(self.db_editor, "qsettings"), mock.patch.object(
            self.db_editor, "import_from_json"
        ) as mock_import_from_json, mock.patch("spinetoolbox.helpers.QFileDialog") as mock_file_dialog:
            mock_file_dialog.getOpenFileName.return_value = "my_json_file.json", "JSON files (*.json)"
            self.db_editor.import_file()
            mock_import_from_json.assert_called_once_with("my_json_file.json")


if __name__ == "__main__":
    unittest.main()
