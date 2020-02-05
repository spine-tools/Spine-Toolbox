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
Unit tests for DataStoreForm classes.

:author: M. Marin (KTH)
:date:   6.12.2018
"""

import unittest
from unittest import mock
import logging
import os
import sys
from PySide2.QtWidgets import QApplication, QAction
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.widgets.data_store_widget import DataStoreForm
from spinetoolbox.widgets.add_db_items_dialogs import AddObjectClassesDialog


class TestAddItemsDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def setUp(self):
        """Overridden method. Runs before each test. Makes instance of DataStoreForm class."""
        with mock.patch("spinetoolbox.spine_db_manager.QMessageBox"), mock.patch(
            "spinetoolbox.widgets.data_store_widget.DataStoreForm.restore_ui"
        ):
            self.mock_db_mngr = mock.MagicMock()

            def get_db_map_for_listener_side_effect(listener, url, codename=None):
                mock_db_map = mock.MagicMock()
                mock_db_map.codename = codename
                return mock_db_map

            self.mock_db_mngr.get_db_map_for_listener.side_effect = get_db_map_for_listener_side_effect
            self.mock_db_mngr.undo_action.__getitem__.side_effect = lambda key: QAction()
            self.mock_db_mngr.redo_action.__getitem__.side_effect = lambda key: QAction()
            self.ds_view_form = DataStoreForm(self.mock_db_mngr, ("mock_url", "mock_db"))
            self.mock_db_map = self.ds_view_form.db_map

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        with mock.patch("spinetoolbox.widgets.data_store_widget.DataStoreForm.save_window_state") as mock_save_w_s:
            self.ds_view_form.close()
            mock_save_w_s.assert_called_once()
        self.ds_view_form.deleteLater()
        self.ds_view_form = None
        try:
            os.remove('mock_db.sqlite')
        except OSError:
            pass

    def test_add_object_classes(self):
        """Test object classes are added through the manager when accepting the dialog."""
        dialog = AddObjectClassesDialog(self.ds_view_form, self.mock_db_mngr, self.mock_db_map)
        model = dialog.model
        header = model.header
        model.fetchMore()
        self.assertEqual(header, ['object class name', 'description', 'display icon', 'databases'])
        indexes = [model.index(0, header.index(field)) for field in ('object class name', 'databases')]
        values = ['fish', 'mock_db']
        model.batch_set_data(indexes, values)

        def _add_object_classes(db_map_data):
            self.assertTrue(self.mock_db_map in db_map_data)
            data = db_map_data[self.mock_db_map]
            self.assertEqual(len(data), 1)
            item = data[0]
            self.assertTrue("name" in item)
            self.assertEqual(item["name"], "fish")

        self.mock_db_mngr.add_object_classes.side_effect = _add_object_classes
        dialog.accept()
        self.mock_db_mngr.add_object_classes.assert_called_once()

    def test_do_not_add_object_classes_with_invalid_db(self):
        """Test object classes aren't added when the database is not correct."""
        dialog = AddObjectClassesDialog(self.ds_view_form, self.mock_db_mngr, self.mock_db_map)
        self.ds_view_form.msg_error = mock.NonCallableMagicMock()
        self.ds_view_form.msg_error.attach_mock(mock.MagicMock(), "emit")
        model = dialog.model
        header = model.header
        model.fetchMore()
        self.assertEqual(header, ['object class name', 'description', 'display icon', 'databases'])
        indexes = [model.index(0, header.index(field)) for field in ('object class name', 'databases')]
        values = ['fish', 'gibberish']
        model.batch_set_data(indexes, values)
        dialog.accept()
        self.mock_db_mngr.add_object_classes.assert_not_called()
        self.ds_view_form.msg_error.emit.assert_called_with("Invalid database 'gibberish' at row 1")


if __name__ == '__main__':
    unittest.main()
