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

"""Unit tests for DB editor's custom ``QTableView`` classes."""
import unittest
from unittest import mock

from PySide2.QtCore import QItemSelectionModel
from PySide2.QtWidgets import QApplication

from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.spine_db_manager import SpineDBManager


class TestParameterTableView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        url = "sqlite://"
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = SpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._db_map = self._db_mngr.get_db_map(url, logger, codename="database", create=True)
            self._db_editor = SpineDBEditor(self._db_mngr, {url: "database"})
        QApplication.processEvents()

    def tearDown(self):
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._db_editor = None

    def test_remove_empty_row(self):
        table_view = self._db_editor.ui.tableView_object_parameter_value
        model = table_view.model()
        index = model.index(0, 0)
        selection_model = table_view.selectionModel()
        selection_model.select(index, QItemSelectionModel.ClearAndSelect)
        table_view.remove_selected()
        self.assertFalse(selection_model.hasSelection())


if __name__ == '__main__':
    unittest.main()
