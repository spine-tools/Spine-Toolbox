######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains unit tests for the DataStoreFormBase class.

:author: A. Soininen
:date:   16.3.2020
"""

import unittest
from unittest import mock
from PySide2.QtWidgets import QApplication
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.widgets.data_store_widget import DataStoreFormBase


class TestDataStoreFormBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Builds a DataStoreFormBase object."""
        with mock.patch("spinetoolbox.spine_db_manager.DiffDatabaseMapping") as mock_DiffDBMapping, mock.patch(
            "spinetoolbox.widgets.data_store_widget.DataStoreForm.restore_ui"
        ):
            self.db_mngr = SpineDBManager(None, None)
            self.db_mngr.fetch_db_maps_for_listener = lambda *args: None

            def DiffDBMapping_side_effect(url, upgrade=False, codename=None):
                mock_db_map = mock.MagicMock()
                mock_db_map.codename = codename
                return mock_db_map

            mock_DiffDBMapping.side_effect = DiffDBMapping_side_effect
            self.form = DataStoreFormBase(self.db_mngr, ("mock_url", "mock_db"))

    def tearDown(self):
        """Frees resources after each test."""
        with mock.patch("spinetoolbox.widgets.data_store_widget.DataStoreForm.save_window_state"), mock.patch(
            "spinetoolbox.spine_db_manager.QMessageBox"
        ):
            self.form.close()
        self.form.deleteLater()
        self.form = None

    def test_save_window_state(self):
        self.form.qsettings = mock.MagicMock()
        self.form.save_window_state()
        self.form.qsettings.beginGroup.assert_called_once_with("treeViewWidget")
        self.form.qsettings.endGroup.assert_called_once_with()
        qsettings_save_calls = self.form.qsettings.setValue.call_args_list
        self.assertEqual(len(qsettings_save_calls), 5)
        saved_dict = {saved[0][0]: saved[0][1] for saved in qsettings_save_calls}
        self.assertIn("windowSize", saved_dict)
        self.assertIn("windowPosition", saved_dict)
        self.assertIn("windowState", saved_dict)
        self.assertIn("windowMaximized", saved_dict)
        self.assertIn("n_screens", saved_dict)


if __name__ == '__main__':
    unittest.main()
